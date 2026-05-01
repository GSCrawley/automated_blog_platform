"""PR #6.4 cleanup — interactively remove off-niche products and articles
that were seeded by the old dummy template path.

Usage:
    cd automated-blog-system
    python scripts/cleanup_polluted_seed_data.py [--dry-run]

The script lists, per niche, every product whose name+description+category has
zero keyword overlap with the niche's name+description+keywords, and prompts
for y/N before deleting each batch. Articles linked to a deleted product are
deleted with it (we delete articles first to avoid FK issues).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make src importable when running this script directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _keyword_overlap(niche_text: str, product_text: str) -> int:
    """Crude token overlap. Higher = more related."""
    n = {t.lower().strip() for t in niche_text.replace(",", " ").split() if len(t) > 2}
    p = {t.lower().strip() for t in product_text.replace(",", " ").split() if len(t) > 2}
    return len(n & p)


def main(dry_run: bool) -> int:
    from src.main import create_app
    from src.models.user import db
    from src.models.niche import Niche
    from src.models.product import Product, Article

    app = create_app()
    with app.app_context():
        niches = Niche.query.all()
        if not niches:
            print("No niches found. Nothing to clean.")
            return 0

        total_deleted_products = 0
        total_deleted_articles = 0

        for niche in niches:
            niche_text = " ".join(filter(None, [
                niche.name or "",
                niche.description or "",
                niche.target_keywords or "",
                niche.content_themes or "",
            ]))
            print(f"\n=== Niche: {niche.name} (id={niche.id}) ===")
            print(f"    Keywords: {niche.target_keywords or '(none)'}")

            products = Product.query.filter_by(niche_id=niche.id).all()
            if not products:
                print("    No products. Skipping.")
                continue

            suspicious = []
            for product in products:
                product_text = " ".join(filter(None, [
                    product.name or "",
                    product.description or "",
                    product.category or "",
                ]))
                overlap = _keyword_overlap(niche_text, product_text)
                if overlap == 0:
                    suspicious.append(product)

            if not suspicious:
                print(f"    All {len(products)} products look on-niche.")
                continue

            print(f"    Found {len(suspicious)} suspicious (zero-overlap) products:")
            for p in suspicious:
                article_count = Article.query.filter_by(product_id=p.id).count()
                print(f"      - id={p.id} '{p.name}' [{p.category}] "
                      f"({article_count} article(s))")

            if dry_run:
                print("    [DRY RUN] not deleting.")
                continue

            answer = input(
                f"    Delete these {len(suspicious)} products and "
                f"their articles? [y/N]: "
            ).strip().lower()
            if answer != "y":
                print("    Skipped.")
                continue

            for p in suspicious:
                articles = Article.query.filter_by(product_id=p.id).all()
                for a in articles:
                    db.session.delete(a)
                    total_deleted_articles += 1
                db.session.delete(p)
                total_deleted_products += 1
            db.session.commit()
            print(f"    Deleted {len(suspicious)} products from this niche.")

        print(
            f"\nTotal deleted: {total_deleted_products} products, "
            f"{total_deleted_articles} articles."
        )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be deleted without deleting.",
    )
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))

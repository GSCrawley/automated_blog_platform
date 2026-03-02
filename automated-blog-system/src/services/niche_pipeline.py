"""
Niche Pipeline Service
======================
Orchestrates the automated flow when a new niche is created:
1. Discover lucrative products & affiliate programs for the niche
2. Generate SEO-optimized blog articles for each product
"""

import threading
import logging
import json
import random
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class NichePipelineService:
    """Automatically discovers products and generates content for a niche."""

    # ---------------------------------------------------------------------------
    # Niche-aware product templates used when OpenAI is unavailable (mock mode).
    # Each category maps to a list of product "skeletons" that will be customised
    # at runtime with the niche's keywords.
    # ---------------------------------------------------------------------------
    PRODUCT_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "health": [
            {"name": "Premium Whey Protein Isolate", "category": "Health & Fitness", "price": 49.99,
             "affiliate_programs": ["Amazon Associates", "ClickBank", "ShareASale"],
             "description": "High-quality whey protein isolate for muscle building and recovery."},
            {"name": "Organic Greens Superfood Blend", "category": "Health & Fitness", "price": 39.99,
             "affiliate_programs": ["Amazon Associates", "iHerb Affiliates"],
             "description": "Nutrient-rich organic greens powder with 40+ superfoods."},
            {"name": "Smart Fitness Tracker Pro", "category": "Health & Fitness", "price": 129.99,
             "affiliate_programs": ["Amazon Associates", "Best Buy Affiliate"],
             "description": "Advanced fitness tracker with heart rate, sleep, and VO2 max monitoring."},
            {"name": "Adjustable Dumbbell Set", "category": "Health & Fitness", "price": 299.99,
             "affiliate_programs": ["Amazon Associates", "Dick's Sporting Goods Affiliate"],
             "description": "Space-saving adjustable dumbbells from 5 to 52.5 lbs each."},
            {"name": "Keto Meal Replacement Shake", "category": "Health & Fitness", "price": 34.99,
             "affiliate_programs": ["ClickBank", "ShareASale"],
             "description": "Low-carb, high-fat meal replacement designed for ketogenic diets."},
        ],
        "tech": [
            {"name": "Noise-Canceling Wireless Earbuds", "category": "Electronics", "price": 199.99,
             "affiliate_programs": ["Amazon Associates", "Best Buy Affiliate"],
             "description": "Premium ANC earbuds with spatial audio and 30-hour battery life."},
            {"name": "4K Portable Monitor", "category": "Electronics", "price": 349.99,
             "affiliate_programs": ["Amazon Associates", "B&H Photo Affiliate"],
             "description": "15.6-inch 4K portable monitor for remote work and gaming on the go."},
            {"name": "AI-Powered Smart Home Hub", "category": "Electronics", "price": 149.99,
             "affiliate_programs": ["Amazon Associates", "Best Buy Affiliate"],
             "description": "Central smart home controller with built-in AI assistant and Matter support."},
            {"name": "Mechanical Keyboard for Developers", "category": "Electronics", "price": 179.99,
             "affiliate_programs": ["Amazon Associates", "Newegg Affiliate"],
             "description": "Hot-swappable mechanical keyboard with programmable keys and split design."},
            {"name": "Portable SSD 2TB", "category": "Electronics", "price": 119.99,
             "affiliate_programs": ["Amazon Associates", "Newegg Affiliate"],
             "description": "Ultra-fast portable SSD with 2000 MB/s read speeds and USB-C."},
        ],
        "finance": [
            {"name": "Personal Finance Masterclass", "category": "Education", "price": 199.99,
             "affiliate_programs": ["ClickBank", "Udemy Affiliate"],
             "description": "Comprehensive course covering budgeting, investing, and wealth building."},
            {"name": "Robo-Advisor Investment Platform", "category": "Finance", "price": 0,
             "affiliate_programs": ["Betterment Affiliate", "Wealthfront Affiliate"],
             "description": "Automated investment management with tax-loss harvesting and smart rebalancing."},
            {"name": "Budgeting App Premium", "category": "Software", "price": 11.99,
             "affiliate_programs": ["ShareASale", "Impact Affiliate"],
             "description": "AI-powered budgeting app that learns your spending patterns."},
            {"name": "Crypto Portfolio Tracker", "category": "Software", "price": 14.99,
             "affiliate_programs": ["CoinTracker Affiliate", "ShareASale"],
             "description": "Real-time crypto portfolio tracking with tax reporting features."},
            {"name": "High-Yield Savings Account", "category": "Finance", "price": 0,
             "affiliate_programs": ["CJ Affiliate", "Impact Affiliate"],
             "description": "Online savings account offering 5%+ APY with no minimum balance."},
        ],
        "default": [
            {"name": "Premium Online Course Bundle", "category": "Education", "price": 149.99,
             "affiliate_programs": ["ClickBank", "Udemy Affiliate", "ShareASale"],
             "description": "Curated bundle of top-rated online courses for skill development."},
            {"name": "All-in-One Productivity Suite", "category": "Software", "price": 12.99,
             "affiliate_programs": ["AppSumo Affiliate", "ShareASale"],
             "description": "Comprehensive productivity software combining notes, tasks, and collaboration."},
            {"name": "Ergonomic Standing Desk", "category": "Home Office", "price": 499.99,
             "affiliate_programs": ["Amazon Associates", "FlexiSpot Affiliate"],
             "description": "Electric standing desk with memory presets and cable management."},
            {"name": "Wireless Charging Station", "category": "Electronics", "price": 59.99,
             "affiliate_programs": ["Amazon Associates", "Best Buy Affiliate"],
             "description": "3-in-1 wireless charger for phone, watch, and earbuds."},
            {"name": "Premium VPN Service", "category": "Software", "price": 3.99,
             "affiliate_programs": ["NordVPN Affiliate", "ExpressVPN Affiliate", "ShareASale"],
             "description": "Fast, secure VPN service with 5000+ servers in 60 countries."},
        ],
    }

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def run_pipeline(self, app, niche_id: int) -> None:
        """
        Launch the full pipeline in a background thread so the API response
        returns immediately.
        """
        thread = threading.Thread(
            target=self._execute_pipeline,
            args=(app, niche_id),
            daemon=True,
        )
        thread.start()
        logger.info(f"Pipeline started for niche {niche_id} in background thread")

    # -------------------------------------------------------------------------
    # Internal pipeline
    # -------------------------------------------------------------------------

    def _execute_pipeline(self, app, niche_id: int) -> None:
        """Run inside a background thread with its own app context."""
        with app.app_context():
            from src.models.niche import Niche
            from src.models.user import db

            niche = Niche.query.get(niche_id)
            if not niche:
                logger.error(f"Pipeline: niche {niche_id} not found")
                return

            try:
                # --- Phase 1: Discover products ---
                self._update_status(niche, db, "discovering_products",
                                    "Analyzing niche and discovering lucrative products...")
                products = self._discover_products(niche, db)
                logger.info(f"Pipeline: discovered {len(products)} products for niche '{niche.name}'")

                # --- Phase 2: Generate articles ---
                self._update_status(niche, db, "generating_articles",
                                    f"Generating articles for {len(products)} products...")
                articles = self._generate_articles(niche, products, db)
                logger.info(f"Pipeline: generated {len(articles)} articles for niche '{niche.name}'")

                # --- Done ---
                self._update_status(
                    niche, db, "completed",
                    f"Pipeline complete: {len(products)} products, {len(articles)} articles created."
                )

            except Exception as exc:
                logger.exception(f"Pipeline error for niche {niche_id}")
                self._update_status(niche, db, "error", str(exc))

    # -------------------------------------------------------------------------
    # Phase 1 – Product discovery
    # -------------------------------------------------------------------------

    def _discover_products(self, niche, db) -> list:
        """
        Discover products relevant to the niche.  Uses OpenAI when available,
        otherwise falls back to smart mock data that is tailored to the niche.
        """
        from src.models.product import Product
        from src.config import Config

        product_dicts = self._get_niche_products(niche)

        created_products = []
        for pd in product_dicts:
            # Avoid duplicates
            existing = Product.query.filter_by(name=pd["name"], niche_id=niche.id).first()
            if existing:
                created_products.append(existing)
                continue

            product = Product(
                name=pd["name"],
                description=pd["description"],
                category=pd["category"],
                price=pd["price"],
                currency=pd.get("currency", "USD"),
                trend_score=pd.get("trend_score", round(random.uniform(70, 98), 1)),
                search_volume=pd.get("search_volume", random.randint(5000, 150000)),
                competition_level=pd.get("competition_level", niche.competition_level or "medium"),
                affiliate_programs=json.dumps(pd.get("affiliate_programs", [])),
                primary_keywords=json.dumps(pd.get("primary_keywords", [])),
                secondary_keywords=json.dumps(pd.get("secondary_keywords", [])),
                source_url=pd.get("source_url", ""),
                image_url=pd.get("image_url", ""),
                niche_id=niche.id,
            )
            db.session.add(product)
            db.session.flush()
            created_products.append(product)

        db.session.commit()
        return created_products

    def _get_niche_products(self, niche) -> List[Dict[str, Any]]:
        """
        Try OpenAI-powered discovery first; fall back to template-based mock.
        """
        from src.config import Config

        if Config.OPENAI_API_KEY:
            try:
                return self._discover_products_with_ai(niche)
            except Exception as exc:
                logger.warning(f"AI product discovery failed, using templates: {exc}")

        return self._discover_products_from_templates(niche)

    def _discover_products_with_ai(self, niche) -> List[Dict[str, Any]]:
        """Use OpenAI to generate niche-specific product recommendations."""
        import openai
        from src.config import Config

        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

        prompt = f"""You are an expert affiliate marketing strategist. Given the following blog niche, 
recommend exactly 5 highly lucrative products with the best affiliate marketing potential.

Niche: {niche.name}
Description: {niche.description or 'N/A'}
Target Audience: {niche.target_audience or 'N/A'}
Target Keywords: {niche.target_keywords or 'N/A'}
Monetization Strategy: {niche.monetization_strategy or 'Affiliate marketing'}

For each product, provide a JSON object with these exact keys:
- name (string): Product name
- description (string): 2-3 sentence product description
- category (string): Product category
- price (number): Typical price in USD
- affiliate_programs (array of strings): Relevant affiliate networks/programs
- primary_keywords (array of 3 strings): Main SEO keywords
- secondary_keywords (array of 3 strings): Supporting keywords
- source_url (string): Product website URL or empty string
- image_url (string): Empty string

Return ONLY a valid JSON array of 5 product objects, no other text."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a JSON-only API. Respond with valid JSON arrays only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0]
        products = json.loads(raw)
        if not isinstance(products, list) or len(products) == 0:
            raise ValueError("AI returned empty or non-list response")
        return products[:5]

    def _discover_products_from_templates(self, niche) -> List[Dict[str, Any]]:
        """
        Smart template-based product discovery.  Picks the template category
        closest to the niche and enriches products with the niche's keywords.
        """
        niche_lower = (niche.name + " " + (niche.description or "")).lower()
        keywords_str = niche.target_keywords or ""
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

        # Pick the best matching template category
        category_scores = {}
        for cat, hints in {
            "health": ["health", "fitness", "supplement", "workout", "nutrition", "diet", "wellness", "body", "muscle", "weight"],
            "tech": ["tech", "software", "gadget", "electronic", "computer", "phone", "device", "ai", "app", "digital"],
            "finance": ["finance", "money", "invest", "budget", "crypto", "bank", "wealth", "stock", "trading", "income"],
        }.items():
            score = sum(1 for h in hints if h in niche_lower)
            category_scores[cat] = score

        best_cat = max(category_scores, key=category_scores.get)
        if category_scores[best_cat] == 0:
            best_cat = "default"

        templates = self.PRODUCT_TEMPLATES[best_cat]
        products = []
        for tpl in templates:
            product = dict(tpl)
            # Enrich with niche-specific keywords
            base_keywords = keywords[:3] if keywords else [niche.name.lower()]
            product["primary_keywords"] = [
                f"{base_keywords[0]} {product['category'].lower()}",
                f"best {product['name'].lower()}",
                f"{niche.name.lower()} {product['name'].split()[0].lower()}",
            ]
            product["secondary_keywords"] = [
                f"{kw} review" for kw in base_keywords[:3]
            ] if len(base_keywords) >= 1 else [f"{niche.name.lower()} products"]
            product["source_url"] = ""
            product["image_url"] = ""
            product["currency"] = "USD"
            products.append(product)

        return products

    # -------------------------------------------------------------------------
    # Phase 2 – Article generation
    # -------------------------------------------------------------------------

    def _generate_articles(self, niche, products, db) -> list:
        """Generate an SEO-optimized article for each product."""
        from src.models.product import Article
        from src.services.content_generator import ContentGenerator

        generator = ContentGenerator()
        created_articles = []

        for product in products:
            # Skip if article already exists
            existing = Article.query.filter_by(product_id=product.id, niche_id=niche.id).first()
            if existing:
                created_articles.append(existing)
                continue

            product_data = product.to_dict()
            # Ensure the niche context is available to the generator
            product_data["niche_name"] = niche.name
            product_data["niche_keywords"] = niche.target_keywords or ""

            article_data = generator.generate_article(product_data)

            article = Article(
                title=article_data["title"],
                content=article_data["content"],
                meta_description=article_data.get("meta_description", ""),
                keywords=json.dumps(article_data.get("keywords", [])),
                product_id=product.id,
                niche_id=niche.id,
                seo_score=article_data.get("seo_score", 0),
                readability_score=article_data.get("readability_score", 0),
                word_count=len(article_data.get("content", "").split()),
                affiliate_links_count=article_data.get("affiliate_links_count", 0),
                status="draft",
            )
            db.session.add(article)
            db.session.flush()
            created_articles.append(article)

            # Update pipeline message with progress
            niche.pipeline_message = (
                f"Generated {len(created_articles)}/{len(products)} articles..."
            )
            db.session.commit()

        return created_articles

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _update_status(niche, db, status: str, message: str) -> None:
        niche.pipeline_status = status
        niche.pipeline_message = message
        db.session.commit()
        logger.info(f"Pipeline [{niche.name}]: {status} — {message}")

# Active Context — automated_blog_platform

> Updated 2026-06-01.

## Current Focus

Standing up the **first live blog**: high-ticket home-office / home-based-
business products sold on Amazon, tagged with Associates store `deskcred-20`,
publishing to `https://deskcred-com.ghost.io`. Niche angle is being chosen
from currently-trending high-ticket home-office categories.

In flight on branch `chore/cleanup-and-amazon-deploy`:

1. Repo hygiene — added `redis` (and pinned `openai`) to
   `requirements.txt`; untracking `.DS_Store` / `dump.rdb`; removing
   `repomix-output.xml` and ignoring `.kilo/`.
2. Stale-doc cleanup — this memory-bank rewritten to current reality;
   `WARP.md` deleted (superseded by `RUN.md`).
3. Amazon Associates wiring — ensure discovered products receive
   `affiliate_url` + `tracking_id=deskcred-20` so CTAs attribute correctly.
4. First real article generated and published end-to-end through the
   PR #6 human-review flow.

## Recent State

- PRs #1–#6 (incl. #5a/#5b/#6.4) are merged on `main`.
- `chore/migrations-env-imports-and-pyc-cleanup` added model imports to
  `migrations/env.py` and stopped tracking `.pyc`.
- Ghost is configured in `.env` (`deskcred-com.ghost.io`) with admin +
  content keys. OpenAI / Tavily / Serper keys present.

## Active Decisions

- **Amazon-only monetization for now.** Single affiliate network
  (Associates, `deskcred-20`); second network deferred to PR #7.
- **`USE_MOCK_DATA` must be `False`** for real generation, with API keys
  set. Watch per-article budget (PR #3 circuit breaker).
- **Human-in-the-loop publish only.** No autonomous publishing.

## Next Steps

- Flip `USE_MOCK_DATA` to `False`; confirm AI product discovery returns
  Amazon products with affiliate URLs + the `deskcred-20` tag.
- Run the test suite, then a live Ghost smoke draft.
- Create the niche, run the pipeline, review + publish one article.
- Accumulate toward ≥20 published articles to unlock PR #7 (Feedback Loop).

## Open Questions

- Exact niche sub-angle (trending-driven) and the initial product set.
- Whether to enrich AI discovery with real Amazon product URLs/ASINs vs.
  hand-curating the first batch.

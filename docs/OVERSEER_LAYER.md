# Overseer Layer (PR #21)

A supervisory control plane that runs the automated blog platform, finds what is broken or underperforming, and fixes what is safe to fix. Everything else goes to a human or to a pull request.

The overseers never write articles and never publish. The CrewAI `BlogCreationFlow` still does the writing, and the human review gate (PR #6) is still the only way to publish.

## Why a layer and not more agents

The platform already has a writer pipeline (CrewAI), a judge (the four-axis Editor), and a statistical feedback loop (PR #7). What it lacked was something that watches the whole system end to end and asks, every 30 minutes, "is this blog actually on track to earn money, and if not, why?" That job needs deterministic checks over the database, a memory of what it already flagged, and a hard line between safe automatic fixes and decisions a human should make. A rules-based layer does that better than another LLM agent, and every check is unit-testable.

## Roster

| Overseer | Business function it embodies | What it watches |
|---|---|---|
| `chief` | Orchestration and budget | Runs the loop, prioritises findings, projects the month's spend against the $100 cap |
| `systems` | Custom Bot Development | Route groups that failed to load at startup, stuck or crashed pipeline runs, missing config, unmetered LLM spend, broken integrations, superseded files |
| `content` | Programmatic Content Agency | Review-queue backlog, editorial axes that block more than 50% of articles, stale or thin live posts |
| `market` | Automated E-commerce Research | Products below the $500 MSRP floor, products with no affiliate URL or tracking ID, niche pipelines in error |
| `revenue` | Affiliate Funnel Management | Live articles with no affiliate link, tracking-ID collisions, missing earnings data, clicks without sales, winners worth amplifying |
| `audience` | 24/7 Lead Generation | Articles with no Search Console impressions after 7 days, articles not yet shared to the Facebook Page |
| `compliance` | Cross-cutting guardrail | Publish-gate bypass, missing Amazon Associate statement and link-level disclosure, paid ads pointing directly at Amazon |

## The loop

```
sense ──► diagnose ──► propose ──► gate ──► apply ──► verify
 (all 7     (typed       (action     (auto-safe   (handler    (next cycle: finding
 overseers)  findings,    attached     runs; the    returns     stops firing → resolved,
             deduped by   to each      rest wait    result +    applied action → verified)
             fingerprint) finding)     for human)   undo recipe)
```

- Findings are deduplicated by fingerprint while open. A repeat increments `occurrences` instead of creating a new row.
- Each cycle is recorded in `overseer_runs` with counts and a top-10 summary.
- If one overseer crashes, the others still run, and the crash becomes an `overseer_crashed` engineering finding.

## Risk gate

Only these handlers may run without approval (`AUTO_SAFE` in `src/overseers/actions.py`):

| Auto-safe action | Effect | Undo |
|---|---|---|
| `notify_human` | Surfaces the finding | None needed |
| `mark_article_error` | Stuck article becomes `error` so it is visible and retryable | Previous status stored |
| `generate_improvement_proposals` | Creates pending PR #7 proposals; it does not edit content | Dismiss proposals |
| `refresh_performance` | Recomputes the 28-day roll-up | Idempotent |
| `pause_pipeline` | Blocks new flows via `CostMeter.assert_can_start_flow` | Human resume |
| `reject_action` | Compliance auto-rejects a non-compliant proposal | Re-propose |

An overseer cannot promote itself: `effective_risk()` downgrades any other kind to `approval`.

The following are never automatic by design: publishing or unpublishing, spending money, posting publicly, and code changes.

| Approval-gated action | Effect |
|---|---|
| `retry_article` | Resets to stage 0 and re-runs the flow. Enforces the GOALS.md retry budget of 2. |
| `archive_article` | Soft-delete (disposition after the retry budget is used up) |
| `unpublish_article` | Ghost post back to draft (for publish-gate violations) |
| `resume_pipeline` | Lifts an overseer pause |
| `engineering_ticket` | On approval, lands in `GET /api/overseer/engineering-queue` for a coding agent to turn into a PR |
| `create_meta_campaign_draft` | Creates a PAUSED Meta campaign pointing at the blog article |
| `distribute_to_facebook_page` | Posts the article link to the Facebook Page |

## Meta AI integration

| Capability | Module | Notes |
|---|---|---|
| Muse Spark text | `src/services/meta_ai/model_client.py` | Uses the OpenAI-compatible `https://api.meta.ai/v1/chat/completions` endpoint. Metered through `CostMeter` at $1.25/$4.25 per 1M tokens. |
| CrewAI writer on Muse Spark | `core/crewai_system/llm_providers.py` | Set `CONTENT_LLM_PROVIDER=meta` to switch the author and monetization agents. The default stays OpenAI. |
| Muse Image | `MetaModelClient.generate_image` | Billed as a $0.01 flat-fee `CostEvent`. The response is tagged `ai_generated=true`. |
| Contributor tier | Refused by default | About 12x cheaper, but Meta uses your prompts to improve its products. Opt in with `META_ALLOW_CONTRIBUTOR_TIER=true`. |
| Campaign drafts | `marketing_client.create_campaign_draft` | Always `status=PAUSED`. Code can only pause or archive, never activate. Graph API version defaults to `v26.0`. |
| Conversions API | `send_conversion_event` | Sends the newsletter signup as a `Lead` event. Email is SHA-256 hashed. `event_id` deduplicates against the browser Pixel. |
| Page distribution | `post_link_to_page` | Feeds the GOALS.md "distribution routine fires at least once" requirement |

### Amazon rule for paid traffic

Amazon's April 14, 2026 policy update disqualifies purchases referred by paid or boosted ads linking to Amazon. Paid search may send users to your own site, but not directly to Amazon or through a redirecting link. The overseer layer enforces this in three places:

1. The campaign handler refuses Amazon destinations.
2. The compliance overseer auto-rejects any proposed draft that points at Amazon.
3. Only winners with a `published_url` on the blog get proposed.

## Revenue signal fix

`AmazonAssociatesProvider` calls `associates-report.amazon.<tld>`, which is not a documented Amazon API. Amazon's programmatic access is now the Creators API, which uses OAuth 2.0 and requires 10 qualifying sales in the past 30 days. Until the blog qualifies, download a report from Associates Central and post it:

```bash
curl -X POST "http://127.0.0.1:5000/api/overseer/revenue/associates-csv?date=2026-10-07" \
  -H "X-Overseer-Token: $OVERSEER_API_TOKEN" --data-binary @tracking-id-summary.csv
```

Per-article attribution requires one tracking ID per article (or per cluster). The `tracking_id_collision` finding flags articles that share `deskcred-20`.

## Operating it

```bash
# one cycle, now
curl -X POST http://127.0.0.1:5000/api/overseer/run -H "X-Overseer-Token: $OVERSEER_API_TOKEN" -d '{}'
# what's open
curl "http://127.0.0.1:5000/api/overseer/findings?severity=critical"
# approve + apply an action
curl -X POST http://127.0.0.1:5000/api/overseer/actions/42/approve -H "X-Overseer-Token: $OVERSEER_API_TOKEN" -d '{"by":"gideon"}'
# hand approved engineering tickets to a coding agent
curl "http://127.0.0.1:5000/api/overseer/engineering-queue?format=md"
```

### Grok Bot routines (external operators)

The in-app overseers are deterministic. Grok Bot routines add the open-ended research and coding work on top, through the same API and the same gate:

| Routine | Cadence | Does |
|---|---|---|
| Overseer pulse | Every 30 min | `POST /run`. Posts any critical findings to Slack. |
| Engineering desk | Daily | Reads `/engineering-queue?format=md` and opens one branch and draft PR per ticket. Never merges. |
| Market scout | Daily | Researches current price, availability and successor models for each live product (web and X search). Proposes product updates. |
| Revenue import | Weekly | Downloads the Associates Central report and posts it to `/revenue/associates-csv` (a human handles any verification step) |

Routines must stay at least 5 minutes apart, with a maximum of 50 per Bot.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OVERSEER_INTERVAL_MINUTES` | `30` | Scheduler cadence. `0` disables it. |
| `OVERSEER_AUTO_APPLY` | `true` | Global kill switch for auto-safe actions |
| `OVERSEER_API_TOKEN` | unset | Required header for mutating endpoints when set |
| `SITE_AFFILIATE_DISCLOSURE_PRESENT` | `false` | Set `true` once the Ghost theme carries the Amazon Associate statement |
| `CONTENT_LLM_PROVIDER` | `openai` | `meta` switches the content crew to Muse Spark |
| `META_MODEL_API_KEY`, `META_TEXT_MODEL`, `META_IMAGE_MODEL` | `muse-spark-1.3`, `muse-image-1.0` | Meta Model API |
| `META_AD_ACCOUNT_ID`, `META_SYSTEM_USER_TOKEN`, `META_PIXEL_ID` | unset | Marketing API and Conversions API |
| `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN` | unset | Page distribution |
| `META_GRAPH_API_VERSION` | `v26.0` | Graph and Marketing API version |

## Sources

- Meta Model API models, endpoints and pricing: https://dev.meta.ai/docs/overview, https://dev.meta.ai/products/meta-model-api
- Graph/Marketing API v26.0 (July 29, 2026): https://www.blotato.com/blog/facebook-api-pricing
- Campaign creation with `status=PAUSED` and `special_ad_categories`: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
- Conversions API `/events` endpoint: https://developers.facebook.com/docs/marketing-api/conversions-api/using-the-api/
- Amazon April 14, 2026 policy changes: https://affiliate-program.amazon.com/help/operating/compare
- Amazon paid-search routing and Redirecting Links: https://affiliate-program.amazon.com/help/operating/policies
- Amazon Associate statement (Operating Agreement section 5): https://affiliate-program.amazon.com/help/operating/agreement
- Link-level FTC disclosure guidance: https://affiliate-program.amazon.com/help/node/topic/GHQNZAU6669EZS98
- Creators API prerequisites: https://affiliate-program.amazon.com/creatorsapi/docs/
- PA-API 5 deprecation: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation
- Associates report downloads (CSV/XML): https://affiliate-program.amazon.co.uk/help/node/topic/GQ5FS7J76MT59WLW
- Grok Bot routines: https://docs.x.ai/grok-bot/skills-routines-and-automations

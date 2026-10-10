# Meta AI Integration (PR #22)

This PR is stacked on PR #21, the overseer layer. It adds Meta's content models and advertising APIs, and connects them to the overseers through the same approval gate. It is opt-in: with no `META_*` variables set, the platform behaves exactly as it does on PR #21.

## Content creation

| Capability | Module | Notes |
|---|---|---|
| Muse Spark text | `src/services/meta_ai/model_client.py` | Calls the OpenAI-compatible `https://api.meta.ai/v1/chat/completions` endpoint. Every call goes through `CostMeter` at $1.25 input and $4.25 output per 1M tokens. |
| Author agent on Muse Spark | `core/crewai_system/llm_providers.py`, `src/overseers/author_model_gate.py` | The author agent moves to Muse Spark automatically once the overseers verify the whole system (see below). The monetization specialist and research crews stay on the default. `CONTENT_LLM_PROVIDER=meta` still forces the whole content crew to Meta. CrewAI success callbacks record Muse Spark token usage against the active article at `crewai_generation`. |
| Muse Image | `MetaModelClient.generate_image` | Recorded as a $0.01 flat-fee `CostEvent` through `CostMeter.record_flat`. Responses are tagged `ai_generated=true`. |
| Contributor tier | Refused by default, both when the client is built and on each `chat()` call | About 12x cheaper, but Meta uses the prompts to improve its products. Opt in with `META_ALLOW_CONTRIBUTOR_TIER=true`. |

## Author-model gate

Decision of Oct 9, 2026: use Muse Spark for the author agent once the whole system has been verified to work, and the current default until then. The Chief overseer checks the gate on every cycle. The author switches only when all of these have held for `AUTHOR_MODEL_STABLE_HOURS` (default 24):

| Check | Passes when |
|---|---|
| `overseers_healthy` | No overseer crashed this cycle |
| `no_open_critical_or_high_findings` | No open critical or high finding anywhere |
| `live_article_on_ghost` | A published article has a live URL (GOALS.md Definition of Done) |
| `distribution_fired` | A Facebook Page post was applied (Definition of Done) |
| `search_impressions_recorded` | Search Console impressions exist (Definition of Done) |
| `generation_spend_metered` | `crewai_generation` cost events exist, so the $100 cap sees real spend |
| `affiliate_earnings_ingested` | At least one affiliate earnings row was imported |
| `meta_api_key_configured` | `META_MODEL_API_KEY` is set |

Default-model generation spend is not metered yet (overseer finding `llm_spend_unmetered`), so the gate cannot pass until that engineering ticket is fixed. That is intended: the switch makes each article about 7x more expensive, so the budget guard has to see it first.

The switch is sticky, so a later fault does not change models mid-run. `GET /api/overseer/author-model` shows the current provider and every check. `POST /api/overseer/controls/author-model/revert` puts the author back on the default and locks the gate. `POST /api/overseer/controls/author-model/rearm` clears the lock. Both need `X-Overseer-Token`. `AUTHOR_LLM_PROVIDER` overrides the gate: `gated` (default), `default` (never switch), or `meta` (switch now).

## Advertising and distribution

| Capability | Module | Notes |
|---|---|---|
| Campaign drafts | `MetaMarketingClient.create_campaign_draft` | Always created with `status=PAUSED`. Objectives are limited to traffic, leads, engagement and awareness. Code can only pause or archive a campaign, never activate one. |
| Conversions API | `POST /api/webhooks/ghost/newsletter-signup` | A Ghost `member.added` webhook sends a `Lead` event with the request user agent and a stable ID based on the Ghost member ID (or normalized email when absent). Configure Ghost's webhook secret to match `GHOST_WEBHOOK_SECRET`; include `member.email` and preferably `member.id` in the JSON body. `event_source_url` is optional and defaults to `GHOST_API_URL`. Email is SHA-256 hashed by the client. |
| Page distribution | `post_link_to_page` | Meets the GOALS.md requirement that the distribution routine fires at least once per post |

The Graph API version defaults to `v26.0` and can be changed with `META_GRAPH_API_VERSION`.

## How the overseers use it

| Overseer | Finding | Action | Risk |
|---|---|---|---|
| Revenue | `amplify_winner`: an article in the `winner` performance tier, with a live blog URL | `create_meta_campaign_draft` aimed at the blog article | Needs approval |
| Audience | `not_distributed`: a live article not yet shared to the Page | `distribute_to_facebook_page` | Needs approval |
| Audience | `distribution_unconfigured`: articles are live but only one Page credential is set | `notify_human` | Auto |
| Compliance | `paid_ad_links_to_amazon`: a proposed or approved campaign draft points at Amazon | `reject_action` | Auto |
| Systems | `missing_config`: `CONTENT_LLM_PROVIDER=meta` is set, or the author agent has switched, but `META_MODEL_API_KEY` is not | `notify_human` | Auto |

Neither Meta action is in `AUTO_SAFE`. `effective_risk()` downgrades both to `approval`, and a test pins this behavior.

## Amazon rule for paid traffic

Amazon's April 14, 2026 update disqualifies purchases referred by paid or boosted ads that link to Amazon. Paid search may send users to your own site, but not directly to Amazon or through a redirecting link. This PR enforces that in three places:

1. The campaign handler refuses Amazon destinations.
2. The compliance overseer auto-rejects any pending draft that points at Amazon.
3. Only winners with a `published_url` on the blog are proposed.

Whether a social ad that lands on a blog article with Amazon links is fully safe is not spelled out in the policy. Confirm with Associates support before scaling paid traffic to Amazon-linked articles. Newsletter Lead campaigns and direct-merchant pages are the safer first targets.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `CONTENT_LLM_PROVIDER` | `openai` | Set to `meta` to force the whole content crew to Muse Spark |
| `AUTHOR_LLM_PROVIDER` | `gated` | Author agent: `gated` switches after verification, `default` never switches, `meta` switches now |
| `AUTHOR_MODEL_STABLE_HOURS` | `24` | How long every verification check must hold before the author switches |
| `META_MODEL_API_KEY` | unset | Meta Model API key |
| `META_MODEL_API_BASE` | `https://api.meta.ai/v1` | Model API base URL |
| `META_TEXT_MODEL`, `META_IMAGE_MODEL` | `muse-spark-1.3`, `muse-image-1.0` | Model IDs |
| `META_ALLOW_CONTRIBUTOR_TIER` | `false` | Allows `-contributor` models |
| `META_AD_ACCOUNT_ID`, `META_SYSTEM_USER_TOKEN` | unset | Marketing API. Both must be set before `amplify_winner` can fire. |
| `META_PIXEL_ID` | unset | Conversions API |
| `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN` | unset | Page distribution |
| `GHOST_WEBHOOK_SECRET` | unset | Secret used to verify the Ghost member webhook signature |
| `META_GRAPH_API_VERSION` | `v26.0` | Graph and Marketing API version |

## Sources

- Meta Model API models and endpoints: https://dev.meta.ai/docs/overview
- Meta Model API pricing and data use by tier: https://dev.meta.ai/products/meta-model-api
- Graph and Marketing API v26.0 release (July 29, 2026): https://www.blotato.com/blog/facebook-api-pricing
- Campaign creation with `status=PAUSED` and `special_ad_categories`: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group
- Conversions API `/events` endpoint: https://developers.facebook.com/docs/marketing-api/conversions-api/using-the-api/
- Meta AI ad labels: https://www.meta.com/help/artificial-intelligence/355108217670024/
- Amazon April 14, 2026 policy changes: https://affiliate-program.amazon.com/help/operating/compare
- Amazon paid-search routing and Redirecting Links: https://affiliate-program.amazon.com/help/operating/policies

# Product Goal — automated_blog_platform

## Mission
Establish and scale a network of high-ticket affiliate media properties
to maximize Monthly Recurring Revenue (MRR) and owned-audience growth,
using an autonomous content flywheel.

## Scope of Autonomy
The system is authorized to:

1. Research trending products with MSRP ≥ $500 using real-time market data
   (Tavily, SerperDev, Firecrawl).
2. Publish SEO-optimized, long-form articles via **Ghost Headless CMS API**,
   prioritizing Buyer-Intent keywords.
3. Execute a multi-channel distribution routine per post (X, LinkedIn, Email).
4. Continuously audit published content for freshness, broken links, and
   conversion performance, using Google Search Console and affiliate
   dashboard analytics as the feedback signal.

## Primary KPIs
- **Organic Traffic Growth** — GSC impressions + clicks, 28-day trailing.
- **Newsletter Opt-in Rate** — % of sessions that convert to subscribers.
- **Earnings Per Click (EPC)** — by offer, per article.

## Operating Constraints (hard rules for the flow)
- **Monthly API + hosting budget: $100 hard cap**, enforced per-article
  via a token/cost circuit breaker in `BlogCreationFlow` (PR #3).
- **Per-article retry budget: 2 cycles**, then automated disposition
  (retire if monetization-blocked on a low-EPC offer; otherwise swap the
  affiliate offer and restart Stage 1).
- **Editorial axes are independent** — Content, SEO/UX, Monetization,
  Compliance. Rejection on one axis only re-invokes the crew responsible
  for that axis; never a blanket rewrite (PR #2).
- **Stage handoff is by database record, never by filesystem path**
  (PR #3).
- **Publisher refuses to publish unless `editorial_verdict == "PUBLISH"`**
  — enforced at the API layer in `routes/publisher.py` (shipped in PR #1).

## Definition of Done — First Blog
One niche selected. One article generated end-to-end through all 5 stages.
Published to Ghost. Live URL stored on the Article record. Distribution
routine fires at least once. GSC impressions recorded after 7 days.

## Non-goals (for now)
- WordPress publishing (deprecated).
- Multi-tenant SaaS (deferred to post-first-revenue).
- Video/TikTok distribution (deferred).

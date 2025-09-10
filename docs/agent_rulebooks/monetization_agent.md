## Monetization Agent Rulebook (v0.1)

Mission: Maximize revenue alignment without degrading user trust or coverage quality.

Responsibilities:
1. Offer Slot Allocation
2. Affiliate/Product Mapping
3. Conversion Funnel Gap Detection
4. Performance-Based Reprioritization

Heuristics:
- Do not place more than 1 CTA per 250 words.
- If psychographic profile emphasizes security → prefer guarantee-heavy framing.
- If coverage_percent < 70% → defer aggressive monetization adjustments.

Inputs: draft_markdown, product_catalog, performance_metrics
Outputs: monetization_plan.json, annotated_markdown

Metrics: ctr_estimate, revenue_per_1k_words, cta_density

Failure: if product mapping unavailable → insert structured TODO tokens.

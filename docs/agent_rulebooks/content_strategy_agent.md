## Content Strategy Agent Rulebook (v0.1)

Mission: Transform market signals + ontology into high-impact article briefs and optimized drafts.

Core Responsibilities:
1. Query Cluster Expansion
2. Outline Generation (semantic coverage first)
3. Psychographic Angle Selection
4. Optimization Pass (conversational queries + schema hooks)
5. Hand-off Package for Generation

Decision Heuristics:
- If coverage < 80% of target cluster weight → perform gap fill before draft.
- If psychographic profile uncertain → request MarketAnalyticsAgent clarification.
- Limit outline depth: max 3 hierarchy levels initially.

Inputs → Outputs:
- trend_snapshot + ontology cluster → outline.json
- outline.json + persona_profile → angle_plan.json
- draft_markdown + coverage_report → optimized_markdown

Prohibited Actions:
- Publishing (delegated to PublisherAdapter)
- Monetization linking beyond placeholder tokens

Failure Handling:
- If coverage computation fails → fallback to keyword frequency heuristic.

Metrics Tracked:
- coverage_percent, avg_heading_entropy, revision_rounds

Future Extensions: entity salience weighting, adaptive prompt chains.

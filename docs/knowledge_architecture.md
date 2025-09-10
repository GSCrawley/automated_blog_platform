## Knowledge Architecture & Ontology (Initial Draft)

Purpose: Provide a normalized structure for classifying optimization knowledge so agents can retrieve the right tactical guidance with low ambiguity.

### 1. Core Ontology Layers
1. Category (broad domain of leverage)
2. Lever (actionable optimization vector inside a category)
3. Tactic (concrete method / pattern)
4. Pattern Artifact (prompt template, schema snippet, KPI formula)
5. Evidence Metric (measurement that validates tactic impact)

### 2. Current Category Set (v1)
- AI Search Optimization
- Psychographic Targeting
- Platform Optimization
- Community & Engagement
- Content Multiplication
- Analytics & Feedback
- Technical Delivery
- Monetization

### 3. Lever Examples
| Category | Lever | Description |
|----------|-------|-------------|
| AI Search Optimization | Conversational Query Coverage | Ensure article surfaces for natural language queries & multi-intent chains |
| Psychographic Targeting | Motivation Trigger Mapping | Align copy blocks to intrinsic motivators (identity, mastery, status, security) |
| Platform Optimization | Format Native Adaptation | Reshape core narrative to native affordances (short-form hook density, vertical framing, etc.) |
| Community & Engagement | Feedback Loop Seeding | Insert structured CTA anchoring comments, shares, or UGC prompts |
| Content Multiplication | Atomization Sequencing | Systematically derive derivative assets in impact-maximizing order |
| Analytics & Feedback | Semantic Coverage Scoring | Score generated content vs. ontology concepts and query clusters |
| Technical Delivery | Performance Budget Enforcement | Keep CLS, LCP, INP within thresholds using build-time audits |
| Monetization | Offer Alignment Mapping | Match product/offers to intent stage & psychographic profile |

### 4. Tactic Record Schema
```json
{
  "id": "tactic.semantic_coverage.scoring.v1",
  "category": "Analytics & Feedback",
  "lever": "Semantic Coverage Scoring",
  "name": "Compute Coverage Delta",
  "description": "Compare extracted entities & intent phrases from draft vs. target cluster graph to produce % coverage and missing nodes list.",
  "applies_to": ["ContentStrategyAgent", "PerformanceAnalyticsAgent"],
  "inputs": ["draft_article_markdown", "cluster_graph", "entity_extraction"],
  "outputs": ["coverage_percent", "missing_nodes", "priority_fill_list"],
  "metrics": ["coverage_percent", "avg_node_weight_covered"],
  "confidence_basis": "Heuristic graph comparison (future: embed similarity weighting)",
  "status": "draft"
}
```

### 5. Agent Mapping (High-Level)
- ContentStrategyAgent: AI Search Optimization, Psychographic Targeting, Content Multiplication (outline phase selection only), Analytics (coverage pre-check)
- MonetizationAgent: Monetization, Psychographic Targeting (offer framing), Analytics (conversion deltas)
- PerformanceAnalyticsAgent: Analytics & Feedback, Technical Delivery, AI Search Optimization (visibility signals)
- PublisherAdapter (future): Technical Delivery, Community & Engagement (distribution triggers)
- MarketAnalyticsAgent: Feeds upstream ontology expansions (discovers emergent levers)

### 6. Retrieval Metadata Plan
Each chunk annotated with: category, lever, applies_to (agent list), tags (freeform), priority (1–5), version.

### 7. Incremental Roadmap
1. (Now) Add metadata extraction placeholders in knowledge base.
2. Encode initial 12–20 high-value tactics into JSON (later persistent store).
3. Add embedding layer & hybrid scoring fusion.
4. Introduce semantic coverage evaluation service.
5. Add feedback loop storing tactic usage + outcome metrics.

### 8. Open Questions
- Best minimal embedding model? (Likely local Instructor or OpenAI small embedding to start.)
- Store ontology in flat JSON vs. lightweight SQLite table? (Start JSON → migrate when write frequency increases.)

---
Status: Initial draft committed (v0.1). Will evolve alongside Phase 9 tasks.

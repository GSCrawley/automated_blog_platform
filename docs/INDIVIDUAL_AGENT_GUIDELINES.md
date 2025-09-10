### Once we start working on the agentic core of the application, we need to work out the agentic workflow in terms of each agent's role in creating the most sucessful blog possible - this will be the most important aspect of the application and will require a lot of thought and planning - each stage of the system should be developed and tested in isolation and then integrated with the other stages to create a cohesive and functional system.

### Each agent is going to have its own unique 'rulebook' containing the guidelines that it must follow in order to make the best possible decisions and take the most optimal actions


1. Market Research Agent
### see market research agent framework for details. follow the example of the market research agent framework to create a similar framework for each agent, tailored of course to that agent's specific role in the system. 

2. Content Strategy Agent

Rulebook reference: `docs/agent_rulebooks/content_strategy_agent.md`

Initial Focus Areas:
- Query Cluster Coverage (Ontology → Outline)
- Psychographic Angle Selection
- Semantic Gap Detection
- Outline → Prompt Packaging

Success Metrics (early): coverage_percent >= 80%, heading uniqueness ratio >= 0.6

3. Publisher Adapter Framework - Generic publishing abstraction replacing the deprecated WordPress Manager role

4. Monetization Agent

Rulebook reference: `docs/agent_rulebooks/monetization_agent.md`

Initial Focus Areas:
- Offer Slot Allocation & Density Control
- Psychographic Offer Framing
- Conversion Funnel Gap Analysis

Success Metrics: cta_density <= 0.004 per char, projected_revenue / 1k words baseline uplift

5. Performance Analytics Agent

Rulebook reference: `docs/agent_rulebooks/performance_analytics_agent.md`

Initial Focus Areas:
- Coverage Drift Detection
- Engagement & Scroll Depth Correlation
- Anomaly Detection & Alerting

Success Metrics: mean_detection_lag < 10m, false_positive_rate < 5%

6. Orchestrator Agent

### 

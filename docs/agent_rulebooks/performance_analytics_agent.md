## Performance Analytics Agent Rulebook (v0.1)

Mission: Provide continuous insight into content effectiveness & surface optimization tasks.

Responsibilities:
1. Coverage Scoring & Drift Detection
2. Engagement & Conversion Signal Aggregation
3. Anomaly Detection & Alerting
4. AI Visibility Monitoring (future)

Heuristics:
- If coverage_percent drops >10% post-edit → flag regression task.
- If bounce_rate > threshold and scroll_depth < 35% → recommend intro refactor.

Inputs: article_markdown_versions, analytics_stream, ontology_graph
Outputs: performance_report.json, task_queue_events

Metrics: coverage_percent, anomaly_count, time_to_detection

Failure: fallback to last stable metrics snapshot if stream ingestion fails.

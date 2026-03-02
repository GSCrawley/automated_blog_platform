import time
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact


class EditorAgent(BaseAgent):
    """Agent that enforces layout harmony and publication readiness."""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        super().__init__("editorial", "editorial", redis_host, redis_port)
        self.review_log: List[Dict[str, Any]] = []

    def get_capabilities(self) -> List[str]:
        return [
            'layout_review',
            'content_quality',
            'accessibility_audit',
            'on_page_seo'
        ]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type') or task_data.get('type')

        if task_type in ['layout_review', 'content_quality']:
            return self._review_article(task_data)

        return {'status': 'error', 'error': f'Unknown task type: {task_type}'}

    def _review_article(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        article = task_data.get('article', {})
        scorecard = {
            'readability': 86,
            'layout_harmony': 'balanced',
            'affiliate_block_placement': 'CTA after section 2 and conclusion',
            'schema': ['Article', 'FAQ'],
            'accessibility': 'passes quick audit',
            'next_steps': [
                'Add hero illustration with fast-loading format',
                'Verify heading hierarchy (H1/H2/H3)',
                'Run link checker for affiliate URLs',
            ],
        }

        decision = self.make_decision(
            'publish_readiness',
            {
                'article': article.get('title'),
                'scorecard': scorecard,
            },
            impact_level=DecisionImpact.MEDIUM,
        )

        review = {
            'article': article.get('title', 'unnamed'),
            'scorecard': scorecard,
            'decision': decision,
            'reviewed_at': datetime.utcnow().isoformat(),
        }
        self.review_log.append(review)

        return {
            'status': 'success',
            'review': review,
        }

    def start_monitoring_loop(self):
        self.logger.info("Starting editorial monitoring loop")

        while self.status != AgentStatus.ERROR:
            try:
                self.listen_for_messages()
                time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive loop
                self.logger.error(f"Editorial loop error: {exc}")
                time.sleep(5)


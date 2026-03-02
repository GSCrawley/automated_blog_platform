import time
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact


class AuthorAgent(BaseAgent):
    """Agent that drafts and repurposes articles for the selected niche."""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        super().__init__("authoring", "authoring", redis_host, redis_port)
        self.last_outline: Dict[str, Any] | None = None

    def get_capabilities(self) -> List[str]:
        return [
            'content_generation',
            'content_replication',
            'outline_planning',
            'research_synthesis'
        ]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type') or task_data.get('type')

        if task_type in ['content_generation', 'draft_article']:
            return self._generate_article(task_data)
        if task_type == 'outline_planning':
            return self._plan_outline(task_data)

        return {'status': 'error', 'error': f'Unknown task type: {task_type}'}

    def _plan_outline(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        niche = task_data.get('niche') or 'general'
        product = task_data.get('product', {})
        outline = {
            'title': f"{product.get('name', niche)} Review: Profitability & Workflow Impact",
            'sections': [
                'Pain points and urgency for automation',
                'Why this product wins vs. status quo',
                'Implementation steps and integrations',
                'Pricing, ROI, and affiliate positioning',
                'Comparable tools and upgrade paths',
            ],
            'ctas': ['Try the workflow demo', 'Start free trial', 'Book optimization consult'],
        }

        self.last_outline = outline
        return {
            'status': 'success',
            'outline': outline,
            'planned_at': datetime.utcnow().isoformat(),
        }

    def _generate_article(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        product = task_data.get('product', {})
        niche = task_data.get('niche', 'general')
        now = datetime.utcnow().isoformat()

        article = {
            'title': f"{product.get('name', niche)}: Automating Profitability in {niche}",
            'summary': 'Drafted from research agents with CTA-ready hooks.',
            'sections': [
                'Market urgency and profitability snapshot',
                'Feature deep dive with automation examples',
                'Affiliate-ready placements and compliance reminders',
                'Conversion booster FAQs and objections',
            ],
            'word_count': 1200,
            'niche': niche,
            'product': product.get('name'),
            'metadata': {
                'status': 'draft',
                'keywords': task_data.get('keywords', []),
                'seo_score': 82,
            },
        }

        decision = self.make_decision(
            'content_release',
            article,
            impact_level=DecisionImpact.LOW,
        )

        return {
            'status': 'success',
            'article': article,
            'decision': decision,
            'generated_at': now,
        }

    def start_monitoring_loop(self):
        self.logger.info("Starting authoring monitoring loop")

        while self.status != AgentStatus.ERROR:
            try:
                self.listen_for_messages()
                time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive loop
                self.logger.error(f"Authoring loop error: {exc}")
                time.sleep(5)


import time
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact


class AffiliateOpsAgent(BaseAgent):
    """Agent that validates affiliate readiness and integration quality."""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        super().__init__("affiliate_ops", "affiliate_ops", redis_host, redis_port)
        self.integration_audits: List[Dict[str, Any]] = []

    def get_capabilities(self) -> List[str]:
        return [
            'affiliate_validation',
            'compliance_review',
            'tracking_setup',
            'content_monetization'
        ]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type') or task_data.get('type')

        if task_type == 'affiliate_validation':
            return self._audit_affiliate_setup(task_data)
        if task_type == 'tracking_setup':
            return self._prepare_tracking(task_data)

        return {'status': 'error', 'error': f'Unknown task type: {task_type}'}

    def _audit_affiliate_setup(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        niche = task_data.get('niche')
        product = task_data.get('product') or {}
        audit = {
            'niche': niche,
            'product': product.get('name', 'unspecified'),
            'link_health': 'pending',
            'cookie_window': '30-90 days',
            'payout_model': 'recurring SaaS',
            'actions': [
                'Verify subid/UTM passthrough across CTA buttons',
                'Add disclosure block to hero and footer',
                'Enable link checker to run nightly',
            ],
        }

        audit_decision = self.make_decision(
            'affiliate_compliance',
            audit,
            impact_level=DecisionImpact.MEDIUM,
        )
        self.integration_audits.append(audit)

        return {
            'status': 'success',
            'audit': audit,
            'decision': audit_decision,
            'timestamp': datetime.utcnow().isoformat(),
        }

    def _prepare_tracking(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        tracking_plan = {
            'events': ['affiliate_click', 'scroll_depth', 'cta_view', 'conversion_signal'],
            'pixels': ['GA4', 'Postback-ready webhooks'],
            'qa': 'Validate attribution with sandbox conversions before launch.',
        }

        return {
            'status': 'success',
            'tracking_plan': tracking_plan,
            'prepared_at': datetime.utcnow().isoformat(),
        }

    def start_monitoring_loop(self):
        self.logger.info("Starting affiliate ops monitoring loop")

        while self.status != AgentStatus.ERROR:
            try:
                self.listen_for_messages()
                time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive loop
                self.logger.error(f"Affiliate ops loop error: {exc}")
                time.sleep(5)


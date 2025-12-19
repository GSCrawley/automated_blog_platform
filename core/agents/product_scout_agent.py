import time
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact


class ProductScoutAgent(BaseAgent):
    """Agent responsible for sourcing profitable products for a niche."""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        super().__init__("product_scout", "product_scout", redis_host, redis_port)
        self.discovery_cache: Dict[str, List[Dict[str, Any]]] = {}

    def get_capabilities(self) -> List[str]:
        return [
            'product_research',
            'affiliate_alignment',
            'market_research',
            'content_support'
        ]

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task_data.get('task_type') or task_data.get('type')

        if task_type in ['product_research', 'product_discovery']:
            return self._discover_products(task_data)
        if task_type == 'affiliate_alignment':
            return self._evaluate_affiliate_fitness(task_data)

        return {'status': 'error', 'error': f'Unknown task type: {task_type}'}

    def _discover_products(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        niche = task_data.get('niche') or task_data.get('niche_name', 'general')
        cache_key = f"{niche}_products"
        now = datetime.utcnow().isoformat()

        products = self.discovery_cache.get(cache_key) or [
            {
                'name': f'{niche} Starter Suite',
                'affiliate_ready': True,
                'commission_rate': '25% recurring',
                'price_point': '$20-500/mo',
                'trend_score': 0.9,
                'rationale': 'High AOV SaaS with sticky usage and active search demand',
            },
            {
                'name': f'{niche} Enterprise Toolkit',
                'affiliate_ready': True,
                'commission_rate': '30% recurring',
                'price_point': '$150-800/mo',
                'trend_score': 0.87,
                'rationale': 'Premium buyers, urgency for workflow automation',
            },
        ]

        self.discovery_cache[cache_key] = products
        self.performance_metrics['last_discovery'] = now

        return {
            'status': 'success',
            'niche': niche,
            'products': products,
            'timestamp': now,
        }

    def _evaluate_affiliate_fitness(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        product = task_data.get('product') or {}
        affiliate_options = product.get('affiliate_programs') or [
            {'network': 'Replit', 'rate': '30% recurring', 'status': 'active'},
            {'network': 'AI tool marketplace', 'rate': '25% recurring', 'status': 'active'},
        ]

        fitness = {
            'product_name': product.get('name', 'unknown'),
            'eligible_programs': affiliate_options,
            'integration_notes': 'Use UTM conventions and deep links for onboarding flows.',
            'risk_flags': ['Validate partner terms monthly to keep commissions current.'],
        }

        decision = self.make_decision(
            'affiliate_program_alignment',
            fitness,
            impact_level=DecisionImpact.MEDIUM,
        )

        return {
            'status': 'success',
            'decision': decision,
            'evaluated_at': datetime.utcnow().isoformat(),
        }

    def start_monitoring_loop(self):
        self.logger.info("Starting product scout monitoring loop")

        while self.status != AgentStatus.ERROR:
            try:
                self.listen_for_messages()
                time.sleep(1)
            except Exception as exc:  # pragma: no cover - defensive loop
                self.logger.error(f"Product scout loop error: {exc}")
                time.sleep(5)


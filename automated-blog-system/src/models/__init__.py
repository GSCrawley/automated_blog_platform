import logging

from .user import User, db
from .product import Product, Article
from .niche import Niche

logger = logging.getLogger(__name__)

# Import agent models if available
try:
    from .agent_models import AgentState, BlogInstance, AgentTask, MarketData, AgentDecision
    logger.debug("Agent models imported in __init__.py")
except ImportError as e:
    logger.debug("Agent models not available in __init__.py: %s", e)

__all__ = [
    'User', 'Product', 'Article', 'Niche', 'db',
    # Agent models (if available)
    'AgentState', 'BlogInstance', 'AgentTask', 'MarketData', 'AgentDecision'
]

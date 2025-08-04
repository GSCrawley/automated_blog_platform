from .user import User, db
from .product import Product, Article
from .niche import Niche

# Import agent models if available
try:
    from .agent_models import AgentState, BlogInstance, AgentTask, MarketData, AgentDecision
    print("✅ Agent models imported in __init__.py")
except ImportError as e:
    print(f"⚠️ Agent models not available in __init__.py: {e}")

__all__ = [
    'User', 'Product', 'Article', 'Niche', 'db',
    # Agent models (if available)
    'AgentState', 'BlogInstance', 'AgentTask', 'MarketData', 'AgentDecision'
]

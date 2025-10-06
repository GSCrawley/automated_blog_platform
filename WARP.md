# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Essential Development Commands

### Environment Setup
```bash
# Setup Python environment
cd automated-blog-system
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Setup Node.js environment
cd blog-frontend
npm install
# Or if using pnpm (specified in package.json)
pnpm install
```

### Development Workflow
```bash
# Start backend Flask server (from automated-blog-system/)
cd automated-blog-system/src
python main.py
# Server runs on http://localhost:5000

# Start frontend dev server (from blog-frontend/)
cd blog-frontend
npm run dev
# Server runs on http://localhost:5173

# Start Redis (required for agent communication)
redis-server
# Or using homebrew: brew services start redis
```

### Testing Commands
```bash
# Backend API tests
cd automated-blog-system
python test_api.py

# Test agent system
python test_agent_system.py

# Test knowledge base functionality
python test_knowledge_base.py

# Frontend linting
cd blog-frontend
npm run lint
```

### Build Commands
```bash
# Frontend production build
cd blog-frontend
npm run build

# Preview production build
npm run preview
```

## System Architecture Overview

### Multi-Agent System (Core Innovation)
This project implements a **headless GPT-5 Marketing Stack** with autonomous agents:

- **Orchestrator Agent**: Central coordinator managing all blog instances and agent assignments
- **Market Analytics Agent**: Researches trending products, competitive analysis, and market opportunities
- **Content Strategy Agent**: Plans content based on trends, handles SEO optimization, manages content calendar
- **Monetization Agent**: Manages affiliate programs, optimizes ad placement, tracks revenue
- **Performance Analytics Agent**: Monitors KPIs, detects anomalies, identifies growth opportunities

### Agent Communication Layer
- **Redis Pub/Sub**: Inter-agent messaging system
- **Message Broker**: Event-driven architecture with approval queues
- **Decision Framework**: Autonomous vs. approval-required action classification
- **State Management**: Persistent agent state with performance tracking

### Headless Content Pipeline
The system generates structured, optimization-ready article objects that can be:
- Served via API to any downstream renderer
- Transformed into static site output (Next.js/SvelteKit/JAMStack)
- Enhanced by Knowledge Base + Semantic Retrieval modules
- Routed to publisher adapters (WordPress integration deprecated but may return as plugin)

### Knowledge Base & RAG Implementation
- **Ontology Structure**: Category → Lever → Tactic → Pattern Artifact hierarchy
- **Knowledge Layers**: Static seed docs, dynamic market harvest, topical authority mapping
- **Retrieval Pipeline**: Hybrid keyword + vector search for content augmentation
- **Semantic Coverage**: Scoring system for content optimization

## Project Structure Patterns

### Backend Structure (Flask)
```
automated-blog-system/src/
├── models/           # SQLAlchemy database models
│   ├── agent_models.py    # Agent state, tasks, decisions
│   ├── product.py         # Products and articles
│   ├── niche.py          # Multi-niche blog management
│   └── user.py           # User management
├── routes/           # API endpoints
│   ├── agent_routes.py    # Agent system API
│   ├── blog.py           # Core blog CRUD
│   └── automation.py     # Automation workflows
├── services/         # Business logic (being migrated to agents)
│   ├── knowledge_base.py  # RAG and retrieval
│   ├── content_generator.py  # AI content creation
│   └── seo_optimizer.py   # SEO analysis
└── config.py         # Application configuration
```

### Agent System Structure
```
core/
├── agents/
│   ├── base_agent.py          # Abstract base class with communication
│   ├── agent_manager.py       # Agent lifecycle management
│   ├── orchestrator_agent.py  # Central coordination
│   └── market_analytics_agent.py  # Market research
├── infrastructure/
│   └── message_broker.py      # Redis pub/sub wrapper
└── scrapers/
    └── base_scraper.py        # Web scraping foundation
```

### Frontend Structure (React + Vite)
```
blog-frontend/src/
├── components/       # React components
│   └── agent-components/  # Agent monitoring UI
├── services/        # API integration
│   ├── api.js           # Core API client
│   └── agentApi.js      # Agent system API
└── hooks/           # Custom React hooks
```

## Agent System Development

### Agent Communication Pattern
```python
# Sending messages between agents
agent.send_message('market_analytics', {
    'type': 'task_assignment',
    'task_id': 'analyze_trend_001',
    'data': {'product_category': 'consumer_electronics'}
})

# Broadcasting to all agents
agent.broadcast_message({
    'type': 'system_update',
    'data': {'new_niche_added': 'smart_home'}
})
```

### Creating New Agents
1. Extend `BaseAgent` class in `core/agents/`
2. Implement required methods: `execute_task()`, `get_capabilities()`
3. Register agent in `AgentManager.initialize_default_agents()`
4. Add agent-specific routes in `src/routes/agent_routes.py`

### Agent State Management
```python
# Update agent state
agent.update_state({
    'last_analysis': datetime.utcnow().isoformat(),
    'products_analyzed': 150,
    'trends_detected': 5
})

# Persist to database
agent.persist_state()
```

## API Endpoints

### Core Blog API
- `GET /api/blog/articles` - List articles
- `POST /api/blog/articles` - Create article
- `PUT /api/blog/articles/<id>` - Update article
- `DELETE /api/blog/articles/<id>` - Delete article
- `GET /api/blog/products` - List products
- `GET /api/blog/niches` - List niches

### Agent System API
- `GET /api/agent/status` - System health
- `GET /api/agent/list` - Active agents
- `POST /api/agent/task` - Assign task
- `GET /api/agent/decisions` - Pending decisions

## Configuration Requirements

### Environment Variables
```bash
# Required for OpenAI integration
OPENAI_API_KEY=your_key_here

# Database configuration
DATABASE_URL=sqlite:///automated_blog_system.db

# Redis configuration (for agents)
REDIS_HOST=localhost
REDIS_PORT=6379

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Database Setup
```python
# Initialize database tables
with app.app_context():
    db.create_all()
    
# The system uses SQLite by default for development
# Database file: automated-blog-system/src/automated_blog_system.db
```

## Knowledge Base Integration

### Ontology Structure
The knowledge base follows a hierarchical structure:
1. **Category** (broad domain): AI Search Optimization, Psychographic Targeting
2. **Lever** (optimization vector): Conversational Query Coverage, Motivation Trigger Mapping  
3. **Tactic** (concrete method): Specific implementation patterns
4. **Metrics** (validation): Coverage percentage, semantic density scores

### RAG Pipeline
```python
# Retrieval-augmented generation workflow
knowledge_base.load_seed_documents()
results = knowledge_base.retrieve_relevant_tactics(
    agent_type="ContentStrategyAgent",
    category="AI Search Optimization"
)
content = content_generator.generate_with_context(prompt, results)
```

## Headless Article Contract

The system produces structured article objects ready for any publishing platform:

```json
{
    "id": 123,
    "title": "String",
    "slug": "kebab-case-string",
    "summary": "Concise abstract",
    "sections": [{"heading": "H2 text", "content": "Markdown or HTML-safe"}],
    "keywords": ["primary", "secondary"],
    "entities": ["BrandX", "ConceptY"],
    "calls_to_action": [{"type": "affiliate", "target": "vendor-id", "anchor": "Buy Now"}],
    "meta": {"read_time_minutes": 7, "semantic_density": 0.82},
    "source_attribution": [{"url": "https://...", "confidence": 0.74}]
}
```

## Testing Strategies

### Agent System Testing
```bash
# Test agent communication
python -c "
from core.agents.agent_manager import AgentManager
manager = AgentManager()
manager.initialize_default_agents()
print('Agents:', manager.list_active_agents())
"

# Test Redis connection
redis-cli ping
```

### API Integration Testing  
```bash
# Test backend API
curl http://localhost:5000/api/blog/articles
curl http://localhost:5000/api/agent/status

# Frontend API integration
cd blog-frontend
node src/test_api.js
```

## Development Notes

### Agent Rulebooks
Each agent follows specific guidelines defined in `docs/agent_rulebooks/`:
- Content Strategy Agent: Query cluster coverage, psychographic angle selection
- Monetization Agent: Offer slot allocation, conversion funnel analysis  
- Performance Analytics Agent: Coverage drift detection, anomaly alerting

### WordPress Deprecation
The original WordPress integration has been removed in favor of headless architecture. The `wordpress_service.py` file remains as a stub to prevent import errors.

### Current Development Phase
Focus areas (as per todo.md):
1. Complete CRUD operations for Articles, Products, Niches
2. Knowledge Base + RAG pipeline implementation
3. Content Strategy Agent development
4. Performance feedback loops

### Multi-Niche Support
The system supports multiple blog niches with separate:
- Product catalogs per niche
- Content strategies per niche  
- Performance tracking per niche
- Agent resource allocation per niche

## Troubleshooting

### Agent System Issues
```bash
# Check Redis connection
redis-cli ping

# View agent logs
tail -f automated-blog-system/logs/agent_system.log

# Restart agent system
# Kill existing processes and restart Flask server
```

### Database Issues
```bash
# Reset database (development only)
rm automated-blog-system/src/automated_blog_system.db
cd automated-blog-system/src && python main.py

# Check database content
sqlite3 automated-blog-system/src/automated_blog_system.db ".tables"
```

### Frontend Issues
```bash
# Clear node modules and reinstall
cd blog-frontend
rm -rf node_modules package-lock.json
npm install

# Check Vite configuration
npm run build --verbose
```

This documentation reflects the current headless GPT-5 Marketing Stack architecture focused on autonomous content generation and multi-agent coordination. The system emphasizes scalable, AI-driven content creation with sophisticated knowledge retrieval and semantic optimization capabilities.
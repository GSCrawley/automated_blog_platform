# Agent System Setup Guide
Guide for running and extending the multi-agent architecture in the headless GPT-5 Marketing Stack.

## Prerequisites

### Redis
Used for inter-agent pub/sub messaging.

macOS:
```bash
brew install redis
brew services start redis
```
Linux:
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable --now redis-server
```
Docker:
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Quick Start

Check readiness:
```bash
python start_agents.py --check-only
```
Start agents:
```bash
python start_agents.py
```
Custom Redis:
```bash
python start_agents.py --redis-host localhost --redis-port 6379 --log-level INFO
```

### Monitor Agents
- Frontend dashboard (Agent Monitor)
- Logs (stdout / file)
- Redis CLI: `redis-cli MONITOR`

## Current Agents

### Orchestrator Agent
Task coordination, scheduling, health aggregation.

### Market Analytics Agent
Trend & product signal monitoring (future: scraping + scoring).

### Planned
- Content Strategy Agent
- Monetization Agent
- Performance Analytics Agent
- Publisher Adapter Framework (replaces deprecated WordPress Manager role)

## Configuration

`.env` example:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
LOG_LEVEL=INFO
LOG_FILE=agents.log
AGENT_BASE_DELAY=1.0
AGENT_MAX_DELAY=5.0
SCRAPER_USER_AGENT="Mozilla/5.0 (compatible; HeadlessMarketingBot/1.0)"
SCRAPER_RATE_LIMIT=2.0
```

## API Endpoints
```
GET  /agents/status
POST /agents/<name>/assign
GET  /agents/<name>/tasks
POST /agents/<name>/tasks
GET  /decisions/pending
POST /decisions/<id>/approve
GET  /system/health
```

## Frontend Integration
Components (live / planned): AgentMonitor.jsx, ApprovalCenter.jsx (planned), BlogInstanceManager.jsx (planned)

## Troubleshooting
| Issue | Check |
|-------|-------|
| Redis connection failed | Service running / host & port |
| Import errors | Reinstall deps / working dir |
| Agent idle | DEBUG logs + Redis pub/sub |

Debug mode:
```bash
python start_agents.py --log-level DEBUG --log-file debug.log
```
Health check:
```bash
curl http://localhost:5001/system/health
```

## Development

### Adding an Agent
1. Subclass `BaseAgent`
2. Implement cycle / task logic
3. Register in `AgentManager`
4. Add routes (if external control needed)
5. Use knowledge base via `from src.services.knowledge_base import get_kb`

### Testing
```bash
pytest -k agent
```

## Roadmap Alignment
Removed: WordPress Manager Agent (legacy integration).
Future: Publisher adapters (static export first; CMS connectors later).

## Next Steps
1. Finalize CRUD + headless article enrichment
2. Implement Content Strategy Agent (generation + optimization loop)
3. Integrate Knowledge Base retrieval pipeline
4. Add Monetization & Performance agents
5. Introduce Publisher Adapter abstraction
6. Implement approval + feedback workflow

End of document.
# Agent System Setup Guide\n\nThis guide will help you set up and run the multi-agent architecture for the Automated Blog Platform.\n\n## Prerequisites

 1. Redis Installation\n\nThe agent system requires Redis for inter-agent communication.\n\n**macOS (using Homebrew):**\n```bash\nbrew install redis\nbrew services start redis\n```\n\n**Ubuntu/Debian:**\n```bash\nsudo apt-get update\nsudo apt-get install redis-server\nsudo systemctl start redis-server\nsudo systemctl enable redis-server\n```\n\n**Docker:**\n```bash\ndocker run -d -p 6379:6379 --name redis redis:alpine\n```\n\n### 
 
 2. Python Dependencies\n\nInstall the required Python packages:\n```bash\npip install -r requirements.txt\n```\n\n## Quick Start\n\n### 1. Check System Readiness\n\nBefore starting the agents, verify that all dependencies are installed and Redis is running:\n\n```bash\npython start_agents.py --check-only\n```\n\nThis will check:\n- Required Python packages\n- Redis connection\n- System readiness\n\n### 2. Start the Agent System\n\nStart all agents with default settings:\n\n```bash\npython start_agents.py\n```\n\nOr with custom Redis configuration:\n\n```bash\npython start_agents.py --redis-host localhost --redis-port 6379 --log-level INFO\n```\n\n### 
 
   3. Monitor Agent Status\n\nOnce the agents are running, you can monitor them through:\n\n1. **Web Interface**: Navigate to the Agent Monitor in the React frontend\n2. **Logs**: Check the console output or log files\n3. **Redis CLI**: Connect to Redis to see agent communication\n\n```bash\nredis-cli\n> KEYS agents.*\n> MONITOR\n```\n\n## Agent Architecture\n\nThe system currently includes these agents:\n\n### Orchestrator Agent\n- **Role**: Central coordinator\n- **Responsibilities**: \n  - Manages all blog instances\n  - Coordinates agent assignments\n  - Handles decision approvals\n  - Monitors system health\n\n### Market Analytics Agent\n- **Role**: Market research and trend analysis\n- **Responsibilities**:\n  - Monitors product trends\n  - Performs competitive analysis\n  - Discovers trending products\n  - Provides market insights\n\n## 
   
   Configuration\n\n### Environment Variables\n\nCreate a `.env` file in the project root:\n\n```env\n# Redis Configuration\nREDIS_HOST=localhost\nREDIS_PORT=6379\nREDIS_DB=0\n\n#Logging\nLOG_LEVEL=INFO\nLOG_FILE=agents.log\n\n# Agent Settings\nAGENT_BASE_DELAY=1.0\nAGENT_MAX_DELAY=5.0\n\n# 
   
   Scraping Settings\nSCRAPER_USER_AGENT=\"Mozilla/5.0 (compatible; BlogPlatform/1.0)\"\nSCRAPER_RATE_LIMIT=2.0\n```\n\n### Agent Configuration\n\nEach agent can be configured individually through the database or configuration files.\n\n## API Integration\n\nThe agent system exposes REST API endpoints through the Flask backend:\n\n- `GET /agents/status` - Get status of all agents\n- `POST /agents/{agent_name}/assign` - Assign agent to blog instance\n- `GET /agents/{agent_name}/tasks` - Get agent tasks\n- `POST /agents/{agent_name}/tasks` - Assign task to agent\n- `GET /decisions/pending` - Get pending decisions\n- `POST /decisions/{id}/approve` - Approve decision\n- `GET /system/health` - Get system health status
   
   ## \n\n## Frontend Integration\n\nThe React frontend includes agent monitoring components:\n\n1. **AgentMonitor.jsx** - Real-time agent status monitoring\n2. **ApprovalCenter.jsx** - Decision approval interface (to be created)\n3. **BlogInstanceManager.jsx** - Multi-blog management (to be created)\n\n## Troubleshooting\n\n### Common Issues\n\n**Redis Connection Failed:**\n- Ensure Redis is installed and running\n- Check firewall settings\n- Verify Redis configuration\n\n**Import Errors:**\n- Install missing dependencies: `pip install -r requirements.txt`\n- Check Python path configuration\n\n**Agent Not Starting:**\n- Check log files for error messages\n- Verify Redis connectivity\n- Ensure no port conflicts\n\n### Debug Mode\n\nRun with debug logging:\n\n```bash\npython start_agents.py --log-level DEBUG --log-file debug.log\n```\n\n
   
   ### Health Checks\n\nMonitor system health:\n\n```bash\ncurl http://localhost:5001/system/health\n```\n\n
   
   ## Development\n\n### Adding New Agents\n\n1. Create a new agent class inheriting from `BaseAgent`\n2. Implement required methods: `execute_task()`, `get_capabilities()`\n3. Register the agent in `AgentManager.initialize_default_agents()`\n4. Add API endpoints in `agent_routes.py`\n5. Update frontend components as needed\n\n### Testing\n\nRun agent system tests:\n\n```bash\npython -m pytest tests/test_agents.py\n```\n\n## Production Deployment\n\nFor production deployment:\n\n1. Use a production Redis instance\n2. Configure proper logging and monitoring\n3. Set up process management (systemd, supervisor, etc.)\n4. Configure load balancing if needed\n5. Set up backup and recovery procedures\n\n## Next Steps\n\n1. Complete Phase 6 CRUD verification\n2. Implement remaining agent types:\n   - Content Strategy Agent\n   - WordPress Manager Agent\n   - Monetization Agent\n   - Performance Analytics Agent\n3. Add web scraping infrastructure\n4. Implement approval workflow UI\n5. Add comprehensive monitoring and alerting\n\nFor more information, see the main README.md and todo.md files."
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




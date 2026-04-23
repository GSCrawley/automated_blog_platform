# Automated Blog Platform

## Project Overview

The Automated Blog Platform is a headless, multi-agent content automation system that generates, optimizes, and manages SEO-focused affiliate content with minimal human intervention. The system combines a **CrewAI-powered pipeline** for end-to-end blog creation with a **custom Redis-based agent framework** for autonomous coordination. Content is produced as structured JSON objects ready for downstream publishing to any target (static sites, CMS adapters, API syndication).

## Core System Objectives

- **Automated Content Generation**: Generate high-quality, SEO-optimized articles on trending high-ticket products via a multi-stage CrewAI pipeline
- **Real-Time Market Research**: Discover trending products and competitive intelligence using Tavily, SerperDev, and Firecrawl integrations
- **SEO Optimization**: AI-first SEO with keyword analysis, content optimization, and search intent targeting
- **Affiliate Marketing Integration**: Automated affiliate link placement with compliance auditing and monetization optimization
- **Multi-Niche Adaptability**: Niche-agnostic design that adapts to any profitable market without code changes
- **Multi-Blog Management**: Coordinate multiple blog instances across different niches
- **Autonomous Decision Making**: Agent-based system with approval workflows for high-impact decisions
- **Conversational Editing**: Natural language interface for content modification via CrewAI crews

## System Architecture

The system follows a modular, agent-based architecture with two complementary agent layers:

### CrewAI Pipeline (`core/crewai_system/`)

The primary content creation engine uses **CrewAI** to orchestrate a 5-stage blog creation flow (`BlogCreationFlow`) with typed state management:

| Stage | Crew | Agents | Purpose |
|-------|------|--------|---------|
| **0 — Research** | ResearchCrew | Niche Trend Researcher, Affiliate Opportunity Scout, Psychology/UX Researcher, Competitor Intelligence | Real-time intelligence gathering via Tavily, SerperDev, Firecrawl |
| **1 — Strategy** | ContentStrategyCrew | Content Strategy Director, SEO/Search Intent Specialist | Content planning informed by research output |
| **2 — Creation** | ContentCreationCrew | Author Agent, Monetization Specialist | Article writing with embedded affiliate monetization |
| **3 — Editorial** | EditorCrew | Content Quality Editor, Monetization Auditor, SEO/UX Reviewer, Compliance Checker | Quality gate with verdict system (PUBLISH / REVISE / REJECT) |
| **Revision** | — | Editorial routing | Feedback loop integration when revisions are required |

Additional crew:
- **ConversationalEditorCrew**: NLP Parser, Action Coordinator, Content Editor, Media Manager, QA — enables natural language article editing through custom tools (CommandParser, ArticleParser, ContentModifier)

**CrewAI Knowledge Base** (`TARGET_BLOG_KG`):
- Uses OpenAI `text-embedding-3-small` for embeddings
- LLM: `gpt-4o-mini` for planning
- Scoped memory contexts with recency/semantic/importance weighting

### Custom Agent Framework (`core/agents/`)

A standalone Redis pub/sub agent system provides autonomous coordination and monitoring:

| Agent | Status | Capabilities |
|-------|--------|-------------|
| **Orchestrator Agent** | ✅ Active | Agent coordination, task delegation, decision approval, system monitoring, blog instance management |
| **Market Analytics Agent** | ✅ Active | Market research, trend analysis, competitive analysis, product discovery, sentiment analysis |
| **Author Agent** | 🚧 Developed | Content generation, content replication, outline planning, research synthesis |
| **Editor Agent** | 🚧 Developed | Layout review, content quality, accessibility audit, on-page SEO |
| **Product Scout Agent** | 🚧 Developed | Product research, affiliate alignment, market research, content support |
| **Affiliate Ops Agent** | 🚧 Developed | Affiliate validation, compliance review, tracking setup, content monetization |

**Infrastructure**:
- `base_agent.py` — Abstract base class with autonomous decision-making, Redis messaging, state persistence, and performance tracking
- `agent_manager.py` — Lifecycle management, agent registry, health monitoring
- `message_broker.py` — Redis pub/sub with priority-based task queuing (1–10 scale), channel routing (`agents.global`, `agents.{name}`)

### Backend (Flask + SQLAlchemy)

The backend API layer is built with Python Flask and SQLAlchemy:

- **Models** (`automated-blog-system/src/models/`):
  - `agent_models.py` — AgentState, BlogInstance, AgentTask, AgentDecision
  - `product.py` — Product (affiliate products with trend scores) and Article (generated content with metadata)
  - `niche.py` — Niche (market verticals with market_size, competition, profitability scoring)

- **Routes** (`automated-blog-system/src/routes/`):
  - `agent_routes.py` — Agent status, task assignment, decision queue, performance metrics
  - `blog.py` — Full CRUD for articles, products, niches; trending products endpoint
  - `automation.py` — Article generation triggers, market analysis, automation status
  - `user.py` — User management (stub)

- **Services** (`automated-blog-system/src/services/`):
  - `content_generator.py` — OpenAI GPT-4o-mini integration for SEO-optimized article generation with title/meta/keyword generation
  - `seo_optimizer.py` — Keyword optimization analysis, meta tag generation, content improvement recommendations
  - `knowledge_base.py` — Document ingestion from `/docs`, markdown section tokenization, metadata extraction, semantic retrieval with agent filtering
  - `trend_analyzer.py` — Market trend analysis with mock data fallback
  - `niche_pipeline.py` — Multi-niche workflow coordination
  - `automation_scheduler.py` — Thread-based scheduling for daily content generation (9 AM) and content updates (3 PM)
  - `wordpress_service.py` — Deprecated stub (raises RuntimeError; retained to prevent stale import breakage)

### Frontend (React 19 + Vite)

A modern React-based dashboard for monitoring and controlling the system:

- **Core Views**: Dashboard, Articles, Products, Niches, Analytics, Settings
- **Content Tools**: GenerateArticle (AI article generation), ConversationalEditor (natural language editing via CrewAI backend)
- **Management**: ProductApproval (approval workflows), MediaUpload
- **Simplified List Views**: ArticlesSimple, ProductsSimple, NichesSimple (reliable search/filter components)
- **Developer Utilities**: ApiTest, UiTest, ProductsDebug

**Frontend Stack**:
- React 19.1 with Vite 6.3 bundler
- Radix UI component primitives (30+ components)
- TailwindCSS 4.1 for styling
- Recharts for analytics visualization
- Framer Motion for animations
- React Hook Form + Zod for form validation
- React Router DOM 7.6 for navigation

### Web Scraping Infrastructure

`core/scrapers/base_scraper.py` provides a base class for implementing web scrapers for market research and product discovery. External scraping is handled primarily through the CrewAI ResearchCrew's Firecrawl integration.

### Headless Content Layer

The system produces structured, optimization-ready article objects (title, summary, keywords, semantic entities, monetization context) that can be:

- Served via the Flask API to any downstream renderer
- Transformed into static site output (JAMstack adapter planned)
- Enriched by the Knowledge Base and semantic retrieval modules
- Routed through the CrewAI editorial pipeline for quality assurance

## External Integrations

| Service | Purpose | Status |
|---------|---------|--------|
| **OpenAI** (GPT-4o-mini, text-embedding-3-small) | Content generation, embeddings, LLM planning | ✅ Integrated |
| **Tavily Search API** | Real-time research queries for ResearchCrew | ✅ Integrated |
| **SerperDev API** | SEO/search intelligence for ResearchCrew | ✅ Integrated |
| **Firecrawl** | Web scraping and content extraction for ResearchCrew | ✅ Integrated |
| **Redis** | Agent pub/sub messaging and task queues | ✅ Integrated |
| **LanceDB** | Vector database for embeddings | ⚙️ In dependencies, pending integration |

## Project Status

### Completed Phases (7 of 17)

1. ✅ **Phase 1** — Database setup and configuration (SQLite + SQLAlchemy)
2. ✅ **Phase 2** — Frontend-Backend integration
3. ✅ **Phase 3** — Backend API testing and verification
4. ✅ **Phase 4** — Frontend integration (React components + API communication)
5. ✅ **Phase 5** — Multi-niche system implementation
6. ✅ **Phase 6** — CRUD functionality verification
7. ✅ **Phase 7** — Multi-agent architecture (Orchestrator + Market Analytics agents, Redis messaging, CrewAI pipeline)

### In Progress

- **Phase 7.5** — Frontend agent integration (connecting agent monitoring UI to live data)
- **Phase 8** — CRUD operations completion (create/update/delete for all entities)
- **Phase 9** — Knowledge Base & RAG pipeline (ontology expansion, embedding index, hybrid retrieval)

### Upcoming

- **Phase 10** — Multi-blog management (headless)
- **Phase 11** — Notification & approval system
- **Phase 12** — Performance optimization & learning
- **Phase 13** — SEO tools integration (headless)
- **Phase 14** — Advanced features
- **Phase 15** — SaaS transformation
- **Phase 16** — Testing & QA
- **Phase 17** — Deployment & scaling

## File Structure

```
automated-blog-platform/
├── core/                              # Agent system & intelligence layer
│   ├── agents/                        # Custom Redis-based agent framework
│   │   ├── base_agent.py             # Abstract base class (decision-making, messaging, state)
│   │   ├── agent_manager.py          # Lifecycle management & registry
│   │   ├── orchestrator_agent.py     # Central coordinator (✅ active)
│   │   ├── market_analytics_agent.py # Market research & trends (✅ active)
│   │   ├── author_agent.py           # Content generation
│   │   ├── editor_agent.py           # Quality assurance
│   │   ├── product_scout_agent.py    # Product research
│   │   └── affiliate_ops_agent.py    # Monetization & compliance
│   ├── crewai_system/                 # CrewAI pipeline integration
│   │   ├── blog_creation_flow.py     # 5-stage BlogCreationFlow orchestrator
│   │   ├── research_crew.py          # Stage 0: Market intelligence gathering
│   │   ├── content_strategy_crew.py  # Stage 1: Content planning
│   │   ├── content_creation_crew.py  # Stage 2: Article writing
│   │   ├── editor_crew.py           # Stage 3: Editorial QA gate
│   │   ├── conversational_editor_crew.py  # NL editing interface
│   │   ├── tools/                    # Custom CrewAI tools
│   │   └── knowledge/                # CrewAI memory & KG config
│   ├── infrastructure/                # Communication layer
│   │   └── message_broker.py         # Redis pub/sub + task queues
│   ├── scrapers/                      # Web scraping foundation
│   │   └── base_scraper.py
│   └── data/                          # CrewAI memory storage
├── automated-blog-system/             # Flask backend & API
│   ├── src/
│   │   ├── main.py                   # Flask app entry point
│   │   ├── config.py                 # Configuration management
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── agent_models.py       # AgentState, BlogInstance, AgentTask, AgentDecision
│   │   │   ├── product.py            # Product, Article
│   │   │   ├── niche.py              # Niche
│   │   │   └── user.py               # DB initialization
│   │   ├── routes/                   # API blueprints
│   │   │   ├── agent_routes.py       # /api/agents/*
│   │   │   ├── blog.py               # /api/blog/*
│   │   │   ├── automation.py         # /api/automation/*
│   │   │   └── user.py               # /api/users/*
│   │   └── services/                 # Business logic
│   │       ├── content_generator.py  # OpenAI content generation
│   │       ├── seo_optimizer.py      # SEO analysis & recommendations
│   │       ├── knowledge_base.py     # Document ingestion & retrieval
│   │       ├── trend_analyzer.py     # Market trend analysis
│   │       ├── niche_pipeline.py     # Multi-niche workflows
│   │       ├── automation_scheduler.py # Scheduled content tasks
│   │       └── wordpress_service.py  # Deprecated stub
│   └── requirements.txt
├── blog-frontend/                     # React 19 frontend (Vite)
│   ├── src/
│   │   ├── components/               # UI components
│   │   │   ├── Dashboard.jsx         # System overview
│   │   │   ├── ConversationalEditor.jsx # NL editing interface
│   │   │   ├── Analytics.jsx         # Performance analytics
│   │   │   ├── GenerateArticle.jsx   # AI article generation
│   │   │   ├── ArticlesSimple.jsx    # Article list (search/filter)
│   │   │   ├── ProductsSimple.jsx    # Product list (search/filter)
│   │   │   ├── NichesSimple.jsx      # Niche list (search/filter)
│   │   │   ├── ProductApproval.jsx   # Approval workflow UI
│   │   │   ├── Settings.jsx          # System configuration
│   │   │   ├── agent-components/     # Agent monitoring UI
│   │   │   └── ui/                   # Radix UI component library
│   │   ├── services/                 # API client services
│   │   ├── hooks/                    # Custom React hooks
│   │   └── App.jsx                   # App root with routing
│   └── package.json
├── docs/                              # Documentation
│   ├── agent_rulebooks/              # Agent behavior guidelines
│   ├── niche_info/                   # Market research data
│   ├── AGENT_SYSTEM_SETUP.md         # Agent system architecture docs
│   ├── knowledge_architecture.md     # Ontology framework (8 categories)
│   ├── implementation_plan.md        # 16-week transformation roadmap
│   └── market_research_agent_framework.md
├── memory-bank/                       # Development context & progress tracking
├── KGsTemp/                           # Knowledge graph visualization data (JSON)
├── start_agents.py                    # Agent system startup (Redis check, graceful shutdown)
├── start_backend.sh                   # Flask server startup script
├── start_frontend.sh                  # React dev server startup script
├── requirements.txt                   # Root Python dependencies
├── todo.md                            # 17-phase development roadmap
└── WARP.md                            # Developer quick-start guide
```

## Knowledge Base Architecture

The knowledge base supports content generation with an 8-category ontology defined in `docs/knowledge_architecture.md`:

- AI Search Optimization
- Psychographic Targeting
- Platform Optimization
- Community & Engagement
- Content Multiplication
- Analytics & Feedback
- Technical Delivery
- Monetization

**Data Layers**:
- **Static Seed**: Curated marketing strategy docs from `/docs` (loaded via `knowledge_base.py`)
- **Dynamic Harvest**: Agent-scraped market & competitor signals
- **Ontology**: Category → Lever → Tactic hierarchy with metadata tagging
- **CrewAI Memory**: Scoped knowledge contexts via `TARGET_BLOG_KG` with semantic embeddings

## Headless Article Contract

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
    "source_attribution": [{"url": "https://...", "confidence": 0.74}],
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
}
```

Planned additions: topical authority score, internal link suggestions, SERP gap insights.

## Requirements

### Backend Dependencies
- Python 3.11+
- Flask 3.1 + Flask-CORS
- SQLAlchemy 2.0
- CrewAI 0.100+ with CrewAI-Tools 0.40+
- OpenAI (GPT-4o-mini, text-embedding-3-small)
- Redis 5.0 (agent communication / event bus)
- Tavily Python SDK (research queries)
- LanceDB 0.18+ (vector storage — pending full integration)
- BeautifulSoup4 + lxml (web scraping)
- aiohttp + aiofiles (async support)

### Frontend Dependencies
- Node.js
- React 19.1 with Vite 6.3
- Radix UI (component primitives)
- TailwindCSS 4.1
- Recharts (charts/analytics)
- Framer Motion (animations)
- React Hook Form + Zod (form validation)

### API Keys / Secrets
- OpenAI API Key
- Tavily Search API Key
- SerperDev API Key
- Firecrawl API Key (for web scraping)

## Development Quick Start

```bash
# 1. Backend setup
cd automated-blog-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Frontend setup
cd blog-frontend
npm install   # or pnpm install

# 3. Start Redis (required for agent communication)
redis-server

# 4. Start backend + agents (Flask on port 5001, agents auto-start in background)
bash start_backend.sh
# or manually: cd automated-blog-system/src && python main.py

# 5. Start frontend (Vite dev server on port 5173)
bash start_frontend.sh
# or manually: cd blog-frontend && npm run dev
```

> **Note:** Each of steps 3–5 runs in the foreground — use a separate terminal tab/window for each. Redis (port 6379), Flask (port 5001), and Vite (port 5173) don't conflict.

**For WARP Terminal users:** See `WARP.md` for comprehensive development commands and architecture guidance.

## Known Issues

- **CRUD Operations**: Create/Update/Delete not fully implemented for all entities
- **Agent Dashboard**: Agent monitoring UI not yet connected to live data
- **Decision Workflow**: Approval system UI not yet built
- **Analytics**: Currently displays mock data; real backend integration pending
- **Knowledge Base**: Uses naive token overlap retrieval; embedding-based search pending
- **Database**: SQLite for development; PostgreSQL recommended for production

## Contributing (Internal)

1. Keep changes atomic; remove residual legacy WordPress references when encountered.
2. Prefer adding tests around new agent and CrewAI crew behaviors.
3. Document new JSON contracts in README before large refactors.
4. Refer to `WARP.md` for development workflow and testing strategies.
5. Agent rulebooks in `docs/agent_rulebooks/` define expected behavior for each agent role.

---

## Legacy WordPress Deprecation Note

WordPress integration has been fully removed. `wordpress_service.py` is retained only as a stub raising `RuntimeError` to prevent stale import breakage. Former WordPress-specific database columns (`wordpress_post_id`, `wordpress_url`, etc.) have been removed from models.

---

## Roadmap

See `todo.md` for the full 17-phase development roadmap and `docs/implementation_plan.md` for the 16-week JAMstack transformation plan.

Planned future work includes:
- JAMstack frontend migration (Next.js/Strapi/Vercel)
- Agent team expansion to 4 specialized teams (13+ agents)
- Multi-platform content distribution (TikTok, Instagram, YouTube)
- Full RAG pipeline with vector embeddings
- SaaS transformation with multi-tenant architecture

# Tech Context - Automated Blog Platform

## Technology Stack Overview

### JAMstack Frontend Technologies (Primary - Phase 1)
- **Framework**: Next.js 14+ with App Router for static generation and optimal performance
- **Build Tool**: Built-in Next.js optimization with automatic code splitting and tree shaking
- **UI Components**: Tailwind CSS with shadcn/ui components and custom optimization components
- **State Management**: Zustand for global state, React Query for server state management
- **HTTP Client**: Built-in fetch API with React Query for caching and synchronization
- **Deployment**: Vercel with automatic deployments, global CDN, and edge functions

### Headless CMS Backend (Primary - Phase 1)
- **CMS Platform**: Strapi 4.15+ with custom content types and agent integration hooks
- **Database**: PostgreSQL for production, SQLite for development
- **API Layer**: REST and GraphQL APIs with automatic generation
- **Media Management**: Strapi media library with CDN integration and automatic optimization
- **Agent Integration**: Custom plugins and webhooks for agent automation workflows

### Legacy System (Maintained During Transition)
- **Runtime**: Python 3.9+
- **Web Framework**: Flask with SQLAlchemy ORM
- **Frontend**: React 18 with Vite build tool
- **WordPress Integration**: WordPress REST API (bridging during migration)
- **Database**: SQLite (development), prepared for PostgreSQL migration

### Advanced Agent Infrastructure
- **Base Architecture**: Enhanced agent framework with team coordination capabilities
- **Team Communication**: Redis pub/sub messaging with team-specific channels and cross-team coordination
- **Agent Teams**: Specialized teams (Content Strategy, Technical Infrastructure, Multi-Platform Distribution, Interactive Editor)
- **Persistence**: SQLAlchemy models extended for team state and coordination data
- **Scheduling**: Advanced asyncio task processing with team-based resource allocation
- **Monitoring**: Comprehensive health checking and performance tracking across all agent teams

### JAMstack Integrations
- **Strapi API**: Headless CMS integration for content management and agent automation
- **Vercel API**: Automated deployment triggers and performance monitoring
- **Next.js API**: Static generation coordination and dynamic content updates
- **Edge Functions**: Real-time personalization and analytics processing at CDN edge

### Advanced External Integrations
- **OpenAI API**: Enhanced content generation with conversational optimization and psychographic targeting
- **AI Search APIs**: Specialized integration for AI crawler optimization and search visibility tracking
- **Multi-Platform APIs**: TikTok, Instagram, YouTube APIs for content distribution and community building
- **Analytics Platforms**: Google Analytics 4, Mixpanel, Segment for comprehensive behavioral tracking
- **Optimization Services**: Custom AI SEO tools, psychographic analysis, real-time contextual analytics

## Development Environment

### JAMstack Dependencies (Phase 1 Implementation)
```bash
# Next.js Frontend Dependencies
next==14.0.0
react==18.2.0
@strapi/strapi==4.15.0
tailwindcss==3.3.0
zustand==4.4.7
@tanstack/react-query==5.0.0
framer-motion==10.16.0
@vercel/analytics==1.1.0
next-seo==6.4.0

# Python Agent System (Enhanced)
Flask==2.3.3
SQLAlchemy==2.0.21
Redis==5.0.0
OpenAI>=1.0.0
strapi-python-client==1.0.0
vercel-python==2.1.0
segment-analytics-python==2.2.3
mixpanel==4.10.0
```

### JAMstack Development Setup
- **Next.js Frontend**: Development server on port 3000 with hot reload and optimization
- **Strapi Backend**: Headless CMS on port 1337 with admin panel and API endpoints
- **Agent System**: Enhanced Python agents with team coordination on existing Flask API (port 5001)
- **Redis**: Multi-channel messaging for team-based communication on port 6379
- **PostgreSQL**: Production database with agent state management and content storage
- **Vercel**: Local deployment testing with preview environments

### Legacy System (Maintained)
- **React Frontend**: Vite dev server on port 5173 (maintained during transition)
- **Flask Backend**: API server on port 5001 (enhanced with JAMstack integration)
- **SQLite**: Development database (migrating to PostgreSQL)

### Enhanced Project Structure
```
automated-blog-platform/
├── jamstack-frontend/        # Next.js Application (NEW - Phase 1)
│   ├── pages/               # Next.js pages with dynamic routing
│   ├── components/          # Modern UI components with optimization
│   │   ├── analytics/       # Real-time contextual analytics
│   │   ├── optimization/    # AI SEO and psychographic components
│   │   └── editor/         # Conversational editing interface
│   ├── lib/                # JAMstack integrations
│   │   ├── strapi.js       # Headless CMS integration
│   │   ├── analytics.js    # Real-time analytics system
│   │   └── optimization.js # AI optimization engines
│   └── next.config.js      # Optimized configuration
├── strapi-backend/          # Headless CMS (NEW - Phase 1)
│   ├── api/                # Content types and controllers
│   ├── config/             # Database and plugin configs
│   └── extensions/         # Agent integration middleware
├── core/                    # Enhanced Agent System
│   ├── agents/
│   │   ├── teams/          # Specialized agent teams (NEW)
│   │   │   ├── content_strategy/     # AI SEO, psychographic, content
│   │   │   ├── technical_infrastructure/ # Next.js, performance, analytics
│   │   │   ├── multi_platform_distribution/ # Platform optimization
│   │   │   └── interactive_editor/   # Conversational interface
│   │   ├── base_agent.py   # Enhanced with team coordination
│   │   └── orchestrator_agent.py # Multi-team coordination
│   ├── optimization/       # Advanced optimization systems (NEW)
│   │   ├── ai_seo_optimizer.py
│   │   ├── psychographic_engine.py
│   │   └── content_multiplier.py
│   └── analytics/          # Real-time analytics (NEW)
│       ├── contextual_metrics.py
│       └── psychographic_analytics.py
├── automated-blog-system/   # Legacy Flask Backend (Enhanced)
│   └── src/                # Extended with JAMstack integration
└── blog-frontend/          # Legacy React Frontend (Maintained)
    └── src/                # Maintained during transition
```

## Database Architecture

### Core Entities
```sql
-- Niches table
CREATE TABLE niches (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    market_size_score INTEGER,
    competition_score INTEGER,
    profitability_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    niche_id INTEGER,
    affiliate_url TEXT,
    commission_rate DECIMAL(5,2),
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (niche_id) REFERENCES niches(id)
);

-- Articles table
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    product_id INTEGER,
    wordpress_post_id INTEGER,
    seo_title VARCHAR(70),
    meta_description VARCHAR(160),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### Agent State Management
- **Agent Registry**: Track active agents and their capabilities
- **Task Queue**: Persistent task storage with priority handling
- **Decision History**: Audit trail of all agent decisions
- **Performance Metrics**: Time-series data for agent effectiveness

## API Architecture

### RESTful Endpoints
```
# Blog Management
GET    /api/blog/articles     # List articles
POST   /api/blog/articles     # Create article
PUT    /api/blog/articles/:id # Update article
DELETE /api/blog/articles/:id # Delete article

GET    /api/blog/products     # List products
POST   /api/blog/products     # Create product
PUT    /api/blog/products/:id # Update product
DELETE /api/blog/products/:id # Delete product

GET    /api/blog/niches       # List niches
POST   /api/blog/niches       # Create niche
PUT    /api/blog/niches/:id   # Update niche
DELETE /api/blog/niches/:id   # Delete niche

# Agent Management
GET    /api/agents/status     # Get all agent status
POST   /api/agents/:name/start # Start specific agent
POST   /api/agents/:name/stop  # Stop specific agent
GET    /api/agents/:name/tasks # Get agent tasks

# System Health
GET    /api/system/health     # Overall system status
```

### Response Formats
```json
// Standard success response
{
    "success": true,
    "data": {...},
    "message": "Operation completed successfully"
}

// Error response
{
    "success": false,
    "error": "Error description",
    "code": "ERROR_CODE"
}

// Agent status response
{
    "active_agents": 2,
    "agent_manager_available": true,
    "overall_status": "healthy",
    "agents": {
        "orchestrator": {"status": "active", "last_heartbeat": "..."},
        "market_analytics": {"status": "active", "last_heartbeat": "..."}
    }
}
```

## Security Considerations

### API Security
- **Authentication**: API key validation for external services
- **Input Validation**: Comprehensive sanitization of all inputs
- **Rate Limiting**: Protection against abuse and excessive requests
- **CORS Configuration**: Controlled cross-origin resource sharing

### Agent Security
- **Sandboxed Execution**: Isolated environments for agent operations
- **Permission Control**: Granular permissions for different agent actions
- **Audit Logging**: Complete trail of all system changes
- **Rollback Capability**: Ability to reverse problematic changes

### Data Protection
- **Environment Variables**: Secure storage of API keys and credentials
- **Database Security**: Parameterized queries to prevent SQL injection
- **Content Validation**: Sanitization of generated content before publication
- **Backup Strategy**: Regular backups of all critical data

## Performance Optimization

### Backend Optimizations
- **Database Indexing**: Optimized queries for frequently accessed data
- **Connection Pooling**: Efficient database connection management
- **Caching Strategy**: Redis-based caching for expensive operations
- **Async Processing**: Non-blocking operations for improved responsiveness

### Frontend Optimizations
- **Code Splitting**: Lazy loading of components for faster initial load
- **Bundle Optimization**: Minimized JavaScript bundle sizes
- **API Caching**: Client-side caching of frequently requested data
- **Responsive Design**: Optimized performance across all device types

### Agent Performance
- **Efficient Scheduling**: Optimized task distribution and execution
- **Resource Management**: CPU and memory usage monitoring
- **Parallel Processing**: Concurrent execution where appropriate
- **Performance Metrics**: Detailed tracking of agent efficiency

## Deployment Architecture

### JAMstack Production Environment
- **Vercel Deployment**: Automated deployments with global CDN and edge optimization
- **Strapi Cloud**: Managed headless CMS with automatic scaling and backup
- **PostgreSQL Database**: Managed database service with replication and automatic backup
- **Redis Cloud**: Managed Redis instance for agent messaging with clustering support
- **Edge Functions**: Real-time personalization and analytics at CDN edge locations

### Performance and Optimization
- **Global CDN**: Content delivery from edge locations worldwide for sub-2-second load times
- **Static Generation**: Pre-built pages with incremental static regeneration for dynamic updates
- **Image Optimization**: Automatic WebP conversion, responsive images, and lazy loading
- **Core Web Vitals**: Optimized for Google's performance metrics and SEO rankings
- **Agent Processing**: Distributed agent team processing with automatic load balancing

### Advanced Monitoring and Analytics
- **Real-time Analytics**: Contextual metrics collection with behavioral segmentation
- **System Health Monitoring**: Comprehensive agent team status and performance tracking
- **Performance Metrics**: Core Web Vitals monitoring with automatic optimization alerts
- **Business Intelligence**: Revenue tracking, conversion optimization, and market intelligence
- **Error Tracking**: Advanced error monitoring with automatic recovery workflows

### Scalability Architecture
- **Serverless Scaling**: Automatic scaling based on demand without server management
- **Multi-Platform Distribution**: Independent scaling for TikTok, Instagram, YouTube content distribution
- **Agent Team Scaling**: Specialized scaling for different agent teams based on workload
- **Database Clustering**: Horizontal database scaling with automated sharding and replication
- **CDN Optimization**: Global content distribution with edge caching and optimization

This technical context provides the foundation for all development decisions and ensures consistent implementation across all system components.

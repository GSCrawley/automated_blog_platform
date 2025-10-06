// Current Architecture Knowledge Graph (Live State Snapshot)
// File: neo4j_current_architecture_kg.cypher
// Update at end of each work session to reflect present reality.
// Rule (assistant internal): When session ends and architectural changes occurred, regenerate this file.
// MATCH (n) DETACH DELETE n;  // (Use only in a clean sandbox)

// ===== CURRENT CORE COMPONENTS =====
CREATE (flask:Component {name:'Flask Backend', type:'BackendAPI', status:'active', technology:'Python/Flask'});
CREATE (react:Component {name:'React Frontend', type:'Frontend', status:'active', technology:'React/Vite'});
CREATE (sqlite:Component {name:'SQLite DB', type:'Database', status:'active', technology:'SQLite'});
CREATE (redis:Component {name:'Redis Broker', type:'MessageBroker', status:'active'});
CREATE (kb_service:Component {name:'Knowledge Base Service', type:'Service', status:'initial', features:'Chunking+Keyword Overlap'});
CREATE (docs_repo:Knowledge {name:'Docs Corpus', status:'seed', description:'/docs markdown files'});

// ===== ACTIVE AGENTS =====
CREATE (orchestrator:Agent {name:'Orchestrator Agent', status:'active', responsibilities:'Coordination'});
CREATE (market_analytics:Agent {name:'Market Analytics Agent', status:'active', responsibilities:'Trend & market signals'});

// ===== RELATIONSHIPS =====
CREATE (react)-[:CALLS_API]->(flask);
CREATE (flask)-[:USES]->(sqlite);
CREATE (orchestrator)-[:COORDINATES]->(market_analytics);
CREATE (orchestrator)-[:USES]->(redis);
CREATE (market_analytics)-[:USES]->(redis);
CREATE (kb_service)-[:INDEXES]->(docs_repo);
CREATE (orchestrator)-[:QUERIES]->(kb_service);
CREATE (market_analytics)-[:QUERIES]->(kb_service);

// ===== ROADMAP PLACEHOLDERS (Not Yet Implemented) =====
CREATE (rag_pipeline:PlannedComponent {name:'RAG Pipeline', status:'planned'});
CREATE (embedding_service:PlannedComponent {name:'Embedding Service', status:'planned'});
CREATE (content_strategy_agent:PlannedAgent {name:'Content Strategy Agent', status:'planned'});
CREATE (monetization_agent:PlannedAgent {name:'Monetization Agent', status:'planned'});
CREATE (performance_agent:PlannedAgent {name:'Performance Analytics Agent', status:'planned'});

CREATE (rag_pipeline)-[:FUTURE_DEPENDS_ON]->(kb_service);
CREATE (embedding_service)-[:FUTURE_AUGMENTS]->(kb_service);
CREATE (content_strategy_agent)-[:FUTURE_NEEDS]->(rag_pipeline);
CREATE (monetization_agent)-[:FUTURE_NEEDS]->(rag_pipeline);
CREATE (performance_agent)-[:FUTURE_NEEDS]->(rag_pipeline);

// ===== BUSINESS GOALS (Tracking Alignment) =====
CREATE (goal_kb:Goal {name:'Improve Retrieval Quality', metric:'coverage_percent', target:'>70% early'});
CREATE (kb_service)-[:SUPPORTS]->(goal_kb);

// ===== QUICK QUERIES =====
// Active components: MATCH (c:Component) RETURN c.name,c.status;
// Planned dependencies: MATCH (n)-[:FUTURE_*]->(m) RETURN n,m;
// Knowledge flow: MATCH (a:Agent)-[:QUERIES]->(kb:Component {name:'Knowledge Base Service'}) RETURN a.name;

// END CURRENT ARCHITECTURE SNAPSHOT

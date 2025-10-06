// Projected Final Architecture Knowledge Graph (Headless GPT-5 Marketing Stack)
// File: neo4j_projected_final_architecture_kg.cypher
// Purpose: Represents the TARGET end-state architecture after all roadmap phases
// Safe Re-run: File now uses MERGE + scope tagging (scope:'projected_final') for idempotence.
// To refresh only this scope (CAUTION): MATCH (n {scope:'projected_final'}) DETACH DELETE n;
// To diff changes, export existing subset: MATCH (n {scope:'projected_final'}) RETURN n;

// ========================= META =============================
MERGE (arch:Meta {name:'ArchitectureVersion', scope:'projected_final'})
	ON CREATE SET arch.version='v1.0-final-projection', arch.generated=date(), arch.description='Projected end-state after Phase 9–13 completion'
	ON MATCH SET arch.last_refreshed=datetime();

// ===================== CORE PLATFORM ========================
MERGE (nextjs:Component {name:'Next.js Frontend', scope:'projected_final'})
	ON CREATE SET nextjs.type='Frontend', nextjs.status='target', nextjs.technology='Next.js 14+', nextjs.delivery='Static+ISR';
MERGE (strapi:Component {name:'Strapi CMS', scope:'projected_final'})
	ON CREATE SET strapi.type='HeadlessCMS', strapi.status='target', strapi.technology='Strapi 4.x';
MERGE (vercel:Component {name:'Vercel Edge', scope:'projected_final'})
	ON CREATE SET vercel.type='Deployment', vercel.status='target', vercel.technology='Vercel/CDN';
MERGE (postgres:Component {name:'PostgreSQL Database', scope:'projected_final'})
	ON CREATE SET postgres.type='Database', postgres.status='target', postgres.technology='PostgreSQL 15+';
MERGE (redis:Component {name:'Redis Message Broker', scope:'projected_final'})
	ON CREATE SET redis.type='MessageBroker', redis.status='active', redis.technology='Redis';
MERGE (api_gateway:Component {name:'Flask API Gateway', scope:'projected_final'})
	ON CREATE SET api_gateway.type='BackendAPI', api_gateway.status='transitional', api_gateway.technology='Python/Flask';
MERGE (kb_service:Component {name:'Knowledge Base Service', scope:'projected_final'})
	ON CREATE SET kb_service.type='Service', kb_service.status='evolving', kb_service.technology='Python';
MERGE (embedding_service:Component {name:'Embedding Service', scope:'projected_final'})
	ON CREATE SET embedding_service.type='MLService', embedding_service.status='planned', embedding_service.technology='Local/External Embeddings';
MERGE (rag_pipeline:Component {name:'RAG Pipeline', scope:'projected_final'})
	ON CREATE SET rag_pipeline.type='Service', rag_pipeline.status='planned', rag_pipeline.technology='Hybrid Retrieval';
MERGE (ontology_store:Component {name:'Ontology Store', scope:'projected_final'})
	ON CREATE SET ontology_store.type='KnowledgeStore', ontology_store.status='planned', ontology_store.storage='JSON→SQLite';
MERGE (analytics_stream:Component {name:'Analytics Stream Processor', scope:'projected_final'})
	ON CREATE SET analytics_stream.type='Analytics', analytics_stream.status='planned', analytics_stream.technology='Event Processing';
MERGE (publisher_adapter:Component {name:'Publisher Adapter Framework', scope:'projected_final'})
	ON CREATE SET publisher_adapter.type='Abstraction', publisher_adapter.status='planned', publisher_adapter.purpose='Multi-channel publishing';
MERGE (edge_cache:Component {name:'Edge Cache Layer', scope:'projected_final'})
	ON CREATE SET edge_cache.type='Edge', edge_cache.status='planned', edge_cache.technology='CDN/Edge Functions';

// ===================== AGENT TEAMS & AGENTS =================
MERGE (orchestrator:Agent {name:'Orchestrator Agent', scope:'projected_final'})
	ON CREATE SET orchestrator.role='Coordinator', orchestrator.status='target';
MERGE (market_analytics:Agent {name:'Market Analytics Agent', scope:'projected_final'})
	ON CREATE SET market_analytics.role='Signal Intake', market_analytics.status='target';
MERGE (content_strategy_team:AgentTeam {name:'Content Strategy Team', scope:'projected_final'})
	ON CREATE SET content_strategy_team.focus='Query Coverage + Psychographics';
MERGE (ai_seo_agent:Agent {name:'AI SEO Optimization Agent', scope:'projected_final'})
	ON CREATE SET ai_seo_agent.role='Semantic & Conversational SEO';
MERGE (psychographic_agent:Agent {name:'Psychographic Targeting Agent', scope:'projected_final'})
	ON CREATE SET psychographic_agent.role='Persona & Motivation Mapping';
MERGE (content_generation_agent:Agent {name:'Content Generation Agent', scope:'projected_final'})
	ON CREATE SET content_generation_agent.role='Draft & Optimization';
MERGE (monetization_agent:Agent {name:'Monetization Agent', scope:'projected_final'})
	ON CREATE SET monetization_agent.role='Offer Mapping & Revenue Optimization';
MERGE (performance_agent:Agent {name:'Performance Analytics Agent', scope:'projected_final'})
	ON CREATE SET performance_agent.role='Coverage & Anomaly Detection';
MERGE (platform_team:AgentTeam {name:'Platform Distribution Team', scope:'projected_final'})
	ON CREATE SET platform_team.focus='Adaptation & Syndication';
MERGE (content_multiplication_agent:Agent {name:'Content Multiplication Agent', scope:'projected_final'})
	ON CREATE SET content_multiplication_agent.role='Atomization & Derivatives';
MERGE (platform_optimization_agent:Agent {name:'Platform Optimization Agent', scope:'projected_final'})
	ON CREATE SET platform_optimization_agent.role='Channel Native Optimization';
MERGE (community_agent:Agent {name:'Community Growth Agent', scope:'projected_final'})
	ON CREATE SET community_agent.role='Engagement & UGC';
MERGE (publisher_agent:Agent {name:'Publisher Adapter Agent', scope:'projected_final'})
	ON CREATE SET publisher_agent.role='Channel Publishing Orchestration';

// ===================== OPTIMIZATION & ANALYTICS SYSTEMS =====
MERGE (ai_seo_optimizer:System {name:'AI SEO Optimizer', scope:'projected_final'})
	ON CREATE SET ai_seo_optimizer.type='Optimization', ai_seo_optimizer.capabilities='Conversational queries, schema, topical graphs';
MERGE (psychographic_engine:System {name:'Psychographic Engine', scope:'projected_final'})
	ON CREATE SET psychographic_engine.type='Optimization', psychographic_engine.capabilities='Behavioral segmentation, triggers';
MERGE (coverage_scorer:System {name:'Semantic Coverage Scorer', scope:'projected_final'})
	ON CREATE SET coverage_scorer.type='Analytics', coverage_scorer.capabilities='Ontology gap analysis';
MERGE (monetization_engine:System {name:'Monetization Engine', scope:'projected_final'})
	ON CREATE SET monetization_engine.type='Optimization', monetization_engine.capabilities='Offer slotting, revenue heuristics';
MERGE (anomaly_detector:System {name:'Anomaly Detector', scope:'projected_final'})
	ON CREATE SET anomaly_detector.type='Analytics', anomaly_detector.capabilities='Engagement & performance drift';
MERGE (embedding_index:System {name:'Embedding Index', scope:'projected_final'})
	ON CREATE SET embedding_index.type='Retrieval', embedding_index.mode='Vector';
MERGE (keyword_index:System {name:'Keyword/Token Index', scope:'projected_final'})
	ON CREATE SET keyword_index.type='Retrieval', keyword_index.mode='Lexical';
MERGE (fusion_ranker:System {name:'Hybrid Fusion Ranker', scope:'projected_final'})
	ON CREATE SET fusion_ranker.type='Retrieval', fusion_ranker.mode='Rank Fusion';

// ===================== KNOWLEDGE GRAPH / ONTOLOGY ===========
MERGE (ontology:Knowledge {name:'Optimization Ontology', scope:'projected_final'})
	ON CREATE SET ontology.version='v0.1', ontology.layers='Category>Lever>Tactic';
MERGE (rulebooks:Knowledge {name:'Agent Rulebooks', scope:'projected_final'})
	ON CREATE SET rulebooks.coverage='ContentStrategy, Monetization, Performance';
MERGE (tactics_lib:Knowledge {name:'Tactics Library', scope:'projected_final'})
	ON CREATE SET tactics_lib.planned_count=20;

// Example categories & levers (minimal seed)
MERGE (cat_ai:Category {name:'AI Search Optimization', scope:'projected_final'});
MERGE (lev_conv:Lever {name:'Conversational Query Coverage', scope:'projected_final'});
MERGE (cat_psy:Category {name:'Psychographic Targeting', scope:'projected_final'});
MERGE (lev_mot:Lever {name:'Motivation Trigger Mapping', scope:'projected_final'});
MERGE (cat_mon:Category {name:'Monetization', scope:'projected_final'});
MERGE (lev_offer:Lever {name:'Offer Alignment Mapping', scope:'projected_final'});

// (Replaced below with property-based relationship section to avoid variable-scope node duplication)

// (Removed variable-only relationship MERGEs; see new section RELATIONSHIPS REBUILD)

// ===================== PHASES (Revised) =====================
MERGE (phase9:Phase {name:'Phase 9 KB & RAG', scope:'projected_final'})
	ON CREATE SET phase9.status='in-progress', phase9.priority='critical';
MERGE (phaseAgents:Phase {name:'Agent Expansion', scope:'projected_final'})
	ON CREATE SET phaseAgents.status='planned';
MERGE (phaseHybrid:Phase {name:'Hybrid Retrieval', scope:'projected_final'})
	ON CREATE SET phaseHybrid.status='planned';
MERGE (phaseRulebooks:Phase {name:'Rulebook Validation Hooks', scope:'projected_final'})
	ON CREATE SET phaseRulebooks.status='planned';
MERGE (phaseDistribution:Phase {name:'Distribution Framework', scope:'projected_final'})
	ON CREATE SET phaseDistribution.status='planned';
MERGE (phaseMonetization:Phase {name:'Monetization Optimization', scope:'projected_final'})
	ON CREATE SET phaseMonetization.status='planned';
MERGE (phasePerf:Phase {name:'Performance Analytics', scope:'projected_final'})
	ON CREATE SET phasePerf.status='planned';
MERGE (phaseIntegrate:Phase {name:'Full Integration', scope:'projected_final'})
	ON CREATE SET phaseIntegrate.status='planned';
MERGE (phaseScale:Phase {name:'Scale & Hardening', scope:'projected_final'})
	ON CREATE SET phaseScale.status='planned';

// (Phase dependency edges recreated in RELATIONSHIPS REBUILD section)

// ===================== RELATIONSHIPS REBUILD =====================
// NOTE: Neo4j variable scope does not persist across statements; using bare variables like (ai_seo_agent) in a new statement creates anonymous nodes.
// We instead MATCH nodes by stable identifying properties and MERGE relationships, preventing isolated duplicates.

// Category -> Lever
UNWIND [
	['AI Search Optimization','Conversational Query Coverage'],
	['Psychographic Targeting','Motivation Trigger Mapping'],
	['Monetization','Offer Alignment Mapping']
] AS catLev
MATCH (c:Category {name:catLev[0], scope:'projected_final'})
MATCH (l:Lever {name:catLev[1], scope:'projected_final'})
MERGE (c)-[:HAS_LEVER]->(l);

// Agents USE Systems
UNWIND [
	['AI SEO Optimization Agent','AI SEO Optimizer'],
	['Psychographic Targeting Agent','Psychographic Engine'],
	['Content Generation Agent','Semantic Coverage Scorer'],
	['Performance Analytics Agent','Semantic Coverage Scorer'],
	['Performance Analytics Agent','Anomaly Detector'],
	['Monetization Agent','Monetization Engine']
] AS usePair
MATCH (a:Agent {name:usePair[0], scope:'projected_final'})
MATCH (s:System {name:usePair[1], scope:'projected_final'})
MERGE (a)-[:USES]->(s);

// RAG Pipeline uses retrieval systems
UNWIND ['Embedding Index','Keyword/Token Index','Hybrid Fusion Ranker'] AS sysName
MATCH (rp:Component {name:'RAG Pipeline', scope:'projected_final'})
MATCH (s:System {name:sysName, scope:'projected_final'})
MERGE (rp)-[:USES]->(s);

// Team composition
UNWIND [
	['Content Strategy Team','AI SEO Optimization Agent'],
	['Content Strategy Team','Psychographic Targeting Agent'],
	['Content Strategy Team','Content Generation Agent'],
	['Platform Distribution Team','Content Multiplication Agent'],
	['Platform Distribution Team','Platform Optimization Agent'],
	['Platform Distribution Team','Community Growth Agent']
] AS teamPair
MATCH (t:AgentTeam {name:teamPair[0], scope:'projected_final'})
MATCH (ag:Agent {name:teamPair[1], scope:'projected_final'})
MERGE (t)-[:CONTAINS]->(ag);

// Orchestration
UNWIND [
	'Content Strategy Team','Platform Distribution Team','Monetization Agent','Performance Analytics Agent','Publisher Adapter Agent'
] AS coordTarget
MATCH (orc:Agent {name:'Orchestrator Agent', scope:'projected_final'})
MATCH (target {name:coordTarget, scope:'projected_final'})
MERGE (orc)-[:COORDINATES]->(target);

// Market analytics feeds knowledge
UNWIND ['Optimization Ontology','Tactics Library'] AS knowName
MATCH (ma:Agent {name:'Market Analytics Agent', scope:'projected_final'})
MATCH (k:Knowledge {name:knowName, scope:'projected_final'})
MERGE (ma)-[:FEEDS]->(k);

// Knowledge & Retrieval flow
UNWIND ['Agent Rulebooks','Tactics Library'] AS idxName
MATCH (kbs:Component {name:'Knowledge Base Service', scope:'projected_final'})
MATCH (k:Knowledge {name:idxName, scope:'projected_final'})
MERGE (kbs)-[:INDEXES]->(k);

MATCH (os:Component {name:'Ontology Store', scope:'projected_final'})
MATCH (ont:Knowledge {name:'Optimization Ontology', scope:'projected_final'})
MERGE (os)-[:DEFINES]->(ont);

MATCH (emb:Component {name:'Embedding Service', scope:'projected_final'})
MATCH (tlib:Knowledge {name:'Tactics Library', scope:'projected_final'})
MERGE (emb)-[:VECTORIZES]->(tlib);

MATCH (emb)-[:VECTORIZES]->(tlib)
MATCH (eIdx:System {name:'Embedding Index', scope:'projected_final'})
MERGE (emb)-[:POWERS]->(eIdx);

MATCH (kbs)-[:INDEXES]->(tlib)
MATCH (kIdx:System {name:'Keyword/Token Index', scope:'projected_final'})
MERGE (kbs)-[:POWERS]->(kIdx);

UNWIND ['Embedding Index','Keyword/Token Index'] AS fuseIdx
MATCH (fr:System {name:'Hybrid Fusion Ranker', scope:'projected_final'})
MATCH (idx:System {name:fuseIdx, scope:'projected_final'})
MERGE (fr)-[:FUSES]->(idx);

MATCH (rp:Component {name:'RAG Pipeline', scope:'projected_final'})
MATCH (fr:System {name:'Hybrid Fusion Ranker', scope:'projected_final'})
MERGE (rp)-[:QUERIES]->(fr);

UNWIND ['Content Generation Agent','AI SEO Optimization Agent','Monetization Agent','Performance Analytics Agent'] AS ctxAgent
MATCH (a:Agent {name:ctxAgent, scope:'projected_final'})
MATCH (rp:Component {name:'RAG Pipeline', scope:'projected_final'})
MERGE (a)-[:REQUESTS_CONTEXT]->(rp);

// Publishing & distribution
MATCH (pubA:Agent {name:'Publisher Adapter Agent', scope:'projected_final'})
MATCH (pubF:Component {name:'Publisher Adapter Framework', scope:'projected_final'})
MERGE (pubA)-[:USES]->(pubF);

UNWIND ['Next.js Frontend','Platform Optimization Agent'] AS pubTarget
MATCH (pubF:Component {name:'Publisher Adapter Framework', scope:'projected_final'})
MATCH (pt {name:pubTarget, scope:'projected_final'})
MERGE (pubF)-[:PUBLISHES_TO]->(pt);

MATCH (ver:Component {name:'Vercel Edge', scope:'projected_final'})
MATCH (nx:Component {name:'Next.js Frontend', scope:'projected_final'})
MERGE (ver)-[:DEPLOYS]->(nx);

MATCH (nx:Component {name:'Next.js Frontend', scope:'projected_final'})
MATCH (api:Component {name:'Flask API Gateway', scope:'projected_final'})
MERGE (nx)-[:CONSUMES_API]->(api);

// Content Types & generation (single query so ctype stays in scope)
UNWIND ['Article','Product','Niche'] AS ctype
MERGE (ct:ContentType {name:ctype, scope:'projected_final'})
	ON CREATE SET ct.created=date()
WITH ct
MATCH (str:Component {name:'Strapi CMS', scope:'projected_final'})
MERGE (str)-[:STORES]->(ct);

// Content lifecycle
MATCH (genA:Agent {name:'Content Generation Agent', scope:'projected_final'})
MATCH (art:ContentType {name:'Article', scope:'projected_final'})
MERGE (genA)-[:CREATES]->(art);

MATCH (monA:Agent {name:'Monetization Agent', scope:'projected_final'})
MATCH (art:ContentType {name:'Article', scope:'projected_final'})
MERGE (monA)-[:ANNOTATES]->(art);

MATCH (perfA:Agent {name:'Performance Analytics Agent', scope:'projected_final'})
MATCH (art:ContentType {name:'Article', scope:'projected_final'})
MERGE (perfA)-[:EVALUATES]->(art);

// Analytics & feedback
MATCH (nx:Component {name:'Next.js Frontend', scope:'projected_final'})
MATCH (as:Component {name:'Analytics Stream Processor', scope:'projected_final'})
MERGE (nx)-[:EMITS_EVENTS]->(as);

UNWIND ['Performance Analytics Agent','Monetization Agent'] AS feedAgent
MATCH (as:Component {name:'Analytics Stream Processor', scope:'projected_final'})
MATCH (ag {name:feedAgent, scope:'projected_final'})
MERGE (as)-[:FEEDS]->(ag);

MATCH (perfA:Agent {name:'Performance Analytics Agent', scope:'projected_final'})
MATCH (cov:System {name:'Semantic Coverage Scorer', scope:'projected_final'})
MERGE (perfA)-[:UPDATES]->(cov);

MATCH (perfA:Agent {name:'Performance Analytics Agent', scope:'projected_final'})
MATCH (genA:Agent {name:'Content Generation Agent', scope:'projected_final'})
MERGE (perfA)-[:TRIGGERS_TASK]->(genA);

// Business goals & enablement
UNWIND [
	['Reach Expansion','10x distribution'],
	['Operational Efficiency','90% manual reduction'],
	['Revenue Uplift','3x RPM'],
	['Quality & Coverage','>90% semantic coverage']
] AS goalData
MERGE (g:BusinessGoal {name:goalData[0], scope:'projected_final'}) ON CREATE SET g.target=goalData[1];

UNWIND [
	['AI SEO Optimizer','Quality & Coverage'],
	['Content Multiplication Agent','Reach Expansion'],
	['Monetization Engine','Revenue Uplift'],
	['Orchestrator Agent','Operational Efficiency']
] AS enablePair
MATCH (enabler {name:enablePair[0], scope:'projected_final'})
MATCH (goal:BusinessGoal {name:enablePair[1], scope:'projected_final'})
MERGE (enabler)-[:ENABLES]->(goal);

// Phase dependencies
UNWIND [
	['Phase 9 KB & RAG','Hybrid Retrieval'],
	['Hybrid Retrieval','Agent Expansion'],
	['Agent Expansion','Rulebook Validation Hooks'],
	['Rulebook Validation Hooks','Distribution Framework'],
	['Distribution Framework','Monetization Optimization'],
	['Monetization Optimization','Performance Analytics'],
	['Performance Analytics','Full Integration'],
	['Full Integration','Scale & Hardening']
] AS phasePair
MATCH (p1:Phase {name:phasePair[0], scope:'projected_final'})
MATCH (p2:Phase {name:phasePair[1], scope:'projected_final'})
MERGE (p1)-[:PREREQUISITE_FOR]->(p2);

===================== QUERY EXAMPLES =======================
1. Agent -> Systems
MATCH (a:Agent)-[:USES]->(s:System) RETURN a.name, collect(s.name);
2. Retrieval Flow
MATCH (content_generation_agent)-[:REQUESTS_CONTEXT]->(r:RAGPipeline)-[:QUERIES]->(f)-[:FUSES]->(idx) RETURN r,f,collect(idx.name);
3. Ontology Coverage Agents
MATCH (ag:Agent)-[:REQUESTS_CONTEXT]->(:RAGPipeline) RETURN DISTINCT ag.name;
4. Phase Dependency Path
MATCH path = (p:Phase)-[:PREREQUISITE_FOR*]->(q:Phase) RETURN path;

===================== VERIFICATION / INTEGRITY QUERIES =======================
A. Orphan Nodes (expect near-zero aside from Meta)
MATCH (n {scope:'projected_final'}) WHERE NOT (n)--() RETURN n.name, labels(n);

B. Agents missing primary system bindings (no :USES or :REQUESTS_CONTEXT)
MATCH (a:Agent {scope:'projected_final'})
WHERE NOT (a)-[:USES]->(:System) AND NOT (a)-[:REQUESTS_CONTEXT]->(:Component {name:'RAG Pipeline'})
RETURN a.name;

// C. Systems unused by any agent
MATCH (s:System {scope:'projected_final'}) WHERE NOT (:Agent)-[:USES]->(s) RETURN s.name;

// D. Retrieval chain completeness (agents reaching both lexical + vector indices)
MATCH (a:Agent)-[:REQUESTS_CONTEXT]->(:Component {name:'RAG Pipeline'})-[:QUERIES]->(:Component {name:'Hybrid Fusion Ranker'})-[:FUSES]->(idx:System)
WITH a, collect(DISTINCT idx.mode) AS modes RETURN a.name, modes, size(modes)=2 AS has_both_indices;

E. Ontology lever coverage
MATCH (c:Category {scope:'projected_final'}) OPTIONAL MATCH (c)-[:HAS_LEVER]->(l:Lever)
WITH c, count(l) AS lever_count RETURN c.name, lever_count, lever_count>0 AS ok;

F. Business goals enablement
MATCH (g:BusinessGoal {scope:'projected_final'}) OPTIONAL MATCH (n)-[:ENABLES]->(g)
WITH g, collect(DISTINCT n.name) AS enablers RETURN g.name, enablers, size(enablers)>0 AS has_enabler;

G. Phase linearity (starting phase + max chain depth)
MATCH (p:Phase {scope:'projected_final'}) WHERE NOT (():Phase)-[:PREREQUISITE_FOR]->(p)
CALL { WITH p MATCH path=(p)-[:PREREQUISITE_FOR*]->(q:Phase) RETURN max(length(path)) AS depth }
RETURN p.name AS starting_phase, depth;

H. Duplicate name guard
MATCH (n {scope:'projected_final'}) WITH n.name AS name, collect(labels(n)) AS lbls, count(*) AS c WHERE c>1 RETURN name,lbls,c;

I. Content production to publish path
MATCH (:Agent {name:'Content Generation Agent'})-[:CREATES]->(:ContentType)<-[:STORES]-(:Component {name:'Strapi CMS'})
OPTIONAL MATCH (:Agent {name:'Publisher Adapter Agent'})-[:USES]->(:Component {name:'Publisher Adapter Framework'})-[:PUBLISHES_TO]->(:Component {name:'Next.js Frontend'})
RETURN 'ok' AS pipeline;

J. Feedback loop presence
MATCH (:Agent {name:'Performance Analytics Agent'})-[:UPDATES]->(:System {name:'Semantic Coverage Scorer'})
OPTIONAL MATCH (:Agent {name:'Performance Analytics Agent'})-[:TRIGGERS_TASK]->(:Agent {name:'Content Generation Agent'}) RETURN 'coverage_loop' AS loop, count(*)>0 AS triggers_regen;

K. Phase status summary
MATCH (p:Phase {scope:'projected_final'}) RETURN p.name, p.status ORDER BY p.name;

L. Goal alignment aggregate
MATCH (g:BusinessGoal {scope:'projected_final'}) OPTIONAL MATCH (n)-[:ENABLES]->(g)
WITH g, count(n) AS c WITH collect({goal:g.name,enablers:c}) AS rows, sum(c) AS total RETURN rows,total;

M. RAG dependency readiness
MATCH (:Component {name:'RAG Pipeline'})-[:QUERIES]->(:Component {name:'Hybrid Fusion Ranker'})-[:FUSES]->(idx:System)
WITH collect(DISTINCT idx.mode) AS modes MATCH (a:Agent)-[:REQUESTS_CONTEXT]->(:Component {name:'RAG Pipeline'})
WITH modes, collect(DISTINCT a.name) AS agents RETURN modes, size(modes)=2 AS has_both_indices, agents;

===================== MAINTENANCE UTILITIES (COMMENTED) ======================
Refresh (destructive): MATCH (n {scope:'projected_final'}) DETACH DELETE n;
Reapply: :source neo4j_projected_final_architecture_kg.cypher
Export via APOC:
CALL apoc.export.json.query("MATCH (n {scope:'projected_final'}) OPTIONAL MATCH (n)-[r]->(m {scope:'projected_final'}) RETURN n,r,m","projected_final_export.json",{});

===================== END OF PROJECTED FINAL =================

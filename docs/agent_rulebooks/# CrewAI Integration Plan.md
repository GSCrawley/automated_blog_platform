**\# Auto-Blog-Platform**

**\# CrewAI Integration Plan: Real-Time Research, Target Blog Knowledge Graph & Editor Agent System**

\*\*Document Purpose:\*\* Step-by-step instructional guide for the Orchestrator to implement the two missing capability pillars of the automated blog platform:  
1\. Real-time research as the \*\*first step\*\* of every stage in the blog creation process  
2\. A \*\*Target Blog Knowledge Graph\*\* that accumulates ideal-state intelligence across all runs  
3\. A \*\*dedicated Editor/QA Agent crew\*\* that checks all completed work against the Knowledge Graph target

\---

\#\# Current State Summary

The project has a solid 6-agent custom foundation (\`orchestrator\`, \`market\_analytics\`, \`author\`, \`editor\`, \`product\_scout\`, \`affiliate\_ops\`) running on a Flask \+ Redis \+ SQLite \+ React stack. The key gap is:

\- All research methods return \*\*mock/hardcoded data\*\* — no real-time lookups  
\- The existing knowledge base (\`knowledge\_base.py\`) is \*\*keyword-only\*\* with no vector embeddings and no cross-run persistence  
\- The \`EditorAgent\` reviews layout but does \*\*not check content against any ideal-state target\*\*  
\- There is \*\*no dedicated research phase\*\* triggering before each stage of the pipeline  
\- CrewAI framework is \*\*not yet installed or used\*\* — the current agents are a custom Redis-based system

This plan migrates the core agent intelligence layer to \*\*CrewAI\*\* while preserving the existing Flask API, Redis messaging, SQLite models, and React frontend that are already working.

\---

**\#\# Architecture Overview: What We Are Building**

**\`\`\`**  
**BlogCreationFlow (CrewAI Flow)**  
**├── Stage 0: Intelligence Gathering (runs FIRST, before any stage)**  
**│   └── ResearchCrew → writes to TargetBlogKnowledgeGraph**  
**│       ├── NicheTrendResearcher**  
**│       ├── AffiliateOpportunityScout**  
**│       ├── PsychologyAndUXResearcher**  
**│       └── CompetitorIntelligenceAgent**  
**│**  
**├── Stage 1: Strategy (informed by Knowledge Graph)**  
**│   └── ContentStrategyCrew**  
**│       ├── TopicClusterPlanner**  
**│       └── KeywordAndIntentMapper**  
**│**  
**├── Stage 2: Content Creation**  
**│   └── ContentCreationCrew**  
**│       ├── AuthorAgent (upgraded)**  
**│       └── MonetizationAgent**  
**│**  
**├── Stage 3: QA & Editorial Review**  
**│   └── EditorCrew (NEW — checks against TargetBlogKnowledgeGraph)**  
**│       ├── ContentQualityEditor**  
**│       ├── MonetizationAuditor**  
**│       ├── SEOAndUXReviewer**  
**│       └── ComplianceChecker**  
**│**  
**└── Stage 4: Publish & Monitor**  
    **└── PublisherAdapter (future)**  
**\`\`\`**

**The \*\*TargetBlogKnowledgeGraph\*\* is the shared, persistent CrewAI \`Memory\` instance that all crews read from and the ResearchCrew writes to. It represents the system's ever-improving picture of what the \*\*ideal finished blog\*\* looks like.**

**\---**

**\#\# Step 1: Install CrewAI and Dependencies**

**\#\#\# 1.1 Update \`requirements.txt\`**

**Add the following to the root \`requirements.txt\`:**

**\`\`\`**  
**crewai\>=0.100.0**  
**crewai-tools\>=0.40.0**  
**tavily-python\>=0.5.0**  
**lancedb\>=0.18.0**  
**\`\`\`**

\*\*Why these packages:\*\*  
\- \`crewai\` — core framework for agents, tasks, crews, flows, and unified memory  
\- \`crewai-tools\` — provides \`SerperDevTool\`, \`TavilySearchTool\`, \`FirecrawlScrapeWebsiteTool\`, \`WebsiteSearchTool\`, \`ScrapeWebsiteTool\`  
\- \`tavily-python\` — Tavily AI search API (recommended over SerperDev for real-time, structured research)  
\- \`lancedb\` — CrewAI's default unified memory storage backend (already used internally)

**\#\#\# 1.2 Environment Variables**

Add to \`.env\` (and \`config.py\`):

\`\`\`  
TAVILY\_API\_KEY=your\_tavily\_key  
SERPER\_API\_KEY=your\_serper\_key  
OPENAI\_API\_KEY=your\_openai\_key  \# already present  
CREWAI\_STORAGE\_DIR=./data/crewai\_memory  
\`\`\`

\`CREWAI\_STORAGE\_DIR\` tells CrewAI where to persist the LanceDB memory store across runs. Use a path inside the project that is NOT \`/tmp\` (which is wiped on restart).

\---

\#\# Step 2: Create the Target Blog Knowledge Graph (Persistent Memory)

The Knowledge Graph is a configured \*\*CrewAI \`Memory\` instance\*\* shared across all crews. It accumulates intelligence about the ideal blog across every run.

\#\#\# 2.1 Create \`core/crewai\_system/knowledge\_graph.py\`

\`\`\`python  
from crewai import Memory

\# Target Blog Knowledge Graph — the shared persistent intelligence layer.  
\# Tuned for a "knowledge accumulation" use case:  
\# \- High importance weight: what makes a blog successful matters more than recency  
\# \- Long half-life: strategic insights remain valid for months  
\# \- Low recency weight: old research is still useful  
TARGET\_BLOG\_KG \= Memory(  
    storage="./data/crewai\_memory/target\_blog\_kg",  
    recency\_weight=0.15,  
    semantic\_weight=0.55,  
    importance\_weight=0.30,  
    recency\_half\_life\_days=90,  
    consolidation\_threshold=0.82,  \# Merge near-duplicate insights  
    embedder={  
        "provider": "openai",  
        "config": {"model\_name": "text-embedding-3-small"}  
    },  
    llm="gpt-4o-mini",  
)  
\`\`\`

\*\*Scope structure\*\* the Research Crew will populate:

\`\`\`  
/target\_blog  
  /target\_blog/trending\_topics        — what topics are hot right now  
  /target\_blog/affiliate\_programs     — best-paying programs, commission rates  
  /target\_blog/product\_opportunities  — products with high revenue potential  
  /target\_blog/psychology             — proven marketing tactics, writing styles  
  /target\_blog/ux\_and\_layout         — trending blog UI, CTA placement  
  /target\_blog/competitor\_intel       — what top blogs are doing well  
  /target\_blog/content\_standards      — ideal quality benchmarks  
  /target\_blog/monetization\_patterns  — what monetization setups work best  
\`\`\`

\*\*Important:\*\* This memory object must be imported and shared — never instantiated more than once per process. Use it as a module-level singleton.

\---

\#\# Step 3: Create the Research Crew (Stage 0 — Runs First, Every Time)

This crew runs \*\*before any other stage\*\* and updates the Knowledge Graph with real-time data.

\#\#\# 3.1 Create \`core/crewai\_system/crews/research\_crew/\`

\#\#\#\# File: \`config/agents.yaml\`

\`\`\`yaml  
niche\_trend\_researcher:  
  role: "Real-Time Niche Trend Analyst"  
  goal: \>  
    Discover what topics, questions, products, and content formats are currently  
    trending in the {niche} niche. Identify emerging keywords, seasonal patterns,  
    and the exact search intent of the target audience right now.  
  backstory: \>  
    You are a world-class market researcher with expertise in identifying profitable  
    content opportunities before they peak. You use real-time data from search  
    engines, social media signals, and Google Trends to surface high-demand topics  
    with low competition. Your research directly determines which content gets created.  
  tools:  
    \- TavilySearchTool  
    \- SerperDevTool  
    \- WebsiteSearchTool

affiliate\_opportunity\_scout:  
  role: "Affiliate Program Revenue Analyst"  
  goal: \>  
    Identify the most lucrative affiliate programs, products, and services in the  
    {niche} niche. Rank opportunities by commission rate, EPC (earnings per click),  
    cookie duration, and conversion rate. Identify which programs will pay to  
    advertise directly on the blog.  
  backstory: \>  
    You are a seasoned affiliate marketer who has generated millions in commissions  
    across dozens of niches. You know exactly which networks (ShareASale, CJ Affiliate,  
    Impact, Amazon Associates, direct programs) pay the best rates, which products  
    convert at the highest rates, and how to maximize revenue per visitor.  
  tools:  
    \- TavilySearchTool  
    \- SerperDevTool  
    \- FirecrawlScrapeWebsiteTool

psychology\_and\_ux\_researcher:  
  role: "Consumer Psychology & UX Intelligence Specialist"  
  goal: \>  
    Research which marketing tactics, writing styles, emotional triggers, social  
    proof formats, and blog UI/UX patterns produce the highest conversion rates  
    in the {niche} niche. Identify trending blog layouts, CTA placement strategies,  
    and psychographic targeting techniques that are working right now.  
  backstory: \>  
    You combine behavioral psychology, conversion rate optimization (CRO), and  
    UX research to understand exactly why visitors buy. You are an expert in  
    decision architecture, loss aversion triggers, authority signals, FOMO mechanics,  
    and the psychological principles that turn readers into buyers.  
  tools:  
    \- TavilySearchTool  
    \- SerperDevTool  
    \- FirecrawlScrapeWebsiteTool

competitor\_intelligence\_agent:  
  role: "Competitor Blog Intelligence Analyst"  
  goal: \>  
    Analyze the top 5 performing blogs in the {niche} niche. Document their content  
    structure, monetization strategies, affiliate products used, UI patterns,  
    writing style, CTA approaches, and identify their content gaps. Extract what  
    makes them successful and where we can do better.  
  backstory: \>  
    You are a competitive intelligence specialist who reverse-engineers successful  
    content strategies. You do not copy — you identify patterns, extract principles,  
    and synthesize insights that inform a superior strategy.  
  tools:  
    \- TavilySearchTool  
    \- SerperDevTool  
    \- FirecrawlScrapeWebsiteTool  
    \- WebsiteSearchTool  
\`\`\`

\#\#\#\# File: \`config/tasks.yaml\`

\`\`\`yaml  
research\_trending\_topics:  
  description: \>  
    Conduct real-time research on trending topics in the {niche} niche.  
    Use Tavily and Serper to search:  
    1\. "trending {niche} topics {current\_year}"  
    2\. "{niche} most searched questions right now"  
    3\. "what is trending in {niche} this month"  
    4\. "{niche} emerging trends {current\_year}"  
      
    For each trend found, record: topic name, search volume estimate, trend  
    trajectory (rising/peaked/declining), best content format, target audience  
    psychographic profile, and monetization alignment.  
      
    Save ALL findings to the Target Blog Knowledge Graph under  
    scope: /target\_blog/trending\_topics  
      
    Also query the Knowledge Graph for past research on this niche to identify  
    what has changed since the last run.  
  expected\_output: \>  
    A structured JSON report with fields:  
    \- top\_10\_trending\_topics: list of {topic, trend\_score, search\_volume, format, monetization\_fit}  
    \- emerging\_keywords: list of {keyword, intent, competition\_level, estimated\_cpc}  
    \- audience\_insights: {primary\_psychographic, key\_pain\_points, buying\_triggers}  
    \- recommended\_priority\_topics: top 3 with reasoning  
  agent: niche\_trend\_researcher

research\_affiliate\_opportunities:  
  description: \>  
    Research the most lucrative affiliate opportunities in the {niche} niche.  
    Search for:  
    1\. "best affiliate programs {niche} {current\_year} highest commission"  
    2\. "{niche} affiliate programs commission rates comparison"  
    3\. "direct advertising {niche} blogs CPM rates {current\_year}"  
    4\. "{niche} products highest EPC affiliate"  
      
    For each opportunity: program name, network, commission rate/structure,   
    cookie duration, conversion rate if available, EPC, payout frequency,  
    approval difficulty, best-performing products.  
      
    Also research: which companies pay directly for ad placements on blogs  
    in this niche, typical CPM/CPC rates, and any exclusive high-paying programs.  
      
    Save ALL findings to scope: /target\_blog/affiliate\_programs  
    and /target\_blog/product\_opportunities  
  expected\_output: \>  
    A structured JSON report with:  
    \- top\_affiliate\_programs: list of {name, network, commission\_rate, cookie\_days,  
      avg\_epc, products, approval\_difficulty, notes}  
    \- direct\_advertising\_opportunities: list of {company, contact, rate\_type,   
      estimated\_rate, requirements}  
    \- recommended\_primary\_programs: top 3 with revenue projections  
    \- product\_opportunities: top 10 products to feature with revenue potential  
  agent: affiliate\_opportunity\_scout  
  context:  
    \- research\_trending\_topics

research\_psychology\_and\_ux:  
  description: \>  
    Research proven psychology tactics, writing styles, and UX patterns that  
    maximize revenue in the {niche} niche. Search for:  
    1\. "highest converting blog layouts {niche} {current\_year}"  
    2\. "affiliate blog CTA placement best practices conversion rate"  
    3\. "{niche} blog copywriting psychological triggers"  
    4\. "trending blog UI design {current\_year} high converting"  
    5\. "email list building tactics {niche} best performing"  
    6\. "social proof formats that convert blogs {niche}"  
      
    Research marketing psychology principles specifically proven for this niche:  
    urgency/scarcity, social proof, authority signals, loss aversion,  
    identity-based positioning, before/after framing.  
      
    Save ALL findings to scope: /target\_blog/psychology  
    and /target\_blog/ux\_and\_layout  
  expected\_output: \>  
    A structured JSON report with:  
    \- proven\_writing\_styles: list of {style, description, best\_for, example\_structure}  
    \- high\_converting\_ux\_patterns: list of {pattern, placement, expected\_lift, example}  
    \- psychological\_triggers: list of {trigger, implementation, evidence}  
    \- email\_capture\_strategies: top 3 with opt-in rate benchmarks  
    \- cta\_templates: 5 proven CTA formats for this niche  
    \- trending\_blog\_layouts: description of what is working now  
  agent: psychology\_and\_ux\_researcher  
  context:  
    \- research\_trending\_topics  
    \- research\_affiliate\_opportunities

analyze\_top\_competitors:  
  description: \>  
    Identify and analyze the top 5 performing blogs in the {niche} niche.  
    Use Tavily to search "top {niche} blogs {current\_year}" and FirecrawlScrape  
    to extract content structure, monetization elements, and UI patterns from  
    each blog's homepage and 2-3 sample articles.  
      
    For each competitor document:  
    \- Content structure (H1/H2/H3 patterns, word count, media usage)  
    \- Affiliate products featured and placement strategy  
    \- CTA design, copy, and placement  
    \- Email capture mechanisms  
    \- Internal linking structure  
    \- Writing style and tone  
    \- What they are doing WELL  
    \- Identifiable CONTENT GAPS we can exploit  
      
    Synthesize this into a "Target Blog Blueprint" — the composite ideal  
    blog based on what the best performers are doing.  
      
    Save ALL findings to scope: /target\_blog/competitor\_intel  
    and /target\_blog/content\_standards  
  expected\_output: \>  
    A structured JSON report with:  
    \- competitor\_profiles: list of 5 {name, url, strengths, weaknesses, key\_tactics}  
    \- content\_gaps: list of {gap\_description, opportunity\_score, recommended\_approach}  
    \- target\_blog\_blueprint: {  
        ideal\_article\_structure, ideal\_word\_count, ideal\_cta\_count,  
        ideal\_affiliate\_density, recommended\_writing\_tone,  
        must\_have\_sections, monetization\_pattern  
      }  
    \- differentiation\_opportunities: top 5 ways to outperform competitors  
  agent: competitor\_intelligence\_agent  
  context:  
    \- research\_trending\_topics  
    \- research\_affiliate\_opportunities  
    \- research\_psychology\_and\_ux  
\`\`\`

\#\#\#\# File: \`research\_crew.py\`

\`\`\`python  
from crewai import Agent, Crew, Task, Process  
from crewai.project import CrewBase, agent, task, crew, after\_kickoff  
from crewai\_tools import TavilySearchTool, SerperDevTool, FirecrawlScrapeWebsiteTool, WebsiteSearchTool  
from crewai.agents.agent\_builder.base\_agent import BaseAgent  
from typing import List  
from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG

@CrewBase  
class ResearchCrew:  
    """  
    Stage 0: Real-Time Intelligence Gathering  
      
    This crew runs FIRST before any stage of the blog creation pipeline.  
    It populates the Target Blog Knowledge Graph with current intelligence  
    about trends, affiliate opportunities, psychology, and competitor strategies.  
    """

    agents: List\[BaseAgent\]  
    tasks: List\[Task\]  
    agents\_config \= 'config/agents.yaml'  
    tasks\_config \= 'config/tasks.yaml'

    def \_build\_tools(self):  
        return {  
            'tavily': TavilySearchTool(),  
            'serper': SerperDevTool(),  
            'firecrawl': FirecrawlScrapeWebsiteTool(),  
            'website\_search': WebsiteSearchTool(),  
        }

    @agent  
    def niche\_trend\_researcher(self) \-\> Agent:  
        tools \= self.\_build\_tools()  
        return Agent(  
            config=self.agents\_config\['niche\_trend\_researcher'\],  
            tools=\[tools\['tavily'\], tools\['serper'\], tools\['website\_search'\]\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/trending\_topics"),  
            verbose=True,  
            max\_iter=5,  
        )

    @agent  
    def affiliate\_opportunity\_scout(self) \-\> Agent:  
        tools \= self.\_build\_tools()  
        return Agent(  
            config=self.agents\_config\['affiliate\_opportunity\_scout'\],  
            tools=\[tools\['tavily'\], tools\['serper'\], tools\['firecrawl'\]\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/affiliate\_programs"),  
            verbose=True,  
            max\_iter=5,  
        )

    @agent  
    def psychology\_and\_ux\_researcher(self) \-\> Agent:  
        tools \= self.\_build\_tools()  
        return Agent(  
            config=self.agents\_config\['psychology\_and\_ux\_researcher'\],  
            tools=\[tools\['tavily'\], tools\['serper'\], tools\['firecrawl'\]\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/psychology"),  
            verbose=True,  
            max\_iter=5,  
        )

    @agent  
    def competitor\_intelligence\_agent(self) \-\> Agent:  
        tools \= self.\_build\_tools()  
        return Agent(  
            config=self.agents\_config\['competitor\_intelligence\_agent'\],  
            tools=\[tools\['tavily'\], tools\['serper'\], tools\['firecrawl'\], tools\['website\_search'\]\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/competitor\_intel"),  
            verbose=True,  
            max\_iter=7,  
        )

    @task  
    def research\_trending\_topics(self) \-\> Task:  
        return Task(config=self.tasks\_config\['research\_trending\_topics'\])

    @task  
    def research\_affiliate\_opportunities(self) \-\> Task:  
        return Task(config=self.tasks\_config\['research\_affiliate\_opportunities'\])

    @task  
    def research\_psychology\_and\_ux(self) \-\> Task:  
        return Task(config=self.tasks\_config\['research\_psychology\_and\_ux'\])

    @task  
    def analyze\_top\_competitors(self) \-\> Task:  
        return Task(config=self.tasks\_config\['analyze\_top\_competitors'\])

    @after\_kickoff  
    def persist\_to\_knowledge\_graph(self, output):  
        """  
        After the research crew completes, explicitly save the consolidated  
        findings to the Target Blog Knowledge Graph for all future crews to use.  
        """  
        facts \= TARGET\_BLOG\_KG.extract\_memories(str(output.raw))  
        TARGET\_BLOG\_KG.remember\_many(  
            facts,  
            \# Let the LLM infer the best scope under /target\_blog  
        )  
        return output

    @crew  
    def crew(self) \-\> Crew:  
        return Crew(  
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,  \# Each researcher builds on the previous  
            memory=TARGET\_BLOG\_KG,       \# All agents share the Knowledge Graph  
            planning=True,               \# Pre-plan task execution for better coordination  
            planning\_llm="gpt-4o",       \# Use strong model for planning  
            verbose=True,  
            output\_log\_file="./logs/research\_crew.json",  
        )  
\`\`\`

\---

\#\# Step 4: Create the Content Strategy Crew (Stage 1\)

This crew reads from the Knowledge Graph to plan what to create.

\#\#\# 4.1 Create \`core/crewai\_system/crews/content\_strategy\_crew/\`

\#\#\#\# Key agents to implement (following same YAML \+ class pattern as above):

\*\*\`content\_strategist\`\*\*  
\- Role: "Content Strategy Director"  
\- Goal: Build a content plan for the {niche} blog based on the research findings in the Knowledge Graph  
\- Tools: \`TavilySearchTool\`, \`RagTool\` (pointed at the Target Blog KG)  
\- Memory: Scoped to \`/target\_blog/content\_standards\`  
\- Key task: \`plan\_content\_calendar\` — query KG for trending topics and affiliate opportunities, output a 30-article content plan with keyword targets, content types, and affiliate alignment for each article

\*\*\`keyword\_and\_intent\_mapper\`\*\*  
\- Role: "SEO & Search Intent Specialist"  
\- Goal: Map high-value keywords to content clusters, validate search volumes, and define the intent behind each target keyword  
\- Tools: \`SerperDevTool\`, \`TavilySearchTool\`  
\- Key task: \`map\_keywords\_to\_intent\` — takes content plan, enriches with keyword data

\*\*Crew configuration:\*\*  
\`\`\`python  
Crew(  
    agents=self.agents,  
    tasks=self.tasks,  
    process=Process.sequential,  
    memory=TARGET\_BLOG\_KG,  \# Read-only recommended; writes go to /target\_blog/content\_standards  
    verbose=True,  
)  
\`\`\`

\*\*Critical: Before kickoff, recall from KG:\*\*  
\`\`\`python  
@before\_kickoff  
def load\_research\_context(self, inputs):  
    \# Pull latest research from Knowledge Graph  
    trending \= TARGET\_BLOG\_KG.recall(  
        "trending topics affiliate opportunities",  
        scope="/target\_blog",  
        limit=20  
    )  
    inputs\['research\_context'\] \= "\\n".join(  
        m.record.content for m in trending  
    )  
    return inputs  
\`\`\`

\---

\#\# Step 5: Create the Content Creation Crew (Stage 2\)

\#\#\# 5.1 Create \`core/crewai\_system/crews/content\_creation\_crew/\`

\#\#\#\# Key agents:

\*\*\`author\_agent\`\*\* (replaces/wraps the existing \`AuthorAgent\`)  
\- Role: "Expert Affiliate Marketing Content Writer"  
\- Goal: Write a comprehensive, psychologically optimized article on {topic} that ranks in search, provides genuine value, and generates affiliate revenue  
\- Tools: \`TavilySearchTool\`, \`SerperDevTool\`  
\- Memory: Scoped view of \`/target\_blog\` (read) \+ \`/content/drafts\` (write)  
\- Key backstory must reference: the target blog blueprint, writing psychology, affiliate density guidelines

\*\*\`monetization\_specialist\`\*\* (replaces/wraps existing \`AffiliateOpsAgent\` logic)  
\- Role: "Affiliate Monetization Specialist"  
\- Goal: Integrate the optimal affiliate links, CTAs, email capture prompts, and ad placements into the draft content without compromising reader trust  
\- Tools: Custom \`AffiliateLinksLookupTool\` (wraps existing DB queries)  
\- Memory: Scoped to \`/target\_blog/affiliate\_programs\`  
\- Constraint: Maximum 1 CTA per 250 words; never monetize before establishing trust (first 300 words)

\*\*Task flow:\*\*  
\`\`\`  
research\_article\_topic (author with Tavily)  
    → draft\_article\_outline (author, using KG context)  
        → write\_article\_draft (author)  
            → integrate\_monetization (monetization\_specialist)  
\`\`\`

\*\*Critical — Before each article task, recall from KG:\*\*  
\`\`\`python  
\# In the author's task description, include:  
"""  
Before writing, recall from the Target Blog Knowledge Graph:  
\- The ideal writing style and psychological triggers for {niche}  
\- The target blog blueprint (article structure, word count targets)  
\- The top affiliate products to feature  
\- Any content standards or quality benchmarks stored in the KG

Use these insights to inform every decision in your writing.  
"""  
\`\`\`

\---

\#\# Step 6: Create the Editor Crew (Stage 3 — The QA Gate)

This is the \*\*new secondary group of editor agents\*\* that checks all work against the Target Blog Knowledge Graph.

\#\#\# 6.1 Create \`core/crewai\_system/crews/editor\_crew/\`

\#\#\#\# File: \`config/agents.yaml\`

\`\`\`yaml  
content\_quality\_editor:  
  role: "Senior Content Quality Editor"  
  goal: \>  
    Review the completed article draft and score it against the Target Blog  
    Knowledge Graph's content standards. Identify every gap between the draft  
    and the ideal blog post this system is building toward. Provide specific,  
    actionable feedback for every deviation.  
  backstory: \>  
    You are a senior editor who has edited thousands of high-performing affiliate  
    articles. You know exactly what separates a $100/month article from a  
    $10,000/month article. You consult the Target Blog Knowledge Graph before  
    every review to ensure your standards reflect the current best practices  
    and competitive intelligence.

monetization\_auditor:  
  role: "Affiliate Monetization Auditor"  
  goal: \>  
    Audit the article for monetization completeness and compliance. Check that  
    all recommended affiliate opportunities from the Knowledge Graph are properly  
    utilized, CTA density is optimal, disclosures are present, and the revenue  
    potential of the article is maximized without compromising reader trust.  
  backstory: \>  
    You are a monetization expert who reviews content through a revenue lens.  
    You know the commission rates, conversion patterns, and placement rules  
    for every affiliate program in the Knowledge Graph. Nothing slips past you.

seo\_and\_ux\_reviewer:  
  role: "SEO & UX Quality Reviewer"    
  goal: \>  
    Review the article for SEO completeness and UX best practices. Check heading  
    structure, keyword usage, meta description, internal linking opportunities,  
    schema markup requirements, and layout against the trending UI patterns in  
    the Knowledge Graph. Score against the target blog blueprint.  
  backstory: \>  
    You are an SEO specialist and UX reviewer who ensures every article is  
    technically optimized and formatted for maximum engagement. You reference  
    the competitor intelligence and UX patterns stored in the Knowledge Graph  
    to validate every design decision.

compliance\_checker:  
  role: "Legal & Compliance Reviewer"  
  goal: \>  
    Verify FTC affiliate disclosure compliance, GDPR cookie consent requirements,  
    accuracy of product claims, and editorial integrity. Flag any claims that  
    could create legal exposure. Ensure all sponsored content is properly disclosed.  
  backstory: \>  
    You are a compliance specialist protecting the blog from legal risk while  
    maintaining editorial standards. You check facts against source material  
    and ensure all regulatory requirements are met.  
\`\`\`

\#\#\#\# File: \`config/tasks.yaml\`

\`\`\`yaml  
check\_content\_quality:  
  description: \>  
    Review the article draft: {article\_draft}  
      
    FIRST, query the Target Blog Knowledge Graph for:  
    \- Content standards and quality benchmarks: scope /target\_blog/content\_standards  
    \- Target blog blueprint (ideal structure): scope /target\_blog/competitor\_intel  
    \- Proven writing styles for this niche: scope /target\_blog/psychology  
      
    Then evaluate the draft against EVERY standard found in the KG. Score each  
    dimension on a 1-10 scale:  
    \- Headline quality and click magnetism  
    \- Introduction hook strength and psychological engagement  
    \- Content depth and expertise demonstration (E-E-A-T)  
    \- Value delivery vs. sales pitch balance  
    \- Reading flow and transitions  
    \- Section structure vs. ideal blueprint  
    \- Conclusion and next-step clarity  
      
    For any score below 8, provide SPECIFIC rewrite instructions.  
    Overall threshold: average score must be ≥7.5 to pass. If it fails,  
    return FAIL with a prioritized list of required revisions.  
  expected\_output: \>  
    JSON: {  
      "pass": true/false,  
      "overall\_score": float,  
      "dimension\_scores": {dimension: score},  
      "required\_revisions": \[list of specific changes if pass=false\],  
      "recommendations": \[list of improvement suggestions even if pass=true\],  
      "kg\_standards\_consulted": \[list of KG insights used\]  
    }  
  agent: content\_quality\_editor

audit\_monetization:  
  description: \>  
    Audit the article for monetization quality: {article\_draft}  
      
    FIRST, query the Target Blog Knowledge Graph for:  
    \- Top affiliate programs and products: scope /target\_blog/affiliate\_programs  
    \- Product opportunities and revenue potential: scope /target\_blog/product\_opportunities  
    \- Monetization patterns that work: scope /target\_blog/monetization\_patterns  
      
    Evaluate:  
    \- Are the highest-commission affiliate products from the KG featured?  
    \- Is affiliate link density within the optimal range (1 link per 300-500 words)?  
    \- Are CTAs positioned at psychologically optimal points (after pain point articulation, after social proof, at conclusion)?  
    \- Is there an email capture mechanism?  
    \- Are FTC disclosures present at the top of the article?  
    \- Is the monetization mix diverse (affiliate links \+ email \+ direct ads if available)?  
    \- Revenue potential score vs. what the KG shows top performers achieve  
      
    Threshold: monetization\_score must be ≥7.0 to pass.  
  expected\_output: \>  
    JSON: {  
      "pass": true/false,  
      "monetization\_score": float,  
      "missing\_affiliate\_opportunities": \[list from KG not utilized\],  
      "cta\_audit": {count, placement\_quality, copy\_quality},  
      "required\_changes": \[list if pass=false\],  
      "estimated\_monthly\_revenue\_potential": string,  
      "kg\_programs\_referenced": \[list\]  
    }  
  agent: monetization\_auditor  
  context:  
    \- check\_content\_quality

review\_seo\_and\_ux:  
  description: \>  
    Review the article for SEO and UX quality: {article\_draft}  
      
    FIRST, query the Target Blog Knowledge Graph for:  
    \- UX and layout patterns: scope /target\_blog/ux\_and\_layout  
    \- Competitor content structures: scope /target\_blog/competitor\_intel  
    \- Trending UI patterns and CTA placements  
      
    Evaluate:  
    \- H1/H2/H3 structure vs. ideal blueprint  
    \- Primary keyword in H1, first 100 words, and naturally throughout  
    \- Meta description (150-160 chars, includes keyword, compelling CTA)  
    \- Internal linking placeholders present  
    \- Image alt text requirements noted  
    \- Schema markup type identified (Article, FAQ, HowTo, Review)  
    \- Table of contents for articles \>1500 words  
    \- Mobile reading experience (short paragraphs, bullet points)  
    \- Page speed considerations (no inline heavy scripts suggested)  
      
    Threshold: seo\_ux\_score must be ≥7.5 to pass.  
  expected\_output: \>  
    JSON: {  
      "pass": true/false,  
      "seo\_ux\_score": float,  
      "heading\_structure\_score": float,  
      "keyword\_optimization\_score": float,  
      "schema\_markup\_recommendation": string,  
      "required\_seo\_fixes": \[list if pass=false\],  
      "ux\_improvements": \[list\],  
      "kg\_patterns\_referenced": \[list\]  
    }  
  agent: seo\_and\_ux\_reviewer  
  context:  
    \- check\_content\_quality

check\_compliance:  
  description: \>  
    Perform compliance review on: {article\_draft}  
      
    Check:  
    \- FTC affiliate disclosure present and prominent (before first affiliate link)  
    \- All product claims are accurate and verifiable (flag unverified superlatives)  
    \- No fake urgency or deceptive scarcity claims  
    \- GDPR-relevant content (cookie notices referenced if needed)  
    \- No trademark violations or unauthorized use of brand names in misleading ways  
    \- Author expertise claims are substantiated  
      
    Any CRITICAL compliance failure causes an automatic FAIL and must be fixed  
    before publication regardless of other scores.  
  expected\_output: \>  
    JSON: {  
      "pass": true/false,  
      "critical\_issues": \[list of blockers\],  
      "warnings": \[list of non-blocking concerns\],  
      "ftc\_disclosure\_present": true/false,  
      "fact\_check\_flags": \[list of claims to verify\]  
    }  
  agent: compliance\_checker

compile\_editorial\_verdict:  
  description: \>  
    Compile the results from all four editor reviews:  
    \- Content quality check: {check\_content\_quality}  
    \- Monetization audit: {audit\_monetization}  
    \- SEO/UX review: {review\_seo\_and\_ux}  
    \- Compliance check: {check\_compliance}  
      
    Produce a final editorial verdict: APPROVED, REVISION\_REQUIRED, or REJECTED.  
      
    Rules:  
    \- APPROVED: all four checks pass AND no critical compliance issues  
    \- REVISION\_REQUIRED: 1-2 checks fail but no critical compliance issues  
      → Return consolidated revision checklist ordered by priority  
    \- REJECTED: critical compliance issues OR 3+ checks fail  
      → Return explanation and recommendation to restart from Stage 2  
      
    Update the Target Blog Knowledge Graph with:  
    \- Lessons learned from this review (scope: /target\_blog/content\_standards)  
    \- Any new patterns observed that should inform future content  
  expected\_output: \>  
    JSON: {  
      "verdict": "APPROVED" | "REVISION\_REQUIRED" | "REJECTED",  
      "composite\_score": float,  
      "revision\_checklist": \[ordered list of required changes\],  
      "approved\_for\_publication": true/false,  
      "kg\_updates\_made": \[list of insights added to Knowledge Graph\],  
      "article\_id": string  
    }  
  agent: content\_quality\_editor  
  context:  
    \- check\_content\_quality  
    \- audit\_monetization  
    \- review\_seo\_and\_ux  
    \- check\_compliance  
\`\`\`

\#\#\#\# File: \`editor\_crew.py\`

\`\`\`python  
from crewai import Agent, Crew, Task, Process  
from crewai.project import CrewBase, agent, task, crew, before\_kickoff, after\_kickoff  
from crewai.agents.agent\_builder.base\_agent import BaseAgent  
from typing import List  
from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG

@CrewBase  
class EditorCrew:  
    """  
    Stage 3: Editorial QA Gate  
      
    Checks all completed content against the Target Blog Knowledge Graph.  
    Issues verdicts: APPROVED / REVISION\_REQUIRED / REJECTED.  
    Also feeds lessons learned BACK into the Knowledge Graph after each review,  
    continuously improving the system's quality standards.  
    """

    agents: List\[BaseAgent\]  
    tasks: List\[Task\]  
    agents\_config \= 'config/agents.yaml'  
    tasks\_config \= 'config/tasks.yaml'

    @before\_kickoff  
    def load\_editorial\_standards(self, inputs):  
        """  
        Pre-load current Knowledge Graph standards before reviewing.  
        This ensures the editors always use the LATEST accumulated intelligence.  
        """  
        \# Recall content standards  
        standards \= TARGET\_BLOG\_KG.recall(  
            "content quality standards ideal article structure benchmark",  
            scope="/target\_blog/content\_standards",  
            limit=15,  
            depth="deep"  
        )  
        \# Recall monetization patterns  
        monetization \= TARGET\_BLOG\_KG.recall(  
            "monetization patterns affiliate programs revenue optimization",  
            scope="/target\_blog",  
            limit=10  
        )  
        \# Recall UX/layout patterns  
        ux\_patterns \= TARGET\_BLOG\_KG.recall(  
            "blog layout UX patterns conversion CTA placement",  
            scope="/target\_blog/ux\_and\_layout",  
            limit=10  
        )  
          
        \# Inject into task context  
        inputs\['kg\_standards'\] \= "\\n".join(  
            f"- {m.record.content}" for m in standards  
        )  
        inputs\['kg\_monetization'\] \= "\\n".join(  
            f"- {m.record.content}" for m in monetization  
        )  
        inputs\['kg\_ux\_patterns'\] \= "\\n".join(  
            f"- {m.record.content}" for m in ux\_patterns  
        )  
        return inputs

    @after\_kickoff  
    def update\_knowledge\_graph\_with\_lessons(self, output):  
        """  
        After each editorial review, extract lessons learned and feed them  
        back into the Knowledge Graph. This is how the system continuously  
        improves its editorial standards over time.  
        """  
        lessons \= TARGET\_BLOG\_KG.extract\_memories(str(output.raw))  
        TARGET\_BLOG\_KG.remember\_many(  
            \[l for l in lessons if any(  
                kw in l.lower() for kw in   
                \['should', 'must', 'always', 'never', 'best', 'ideal', 'standard'\]  
            )\],  
        )  
        return output

    @agent  
    def content\_quality\_editor(self) \-\> Agent:  
        return Agent(  
            config=self.agents\_config\['content\_quality\_editor'\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/content\_standards"),  
            verbose=True,  
            max\_iter=4,  
        )

    @agent  
    def monetization\_auditor(self) \-\> Agent:  
        return Agent(  
            config=self.agents\_config\['monetization\_auditor'\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/affiliate\_programs"),  
            verbose=True,  
            max\_iter=3,  
        )

    @agent  
    def seo\_and\_ux\_reviewer(self) \-\> Agent:  
        return Agent(  
            config=self.agents\_config\['seo\_and\_ux\_reviewer'\],  
            memory=TARGET\_BLOG\_KG.scope("/target\_blog/ux\_and\_layout"),  
            verbose=True,  
            max\_iter=3,  
        )

    @agent  
    def compliance\_checker(self) \-\> Agent:  
        return Agent(  
            config=self.agents\_config\['compliance\_checker'\],  
            verbose=True,  
            max\_iter=3,  
        )

    @task  
    def check\_content\_quality(self) \-\> Task:  
        return Task(config=self.tasks\_config\['check\_content\_quality'\])

    @task  
    def audit\_monetization(self) \-\> Task:  
        return Task(config=self.tasks\_config\['audit\_monetization'\])

    @task  
    def review\_seo\_and\_ux(self) \-\> Task:  
        return Task(config=self.tasks\_config\['review\_seo\_and\_ux'\])

    @task  
    def check\_compliance(self) \-\> Task:  
        return Task(config=self.tasks\_config\['check\_compliance'\])

    @task  
    def compile\_editorial\_verdict(self) \-\> Task:  
        return Task(config=self.tasks\_config\['compile\_editorial\_verdict'\])

    @crew  
    def crew(self) \-\> Crew:  
        return Crew(  
            agents=self.agents,  
            tasks=self.tasks,  
            process=Process.sequential,  
            memory=TARGET\_BLOG\_KG,  
            verbose=True,  
            output\_log\_file="./logs/editor\_crew.json",  
        )  
\`\`\`

\---

\#\# Step 7: Create the Master Blog Creation Flow

This Flow orchestrates all crews in the correct sequence and manages state between stages.

\#\#\# 7.1 Create \`core/crewai\_system/blog\_creation\_flow.py\`

\`\`\`python  
from crewai.flow.flow import Flow, listen, start, router  
from pydantic import BaseModel  
from typing import Optional, Dict, Any  
from core.crewai\_system.crews.research\_crew.research\_crew import ResearchCrew  
from core.crewai\_system.crews.content\_strategy\_crew.content\_strategy\_crew import ContentStrategyCrew  
from core.crewai\_system.crews.content\_creation\_crew.content\_creation\_crew import ContentCreationCrew  
from core.crewai\_system.crews.editor\_crew.editor\_crew import EditorCrew  
from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG  
import json

class BlogCreationState(BaseModel):  
    """Typed state that persists across all stages of the blog creation pipeline."""  
    \# Inputs  
    niche: str \= ""  
    blog\_instance\_id: str \= ""  
    current\_year: str \= ""  
      
    \# Stage outputs  
    research\_output: Optional\[Dict\[str, Any\]\] \= None  
    content\_plan: Optional\[Dict\[str, Any\]\] \= None  
    article\_draft: Optional\[str\] \= None  
    editorial\_verdict: Optional\[Dict\[str, Any\]\] \= None  
      
    \# Pipeline control  
    revision\_count: int \= 0  
    max\_revisions: int \= 2  
    pipeline\_status: str \= "pending"  
      
    \# Article being worked on  
    current\_topic: str \= ""  
    current\_article\_id: str \= ""

class BlogCreationFlow(Flow\[BlogCreationState\]):  
    """  
    Master orchestration flow for the automated blog platform.  
      
    Execution sequence:  
    1\. Research (Stage 0\) — real-time intelligence gathering  
    2\. Strategy (Stage 1\) — content planning from research  
    3\. Creation (Stage 2\) — article writing  
    4\. Editorial QA (Stage 3\) — check against Knowledge Graph  
    5\. Revise (if needed) — loop back to Stage 2 with editor feedback  
    6\. Approve — mark ready for publication  
    """  
      
    @start()  
    def initialize\_pipeline(self):  
        """Set up the pipeline and inject current date context."""  
        from datetime import datetime  
        self.state.current\_year \= str(datetime.now().year)  
        self.state.pipeline\_status \= "research\_phase"  
        print(f"\[BlogCreationFlow\] Starting pipeline for niche: {self.state.niche}")

    @listen(initialize\_pipeline)  
    def run\_research\_stage(self):  
        """  
        STAGE 0: Real-Time Intelligence Gathering  
        Always runs first. Populates the Target Blog Knowledge Graph.  
        """  
        print("\[BlogCreationFlow\] Stage 0: Research")  
          
        result \= ResearchCrew().crew().kickoff(inputs={  
            "niche": self.state.niche,  
            "current\_year": self.state.current\_year,  
            "blog\_instance\_id": self.state.blog\_instance\_id,  
        })  
          
        self.state.research\_output \= result.json\_dict or {"raw": result.raw}  
        self.state.pipeline\_status \= "strategy\_phase"  
          
        \# Store key research facts in flow memory  
        self.remember(  
            f"Research completed for {self.state.niche}. "  
            f"Key findings: {result.raw\[:500\]}",  
            scope=f"/flow/{self.state.blog\_instance\_id}/research"  
        )

    @listen(run\_research\_stage)  
    def run\_strategy\_stage(self):  
        """  
        STAGE 1: Content Strategy  
        Uses research results to plan what to create.  
        """  
        print("\[BlogCreationFlow\] Stage 1: Content Strategy")  
          
        result \= ContentStrategyCrew().crew().kickoff(inputs={  
            "niche": self.state.niche,  
            "current\_year": self.state.current\_year,  
            "research\_summary": str(self.state.research\_output),  
        })  
          
        self.state.content\_plan \= result.json\_dict or {"raw": result.raw}  
        self.state.pipeline\_status \= "creation\_phase"  
          
        \# Extract the first topic to write about  
        if result.json\_dict and "priority\_topics" in result.json\_dict:  
            self.state.current\_topic \= result.json\_dict\["priority\_topics"\]\[0\]\["topic"\]  
        else:  
            self.state.current\_topic \= f"Best {self.state.niche} Products {self.state.current\_year}"

    @listen(run\_strategy\_stage)  
    def run\_creation\_stage(self):  
        """  
        STAGE 2: Content Creation  
        Writes the article using research intelligence.  
        """  
        print(f"\[BlogCreationFlow\] Stage 2: Writing '{self.state.current\_topic}'")  
          
        result \= ContentCreationCrew().crew().kickoff(inputs={  
            "niche": self.state.niche,  
            "topic": self.state.current\_topic,  
            "content\_plan\_context": str(self.state.content\_plan),  
            "revision\_feedback": self.\_get\_revision\_feedback(),  
        })  
          
        self.state.article\_draft \= result.raw  
        self.state.pipeline\_status \= "editorial\_phase"

    @listen(run\_creation\_stage)  
    def run\_editorial\_stage(self):  
        """  
        STAGE 3: Editorial QA Gate  
        Checks the article against the Target Blog Knowledge Graph.  
        """  
        print("\[BlogCreationFlow\] Stage 3: Editorial Review")  
          
        result \= EditorCrew().crew().kickoff(inputs={  
            "article\_draft": self.state.article\_draft,  
            "niche": self.state.niche,  
            "current\_topic": self.state.current\_topic,  
        })  
          
        self.state.editorial\_verdict \= result.json\_dict or {"raw": result.raw}  
        return result.json\_dict.get("verdict", "REVISION\_REQUIRED") if result.json\_dict else "REVISION\_REQUIRED"

    @router(run\_editorial\_stage)  
    def editorial\_routing(self):  
        """Route based on editorial verdict."""  
        verdict \= self.state.editorial\_verdict  
        if isinstance(verdict, dict):  
            result \= verdict.get("verdict", "REVISION\_REQUIRED")  
        else:  
            result \= "REVISION\_REQUIRED"  
          
        if result \== "APPROVED":  
            return "approved"  
        elif result \== "REJECTED" or self.state.revision\_count \>= self.state.max\_revisions:  
            return "rejected"  
        else:  
            return "needs\_revision"

    @listen("approved")  
    def finalize\_article(self):  
        """Article passed editorial review — mark ready for publication."""  
        print(f"\[BlogCreationFlow\] APPROVED: '{self.state.current\_topic}'")  
        self.state.pipeline\_status \= "approved"  
          
        \# Save the approved article pattern to the KG  
        self.remember(  
            f"APPROVED article pattern for {self.state.niche}: {self.state.current\_topic}. "  
            f"Score: {self.state.editorial\_verdict.get('composite\_score', 'N/A')}",  
            scope=f"/target\_blog/content\_standards"  
        )  
          
        return {  
            "status": "approved",  
            "article": self.state.article\_draft,  
            "verdict": self.state.editorial\_verdict,  
            "blog\_instance\_id": self.state.blog\_instance\_id,  
        }

    @listen("needs\_revision")  
    def handle\_revision\_request(self):  
        """Article needs revision — increment counter and re-run creation."""  
        self.state.revision\_count \+= 1  
        print(f"\[BlogCreationFlow\] Revision {self.state.revision\_count}/{self.state.max\_revisions}")  
        self.state.pipeline\_status \= f"revision\_{self.state.revision\_count}"  
        \# The flow will re-run run\_creation\_stage with revision feedback

    @listen("rejected")  
    def handle\_rejection(self):  
        """Article rejected — escalate to human review."""  
        print(f"\[BlogCreationFlow\] REJECTED: '{self.state.current\_topic}'")  
        self.state.pipeline\_status \= "rejected"  
        return {  
            "status": "rejected",  
            "reason": self.state.editorial\_verdict,  
            "requires\_human\_review": True,  
        }

    def \_get\_revision\_feedback(self) \-\> str:  
        """Extract revision instructions from the last editorial verdict."""  
        if not self.state.editorial\_verdict:  
            return ""  
        verdict \= self.state.editorial\_verdict  
        if isinstance(verdict, dict) and "revision\_checklist" in verdict:  
            return "\\n".join(f"- {item}" for item in verdict\["revision\_checklist"\])  
        return ""  
\`\`\`

\---

\#\# Step 8: Create Custom Tools

The following custom tools bridge CrewAI agents to the existing application infrastructure.

\#\#\# 8.1 Create \`core/crewai\_system/tools/\`

\#\#\#\# \`affiliate\_db\_tool.py\`

\`\`\`python  
from crewai.tools import BaseTool  
from pydantic import BaseModel, Field  
from typing import Type

class AffiliateDBInput(BaseModel):  
    niche: str \= Field(description="The niche/category to search affiliate products for")  
    limit: int \= Field(default=10, description="Maximum number of results to return")

class AffiliateLinksLookupTool(BaseTool):  
    """  
    Queries the existing SQLite database for affiliate products and programs  
    that have already been validated and stored in the system.  
    """  
    name: str \= "affiliate\_database\_lookup"  
    description: str \= (  
        "Look up affiliate products, programs, and commission information "  
        "from the platform's internal database. Use this to find products "  
        "that have already been vetted and are ready to feature in articles."  
    )  
    args\_schema: Type\[BaseModel\] \= AffiliateDBInput

    def \_run(self, niche: str, limit: int \= 10\) \-\> str:  
        \# Import here to avoid circular deps with Flask app context  
        from automated\_blog\_system.src.models.product import Product  
        products \= Product.query.filter(  
            Product.niche.ilike(f"%{niche}%")  
        ).order\_by(Product.trend\_score.desc()).limit(limit).all()  
          
        if not products:  
            return f"No products found for niche: {niche}"  
          
        result \= \[\]  
        for p in products:  
            result.append(  
                f"Product: {p.name} | Commission: {p.affiliate\_commission}% | "  
                f"Trend Score: {p.trend\_score} | URL: {p.affiliate\_link}"  
            )  
        return "\\n".join(result)  
\`\`\`

\#\#\#\# \`knowledge\_graph\_query\_tool.py\`

\`\`\`python  
from crewai.tools import BaseTool  
from pydantic import BaseModel, Field  
from typing import Type, Optional

class KGQueryInput(BaseModel):  
    query: str \= Field(description="What to search for in the Knowledge Graph")  
    scope: Optional\[str\] \= Field(  
        default="/target\_blog",  
        description="The KG scope to search within (e.g., /target\_blog/affiliate\_programs)"  
    )  
    limit: int \= Field(default=10, description="Number of results to return")

class TargetBlogKGTool(BaseTool):  
    """  
    Queries the Target Blog Knowledge Graph directly.  
    Use this to retrieve accumulated intelligence about the ideal blog,  
    trending topics, affiliate opportunities, and content standards.  
    """  
    name: str \= "target\_blog\_knowledge\_graph"  
    description: str \= (  
        "Query the Target Blog Knowledge Graph for accumulated intelligence about: "  
        "trending topics, affiliate programs, psychological tactics, competitor insights, "  
        "content quality standards, and UX patterns. Always consult this before making "  
        "decisions about content strategy, monetization, or quality standards."  
    )  
    args\_schema: Type\[BaseModel\] \= KGQueryInput

    def \_run(self, query: str, scope: str \= "/target\_blog", limit: int \= 10\) \-\> str:  
        from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG  
        matches \= TARGET\_BLOG\_KG.recall(query, scope=scope, limit=limit)  
          
        if not matches:  
            return f"No knowledge found for query: '{query}' in scope: {scope}"  
          
        results \= \[\]  
        for match in matches:  
            results.append(  
                f"\[Score: {match.score:.2f}\] {match.record.content}"  
            )  
        return "\\n---\\n".join(results)  
\`\`\`

\---

\#\# Step 9: Wire CrewAI Flow into the Existing Flask API

\#\#\# 9.1 Create \`automated-blog-system/src/services/crewai\_pipeline\_service.py\`

\`\`\`python  
import threading  
from core.crewai\_system.blog\_creation\_flow import BlogCreationFlow, BlogCreationState

class CrewAIPipelineService:  
    """  
    Service layer that bridges the existing Flask API with the new CrewAI Flow.  
    This allows the existing routes (POST /api/agents/niches/{id}/activate, etc.)  
    to trigger the new CrewAI pipeline without breaking any existing endpoints.  
    """  
      
    @staticmethod  
    def run\_pipeline\_async(niche: str, blog\_instance\_id: str):  
        """  
        Launch the full blog creation pipeline asynchronously.  
        Called from the existing Flask route handlers.  
        """  
        def \_run():  
            flow \= BlogCreationFlow()  
            result \= flow.kickoff(inputs={  
                "niche": niche,  
                "blog\_instance\_id": blog\_instance\_id,  
            })  
            return result  
          
        thread \= threading.Thread(target=\_run)  
        thread.daemon \= True  
        thread.start()  
      
    @staticmethod  
    def run\_research\_only(niche: str) \-\> dict:  
        """  
        Run only the Research Stage (Stage 0\) to refresh the Knowledge Graph.  
        Can be called on-demand from the admin interface.  
        """  
        from core.crewai\_system.crews.research\_crew.research\_crew import ResearchCrew  
        from datetime import datetime  
          
        result \= ResearchCrew().crew().kickoff(inputs={  
            "niche": niche,  
            "current\_year": str(datetime.now().year),  
        })  
        return {"status": "complete", "summary": result.raw\[:1000\]}  
      
    @staticmethod  
    def run\_editorial\_review(article\_draft: str, niche: str, topic: str) \-\> dict:  
        """  
        Run the Editor Crew against a specific article draft.  
        Can be called standalone from the Flask API for manual review.  
        """  
        from core.crewai\_system.crews.editor\_crew.editor\_crew import EditorCrew  
          
        result \= EditorCrew().crew().kickoff(inputs={  
            "article\_draft": article\_draft,  
            "niche": niche,  
            "current\_topic": topic,  
        })  
        return result.json\_dict or {"raw": result.raw}  
\`\`\`

\#\#\# 9.2 Update \`automated-blog-system/src/routes/agent\_routes.py\`

Add a new endpoint for triggering the CrewAI pipeline and querying the Knowledge Graph:

\`\`\`python  
\# Add to existing agent\_routes.py blueprint

@agent\_bp.route('/niches/\<int:niche\_id\>/crewai-pipeline', methods=\['POST'\])  
def trigger\_crewai\_pipeline(niche\_id):  
    """Trigger the full CrewAI blog creation pipeline for a niche."""  
    from src.services.crewai\_pipeline\_service import CrewAIPipelineService  
      
    niche \= Niche.query.get\_or\_404(niche\_id)  
    CrewAIPipelineService.run\_pipeline\_async(  
        niche=niche.name,  
        blog\_instance\_id=str(niche\_id)  
    )  
    return jsonify({"status": "pipeline\_started", "niche": niche.name})

@agent\_bp.route('/knowledge-graph/query', methods=\['POST'\])  
def query\_knowledge\_graph():  
    """Query the Target Blog Knowledge Graph."""  
    data \= request.get\_json()  
    query \= data.get('query', '')  
    scope \= data.get('scope', '/target\_blog')  
    limit \= data.get('limit', 10\)  
      
    from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG  
    matches \= TARGET\_BLOG\_KG.recall(query, scope=scope, limit=limit)  
      
    return jsonify({  
        "query": query,  
        "scope": scope,  
        "results": \[  
            {  
                "content": m.record.content,  
                "score": m.score,  
                "scope": str(m.record.scope) if hasattr(m.record, 'scope') else scope,  
            }  
            for m in matches  
        \]  
    })

@agent\_bp.route('/knowledge-graph/tree', methods=\['GET'\])  
def get\_knowledge\_graph\_tree():  
    """Get the Target Blog Knowledge Graph scope tree."""  
    from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG  
    return jsonify({"tree": TARGET\_BLOG\_KG.tree()})  
\`\`\`

\---

\#\# Step 10: Directory Structure to Create

Create this directory structure. All files should be created in the correct locations:

\`\`\`  
core/crewai\_system/  
├── \_\_init\_\_.py  
├── knowledge\_graph.py                  ← Step 2: Singleton KG instance  
├── blog\_creation\_flow.py               ← Step 7: Master Flow  
├── tools/  
│   ├── \_\_init\_\_.py  
│   ├── affiliate\_db\_tool.py            ← Step 8.1  
│   └── knowledge\_graph\_query\_tool.py  ← Step 8.1  
└── crews/  
    ├── research\_crew/                  ← Step 3  
    │   ├── \_\_init\_\_.py  
    │   ├── research\_crew.py  
    │   └── config/  
    │       ├── agents.yaml  
    │       └── tasks.yaml  
    ├── content\_strategy\_crew/          ← Step 4  
    │   ├── \_\_init\_\_.py  
    │   ├── content\_strategy\_crew.py  
    │   └── config/  
    │       ├── agents.yaml  
    │       └── tasks.yaml  
    ├── content\_creation\_crew/          ← Step 5  
    │   ├── \_\_init\_\_.py  
    │   ├── content\_creation\_crew.py  
    │   └── config/  
    │       ├── agents.yaml  
    │       └── tasks.yaml  
    └── editor\_crew/                    ← Step 6  
        ├── \_\_init\_\_.py  
        ├── editor\_crew.py  
        └── config/  
            ├── agents.yaml  
            └── tasks.yaml

data/  
└── crewai\_memory/  
    └── target\_blog\_kg/                 ← LanceDB persistent storage (auto-created)

logs/  
├── research\_crew.json  
└── editor\_crew.json

automated-blog-system/src/services/  
└── crewai\_pipeline\_service.py         ← Step 9.1  
\`\`\`

\---

\#\# Step 11: Execution Order & Integration Rules

\#\#\# The Non-Negotiable Pipeline Rule

\*\*Research ALWAYS runs first.\*\* The flow enforces this through the \`@start()\` → \`initialize\_pipeline\` → \`@listen(initialize\_pipeline)\` → \`run\_research\_stage\` sequence. No crew can begin work without the research stage completing first.

\#\#\# Knowledge Graph Read/Write Rules

| Crew | KG Access |  
|---|---|  
| ResearchCrew | WRITE to all \`/target\_blog/\*\` scopes |  
| ContentStrategyCrew | READ from \`/target\_blog/\*\`, WRITE to \`/target\_blog/content\_standards\` |  
| ContentCreationCrew | READ from \`/target\_blog/\*\` via \`TargetBlogKGTool\` |  
| EditorCrew | READ from \`/target\_blog/\*\` (before\_kickoff), WRITE lessons learned (after\_kickoff) |

\#\#\# Revision Loop Rules

\- Maximum 2 revision cycles before escalating to human review  
\- On each revision, the editor's \`revision\_checklist\` is passed as \`revision\_feedback\` to the ContentCreationCrew  
\- The ContentCreationCrew agent's task description must include: "Address all items in the revision\_feedback list before any other consideration"  
\- If the article is REJECTED (3+ failures or critical compliance), a \`DecisionImpact.HIGH\` approval is logged to the existing SQLite \`AgentDecision\` table via the \`OrchestratorAgent\`

\#\#\# Backward Compatibility

\- The existing custom agent classes (\`MarketAnalyticsAgent\`, \`EditorAgent\`, etc.) are \*\*not deleted\*\* — they continue to run for status monitoring, Redis pub/sub messaging, and the existing frontend dashboard  
\- The new CrewAI crews handle the actual intelligence work  
\- The existing Flask routes that work continue to work — new routes are additions, not replacements  
\- The existing \`NichePipelineService\` can be progressively replaced by calling \`CrewAIPipelineService\` instead

\---

\#\# Step 12: Testing Strategy

\#\#\# 12.1 Test the Knowledge Graph Standalone

\`\`\`python  
\# test\_knowledge\_graph.py  
from core.crewai\_system.knowledge\_graph import TARGET\_BLOG\_KG

\# Write a test fact  
TARGET\_BLOG\_KG.remember(  
    "Best affiliate programs for men's health: Testogen (40% commission), "  
    "TestoPrime (25% \+ recurring), Amazon Associates (3-8%)",  
    scope="/target\_blog/affiliate\_programs"  
)

\# Read it back  
results \= TARGET\_BLOG\_KG.recall("affiliate commission rates health")  
assert len(results) \> 0  
print("KG test passed:", results\[0\].record.content\[:100\])  
\`\`\`

\#\#\# 12.2 Test the Research Crew (dry run with small niche)

\`\`\`python  
\# test\_research\_crew.py  
from core.crewai\_system.crews.research\_crew.research\_crew import ResearchCrew

result \= ResearchCrew().crew().kickoff(inputs={  
    "niche": "men's health supplements",  
    "current\_year": "2026",  
})  
print("Research complete:", result.raw\[:500\])  
\`\`\`

\#\#\# 12.3 Test the Editor Crew standalone

\`\`\`python  
\# test\_editor\_crew.py  
from core.crewai\_system.crews.editor\_crew.editor\_crew import EditorCrew

test\_article \= """  
\# Best Protein Powders for Men 2026  
\[Article content here...\]  
"""

result \= EditorCrew().crew().kickoff(inputs={  
    "article\_draft": test\_article,  
    "niche": "men's health",  
    "current\_topic": "Best Protein Powders 2026",  
})  
print("Editorial verdict:", result.json\_dict)  
\`\`\`

\#\#\# 12.4 Test the full Flow end-to-end

\`\`\`python  
\# test\_full\_flow.py  
from core.crewai\_system.blog\_creation\_flow import BlogCreationFlow

flow \= BlogCreationFlow()  
result \= flow.kickoff(inputs={  
    "niche": "men's health",  
    "blog\_instance\_id": "test-001",  
})  
print("Final result:", result)

\# Visualize the flow structure  
flow.plot("blog\_creation\_flow\_diagram")  
\`\`\`

\---

\#\# Step 13: Frontend Integration (Knowledge Graph Dashboard)

Add a new React component to visualize the Target Blog Knowledge Graph:

\#\#\# 13.1 \`blog-frontend/src/components/KnowledgeGraphViewer.jsx\`

Display:  
1\. A tree view of all \`/target\_blog/\*\` scopes with record counts (from \`GET /api/agents/knowledge-graph/tree\`)  
2\. A search interface for querying the KG in real-time (from \`POST /api/agents/knowledge-graph/query\`)  
3\. A "Refresh Research" button that triggers \`POST /api/agents/niches/{id}/crewai-pipeline\` for research-only mode  
4\. A timeline showing when each scope was last updated (recency indicator)

Key design principle: the Knowledge Graph viewer gives the user real-time visibility into what the agents "know" about their ideal blog — making the system transparent and trustworthy.

\---

\#\# Implementation Priority & Sequencing

Execute these steps in this exact order to minimize risk and test incrementally:

| Priority | Step | Time Estimate | Can Test Independently |  
|---|---|---|---|  
| 1 | Step 1: Install dependencies | 30 min | Yes |  
| 2 | Step 2: Knowledge Graph singleton | 1 hour | Yes (Step 12.1) |  
| 3 | Step 3: Research Crew | 3-4 hours | Yes (Step 12.2) |  
| 4 | Step 6: Editor Crew | 3-4 hours | Yes (Step 12.3) |  
| 5 | Step 5: Content Creation Crew | 2-3 hours | No (needs KG data) |  
| 6 | Step 4: Content Strategy Crew | 2 hours | No (needs KG data) |  
| 7 | Step 7: Master Blog Creation Flow | 2-3 hours | Yes (Step 12.4) |  
| 8 | Step 8: Custom Tools | 2 hours | Yes |  
| 9 | Step 9: Flask API integration | 1-2 hours | No (needs all above) |  
| 10 | Step 13: Frontend KG Viewer | 3-4 hours | No (needs API) |

\*\*Rationale for this order:\*\* The Knowledge Graph and Research Crew are foundational — everything else depends on them having data. The Editor Crew is built second because it can be tested independently against any article text. The Content Crews are built last because they need KG data to generate meaningful output.

\---

\#\# Summary of What This Plan Delivers

\#\#\# Research at Every Stage  
\- A dedicated 4-agent \`ResearchCrew\` runs \*\*first\*\* at every pipeline invocation  
\- Agents use \`TavilySearchTool\` and \`SerperDevTool\` for real-time web research  
\- \`FirecrawlScrapeWebsiteTool\` scrapes competitor blog content  
\- Research findings update the Knowledge Graph immediately via \`@after\_kickoff\` hook

\#\#\# Target Blog Knowledge Graph  
\- A persistent \`Memory\` instance backed by LanceDB (survives server restarts)  
\- Organized into 8 scopes: trending topics, affiliate programs, product opportunities, psychology, UX/layout, competitor intel, content standards, monetization patterns  
\- Continuously updated by both the ResearchCrew (new intelligence) and the EditorCrew (lessons learned from each review)  
\- Accessible to all crews via shared instance and queryable via API and custom tool

\#\#\# Editor Agent System (QA Gate)  
\- A 4-agent \`EditorCrew\` that runs after every article draft  
\- Each editor specializes in a dimension: content quality, monetization, SEO/UX, compliance  
\- All editors consult the Knowledge Graph \*\*before\*\* reviewing (\`@before\_kickoff\`)  
\- Issues APPROVED / REVISION\_REQUIRED / REJECTED verdicts  
\- Feeds lessons learned \*\*back\*\* into the Knowledge Graph after every review (\`@after\_kickoff\`)  
\- Supports up to 2 revision cycles with specific feedback passed to the ContentCreationCrew

\#\#\# Continuous Improvement Loop  
Every time an article is reviewed, the EditorCrew's \`after\_kickoff\` hook extracts insights and writes them back to \`/target\_blog/content\_standards\`. Over time, the Knowledge Graph accumulates an increasingly precise picture of what an ideal article for this niche looks like — making every subsequent article better than the last.

Error:

Error: The user has specified a rule which prevents you from using this specific tool call. Here are some of the relevant rules \[{"permission":"\*","pattern":"\*","action":"allow"},{"permission":"edit","pattern":"\*","action":"deny"},{"permission":"edit","pattern":".kilo/plans/\*.md","action":"allow"},{"permission":"edit","pattern":".opencode/plans/\*.md","action":"allow"},{"permission":"edit","pattern":"../../../../home/agent\_7000f2bc-e19a-4e0a-9b82-a39f26004734/.local/share/kilo/plans/\*.md","action":"allow"}\]  
Kilo Codeabout 1 hour ago17,191 tokens · $0.0905  
I'm in plan mode — I cannot write files. Let me present the full plan directly:  
Kilo Codeabout 1 hour ago  
Failed  
This model does not support assistant message prefill. The conversation must end with a user message.  
Scroll   

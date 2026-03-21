from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, after_kickoff
from crewai_tools import TavilySearchTool, SerperDevTool, FirecrawlScrapeWebsiteTool, WebsiteSearchTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG

@CrewBase
class ResearchCrew:
    """
    Stage 0: Real-Time Intelligence Gathering
    
    This crew runs FIRST before any stage of the blog creation pipeline.
    It populates the Target Blog Knowledge Graph with current intelligence
    about trends, affiliate opportunities, psychology, and competitor strategies.
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _build_tools(self):
        return {
            'tavily': TavilySearchTool(),
            'serper': SerperDevTool(),
            'firecrawl': FirecrawlScrapeWebsiteTool(),
            'website_search': WebsiteSearchTool(),
        }

    @agent
    def niche_trend_researcher(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['niche_trend_researcher'],
            tools=[tools['tavily'], tools['serper'], tools['website_search']],
            memory=TARGET_BLOG_KG.scope("/target_blog/trending_topics"),
            verbose=True,
            max_iter=5,
        )

    @agent
    def affiliate_opportunity_scout(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['affiliate_opportunity_scout'],
            tools=[tools['tavily'], tools['serper'], tools['firecrawl']],
            memory=TARGET_BLOG_KG.scope("/target_blog/affiliate_programs"),
            verbose=True,
            max_iter=5,
        )

    @agent
    def psychology_and_ux_researcher(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['psychology_and_ux_researcher'],
            tools=[tools['tavily'], tools['serper'], tools['firecrawl']],
            memory=TARGET_BLOG_KG.scope("/target_blog/psychology"),
            verbose=True,
            max_iter=5,
        )

    @agent
    def competitor_intelligence_agent(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['competitor_intelligence_agent'],
            tools=[tools['tavily'], tools['serper'], tools['firecrawl'], tools['website_search']],
            memory=TARGET_BLOG_KG.scope("/target_blog/competitor_intel"),
            verbose=True,
            max_iter=7,
        )

    @task
    def research_trending_topics(self) -> Task:
        return Task(config=self.tasks_config['research_trending_topics'])

    @task
    def research_affiliate_opportunities(self) -> Task:
        return Task(config=self.tasks_config['research_affiliate_opportunities'])

    @task
    def research_psychology_and_ux(self) -> Task:
        return Task(config=self.tasks_config['research_psychology_and_ux'])

    @task
    def analyze_top_competitors(self) -> Task:
        return Task(config=self.tasks_config['analyze_top_competitors'])

    @after_kickoff
    def persist_to_knowledge_graph(self, output):
        """
        After the research crew completes, explicitly save the consolidated
        findings to the Target Blog Knowledge Graph for all future crews to use.
        """
        facts = TARGET_BLOG_KG.extract_memories(str(output.raw))
        TARGET_BLOG_KG.remember_many(
            facts,
            # Let the LLM infer the best scope under /target_blog
        )
        return output

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Each researcher builds on the previous
            memory=TARGET_BLOG_KG,       # All agents share the Knowledge Graph
            planning=True,               # Pre-plan task execution for better coordination
            planning_llm="gpt-4o",       # Use strong model for planning
            verbose=True,
            output_log_file="./logs/research_crew.json",
        )
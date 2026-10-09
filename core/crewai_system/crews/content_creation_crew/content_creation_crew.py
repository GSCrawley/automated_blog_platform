from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from crewai_tools import TavilySearchTool, SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG
from core.crewai_system.tools.affiliate_db_tool import AffiliateLinksLookupTool

@CrewBase
class ContentCreationCrew:
    """
    Stage 2: Content Creation
    
    This crew writes high-quality affiliate marketing articles based on the content plan.
    It consists of an expert author and a monetization specialist who work together
    to create articles that rank well and generate revenue.
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _build_tools(self):
        return {
            'tavily': TavilySearchTool(),
            'serper': SerperDevTool(),
            'affiliate_lookup': AffiliateLinksLookupTool(),
        }

    @agent
    def author_agent(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['author_agent'],
            tools=[tools['tavily'], tools['serper']],
            memory=TARGET_BLOG_KG.scope("/target_blog"),
            verbose=True,
            max_iter=7,
        )

    @agent
    def monetization_specialist(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['monetization_specialist'],
            tools=[tools['affiliate_lookup']],
            memory=TARGET_BLOG_KG.scope("/target_blog/affiliate_programs"),
            verbose=True,
            max_iter=5,
        )

    @task
    def research_article_topic(self) -> Task:
        return Task(config=self.tasks_config['research_article_topic'])

    @task
    def draft_article_outline(self) -> Task:
        return Task(config=self.tasks_config['draft_article_outline'])

    @task
    def write_article_draft(self) -> Task:
        return Task(config=self.tasks_config['write_article_draft'])

    @task
    def integrate_monetization(self) -> Task:
        return Task(config=self.tasks_config['integrate_monetization'])

    @before_kickoff
    def load_content_context(self, inputs):
        """
        Load relevant context from the Knowledge Graph before creating content.
        """
        # Recall writing guidelines and psychological triggers
        writing_context = TARGET_BLOG_KG.recall(
            "writing style psychological triggers article structure",
            scope="/target_blog",
            limit=10
        )
        
        # Recall affiliate opportunities
        affiliate_context = TARGET_BLOG_KG.recall(
            "affiliate programs products opportunities",
            scope="/target_blog/affiliate_programs",
            limit=10
        )
        
        inputs['kg_writing_guidelines'] = "\n".join(
            f"- {m.record.content}" for m in writing_context
        )
        inputs['kg_affiliate_opportunities'] = "\n".join(
            f"- {m.record.content}" for m in affiliate_context
        )
        
        return inputs

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Tasks must be done in order
            memory=TARGET_BLOG_KG,
            verbose=True,
        )

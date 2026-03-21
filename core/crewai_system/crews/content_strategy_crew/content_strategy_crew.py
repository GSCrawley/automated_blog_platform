from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG
from crewai_tools import TavilySearchTool, SerperDevTool, RagTool

@CrewBase
class ContentStrategyCrew:
    """
    Stage 1: Content Strategy Planning
    
    This crew reads from the Target Blog Knowledge Graph to plan what content to create.
    It consists of a Content Strategy Director and an SEO & Search Intent Specialist
    who work together to build a comprehensive content plan based on research findings.
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _build_tools(self):
        # Note: RagTool would need to be imported and instantiated here
        # For now, we'll note that the Content Strategy Director should use RagTool
        # pointed at the Target Blog KG, but we'll keep the tools minimal for now
        # as the exact implementation of RagTool may vary
        return {}

    @agent
    def content_strategy_director(self) -> Agent:
        return Agent(
            config=self.agents_config['content_strategy_director'],
            # In a full implementation, this would include RagTool pointed at Target Blog KG
            # tools=[RagTool(storage=TARGET_BLOG_KG.storage_path)],  # Placeholder
            memory=TARGET_BLOG_KG.scope("/target_blog/content_standards"),
            verbose=True,
            max_iter=5,
        )

    @agent
    def seo_and_search_intent_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['seo_and_search_intent_specialist'],
            # Tools would be SerperDevTool and TavilySearchTool
            # tools=[SerperDevTool(), TavilySearchTool()],  # Placeholder
            verbose=True,
            max_iter=5,
        )

    @task
    def plan_content_calendar(self) -> Task:
        return Task(config=self.tasks_config['plan_content_calendar'])

    @task
    def map_keywords_to_intent(self) -> Task:
        return Task(config=self.tasks_config['map_keywords_to_intent'])

    @before_kickoff
    def load_research_context(self, inputs):
        # Pull latest research from Knowledge Graph
        trending = TARGET_BLOG_KG.recall(
            "trending topics affiliate opportunities",
            scope="/target_blog",
            limit=20
        )
        inputs['research_context'] = "\n".join(
            m.record.content for m in trending
        )
        return inputs

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=TARGET_BLOG_KG,  # Read-only recommended; writes go to /target_blog/content_standards
            verbose=True,
        )
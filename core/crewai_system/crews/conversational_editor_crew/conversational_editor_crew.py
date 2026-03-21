from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG
from core.crewai_system.tools.command_parser_tool import CommandParserTool
from core.crewai_system.tools.content_modifier_tool import ContentModifierTool
from core.crewai_system.tools.article_parser_tool import ArticleParserTool

@CrewBase
class ConversationalEditorCrew:
    """
    Conversational Editor Crew

    Enables natural language editing of blog articles through a multi-agent system
    that parses commands, coordinates actions, and applies changes while maintaining
    editorial quality standards.
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _build_tools(self):
        return {
            'command_parser': CommandParserTool(),
            'content_modifier': ContentModifierTool(),
            'article_parser': ArticleParserTool(),
        }

    @before_kickoff
    def load_editorial_context(self, inputs):
        """
        Load relevant editorial standards and context before processing commands.
        """
        # Load content quality standards
        quality_standards = TARGET_BLOG_KG.recall(
            "content quality standards writing guidelines editorial best practices",
            scope="/target_blog/content_standards",
            limit=10
        )

        # Load conversational editing patterns
        editing_patterns = TARGET_BLOG_KG.recall(
            "conversational editing patterns user commands natural language processing",
            scope="/target_blog/conversational_editing",
            limit=10
        )

        inputs['kg_quality_standards'] = "\n".join(
            f"- {m.record.content}" for m in quality_standards
        )
        inputs['kg_editing_patterns'] = "\n".join(
            f"- {m.record.content}" for m in editing_patterns
        )

        return inputs

    @after_kickoff
    def learn_from_editing_session(self, output):
        """
        Learn from successful editing patterns to improve future conversations.
        """
        if hasattr(output, 'raw') and output.raw:
            lessons = TARGET_BLOG_KG.extract_memories(str(output.raw))
            TARGET_BLOG_KG.remember_many([
                l for l in lessons if any(
                    kw in l.lower() for kw in
                    ['edit', 'change', 'modify', 'command', 'user', 'pattern']
                )
            ])
        return output

    @agent
    def nlp_parser(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['nlp_parser'],
            tools=[tools['command_parser']],
            memory=TARGET_BLOG_KG.scope("/target_blog/conversational_editing"),
            verbose=True,
            max_iter=3,
        )

    @agent
    def action_coordinator(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['action_coordinator'],
            tools=[tools['article_parser']],
            memory=TARGET_BLOG_KG.scope("/target_blog/content_standards"),
            verbose=True,
            max_iter=4,
        )

    @agent
    def content_editor(self) -> Agent:
        tools = self._build_tools()
        return Agent(
            config=self.agents_config['content_editor'],
            tools=[tools['content_modifier']],
            memory=TARGET_BLOG_KG.scope("/target_blog"),
            verbose=True,
            max_iter=5,
        )

    @agent
    def media_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['media_manager'],
            memory=TARGET_BLOG_KG.scope("/target_blog/ux_and_layout"),
            verbose=True,
            max_iter=3,
        )

    @agent
    def quality_assurance(self) -> Agent:
        return Agent(
            config=self.agents_config['quality_assurance'],
            memory=TARGET_BLOG_KG.scope("/target_blog/content_standards"),
            verbose=True,
            max_iter=3,
        )

    @task
    def parse_command(self) -> Task:
        return Task(config=self.tasks_config['parse_command'])

    @task
    def coordinate_action(self) -> Task:
        return Task(config=self.tasks_config['coordinate_action'])

    @task
    def modify_content(self) -> Task:
        return Task(config=self.tasks_config['modify_content'])

    @task
    def handle_media(self) -> Task:
        return Task(config=self.tasks_config['handle_media'])

    @task
    def validate_changes(self) -> Task:
        return Task(config=self.tasks_config['validate_changes'])

    @task
    def apply_changes(self) -> Task:
        return Task(config=self.tasks_config['apply_changes'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=TARGET_BLOG_KG,
            verbose=True,
            output_log_file="./logs/conversational_editor_crew.json",
        )
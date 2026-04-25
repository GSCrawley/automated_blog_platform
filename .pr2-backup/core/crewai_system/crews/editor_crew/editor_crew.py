from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG

@CrewBase
class EditorCrew:
    """
    Stage 3: Editorial QA Gate
    
    Checks all completed content against the Target Blog Knowledge Graph.
    Issues verdicts: APPROVED / REVISION_REQUIRED / REJECTED.
    Also feeds lessons learned BACK into the Knowledge Graph after each review,
    continuously improving the system's quality standards.
    """

    agents: List[BaseAgent]
    tasks: List[Task]
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @before_kickoff
    def load_editorial_standards(self, inputs):
        """
        Pre-load current Knowledge Graph standards before reviewing.
        This ensures the editors always use the LATEST accumulated intelligence.
        """
        # Recall content standards
        standards = TARGET_BLOG_KG.recall(
            "content quality standards ideal article structure benchmark",
            scope="/target_blog/content_standards",
            limit=15,
            depth="deep"
        )
        # Recall monetization patterns
        monetization = TARGET_BLOG_KG.recall(
            "monetization patterns affiliate programs revenue optimization",
            scope="/target_blog",
            limit=10
        )
        # Recall UX/layout patterns
        ux_patterns = TARGET_BLOG_KG.recall(
            "blog layout UX patterns conversion CTA placement",
            scope="/target_blog/ux_and_layout",
            limit=10
        )
          
        # Inject into task context
        inputs['kg_standards'] = "\n".join(
            f"- {m.record.content}" for m in standards
        )
        inputs['kg_monetization'] = "\n".join(
            f"- {m.record.content}" for m in monetization
        )
        inputs['kg_ux_patterns'] = "\n".join(
            f"- {m.record.content}" for m in ux_patterns
        )
        return inputs

    @after_kickoff
    def update_knowledge_graph_with_lessons(self, output):
        """
        After each editorial review, extract lessons learned and feed them
        back into the Knowledge Graph. This is how the system continuously
        improves its editorial standards over time.
        """
        lessons = TARGET_BLOG_KG.extract_memories(str(output.raw))
        TARGET_BLOG_KG.remember_many(
            [l for l in lessons if any(
                kw in l.lower() for kw in 
                ['should', 'must', 'always', 'never', 'best', 'ideal', 'standard']
            )],
        )
        return output

    @agent
    def content_quality_editor(self) -> Agent:
        return Agent(
            config=self.agents_config['content_quality_editor'],
            memory=TARGET_BLOG_KG.scope("/target_blog/content_standards"),
            verbose=True,
            max_iter=4,
        )

    @agent
    def monetization_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config['monetization_auditor'],
            memory=TARGET_BLOG_KG.scope("/target_blog/affiliate_programs"),
            verbose=True,
            max_iter=3,
        )

    @agent
    def seo_and_ux_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['seo_and_ux_reviewer'],
            memory=TARGET_BLOG_KG.scope("/target_blog/ux_and_layout"),
            verbose=True,
            max_iter=3,
        )

    @agent
    def compliance_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['compliance_checker'],
            verbose=True,
            max_iter=3,
        )

    @task
    def check_content_quality(self) -> Task:
        return Task(config=self.tasks_config['check_content_quality'])

    @task
    def audit_monetization(self) -> Task:
        return Task(config=self.tasks_config['audit_monetization'])

    @task
    def review_seo_and_ux(self) -> Task:
        return Task(config=self.tasks_config['review_seo_and_ux'])

    @task
    def check_compliance(self) -> Task:
        return Task(config=self.tasks_config['check_compliance'])

    @task
    def compile_editorial_verdict(self) -> Task:
        return Task(config=self.tasks_config['compile_editorial_verdict'])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=TARGET_BLOG_KG,
            verbose=True,
            output_log_file="./logs/editor_crew.json",
        )

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional

class KGQueryInput(BaseModel):
    query: str = Field(description="What to search for in the Knowledge Graph")
    scope: Optional[str] = Field(
        default="/target_blog",
        description="The KG scope to search within (e.g., /target_blog/affiliate_programs)"
    )
    limit: int = Field(default=10, description="Number of results to return")

class TargetBlogKGTool(BaseTool):
    """
    Queries the Target Blog Knowledge Graph directly.
    Use this to retrieve accumulated intelligence about the ideal blog,
    trending topics, affiliate opportunities, and content standards.
    """
    name: str = "target_blog_knowledge_graph"
    description: str = (
        "Query the Target Blog Knowledge Graph for accumulated intelligence about: "
        "trending topics, affiliate programs, psychological tactics, competitor insights, "
        "content quality standards, and UX patterns. Always consult this before making "
        "decisions about content strategy, monetization, or quality standards."
    )
    args_schema: Type[BaseModel] = KGQueryInput

    def _run(self, query: str, scope: str = "/target_blog", limit: int = 10) -> str:
        from core.crewai_system.knowledge_graph import TARGET_BLOG_KG
        matches = TARGET_BLOG_KG.recall(query, scope=scope, limit=limit)
          
        if not matches:
            return f"No knowledge found for query: '{query}' in scope: {scope}"
          
        results = []
        for match in matches:
            results.append(
                f"[Score: {match.score:.2f}] {match.record.content}"
            )
        return "\n---\n".join(results)

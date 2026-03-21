from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class AffiliateDBInput(BaseModel):
    niche: str = Field(description="The niche/category to search affiliate products for")
    limit: int = Field(default=10, description="Maximum number of results to return")

class AffiliateLinksLookupTool(BaseTool):
    """
    Queries the existing SQLite database for affiliate products and programs
    that have already been validated and stored in the system.
    """
    name: str = "affiliate_database_lookup"
    description: str = (
        "Look up affiliate products, programs, and commission information "
        "from the platform's internal database. Use this to find products "
        "that have already been vetted and are ready to feature in articles."
    )
    args_schema: Type[BaseModel] = AffiliateDBInput

    def _run(self, niche: str, limit: int = 10) -> str:
        # Import here to avoid circular deps with Flask app context
        from automated_blog_system.src.models.product import Product
        products = Product.query.filter(
            Product.niche.ilike(f"%{niche}%")
        ).order_by(Product.trend_score.desc()).limit(limit).all()
          
        if not products:
            return f"No products found for niche: {niche}"
          
        result = []
        for p in products:
            result.append(
                f"Product: {p.name} | Commission: {p.affiliate_commission}% | "
                f"Trend Score: {p.trend_score} | URL: {p.affiliate_link}"
            )
        return "\n".join(result)

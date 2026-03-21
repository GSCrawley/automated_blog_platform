from crewai import Memory

# Target Blog Knowledge Graph — the shared persistent intelligence layer.
# Tuned for a "knowledge accumulation" use case:
# - High importance weight: what makes a blog successful matters more than recency
# - Long half-life: strategic insights remain valid for months
# - Low recency weight: old research is still useful
TARGET_BLOG_KG = Memory(
    storage="./data/crewai_memory/target_blog_kg",
    recency_weight=0.15,
    semantic_weight=0.55,
    importance_weight=0.30,
    recency_half_life_days=90,
    consolidation_threshold=0.82,  # Merge near-duplicate insights
    embedder={
        "provider": "openai",
        "config": {"model_name": "text-embedding-3-small"}
    },
    llm="gpt-4o-mini",
)
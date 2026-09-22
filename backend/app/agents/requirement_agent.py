from typing import Dict, Any, List, Optional
from app.services.llm_provider import BaseLLMProvider, get_llm_provider

class RequirementAgent:
    """
    Analyzes application portal and extracts machine-readable schema.
    """
    def __init__(self, llm: Optional[BaseLLMProvider] = None):
        self.llm = llm or get_llm_provider()

    def analyze_portal(self, url: str, goal: str, portal_html: Optional[str] = None, app_type: Optional[str] = None) -> Dict[str, Any]:
        context = portal_html or f"Portal at {url}: Multi-step citizen application portal for {app_type or goal}."
        schema = self.llm.analyze_requirements(page_context=context, goal=goal, app_type=app_type)
        return schema

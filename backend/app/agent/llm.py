import logging
from collections.abc import AsyncIterator
from typing import Protocol

from app.agent.state import (
    RecommendationContext,
    ReviewAnalysis,
    ShoppingIntent,
    ShoppingProfile,
)

logger = logging.getLogger(__name__)

                                                                          
 
                                             
 
         
 
                                      
 
                      
class LLMProvider(Protocol):                          
    """Minimal provider contract used by the shopping agent.

    The agent only needs these capabilities:
    1. turn a fuzzy user message into a structured shopping intent;
    2. write a recommendation from already-ranked products;
    3. turn a free-text review into a structured ReviewAnalysis.
    """
         
              
       
            
              
     
                             
     
                  
     
         
              
       
         
                          
    name: str

    async def parse_intent(
        self, message: str, profile: ShoppingProfile
    ) -> ShoppingIntent: ...

    async def write_recommendation(self, context: RecommendationContext) -> str: ...

    async def analyze_review(self, content: str, rating: int) -> ReviewAnalysis: ...

    def stream_recommendation(
        self, context: RecommendationContext
    ) -> AsyncIterator[str]: ...
                                    
 
               
 
                                  
 
                          
 
                                    
 
                      
 
                                                                                                                                         
 
       
 
                        
 
          
 
   
                      
                      
                   
                         
                   
      
                                 
                      
   
 
                        

def create_provider(settings) -> LLMProvider:
    """Create the configured provider, falling back to Mock if credentials are missing."""
    from app.agent.anthropic_provider import AnthropicProvider
    from app.agent.mock import MockProvider
    from app.agent.openai_provider import OpenAICompatibleProvider

    if settings.llm_provider == "anthropic":
        try:
            return AnthropicProvider(settings)
        except ValueError as exc:
            logger.warning("Anthropic provider unavailable, falling back to mock: %s", exc)
            return MockProvider()

    if settings.llm_provider == "openai":
        try:
            return OpenAICompatibleProvider(settings)
        except ValueError as exc:
            logger.warning("OpenAI provider unavailable, falling back to mock: %s", exc)
            return MockProvider()

    return MockProvider()
                                          
 
                             
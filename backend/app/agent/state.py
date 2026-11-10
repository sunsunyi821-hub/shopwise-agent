from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

from app.models import Product


class ShoppingProfile(BaseModel):
    """Accumulated user preferences for a shopping session."""
                                    
    category: str | None = None
    query: str | None = None
    budget_max: float | None = Field(default=None, ge=0)
    budget_min: float | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)
                  
        
     
                  
        
    attributes: dict[str, Any] = Field(default_factory=dict)
           
                            
    brands_include: list[str] = Field(default_factory=list)
    brands_exclude: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)

    def merged_with(self, intent: "ShoppingIntent") -> "ShoppingProfile":
        """Merge a freshly parsed intent into the existing profile.

        New non-empty values win; list fields are unioned; attributes are merged.
        """
        data = self.model_dump()
                          
         
                   
         
                       
            
         
                      
         
                  
         
                  
                 
         
                           
         
                 
              
             
         
                  
                   
            
                      
           
                  
                
         
                     
                
             
        for field in (
            "category",
            "query",
            "budget_max",
            "budget_min",
            "min_rating",
        ):
            value = getattr(intent, field)
            if value is not None:
                data[field] = value
                                           
        data["attributes"] = {**self.attributes, **{
            k: v for k, v in intent.attributes.items() if v not in (None, "")
        }}
                                                        
        data["brands_include"] = sorted(set(self.brands_include) | set(intent.brands_include))
                  
 
                 
 
                   
        data["brands_exclude"] = sorted(set(self.brands_exclude) | set(intent.brands_exclude))
        data["exclude_keywords"] = sorted(
            set(self.exclude_keywords) | set(intent.exclude_keywords)
        )
        data["priorities"] = list(dict.fromkeys([*self.priorities, *intent.priorities]))
        return ShoppingProfile(**data)
        
 
                    

class ShoppingIntent(ShoppingProfile):
    """What the user wants in this turn, plus whether we need to ask a follow-up."""

    needs_clarification: bool = False
    clarification_question: str | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)

                                  
class ScoredProduct(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    product: Product
        
             
         
     
                                    
     
         
              
            
    score: float
    breakdown: dict[str, float] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReviewAnalysis(BaseModel):
    """Structured output produced by the LLM for a free-text review.

    The rating is supplied by the user; the model only summarizes the text.
    """

    sentiment: Literal["positive", "neutral", "negative"] = "neutral"
    summary: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RecommendationContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    profile: ShoppingProfile
    intent: ShoppingIntent
    scored: list[ScoredProduct]
    relaxations: list[str] = Field(default_factory=list)


class ShoppingState(TypedDict, total=False):
    user_message: str
    profile: ShoppingProfile
    intent: ShoppingIntent
    candidates: list[Product]
    scored: list[ScoredProduct]
    relaxations: list[str]
    recommendation: str
    top_product_id: str | None
    clarification: str | None
    stage: str
    error: str | None
                                            
                                                 
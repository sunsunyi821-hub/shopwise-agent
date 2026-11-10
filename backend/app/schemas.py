from datetime import datetime
from typing import Any
                                                                   
 
                     
from pydantic import BaseModel, ConfigDict, Field

from app.agent.state import ShoppingIntent


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
              
              
                       
                            
                      
       
     
            
     
                                    
     
                                  
                 
                   
                      
     
         
     
                                              
     
                 
              
         
     
             
     
                  
     
         
     
                   
               
                    
     
         
     
                  
                   
                
     
                
     
                  
     
          
     
                     
     
              
     
                      
                                    
     
            
     
                                                     
     
              
                          
     
             
     
                                                
     
                                  
                                                         
     
                 
                   
                      
     
                    
                             
                              
                                   
                             
     
                         
     
                                                 
     
                                   
                                 
     
        
             
                
            
               
             
       
              
           
     
              
          
     
                
                  
                   
     
           
     
                 
                    
                         
                     
       
     
         
                            
          
    id: str
    name: str
    brand: str
    category: str
    price: float
    original_price: float | None = None
    rating: float
    review_count: int
    description: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    image_key: str


class ProductListResponse(BaseModel):
    products: list[ProductOut]
    total: int
    relaxations: list[str] = Field(default_factory=list)


class ScoredProductOut(BaseModel):
    product: ProductOut
    score: float
    breakdown: dict[str, float]
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PurchaseProposal(BaseModel):
    product_id: str
    product_name: str
    quantity: int = 1
    unit_price: float
    total_price: float
    currency: str = "CNY"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    user_id: str = Field(default="demo-user", min_length=1, max_length=64)


class ChatResponse(BaseModel):
    session_id: str
    provider: str = "mock"
    intent: ShoppingIntent | None = None
    products: list[ScoredProductOut] = Field(default_factory=list)
    recommendation: str = ""
    top_product_id: str | None = None
    purchase_proposal: PurchaseProposal | None = None
    clarification: str | None = None
    degraded: bool = False


class ReviewCreate(BaseModel):
    order_id: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=5, max_length=2000)
    author: str = Field(default="Anonymous", max_length=32)
    user_id: str = Field(default="demo-user", min_length=1, max_length=64)


class ReviewUpdate(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str = Field(min_length=5, max_length=2000)
    author: str | None = Field(default=None, max_length=32)
    user_id: str = Field(default="demo-user", min_length=1, max_length=64)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: str
    order_id: str | None = None
    rating: int
    content: str
    author: str
    sentiment: str
    summary: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ReviewCreatedOut(ReviewOut):
    degraded: bool = False


class OrderCreate(BaseModel):
    product_id: str = Field(min_length=1)
    quantity: int = Field(default=1, ge=1, le=5)
    address: str = Field(min_length=5, max_length=200)
    session_id: str | None = None
    user_id: str = Field(default="demo-user", min_length=1, max_length=64)
    confirm: bool = False


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    session_id: str | None
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    status: str
    address: str
    created_at: datetime
    reviewed: bool = False


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    profile: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = Field(default_factory=list)

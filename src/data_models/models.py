from pydantic import BaseModel, Field
from typing import List

class EvaluationReport(BaseModel):
    """
    Data model for the final evaluation report.
    """
    comprehensive_score: float = Field(..., description="综合评分 (满分10分)")
    demand_mining_score: int = Field(..., description="需求挖掘分数")
    product_recommendation_score: int = Field(..., description="产品推荐分数")
    objection_handling_score: int = Field(..., description="异议处理分数")
    trust_building_score: int = Field(..., description="建立信任分数")
    closing_score: int = Field(..., description="推动成交分数")
    strengths: List[str] = Field(..., description="本次对话中的优点")
    suggestions: List[str] = Field(..., description="具体的改进建议")

class ChatMessage(BaseModel):
    """
    Data model for a single chat message.
    """
    role: str = Field(..., description="The role of the speaker (e.g., 'user' or 'assistant')")
    content: str = Field(..., description="The content of the message") 
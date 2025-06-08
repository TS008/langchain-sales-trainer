from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

# 简化的评估提示词模板，减少token消耗
EVALUATION_PROMPT_TEMPLATE = """
你是销售培训师。请对以下销售对话进行快速评估（请控制在200字以内）:

对话记录说明：
- salesperson: 销售人员的话术
- customer: 客户的回应

{conversation_history}

请按以下格式简洁回复:

**综合评分**: X/10

**各项评分**:
需求挖掘: X/10
产品推荐: X/10  
异议处理: X/10
建立信任: X/10
推动成交: X/10

**优点**: [1-2个关键优点]

**改进建议**: [2-3个具体建议]
"""

# 缓存评估链实例
_evaluation_chain = None

def create_evaluation_chain():
    """
    Creates a chain that evaluates a conversation history using DeepSeek.
    使用缓存避免重复创建
    """
    global _evaluation_chain
    
    if _evaluation_chain is None:
        prompt = PromptTemplate(
            template=EVALUATION_PROMPT_TEMPLATE,
            input_variables=["conversation_history"]
        )
        
        llm = ChatOpenAI(
            model_name=DEEPSEEK_MODEL,
            openai_api_key=DEEPSEEK_API_KEY,
            openai_api_base=DEEPSEEK_BASE_URL,
            temperature=0.1,  # 降低温度，提高稳定性和速度
            max_tokens=300,   # 限制输出长度
            streaming=True    # 启用流式输出
        )

        _evaluation_chain = (
            prompt
            | llm
            | StrOutputParser()
        )
    
    return _evaluation_chain 
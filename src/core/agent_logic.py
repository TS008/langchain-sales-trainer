from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from src.prompts.persona_prompts import PERSONA_PROMPTS
from src.rag.rag_system import query_vector_store
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, OPENAI_API_KEY

# 全局LLM实例缓存，避免重复创建
_llm_cache = {}

def get_llm(use_deepseek: bool = True, temperature: float = 0.7):
    """获取缓存的LLM实例，避免重复创建"""
    cache_key = f"{'deepseek' if use_deepseek else 'openai'}_{temperature}"
    
    if cache_key not in _llm_cache:
        if use_deepseek:
            _llm_cache[cache_key] = ChatOpenAI(
                model_name=DEEPSEEK_MODEL,
                openai_api_key=DEEPSEEK_API_KEY,
                openai_api_base=DEEPSEEK_BASE_URL,
                temperature=temperature,
                streaming=True,  # 启用流式输出
                max_tokens=500,  # 限制输出长度，提高响应速度
            )
        else:
            _llm_cache[cache_key] = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                openai_api_key=OPENAI_API_KEY,
                temperature=temperature,
                streaming=True,
                max_tokens=500,
            )
    
    return _llm_cache[cache_key]

def create_agent(persona_name: str, use_deepseek: bool = True):
    """
    Creates a simple LangChain agent for a given customer persona.
    """
    if persona_name not in PERSONA_PROMPTS:
        raise ValueError(f"Unknown persona: {persona_name}")

    prompt = PERSONA_PROMPTS[persona_name]
    llm = get_llm(use_deepseek, temperature=0.7)

    # 使用更轻量的内存管理
    memory = ConversationBufferMemory(
        ai_prefix=persona_name.split(" ")[1],
        max_token_limit=1000,  # 限制内存长度
        return_messages=False   # 减少内存开销
    )
    
    conversation = ConversationChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=False  # 关闭详细日志，提高性能
    )

    return conversation

def create_rag_agent(persona_name: str, use_deepseek: bool = True):
    """
    Creates a simple RAG-powered agent using keyword matching.
    """
    if persona_name not in PERSONA_PROMPTS:
        raise ValueError(f"Unknown persona: {persona_name}")

    base_prompt = PERSONA_PROMPTS[persona_name]
    
    # 简化的提示词模板
    enhanced_template = base_prompt.template + """

相关产品信息:
{context}

请简洁地以您的角色身份回应（控制在100字以内）：
"""

    prompt = PromptTemplate(
        template=enhanced_template,
        input_variables=["history", "input", "context"]
    )

    # 使用缓存的LLM实例
    llm = get_llm(use_deepseek, temperature=0.7)

    def rag_chain_invoke(inputs):
        """优化的RAG链调用函数"""
        user_input = inputs.get("input", "")
        history = inputs.get("history", "")
        
        # 限制历史记录长度，提高性能
        history_lines = history.split('\n')
        if len(history_lines) > 10:  # 只保留最近10轮对话
            history = '\n'.join(history_lines[-10:])
        
        # 获取相关产品信息（减少检索数量）
        relevant_docs = query_vector_store(user_input, k=1)  # 只检索1个最相关的
        context = relevant_docs[0].page_content if relevant_docs else "暂无相关产品信息"
        
        # 格式化提示（简化）
        formatted_prompt = prompt.format(
            history=history,
            input=user_input,
            context=context
        )
        
        # 调用LLM
        response = llm.invoke(formatted_prompt)
        
        # 提取文本内容
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    # 创建轻量级调用包装器
    class SimpleRAGChain:
        def invoke(self, inputs):
            return rag_chain_invoke(inputs)
    
    return SimpleRAGChain() 
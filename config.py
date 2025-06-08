import os

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# OpenAI API Configuration (as an alternative)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

# Vector Store Configuration
PRODUCT_KNOWLEDGE_PATH = "data/product_knowledge.csv"
VECTOR_STORE_PATH = "data/vector_store"

# Performance Configuration
PERFORMANCE_CONFIG = {
    # AI模型性能设置
    "max_tokens": 500,              # 限制输出长度，提高响应速度
    "temperature": 0.7,             # 对话温度
    "evaluation_temperature": 0.1,  # 评估温度（更稳定）
    "evaluation_max_tokens": 300,   # 评估输出长度限制
    
    # 缓存设置
    "keyword_search_cache_size": 128,  # 关键词搜索缓存大小
    "conversation_memory_limit": 1000, # 对话内存限制
    "history_context_limit": 10,       # 历史对话上下文轮数限制
    
    # RAG设置
    "rag_retrieval_count": 1,       # RAG检索数量（减少以提高速度）
    "chunk_size": 200,              # 文档块大小
    "chunk_overlap": 20,            # 文档块重叠
    "bert_batch_size": 32,          # BERT编码批次大小
    
    # UI设置
    "enable_streaming": True,       # 启用流式输出
    "enable_verbose": False,        # 关闭详细日志
} 

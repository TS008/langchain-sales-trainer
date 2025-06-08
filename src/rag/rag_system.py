import os
import pandas as pd
import numpy as np
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from typing import List
import time
from functools import lru_cache

from config import PRODUCT_KNOWLEDGE_PATH, VECTOR_STORE_PATH

# 全局缓存
_bert_model = None
_vectorstore = None
_product_data = None

class BertEmbeddings(Embeddings):
    """
    基于BERT的embedding类，使用sentence-transformers，带缓存优化
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        global _bert_model
        if _bert_model is None:
            print(f"正在加载BERT模型: {model_name}")
            _bert_model = SentenceTransformer(model_name)
            print("BERT模型加载完成")
        self.model = _bert_model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """为文档生成embeddings"""
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """为查询生成embedding"""
        embedding = self.model.encode([text], show_progress_bar=False)
        return embedding[0].tolist()

@lru_cache(maxsize=128)
def _cached_keyword_search(query: str, k: int = 2):
    """缓存的关键词搜索"""
    global _product_data
    
    if _product_data is None:
        try:
            _product_data = pd.read_csv(PRODUCT_KNOWLEDGE_PATH)
        except Exception as e:
            print(f"加载产品数据失败: {e}")
            return [Document(page_content="产品信息加载失败", metadata={"id": 0})]
    
    relevant_products = []
    query_lower = query.lower()
    
    # 优化的关键词匹配
    keywords = ['手镯', '黄金', '价格', '克', '折扣', '工艺', '设计', '传承', '星动', '玲珑', '福运']
    
    for _, row in _product_data.iterrows():
        product_text = f"{row['name']} {row['series']} {row['craft']} {row['meaning']} {row['description']}".lower()
        
        # 快速关键词匹配评分
        score = sum(1 for keyword in keywords if keyword in query_lower and keyword in product_text)
        
        # 简单的文本包含检查
        if score > 0 or any(word in product_text for word in query_lower.split()[:3]):  # 只检查前3个词
            content = f"产品名称: {row['name']}, 系列: {row['series']}, 工艺: {row['craft']}, 寓意: {row['meaning']}, 价格: {row['price_yuan']}元, 重量: {row['weight_g']}克, 描述: {row['description']}"
            relevant_products.append(Document(page_content=content, metadata={"id": row['id'], "score": score}))
    
    # 按得分排序并返回前k个
    relevant_products.sort(key=lambda x: x.metadata.get('score', 0), reverse=True)
    return relevant_products[:k] if relevant_products else [Document(page_content="暂无相关产品信息", metadata={"id": 0})]

def create_vector_store():
    """
    使用BERT embeddings创建FAISS向量存储，带性能优化
    """
    if os.path.exists(VECTOR_STORE_PATH):
        print("向量存储已存在，跳过创建")
        return True

    try:
        start_time = time.time()
        print("开始创建向量存储...")
        
        # 加载产品数据
        df = pd.read_csv(PRODUCT_KNOWLEDGE_PATH)
        print(f"已加载 {len(df)} 个产品")
        
        # 创建文档
        documents = []
        for _, row in df.iterrows():
            # 简化内容，减少token数量
            content = f"{row['name']} {row['series']} {row['craft']} 价格{row['price_yuan']}元 {row['meaning']}"
            documents.append(Document(page_content=content, metadata={"id": row['id']}))

        # 较小的chunk_size，提高查询精度
        text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=20)
        docs = text_splitter.split_documents(documents)
        print(f"创建了 {len(docs)} 个文档块")
        
        # 使用BERT embeddings
        embeddings = BertEmbeddings()
        print("正在生成embeddings...")
        
        # 创建并保存FAISS向量存储
        vectorstore = FAISS.from_documents(docs, embeddings)
        vectorstore.save_local(VECTOR_STORE_PATH)
        
        elapsed_time = time.time() - start_time
        print(f"向量存储已保存到: {VECTOR_STORE_PATH}，耗时: {elapsed_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"创建向量存储失败: {e}")
        return False

def query_vector_store(query: str, k: int = 2):
    """
    查询FAISS向量存储以找到相关产品，带缓存优化
    """
    global _vectorstore
    
    try:
        # 懒加载向量存储
        if _vectorstore is None:
            if not os.path.exists(VECTOR_STORE_PATH):
                print("向量存储不存在，使用关键词搜索")
                return _cached_keyword_search(query, k)
            
            print("正在加载向量存储...")
            embeddings = BertEmbeddings()
            _vectorstore = FAISS.load_local(
                VECTOR_STORE_PATH, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            print("向量存储加载完成")
        
        # 执行快速相似性搜索
        results = _vectorstore.similarity_search(query, k=k)
        return results
        
    except Exception as e:
        print(f"向量存储查询失败: {e}，回退到关键词搜索")
        # 如果向量存储查询失败，回退到缓存的关键词匹配
        return _cached_keyword_search(query, k)

def _fallback_keyword_search(query: str, k: int = 2):
    """
    回退的关键词搜索方法（保留兼容性）
    """
    return _cached_keyword_search(query, k) 
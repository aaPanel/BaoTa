import os
import sys
import json
import math
import time
import uuid
import requests
import logging
from typing import List, Dict, Any, Tuple
import openai
import numpy as np

panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'
if panelPath not in sys.path:
    os.chdir(panelPath)
    sys.path.insert(0, panelPath + "/class/")
try:
    import public
except ImportError:
    public = None

class SimpleVectorDB:
    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        self.persist_file = os.path.join(persist_dir, "vector_store.json")
        self.data: List[Dict[str, Any]] = [] # stores {"id":, "text":, "metadata":, "embedding":}
        
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
            
        self.load()
        
    def load(self):
        if os.path.exists(self.persist_file):
            try:
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                self.data = []
    
    def save(self):
        try:
            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False)
        except Exception as e:
            pass

    def add(self, documents: List[str], metadatas: List[Dict], ids: List[str], embeddings: List[List[float]]):
        for doc, meta, doc_id, emb in zip(documents, metadatas, ids, embeddings):
            self.data = [d for d in self.data if d['id'] != doc_id]
            
            self.data.append({
                "id": doc_id,
                "text": doc,
                "metadata": meta,
                "embedding": emb
            })
        self.save()

    def search(self, query_embedding: List[float], n_results: int = 5, score: float = 0.5, where: Dict = None, metric: str = "cosine") -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: The query vector.
            n_results: Number of results to return.
            score: Minimum score threshold.
            where: Metadata filter.
            metric: Distance metric to use. Options: "cosine" (default), "euclidean", "dot".
                    - "cosine": Cosine similarity (normalized dot product). Range [-1, 1].
                    - "euclidean": 1 / (1 + L2_distance). Range (0, 1].
                    - "dot": Dot product. Range (-inf, inf).
        """
        if not self.data:
            return []
            
        candidates = self.data
        if where:
            filtered = []
            for item in candidates:
                match = True
                for k, v in where.items():
                    if item['metadata'].get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(item)
            candidates = filtered
            
        if not candidates:
            return []

        results = []
        
        query_vec = np.array(query_embedding)
        cand_vecs = np.array([c['embedding'] for c in candidates])

        if metric == "cosine":
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0: query_norm = 1e-9

            cand_norms = np.linalg.norm(cand_vecs, axis=1)
            cand_norms[cand_norms == 0] = 1e-9

            dot_products = np.dot(cand_vecs, query_vec)
            scores = dot_products / (cand_norms * query_norm)

        elif metric == "euclidean":
            # Euclidean distance: smaller is closer.
            # Convert to similarity score: 1 / (1 + distance)
            dists = np.linalg.norm(cand_vecs - query_vec, axis=1)
            scores = 1 / (1 + dists)

        elif metric == "dot":
            scores = np.dot(cand_vecs, query_vec)

        else:
            raise ValueError(f"Unknown metric: {metric}")
        
        # Sort by score descending
        top_k_indices = np.argsort(scores)[-n_results:][::-1]

        for idx in top_k_indices:
            item = candidates[idx]
            score_ = float(scores[idx])
            if score_ >= score:
                results.append({
                    "id": item['id'],
                    "text": item['text'],
                    "metadata": item['metadata'],
                    "score": score_
                })

        return results

class RAGService:
    def __init__(
        self,
        session_dir: str,
        openai_api_key: str,
        openai_base_url: str,
        embedding_api_key: str = None,
        embedding_base_url: str = None,
        embedding_model_name: str = "text-embedding-v4",
        small_model_name: str = None,
        rag_retrieval_count: int = 10,
        rag_final_count: int = 5,
        default_headers: Dict = None
    ):
        self.session_dir = session_dir
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url
        self.embedding_api_key = embedding_api_key or openai_api_key
        self.embedding_base_url = embedding_base_url or openai_base_url
        self.embedding_model_name = embedding_model_name
        self.small_model_name = small_model_name
        self.rag_retrieval_count = rag_retrieval_count
        self.rag_final_count = rag_final_count
        
        self.vector_db = SimpleVectorDB(persist_dir=session_dir)
        
        # self.openai_client = openai.OpenAI(
        #     api_key=openai_api_key,
        #     base_url=openai_base_url,
        #     default_headers=default_headers
        # )
        
        self.emb_api_key = embedding_api_key
        self.emb_base_url = embedding_base_url
        self.emb_model_name = embedding_model_name
        
        self.embedding_client = openai.OpenAI(
            api_key=self.emb_api_key,
            base_url=self.emb_base_url,
            default_headers=default_headers
        )
        # else:
        #     self.embedding_client = self.openai_client
        
        self.small_model_name = small_model_name
    
    def close(self):
        self.embedding_client.close()

    def get_embedding(self, text: str) -> List[float]:
        try:
            model = self.emb_model_name or "text-embedding-3-small"
            text = text.replace("\n", " ")
            
            response = self.embedding_client.embeddings.create(
                input=[text],
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            return []

    def generate_context_prefix(self, user_text: str, ai_text: str) -> str:
        # 暂时禁用小模型精简功能
        return "[Context: General]"
        # try:
        #     prompt = (
        #         f"请分析以下对话片段，并提供一个非常简要的背景标签 (例如:[Context: Nginx Config]).\\n"
        #         f"Dialogue:\\nUser: {user_text}\\nAI: {ai_text}\\n\\nContext Label:"
        #     )
        #     model_name = self.small_model_name
        #     response = self.openai_client.chat.completions.create(
        #         model=model_name,
        #         messages=[{"role": "user", "content": prompt}],
        #         max_tokens=20
        #     )
        #     return response.choices[0].message.content.strip()
        # except Exception as e:
        #     return "[Context: General]"

    def add_memory(self, user_msg: Dict, ai_msg: Dict, session_id: str):
        user_content = user_msg.get("content", "")
        if isinstance(user_content, list):
            user_text = "\n".join([item.get("text", "") for item in user_content if isinstance(item, dict) and item.get("type") == "text"])
        else:
            user_text = str(user_content)
            
        ai_content = ai_msg.get("content", "")
        if isinstance(ai_content, list):
            ai_text = "\n".join([item.get("text", "") for item in ai_content if isinstance(item, dict) and item.get("type") == "text"])
        else:
            ai_text = str(ai_content)
        
        prefix = self.generate_context_prefix(user_text, ai_text)
        full_text = f"{prefix} User: {user_text} -> AI: {ai_text}"
        
        embedding = self.get_embedding(full_text)
        if not embedding:
            return

        doc_id = f"{user_msg['id']}_{ai_msg['id']}"
        
        self.vector_db.add(
            documents=[full_text],
            metadatas=[{
                "session_id": session_id,
                "timestamp": ai_msg.get("timestamp", int(time.time())),
                "user_msg_id": user_msg["id"],
                "ai_msg_id": ai_msg["id"],
                "type": "conversation_pair"
            }],
            ids=[doc_id],
            embeddings=[embedding]
        )

    def add_document(self, text: str, metadata: Dict = None):
        """
        Add a generic document to the knowledge base.
        """
        if metadata is None:
            metadata = {}
        
        embedding = self.get_embedding(text)
        if not embedding:
            return
            
        doc_id = str(uuid.uuid4())
        self.vector_db.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id],
            embeddings=[embedding]
        )

    def search(self, query: str, session_id: str = None,score: float = 0.2, scope: str = "session", exclude_ids: List[str] = None,full_text:bool = True,session_history: List[Dict[str, Any]] = None,enable_rag_judgment: bool = None,) -> List[str]:
        """
        从知识库中检索与查询最相关的上下文信息。
        - query: 用户查询文本
        - session_id: 当前会话ID（仅在scope为"session"时使用
        - score: 最小相似度分数阈值（范围0-1，默认0.2）
        - scope: 检索范围，"session"（仅当前会话）或"global"（所有会话）
        - exclude_ids: 要排除的消息ID列表（例如，当前对话中的消息ID，避免检索到自己）
        - full_text: 是否返回完整文本（包含时间戳等元信息）还是仅返回原始文本
        """
        if exclude_ids is None:
            exclude_ids = []

        where_clause = {}
        if scope == "session" and session_id:
            where_clause = {"session_id": session_id}
        
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []

        results = self.vector_db.search(
            query_embedding=query_embedding,
            n_results=self.rag_retrieval_count,
            score=score,
            where=where_clause if where_clause else None
        )

        if not results:
            return []

        candidates = []
        for res in results:
            meta = res['metadata']
            if meta.get('user_msg_id','') in exclude_ids or meta.get('ai_msg_id','') in exclude_ids:
                continue
                
            candidates.append(res)

        candidates = candidates[:self.rag_final_count]
        if not full_text:
            return candidates
        
        final_context = []
        for c in candidates:
            ts = c['metadata'].get('timestamp')
            if ts:
                time_str = str(ts)
                final_context.append(f"[Time: {time_str}] {c['text']}")
            else:
                final_context.append(f"{c['text']}")
        return final_context

    def close(self):
        self.embedding_client.close()

class ExternalRAGService:
    API_URL = "https://www.bt.cn/plugin_api/chat/api/knowledge-base/retrieve"

    def __init__(
        self,
        appid: str = "bt_app_002",
        index_id: str = "main",
        rag_final_count: int = 5,
        enable_rag_judgment: bool = False,
        api_key: str = "--",
        base_url: str = "https://www.bt.cn/plugin_api/chat/openai/v3",
        model_name: str = "fast",
        default_headers: Dict[str, str] = None
    ):
        self.appid = appid
        self.rag_final_count = rag_final_count
        self.index_id = index_id
        self.enable_rag_judgment = enable_rag_judgment

        self.judgment_api_key = api_key
        self.judgment_base_url = base_url
        self.judgment_model_name = model_name
        self.judgment_default_headers = default_headers or {}

        if public is not None:
            user_info = public.get_user_info()
            self.uid = str(user_info.get('uid', ''))
            self.access_key = user_info.get('access_key', '')
        else:
            self.uid = ''
            self.access_key = ''

    def close(self):
        pass

    def _should_use_rag(self, user_input: str, session_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        判断是否需要 RAG 检索（内部方法）
        - user_input: 当前用户输入
        - session_history: 最近对话历史（用于结合上下文判断）
        """
        prompt = """你是一个 RAG 检索判断助手。根据用户输入和对话上下文，判断是否需要从外部知识库中检索相关信息来回答。

判断标准：
- 如果问题涉及特定领域知识、技术文档、产品信息、常见问题等，应该检索
- 如果是简单的闲聊、情感交流或通用知识，不需要检索
- 如果上下文中有明确指向特定领域的问题，应该检索

请以 JSON 格式返回：
{
    "use_rag": true/false,
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}"""

        try:
            from chat_client.single_agent import SingleAgent
            single_agent = SingleAgent(
                api_key=self.judgment_api_key,
                base_url=self.judgment_base_url,
                model_name=self.judgment_model_name,
                default_headers=self.judgment_default_headers,
                temperature=0.1
            )
            
            notime = time.time()
            if session_history:
                formatted_history = []
                for msg in session_history[-6:]:
                    role = msg.get("role", "user")
                    if role not in ("user", "assistant"):
                        continue
                    if role == "user":
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            content = " ".join([c.get("text", "") for c in content if c.get("type") == "text"])
                        formatted_history.append({"role": role, "content": str(content)})
                    else:
                        content = msg.get("content", "")
                        if isinstance(content, list):
                            content = " ".join([c.get("text", "") for c in content if c.get("type") == "text"])
                        if not content:
                            content = msg.get("reasoning_content", "")
                        if not content:
                            continue
                        formatted_history.append({"role": role, "content": str(content)})
                # logging.info(f"RAG Judgment Session History:{formatted_history}")
                result = single_agent.chat(
                    prompt=prompt,
                    messages=formatted_history,
                    input_text=f"当前用户输入：{user_input}",
                    json_response=True,
                    temperature=0.1,
                    extra_body={"enable_thinking":False}
                )
            else:
                result = single_agent.chat(
                    prompt=prompt,
                    input_text=user_input,
                    json_response=True,
                    temperature=0.1,
                    extra_body={"enable_thinking":False}
                )

            single_agent.close()
            # logging.info(f"RAG Judgment Result:{time.time()-notime} {result}")
            if result["success"]:
                return {
                    "use_rag": result["data"].get("use_rag", False),
                    "confidence": result["data"].get("confidence", 0.0),
                    "reason": result["data"].get("reason", "")
                }
            else:
                return {
                    "use_rag": True,
                    "confidence": 0.0,
                    "reason": result.get("error", "判断失败，默认检索")
                }
        except Exception as e:
            return {
                "use_rag": True,
                "confidence": 0.0,
                "reason": f"判断异常: {str(e)}，默认检索"
            }

    def search(self, query: str, score: float = 0.2, scope: str = "session", full_text: bool = True, enable_rag_judgment: bool = None, session_history: List[Dict[str, Any]] = None) -> List[str]:
        """
        从外部知识库检索与查询最相关的上下文信息。
        - query: 用户查询文本
        - score: 最小相似度分数阈值（范围0-1，默认0.2）
        - enable_rag_judgment: 覆盖类级别的判断开关
        - session_history: 最近对话历史（用于 RAG 判断时结合上下文）
        """
        if enable_rag_judgment is None:
            enable_rag_judgment = self.enable_rag_judgment

        if enable_rag_judgment:
            rag_judgment = self._should_use_rag(query, session_history)
            # logging.info(f"RAG Judgment: {rag_judgment}")
            # logging.info(f"Session: {session_history}")
            if not rag_judgment.get("use_rag", True):
                return []
        try:
            headers = {
                "Content-Type": "application/json",
                "uid": self.uid,
                "access-key": self.access_key,
                "appid": self.appid
            }
            
            payload = {
                "query": query,
                "dense_similarity_top_k": 100,
                "enable_reranking": True,
                "rerank_min_score": 0.5,
                "index_id": self.index_id,
                "rerank_top_n": self.rag_final_count
            }
            
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # public.print_log(response.text)
            
            if response.status_code != 200:
                return []
            
            result = response.json()
            
            if not result.get("status") or "data" not in result:
                return []
            
            nodes = result["data"].get("Nodes", [])
            
            filtered_docs = []
            for node in nodes:
                node_score = node.get("Score", 0)
                if node_score >= score:
                    text = node.get("Text", "")
                    if text:
                        filtered_docs.append(text)
            
            return filtered_docs[:self.rag_final_count]
            
        except Exception as e:
            return []

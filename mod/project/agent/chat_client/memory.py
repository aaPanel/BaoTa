import json
import os
import time
import uuid
from typing import List, Dict, Any, Union

class MemoryManager:
    def __init__(self, session_id: str, sessions_dir: str = "sessions", sliding_window_size: int = 10, skill_agent_id: str = None):
        self.session_id = session_id
        self.sliding_window_size = sliding_window_size
        self.skill_agent_id = skill_agent_id

        self.session_dir = os.path.join(sessions_dir, session_id)
        self.file_path = os.path.join(self.session_dir, "sessions.json")
        self.meta_file_path = os.path.join(self.session_dir, "meta.json")
        self.history: List[Dict[str, Any]] = []
        self._ensure_sessions_dir()
        self.load_session()
        self._load_or_create_meta()

    def _ensure_sessions_dir(self):
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

    def _load_or_create_meta(self):
        if not os.path.exists(self.meta_file_path):
            meta = {
                "session_id": self.session_id,
                "skill_agent_id": self.skill_agent_id,
                "created_at": time.time()
            }
            if self.skill_agent_id:
                meta["skill_agent_id"] = self.skill_agent_id
            try:
                with open(self.meta_file_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
            except:
                pass
        else:
            try:
                with open(self.meta_file_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                if self.skill_agent_id and not meta.get("skill_agent_id"):
                    meta["skill_agent_id"] = self.skill_agent_id
                    with open(self.meta_file_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
            except:
                pass

    def load_session(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                self.history = []
        else:
            self.history = []

    def save_session(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def add_message(self, role: str, content: Union[str, List[Dict[str, Any]]], id: str = None, **kwargs):
        msg = {
            "id": id if id else str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": time.time(),
            **kwargs
        }
        self.history.append(msg)
        self.save_session()
        return msg
    
    def _split_into_rounds(self) -> List[List[Dict[str, Any]]]:
        """
        将历史消息分割为对话轮次。
        一轮对话定义为：从一个 'user' 消息开始，包含随后的所有 'assistant'/'tool' 消息，
        直到遇到下一个 'user' 消息或历史结束。
        """
        rounds = []
        current_round = []
        
        for msg in self.history:
            # 过滤掉 reasoning_content
            clean_msg = msg.copy()
            if "reasoning_content" in clean_msg:
                del clean_msg["reasoning_content"]

            if clean_msg['role'] == 'user':
                if current_round:
                    rounds.append(current_round)
                current_round = [clean_msg]
            else:
                # 兼容性：如果历史记录不是以 user 开头（罕见），也归入当前轮次（或创建新轮次）
                if not current_round and not rounds:
                    # 孤立的非 user 消息，作为第一轮
                    current_round = [clean_msg]
                else:
                    current_round.append(clean_msg)
        
        if current_round:
            rounds.append(current_round)
        
        return rounds
    
    def get_sliding_window(self) -> List[Dict[str, Any]]:
        """
        返回最后 N 轮对话中的所有消息。
        配置项 SLIDING_WINDOW_SIZE 现在表示轮次数，而非单条消息数。
        """
        rounds = self._split_into_rounds()
        
        # 获取最后 N 轮
        last_n_rounds = rounds[-self.sliding_window_size:]
        
        # 展平为消息列表
        window_messages = []
        for r in last_n_rounds:
            window_messages.extend(r)
        
        return window_messages

    def get_full_history(self) -> List[Dict[str, Any]]:
        return self.history

    def get_total_rounds(self) -> int:
        return len(self._split_into_rounds())

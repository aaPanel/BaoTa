"""
一次性 ChatCompletion 接口
用于执行一次性小任务，如生成聊天标题、RAG 判断、聊天压缩等
不支持流式响应，直接返回完整响应
"""

import json
from typing import Dict, Any, List, Union, Optional
import openai


class SingleAgent:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str = "gpt-4o-mini",
        default_headers: Optional[Dict[str, str]] = None,
        temperature: float = 0.7,
        top_p: float = 1.0
    ):
        """
        初始化一次性 Agent

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称，默认 gpt-4o-mini
            default_headers: 默认请求头
            temperature: 温度参数
            top_p: Top P 参数
        """
        
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.default_headers = default_headers or {}
        self.temperature = temperature
        self.top_p = top_p

        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=self.default_headers
        )

    def close(self):
        """关闭客户端连接"""
        self.client.close()

    def chat(
        self,
        prompt: Optional[str] = None,
        input_text: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        json_response: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行一次性 ChatCompletion

        支持两种调用模式：

        1. prompt + input 模式（推荐用于简单任务）:
           agent.chat(prompt="你是一个标题生成助手", input_text="用户的问题是什么")

        2. messages 模式（传入完整的对话历史）:
           agent.chat(messages=[
               {"role": "user", "content": "你好"}
           ])
           
        3. prompt + messages 模式（传入对话历史 + 系统提示）:
           agent.chat(prompt="你是一个助手", messages=[
               {"role": "user", "content": "你好"}
           ])
           prompt 会被添加到 messages 的第一条

        Args:
            prompt: 系统提示/任务描述（如"你是一个标题生成助手"）
            input_text: 用户输入/任务内容
            messages: 完整的消息列表
            json_response: 是否返回 JSON 响应
            json_schema: JSON 响应格式定义（可选）
            temperature: 覆盖默认 temperature
            model: 覆盖默认 model
            **kwargs: 其他 OpenAI API 参数

        Returns:
            Dict 包含:
            - success: bool 是否成功
            - response: str 响应内容（非 JSON 模式）
            - data: Any 解析后的数据（JSON 模式）
            - error: str 错误信息（失败时）
            - usage: Dict token 使用统计
        """
        try:
            # 构建消息列表
            if messages is not None:
                # messages 模式
                if prompt is not None:
                    # 如果同时有 prompt，在 messages 第一条插入 system prompt
                    request_messages = [{"role": "system", "content": prompt}] + messages
                else:
                    # 只有 messages
                    request_messages = messages
                    
                if input_text is not None:
                    # 如果同时有 input_text，追加到末尾
                    request_messages.append({"role": "user", "content": input_text})
            elif prompt is not None and input_text is not None:
                # prompt + input 模式
                request_messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_text}
                ]
            elif prompt is not None:
                # 只有 prompt，作为系统消息
                request_messages = [
                    {"role": "system", "content": prompt}
                ]
            else:
                return {
                    "success": False,
                    "error": "必须提供 prompt + input_text 或 messages 参数"
                }

            # 构建请求参数
            params = {
                "model": model or self.model_name,
                "messages": request_messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "top_p": self.top_p,
                **kwargs
            }

            # 处理 JSON 响应
            if json_response or json_schema:
                if json_schema:
                    params["response_format"] = {"type": "json_schema", "json_schema": json_schema}
                else:
                    params["response_format"] = {"type": "json_object"}

            # 调用 API（非流式）
            response = self.client.chat.completions.create(**params)

            # 提取响应内容
            if not response.choices:
                return {
                    "success": False,
                    "error": "API 返回空响应"
                }

            content = response.choices[0].message.content

            # 获取 usage 信息
            usage = None
            if response.usage:
                usage = {
                    "total_tokens": response.usage.total_tokens,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }

            # 处理响应
            if json_response or json_schema:
                try:
                    data = json.loads(content)
                    return {
                        "success": True,
                        "data": data,
                        "response": content,
                        "usage": usage
                    }
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"JSON 解析失败: {str(e)}",
                        "response": content,
                        "usage": usage
                    }
            else:
                return {
                    "success": True,
                    "response": content,
                    "usage": usage
                }

        except openai.AuthenticationError:
            return {
                "success": False,
                "error": "API 密钥错误或无效"
            }
        except openai.RateLimitError:
            return {
                "success": False,
                "error": "接口调用频率超限，请稍后重试"
            }
        except openai.APIConnectionError as e:
            return {
                "success": False,
                "error": f"无法连接到 API 服务器: {str(e)}"
            }
        except openai.APIError as e:
            return {
                "success": False,
                "error": f"API 返回错误: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"未知错误: {str(e)}"
            }

    def generate_title(self, user_input: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成聊天标题的便捷方法

        Args:
            user_input: 用户输入
            prompt: 可选的系统提示

        Returns:
            包含 title 的字典
        """
        default_prompt = prompt or "你是一个标题生成助手。请根据用户输入生成一个简短、准确的聊天标题（不超过20个字）。只返回标题，不要其他内容。"
        return self.chat(
            prompt=default_prompt,
            input_text=f"请为以下对话生成标题：{user_input}",
            temperature=0.3
        )

    def should_use_rag(self, user_input: str, threshold: float = 0.5) -> Dict[str, Any]:
        """
        判断是否需要 RAG 检索

        Args:
            user_input: 用户输入
            threshold: 判断阈值

        Returns:
            Dict 包含:
            - use_rag: bool 是否需要 RAG
            - confidence: float 置信度
            - reason: str 判断理由
        """
        prompt = """你是一个 RAG 检索判断助手。根据用户输入，判断是否需要从知识库中检索相关信息来回答。

判断标准：
- 如果问题涉及特定领域知识、技术文档、产品信息等，应该检索
- 如果是简单的闲聊或通用知识，不需要检索

请以 JSON 格式返回：
{
    "use_rag": true/false,
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}"""

        result = self.chat(
            prompt=prompt,
            input_text=user_input,
            json_response=True,
            temperature=0.1
        )

        if result["success"]:
            return {
                "use_rag": result["data"].get("use_rag", False),
                "confidence": result["data"].get("confidence", 0.0),
                "reason": result["data"].get("reason", "")
            }
        else:
            return {
                "use_rag": False,
                "confidence": 0.0,
                "reason": result.get("error", "判断失败")
            }

    def compress_conversation(
        self,
        messages: List[Dict[str, Any]],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        压缩对话历史

        Args:
            messages: 对话历史列表
            prompt: 可选的系统提示

        Returns:
            压缩后的对话摘要
        """
        default_prompt = prompt or """你是一个对话压缩助手。请将对话历史压缩为简短的摘要，
保留关键信息和上下文。输出格式为 JSON：
{
    "summary": "对话摘要",
    "key_points": ["关键点1", "关键点2"],
    "entities": ["提到的实体1", "实体2"]
}"""

        # 格式化消息
        formatted_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join([c.get("text", "") for c in content if c.get("type") == "text"])
            formatted_messages.append(f"{role}: {content}")

        conversation_text = "\n".join(formatted_messages)

        return self.chat(
            prompt=default_prompt,
            input_text=f"请压缩以下对话历史：\n{conversation_text}",
            json_response=True,
            temperature=0.3
        )

    def extract_structured_info(
        self,
        text: str,
        schema: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文本中提取结构化信息

        Args:
            text: 输入文本
            schema: JSON Schema 定义
            prompt: 可选的提示词

        Returns:
            提取的结构化数据
        """
        default_prompt = prompt or "你是一个信息提取助手。请从文本中提取结构化信息。"

        return self.chat(
            prompt=default_prompt,
            input_text=f"请从以下文本中提取信息：\n{text}",
            json_schema=schema,
            temperature=0.1
        )

    def classify_intent(
        self,
        user_input: str,
        categories: List[str],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        意图分类

        Args:
            user_input: 用户输入
            categories: 分类类别列表
            prompt: 可选的系统提示

        Returns:
            Dict 包含:
            - category: str 分类结果
            - confidence: float 置信度
            - reason: str 分类理由
        """
        default_prompt = prompt or f"""你是一个意图分类助手。请将用户输入分类到以下类别之一：
{', '.join(categories)}

请以 JSON 格式返回：
{{
    "category": "分类结果",
    "confidence": 0.0-1.0,
    "reason": "分类理由"
}}"""

        return self.chat(
            prompt=default_prompt,
            input_text=f"请分类以下用户输入：{user_input}",
            json_response=True,
            temperature=0.1
        )

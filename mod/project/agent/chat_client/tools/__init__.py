import inspect
import json
import functools
import os
from typing import Dict, Any, Callable, List, Optional, get_type_hints, Union

class ToolRegistry:
    # 状态持久化文件路径
    STATE_FILE = "/www/server/panel/data/agent/tools_state.json"

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._states: Dict[str, Dict[str, Any]] = self._load_states()

    def _load_states(self) -> Dict[str, Any]:
        """从文件加载工具状态"""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_states(self):
        """将工具状态保存到文件"""
        try:
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._states, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def tool_exists(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools
    
    def is_tool_enabled(self, name: str, enabled_ids: List[str]) -> bool:
        """
        检查工具是否在允许列表中。

        Args:
            name: 工具名称（函数名）
            enabled_ids: 允许使用的工具ID列表

        Returns:
            bool: 工具是否被允许使用
        """
        meta = self._metadata.get(name)
        if not meta:
            return False
        return meta["id"] in enabled_ids
    
    def get_tool_id(self, name: str) -> Optional[str]:
        """获取工具的ID"""
        meta = self._metadata.get(name)
        if meta:
            return meta["id"]
        return None

    def register_tool(self, tool_id: Union[str, Callable, type] = None, **kwargs):
        """
        注册工具的装饰器。
        支持:
        @register_tool
        @register_tool("my_tool_id")
        @register_tool(id="my_tool_id")
        @register_tool(id="my_tool_id", category="system")
        @register_tool(id="my_tool_id", category="system", name_cn="系统服务")
        
        以及装饰类:
        @register_tool
        class MyTool:
            def execute(self, ...): ...
        """
        category = kwargs.get("category", "default")
        name_cn = kwargs.get("name_cn", "")
        risk_level = kwargs.get("risk_level", "low")

        # 处理 id="xxx" 的关键字参数情况
        if tool_id is None and "id" in kwargs:
            tool_id = kwargs["id"]
        
        # 如果是类 (作为装饰器无参数直接使用 @register_tool)
        if inspect.isclass(tool_id):
            return self._register_class(tool_id, None, category, name_cn, risk_level)

        # 如果是函数 (作为普通装饰器使用 @register_tool (无参数))
        if callable(tool_id):
            func = tool_id
            return self._register_func(func, None, category, name_cn, risk_level)
            
        # 如果带有参数 @register_tool(...)
        def decorator(obj):
            if inspect.isclass(obj):
                return self._register_class(obj, tool_id, category, name_cn, risk_level)
            else:
                return self._register_func(obj, tool_id, category, name_cn, risk_level)
        return decorator

    def _register_class(self, clazz: type, tool_id: Optional[str], category: str, name_cn: str, risk_level: str):
        # 实例化类
        try:
            instance = clazz()
        except Exception as e:
            raise ValueError(f"Failed to instantiate tool class {clazz.__name__}: {e}")

        # 查找入口方法
        func = None
        if hasattr(instance, 'execute') and callable(instance.execute):
            func = instance.execute
        elif callable(instance):
            func = instance.__call__
        else:
            raise ValueError(f"Class {clazz.__name__} must implement 'execute' method or be callable.")

        # 确定工具ID
        if not tool_id:
            tool_id = clazz.__name__
            
        # 创建包装器以保持正确的名称和文档
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        wrapper.__name__ = tool_id
        
        # 如果方法没有文档字符串，尝试使用类的文档字符串
        if not wrapper.__doc__:
            wrapper.__doc__ = inspect.getdoc(clazz)
            
        # 注册包装后的函数
        # 注意：这里我们返回 clazz，以便类定义保持不变，
        # 但我们在内部注册了 wrapper 函数作为工具执行体。
        self._register_func(wrapper, tool_id, category, name_cn, risk_level)
        return clazz

    def _register_func(self, func: Callable, tool_id: Optional[str], category: str, name_cn: str, risk_level: str):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        name = func.__name__
        # 如果没有提供ID，使用函数名作为ID
        final_id = tool_id if tool_id else name
        
        self._tools[name] = func
        schema = self._generate_schema(func)
        self._schemas.append(schema)
        
        # 存储元数据
        state = self._states.get(final_id, {"show": True})
        self._metadata[name] = {
            "id": final_id,
            "name": name,
            "name_cn": name_cn,
            "category": category,
            "risk_level": risk_level,
            "description": schema["function"]["description"],
            "show": state.get("show", True)
        }
        
        return wrapper

    def set_tool_show_status(self, tool_id: str = None, show: bool = True, category: str = None) -> bool:
        """设置工具或分类下工具的显示状态"""
        found = False
        
        # 如果提供了 category，按分类批量设置
        if category:
            for name, meta in self._metadata.items():
                if meta.get("category") == category:
                    meta["show"] = show
                    self._states[meta["id"]] = {"show": show}
                    found = True
        
        # 如果提供了 tool_id，按 ID 设置
        elif tool_id:
            for name, meta in self._metadata.items():
                if meta["id"] == tool_id:
                    meta["show"] = show
                    self._states[tool_id] = {"show": show}
                    found = True
        
        if found:
            self._save_states()
            return True
        return False

    def get_openai_tools(self, enabled_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        返回 OpenAI 格式的工具定义。
        
        Args:
            enabled_ids: 允许使用的工具ID列表。如果不传，则返回所有(兼容旧行为)。
        """
        # 动态更新支持动态文档的工具 schema
        self._refresh_dynamic_docs()
        
        if enabled_ids is None:
            return self._schemas
        filtered_schemas = []
        for schema in self._schemas:
            name = schema["function"]["name"]
            meta = self._metadata.get(name)
            # 只有 ID 在启用列表中才返回
            if meta and meta["id"] in enabled_ids:
                filtered_schemas.append(schema)
        return filtered_schemas

    def _refresh_dynamic_docs(self):
        """
        刷新支持动态文档的工具的 schema description。
        对于实现了动态 __doc__ property 的工具，每次获取工具列表时重新生成 description。
        """
        for name, func in self._tools.items():
            # 获取实际的文档字符串（会调用 __doc__ property 如果存在）
            doc = inspect.getdoc(func)
            if doc and doc != "No description provided.":
                # 更新 schema 中的 description
                for schema in self._schemas:
                    if schema["function"]["name"] == name:
                        if schema["function"]["description"] != doc:
                            schema["function"]["description"] = doc
                        break

    def get_all_tools_info(self) -> List[Dict[str, Any]]:
        """获取所有工具的详细信息列表 (用于前端展示)"""
        infos = []
        for name, meta in self._metadata.items():
            # 创建副本以免修改原始元数据
            info = meta.copy()
            # 如果存在 name_cn，替换 name 字段
            if info.get("name_cn"):
                info["name"] = info["name_cn"]
            infos.append(info)
        return infos

    def get_tool_func(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def _generate_schema(self, func: Callable) -> Dict[str, Any]:
        """根据文档字符串和类型提示生成 OpenAI 函数 Schema"""
        # 对于 callable 对象（类的实例），使用 __call__ 方法
        target_func = func
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            if hasattr(func, '__call__'):
                target_func = func.__call__
        
        sig = inspect.signature(target_func)
        doc = inspect.getdoc(func) or "No description provided."
        
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        try:
            type_hints = get_type_hints(target_func)
        except Exception:
            type_hints = {}
        
        for name, param in sig.parameters.items():
            if name == "self" or name == "cls":
                continue
            
            # Skip *args and **kwargs
            if param.kind == inspect.Parameter.VAR_POSITIONAL or param.kind == inspect.Parameter.VAR_KEYWORD:
                continue
                
            param_type = type_hints.get(name, str)
            json_type = self._python_type_to_json_type(param_type)
            
            param_info = {"type": json_type}
            # 可以改进简单的描述提取，但目前暂跳过
            # 除非解析文档字符串参数。
            
            parameters["properties"][name] = param_info
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)
                
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "strict": True,
                "description": doc,
                "parameters": parameters
            }
        }

    def _python_type_to_json_type(self, py_type) -> str:
        if py_type == int:
            return "integer"
        elif py_type == float:
            return "number"
        elif py_type == bool:
            return "boolean"
        elif py_type == list or getattr(py_type, "__origin__", None) == list:
            return "array"
        elif py_type == dict or getattr(py_type, "__origin__", None) == dict:
            return "object"
        else:
            return "string"

# 全局注册实例
registry = ToolRegistry()

# 装饰器别名
def register_tool(tool_id=None, **kwargs):
    return registry.register_tool(tool_id, **kwargs)

# 导入所有工具以确保它们被注册
from . import agent_tools
from . import edit
from . import terminal
from . import task
from . import todo
from . import summary
from . import webfetch
from . import skill

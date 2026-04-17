# coding: utf-8
# -------------------------------------------------------------------
# AI助手管理器
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
import os, ast, datetime, json, importlib, inspect, random, shutil, base64
import time
import zipfile
import tarfile
from urllib.parse import quote

import yaml

import public

#尝试引入openai和numpy 如果没安装则执行命令安装
try:
    import openai
except ImportError:
    public.ExecShell("btpip install openai==1.39.0")
    import openai

try:
    import numpy as np
except ImportError:
    public.ExecShell("btpip install numpy==1.21.6")
    import numpy

from mod.project.agent.chat_client.tools import registry
from mod.project.agent.chat_client.skills import skill_manager
from mod.project.agent.chat_client.agent import Agent
from mod.project.agent.chat_client.simple_agent import SimpleAgent
from mod.project.agent.chat_client.single_agent import SingleAgent

import requests
import logging

# suppress verbose logging from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

panelPath = os.getenv('BT_PANEL')
if not panelPath: panelPath = '/www/server/panel'


plugin_path = '{}/mod/project/agent'.format(panelPath)
class main():
    DEFAULT_CONFIG = {
        "api_usage_url": "https://www.bt.cn/plugin_api/chat/api/usage",
        "default_headers": {
            "uid": "",
            "access-key": "",
            "appid": ""
        },

        "system_prompt": """
身份定义：
你是一个宝塔面板内置的AI助手，一个专业、高效且具备运维专项能力的智能伙伴。你不仅精通Linux运维、服务器安全、网站管理，还具备通用的知识问答与辅助能力。

核心准则：
1. 工具使用：
   - 你拥有执行工具的能力，但前提是用户必须明确启用相关工具。
   - 当发现用户的需求需要特定工具支持，而当前已有工具不足以完成该功能时，需提示用户当前工具无法完成该功能性需求，需提醒用户开启对应工具（如命令执行工具）。
   - 在拥有数据或上下文的情况下，严禁重复调用同一个工具，避免浪费系统资源。
   - 若用户未提供调用工具所需的必填参数（如服务器 IP端口号等），禁止直接调用工具，需主动追问，直至收集到完整、有效的信息；

2. 安全确认：
   - 执行任何涉及修改系统状态、删除数据、重启服务等危险命令前，必须先与用户进行确认。
   - 确认时，清晰说明将要执行的操作、涉及的对象以及可能带来的风险。

3. 真实性与落地：
   - 只提供真实有效的执行结果，绝不捏造数据或执行过程。
   - 如果无法通过工具完成任务，请给出真实可落地的手动操作方案或建议，而不是编造虚假的成功结果。

4. 交互体验：
   - 保持有人情味的对话风格，既专业又平易近人。
   - 在解决运维问题的同时，也能进行日常闲聊和情感互动。

能力范围：
- 运维专项：Linux系统管理（进程、日志、网络、磁盘）、服务器安全加固、环境部署（LNMP/LAMP）、故障排查。
- 通用辅助：代码编写、知识解答、文本处理等。
        """,
        
        # openai模型配置
        "api_base_url": "https://www.bt.cn/plugin_api/chat/openai/v1",
        "api_key": "--",
        "default_model": "",                                            #暂时先不用
        "models": [
            "qwen3.5-plus",
            "qwen3-max-2026-01-23",
            "qwen-max-2025-01-25",
            "qwen-plus",
            "doubao-seed-code-preview-251028",
        ],
        
        #嵌入模型配置
        "embedding": {
            "embedding_api_key": "--",
            "embedding_base_url": "https://www.bt.cn/plugin_api/chat/openai/embedding/v1",
            "embedding_model_name": "text-embedding-v4",
        },
        "rag": {
            "sliding_window_size": 15,      #滑动窗口大小  每次对话只保留最近n条对话
            "rag_trigger_threshold": 10,    #触发RAG的阈值当 聊天记录轮对话超过阈值时才会触发RAG
            "rag_retrieval_count": 10,      #RAG搜索数量 从向量库中获取出n条
            "rag_final_count": 5            #RAG搜索数量 最终会拼接在Message
        },
        "agent":{
            "max_tool_iterations": 30,       #最大工具调用次数  防止无限循环调用
            "temperature": 0.9,              #温度参数 控制回复的随机性
            "top_p": 0.8,                    #top_p参数 控制回复的多样性
        }
    }

    # 初始化
    def __init__(self):
        self.plugin_path = plugin_path
        self.data_path = "{}/data/agent".format(public.get_panel_path())

        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
        self.config_path = os.path.join(self.data_path, 'config.json')
        
        # 1. 以默认配置为基准 (深拷贝)
        self.config = json.loads(json.dumps(self.DEFAULT_CONFIG))
        
        # 2. 加载用户配置并逐 key 判断合并 (文件中有有效值用文件的,否则用默认的)
        user_config = self._load_config()
        self._merge_config_with_rules(self.config, user_config)
        
        # 3. 更新动态配置 (用户信息)
        user_info = public.get_user_info()
        self.DEFAULT_CONFIG['default_headers']['uid'] = str(user_info.get('uid', ''))
        self.DEFAULT_CONFIG['default_headers']['access-key'] = user_info.get('access_key', '')
        self.DEFAULT_CONFIG['default_headers']['appid'] = 'bt_app_001'
        

        if self.config.get('api_key') == self.DEFAULT_CONFIG['api_key']:
            self.config['default_headers']['uid'] = self.DEFAULT_CONFIG['default_headers']['uid']
            self.config['default_headers']['access-key'] = self.DEFAULT_CONFIG['default_headers']['access-key']
            self.config['default_headers']['appid'] = self.DEFAULT_CONFIG['default_headers']['appid']
            
            # 百炼平台埋点
            product_id_path = os.path.join(self.plugin_path, 'aliyun_product_id.pl')
            if os.path.exists(product_id_path):
                try:
                    product_id = public.readFile(product_id_path).strip()
                    account_id_path = os.path.join(self.plugin_path, 'aliyun_account_id.pl')
                    account_id = public.readFile(account_id_path).strip()
                    self.config['default_headers']['x-dashscope-euid'] = json.dumps({"bizType": "B2B", "moduleType": "Third-partyproducts", "moduleCode": f"market_{product_id}","accountType": "Aliyun", "accountId": account_id})
                except:
                    pass
            if "aliyun" in public.get_oem_name():
                models = self.config["models"]
                for i in range(len(models) - 1, -1, -1):
                    if models[i].startswith("doubao") or models[i] in ["glm-4-7-251222", "deepseek-v3-2-251201",
                                                                                 "deepseek-r1-250528",
                                                                                 "kimi-k2-thinking-251104"]:
                        models.pop(i)
    def _load_config(self):
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _save_config(self):
        """保存配置到 config.json，过滤掉与默认值相同的配置"""
        try:
            # 过滤掉与默认值相同的配置
            filtered_config = self._filter_default_values(self.config, self.DEFAULT_CONFIG)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_config, f, indent=4, ensure_ascii=False)
            return True, '保存成功'
        except Exception as e:
            return False, f'保存配置失败: {str(e)}'

    def _filter_default_values(self, current, defaults):
        """递归过滤掉与默认值相同的配置项"""
        filtered = {}
        for k, v in current.items():
            if k not in defaults:
                # 默认配置中不存在的 key，直接保留
                filtered[k] = v
            elif isinstance(v, dict) and isinstance(defaults[k], dict):
                # 递归处理嵌套字典
                nested_filtered = self._filter_default_values(v, defaults[k])
                if nested_filtered:  # 只保留有内容的嵌套字典
                    filtered[k] = nested_filtered
            elif v != defaults[k]:
                # 值与默认值不同，保留
                filtered[k] = v
            # 值与默认值相同，跳过不保存
        return filtered

            
    def _load_agents_config(self):
        """读取 agents.json 配置文件"""
        agents_config_file = os.path.join(self.plugin_path, 'agents.json')
        if not os.path.exists(agents_config_file):
            return None, '缺少配置文件 agents.json'
        
        try:
            with open(agents_config_file, 'r', encoding='utf-8') as f:
                return json.load(f), None
        except Exception as e:
            return None, f'加载配置失败 agents.json: {str(e)}'
    
    def sse_pack(self,event=None, id=None, data=None, retry=None):
        """
        通用 SSE 打包器
        - event: 事件类型 (message / message_end / error / progress 等)
        - data: 任意 dict，前端直接拿来用
        - id: 可选事件 ID
        """
        lines = []
        if id is not None:
            lines.append(f"id: {id}")
        if event is not None:
            lines.append(f"event: {event}")
        if retry is not None:
            lines.append(f"retry: {retry}")
        if data is not None:
            if isinstance(data, str):
                # 转义换行符，确保SSE格式正确，同时保留换行符给前端
                data = data.replace('\n', '\\n')
                lines.append(f"data: {data}")
            else:
                lines.append(f"data: {json.dumps(data, ensure_ascii=False)}")
        
        return "\n".join(lines) + "\n\n"
    
    def get_config(self, get):
        """
        获取插件配置信息
        """
        
        data = {}
        if self.config.get('api_key') == self.DEFAULT_CONFIG['api_key']:
            response = requests.get(self.config['api_usage_url'], headers=self.config['default_headers'])
            res = response.json()

            if 'status' not in res or not res['status']:
                return public.returnMsg(False, msg=res.get('message', '获取用户信息失败,请确认是否绑定宝塔账号!'))

            data = res.get("data", {})

        q_type = get.get('type', '')
        if q_type == 'aics':
            questions = [
                {"question": "Nginx服务无法启动", "tools": ["RunCommand"]},
                {"question": "查看服务器资源使用情况", "tools": ["get_system_resources"]},
                {"question": "查询服务器IP地址", "tools": ["get_server_ip"]},
                {"question": "CPU、磁盘负载过高怎么办?", "tools": ["get_system_resources", "get_top_processes"]},
                {"question": "MySql服务状态异常", "tools": ["RunCommand"]},
                {"question": "为系统负载进行体检", "tools": ["get_system_resources", "get_top_processes"]},
                {"question": "生成站点访问数据报告", "tools": ["get_sites", "get_site_analysis"]},
                {"question": "宝塔面板WAF是什么? ", "tools": []},
                {"question": "宝塔面板网站监控表有哪些功能?", "tools": []},
                {"question": "宝塔面板如何开启二次认证?", "tools": []},
                {"question": "宝塔面板内有哪些实用的安全工具?", "tools": []},
                {"question": "宝塔面板内有哪些好用免费的网站分析工具?", "tools": []}
            ]
            questions = random.sample(questions, 5)
        else:
            questions = [
                {"question": "Nginx服务无法启动", "tools": ["get_service_status"]},
                {"question": "检查Docker运行状态", "tools": ["get_docker_info", "get_docker_containers"]},
                {"question": "查看服务器资源使用情况", "tools": ["get_system_resources"]},
                {"question": "查询服务器IP地址", "tools": ["get_server_ip"]},
                {"question": "CPU、磁盘负载过高怎么办?", "tools": ["get_system_resources", "get_top_processes"]},
                {"question": "Docker Mysql容器状态异常", "tools": ["get_docker_info", "get_docker_containers", "get_docker_logs"]},
                {"question": "面板Mysql数据库连接失败", "tools": ["get_mysql_list", "get_firewall_status"]},
                {"question": "MySql服务状态异常", "tools": ["get_service_status"]},
                {"question": "为系统负载进行体检", "tools": ["get_system_resources", "get_top_processes"]},
                {"question": "生成站点访问数据报告", "tools": ["get_sites", "get_site_analysis"]},
                {"question": "帮我总结一下宝塔面板活动页内容：https://www.bt.cn/new/activity.html", "tools": ["WebFetch"]}
            ]
            questions = random.sample(questions, 9)

        reset_time = data.get("reset_time", 0)
        if reset_time:
            reset_time = datetime.datetime.fromtimestamp(reset_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            reset_time = "使用后24小时"

        configs = {
            # "account_type": "企业版",
            "daily_quota": {
                "used": data.get("used",0),
                "total": data.get("limit",0),
                "reset_time": reset_time,
                "activate": data.get("activate", 50),
                "common_packages": data.get("common_packages",{"total_count":0,"used_count":0,"remaining_count":0,"packages":[]})
            },
            "config": self.config,
            "is_custom_api": bool(self.config.get('api_key') == self.DEFAULT_CONFIG['api_key']),
            "questions": questions,
        }

        return public.return_data(True, data=configs)

    def get_models(self, get):
        """获取可用模型列表
        """
        base_url = get.get('base_url','')
        key = get.get('key','')
        
        if not base_url or not key:
            base_url = self.config.get('api_base_url', '')
            key = self.config.get('api_key', '')
            # return public.returnMsg(False, '缺少参数 base_url 或 key')
        
         # 动态导入 openai 库
        
        import openai
        
        client = openai.OpenAI(
            api_key=key,
            base_url=base_url,
            default_headers=self.config['default_headers']
        )
        try:
            response = client.models.list()
            model_names = [model.id for model in response.data]
            if "aliyun" in public.get_oem_name() and "bt.cn" in base_url:
                for i in range(len(model_names)-1, -1, -1):
                    if model_names[i].startswith("doubao") or model_names[i] in ["glm-4-7-251222", "deepseek-v3-2-251201", "deepseek-r1-250528", "kimi-k2-thinking-251104"]:
                        model_names.pop(i)

            return public.return_data(True, data=model_names)
        except Exception as e:
            return public.return_data(True, data=[])

    def set_config(self, get):
        """配置插件设置"""
        config_str = get.get('config', '').strip()
        if not config_str:
            return public.returnMsg(False, '缺少配置参数 config')

        try:
            user_config = json.loads(config_str)
        except:
            return public.returnMsg(False, '配置参数格式错误')

        # 以默认配置为基准
        new_config = json.loads(json.dumps(self.DEFAULT_CONFIG))
        
        # 合并配置
        self._merge_config_with_rules(new_config, user_config)
        
        # 更新 self.config
        self.config = new_config

        status, msg = self._save_config()
        if status:
            return public.returnMsg(True, '设置成功')
        else:
            return public.returnMsg(False, msg)

    def _merge_config_with_rules(self, base, update):
        """递归合并配置，空值使用默认值"""
        for k, v in update.items():
            # 处理字符串 strip
            if isinstance(v, str):
                v = v.strip()
            
            # 判断是否为空 (None, "", [])
            is_empty = (v is None) or (v == "") or (isinstance(v, list) and len(v) == 0)

            if is_empty:
                continue

            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge_config_with_rules(base[k], v)
            else:
                base[k] = v

    def get_tool_list(self, get):
        """
        获取所有工具列表、启用状态及显示配置（不包含 Skills 工具）
        @param get: 前端请求参数字典
        @param type: 可选，'aics' 表示返回 AICS 专用工具列表
        @return: {
            "status": bool,
            "data": [
                {
                    "id": str,          # 工具ID
                    "name": str,        # 工具名称（中文或ID）
                    "name_cn": str,     # 工具中文名称
                    "category": str,    # 工具分类
                    "risk_level": str,  # 风险等级
                    "description": str, # 工具描述
                    "show": bool,       # 是否在前端菜单显示
                    "enabled": bool     # 是否启用
                }
            ]
        }
        """
        tools = registry.get_all_tools_info()
        tools = [tool for tool in tools if str(tool.get("id", "")).lower() != "skills"]

        tool_type = get.get('type', '')
        if tool_type == 'aics':
            aics_tool_ids = ['Glob', 'Grep', 'LS', 'Read', 'Write', 'StopCommand', 'CheckCommandStatus', 'RunCommand', 'WebFetch',"get_system_resources","get_top_processes","get_sites","get_site_analysis","get_server_ip","get_site_overview","get_sites_logs"]
            tools = [tool for tool in tools if tool.get('id') in aics_tool_ids]
            for tool in tools:
                tool['enabled'] = True

        return public.return_data(True, data=tools)

    def set_tool_show_status(self, get):
        """
        设置工具的前端显示状态（支持按 ID 或分类设置）
        @param get: {
            "tool_id": str,  # 选填：工具ID
            "category": str, # 选填：分类名称（如 'agent', 'file'），优先级高于 tool_id
            "show": str      # 选填：'True' 或 'False'，默认为 'True'
        }
        @return: { "status": bool, "msg": str }
        """
        tool_id = get.get('tool_id')
        category = get.get('category')
        show = str(get.get('show', 'True')).lower() == 'true'

        if not tool_id and not category:
            return public.return_data(False, '参数错误，缺少 tool_id 或 category')

        res = registry.set_tool_show_status(tool_id=tool_id, show=show, category=category)
        if res:
            return public.return_data(True, '设置成功')
        return public.return_data(False, '设置失败，未找到匹配的工具或分类')

    def get_skill_list(self, get):
        """
        获取所有 skills 列表及启用状态
        @return: {
            "status": True,
            "data": {
                "total": int,
                "enabled": int,
                "disabled": int,
                "skills": [
                    {
                        "name": str,
                        "description": str,
                        "enabled": bool,
                        "location": str,
                        "metadata": dict
                    }
                ]
            }
        }
        """
        all_skills = skill_manager.get_all_skills_info()

        # 只返回主技能（一级目录下的 SKILL.md）
        skills = []
        for skill in all_skills:
            location = skill.get("location", "")
            # 计算 SKILL.md 相对于 skills 目录的层级
            rel_path = location.replace(skill_manager.SKILLS_DIR, "").strip("/")
            path_parts = rel_path.split("/")
            # 只保留顶层技能（第一级目录）
            if len(path_parts) == 2 and path_parts[1] == "SKILL.md":
                skills.append(skill)

        enabled_count = len([skill for skill in skills if skill.get("enabled")])
        data = {
            "total": len(skills),
            "enabled": enabled_count,
            "disabled": len(skills) - enabled_count,
            "skills": skills
        }
        return public.return_data(True, data=data)

    def set_skill_status(self, get):
        """
        设置单个 skill 的启用状态
        @param get.skill_name: skill 名称
        @param get.enabled: 是否启用 (true/false/1/0)
        @return: public.returnMsg
        """
        skill_name = get.get('skill_name', '').strip()
        enabled_raw = str(get.get('enabled', '')).strip().lower()
        if not skill_name:
            return public.returnMsg(False, '缺少参数 skill_name')
        if enabled_raw not in ['true', 'false', '1', '0']:
            return public.returnMsg(False, '参数 enabled 格式错误，必须是 true/false')
        enabled = enabled_raw in ['true', '1']
        result = skill_manager.set_skill_enabled(skill_name, enabled)
        if not result.get("status"):
            return public.returnMsg(False, result.get("msg", "设置失败"))
        return public.returnMsg(True, result.get("msg", "设置成功"))

    def set_enabled_skills(self, get):
        """
        批量设置启用的 skills 列表
        @param get.enabled_skills: 启用的 skill 名称列表 (JSON string or list)
        @return: {
            "status": True,
            "data": {
                "enabled_skills": list[str],
                "disabled_skills": list[str],
                "invalid_skills": list[str]
            }
        }
        """
        enabled_skills = get.get('enabled_skills', '[]')
        if isinstance(enabled_skills, str):
            try:
                enabled_skills = ast.literal_eval(enabled_skills)
            except Exception:
                return public.returnMsg(False, '参数 enabled_skills 格式错误')
        if not isinstance(enabled_skills, list):
            return public.returnMsg(False, '参数 enabled_skills 必须是列表')
        result = skill_manager.set_enabled_skills(enabled_skills)
        if not result.get("status"):
            return public.returnMsg(False, result.get("msg", "设置失败"))
        return public.return_data(True, data={
            "enabled_skills": result.get("enabled_skills", []),
            "disabled_skills": result.get("disabled_skills", []),
            "invalid_skills": result.get("invalid_skills", [])
        })

    def import_skills(self, get):
        """
        导入 skills 接口，支持 zip 和 tar.gz 格式
        @param get.file_path: 压缩文件路径
        @return: {
            "status": True,
            "msg": "导入成功"
        }
        """
        file_path = get.get('file_path', '').strip()
        if not file_path:
            return public.returnMsg(False, '缺少参数 file_path')
        
        if not os.path.exists(file_path):
            return public.returnMsg(False, '文件不存在')
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.gz' and file_path.endswith('.tar.gz'):
            file_ext = '.tar.gz'
        
        if file_ext not in ['.zip', '.tar.gz']:
            return public.returnMsg(False, '仅支持 zip 和 tar.gz 格式')
        
        skills_dir = skill_manager.SKILLS_DIR
        if not os.path.exists(skills_dir):
            os.makedirs(skills_dir)
        
        try:
            # 获取压缩包文件名（不含扩展名）作为备用文件夹名
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            if base_name.endswith('.tar'):
                base_name = os.path.splitext(base_name)[0]
            
            # 检查压缩包内的文件结构
            has_top_level_dir = False
            if file_ext == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    names = zip_ref.namelist()
                    # 检查是否所有文件都在一个顶层文件夹内
                    top_dirs = set()
                    for name in names:
                        if '/' in name:
                            top_dir = name.split('/')[0]
                            if top_dir:
                                top_dirs.add(top_dir)
                        elif name:  # 根目录下的文件
                            top_dirs.add('')
                    has_top_level_dir = len(top_dirs) == 1 and '' not in top_dirs
            elif file_ext == '.tar.gz':
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    names = tar_ref.getnames()
                    # 检查是否所有文件都在一个顶层文件夹内
                    top_dirs = set()
                    for name in names:
                        if '/' in name:
                            top_dir = name.split('/')[0]
                            if top_dir:
                                top_dirs.add(top_dir)
                        elif name:  # 根目录下的文件
                            top_dirs.add('')
                    has_top_level_dir = len(top_dirs) == 1 and '' not in top_dirs
            
            # 如果没有顶层文件夹，创建一个以压缩包名命名的文件夹
            if not has_top_level_dir:
                extract_dir = os.path.join(skills_dir, base_name)
                if not os.path.exists(extract_dir):
                    os.makedirs(extract_dir)
            else:
                extract_dir = skills_dir
            
            # 解压文件
            if file_ext == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif file_ext == '.tar.gz':
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            skill_manager._ensure_skills_dir()
            
            return public.returnMsg(True, '导入成功')
        except zipfile.BadZipFile:
            return public.returnMsg(False, '无效的 zip 文件')
        except tarfile.TarError:
            return public.returnMsg(False, '无效的 tar.gz 文件')
        except Exception as e:
            return public.returnMsg(False, f'导入失败: {str(e)}')

    def delete_skill(self, get):
        """
        删除 skill 接口，通过 skill name 删除对应的文件夹
        @param get.skill_name: skill 名称（如 "weather"）
        @return: {
            "status": True,
            "msg": "删除成功"
        }
        """
        skill_name = get.get('skill_name', '').strip()
        if not skill_name:
            return public.returnMsg(False, '缺少参数 skill_name')
        
        # 通过 skill name 查找对应的 skill 对象
        skill = skill_manager.get(skill_name)
        if not skill:
            return public.returnMsg(False, f'技能不存在: {skill_name}')
        
        # 获取 skill 文件夹路径（location 是 SKILL.md 的路径，取其父目录）
        skill_dir = os.path.dirname(skill.location)
        
        try:
            if os.path.exists(skill_dir):
                shutil.rmtree(skill_dir)
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(False, '技能文件夹不存在')
        except Exception as e:
            return public.returnMsg(False, f'删除失败: {str(e)}')

    def get_skill_agent_list(self, get):
        """
        获取所有可用 SkillAgent 列表
        @return: {
            "status": True,
            "data": {
                "categories": [str],      # 分类列表（去重）
                "total": int,             # 总数
                "list": [                 # SkillAgent 列表
                    {
                        "id": str,              # SkillAgent ID (文件名)
                        "name": str,            # SkillAgent 名称
                        "description": str,     # SkillAgent 描述
                        "icon": str,            # SkillAgent 图标
                        "category": str,        # SkillAgent 分类
                        "tools": list,          # 默认工具列表
                        "model_name": str,      # 默认模型
                        "preset_questions": list, # 预设问题列表
                        "file": str             # 文件路径
                    }
                ]
            }
        }
        """
        skill_agents_dir = os.path.join(self.plugin_path, 'skill_agents')
        if not os.path.exists(skill_agents_dir):
            return public.return_data(True, data={"categories": [], "total": 0, "list": []})

        skill_agents = []
        categories = set()
        try:
            for filename in os.listdir(skill_agents_dir):
                if not filename.endswith(('.md', '.txt')):
                    continue

                file_path = os.path.join(skill_agents_dir, filename)
                skill_agent_id = os.path.splitext(filename)[0]

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    metadata = {}
                    system_prompt = content

                    if content.startswith('---'):
                        import re
                        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                        if match:
                            frontmatter_str = match.group(1)
                            system_prompt = match.group(2).strip()
                            try:
                                parsed_config = yaml.safe_load(frontmatter_str)
                                if isinstance(parsed_config, dict):
                                    metadata = parsed_config
                            except:
                                pass

                    tools = metadata.get('tools', [])
                    if isinstance(tools, str):
                        try:
                            tools = ast.literal_eval(tools)
                        except:
                            tools = []
                    if not isinstance(tools, list):
                        tools = []

                    preset_questions = metadata.get('preset_questions', [])
                    if not isinstance(preset_questions, list):
                        preset_questions = []

                    category = metadata.get('category', '')
                    if category:
                        categories.add(category)

                    skill_agents.append({
                        "id": skill_agent_id,
                        "name": metadata.get('name', skill_agent_id),
                        "description": metadata.get('description', ''),
                        "icon": metadata.get('icon', ''),
                        "category": category,
                        "tools": tools,
                        "model_name": metadata.get('model_name', ''),
                        "preset_questions": preset_questions,
                        "file": file_path
                    })
                except:
                    continue
        except Exception as e:
            return public.returnMsg(False, f"获取 SkillAgent 列表失败: {str(e)}")

        result = {
            "categories": sorted(list(categories)),
            "total": len(skill_agents),
            "list": skill_agents
        }
        return public.return_data(True, data=result)

    def chat(self, get):
        """
        聊天接口 (SSE)
        支持通过 prompt_id 选定对应的 prompt，也支持直接传递 system_prompt
        支持通过 skill_agent_id 使用预定义的 SkillAgent
        Args:
            - message: 用户输入
            - session_id: 会话 ID (可选)
            - model: 模型名称 (可选，优先级高于 Prompt 配置)
            - system_prompt: 系统提示词 (可选，优先级高于 Prompt)
            - prompt_id: Prompt 配置 ID (可选) 从 prompts 目录加载对应的配置
            - skill_agent_id: SkillAgent ID (可选) 从 skill_agents 目录加载对应的配置
            - tools: 工具列表 (可选，优先级高于 Prompt 配置)
            - sessions_dir: 会话目录 (可选，支持 prompt 模板配置)
            - appid: 应用 ID (可选，用于覆盖 headers 中的 appid)
            - use_external_kb: 是否使用官网知识库
            - custom_headers: 自定义请求头 (可选，JSON字符串格式，会追加到默认headers中，不会覆盖)
        """
        user_input = get.get('message', '')
        if isinstance(user_input, str):
            try:
                parsed_input = json.loads(user_input)
                if isinstance(parsed_input, list):
                    user_input = parsed_input
            except json.JSONDecodeError:
                pass

        session_id = get.get('session_id', 'default_session')
        model = get.get('model', '').strip()
        system_prompt = get.get('system_prompt', '')
        prompt_id = get.get('prompt_id', '')
        skill_agent_id = get.get('skill_agent_id', '')
        tools = get.get('tools', '[]')
        tools = ast.literal_eval(tools)
        thinking = get.get('thinking', 'true').lower() == 'true'
        web_search = get.get('web_search', 'false').lower() == 'true'
        use_external_kb = get.get('use_external_kb', 'false').lower() == 'true'

        if not user_input:
            yield self.sse_pack(event="error", data={"msg": "请输入内容"})
            return

        if skill_agent_id and prompt_id:
            yield self.sse_pack(event="error", data={"msg": "skill_agent_id 与 prompt_id 不能同时使用，请选择其一"})
            return

        # 加载模板配置（skill_agent_id 与 prompt_id 互斥）
        template_id = skill_agent_id if skill_agent_id else prompt_id
        template_type = 'skill_agent' if skill_agent_id else 'prompt'
        final_system_prompt, template_config = self._load_template_config(template_id, template_type, system_prompt)
        if not final_system_prompt:
            final_system_prompt = self.config['system_prompt']

        if not final_system_prompt:
            yield self.sse_pack(event="error", data={"msg": "未找到对应助手配置，请尝试更新插件后再试~"})
            return

        # 确定 model 参数（优先级：URL > 模板配置 > 默认）
        if not model:
            model = template_config.get('model_name') or template_config.get('model')

        # 将模型信息注入到系统提示词中
        if model and final_system_prompt:
            model_info = f"\n\n当前使用模型：{model}"
            final_system_prompt = final_system_prompt + model_info

        # 获取 appid 并覆盖 headers
        headers = self.config['default_headers'].copy()
        appid = self._get_priority_value('appid', get, template_config, headers.get('appid', ''))
        if appid:
            headers['appid'] = appid

        # 合并自定义 headers（前端传递 + 模板定义，追加不覆盖）
        custom_headers = self._merge_custom_headers(get, template_config)
        headers.update(custom_headers)

        # 获取 sessions_dir
        default_sessions = 'skill_agent_sessions' if skill_agent_id else 'sessions'
        sessions_dir = self._get_priority_value('sessions_dir', get, template_config, default_sessions)

        # 工具合并策略：请求中的 tools 优先，追加模板配置中的 tools（去重），prompt 和 skill_agent 模式一致
        final_tools = list(tools) if tools else []
        template_tools = template_config.get('tools', [])
        if isinstance(template_tools, str):
            try:
                template_tools = ast.literal_eval(template_tools)
            except:
                template_tools = []
        if isinstance(template_tools, list):
            for tool in template_tools:
                if tool not in final_tools:
                    final_tools.append(tool)

        # 构造配置
        agent_config = {
            # OpenAI / Chat config
            "api_key": self._get_priority_value('api_key', get, template_config, self.config['api_key']),
            "base_url": self._get_priority_value('base_url', get, template_config, self.config['api_base_url']),
            "model_name": model,
            "small_model_name": '',

            "default_headers": headers,
            
            # Embedding config
            "embedding_api_key": self.config['embedding'].get('embedding_api_key', ''),
            "embedding_base_url": self.config['embedding'].get('embedding_base_url', ''),
            "embedding_model_name": self.config['embedding'].get('embedding_model_name', ''),
            
            # RAG config
            "sliding_window_size": int(self._get_priority_value('sliding_window_size', get, template_config, self.config['rag'].get('sliding_window_size', 10))),
            "rag_trigger_threshold": self.config['rag'].get('rag_trigger_threshold', 10),
            "rag_retrieval_count": self.config['rag'].get('retrieval_count', 10),
            "rag_final_count": self.config['rag'].get('final_count', 5),
            
            # Agent config
            "max_tool_iterations": self._get_priority_value('max_tool_iterations', get, template_config, self.config['agent'].get('max_tool_iterations', 10)),
            "tools": final_tools,
            "system_prompt": final_system_prompt,
            "temperature": float(self._get_priority_value('temperature', get, template_config, self.config['agent'].get('temperature', 1.0))),
            "top_p": float(self._get_priority_value('top_p', get, template_config, self.config['agent'].get('top_p', 1.0))),
            "thinking": thinking,
            "web_search": web_search,
            
            # Paths
            "sessions_dir": os.path.join(self.data_path, sessions_dir),
            
            # External knowledge base config
            "use_external_kb": self._get_priority_value('use_external_kb', get, template_config, False),
            
            # SkillAgent ID
            "skill_agent_id": skill_agent_id,
        }
        
        # 尝试实例化 Agent
        try:
            agent = Agent(session_id=session_id, config=agent_config)
        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"Agent 初始化失败: {str(e)}"})
            return

        try:
            # 运行流式聊天
            for chunk in agent.chat(user_input):
                if chunk.get("type") == "content":
                    yield self.sse_pack(event="message", data=chunk.get("response", ""))
                elif chunk.get("type") == "reasoning":
                    yield self.sse_pack(event="message_think", data=chunk.get("response", ""))
                elif chunk.get("type") == "error":
                    yield self.sse_pack(event="error", data={"msg": chunk.get("data", "")})
                elif chunk.get("type") == "stop":
                    yield self.sse_pack(event="usage", data={"usage": chunk.get("usage", {})})
                elif chunk.get("type") == "meta_info":
                    current_user_id = chunk.get("user_msg_id")
                    current_ai_id = chunk.get("ai_msg_id")
                    yield self.sse_pack(event="meta_info", data={"user_msg_id": current_user_id, "ai_msg_id": current_ai_id})
                else:
                    yield self.sse_pack(event=chunk.get("type"), data=chunk)

            yield self.sse_pack(event="message_end")

        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"聊天发生错误: {str(e)}"})
        finally:
            agent.close()
            log_type = f'{skill_agent_id}' if skill_agent_id else (f'{prompt_id}' if prompt_id else 'run_chat')
            public.set_module_logs(log_type, log_type, 1)

    def _load_template_config(self, template_id, template_type='prompt', system_prompt=None):
        """
        统一模板配置加载方法，支持 prompt 和 skill_agent 两种类型
        Args:
            template_id: 模板 ID（文件名，不含扩展名）
            template_type: 模板类型，'prompt' 或 'skill_agent'
            system_prompt: 外部传入的系统提示词（优先级最高）
        Returns:
            (system_prompt, config_dict)
        """
        template_config = {}
        final_system_prompt = system_prompt

        if template_id:
            if template_type == 'skill_agent':
                templates_dir = os.path.join(self.plugin_path, 'skill_agents')
            else:
                templates_dir = os.path.join(self.plugin_path, 'prompts')

            if os.path.exists(templates_dir):
                for ext in ['.md', '.txt']:
                    template_file_path = os.path.join(templates_dir, f"{template_id}{ext}")
                    if os.path.exists(template_file_path):
                        try:
                            with open(template_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if content.startswith('---'):
                                try:
                                    import re
                                    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                                    if match:
                                        frontmatter_str = match.group(1)
                                        final_system_prompt = match.group(2).strip()
                                        
                                        try:
                                            parsed_config = yaml.safe_load(frontmatter_str)
                                            if isinstance(parsed_config, dict):
                                                template_config.update(parsed_config)
                                        except Exception:
                                            pass
                                    else:
                                        final_system_prompt = content
                                except:
                                    final_system_prompt = content
                            else:
                                final_system_prompt = content
                            break
                        except Exception:
                            pass

        if final_system_prompt:
            try:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                os_version = public.get_os_version()
                final_system_prompt = final_system_prompt.replace('{{CURRENT_TIME}}', current_time)
                final_system_prompt = final_system_prompt.replace('{{OS_VERSION}}', os_version)
            except Exception:
                pass

        return final_system_prompt, template_config

    def _load_prompt_config(self, prompt_id, system_prompt=None):
        """
        加载 Prompt 配置，处理变量替换和参数提取
        返回 (system_prompt, config_dict)
        """
        prompt_config = {}
        final_system_prompt = system_prompt

        # 1. 如果指定了 prompt_id 且没有外部传入 system_prompt，则从文件加载
        if prompt_id and not final_system_prompt:
            prompts_dir = os.path.join(self.plugin_path, 'prompts')
            if os.path.exists(prompts_dir):
                for ext in ['.md', '.txt']:
                    prompt_file_path = os.path.join(prompts_dir, f"{prompt_id}{ext}")
                    if os.path.exists(prompt_file_path):
                        try:
                            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Frontmatter 解析
                            if content.startswith('---'):
                                try:
                                    import re
                                    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
                                    if match:
                                        frontmatter_str = match.group(1)
                                        final_system_prompt = match.group(2).strip()
                                        
                                        # 解析 Key-Value using PyYAML
                                        try:
                                            parsed_config = yaml.safe_load(frontmatter_str)
                                            if isinstance(parsed_config, dict):
                                                prompt_config.update(parsed_config)
                                        except Exception:
                                            pass
                                    else:
                                        final_system_prompt = content
                                except:
                                    final_system_prompt = content
                            else:
                                final_system_prompt = content
                            break # 找到文件后退出循环
                        except Exception:
                            pass

        # 2. 变量替换
        if final_system_prompt:
            try:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                os_version = public.get_os_version()
                final_system_prompt = final_system_prompt.replace('{{CURRENT_TIME}}', current_time)
                final_system_prompt = final_system_prompt.replace('{{OS_VERSION}}', os_version)
            except Exception:
                pass

        return final_system_prompt, prompt_config

    def _get_priority_value(self, key, get, prompt_config, default=None):
        """
        获取配置参数，优先级: URL参数 > Prompt配置 > 默认值
        """
        # 1. URL 参数
        val = get.get(key)
        if val:
            return val
        
        # 2. Prompt 配置
        val = prompt_config.get(key)
        if val:
            return val
            
        # 3. 默认值
        return default

    def _merge_custom_headers(self, get, template_config):
        """
        合并自定义 headers，支持前端传递和模板定义
        优先级：前端传递 > 模板定义
        逻辑：追加到现有 headers，不直接覆盖
        注意：对包含非 ASCII 字符（如中文）的值进行 URL 编码
        """
        custom_headers = {}
        
        # 1. 从模板配置中获取 custom_headers
        template_custom_headers = template_config.get('custom_headers', {})
        if isinstance(template_custom_headers, str):
            try:
                template_custom_headers = json.loads(template_custom_headers)
            except:
                template_custom_headers = {}
        if isinstance(template_custom_headers, dict):
            custom_headers.update(template_custom_headers)
        
        # 2. 从前端参数中获取 custom_headers（优先级更高）
        frontend_custom_headers = get.get('custom_headers', '')
        if frontend_custom_headers:
            if isinstance(frontend_custom_headers, str):
                try:
                    frontend_custom_headers = json.loads(frontend_custom_headers)
                except:
                    frontend_custom_headers = {}
            if isinstance(frontend_custom_headers, dict):
                custom_headers.update(frontend_custom_headers)
        
        # 3. 对包含非 ASCII 字符（如中文）的值进行 URL 编码
        encoded_headers = {}
        for key, value in custom_headers.items():
            if isinstance(value, str):
                # 检查是否包含非 ASCII 字符
                try:
                    value.encode('ascii')
                    # 纯 ASCII，不需要编码
                    encoded_headers[key] = value
                except UnicodeEncodeError:
                    # 包含非 ASCII 字符（如中文），进行 URL 编码
                    encoded_headers[key] = quote(value, safe='')
            else:
                # 非字符串值直接保留
                encoded_headers[key] = value
        
        return encoded_headers

    def simple_chat(self, get):
        """
        简单聊天接口 (SSE)
        用于小型场景，如命令生成等 默认使用官方API
        
        Args:
            - message: 用户输入
            - session_id: 会话 ID (可选)
            - model: 模型名称 (可选，优先级高于 Prompt 配置)
            - system_prompt: 系统提示词 (可选，优先级高于 Prompt
            - prompt_id: Prompt 配置 ID (可选) 从 prompts 目录加载对应的配置，支持 frontmatter 定义参数
            - tools: 工具列表 (可选，优先级高于 Prompt 配置)
            - sessions_dir: 会话目录 (可选，支持 prompt 模板配置)
            - appid: 应用 ID (可选，用于覆盖 headers 中的 appid)
            - custom_headers: 自定义请求头 (可选，JSON字符串格式，会追加到默认headers中，不会覆盖)
        """
        user_input = get.get('message', '')
        if isinstance(user_input, str):
            try:
                parsed_input = json.loads(user_input)
                if isinstance(parsed_input, list):
                    user_input = parsed_input
            except json.JSONDecodeError:
                pass

        session_id = get.get('session_id', 'simple_session')
        model = get.get('model', '').strip()
        system_prompt = get.get('system_prompt', '')
        prompt_id = get.get('prompt_id', '')

        tools = get.get('tools', '[]')
        tools = ast.literal_eval(tools)
        if not tools:
            tools = []

        # 加载 Prompt 配置
        final_system_prompt, prompt_config = self._load_prompt_config(prompt_id, system_prompt)
        if not final_system_prompt:
            final_system_prompt = get.get('system_prompt', '')

        if not final_system_prompt:
            yield self.sse_pack(event="error", data={"msg": "未找到对应助手配置，请尝试更新插件后再试~"})
            return

        if not user_input:
            yield self.sse_pack(event="error", data={"msg": "请输入内容"})
            return
        
        # 确定 model 参数
        if not model:
            model = prompt_config.get('model_name') or prompt_config.get('model')

        # 将模型信息注入到系统提示词中
        if model and final_system_prompt:
            model_info = f"\n\n当前使用模型：{model}"
            final_system_prompt = final_system_prompt + model_info

        # 获取 appid 并覆盖 headers
        headers = self.DEFAULT_CONFIG['default_headers'].copy()
        appid = self._get_priority_value('appid', get, prompt_config, headers.get('appid', ''))
        if appid:
            headers['appid'] = appid

        # 合并自定义 headers（前端传递 + 模板定义，追加不覆盖）
        custom_headers = self._merge_custom_headers(get, prompt_config)
        headers.update(custom_headers)

        # 获取 sessions_dir
        sessions_dir = self._get_priority_value('sessions_dir', get, prompt_config, 'simple_sessions')

        # 工具合并策略：请求中的 tools 优先，追加模板配置中的 tools（去重）
        final_tools = list(tools) if tools else []
        template_tools = prompt_config.get('tools', [])
        if isinstance(template_tools, str):
            try:
                template_tools = ast.literal_eval(template_tools)
            except:
                template_tools = []
        if isinstance(template_tools, list):
            for tool in template_tools:
                if tool not in final_tools:
                    final_tools.append(tool)

        # 确定其他参数: URL 参数 > Prompt 配置 > 全局配置/默认值

        # 构造配置
        agent_config = {
            "api_key": self._get_priority_value('api_key', get, prompt_config, self.DEFAULT_CONFIG['agent'].get('api_key', '')),
            "base_url": self._get_priority_value('base_url', get, prompt_config, self.DEFAULT_CONFIG['agent'].get('base_url', '')),
            "model_name": model,
            "default_headers": headers,
            "system_prompt": final_system_prompt,
            "temperature": float(self._get_priority_value('temperature', get, prompt_config, self.config['agent'].get('temperature', 1.0))),
            "top_p": float(self._get_priority_value('top_p', get, prompt_config, self.config['agent'].get('top_p', 1.0))),
            "sessions_dir": os.path.join(self.data_path, sessions_dir),
            "sliding_window_size": int(self._get_priority_value('sliding_window_size', get, prompt_config, 50)),

            "tools": final_tools,
            "use_global_rag": self._get_priority_value('use_global_rag', get, prompt_config, ''),
            
            # Embedding config for simple agent (if needed)
            "embedding_api_key": self.config['embedding'].get('embedding_api_key', ''),
            "embedding_base_url": self.config['embedding'].get('embedding_base_url', ''),
            "embedding_model_name": self.config['embedding'].get('embedding_model_name', ''),
        }
        # 尝试实例化 Agent
        try:
            agent = SimpleAgent(session_id=session_id, config=agent_config)
        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"SimpleAgent 初始化失败: {str(e)}"})
            return

        try:
            # 运行流式聊天
            for chunk in agent.chat(user_input):
                if chunk.get("type") == "content":
                    yield self.sse_pack(event="message", data=chunk.get("response", ""))
                elif chunk.get("type") == "reasoning":
                    yield self.sse_pack(event="message_think", data=chunk.get("response", ""))
                elif chunk.get("type") == "error":
                    yield self.sse_pack(event="error", data={"msg": chunk.get("data", "")})
                elif chunk.get("type") == "stop":
                    yield self.sse_pack(event="usage", data={"usage": chunk.get("usage", {})})
                elif chunk.get("type") == "meta_info":
                    current_user_id = chunk.get("user_msg_id")
                    current_ai_id = chunk.get("ai_msg_id")
                    yield self.sse_pack(event="meta_info", data={"user_msg_id": current_user_id, "ai_msg_id": current_ai_id})
                else:
                    yield self.sse_pack(event=chunk.get("type"), data=chunk)

            yield self.sse_pack(event="message_end")

        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"聊天发生错误: {str(e)}"})
        finally:
            agent.close()
            public.set_module_logs(f'{prompt_id}', 'run', 1)

    def code_chat(self, get):
        """
        代码模式聊天接口 (SSE)
        基于 Agent 类，但使用 code_mode=True
        参数控制逻辑同 simple_chat
        
        Args:
            - message: 用户输入
            - session_id: 会话 ID (可选)
            - model: 模型名称 (可选，优先级高于 Prompt 配置)
            - system_prompt: 系统提示词 (可选，优先级高于 Prompt)
            - prompt_id: Prompt 配置 ID (可选) 从 prompts 目录加载对应的配置
            - tools: 工具列表 (可选，优先级高于 Prompt 配置)
            - sessions_dir: 会话目录 (可选，支持 prompt 模板配置)
            - appid: 应用 ID (可选，用于覆盖 headers 中的 appid)
            - cwd: 工作目录 (可选，用于代码模式)
            - custom_headers: 自定义请求头 (可选，JSON字符串格式，会追加到默认headers中，不会覆盖)
        """
        user_input = get.get('message', '')
        if isinstance(user_input, str):
            try:
                parsed_input = json.loads(user_input)
                if isinstance(parsed_input, list):
                    user_input = parsed_input
            except json.JSONDecodeError:
                pass

        session_id = get.get('session_id', 'code_session')
        model = get.get('model', '').strip()
        system_prompt = get.get('system_prompt', '')
        prompt_id = get.get('prompt_id', '')
        cwd = get.get('cwd', 'No cwd provided')

        tools = get.get('tools', '[]')
        tools = ast.literal_eval(tools)
        if not tools:
            tools = []

        thinking = get.get('thinking', 'true').lower() == 'true'
        web_search = get.get('web_search', 'false').lower() == 'true'

        # 加载 Prompt 配置
        final_system_prompt, prompt_config = self._load_prompt_config(prompt_id, system_prompt)
        if not final_system_prompt:
            final_system_prompt = get.get('system_prompt', '')

        if not final_system_prompt:
            yield self.sse_pack(event="error", data={"msg": "未找到对应助手配置，请尝试更新插件后再试~"})
            return

        if not user_input:
            yield self.sse_pack(event="error", data={"msg": "请输入内容"})
            return

        # 确定 model 参数
        if not model:
            model = prompt_config.get('model_name') or prompt_config.get('model')

        # 将模型信息注入到系统提示词中
        if model and final_system_prompt:
            model_info = f"\n\n当前使用模型：{model}"
            final_system_prompt = final_system_prompt + model_info

        # 获取 appid 并覆盖 headers
        headers = self.DEFAULT_CONFIG['default_headers'].copy()
        appid = self._get_priority_value('appid', get, prompt_config, headers.get('appid', ''))
        if appid:
            headers['appid'] = appid

        # 合并自定义 headers（前端传递 + 模板定义，追加不覆盖）
        custom_headers = self._merge_custom_headers(get, prompt_config)
        headers.update(custom_headers)

        # 获取 sessions_dir
        sessions_dir = self._get_priority_value('sessions_dir', get, prompt_config, 'code_sessions')

        # 工具合并策略：请求中的 tools 优先，追加模板配置中的 tools（去重）
        final_tools = list(tools) if tools else []
        template_tools = prompt_config.get('tools', [])
        if isinstance(template_tools, str):
            try:
                template_tools = ast.literal_eval(template_tools)
            except:
                template_tools = []
        if isinstance(template_tools, list):
            for tool in template_tools:
                if tool not in final_tools:
                    final_tools.append(tool)

        # 构造配置
        agent_config = {
            "api_key": self._get_priority_value('api_key', get, prompt_config, self.config.get('api_key', '')),
            "base_url": self._get_priority_value('base_url', get, prompt_config, self.config.get('api_base_url', '')),
            "model_name": model,
            "default_headers": headers,
            "system_prompt": final_system_prompt,
            "temperature": float(self._get_priority_value('temperature', get, prompt_config, self.config['agent'].get('temperature', 1.0))),
            "top_p": float(self._get_priority_value('top_p', get, prompt_config, self.config['agent'].get('top_p', 1.0))),
            "sessions_dir": os.path.join(self.data_path, sessions_dir),
            "sliding_window_size": int(self._get_priority_value('sliding_window_size', get, prompt_config, 50)),

            "tools": final_tools,
            "use_global_rag": self._get_priority_value('use_global_rag', get, prompt_config, ''),

            "thinking": thinking,
            "web_search": web_search,
            
            # Code Mode specific
            "code_mode": True,
            "cwd": cwd,
            
            # Embedding config
            "embedding_api_key": self.config['embedding'].get('embedding_api_key', ''),
            "embedding_base_url": self.config['embedding'].get('embedding_base_url', ''),
            "embedding_model_name": self.config['embedding'].get('embedding_model_name', ''),
            
            # Agent specific
             "max_tool_iterations": self._get_priority_value('max_tool_iterations', get, prompt_config, self.config['agent'].get('max_tool_iterations', 10)),
        }
        
        # 尝试实例化 Agent
        try:
            agent = Agent(session_id=session_id, config=agent_config)
        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"Agent 初始化失败: {str(e)}"})
            return

        try:
            # 运行流式聊天
            for chunk in agent.chat(user_input):
                if chunk.get("type") == "content":
                    yield self.sse_pack(event="message", data=chunk.get("response", ""))
                elif chunk.get("type") == "reasoning":
                    yield self.sse_pack(event="message_think", data=chunk.get("response", ""))
                elif chunk.get("type") == "error":
                    yield self.sse_pack(event="error", data={"msg": chunk.get("data", "")})
                elif chunk.get("type") == "stop":
                    yield self.sse_pack(event="usage", data={"usage": chunk.get("usage", {})})
                elif chunk.get("type") == "meta_info":
                    current_user_id = chunk.get("user_msg_id")
                    current_ai_id = chunk.get("ai_msg_id")
                    yield self.sse_pack(event="meta_info", data={"user_msg_id": current_user_id, "ai_msg_id": current_ai_id})
                else:
                    yield self.sse_pack(event=chunk.get("type"), data=chunk)

            yield self.sse_pack(event="message_end")

        except Exception as e:
            yield self.sse_pack(event="error", data={"msg": f"聊天发生错误: {str(e)}"})
        finally:
            agent.close()
            public.set_module_logs(f'{prompt_id}', 'run_code_chat', 1)

    def get_chat_historys(self, get):
        """获取聊天记录列表，支持传入多个 sessions_dir"""
        sessions_dir_param = get.get('sessions_dir', '')

        # 解析 sessions_dir：支持逗号分隔字符串或 JSON 数组
        sessions_dirs = []
        if sessions_dir_param:
            if isinstance(sessions_dir_param, str):
                try:
                    parsed = ast.literal_eval(sessions_dir_param)
                    if isinstance(parsed, list):
                        sessions_dirs = parsed
                    else:
                        sessions_dirs = [sessions_dir_param]
                except:
                    sessions_dirs = [d.strip() for d in sessions_dir_param.split(',') if d.strip()]
            elif isinstance(sessions_dir_param, list):
                sessions_dirs = sessions_dir_param
        else:
            sessions_dirs = ['sessions']

        # 收集所有会话
        all_sessions = {}
        for dir_name in sessions_dirs:
            sessions_dir = os.path.join(self.data_path, dir_name)
            if not os.path.exists(sessions_dir):
                continue

            try:
                dirs = os.listdir(sessions_dir)
                for session_id in dirs:
                    session_path = os.path.join(sessions_dir, session_id)
                    if not os.path.isdir(session_path):
                        continue

                    session_file = os.path.join(session_path, 'sessions.json')
                    if not os.path.exists(session_file):
                        continue

                    try:
                        mtime = os.path.getmtime(session_file)
                        time_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

                        title = session_id
                        with open(session_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                            if history:
                                for msg in history:
                                    if msg.get('role') == 'user':
                                        content = msg.get('content', '')
                                        if isinstance(content, list):
                                            for item in content:
                                                if isinstance(item, dict) and item.get('type') == 'text':
                                                    content = item.get('text', '')
                                                    break
                                        title = content[:20] + '...' if len(content) > 20 else content
                                        break

                        skill_agent_id = ''
                        meta_file = os.path.join(session_path, 'meta.json')
                        if os.path.exists(meta_file):
                            try:
                                with open(meta_file, 'r', encoding='utf-8') as f:
                                    meta = json.load(f)
                                    skill_agent_id = meta.get('skill_agent_id', '')
                            except:
                                pass

                        session_data = {
                            "session_id": session_id,
                            "title": title,
                            "timestamp": int(mtime),
                            "time_str": time_str,
                            "skill_agent_id": skill_agent_id,
                            "sessions_dir": dir_name
                        }

                        if session_id not in all_sessions or mtime > all_sessions[session_id]["timestamp"]:
                            all_sessions[session_id] = session_data
                    except:
                        continue
            except:
                continue

        sessions = sorted(all_sessions.values(), key=lambda x: x["timestamp"], reverse=True)
        return public.return_data(True, data=sessions)

    def get_chat(self, get):
        """获取聊天记录"""
        session_id = get.get('session_id')
        if not session_id:
            return public.returnMsg(False, "缺少参数 session_id")

        custom_sessions_dir = get.get('sessions_dir', '')
        sessions_dir = custom_sessions_dir if custom_sessions_dir else 'sessions'
        session_file = os.path.join(self.data_path, sessions_dir, session_id, 'sessions.json')

        if not os.path.exists(session_file):
            return public.return_data(True, data=[])

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            for msg in history:
                if msg.get('role') == 'tool':
                    content = msg.get('content')
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict) and first_item.get('type') == 'text':
                            msg['content'] = first_item.get('text', '')

            return public.return_data(True, data=history)
        except Exception as e:
            return public.returnMsg(False, f"读取会话记录失败: {str(e)}")

    def del_chat(self, get):
        """删除聊天记录"""
        session_id = get.get('session_id')
        if not session_id:
            return public.returnMsg(False, "缺少参数 session_id")

        custom_sessions_dir = get.get('sessions_dir', '')
        sessions_dir = custom_sessions_dir if custom_sessions_dir else 'sessions'
        session_dir = os.path.join(self.data_path, sessions_dir, session_id)
        if not os.path.exists(session_dir):
            return public.returnMsg(False, "会话不存在")

        try:
            shutil.rmtree(session_dir)
            return public.returnMsg(True, "删除成功")
        except Exception as e:
            return public.returnMsg(False, f"删除失败: {str(e)}")

    def del_chat_msg(self, get):
        """删除聊天记录中的单个消息"""
        session_id = get.get('session_id')
        message_id = get.get('id')

        if not session_id:
            return public.returnMsg(False, "缺少参数 session_id")
        if not message_id:
            return public.returnMsg(False, "缺少参数 id")

        custom_sessions_dir = get.get('sessions_dir', '')
        sessions_dir = custom_sessions_dir if custom_sessions_dir else 'sessions'
        session_file = os.path.join(self.data_path, sessions_dir, session_id, 'sessions.json')
        if not os.path.exists(session_file):
            return public.returnMsg(False, "会话记录不存在")

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            original_len = len(history)
            # 过滤掉要删除的消息
            history = [msg for msg in history if msg.get('id') != message_id]

            if len(history) == original_len:
                return public.returnMsg(False, "未找到指定消息")

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)

            return public.returnMsg(True, "消息已删除")
        except Exception as e:
            return public.returnMsg(False, f"删除失败: {str(e)}")

    def get_usage_records(self, get):
        """
        查询用户资源包使用记录（分页查询）
        @param get:
            p (int): 页码，默认 1
            limit (int): 每页条数，默认 20
            limit_key (str, optional): 资源包类型筛选，如 "openai_usage"
            start_date (str, optional): 开始日期，格式 "YYYY-MM-DD"
            end_date (str, optional): 结束日期，格式 "YYYY-MM-DD"
        """
        page = int(get.get('p', 1))
        page_size = int(get.get('limit', 20))
        # limit_key = get.get('limit_key', '').strip()
        start_date = get.get('start_date', '').strip()
        end_date = get.get('end_date', '').strip()

        url = "https://www.bt.cn/plugin_api/chat/api/usage-records"
        headers = self.config['default_headers'].copy()
        headers['Content-Type'] = 'application/json'

        payload = {
            "page": page,
            "page_size": page_size,
            "limit_key": "openai_usage"
        }

        # if limit_key:
        #     payload["limit_key"] = limit_key
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        try:
            response = requests.post(url, json=payload, headers=headers)
            res = response.json()

            if 'status' not in res or not res['status']:
                return public.returnMsg(False, msg=res.get('message', '查询使用记录失败'))

            return public.return_data(True, data=res.get("data", {}))
        except Exception as e:
            return public.returnMsg(False, msg=f'查询使用记录异常: {str(e)}')

    def export_usage_records(self, get):
        """
        导出用户资源包使用记录
        @param get:
            start_date (str, optional): 开始日期，格式 "YYYY-MM-DD"
            end_date (str, optional): 结束日期，格式 "YYYY-MM-DD"
            limit_key (str, optional): 资源包类型筛选，如 "openai_usage"
        """
        start_date = get.get('start_date', '').strip()
        end_date = get.get('end_date', '').strip()
        # limit_key = get.get('limit_key', '').strip()

        url = "https://www.bt.cn/plugin_api/chat/api/usage-records"
        headers = self.config['default_headers'].copy()
        headers['Content-Type'] = 'application/json'

        payload = {
            "export": True,
            "page": 1,
            "page_size": 999999,
            "limit_key": "openai_usage"
        }
            
        # if limit_key:
        #     payload["limit_key"] = limit_key
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date

        try:
            response = requests.post(url, json=payload, headers=headers)
            res = response.json()

            if 'status' not in res or not res['status']:
                return public.returnMsg(False, msg=res.get('message', '导出使用记录失败'))

            data = res.get("data", {})
            items = data.get("items", [])

            if not items:
                return public.returnMsg(False, msg='暂无使用记录数据')

            tmp_logs_path = "/tmp/export_usage_records"
            if not os.path.exists(tmp_logs_path):
                os.makedirs(tmp_logs_path, 0o600)
            tmp_logs_file = "{}/usage_records_{}.csv".format(tmp_logs_path, int(time.time()))

            with open(tmp_logs_file, mode="w+", encoding="utf-8") as fp:
                fp.write("记录ID,资源包ID,扣减次数,剩余次数,模型名称,使用场景,扣费时间\n")
                for item in items:
                    create_at = item.get("create_at", "")
                    if create_at and "T" in create_at:
                        create_at = create_at.replace("T", " ").split(".")[0]

                    row = (
                        str(item.get("id", "")),
                        str(item.get("common_limit_id", "")),
                        str(item.get("consumed_count", 0)),
                        str(item.get("remaining_count", 0)),
                        str(item.get("model", "")),
                        str(item.get("scenario", "其他")),
                        str(item.get("total_tokens", 0)),
                        create_at,
                    )
                    fp.write(",".join(row) + "\n")

            return {
                "status": True,
                "output_file": tmp_logs_file,
            }
        except Exception as e:
            return public.returnMsg(False, msg=f'导出使用记录异常: {str(e)}')

    def create_ai_credit_order(self, get):
        """
        创建AI积分订单
        @param get.package_id: 套餐ID (必填)
        @return: {
            "status": bool,
            "data": {
                "wx": str,           # 微信支付链接
                "ali": str,          # 支付宝支付链接
                "title": str,        # 订单标题
                "price": float,      # 价格
                "out_trade_no": str, # 订单号
                "wxoid": int         # 微信订单ID
            }
        }
        """
        package_id = get.get('package_id')
        if not package_id:
            return public.returnMsg(False, '缺少参数 package_id')

        try:
            package_id = int(package_id)
        except:
            return public.returnMsg(False, '参数 package_id 格式错误')

        url = "https://www.bt.cn/api/v2/order/ai_credit/create"
        headers = {"Content-Type": "application/json"}
        
        user_info = public.get_user_info()
        params = {"package_id": package_id}
        # params = {"data": json.dumps(params)}
        params.update(user_info)

        try:
            response = requests.post(url, json=params, timeout=30, headers=headers)
            res = response.json()

            if not res.get('success'):
                return public.returnMsg(False, msg=res.get('message', '创建订单失败'))

            order_data = res.get('res', {})
            return public.return_data(True, data=order_data)
        except Exception as e:
            return public.returnMsg(False, msg=f'创建订单异常: {str(e)}')

    def get_ai_credit_packages(self, get):
        """
        获取AI积分套餐列表
        @return: {
            "status": bool,
            "data": [
                {
                    "id": int,         # 套餐ID
                    "name": str,       # 套餐名称
                    "credit": int,     # 积分数量
                    "durations": int,  # 有效期(秒)
                    "desc": str,       # 套餐描述
                    "price": int       # 价格(分)
                }
            ]
        }
        """
        url = "https://www.bt.cn/api/v2/product/ai_credit/packages"
        headers = {"Content-Type": "application/json"}
        
        user_info = public.get_user_info()
        params = {"data": "{}"}
        params.update(user_info)

        try:
            response = requests.get(url, params=params, timeout=30, headers=headers)
            res = response.json()

            if not res.get('success'):
                return public.returnMsg(False, msg=res.get('message', '获取套餐列表失败'))

            packages = res.get('res', [])
            return public.return_data(True, data=packages)
        except Exception as e:
            return public.returnMsg(False, msg=f'获取套餐列表异常: {str(e)}')

    def get_site_list(self, get):
        """
        获取网站列表，支持按网站名模糊查询
        @param get:
            name (str, optional): 网站名模糊查询关键词
            limit (int, optional): 每页数量 (默认 20)
        @return: {
            "status": bool,
            "data": [
                {
                    "name": str,          # 网站名称
                    "project_type": str,  # 项目类型
                    "status": str         # 状态
                }
            ]
        }
        """
        name = get.get('name', '').strip()
        limit = int(get.get('limit', 20))
        
        where_clause = ''
        where_params = ()
        if name:
            where_clause = 'name LIKE ?'
            where_params = ('%{}%'.format(name),)
        
        query = public.M('sites').field('name,project_type,status')
        if where_clause:
            query = query.where(where_clause, where_params)
        
        sites = query.limit(limit).select()
        
        return public.return_data(True, data=sites)

    def single_chat(self, get):
        """
        一次性 ChatCompletion 接口 (非流式)
        用于执行一次性小任务，如生成聊天标题、RAG 判断、聊天压缩、命令生成等
        不支持流式响应，直接返回完整响应
        
        Args:
            - prompt: 系统提示/任务描述（如"你是一个标题生成助手"）
            - input_text: 用户输入/任务内容
            - messages: 完整的消息列表（JSON字符串，可选）
                - 如果提供 messages，则 prompt 会作为 system 消息插入到第一条
                - 如果同时提供 input_text，会追加到 messages 末尾
            - model: 模型名称（可选，默认使用配置中的第一个模型）
            - temperature: 温度参数（可选，默认 0.7）
            - top_p: Top P 参数（可选，默认 1.0）
            - json_response: 是否返回 JSON 响应（可选，默认 false）
            - json_schema: JSON Schema 定义（JSON字符串，可选）
            - max_tokens: 最大输出 token 数（可选）
            - presence_penalty: 存在惩罚（可选）
            - frequency_penalty: 频率惩罚（可选）
            - stop: 停止词（JSON字符串，可选）
            - api_key: 自定义 API Key（可选，覆盖全局配置）
            - base_url: 自定义 Base URL（可选，覆盖全局配置）
            - appid: 自定义 AppID（可选，覆盖 headers 中的 appid）
            - custom_headers: 自定义请求头（可选，JSON字符串格式，会追加到默认headers中，不会覆盖）
            
        Returns:
            {
                "status": bool,
                "msg": str,
                "data": {
                    "success": bool,
                    "response": str,       # 响应内容
                    "data": Any,           # JSON 解析后的数据（json_response=true 时）
                    "usage": {             # token 使用统计
                        "total_tokens": int,
                        "input_tokens": int,
                        "output_tokens": int
                    },
                    "error": str           # 错误信息（失败时）
                }
            }
            
        使用示例:
            1. 简单问答:
               GET /single_chat?prompt=你是一个助手&input_text=你好
            
            2. 生成标题:
               GET /single_chat?prompt=你是一个标题生成助手&input_text=用户的问题是什么&temperature=0.3
            
            3. JSON 响应:
               GET /single_chat?prompt=分析以下文本的情感&input_text=今天天气真好&json_response=true
            
            4. 带 Schema 的 JSON 响应:
               GET /single_chat?prompt=提取信息&input_text=文本内容&json_schema={"type":"object","properties":{"name":{"type":"string"}}}
            
            5. 完整对话历史:
               GET /single_chat?prompt=你是助手&messages=[{"role":"user","content":"你好"},{"role":"assistant","content":"你好！"}]
            
            6. 自定义模型和参数:
               GET /single_chat?prompt=你是助手&input_text=你好&model=qwen3.5-plus&temperature=0.5&max_tokens=1000
        """
        prompt = get.get('prompt', '')
        input_text = get.get('input_text', '')
        messages_str = get.get('messages', '')
        model = get.get('model', '').strip()
        temperature_str = get.get('temperature', '')
        top_p_str = get.get('top_p', '')
        json_response_str = get.get('json_response', 'false').lower()
        json_schema_str = get.get('json_schema', '')
        max_tokens_str = get.get('max_tokens', '')
        presence_penalty_str = get.get('presence_penalty', '')
        frequency_penalty_str = get.get('frequency_penalty', '')
        stop_str = get.get('stop', '')
        custom_api_key = get.get('api_key', '')
        custom_base_url = get.get('base_url', '')
        appid = get.get('appid', '')

        if not prompt and not messages_str:
            return public.returnMsg(False, "缺少参数 prompt 或 messages")

        if not prompt and not input_text and not messages_str:
            return public.returnMsg(False, "必须提供 prompt + input_text 或 messages 参数")

        messages = None
        if messages_str:
            try:
                messages = json.loads(messages_str)
                if not isinstance(messages, list):
                    return public.returnMsg(False, "参数 messages 必须是数组格式")
            except json.JSONDecodeError as e:
                return public.returnMsg(False, f"参数 messages 格式错误: {str(e)}")

        temperature = 0.7
        if temperature_str:
            try:
                temperature = float(temperature_str)
            except ValueError:
                return public.returnMsg(False, "参数 temperature 格式错误")

        top_p = 1.0
        if top_p_str:
            try:
                top_p = float(top_p_str)
            except ValueError:
                return public.returnMsg(False, "参数 top_p 格式错误")

        json_response = json_response_str in ['true', '1', 'yes']

        json_schema = None
        if json_schema_str:
            try:
                json_schema = json.loads(json_schema_str)
            except json.JSONDecodeError as e:
                return public.returnMsg(False, f"参数 json_schema 格式错误: {str(e)}")

        kwargs = {}
        if max_tokens_str:
            try:
                kwargs['max_tokens'] = int(max_tokens_str)
            except ValueError:
                return public.returnMsg(False, "参数 max_tokens 格式错误")

        if presence_penalty_str:
            try:
                kwargs['presence_penalty'] = float(presence_penalty_str)
            except ValueError:
                return public.returnMsg(False, "参数 presence_penalty 格式错误")

        if frequency_penalty_str:
            try:
                kwargs['frequency_penalty'] = float(frequency_penalty_str)
            except ValueError:
                return public.returnMsg(False, "参数 frequency_penalty 格式错误")

        if stop_str:
            try:
                stop = json.loads(stop_str)
                if isinstance(stop, str):
                    stop = [stop]
                kwargs['stop'] = stop
            except json.JSONDecodeError:
                kwargs['stop'] = [stop_str]

        api_key = custom_api_key if custom_api_key else self.config.get('api_key', '')
        base_url = custom_base_url if custom_base_url else self.config.get('api_base_url', '')

        if not api_key or not base_url:
            return public.returnMsg(False, "缺少 API 配置，请先配置 API Key 和 Base URL")

        headers = self.config['default_headers'].copy()
        if appid:
            headers['appid'] = appid

        # 合并自定义 headers（前端传递，single_chat 不支持模板定义）
        frontend_custom_headers = get.get('custom_headers', '')
        if frontend_custom_headers:
            if isinstance(frontend_custom_headers, str):
                try:
                    frontend_custom_headers = json.loads(frontend_custom_headers)
                except:
                    frontend_custom_headers = {}
            if isinstance(frontend_custom_headers, dict):
                # 对包含非 ASCII 字符（如中文）的值进行 URL 编码
                for key, value in frontend_custom_headers.items():
                    if isinstance(value, str):
                        try:
                            value.encode('ascii')
                        except UnicodeEncodeError:
                            frontend_custom_headers[key] = quote(value, safe='')
                headers.update(frontend_custom_headers)

        if not model:
            models = self.config.get('models', [])
            if models:
                model = models[0]
            else:
                model = 'gpt-4o-mini'

        try:
            agent = SingleAgent(
                api_key=api_key,
                base_url=base_url,
                model_name=model,
                default_headers=headers,
                temperature=temperature,
                top_p=top_p
            )

            result = agent.chat(
                prompt=prompt if prompt else None,
                input_text=input_text if input_text else None,
                messages=messages,
                json_response=json_response,
                json_schema=json_schema,
                **kwargs
            )

            agent.close()

            return public.return_data(True, data=result)

        except Exception as e:
            return public.returnMsg(False, f"调用失败: {str(e)}")


if __name__ == '__main__':
    pass

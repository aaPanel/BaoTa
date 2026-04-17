import os
import re
import yaml
from typing import List, Dict, Optional
import public

class Skill:
    def __init__(self, name: str, location: str, description: str, content: str, metadata: Dict):
        self.name = name
        self.location = location
        self.description = description
        self.content = content
        self.metadata = metadata

class SkillManager:
    _instance = None
    
    # 全局 Skills 目录，默认为 chat_client 上一级的 skills 目录
    # 也可以通过环境变量 BT_AGENT_SKILLS_DIR 覆盖
    SKILLS_DIR = f"{public.get_panel_path()}/data/agent/skills"
    SKILLS_STATE_FILE = f"{public.get_panel_path()}/data/agent/skills_state.json"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._ensure_skills_dir()
        self._state = self._load_state()

    def _ensure_skills_dir(self):
        if not os.path.exists(self.SKILLS_DIR):
            try:
                os.makedirs(self.SKILLS_DIR)
            except OSError:
                pass

    def _load_state(self) -> Dict:
        default_state = {"disabled_skills": []}
        if not os.path.exists(self.SKILLS_STATE_FILE):
            return default_state
        try:
            with open(self.SKILLS_STATE_FILE, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f)
            if not isinstance(state, dict):
                return default_state
            disabled = state.get("disabled_skills", [])
            if not isinstance(disabled, list):
                disabled = []
            return {"disabled_skills": [str(name).strip() for name in disabled if str(name).strip()]}
        except Exception:
            return default_state

    def _save_state(self) -> bool:
        try:
            state_dir = os.path.dirname(self.SKILLS_STATE_FILE)
            if state_dir and not os.path.exists(state_dir):
                os.makedirs(state_dir)
            with open(self.SKILLS_STATE_FILE, "w", encoding="utf-8") as f:
                yaml.safe_dump(self._state, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception:
            return False

    def _normalize_names(self, names: List[str]) -> List[str]:
        if not isinstance(names, list):
            return []
        normalized = []
        for name in names:
            if name is None:
                continue
            normalized_name = str(name).strip()
            if normalized_name and normalized_name not in normalized:
                normalized.append(normalized_name)
        return normalized

    def _disabled_name_set(self) -> set:
        disabled_names = self._state.get("disabled_skills", [])
        normalized = self._normalize_names(disabled_names)
        self._state["disabled_skills"] = normalized
        return set(normalized)

    def all(self) -> List[Skill]:
        skills = []
        if not os.path.exists(self.SKILLS_DIR):
            return skills

        # 递归扫描所有子目录
        for root, dirs, files in os.walk(self.SKILLS_DIR):
            if 'SKILL.md' in files:
                skill = self._load_skill_from_dir(root)
                if skill:
                    skills.append(skill)
        return skills

    def get(self, name: str) -> Optional[Skill]:
        # 遍历所有 skills 查找匹配的名字
        for skill in self.all():
            if skill.name == name:
                return skill
        return None

    def get_enabled(self, name: str) -> Optional[Skill]:
        skill = self.get(name)
        if not skill:
            return None
        if not self.is_enabled(name):
            return None
        return skill

    def all_enabled(self) -> List[Skill]:
        disabled_names = self._disabled_name_set()
        return [skill for skill in self.all() if skill.name not in disabled_names]

    def is_enabled(self, name: str) -> bool:
        if not self.get(name):
            return False
        disabled_names = self._disabled_name_set()
        return name not in disabled_names

    def set_skill_enabled(self, name: str, enabled: bool) -> Dict:
        skill = self.get(name)
        if not skill:
            return {"status": False, "msg": f"技能不存在: {name}"}
        disabled_names = self._disabled_name_set()
        if enabled:
            disabled_names.discard(name)
        else:
            disabled_names.add(name)
        self._state["disabled_skills"] = sorted(disabled_names)
        if not self._save_state():
            return {"status": False, "msg": "保存技能状态失败"}
        return {"status": True, "msg": "设置成功"}

    def set_enabled_skills(self, enabled_names: List[str]) -> Dict:
        normalized_enabled = set(self._normalize_names(enabled_names))
        all_skills = self.all()
        all_names = {skill.name for skill in all_skills}
        invalid_names = sorted([name for name in normalized_enabled if name not in all_names])
        final_enabled = sorted([name for name in normalized_enabled if name in all_names])
        disabled_names = sorted(list(all_names - set(final_enabled)))
        self._state["disabled_skills"] = disabled_names
        if not self._save_state():
            return {"status": False, "msg": "保存技能状态失败"}
        return {
            "status": True,
            "msg": "设置成功",
            "enabled_skills": final_enabled,
            "disabled_skills": disabled_names,
            "invalid_skills": invalid_names
        }

    def get_all_skills_info(self) -> List[Dict]:
        disabled_names = self._disabled_name_set()
        infos = []
        for skill in self.all():
            infos.append({
                "name": skill.name,
                "description": skill.description,
                "location": skill.location,
                "enabled": skill.name not in disabled_names,
                "metadata": skill.metadata
            })
        return infos

    def _load_skill_from_dir(self, skill_dir: str) -> Optional[Skill]:
        # 查找 SKILL.md
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_md_path):
            return None

        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, body = self._parse_frontmatter(content)
            
            name = metadata.get('name', os.path.basename(skill_dir))
            description = metadata.get('description', '')
            
            return Skill(
                name=name,
                location=skill_md_path,
                description=description,
                content=body,
                metadata=metadata
            )
        except Exception as e:
            # print(f"Error loading skill from {skill_dir}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> (Dict, str):
        """
        解析 YAML Frontmatter
        格式:
        ---
        key: value
        ---
        body
        """
        frontmatter_regex = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_regex.match(content)
        
        metadata = {}
        body = content
        
        if match:
            yaml_content = match.group(1)
            body = content[match.end():]
            
            # 使用 PyYAML 解析
            try:
                parsed_yaml = yaml.safe_load(yaml_content)
                if isinstance(parsed_yaml, dict):
                    metadata = parsed_yaml
            except yaml.YAMLError:
                # 解析失败时保留空字典或根据需求处理
                pass
        
        return metadata, body

    def list_files(self, skill_dir: str, limit: int = 50) -> List[str]:
        """
        列出 skill 目录下的文件，排除隐藏文件和 SKILL.md
        """
        files = []
        for root, dirs, filenames in os.walk(skill_dir):
            # 排除隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in filenames:
                if filename == "SKILL.md" or filename.startswith('.'):
                    continue
                
                full_path = os.path.join(root, filename)
                files.append(full_path)
                
                if len(files) >= limit:
                    return files
        return files

# 全局单例
skill_manager = SkillManager.get_instance()

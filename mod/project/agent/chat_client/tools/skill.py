
import os
import json
from . import register_tool
from .base import _xml_response
from ..skills import skill_manager

# 动态生成文档字符串以包含可用 skills
def _get_skill_doc():
    skills = skill_manager.all_enabled()
    
    if not skills:
        return "Load a specialized skill that provides domain-specific instructions and workflows. No skills are currently available."

    skill_list = "\n".join([
        f"  <skill>\n    <name>{s.name}</name>\n    <description>{s.description}</description>\n  </skill>"
        for s in skills
    ])

    examples = ", ".join([f"'{s.name}'" for s in skills[:3]])
    hint = f" (e.g., {examples}, ...)" if examples else ""

    return f"""Load a specialized skill that provides domain-specific instructions and workflows.(当用户提到 技能、Skills、Skill时优先告诉用户你拥有以下可用技能)

When you recognize that a task matches one of the available skills listed below, use this tool to load the full skill instructions.

The skill will inject detailed instructions, workflows, and access to bundled resources (scripts, references, templates) into the conversation context.

Tool output includes a `<skill_content name="...">` block with the loaded content.

The following skills provide specialized sets of instructions for particular tasks
Invoke this tool to load a skill when a task matches one of the available skills listed below:

<available_skills>
{skill_list}
</available_skills>

Args:
    name: The name of the skill from available_skills{hint}
"""


class Skills:
    """
    Skills, 动态加载Skills列表,通过动态生成 __doc__ 来更新可用技能列表。
    """
    
    __name__ = "Skills"
    
    @property
    def __doc__(self):
        # 每次访问 __doc__ 时都重新生成，确保获取最新的 skills 状态
        return _get_skill_doc()
    
    def __call__(self, name: str):
        """调用时执行实际的 skill 加载逻辑"""
        skill_obj = skill_manager.get_enabled(name)
        
        if not skill_obj:
            target_skill = skill_manager.get(name)
            if target_skill and not skill_manager.is_enabled(name):
                return _xml_response("error", f"Skill '{name}' is disabled.")
            available = ", ".join([s.name for s in skill_manager.all_enabled()])
            return _xml_response("error", f"Skill '{name}' not found. Available skills: {available or 'none'}")

        # 获取文件列表
        skill_dir = os.path.dirname(skill_obj.location)
        files = skill_manager.list_files(skill_dir)
        file_list_str = "\n".join([f"<file>{f}</file>" for f in files])

        output = [
            f"<skill_content name=\"{skill_obj.name}\">",
            f"# Skill: {skill_obj.name}",
            "",
            skill_obj.content.strip(),
            "",
            f"Base directory for this skill: {skill_dir}",
            "Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.",
            "Note: file list is sampled. limited to 50 files.",
            "",
            "<skill_files>",
            file_list_str,
            "</skill_files>",
            "</skill_content>"
        ]

        return _xml_response("done", "\n".join(output))


# 注册工具
Skills = register_tool(category="Agent", name_cn="Skills", risk_level="low")(Skills())

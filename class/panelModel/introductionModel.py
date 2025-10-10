# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
import public
from panelModel.base import panelBase


class main(panelBase):
    __pulgin_info = {
        "php_filter": {"introduction": ["网站实时监控", "网站及时告警", "木马隔离", "精准拦截恶意行为"], "name": "堡塔PHP安全防护"},
        "bt_security": {"introduction": ["权限隔离", "命令日志记录", "跟踪操作"], "name": "堡塔防入侵"},
        "system_scan": {"introduction": ["全方位扫描", "多系统扫描", "可靠的修复方案", "一键修复", "软件包检测"], "name": "系统漏洞扫描"},
        "vuln_push": {"introduction": ["前沿漏洞情报", "及时推送", "多平台收集情报"], "name": "漏洞情报推送"},
        "disk_analysis": {"introduction": ["磁盘空间占用分析", "快速锁定大文件", "磁盘预警"], "name": "堡塔硬盘分析工具"},
        "btwaf": {"introduction": ["防御常见web攻击", "关键词拦截", "拦截恶意扫描", "阻止黑客入侵"], "name": "Nginx防火墙"},
        "btwaf_httpd": {"introduction": ["防御常见web攻击", "关键词拦截", "拦截恶意扫描", "阻止黑客入侵"], "name": "Apache防火墙"},
        "total": {"introduction": ["网站实时监控", "实时分析网站运行", "精确统计网站流量等数据", "网站SEO优化利器"], "name": "网站监控报表"},
        "rsync": {"introduction": ["多机文件同步", "定时/实时备份", "数据异地灾", "文件异地多活"], "name": "文件同步工具"},
        "tamper_proof": {"introduction": ["保护站点内容安全", "防止黑客非法修", "防止网站挂马", "防止篡改网站"], "name": "网站防篡改程序"},
        "tamper_core": {"introduction": ["内核级防护，更安全", "阻止其他入侵行为", "阻止网站被挂马", "阻止黑客非法修改网页"], "name": "堡塔企业级防篡改 - 重构版"},
        "syssafe": {"introduction": ["灵活的系统加固功能", "防止系统被植入木马", "服务器日志审计", "等保加固功能"], "name": "宝塔系统加固"},
        "task_manager": {"introduction": ["像win一样管理进程", "流量监控", "管理链接", "用户管理"], "name": "宝塔任务管理器"},
        "security_notice": {"introduction": ["PHP内核监控工具", "监控网站木马", "木马自动隔离", "检测入侵"], "name": "PHP网站安全告警"},
    }

    def get_plugin_info(self, get):
        if not hasattr(get, 'plugin_name'):
            return public.returnMsg(False, "请传入正确的参数！")
        return self.__pulgin_info.get(get.plugin_name, {"introduction": [], "name": "未找到配置信息！"})

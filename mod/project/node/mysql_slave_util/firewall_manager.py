# -*- coding: utf-8 -*-
"""
防火墙管理模块
负责主从复制所需的防火墙配置
"""

from typing import Dict, Any
import public


class FirewallManager:
    """防火墙管理器"""
    
    def __init__(self):
        pass

    def allow_master_firewall_port(self, slave_ip: str) -> Dict[str, Any]:
        """允许主库防火墙放行从库IP"""
        try:
            from firewallModel.comModel import main
            f_get = public.dict_obj()
            f_get.protocol = "tcp"
            f_get.port = "3306"
            f_get.choose = "point"
            f_get.types = "accept"
            f_get.address = slave_ip
            f_get.brief = ""
            f_get.domain = ""
            f_get.chain = "INPUT"
            f_get.operation = "add"
            f_get.strategy = "accept"
            result = main().set_port_rule(f_get)
            if result.get("status") is False:
                return public.returnMsg(False, "防火墙放行失败")
            return public.returnMsg(True, "防火墙放行成功")
        except Exception as e:
            return public.returnMsg(False, f"防火墙配置失败: {str(e)}")

    def remove_master_firewall_port(self, slave_ip: str) -> Dict[str, Any]:
        """移除主库防火墙规则"""
        try:
            from firewallModel.comModel import main
            f_get = public.dict_obj()
            f_get.protocol = "tcp"
            f_get.port = "3306"
            f_get.choose = "point"
            f_get.types = "accept"
            f_get.address = slave_ip
            f_get.brief = ""
            f_get.domain = ""
            f_get.chain = "INPUT"
            f_get.operation = "del"
            f_get.strategy = "accept"
            result = main().set_port_rule(f_get)
            if result.get("status") is False:
                return public.returnMsg(False, "防火墙规则删除失败")
            return public.returnMsg(True, "防火墙规则删除成功")
        except Exception as e:
            return public.returnMsg(False, f"防火墙配置失败: {str(e)}")

    def check_firewall_rule_exists(self, slave_ip: str) -> bool:
        """检查防火墙规则是否存在"""
        try:
            from firewallModel.comModel import main
            # 这里可以实现检查逻辑，根据实际API调整
            return False
        except:
            return False 
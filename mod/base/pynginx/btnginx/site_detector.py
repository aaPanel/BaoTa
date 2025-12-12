#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
站点配置分离与分类实现
基于readme.md中第三步的逻辑实现
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from .. import Config, Server, trans_

# 定义站点类型枚举
SITE_TYPE_PHP = "PHP"
SITE_TYPE_PROXY = "反向代理"
SITE_TYPE_STATIC = "静态"
SITE_TYPE_UN_INIT = ""

# 定义站点信息namedtuple，带类型提示
@dataclass
class SiteInfo:
    server_names: List[str]     # 服务器名称列表（可能包含多个）
    listen_ports: List[int]    # 监听端口列表
    site_type: str             # 站点类型
    config_file: str           # 配置文件路径
    server_blocks: List[Server] # 服务器块对象列表（可能包含多个）


class SiteDetector:
    """
    站点配置分离与分类器
    实现readme.md中描述的站点配置分离与分类逻辑
    """

    def __init__(self, main_conf: Config):
        """
        初始化站点检测器
        :param main_conf: Nginx主配置信息
        """
        assert isinstance(main_conf, Config) , "main_conf must be a Config object"
        self.config: Config = main_conf


    def detect_sites(self) -> List[SiteInfo]:
        """
        检测并分类所有站点配置
        :return: 站点信息列表
        """
        http = self.config.find_http()
        if not http:
            return []
        # 获取所有server块
        servers: List[Server] = [trans_(i, Server) for i in http.find_directives("server", include=True)]
        # 转化为站点信息列表
        sites = self._paser_sites(servers)

        ret_sites = []
        # 合并相同server_name的站点
        while sites:
            site = sites.pop(0)
            used_srv = []
            for other_site in sites:
                if set(site.server_names) == set(other_site.server_names):
                    # 合并端口和服务器块
                    site.listen_ports.extend(other_site.listen_ports)
                    site.server_blocks.extend(other_site.server_blocks)
                    used_srv.append(other_site)

            # 从sites中移除已合并的站点
            for srv in used_srv:
                sites.remove(srv)

            site.site_type = self._determine_site_type(site.server_blocks)
            ret_sites.append(site)

        return ret_sites

    def _paser_sites(self, servers: List[Server]) -> List[SiteInfo]:
        """
        解析所有server块列表，生成可供比较的站点信息列表
        :param servers: server块列表
        :return: 站点信息列表
        """
        sites = [] # type: List[SiteInfo]
        
        for server in servers:
            # 查找server_name指令，包括子块中的指令
            server_block = server.get_block()
            if not server_block:
                continue
            server_names = server_block.find_directives("server_name", include=True, sub_block=False)
            if not server_names:
                # 如果没有server_name指令，使用默认名称
                server_name = ["_"]
            else:
                # 获取第一个server_name指令的参数
                server_name = server_names[0].get_parameters() if server_names[0].get_parameters() else ["_"]

            sites.append(SiteInfo(
                server_names=server_name,
                listen_ports=self._get_server_ports([server]),
                site_type=SITE_TYPE_UN_INIT,
                config_file="",
                server_blocks=[server]
            ))

        return sites

    @staticmethod
    def _determine_site_type(servers: List[Server]) -> str:
        """
        判定站点类型
        :param servers: server块列表
        :return: 站点类型
        """
        for server in servers:
            server_block = server.get_block()
            if not server_block:
                continue
            # 检查是否存在fastcgi_pass指令（PHP项目），包括子块中的指令
            if server_block.find_directives("fastcgi_pass", include=True, sub_block=True):
                return SITE_TYPE_PHP
                
            # 检查是否存在proxy_pass指令（反向代理项目），包括子块中的指令
            if server_block.find_directives("proxy_pass", include=True, sub_block=True):
                return SITE_TYPE_PROXY

        # 默认为静态项目
        return SITE_TYPE_STATIC

    @staticmethod
    def _get_server_ports(servers: List[Server]) -> List[int]:
        """
        获取监听端口列表
        :param servers: server块列表
        :return: 监听端口列表
        """
        ports = []
        for server in servers:
            server_block = server.get_block()
            if not server_block:
                continue

            listen_directives = server_block.find_directives("listen", include=True, sub_block=False)
            
            for listen in listen_directives:
                params = listen.get_parameters()
                if not params:
                    continue
                for p in params:
                    if ':' in p:
                        p = p.split(':')[-1]
                    if p.isdigit():
                        try:
                            p_int = int(p)
                            if 0 <= p_int <= 65535:
                                ports.append(p)
                        except ValueError:
                            pass

        return ports

def site_detector(main_conf: Config) -> List[SiteInfo]:
    """
    检测并分类所有站点配置
    :param main_conf: Nginx主配置信息
    :return: 站点信息列表
    """
    detector = SiteDetector(main_conf)
    return detector.detect_sites()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nginx组件实现 - Python版本
包含Http、Server、Location、Upstream等具体组件
"""
import re
from typing import List, Optional, Dict, Union
from dataclasses import dataclass, field

# 导入基础类
from .nginx_base import Directive, Block, IDirective, IBlock, _Trans


@dataclass
class Http(IDirective, IBlock, _Trans):
    """Http块组件"""
    servers: List["Server"] = field(default_factory=list)
    directives: List[IDirective] = field(default_factory=list)
    comment: List[str] = field(default_factory=list)
    inline_comment: List[str] = field(default_factory=list)
    _parent: Optional['IDirective'] = field(default=None, repr=False, compare=False)
    line: int = 0


    def get_parameters(self) -> List[str]:
        return  []

    def get_block(self) -> Optional['IBlock']:
        return self

    def get_name(self) -> str:
        return "http"

    def get_comment(self) -> List[str]:
        return self.comment

    def set_comment(self, comment: List[str]):
        return self.comment

    def get_line(self) -> int:
        return self.line

    def set_parent(self, parent: Optional['IDirective']):
        self._parent = parent

    def get_parent(self) -> Optional['IDirective']:
        return self._parent

    def set_inline_comment(self, comment: str):
        self.inline_comment.append(comment)

    def get_inline_comment(self) -> List[str]:
        return self.inline_comment

    def get_directives(self) -> List[IDirective]:
        res = []
        for directive in self.directives:
            res.append(directive)
        for srv in self.servers:
            res.append(srv)
        return  res

    def get_code_block(self) -> str:
        return ""

    def find_directives(self, directive_name: str) -> List[IDirective]:
        if directive_name == "server":
            return self.servers
        directives = []
        for directive in self.get_directives():
            if directive.get_name() == directive_name:
                directives.append(directive)
            if directive.get_block() is not None:
                directives.extend(directive.get_block().find_directives(directive_name))
        return directives

    @classmethod
    def from_directive(cls, directive: Union[IDirective,Directive]) -> 'Http':
        if directive.__class__ is cls:
            return directive
        if directive.get_block() is None:
            raise ValueError("http 块为空")
        servers = []
        _directives = []
        for directive in directive.get_block().get_directives():
            if directive.__class__ is Server:
                servers.append(directive)
            else:
                _directives.append(directive)
        return cls(
            servers=servers,
            line=directive.get_line(),
            directives=_directives,
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
        )


@dataclass
class Server(Directive, _Trans):
    """Server块组件"""

    @classmethod
    def from_directive(cls, directive: Union[IDirective, Directive]) -> 'Server':
        if directive.__class__ is cls:
            return directive
        if directive.get_block() is None:
            raise ValueError("Server块组件需要有块内容")
        return cls(
            name="server",
            parameters=[],
            line=directive.get_line(),
            block=directive.get_block(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
        )

    def top_find_directives(self, directive_name: str) -> List[IDirective]:
        """在 server 的顶块中查找"""
        directives = self.get_block().get_directives()
        return [directive for directive in directives if directive.get_name() == directive_name]

    # 只在server块内部查询，不会返回子块中的指令如：location 块内信息，
    # param 将顺序依次匹配
    def top_find_directives_with_param(self, directive_name: str, *params: Union[str, re.Pattern]):
        directives = self.get_block().get_directives()
        res = []
        params_match = lambda x, y: x == y if not isinstance(x, re.Pattern) else re.match(x, y)
        for d in directives:
            if d.get_name() == directive_name:
                if len(params) == 0:
                    res.append(d)
                else:
                    d_params = d.get_parameters()
                    min_len = min(len(params), len(d_params))
                    if all([params_match(params[i], d_params[i]) for i in range(min_len)]):
                        res.append(d)
        return  res




@dataclass
class Location(Directive, _Trans):
    """Location块组件"""
    modifier: str = ""
    match: str = ""

    def top_find_directives(self, directive_name: str) -> List[IDirective]:
        """在 server 的顶块中查找"""
        directives = self.get_block().get_directives()
        return [directive for directive in directives if directive.get_name() == directive_name]

    # 只在server块内部查询，不会返回子块中的指令如：location 块内信息，
    # param 将顺序依次匹配
    def top_find_directives_with_param(self, directive_name: str, *params: str):
        directives = self.get_block().get_directives()
        res = []
        for d in directives:
            if d.get_name() == directive_name:
                if len(params) == 0:
                    res.append(d)
                else:
                    d_params = d.get_parameters()
                    min_len = min(len(params), len(d_params))
                    if all([d_params[i] == params[i] for i in range(min_len)]):
                        res.append(d)
        return  res

    def top_find_directives_like_param(self, directive_name: str, param: str):
        directives = self.get_block().get_directives()
        res = []
        for d in directives:
            if d.get_name() == directive_name:
                if not param:
                    res.append(d)
                else:
                    d_params = d.get_parameters()
                    for d_param in d_params:
                        if param in d_param:
                            res.append(d)
        return  res

    @classmethod
    def from_directive(cls, directive: Union[IDirective, Directive]) -> 'Location':
        if directive.__class__ is cls:
            return directive
        param = directive.get_parameters()
        match, modifier = "", ""
        if len(param) == 1:
            match = param[0]
        elif len(param) == 2:
            modifier, match = param
        else:
            raise ValueError("location指令必须有1-2个参数")
        return cls(
            name="location",
            parameters=param,
            line=directive.get_line(),
            block=directive.get_block(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
            modifier=modifier,
            match=match,
        )


@dataclass
class Upstream(IDirective, IBlock, _Trans):
    """Upstream块组件"""
    upstream_name: str = ""
    servers: List['UpstreamServer'] = field(default_factory=list)
    directives: List[IDirective] = field(default_factory=list)
    comment: List[str] = field(default_factory=list)
    inline_comment: List[str] = field(default_factory=list)
    _parent: Optional['IDirective'] = field(default=None, repr=False, compare=False)
    line: int = 0

    def get_name(self) -> str:
        return "upstream"

    def get_parameters(self) -> List[str]:
        return  [self.upstream_name]

    def get_block(self) -> Optional['IBlock']:
        return  self

    def get_comment(self) -> List[str]:
        return self.comment

    def set_comment(self, comment: List[str]):
        self.comment =  comment

    def get_line(self) -> int:
        return self.line

    def set_parent(self, parent: Optional['IDirective']):
        self._parent = parent

    def get_parent(self) -> Optional['IDirective']:
        return self._parent

    def get_inline_comment(self) -> List[str]:
        return self.inline_comment

    def set_inline_comment(self, comment: str):
        self.inline_comment.append(comment)

    def get_directives(self) -> List[IDirective]:
        res: List[IDirective] = self.servers.copy()
        for sub_dir in self.directives:
            res.append(sub_dir)
        return res

    def get_code_block(self) -> str:
        return ""

    def find_directives(self, directive_name: str) -> List[IDirective]:
        """查找指定名称的指令"""
        directives = []
        for directive in self.get_directives():
            if directive.get_name() == directive_name:
                directives.append(directive)
            if directive.get_block() is not None:
                directives.extend(directive.get_block().find_directives(directive_name))
        return directives

    @classmethod
    def from_directive(cls, directive: Union[IDirective, Directive]) -> 'Upstream':
        if type(directive) is cls:
            return directive
        parameters = directive.get_parameters()
        if len(parameters) != 1:
            raise ValueError("upstream指令参数数量错误")
        name = parameters[0]
        if directive.get_block() is None:
            raise ValueError("upstream指令缺少块")
        res = cls(
            line=directive.get_line(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
            upstream_name=name,
        )
        servers = []
        directives = []
        for sun_dir in directive.get_block().get_directives():
            if sun_dir.get_name() == "server":
                ups = UpstreamServer.from_directive(sun_dir)
                ups.set_parent(res)
                servers.append(ups)
            else:
                directives.append(sun_dir)
        res.servers = servers
        res.directives = directives

        return  res


@dataclass
class UpstreamServer(IDirective, _Trans):
    """Upstream Server组件"""
    address: str = ""
    flags: List[str] = field(default_factory=list)
    comment: List[str] = field(default_factory=list)
    inline_comment: List[str] = field(default_factory=list)
    parameters: Dict[str, str] = field(default_factory=dict)
    _parent: Optional['IDirective'] = field(default=None, repr=False, compare=False)
    line: int = 0

    def get_name(self) -> str:
        return "server"

    def get_parameters(self) -> List[str]:
        return self.to_directive().parameters

    def get_block(self) -> Optional['IBlock']:
        return None

    def get_comment(self) -> List[str]:
        return self.comment

    def set_comment(self, comment: List[str]):
        self.comment = comment

    def get_line(self) -> int:
        return self.line

    def set_parent(self, parent: Optional['IDirective']):
        self._parent = parent

    def get_parent(self) -> Optional['IDirective']:
        return self._parent

    def get_inline_comment(self) -> List[str]:
        return self.inline_comment

    def set_inline_comment(self, comment: str):
        self.inline_comment.append(comment)

    @classmethod
    def from_directive(cls, directive: Union[Directive,IDirective]) -> 'UpstreamServer':
        if cls is directive.__class__:
            return directive
        dpt = directive.get_parameters()
        if len(dpt) < 1:
            raise ValueError("upstream 中的server命令至少有一个参数且为地址信息")
        parameters, flags = {}, []
        if len(dpt) > 1:
            parameters = dict(p.split("=")[:2] for p in dpt[1:] if "=" in p)
            flags = [p for p in dpt[1:] if "=" not in p]
        address = dpt[0]
        return cls(
            parameters=parameters,
            line=directive.get_line(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
            flags=flags,
            address=address,
        )

    def to_directive(self)-> Directive:
        parameters = [self.address]
        for k, v in self.parameters.items():
            parameters.append(f"{k}={v}")

        for flag in self.flags:
            parameters.append(flag)

        return Directive(
            name="server",
            parameters=parameters,
            line=self.get_line(),
            block=None,
            comment=self.get_comment(),
            inline_comment=self.get_inline_comment(),
            _parent=self.get_parent(),
        )

    def get_server_address(self) -> str:
        """获取服务器地址"""
        return self.address


@dataclass
class LuaBlock(IDirective, IBlock, _Trans):
    """Lua代码块组件"""
    directives: List[IDirective] = field(default_factory=list)
    name: str = ""
    comment: List[str] = field(default_factory=list)
    inline_comment: List[str] = field(default_factory=list)
    lua_code: str = ""
    _parent: Optional['IDirective'] = field(default=None, repr=False, compare=False)
    line: int = 0
    parameters: List[str] = field(default_factory=list)

    def get_name(self) -> str:
        return self.name

    def get_parameters(self) -> List[str]:
        return self.parameters

    def get_block(self) -> Optional['IBlock']:
        return self

    def get_comment(self) -> List[str]:
        return self.comment

    def set_comment(self, comment: List[str]):
        self.comment = comment

    def get_line(self) -> int:
        return self.line

    def set_parent(self, parent: Optional['IDirective']):
        self._parent = parent

    def get_parent(self) -> Optional['IDirective']:
        return self._parent

    def get_inline_comment(self) -> List[str]:
        return self.inline_comment

    def set_inline_comment(self, comment: str):
        self.inline_comment.append(comment)

    def get_directives(self) -> List[IDirective]:
        return self.directives

    def get_code_block(self) -> str:
        return self.lua_code

    def find_directives(self, directive_name: str) -> List[IDirective]:
        directives = []
        for directive in self.get_directives():
            if directive.get_name() == directive_name:
                directives.append(directive)
            if directive.get_block() is not None:
                directives.extend(directive.get_block().find_directives(directive_name))
        return directives

    @classmethod
    def from_directive(cls, directive: Union[IDirective, Directive]) -> 'LuaBlock':
        if directive.__class__ is LuaBlock:
            return directive
        if directive.get_block() is None:
            raise ValueError("Directive does not have a block")
        return cls(
            line=directive.get_line(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
            name=directive.get_name(),
            parameters=directive.get_parameters(),
            lua_code=directive.get_block().get_code_block(),
        )



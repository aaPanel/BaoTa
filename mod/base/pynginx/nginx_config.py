from dataclasses import dataclass, field
from typing import List, Optional, Union

from .nginx_base import Block, Directive, _Trans, IDirective
from .nginx_components import Server, Http, Upstream


@dataclass
class Config(Block):
    """配置"""
    file_path: str = ""

    def find_servers(self) -> List['Server']:
        """查找所有server块"""
        servers = []
        directives = self.find_directives("server")
        for directive in directives:
            # 使用字符串类型检查避免循环依赖
            if hasattr(directive, '__class__') and directive.__class__.__name__ == 'Server':
                servers.append(directive)
        return servers

    def find_http(self) -> Optional['Http']:
        """查找http块"""
        directives = self.find_directives("http")
        if directives:
            directive = directives[0]
            # 使用字符串类型检查避免循环依赖
            if hasattr(directive, '__class__') and directive.__class__.__name__ == 'Http':
                return directive
        return None

    def find_upstreams(self) -> List['Upstream']:
        """查找所有upstream块"""
        upstreams = []
        directives = self.find_directives("upstream")
        for directive in directives:
            # 使用字符串类型检查避免循环依赖
            if hasattr(directive, '__class__') and directive.__class__.__name__ == 'Upstream':
                upstreams.append(directive)
        return upstreams


@dataclass
class Include(Directive, _Trans):  # 不实现 IBlock 接口，但可以解析
    """包含文件"""
    include_path: str = ""
    configs: List[Config] = field(default_factory=list)

    @classmethod
    def from_directive(cls, directive: Union[IDirective, Directive]) -> 'Include':
        if directive.__class__ is cls:
            return directive
        parameters = directive.get_parameters()
        if not len(parameters) == 1:
            raise ValueError("include指令参数数量错误")
        return cls(
            line=directive.get_line(),
            block=directive.get_block(),
            name=directive.get_name(),
            comment=directive.get_comment(),
            inline_comment=directive.get_inline_comment(),
            parameters=parameters,
            _parent=directive.get_parent(),
            include_path=parameters[0]
        )

    def get_directives(self) -> List[IDirective]:
        res =[]
        for config in self.configs:
            res.extend(config.get_directives())
        return  res

    def find_directives(self, directive_name: str) -> List[IDirective]:
        res =[]
        for config in self.configs:
            res.extend(config.find_directives(directive_name))
        return  res

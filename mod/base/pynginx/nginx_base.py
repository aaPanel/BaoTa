#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nginx解析器基础类和接口
"""
from abc import abstractmethod, ABC
from typing import List, Optional, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum


class TokenType(Enum):
    """词法标记类型"""
    EOF = "EOF"
    KEYWORD = "KEYWORD"
    QUOTED_STRING = "QUOTED_STRING"
    SEMICOLON = "SEMICOLON"
    BLOCK_START = "BLOCK_START"
    BLOCK_END = "BLOCK_END"
    COMMENT = "COMMENT"
    LUA_CODE = "LUA_CODE"
    END_OF_LINE = "END_OF_LINE"  # 新增


@dataclass
class Token:
    """词法标记"""
    type: TokenType
    literal: str
    line: int
    column: int


@dataclass
class Style:
    """输出样式配置"""
    space_before_blocks: bool = False
    start_indent: int = 0
    indent: int = 4
    
    def iterate(self) -> 'Style':
        """创建下一级缩进的样式"""
        return Style(
            space_before_blocks=self.space_before_blocks,
            start_indent=self.start_indent + self.indent,
            indent=self.indent
        )


# 默认样式
INDENTED_STYLE = Style()


class IDirective(ABC):
    """指令接口"""
    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_parameters(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def get_block(self) -> Optional['IBlock']:
        raise NotImplementedError

    @abstractmethod
    def get_comment(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def set_comment(self, comment: List[str]):
        raise NotImplementedError

    @abstractmethod
    def get_line(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def set_parent(self, parent: Optional['IDirective']):
        raise NotImplementedError

    @abstractmethod
    def get_parent(self) -> Optional['IDirective']:
        raise NotImplementedError

    @abstractmethod
    def get_inline_comment(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def set_inline_comment(self, comment: str):
        raise NotImplementedError


class IBlock(ABC):
    """块接口"""

    @abstractmethod
    def get_directives(self) -> List[IDirective]:
        raise NotImplementedError

    @abstractmethod
    def get_code_block(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def find_directives(self, directive_name: str) -> List[IDirective]:
        raise NotImplementedError

    @abstractmethod
    def set_parent(self, parent: Optional[IDirective]):
        raise NotImplementedError

    @abstractmethod
    def get_parent(self) -> Optional[IDirective]:
        raise NotImplementedError


@dataclass
class Directive(IDirective):
    """指令实现"""
    line: int = 0
    block: Optional['Block'] = None
    name: str = ""
    comment: List[str] = field(default_factory=list)
    inline_comment: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    _parent: Optional['IDirective'] = field(default=None, repr=False, compare=False)
    
    def get_name(self) -> str:
        return self.name
    
    def get_parameters(self) -> List[str]:
        return self.parameters
    
    def get_block(self) -> Optional['Block']:
        return self.block
    
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


@dataclass
class Block(IBlock):
    """块实现"""
    directives: List[IDirective] = field(default_factory=list)
    is_lua_block: bool = False
    literal_code: str = ""
    _parent: Optional[IDirective] = field(default=None, repr=False, compare=False)
    
    def get_directives(self) -> List[IDirective]:
        return self.directives

    def get_code_block(self) -> str:
        return self.literal_code
    
    def find_directives(self, directive_name: str) -> List[IDirective]:
        """查找指定名称的指令"""
        directives = []
        for directive in self.get_directives():
            if directive.get_name() == directive_name:
                directives.append(directive)
            if directive.get_block() is not None:
                directives.extend(directive.get_block().find_directives(directive_name))
        return directives
    
    def set_parent(self, parent: Optional[IDirective]):
        self._parent = parent
    
    def get_parent(self) -> Optional[IDirective]:
        return self._parent

    def replace_directive(self, old_directive: IDirective, new_directive: IDirective):
        """替换指令"""
        for i, directive in enumerate(self.directives):
            if directive == old_directive:
                self.directives[i] = new_directive
                break


class _Trans(ABC):

    @classmethod
    @abstractmethod
    def from_directive(cls, directive: Directive) -> IDirective:
        raise NotImplementedError


# 定义类型变量
_T = TypeVar('_T')

def trans_(any_dir, cls: Type[_T]) -> Optional[_T]:
    if cls is any_dir.__class__:
        return any_dir
    try:
        if isinstance(any_dir, _Trans):
            return cls.from_directive(any_dir)
    except:
        pass
    return None

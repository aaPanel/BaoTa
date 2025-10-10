#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nginx配置解析器 - Python版本
基于Go版本的nginx解析器改写
"""

import re
from typing import Optional, List, Dict
import glob
import os

# 导入基础类和接口
from .nginx_base import (
    TokenType, Token, Style, INDENTED_STYLE,
    IDirective, IBlock, Directive, Block, trans_
)

# 导入组件
from .nginx_components import (
    Http, Server, Location, Upstream, LuaBlock, UpstreamServer
)

from .nginx_config import Config, Include


class Lexer:
    """词法分析器，按需生成token，支持lua块模式"""
    def __init__(self, content: str, file_path: str = ""):
        self.content = content
        self.file_path = file_path
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(content)
        self.in_lua_block = False
        self.last_keyword: Optional[str] = None  # 记录最近一次关键字token

    def _scan_lua_code_token(self):
        lua_code = ''
        start_line = self.line
        start_col = self.column
        lua_brace_count = 0  # 括号计数, 开始的括号已被读取，所当括号计数为0，且读取到 } 时结束
        while self.pos < self.length:
            char = self.content[self.pos]
            if char == '#':
                # 读取到行尾，注释内不计brace
                lua_code += char
                self.pos += 1
                self.column += 1
                while self.pos < self.length and self.content[self.pos] != '\n':
                    lua_code += self.content[self.pos]
                    self.pos += 1
                    self.column += 1
                continue
            elif char == '{':
                lua_brace_count += 1
            elif char == '}':
                if lua_brace_count == 0:
                    # 块结束，退出lua模式 保留结束的 } 不读取出来
                    break

                lua_brace_count -= 1

            lua_code += char
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

        return Token(
            type=TokenType.LUA_CODE,
            literal=lua_code,
            line=start_line,
            column=start_col
        )

    def next_token(self):
        if self.in_lua_block:
            self.in_lua_block = False
            return self._scan_lua_code_token()
        while self.pos < self.length:
            char = self.content[self.pos]
            if char == '\n':
                token = Token(
                    type=TokenType.END_OF_LINE,
                    literal='\n',
                    line=self.line,
                    column=self.column
                )
                self.pos += 1
                self.line += 1
                self.column = 1
                return token
            if char.isspace():
                self.pos += 1
                self.column += 1
                continue
            if char == '#':
                start_col = self.column
                comment = self._read_comment()
                return Token(
                    type=TokenType.COMMENT,
                    literal=comment,
                    line=self.line,
                    column=start_col
                )
            if char in ('"', "'", '`'):
                start_col = self.column
                string_literal = self._read_quoted_string(end_char=char)
                return Token(
                    type=TokenType.QUOTED_STRING,
                    literal=string_literal,
                    line=self.line,
                    column=start_col
                )
            if char == ';':
                token = Token(
                    type=TokenType.SEMICOLON,
                    literal=char,
                    line=self.line,
                    column=self.column
                )
                self.pos += 1
                self.column += 1
                return token
            if char == '{':
                # 优化lua块起始检测：仅当最近一次关键字为lua相关指令
                if self.last_keyword and self.last_keyword.lower().endswith("_by_lua_block"):
                    self.in_lua_block = True

                token = Token(
                    type=TokenType.BLOCK_START,
                    literal=char,
                    line=self.line,
                    column=self.column
                )
                self.pos += 1
                self.column += 1
                return token
            if char == '}':
                token = Token(
                    type=TokenType.BLOCK_END,
                    literal=char,
                    line=self.line,
                    column=self.column
                )
                self.pos += 1
                self.column += 1
                return token
            # 关键字或标识符
            start_col = self.column
            keyword = self._read_keyword()
            self.last_keyword = keyword  # 记录最近一次关键字
            return Token(
                type=TokenType.KEYWORD,
                literal=keyword,
                line=self.line,
                column=start_col
            )
        return Token(
            type=TokenType.EOF,
            literal="",
            line=self.line,
            column=self.column
        )

    def _read_comment(self) -> str:
        """读取注释"""
        comment = ""
        while self.pos < self.length and self.content[self.pos] != '\n':
            comment += self.content[self.pos]
            self.pos += 1
            self.column += 1
        return comment

    def _read_quoted_string(self, end_char: str) -> str:
        """读取引号字符串"""
        string_literal = end_char
        self.pos += 1  # 跳过开始的引号
        self.column += 1

        while self.pos < self.length:
            char = self.content[self.pos]
            if char == end_char:
                string_literal += char
                self.pos += 1
                self.column += 1
                break
            if char == '\\' and self.pos + 1 < self.length:
                # 转义字符
                string_literal += char + self.content[self.pos + 1]
                self.pos += 2
                self.column += 2
            else:
                string_literal += char
                self.pos += 1
                self.column += 1

        return string_literal

    def _read_keyword(self) -> str:
        """读取关键字"""
        keyword = ""
        while self.pos < self.length:
            char = self.content[self.pos]
            if char.isspace() or char in ';{}"#':
                break
            keyword += char
            self.pos += 1
            self.column += 1
        return keyword


# 关于非行内注释的解析， 我们仅将命令的前n行(默认为1)作为该指令的注释，如果有>n的情况，则生成纯注释指令
class Parser:
    """语法分析器"""
    def __init__(self, lexer: Lexer, parse_include: bool=False, comment_line_count: int=1):
        self.lexer = lexer
        self.current_token = self.lexer.next_token()
        self.following_token = self.lexer.next_token()
        self.comment_buffer: List[str] = []
        self.comment_line_count = max(comment_line_count, 0)
        self.parse_include = parse_include
        # 缓存已经解析的include文件 key:文件绝对路径 value:Config
        self.parsed_includes: Dict[str, Config] = dict()

    def _update_parsed_includes(self, **kwargs):
        self.parsed_includes.update(**kwargs)

    def _next_token(self):
        self.current_token = self.following_token
        self.following_token = self.lexer.next_token()

    def _current_token_is(self, token_type: TokenType) -> bool:
        """检查当前标记类型"""
        return self.current_token and self.current_token.type == token_type

    def _following_token_is(self, token_type: TokenType) -> bool:
        """检查下一个标记类型"""
        return self.following_token and self.following_token.type == token_type

    def parse(self) -> Config:
        """解析配置"""
        parsed_block = self._parse_block(False)
        return Config(
            directives=parsed_block.get_directives(),
            is_lua_block=parsed_block.is_lua_block,
            literal_code=parsed_block.get_code_block(),
            _parent=parsed_block.get_parent(),
            file_path=self.lexer.file_path
        )

    def _parse_block(self, in_block: bool) -> Block:
        """解析块"""
        context = Block(directives=[], )
        # 设置子指令的parent为当前Block
        # 由于指令还未添加，需在后续append时设置
        
        while True:
            if self._current_token_is(TokenType.END_OF_LINE):
                self._next_token()
                continue
            if self._current_token_is(TokenType.EOF):
                if in_block:
                    raise ValueError("在块中遇到意外的EOF")
                break
            if self._current_token_is(TokenType.BLOCK_END):
                break
            if self._current_token_is(TokenType.LUA_CODE):
                context.is_lua_block = True
                context.literal_code = self.current_token.literal
            elif (self._current_token_is(TokenType.KEYWORD) or
                  self._current_token_is(TokenType.QUOTED_STRING)):
                statement = self._parse_statement()
                if statement.get_block() is not None:
                    b = statement.get_block()
                    for d in b.get_directives():
                        d.set_parent(statement)
                else:
                    statement.set_parent(statement)

                context.directives.append(statement)
            elif self._current_token_is(TokenType.COMMENT):
                if len(self.comment_buffer) >= self.comment_line_count:
                    other, self.comment_buffer = self.comment_buffer[0], self.comment_buffer[1:]
                    context.directives.append(Directive(
                        name="",
                        parameters=[],
                        comment=[other],
                        line=self.current_token.line - self.comment_line_count
                    ))

                self.comment_buffer.append(self.current_token.literal)


            self._next_token()
        if self.comment_buffer:
            context.directives.append(Directive(
                name="",
                parameters=[],
                comment=self.comment_buffer,
            ))
            self.comment_buffer = []
        return context

    def _parse_statement(self) -> IDirective:
        """解析语句"""
        directive = Directive(
            name=self.current_token.literal,
            line=self.current_token.line
        )

        if len(self.comment_buffer):
            directive.set_comment(self.comment_buffer)
            self.comment_buffer = []
        self._next_token()
        # 跳过多余的END_OF_LINE
        while self.current_token and self.current_token.type == TokenType.END_OF_LINE:
            self._next_token()
        # Read parameters
        while (self.current_token and
               (self.current_token.type in [TokenType.KEYWORD, TokenType.QUOTED_STRING] or
                re.match(r'^[a-zA-Z0-9_./~*^()$-]+$', self.current_token.literal))):
            directive.parameters.append(self.current_token.literal)
            self._next_token()
            while self.current_token and self.current_token.type == TokenType.END_OF_LINE:
                self._next_token()

        if self._current_token_is(TokenType.SEMICOLON):
            if (self.following_token and
                self.following_token.type == TokenType.COMMENT and
                self.current_token.line == self.following_token.line):
                directive.inline_comment = [self.following_token.literal]
                self._next_token()
            if directive.name == "server":
                return self._wrap_upstream_servers(directive)
            elif directive.name == "include":
                icl = self._warp_include(directive)
                if self.parse_include:
                    return self._parser_include(icl)
                else:
                    return icl

            return directive

        if self._current_token_is(TokenType.BLOCK_START):

            # 处理lua块
            if directive.name.endswith("_by_lua_block"):

                self._next_token()
                b = Block(directives=[], is_lua_block=True)
                brace_count = 1
                lua_code = ""
                while brace_count > 0 and not self._current_token_is(TokenType.EOF):
                    if self._current_token_is(TokenType.BLOCK_START):
                        brace_count += 1
                    elif self._current_token_is(TokenType.BLOCK_END):
                        brace_count -= 1
                        if brace_count == 0:
                            break
                    if not (self._current_token_is(TokenType.BLOCK_END) and brace_count == 0):
                        lua_code += self.current_token.literal
                        if self.following_token.type not in (
                            TokenType.BLOCK_END, TokenType.END_OF_LINE, TokenType.SEMICOLON
                        ):
                            lua_code += " "

                    self._next_token()

                b.literal_code = lua_code.lstrip("\n").rstrip()
                directive.block = b

                return self._wrap_lua_block(directive)

            block = self._parse_block(True)  # Pass in_block=True
            block.set_parent(directive)
            directive.block = block
            if directive.name == "http":
                return self._wrap_http(directive)
            elif directive.name == "server":
                return self._wrap_server(directive)
            elif directive.name == "location":
                return self._wrap_location(directive)
            elif directive.name == "upstream":
                return self._wrap_upstream(directive)
            return directive
        raise ValueError(
            f"指令 \"{directive.name}\" 在第 {directive.line} 行缺少 ';' 或 '{{' "
            f"(遇到的标记: {self.current_token.type.value} '{self.current_token.literal}')"
        )

    def _parser_include(self, icl: Include) -> Include:
        # 只在 parse_include=True 时调用
        include_path = icl.include_path
        # 绝对路径
        if not os.path.isabs(include_path):
            # 以主配置文件所在目录为基准
            base_dir = os.path.dirname(self.lexer.file_path)
            include_path = os.path.abspath(os.path.join(base_dir, include_path))
        # glob 匹配
        paths = glob.glob(include_path)
        for path in paths:
            abs_path = os.path.abspath(path)
            if self.parsed_includes is not None and abs_path in self.parsed_includes:
                config = self.parsed_includes[abs_path]
            else:
                # 递归解析
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                lexer = Lexer(content.replace('\r\n', '\n'), abs_path)
                parser = Parser(lexer, parse_include=self.parse_include)
                parser._update_parsed_includes(**self.parsed_includes)
                config = parser.parse()
                self._update_parsed_includes(**parser.parsed_includes)
            icl.configs.append(config)
        return icl

    @staticmethod
    def _wrap_http(directive: Directive) -> Http:
        """包装http块"""
        return Http.from_directive(directive)

    @staticmethod
    def _wrap_server(directive: Directive) -> Server:
        """包装server块"""
        return Server.from_directive(directive)

    @staticmethod
    def _wrap_location(directive: Directive) -> Location:
        """包装location块"""
        return Location.from_directive(directive)

    @staticmethod
    def _wrap_upstream(directive: Directive) -> Upstream:
        """包装upstream块"""
        return Upstream.from_directive(directive)

    @staticmethod
    def _wrap_lua_block(directive: Directive) -> LuaBlock:
        """包装lua块"""
        return LuaBlock.from_directive(directive)

    @staticmethod
    def _wrap_upstream_servers(directive: Directive) -> UpstreamServer:
        """包装upstream服务器"""
        return UpstreamServer.from_directive(directive)

    @staticmethod
    def _warp_include(directive: Directive) -> Include:
        """包装location"""
        return Include.from_directive(directive)


def _lua_formatter(code: str, indent:str) -> str:
    code = code.replace("\t", "  ")
    lines = code.split("\n")
    min_scp = 9999
    for line in  lines:
        scp = len(line) - len(line.lstrip())
        if scp < min_scp:
            min_scp = scp

    if 0 < min_scp < 9999:
        lines = [indent + line[min_scp:] for line in lines]
    return "\n".join(lines)


def dump_directive(directive: IDirective, style: Style) -> str:
    if directive is None:
        return ""
    indent = ' ' * style.start_indent
    buf = []
    # 注释
    for c in directive.get_comment() or []:
        buf.append(f'{indent}{c}\n')

    if not directive.get_name(): # 纯注释信息
        return ''.join(buf)
    # 指令名和参数
    line = f'{indent}{directive.get_name()}'
    params = directive.get_parameters()
    if params:
        line += ' ' + ' '.join(params)
    buf.append(line)
    # 块
    block = directive.get_block()
    if block is None:
        if directive.get_name():
            buf.append(';')
        # inline_comment
        inline_comment = directive.get_inline_comment() or []
        if inline_comment:
            buf.append(' ' + ' '.join(inline_comment))
        return ''.join(buf)
    # 块指令
    if block.get_code_block():
        # Lua块
        buf.append(' {\n')
        code = block.get_code_block()
        buf.append(_lua_formatter(code, style.iterate().start_indent * " "))
        buf.append(f'\n{indent}}}')
        return ''.join(buf)
    else:
        buf.append(' {')
        # inline_comment
        inline_comment = directive.get_inline_comment() or []
        if inline_comment:
            buf.append(' ' + ' '.join(inline_comment))
        buf.append('\n')
        buf.append(dump_block(block, style.iterate()))
        buf.append(f'\n{indent}}}')
        return ''.join(buf)


def dump_block(block: IBlock, style: Style) -> str:
    # 支持排序
    directives = block.get_directives()
    buf = []
    n = len(directives)
    for i, directive in enumerate(directives):
        buf.append(dump_directive(directive, style))
        if i != n - 1:
            buf.append('\n')
    return ''.join(buf)


def dump_config(config: 'Config', style: Style=INDENTED_STYLE) -> str:
    return dump_block(config, style)


def write_config(config: Config, style: Style) -> None:
    """写入配置文件"""
    content = dump_config(config, style)
    with open(config.file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def parse_string(content: str, parse_include: bool = False) -> Config:
    """从字符串解析配置"""
    lexer = Lexer(content.replace('\r\n', '\n'))
    parser = Parser(lexer, parse_include)
    return parser.parse()


def parse_file(file_path: str, parse_include: bool = False) -> Config:
    """从文件解析配置"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lexer = Lexer(content.replace('\r\n', '\n'), file_path)
    parser = Parser(lexer, parse_include)
    return parser.parse()


# 便捷函数
def load_config(file_path: str) -> Config:
    """加载配置文件"""
    return parse_file(file_path)


def save_config(config: Config, style: Style = INDENTED_STYLE) -> None:
    """保存配置文件"""
    write_config(config, style)


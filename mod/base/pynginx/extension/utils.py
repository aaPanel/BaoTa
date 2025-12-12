from dataclasses import dataclass
from typing import Union

from .. import *


# 用于按条件查找块内的指令的索引，并支持从某个索引位置开始插入指令
class _IndexBlockTools:
    @dataclass
    class OpL:  # 查找第一个指令
        directive: str = ""
        offset: int = 0
        parameter: str = ""
        comment: str = ""
        remove_comment: bool = False

    class OpR(OpL):  # 查找最后一个指令
        pass

    def __init__(self):
        self._block: Union[Block, Http, Config, Upstream] = Block()

    def find_index(self, *ops: Union[OpL, OpR], default: int = -1) -> int:
        directives = self._block.get_directives()
        if self._block.__class__ is Http:
            directives = self._block.directives
            ops = [op for op in ops if op.directive != "server"]
        elif self._block.__class__ is Upstream:
            directives = self._block.directives
            ops = [op for op in ops if op.directive != "server"]

        for op in ops:
            target_idx = -1
            for i, directive in enumerate(directives):
                if op.directive and op.directive == directive.get_name() and (
                        op.parameter == "" or any(op.parameter in p for p in directive.get_parameters())
                ):
                    target_idx = i
                    if type(op) is self.OpL:
                        return target_idx + op.offset

                elif op.comment:
                    comments = directive.get_comment()
                    for c_dix, comment in enumerate(comments[::-1]):
                        if op.comment in comment:
                            if op.remove_comment:
                                comments.pop(0 - c_dix - 1)
                                directive.set_comment(comments)
                            target_idx = i
                            if type(op) is self.OpL:
                                return target_idx + op.offset
            if target_idx >= 0:
                return target_idx + op.offset
        return default

    def insert_after(self, idx: int, *directives: IDirective):
        cls = type(self._block)
        if cls in (Block, Config):
            self._block.directives = self._block.directives[:idx] + list(directives) + self._block.directives[idx:]
        elif cls is Http:
            srv_list, dir_list = [], []
            for directive in directives:
                if directive.__class__ is Server:
                    srv_list.append(directive)
                else:
                    dir_list.append(directive)
            self._block.servers.extend(srv_list)
            self._block.directives = self._block.directives[:idx] + list(dir_list) + self._block.directives[idx:]
        elif cls is Upstream:
            srv_list, dir_list = [], []
            for directive in directives:
                if directive.__class__ is UpstreamServer:
                    srv_list.append(directive)
                else:
                    dir_list.append(directive)
            self._block.servers.extend(srv_list)
            self._block.directives = self._block.directives[:idx] + dir_list + self._block.directives[idx:]

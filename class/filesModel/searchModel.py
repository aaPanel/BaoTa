#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

#
#------------------------------

import os
import re
import time
import json
import sys
import threading
import traceback
import stat
import simple_websocket
from multiprocessing import SimpleQueue, Process, connection
from typing import Tuple

from filesModel.base import filesBase
import public


class main(filesBase):

    __s_class = []

    def __init__(self):
        for i in range(1, 100):
            self.__s_class.append('f-s-%s' % i)

    def get_search_status(self, ws_get):
        """
        @name 验证是否可用
        """
        return public.returnMsg(True, '1')

    # 检查文件名
    @classmethod
    def __check_filename(cls,
                         file_name: str,
                         search_name: str,
                         is_regular: bool = False,  # 0 为普通模式  1 为正则模式  2 为替换
                         is_word: bool = False,  # 1 全词匹配  0  默认
                         is_case: bool = False,  # 1 区分大小写 0 默认
                         ) -> Tuple[bool, str]:
        search_name_tag = '<span style="color:#000;background:yellow">{}</span>'
        search_len = len(search_name)
        if is_word is True and is_regular is True:  # 全词模式-正则
            search_name = search_name.replace("\b", r"\b")
            if not search_name.startswith(r"\b"):
                search_name = r"\b" + search_name
            if not search_name.endswith(r"\b"):
                search_name = search_name + r"\b"

        search_flags = re.IGNORECASE
        if is_case is True:  # 区分大小写
            search_flags = 0

        new_file_name = ""
        if is_regular is True:  # 正则模式
            num = len(re.findall(search_name, file_name, flags=search_flags))
            new_file_name = re.sub(search_name, search_name_tag.format("\g<0>"), file_name, flags=search_flags)
        else:  # 普通模式
            num = 0

            start_idx = 0
            file_name_len = len(file_name)
            while start_idx < file_name_len:
                end_idx = start_idx + search_len
                if end_idx > file_name_len:
                    new_file_name += file_name[start_idx:]
                    break

                txt = file_name[start_idx:end_idx]
                #  区分大小写                 不区分大小写
                if is_case is True:
                    if txt.lower() != search_name.lower():
                        new_file_name += file_name[start_idx]
                        start_idx += 1
                        continue
                elif txt != search_name:
                    new_file_name += file_name[start_idx]
                    start_idx += 1
                    continue

                if is_word is True:  # 全词模式
                    if start_idx > 0:
                        if re.search(r"\w", file_name[start_idx - 1]):
                            new_file_name += file_name[start_idx]
                            start_idx += 1
                            continue
                    elif end_idx + 1 < file_name_len:
                        if re.search(r"\w", file_name[end_idx + 1]):  # 全词模式
                            new_file_name += file_name[start_idx]
                            start_idx += 1
                            continue

                new_file_name += search_name_tag.format(txt)
                start_idx += search_len
                num += 1
        if num > 0:
            return True, new_file_name
        return False, ""

    # 检查文件后缀
    @classmethod
    def __check_ext(cls, file_name: str, ext_list: list) -> bool:
        if "*" in ext_list:
            return True
        _, ext = os.path.splitext(file_name)
        if "no_ext" in ext_list:
            if len(ext) == 0:
                return True
        if len(ext) > 0:
            if str(ext[1:]).lower() in ext_list:
                return True
        return False

    # 检查文件修改时间
    @classmethod
    def __check_time(cls, path: str, start_time: int, end_time: int) -> bool:
        if not os.path.exists(path):
            return False
        file_mtime = os.path.getmtime(path)
        if file_mtime >= start_time and file_mtime <= end_time:
            return True
        return False

    # 检查文件大小
    @classmethod
    def __check_size(cls, path: str, min_size: int, max_size: int) -> bool:
        if not os.path.exists(path):
            return False
        file_size = os.path.getsize(path)
        if file_size >= min_size and file_size <= max_size:
            return True
        return False

    # 搜索文件内关键词
    @classmethod
    def __search_file_content(cls,
                              file_path: str,  # 文件路径
                              search_content: str,  # 搜索内容
                              is_regular: bool = False,  # 0 为普通模式  1 为正则模式  2 为替换
                              is_word: bool = False,  # 1 全词匹配  0  默认
                              is_case: bool = False,  # 1 区分大小写 0 默认
                              back_zip=None) -> Tuple[list, int]:
        search_content = public.html_encode(search_content)
        resutl = []
        search_num = 0
        if not os.path.exists(file_path):
            return resutl, search_num

        if os.path.getsize(file_path) > 1024 * 1024 * 20:
            return resutl, search_num

        search_content_tag = '<span style="color:#000;background:yellow">{}</span>'
        search_len = len(search_content)
        if is_word is True and is_regular is True:  # 全词模式-正则
            search_content = search_content.replace("\b", r"\b")
            if not search_content.startswith(r"\b"):
                search_content = r"\b" + search_content
            if not search_content.endswith(r"\b"):
                search_content = search_content + r"\b"

        try:
            fp = open(file_path, "r")
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(file_path, "r",encoding="utf-8",errors='ignore')
                except:
                    fp = open(file_path, "r",encoding="GBK",errors='ignore')
            else:
                return resutl, search_num

        search_flags = re.IGNORECASE
        if is_case is True:  # 区分大小写
            search_flags = 0
        try:
            for row_num, line in enumerate(fp, 1):
                line = public.html_encode(line)
                new_line = ""
                if is_regular is True:  # 正则模式
                    num = len(re.findall(search_content, line, flags=search_flags))
                    new_line = re.sub(search_content, search_content_tag.format("\g<0>"), line, flags=search_flags)
                else:  # 普通模式
                    num = 0
                    new_line = ""

                    start_idx = 0
                    line_len = len(line)
                    while start_idx < line_len:
                        end_idx = start_idx + search_len
                        if end_idx > line_len:
                            new_line += line[start_idx:]
                            break

                        txt = line[start_idx:end_idx]

                        if is_case is True: #  区分大小写
                            if txt != search_content:
                                new_line += line[start_idx]
                                start_idx += 1
                                continue
                        elif txt.lower() != search_content.lower(): # 不区分大小写
                            new_line += line[start_idx]
                            start_idx += 1
                            continue

                        if is_word is True: # 全词模式
                            if start_idx > 0:
                                if re.search(r"\w", line[start_idx-1]):
                                    new_line += line[start_idx]
                                    start_idx += 1
                                    continue
                            elif end_idx + 1 < line_len:
                                if re.search(r"\w", line[end_idx+1]): # 全词模式
                                    new_line += line[start_idx]
                                    start_idx += 1
                                    continue

                        new_line += search_content_tag.format(txt)
                        start_idx += search_len
                        num += 1
                if num > 0:
                    search_num += num
                    resutl.append({"row_num": row_num, "search_num": search_num, "line": new_line})
        except Exception as err:
            pass

        if fp and not fp.closed:
            fp.close()
        return resutl, search_num

    # 搜索文件
    @classmethod
    def __search_files(cls, search_data: dict, ws_get=None):
        ws_get._ws.send(public.getJson({
            "type": "files_search",
            "ws_callback": ws_get.ws_callback,
            "result": False,
        }))
            
        for root, _, files in os.walk(search_data["path"]):
            for name in files:
                file_path = os.path.join(root, name)
                html_name = None
                if search_data["search_name"] is not None:
                    flag, html_name = cls.__check_filename(
                        file_name=name,
                        search_name=search_data["search_name"],
                        is_regular=search_data["is_regular"],
                        is_word=search_data["is_word"],
                        is_case=search_data["is_case"])
                    if flag is False:
                        continue
                if cls.__check_ext(name, ext_list=search_data["ext_list"]) is False:
                    continue
                if search_data["start_time"] is not None: # 不限时间
                    if cls.__check_time(file_path, start_time=search_data["start_time"], end_time=search_data["end_time"]) is False:
                        continue
                if search_data["max_size"] is not None:
                    if cls.__check_size(file_path, min_size=search_data["min_size"], max_size=search_data["max_size"]) is False:
                        continue

                if search_data["search_name"] is not None:
                    ws_get._ws.send(public.getJson({
                        "name": name,
                        "path": file_path,
                        "html_path": os.path.join(root, html_name) if html_name is not None else None,
                        "size": os.path.getsize(file_path),
                        "mtime": os.path.getmtime(file_path),
                    }))
                elif search_data["search_content"] is not None:
                    resutl, search_num = cls.__search_file_content(
                        file_path=file_path,
                        search_content=search_data["search_content"],
                        is_regular=search_data["is_regular"],
                        is_word=search_data["is_word"],
                        is_case=search_data["is_case"],
                    )
                    if resutl and search_num != 0:
                        ws_get._ws.send(public.getJson({
                            "name": name,
                            "path": file_path,
                            "search_num": search_num,
                            "search_result": resutl
                        }))
            if search_data["is_subdir"] != 1:  # 不包含子目录
                break

        return True

    # 搜索文件
    def get_search(self, ws_get):
        if not hasattr(ws_get, "_ws"):
            return public.returnMsg(False, "仅支持 websocket 连接！")
        ws: simple_websocket.Server = ws_get._ws
        if not hasattr(ws_get, "path") or not ws_get.path:
            return {'error': '目录不能为空'}
        if not hasattr(ws_get, "search_content") and not hasattr(ws_get, "search_name"):
            return {'error': '搜索信息不能为空'}
        if not hasattr(ws_get, "exts") or not ws_get.exts:
            return {'error': '后缀不能为空；所有文件请输入*.*'}

        if not os.path.isdir(ws_get.path):
            return {'error': '目录不存在'}

        search_data = {
            "search_content": ws_get.search_content if hasattr(ws_get, "search_content") else None, # 搜索内容
            "search_name": ws_get.search_name if hasattr(ws_get, "search_name") else None, # 搜索文件名
            "ext_list": ws_get.exts.split(',') if hasattr(ws_get, "exts") else ["*"], # 搜索后缀
            "path": ws_get.path, # 搜索路径
            "is_subdir": getattr(ws_get, "is_subdir"), # 是否包含子目录
            "is_regular": getattr(ws_get, "is_regular"), # False 为普通模式  True 为正则模式
            "is_case": getattr(ws_get, "is_case"), # True 不区分大小写 False 默认
            "is_word": getattr(ws_get, "is_word"), # True 全词匹配  False  默认
            "start_time": int(ws_get.start_time) if hasattr(ws_get, "start_time") else None, # 开始时间默认为 0
            "end_time": int(ws_get.end_time) if hasattr(ws_get, "end_time") else int(time.time()), # 结束时间
            "min_size": int(ws_get.min_size) if hasattr(ws_get, "min_size") else 0, # 最小文件大小
            "max_size": int(ws_get.max_size) if hasattr(ws_get, "max_size") else None, # 最大文件大小
        }
        public.set_module_logs("search", "get_search")
        try:
            qu = SimpleQueue()
            s = traceback_wrap(SearchByProcess(qu))
            p = Process(target=s, args=(search_data,), daemon=True)
            p.start()

            def read_from_qu():
                while True:
                    data = qu.get()
                    if data is None:
                        break
                    if isinstance(data, str):
                        ws.send(data)

            def watch_conn():
                while True:
                    if not ws.connected:
                        p.kill()
                        qu.put(None)
                        break
                    time.sleep(0.1)

            t = threading.Thread(target=read_from_qu, args=(), daemon=True)
            t2 = threading.Thread(target=watch_conn, args=(), daemon=True)
            t2.start()
            t.start()
            p.join()
            return True
        except Exception as e:
            public.print_log(traceback.format_exc())
        return True


def traceback_wrap(fun):

    def wrap(*args, **kwargs):
        try:
            res = fun(*args, **kwargs)
            public.print_log(res)
            return res
        except Exception as e:
            public.print_log(traceback.format_exc())
            return None
    return wrap

class SearchByProcess(object):

    def __init__(self, pipe: SimpleQueue):
        self.pipe = pipe

    @staticmethod
    def is_regular_file(path):
        try:
            # 获取文件状态信息
            file_stat = os.stat(path)
            if file_stat.st_size == 0:
                return False
            # 判断是否为普通文件 且可以读取
            return stat.S_ISREG(file_stat.st_mode) and os.access(path, os.R_OK)
        except FileNotFoundError:
            # 文件不存在
            return False
        except Exception as e:
            # 处理其他异常，如权限不足等
            print(f"Error checking file: {e}")
            return False

    # 检查文件名
    @classmethod
    def __check_filename(cls,
                         file_name: str,
                         search_name: str,
                         is_regular: bool = False,  # 0 为普通模式  1 为正则模式  2 为替换
                         is_word: bool = False,  # 1 全词匹配  0  默认
                         is_case: bool = False,  # 1 区分大小写 0 默认
                         ) -> Tuple[bool, str]:
        search_name_tag = '<span style="color:#000;background:yellow">{}</span>'
        search_len = len(search_name)
        if is_word is True and is_regular is True:  # 全词模式-正则
            search_name = search_name.replace("\b", r"\b")
            if not search_name.startswith(r"\b"):
                search_name = r"\b" + search_name
            if not search_name.endswith(r"\b"):
                search_name = search_name + r"\b"

        search_flags = re.IGNORECASE
        if is_case is True:  # 区分大小写
            search_flags = 0

        new_file_name = ""
        if is_regular is True:  # 正则模式
            num = len(re.findall(search_name, file_name, flags=search_flags))
            new_file_name = re.sub(search_name, search_name_tag.format("\g<0>"), file_name, flags=search_flags)
        else:  # 普通模式
            num = 0

            start_idx = 0
            file_name_len = len(file_name)
            while start_idx < file_name_len:
                end_idx = start_idx + search_len
                if end_idx > file_name_len:
                    new_file_name += file_name[start_idx:]
                    break

                txt = file_name[start_idx:end_idx]
                #  区分大小写                 不区分大小写
                if is_case is True:
                    if txt.lower() != search_name.lower():
                        new_file_name += file_name[start_idx]
                        start_idx += 1
                        continue
                elif txt != search_name:
                    new_file_name += file_name[start_idx]
                    start_idx += 1
                    continue

                if is_word is True:  # 全词模式
                    if start_idx > 0:
                        if re.search(r"\w", file_name[start_idx - 1]):
                            new_file_name += file_name[start_idx]
                            start_idx += 1
                            continue
                    elif end_idx + 1 < file_name_len:
                        if re.search(r"\w", file_name[end_idx + 1]):  # 全词模式
                            new_file_name += file_name[start_idx]
                            start_idx += 1
                            continue

                new_file_name += search_name_tag.format(txt)
                start_idx += search_len
                num += 1
        if num > 0:
            return True, new_file_name
        return False, ""

    # 检查文件后缀
    @classmethod
    def __check_ext(cls, file_name: str, ext_list: list) -> bool:
        if "*" in ext_list:
            return True
        _, ext = os.path.splitext(file_name)
        if "no_ext" in ext_list:
            if len(ext) == 0:
                return True
        if len(ext) > 0:
            if str(ext[1:]).lower() in ext_list:
                return True
        return False

    # 检查文件修改时间
    @classmethod
    def __check_time(cls, path: str, start_time: int, end_time: int) -> bool:
        if not os.path.exists(path):
            return False
        file_mtime = os.path.getmtime(path)
        if file_mtime >= start_time and file_mtime <= end_time:
            return True
        return False

    # 检查文件大小
    @classmethod
    def __check_size(cls, path: str, min_size: int, max_size: int) -> bool:
        if not os.path.exists(path):
            return False
        file_size = os.path.getsize(path)
        if file_size >= min_size and file_size <= max_size:
            return True
        return False

    # 搜索文件内关键词
    @classmethod
    def __search_file_content(cls,
                              file_path: str,  # 文件路径
                              search_content: str,  # 搜索内容
                              is_regular: bool = False,  # 0 为普通模式  1 为正则模式  2 为替换
                              is_word: bool = False,  # 1 全词匹配  0  默认
                              is_case: bool = False,  # 1 区分大小写 0 默认
                              back_zip=None) -> Tuple[list, int]:

        if not cls.is_regular_file(file_path):
            return [], 0
        search_content = public.html_encode(search_content)
        resutl = []
        search_num = 0
        if not os.path.exists(file_path):
            return resutl, search_num

        if os.path.getsize(file_path) > 1024 * 1024 * 20:
            return resutl, search_num

        search_content_tag = '<span style="color:#000;background:yellow">{}</span>'
        search_len = len(search_content)
        if is_word is True and is_regular is True:  # 全词模式-正则
            search_content = search_content.replace("\b", r"\b")
            if not search_content.startswith(r"\b"):
                search_content = r"\b" + search_content
            if not search_content.endswith(r"\b"):
                search_content = search_content + r"\b"

        stat = os.stat(file_path)
        try:
            fp = open(file_path, "r")
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(file_path, "r", encoding="utf-8", errors='ignore')
                except:
                    fp = open(file_path, "r", encoding="GBK", errors='ignore')
            else:
                return resutl, search_num

        search_flags = re.IGNORECASE
        if is_case is True:  # 区分大小写
            search_flags = 0
        try:
            for row_num, line in enumerate(fp, 1):
                line = public.html_encode(line)
                new_line = ""
                if is_regular is True:  # 正则模式
                    num = len(re.findall(search_content, line, flags=search_flags))
                    new_line = re.sub(search_content, search_content_tag.format("\g<0>"), line, flags=search_flags)
                else:  # 普通模式
                    num = 0
                    new_line = ""

                    start_idx = 0
                    line_len = len(line)
                    while start_idx < line_len:
                        end_idx = start_idx + search_len
                        if end_idx > line_len:
                            new_line += line[start_idx:]
                            break

                        txt = line[start_idx:end_idx]

                        if is_case is True:  # 区分大小写
                            if txt != search_content:
                                new_line += line[start_idx]
                                start_idx += 1
                                continue
                        elif txt.lower() != search_content.lower():  # 不区分大小写
                            new_line += line[start_idx]
                            start_idx += 1
                            continue

                        if is_word is True:  # 全词模式
                            if start_idx > 0:
                                if re.search(r"\w", line[start_idx - 1]):
                                    new_line += line[start_idx]
                                    start_idx += 1
                                    continue
                            elif end_idx + 1 < line_len:
                                if re.search(r"\w", line[end_idx + 1]):  # 全词模式
                                    new_line += line[start_idx]
                                    start_idx += 1
                                    continue

                        new_line += search_content_tag.format(txt)
                        start_idx += search_len
                        num += 1
                if num > 0:
                    search_num += num
                    if search_num > 2000: # 结果数量过多，则跳过剩余部分
                        break
                    resutl.append({"row_num": row_num, "search_num": search_num, "line": new_line})
        except Exception as err:
            pass

        if fp and not fp.closed:
            fp.close()
        return resutl, search_num

    # 搜索文件
    def __call__(self, search_data: dict):
        public.print_log(search_data)
        for root, _, files in os.walk(search_data["path"]):
            for name in files:
                file_path = os.path.join(root, name)
                html_name = None
                if search_data["search_name"] is not None:
                    flag, html_name = self.__check_filename(
                        file_name=name,
                        search_name=search_data["search_name"],
                        is_regular=search_data["is_regular"],
                        is_word=search_data["is_word"],
                        is_case=search_data["is_case"])
                    if flag is False:
                        continue
                if self.__check_ext(name, ext_list=search_data["ext_list"]) is False:
                    continue
                if search_data["start_time"] is not None:  # 不限时间
                    if self.__check_time(file_path, start_time=search_data["start_time"],
                                        end_time=search_data["end_time"]) is False:
                        continue
                if search_data["max_size"] is not None:
                    if self.__check_size(file_path, min_size=search_data["min_size"],
                                        max_size=search_data["max_size"]) is False:
                        continue

                if search_data["search_name"] is not None:
                    self.pipe.put(public.getJson({
                        "name": name,
                        "path": file_path,
                        "html_path": os.path.join(root, html_name) if html_name is not None else None,
                        "size": os.path.getsize(file_path),
                        "mtime": os.path.getmtime(file_path),
                    }))
                elif search_data["search_content"] is not None:
                    result, search_num = self.__search_file_content(
                        file_path=file_path,
                        search_content=search_data["search_content"],
                        is_regular=search_data["is_regular"],
                        is_word=search_data["is_word"],
                        is_case=search_data["is_case"],
                    )
                    if result and search_num != 0:
                        # ！！！ 注意这里非常重要, 发送速度太快会导致面板主进程服务的主线程占用率过高， 无法处理其他请求
                        time.sleep(0.01) # 防占用大量CPU资源
                        self.pipe.put(public.getJson({
                            "name": name,
                            "path": file_path,
                            "search_num": search_num,
                            "search_result": result
                        }))
            if search_data["is_subdir"] != 1:  # 不包含子目录
                break

        self.pipe.put(None)
        return True

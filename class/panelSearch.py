# coding: utf-8
# +-------------------------------------------------------------------
# | version :1.0
# +-------------------------------------------------------------------
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
# | 快速检索
# +--------------------------------------------------------------------

import os
import re
import zipfile
import time
import sys
import json
import db
from typing import Tuple, Union

import public


class panelSearch:
    __BACKUP_PATH = '/www/server/panel/backup/panel_search/'

    def __init__(self):
        pass

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
            # 2024/2/18 下午 6:16 尝试获取文件编码，无异常则直接使用utf-8编码打开文件
            with open(file_path, 'r', encoding='utf-8') as fp:
                for row_num, line in enumerate(fp, 1):
                    break

            fp = open(file_path, 'r', encoding='utf-8')
        except:
            encodings_to_try = ['gbk', 'big5', 'utf-16']
            for encoding in encodings_to_try:
                try:
                    fp = open(file_path, 'r', encoding=encoding)
                    break
                except:
                    pass

            # if sys.version_info[0] != 2:
            #     try:
            #         fp = open(file_path, "r")
            #     except:
            #         fp = open(file_path, "r",encoding="GBK",errors='ignore')
            # else:
            #     return resutl, search_num

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

                        if is_word is True: # 全词模式
                            if start_idx > 0:
                                if re.search(r"\w", line[start_idx-1]):
                                    new_line += line[start_idx]
                                    start_idx += 1
                                    continue
                            if end_idx < line_len:
                                if re.search(r"\w", line[end_idx]): # 全词模式
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

    # 文件内容替换
    @classmethod
    def __replace_file_content(cls,
                               file_path: str,  # 文件路径
                               search_content: str,  # 搜索内容
                               replace: str,  # 替换内容
                               is_regular: bool = False,  # 0 为普通模式  1 为正则模式  2 为替换
                               is_word: bool = False,  # 1 全词匹配  0  默认
                               is_case: bool = False,  # 1 区分大小写 0 默认
                               backup_zip=None) -> int:
        search_content = public.html_encode(search_content)
        replace_num = 0
        if not os.path.exists(file_path):
            return replace_num

        if os.path.getsize(file_path) > 1024 * 1024 * 20:
            return replace_num

        search_len = len(search_content)
        if is_word is True and is_regular is True:  # 全词模式-正则
            search_content = search_content.replace("\b", r"\b")
            if not search_content.startswith(r"\b"):
                search_content = r"\b" + search_content
            if not search_content.endswith(r"\b"):
                search_content = search_content + r"\b"

        try:
            fp = open(file_path, 'r', encoding='UTF-8')
        except:
            fp = open(file_path, 'r')
        content = fp.read()
        fp.close()
        content = public.html_encode(content)

        search_flags = re.IGNORECASE
        if is_case is True:  # 区分大小写
            search_flags = 0
        if is_regular is True:  # 正则模式
            replace_num = len(re.findall(search_content, content, flags=search_flags))
            content = re.sub(search_content, replace, content, flags=search_flags)
        else:  # 普通模式
            replace_num = 0
            new_content = ""

            start_idx = 0
            line_len = len(content)
            while start_idx < line_len:
                end_idx = start_idx + search_len
                if end_idx > line_len:
                    new_content += content[start_idx:]
                    break

                txt = content[start_idx:end_idx]
                if is_case is True:  # 区分大小写
                    if txt != search_content:
                        new_content += content[start_idx]
                        start_idx += 1
                        continue
                elif txt.lower() != search_content.lower():  # 不区分大小写
                    new_content += content[start_idx]
                    start_idx += 1
                    continue

                if is_word is True: # 全词模式
                    if start_idx > 0:
                        if re.search(r"\w", content[start_idx-1]):
                            new_content += content[start_idx]
                            start_idx += 1
                            continue
                    elif end_idx + 1 < line_len:
                        if re.search(r"\w", content[end_idx+1]): # 全词模式
                            new_content += content[start_idx]
                            start_idx += 1
                            continue

                new_content += replace
                start_idx += search_len
                replace_num += 1
            content = new_content

        if backup_zip is not None: # 添加到压缩文件
            bf = file_path.strip('/')
            backup_zip.write(file_path, bf)

        with open(file_path, 'w') as f:
            f.write(content)
            f.close()
        return replace_num

    # 搜索文件
    @classmethod
    def __search_files(cls, search_data: dict, ws_get=None):
        # ws_get._ws.send(public.getJson({
        #     "type": "files_search",
        #     "ws_callback": ws_get.ws_callback,
        #     "result": False,
        # }))
        
        # 获取总文件数
        total_files = sum([len(files) for _, _, files in os.walk(search_data["path"])])
        searched_files = 0  # 初始化已搜索文件数

        for root, _, files in os.walk(search_data["path"]):
            for name in files:
                file_path = os.path.join(root, name)
                searched_files += 1 
                # 计算进度百分比
                progress_percentage = (searched_files / total_files) * 100
                if cls.__check_ext(name, ext_list=search_data["ext_list"]) is False:
                    continue
                    
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
                        "search_result": resutl,
                        "progress": f"{progress_percentage:.2f}%",  # 格式化为两位小数的百分比
                        
                    }))
            if search_data["is_subdir"] != 1:  # 不包含子目录
                break                
        return True

    # 文件内容替换
    @classmethod
    def __replace_files(cls, replace_data: dict, ws_get=None):
        replace_num = 0
        zfile = None
        if replace_data["is_backup"] is True:
            t = time.strftime('%Y%m%d%H%M%S')
            backup_zip_path = os.path.join(cls.__BACKUP_PATH, "%s.zip" % t)
            zfile = zipfile.ZipFile(backup_zip_path, "w", compression=zipfile.ZIP_DEFLATED)        
        
        ws_get._ws.send(public.getJson({
            "type": "files_search",
            "ws_callback": ws_get.ws_callback,
            "end": False,
        }))
        for root, _, files in os.walk(replace_data["path"]):
            for name in files:
                file_path = os.path.join(root, name)

                if cls.__check_ext(name, ext_list=replace_data["ext_list"]) is False:
                    continue
                num = cls.__replace_file_content(
                    file_path=file_path,
                    search_content=replace_data["search_data"],
                    replace=replace_data["replace"],
                    is_regular=replace_data["is_regular"],
                    is_word=replace_data["is_word"],
                    is_case=replace_data["is_case"],
                    backup_zip=zfile,
                )
                if num != 0:
                    ws_get._ws.send(public.getJson({
                        "name": name,
                        "path": file_path,
                        "search_num": num,
                    }))
                    replace_num += num
                    
            if replace_data["is_subdir"] != 1:  # 不包含子目录
                break              

        if zfile is not None:
            zfile.close()
        return replace_num

    # 搜索文件内容
    def get_search(self, ws_get):
        if not hasattr(ws_get, "_ws"):
            return public.returnMsg(False, "仅支持 websocket 连接！")
        if not hasattr(ws_get, "path") or not ws_get.path:
            return {'error': '目录不能为空'}
        if not hasattr(ws_get, "search_content") or not ws_get.search_content:
            return {'error': '搜索信息不能为空'}
        if not hasattr(ws_get, "exts") or not ws_get.exts:
            return {'error': '后缀不能为空；所有文件请输入*.*'}

        if not os.path.isdir(ws_get.path):
            return {'error': '目录不存在'}

        search_data = {
            "search_content": getattr(ws_get, "search_content"),  # 搜索内容
            "ext_list": ws_get.exts.split(',') if hasattr(ws_get, "exts") else ["*"],  # 搜索后缀
            "path": ws_get.path,  # 搜索路径
            "is_subdir": getattr(ws_get, "is_subdir", False),  # 是否包含子目录
            "is_regular": getattr(ws_get, "is_regular", False),  # False 为普通模式  True 为正则模式
            "is_case": getattr(ws_get, "is_case", False),  # True 不区分大小写 False 默认
            "is_word": getattr(ws_get, "is_word", False),  # True 全词匹配  False  默认
        }
        return self.__search_files(search_data=search_data, ws_get=ws_get)

    # 替换
    def get_replace(self, ws_get):
        if not hasattr(ws_get, "_ws"):
            return public.returnMsg(False, "仅支持 websocket 连接！")
        if not hasattr(ws_get, "path") or not ws_get.path:
            return {'error': '目录不能为空'}
        if not hasattr(ws_get, "search_content") or not ws_get.search_content:
            return {'error': '搜索信息不能为空'}
        if not hasattr(ws_get, "replace") or not ws_get.replace:
            return {'error': '替换信息不能为空'}
        if not hasattr(ws_get, "exts") or not ws_get.exts:
            return {'error': '后缀不能为空；所有文件请输入*.*'}

        if not os.path.isdir(ws_get.path):
            return {'error': '目录不存在'}

        replace_data = {
            "search_content": getattr(ws_get, "search_content"),  # 搜索内容
            "replace": getattr(ws_get, "replace"),  # 搜索内容
            "ext_list": ws_get.exts.split(',') if hasattr(ws_get, "exts") else ["*"],  # 搜索后缀
            "path": ws_get.path,  # 搜索路径
            "is_subdir": ws_get.is_subdir == "true" if hasattr(ws_get, "is_subdir") else False,  # 是否包含子目录
            "is_regular": ws_get.is_regular == "true" if hasattr(ws_get, "is_regular") else False,  # False 为普通模式  True 为正则模式
            "is_case": ws_get.is_case == "true" if hasattr(ws_get, "is_case") else False,  # True 不区分大小写 False 默认
            "is_word": ws_get.is_word == "true" if hasattr(ws_get, "is_word") else False,  # True 全词匹配  False  默认
            "is_backup": ws_get.is_backup == "true" if hasattr(ws_get, "is_backup") else False,  # True 备份  False  默认
        }

        return self.__replace_files(replace_data=replace_data, ws_get=ws_get)

    # 替換日志
    def get_replace_logs(self, get):
        import page
        page = page.Page()
        count = public.M('panel_search_log').order('id desc').count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('panel_search_log').field(
            'id,rtext,exts,path,mode,isword,iscase,noword,backup_path,time'
        ).order('id desc').limit(str(page.SHIFT) + ',' +
                                 str(page.ROW)).select()
        if isinstance(data['data'], str): return public.returnMsg(False, [])
        for i in data['data']:
            if not isinstance(i, dict): continue
            if 'backup_path' in i:
                path = i['backup_path']
                if os.path.exists(path):
                    i['is_path_status'] = True
                else:
                    i['is_path_status'] = False
        return public.returnMsg(True, data)

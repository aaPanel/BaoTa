#coding: utf-8
import os,sys,time,json
panelPath = os.getenv('BT_PANEL')
if not panelPath:
    panelPath = "/www/server/panel"
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
import public,re

class logsBase:

    def __init__(self):
        pass


    def find_line_str(self,_line,search):
        """
        @name 查找字符串
        """
        if search:
            if _line.lower().find(search.lower()) != -1:
                return True
        else:
            return True
        return False


    def return_line_area(self,logs_list,ip_list):
        """
        @name 日志行返回归属地
        """
        if len(logs_list) <= 0: return logs_list
        n_data = '\r\n'.join(logs_list)
        res = public.get_ips_area(ip_list)
        for ip in ip_list:
            area = '未知归属地'
            if 'status' in res:
                area = '****（开通企业版可查看）'
            elif ip in res:
                area = res[ip]['info']
            n_data = n_data.replace(ip,'{}({})'.format(ip,area))
        log_list = n_data.split('\r\n')
        return log_list

    def GetNumLines(self,path, num, p=1,search = None):
        """
        @name 取文件指定尾行数
        @param path 文件路径
        @param num 取尾行数
        @param p 当前页
        @param search 搜索关键字
        @return list
        """
        pyVersion = sys.version_info[0]
        max_len = 1024 * 128 * 1024
        try:
            from html import escape
            if not os.path.exists(path): return ""
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')

            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            total_len = 0
            b = True
            n = 0

            for i in range(count):
                while True:
                    newline_pos = str.rfind(str(buf), "\n")

                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]

                            is_res = True
                            if search:
                                is_res = False
                                if line.find(search) >= 0 or re.search(search,line):
                                    is_res = True

                            if is_res:
                                line_len = len(line)
                                total_len += line_len
                                sp_len = total_len - max_len
                                if sp_len > 0:
                                    line = line[sp_len:]
                                try:
                                    data.insert(0, escape(line))
                                except:
                                    pass
                        buf = buf[:newline_pos]
                        n += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pyVersion == 3:
                            try:
                                if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8',errors='ignore')
                            except:
                                try:
                                    if type(t_buf) == bytes: t_buf = t_buf.decode('gbk',errors='ignore')
                                except:
                                    t_buf = str(t_buf)
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                    if total_len >= max_len: break
                if not b: break
            fp.close()
            result = "\n".join(data)

            if not result: raise Exception('null')
        except:
            result = ''
            if len(result) > max_len:
                result = result[-max_len:]

        try:
            try:
                result = json.dumps(result)
                return json.loads(result).strip()
            except:
                if pyVersion == 2:
                    result = result.decode('utf8', errors='ignore')
                else:
                    result = result.encode('utf-8', errors='ignore').decode("utf-8", errors="ignore")
            return result.strip()
        except:
            return ""
#!/usr/bin/python
# coding: utf-8
# Date 2025/11/04
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wpl <wpl@bt.cn>
# 网站安全基础扫描模块
# -------------------------------------------------------------------
import re
import sys, json, os, public, hashlib, requests, time
from BTPanel import cache
import PluginLoader


class main:
    __count = 0
    __shell = "/www/server/panel/data/webbasic_shell_check.txt"
    session = requests.Session()
    send_time = ""  # 记录上一次发送ws时间
    web_name = ""  # 当前检测的网站名
    scan_type = "basicvulscan"
    web_scan_num = 0
    bar = 0
    # 新增：全局进度属性，按站点×模块综合计算
    _total_units = 0
    _done_units = 0
    _module_count_per_site = 0
    # 新增：标记是否处于全站扫描上下文，避免跨次扫描累加
    _in_all_scan = False
    # 添加计数器
    risk_count = {
        "warning": 0,  # 告警（0）
        "low": 0,  # 低危 (1)
        "middle": 0,  # 中危 (2)
        "high": 0  # 高危 (3)
    }
    web_count_list = []

    def GetWebInfo(self, get):
        '''
        @name 获取网站信息
        @author wpl<2025-11-4>
        @param name  网站名称
        @return dict 网站信息
        '''
        webinfo = public.M('sites').where('project_type=? and name=?', ('PHP', get.name)).count()
        if not webinfo: return False
        webinfo = public.M('sites').where('project_type=? and name=?', ('PHP', get.name)).select()
        return webinfo[0]

    def GetAllSite(self, get):
        '''
        @name 获取所有网站信息
        @author wpl<2025-11-4>
        @return list 所有网站信息
        '''
        webinfo = public.M('sites').where('project_type=?', ('PHP',)).select()
        return webinfo

    def WebConfigSecurity(self, webinfo, get):
        '''
        @name 网站配置安全性检测
        @author wpl<2025-11-4>
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "正在扫描 %s 网站配置安全性" % get.name,
                "type": "webscan",
                "bar": self.bar
            }))
        
        result = []
        
        # Nginx版本泄露检测
        if public.get_webserver() == 'nginx':
            nginx_path = '/www/server/nginx/conf/nginx.conf'
            if os.path.exists(nginx_path):
                nginx_info = public.ReadFile(nginx_path)
                if not 'server_tokens off' in nginx_info:
                    result.append({
                        "name": "%s网站存在Nginx版本信息泄露" % get.name,
                        "info": "Nginx版本信息泄露可能会暴露服务器的敏感信息，导致安全风险",
                        "repair": "打开 %s 网站的nginx.conf配置文件，在http { }里加上： server_tokens off;" % get.name,
                        "dangerous": 1, 
                        "type": "webscan"
                    })

        # PHP版本泄露检测
        phpversion = public.get_site_php_version(get.name)
        phpini = '/www/server/php/%s/etc/php.ini' % phpversion
        if os.path.exists(phpini):
            php_info = public.ReadFile(phpini)
            if not 'expose_php = Off' in php_info:
                result.append({
                    "name": "%s网站存在PHP版本信息泄露" % get.name,
                    "info": "PHP版本信息泄露可能会暴露服务器的敏感信息，导致安全风险",
                    "repair": "打开 %s 网站的php.ini配置文件，设置expose_php = Off" % get.name, 
                    "dangerous": 1, "type": "webscan"
                })

        # 防火墙检测
        if not os.path.exists("/www/server/btwaf/"):
            result.append({
                "name": "%s网站未安装防火墙" % get.name,
                "info": "未安装防火墙可能会暴露服务器的敏感信息，导致安全风险",
                "repair": "安装或者开启nginx防火墙", 
                "dangerous": 0, "type": "webscan"
            })

        # 防跨站攻击检测
        web_infos = public.M('sites').where("name=?", (get.name, )).select()
        for web in web_infos:
            run_path = self.GetSiteRunPath(web["name"], web["path"])
            if not run_path:
                continue
            path = web["path"] + run_path
            user_ini_file = path + '/.user.ini'
            
            if not os.path.exists(user_ini_file):
                continue
            user_ini_conf = public.readFile(user_ini_file)
            if "open_basedir" not in user_ini_conf:
                result.append({
                    "name": "%s网站未开启防跨站攻击" % get.name,
                    "info": "未开启防跨站攻击可能会暴露服务器的敏感信息，导致安全风险",
                    "repair": "网站目录-启用防跨站攻击(open_basedir)，防止黑客通过跨越目录读取敏感数据",
                    "dangerous": 0, "type": "webscan"
                })

        # SSL证书安全性检测
        self.WebSSLSecurity(webinfo, get, result)
        
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "扫描 %s 网站配置安全性完成" % get.name,
                "type": "webscan",
                "results": result,
                "bar": self.bar
            }))

        return result

    def _read_recent_logs(self, log_path, lines=10000):
        """
        读取最近N行日志并进行初步过滤
        @param log_path 日志文件路径
        @param lines 读取行数
        @return 过滤后的日志内容
        """
        try:
            # 只读取状态码为200,301,302,403,404,500的请求，过滤掉静态资源请求
            cmd = f"tail -n {lines} '{log_path}' | grep -E ' (200|301|302|403|404|500) ' | grep -v -E '\\.(css|js|png|jpg|jpeg|gif|ico|woff|woff2|ttf|svg)( |\\?|$)'"
            result = public.ExecShell(cmd)[0]
            # 过滤掉空行
            result = [line for line in result.split('\n') if line.strip()]
            # public.print_log(f"过滤后的日志内容，共{len(result)}行")
            return result
        except Exception as e:
            # 如果grep失败，直接读取原始日志
            cmd = f"tail -n {lines} '{log_path}'"
            return public.ExecShell(cmd)[0]

    def _analyze_attack_distribution(self, log_content, security_patterns):
        """
        分析各类攻击的数量和分布
        @param log_content 日志内容
        @param security_patterns 安全检测规则
        @return 攻击统计信息
        """
        attack_stats = {}
        
        for attack_type, pattern_info in security_patterns.items():
            attack_stats[attack_type] = {
                'count': 0,
                'sample_ips': [],
                'sample_urls': []
            }
            
            for line in log_content.split('\n'):
                if line.strip():
                    line_lower = line.lower()
                    # 检查是否包含攻击模式
                    for pattern in pattern_info['patterns']:
                        if pattern.lower() in line_lower:
                            attack_stats[attack_type]['count'] += 1
                            
                            # 提取IP地址
                            try:
                                ip = line.split()[0]
                                if ip not in attack_stats[attack_type]['sample_ips']:
                                    attack_stats[attack_type]['sample_ips'].append(ip)
                            except:
                                pass
                            
                            # 提取URL
                            try:
                                parts = line.split()
                                if len(parts) >= 7:
                                    url = parts[6]
                                    if url not in attack_stats[attack_type]['sample_urls']:
                                        attack_stats[attack_type]['sample_urls'].append(url)
                            except:
                                pass
                            break
        
        return attack_stats

    def _analyze_ip_frequency(self, log_content):
        """
        分析IP访问频率，返回访问次数统计
        @param log_content 日志内容
        @return IP访问频率统计
        """
        ip_stats = {}
        
        for line in log_content.split('\n'):
            if line.strip():
                try:
                    ip = line.split()[0]
                    ip_stats[ip] = ip_stats.get(ip, 0) + 1
                except:
                    continue
        
        # 返回访问次数排序的结果
        return sorted(ip_stats.items(), key=lambda x: x[1], reverse=True)

    def _analyze_url_attacks(self, log_content, security_patterns):
        """
        分析被攻击的URL统计
        @param log_content 日志内容
        @param security_patterns 安全检测规则
        @return 被攻击URL统计
        """
        url_attacks = {}
        
        # 收集所有攻击模式
        all_patterns = []
        for pattern_info in security_patterns.values():
            all_patterns.extend(pattern_info['patterns'])
        
        for line in log_content.split('\n'):
            if line.strip():
                try:
                    parts = line.split()
                    if len(parts) >= 7:
                        url = parts[6]
                        line_lower = line.lower()
                        
                        # 检查是否包含攻击模式
                        for pattern in all_patterns:
                            if pattern.lower() in line_lower:
                                url_attacks[url] = url_attacks.get(url, 0) + 1
                                break
                except:
                    continue
        
        # 返回攻击次数排序的结果
        return sorted(url_attacks.items(), key=lambda x: x[1], reverse=True)

    def WebSSLSecurity(self, webinfo, get, result):
        '''
        @name SSL证书安全性检测
        @author wpl<2025-11-4>
        @param webinfo 网站信息
        @param get 请求参数
        @param result 结果列表
        '''
        if public.get_webserver() == 'nginx':
            conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(webinfo['name'])
            if os.path.exists(conf_file):
                conf_info = public.ReadFile(conf_file)
                keyText = 'ssl_certificate'
                
                if conf_info.find(keyText) == -1:
                    result.append({
                        "name": "%s 网站未启用SSL" % webinfo['name'],
                        "info": "未启用SSL可能会暴露服务器的敏感信息，导致安全风险",
                        "repair": "在网站设置-SSL开启强制https", 
                        "dangerous": 0,
                        "type": "webscan"
                    })
                    
                if 'TLSv1 ' in conf_info:
                    result.append({
                        "name": "%s 网站启用了不安全的TLS1协议" % webinfo['name'],
                        "info": "启用了不安全的TLS1协议可能会暴露服务器的敏感信息，导致安全风险",
                        "repair": "在网站设置，点击高级设置的TLS设置，将TLS1协议禁用", 
                        "dangerous": 2,
                        "type": "webscan"
                    })

    def WebFileLeakDetection(self, webinfo, get):
        '''
        @name 文件泄露检测
        @author wpl<2025-11-4>
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "正在扫描 %s 文件泄露" % get.name,
                "type": "fileleak",
                "bar": self.bar
            }))

        result = []
        site_path = webinfo['path']
        
        # 检测敏感文件
        sensitive_files = ['.env', '.git', '.svn', '.DS_Store']
        
        for filename in sensitive_files:
            file_path = os.path.join(site_path, filename)
            if os.path.exists(file_path):
                result.append({
                    "name": "%s 网站发现敏感文件" % webinfo['name'],
                    "info": "发现敏感文件【%s】可能会暴露服务器的敏感信息，导致安全风险" % filename,
                    "repair": "删除或移动敏感文件到网站根目录外",
                    "dangerous": 2, 
                    "type": "fileleak",
                    "file_path": file_path
                })

        # 检测SQL文件 只检测网站根目录下的SQL文件
        # 只检测网站根目录下的SQL文件
        try:
            files = os.listdir(site_path)
            for file in files:
                if file.endswith('.sql'):
                    file_path = os.path.join(site_path, file)
                    result.append({
                        "name": "%s 网站发现SQL数据库文件" % webinfo['name'],
                        "info": "发现SQL数据库文件【%s】可能会暴露服务器的敏感信息，导致安全风险" % file,
                        "repair": "删除或移动SQL文件到网站根目录外",
                        "dangerous": 3, 
                        "type": "fileleak",
                        "file_path": file_path
                    })
        except Exception as e:
            # 如果无法访问目录，记录错误但不中断扫描
            pass

        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "扫描 %s 文件泄露完成，发现 %d 个问题" % (get.name, len(result)),
                "results": result,
                "type": "fileleak",
                "bar": self.bar
            }))

        return result

    def WebRootTrojanDetection(self, webinfo, get):
        '''
        @name 木马检测
        @author wpl<2025-11-5>
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get:
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback,
                "info": "正在扫描 %s 根目录木马文件" % get.name,
                "type": "webshell",
                "bar": self.bar
            }))

        result = []
        self.__count = 0

        # 仅列出网站根目录中的文件
        base_path = webinfo.get('path') if isinstance(webinfo, dict) else None
        if not base_path or not os.path.isdir(base_path):
            return result
        try:
            entries = os.listdir(base_path)
        except Exception:
            entries = []

        file_list = []
        for name in entries:
            fp = os.path.join(base_path, name)
            # 仅扫描php文件
            if os.path.isfile(fp) and name.lower().endswith('.php'):
                file_list.append(fp)

        if not file_list:
            if '_ws' in get:
                get._ws.send(public.getJson({
                    "end": False, "ws_callback": get.ws_callback,
                    "info": "%s 根目录未发现待扫描文件" % get.name,
                    "type": "webshell",
                    "bar": self.bar
                }))
            return result

        self.__count = len(file_list)
        # 本地正则匹配检测
        rules = [
            "@\\$\\_=", "eval\\(('|\")\\?>", "php_valueauto_append_file", "eval\\(gzinflate\\(",
            "eval\\(str_rot13\\(",
            "base64\\_decode\\(\\$\\_", "eval\\(gzuncompress\\(", "phpjm\\.net", "assert\\(('|\"|\\s*)\\$",
            "require_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "gzinflate\\(base64_decode\\(",
            "echo\\(file_get_contents\\(('|\")\\$_(POST|GET|REQUEST|COOKIE)", "c99shell", "cmd\\.php",
            "call_user_func\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "str_rot13", "webshell", "EgY_SpIdEr",
            "tools88\\.com", "SECFORCE", "eval\\(base64_decode\\(",
            "include\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "array_map[\\s]{0,20}\\(.{1,5}(eval|assert|ass\\\\x65rt).{1,20}\\$_(GET|POST|REQUEST).{0,15}",
            "call_user_func[\\s]{0,25}\\(.{0,25}\\$_(GET|POST|REQUEST).{0,15}",
            "gzdeflate|gzcompress|gzencode",
            "require_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "include_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "call_user_func\\((\"|')assert(\"|')",
            "php_valueauto_prepend_file", "SetHandlerapplication\\/x-httpd-php",
            "fputs\\(fopen\\((.+),('|'\")w('|'\")\\),('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[",
            "file_put_contents\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\],('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\]\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[",
            "require\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "assert\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "eval\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "base64_decode\\(gzuncompress\\(",
            "gzuncompress\\(base64_decode\\(", "ies\",gzuncompress\\(\\$", "eval\\(gzdecode\\(",
            "preg_replace\\(\"\\/\\.\\*\\/e\"", "Scanners", "phpspy", "cha88\\.cn",
            "chr\\((\\d)+\\)\\.chr\\((\\d)+\\)",
            "\\$\\_=\\$\\_", "\\$(\\w)+\\(\\${", "\\(array\\)\\$_(POST|GET|REQUEST|COOKIE)",
            "\\$(\\w)+\\(\"\\/(\\S)+\\/e",
            "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"", "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"", "'e'\\.'v'\\.'a'\\.'l'",
            "@preg\\_replace\\((\")*\\/(\\S)*\\/e(\")*,\\$_POST\\[\\S*\\]", "\\${'\\_'", "@\\$\\_\\(\\$\\_",
            "\\$\\_=\"\""
        ]
        patterns = [re.compile(p, re.IGNORECASE) for p in rules]

        shell_files = []
        for fp in file_list:
            try:
                with open(fp, 'rb') as f:
                    data = f.read()
                try:
                    text = data.decode('utf-8', errors='ignore')
                except Exception:
                    text = data.decode('latin-1', errors='ignore')
                for pat in patterns:
                    if pat.search(text):
                        shell_files.append(fp)
                        break
            except Exception:
                continue

        for shell_file in shell_files:
            result.append({
                "name": "%s 网站根目录发现木马文件" % webinfo.get('name', get.name),
                "info": "发现木马文件【%s】可能会暴露服务器的敏感信息，导致安全风险" % shell_file,
                "repair": "删除木马文件或进行安全检查",
                "dangerous": 3, "type": "webshell",
                "file_path": shell_file
            })

        if '_ws' in get:
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback,
                "info": "扫描 %s 根目录木马文件完成，发现 %d 个木马" % (get.name, len(result)),
                "results": result,
                "type": "webshell",
                "bar": self.bar
            }))

        return result


    def WebBackupFileDetection(self, webinfo, get):
        '''
        @name 备份文件检测
        @author wpl<2025-11-4>
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "正在扫描 %s 备份文件" % get.name,
                "type": "backup",
                "bar": self.bar
            }))

        result = []
        site_path = webinfo['path']
        
        # 备份文件扩展名
        backup_extensions = ['.bak', '.backup', '.old', '.orig', '.tmp', 
                           '.zip', '.rar', '.tar', '.gz', '.7z']

        # 只扫描站点根目录是否存在备份文件（不遍历子目录）
        if os.path.exists(site_path):
            try:
                files = os.listdir(site_path)
                for file in files:
                    file_path = os.path.join(site_path, file)
                    # 只检查文件，跳过目录
                    if os.path.isfile(file_path):
                        file_lower = file.lower()
                        for ext in backup_extensions:
                            if file_lower.endswith(ext):
                                result.append({
                                    "name": "%s 网站发现备份文件" % webinfo['name'],
                                    "info": "发现备份文件【%s】可能会暴露服务器的敏感信息，导致安全风险" % file,
                                    "repair": "删除备份文件或移动到安全位置",
                                    "dangerous": 2, "type": "backup",
                                    "file_path": file_path
                                })
                                break
            except Exception as e:
                # 如果无法访问目录，记录错误但不中断扫描
                pass

        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "扫描 %s 备份文件完成，发现 %d 个备份文件" % (get.name, len(result)),
                "results": result,
                "type": "backup",
                "bar": self.bar
            }))

        return result

    def WebWeakPasswordDetection(self, webinfo, get):
        '''
        @name 弱口令检测（数据库与FTP）
        @author wpl<2025-11-4>
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "正在扫描 %s 弱口令" % get.name,
                "type": "weakpass",
                "bar": self.bar
            }))

        result = []

        # 读取弱口令字典
        weekpassfile = "/www/server/panel/config/weak_pass.txt"
        pass_list = []
        if os.path.exists(weekpassfile):
            try:
                pass_info = public.ReadFile(weekpassfile)
                pass_list = [p.strip() for p in pass_info.split('\n') if p.strip()]
            except:
                pass

        # 获取站点ID
        web_id = None
        try:
            if isinstance(webinfo, dict):
                web_id = webinfo.get('id')

        except:
            web_id = None

        # 数据库弱口令检测
        if pass_list and web_id:
            try:
                database = public.M('databases').where("pid=?", (web_id,)).select()
                if isinstance(database, list):
                    for dbinfo in database:
                        pwd = dbinfo.get('password')
                        if not pwd:
                            continue
                        if pwd in pass_list:
                            dbname = dbinfo.get('name', '')
                            # 密码脱敏
                            if hasattr(self, 'short_passwd'):
                                masked = self.short_passwd(pwd)
                            else:
                                plen = len(pwd)
                                masked = (pwd[:2] + "**" + pwd[-2:]) if plen > 4 else ((pwd[:1] + "****" + pwd[-1]) if 1 < plen <= 4 else "******")
                            result.append({
                                "name": "%s 网站数据库存在弱口令" % webinfo.get('name', ''),
                                "info": "%s 网站数据库【%s】存在弱口令：%s" % (webinfo.get('name', ''), dbname, masked),
                                "repair": "建议在面板数据库修改该用户密码，防止被黑客爆破密码窃取数据",
                                "dangerous": 1, "type": "weakpass"
                            })
            except:
                pass

        # FTP弱口令检测
        if pass_list and web_id:
            try:
                ftps = public.M('ftps').where("pid=?", (web_id,)).select()
                if isinstance(ftps, list):
                    for ftpinfo in ftps:
                        pwd = ftpinfo.get('password')
                        if not pwd:
                            continue
                        if pwd in pass_list:
                            ftpname = ftpinfo.get('name', '')
                            if hasattr(self, 'short_passwd'):
                                masked = self.short_passwd(pwd)
                            else:
                                plen = len(pwd)
                                masked = (pwd[:2] + "**" + pwd[-2:]) if plen > 4 else ((pwd[:1] + "****" + pwd[-1]) if 1 < plen <= 4 else "******")
                            result.append({
                                "name": "%s 网站FTP用户存在弱口令" % webinfo.get('name', ''),
                                "info": "%s 网站FTP用户【%s】存在弱口令：%s" % (webinfo.get('name', ''), ftpname, masked),
                                "repair": "建议修改弱口令，防止被黑客爆破ftp密码篡改网站文件",
                                "dangerous": 2, "type": "weakpass"
                            })
            except:
                pass

        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "扫描 %s 弱口令完成，发现 %d 个问题" % (get.name, len(result)),
                "results": result,
                "type": "weakpass",
                "bar": self.bar
            }))

        return result

    def WebLogDetection(self, webinfo, get):
        '''
        @name 网站日志检测
        @author wpl<2025-11-4> 
        @param webinfo 网站信息
        @param get 请求参数
        @return list 检测结果
        '''
        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "正在扫描 %s 网站日志" % get.name,
                "type": "weblog",
                "bar": self.bar
            }))

        result = []
        
        # 安全检测规则定义
        security_patterns = {
            'xss': {
                'patterns': ['javascript:', 'data:', 'alert(', 'onerror=', 'onload=', 'onclick=',
                           '%3Cscript', '%3Csvg/', '%3Ciframe/', '<script>', '<svg/', '<iframe/',
                           'document.cookie', 'document.location', 'window.location', 'eval(',
                           'expression(', 'vbscript:', 'livescript:', 'mocha:'],
                'name': 'XSS跨站脚本攻击',
                'repair': '1.对用户输入进行HTML编码 2.使用CSP内容安全策略 3.过滤危险标签和属性',
                'risk_level': 2
            },
            'sql_injection': {
                'patterns': ['union select', 'or 1=1', 'and 1=1', 'drop table', 'insert into',
                           'delete from', 'update set', 'exec(', 'execute(', 'sp_', 'xp_',
                           'information_schema', 'mysql.user', 'pg_user', 'sysobjects',
                           'waitfor delay', 'benchmark(', 'sleep(', 'pg_sleep'],
                'name': 'SQL注入攻击',
                'repair': '1.使用参数化查询 2.对输入进行严格验证 3.限制数据库权限 4.使用WAF防护',
                'risk_level': 2
            },
            'file_traversal': {
                'patterns': ['../', '..\\', '/etc/', '/var/', '/usr/', '/root/', '/home/',
                           '.git/', '.svn/', '.env', '.htaccess', '.htpasswd', 'web.config',
                           'wp-config.php', 'database.php', '/proc/', '/dev/',
                           'file://', 'php://filter', 'php://input'],
                'name': '目录遍历/文件包含攻击',
                'repair': '1.验证文件路径 2.使用白名单限制访问 3.禁用危险函数 4.设置适当的文件权限',
                'risk_level': 2
            },
            'php_execution': {
                'patterns': ['eval(', 'system(', 'exec(', 'shell_exec(', 'passthru(',
                           'file_get_contents(', 'file_put_contents(', 'fopen(', 'fwrite(',
                           'phpinfo(', 'base64_decode(', 'gzinflate(', 'str_rot13(',
                           'php://', 'data://', 'expect://', 'phar://', 'assert(',
                           'preg_replace(/.*e', 'create_function('],
                'name': 'PHP代码执行攻击',
                'repair': '1.禁用危险函数 2.严格过滤用户输入 3.使用安全的代码执行方式 4.定期更新PHP版本',
                'risk_level': 2
            },
            'sensitive_files': {
                'patterns': ['.env', '.env.local', '.env.production', 'wp-config.php',
                           'database.php', 'settings.php', '.htaccess', '.htpasswd', 'web.config',
                           'composer.json', 'package.json', '.git/config', 'phpinfo.php',
                           'info.php', 'test.php', 'shell.php', 'webshell.php', 'setup.php', '.DS_Store', 'Thumbs.db'],
                'name': '敏感文件访问尝试',
                'repair': '1.删除或移动敏感文件 2.设置访问权限 3.使用.htaccess限制访问 4.定期检查文件权限',
                'risk_level': 2
            }
        }
        
        # 只检测access.log文件，移除error.log检测
        access_log = '/www/wwwlogs/%s.log' % get.name
        
        # 检测日志文件大小
        if os.path.exists(access_log):
            file_size = os.path.getsize(access_log)
            # 如果日志文件大于500MB，提示清理
            # if file_size > 500 * 1024 * 1024:
            #     result.append({
            #         "name": "访问日志文件过大: %s (%.2fMB)" % (os.path.basename(access_log), file_size/1024/1024),
            #         "repair": "1.配置日志轮转 2.定期清理旧日志 3.压缩历史日志文件",
            #         "dangerous": 1, 
            #         "type": "weblog",
            #         "file_path": access_log
            #     })
            # public.print_log(f"访问日志文件大小: {file_size/1024/1024:.2f}MB")

            
            try:
                # 优化的日志读取策略：只读取最近10000行，并进行初步过滤
                log_content = self._read_recent_logs(access_log, 10000)
                # 输出前10条数据
                # public.print_log(f"前10条日志数据: {log_content[:10]}")

                # 归一化日志内容类型，确保分析函数总是接收到字符串
                if isinstance(log_content, list):
                    normalized_lines = []
                    for line in log_content:
                        if isinstance(line, bytes):
                            try:
                                normalized_lines.append(line.decode('utf-8', errors='ignore'))
                            except Exception:
                                normalized_lines.append(line.decode('latin-1', errors='ignore'))
                        elif isinstance(line, str):
                            normalized_lines.append(line)
                        elif line is None:
                            continue
                        else:
                            # 对于其他类型(如数字/对象)，转为字符串以避免异常
                            normalized_lines.append(str(line))
                    log_content = '\n'.join(normalized_lines)
                elif isinstance(log_content, bytes):
                    try:
                        log_content = log_content.decode('utf-8', errors='ignore')
                    except Exception:
                        log_content = log_content.decode('latin-1', errors='ignore')

                if log_content:
                    # 统计分析
                    # public.print_log(f"开始分析日志内容，共{len(log_content)}行")
                    attack_stats = self._analyze_attack_distribution(log_content, security_patterns)
                    ip_stats = self._analyze_ip_frequency(log_content)
                    # url_stats = self._analyze_url_attacks(log_content, security_patterns) // 统计URL访问排行
                    # public.print_log(f"分析完成，共检测到{sum(stats['count'] for stats in attack_stats.values())}次攻击")
                    
                    # 生成安全检测结果
                    for attack_type, stats in attack_stats.items():
                        if stats['count'] > 0:
                            pattern_info = security_patterns[attack_type]
                            result.append({
                                "name": f"{webinfo['name']} 检测到{pattern_info['name']}",
                                "info": f"检测到{pattern_info['name']}攻击，共{stats['count']}次尝试",
                                "repair": pattern_info['repair'],
                                "dangerous": pattern_info['risk_level'],
                                "type": "weblog",
                                "attack_count": stats['count'],
                                "attack_type": attack_type,
                                "sample_ips": stats['sample_ips'][:5]  # 显示前5个攻击IP
                                # "sample_urls": stats['sample_urls'][:3]  # 显示前3个被攻击URL
                            })
                    
                    # IP Top10
                    if ip_stats:
                        suspicious_ips = [f"{ip}|{count}" for ip, count in ip_stats][:10]
                        if suspicious_ips:
                            # 仅打印日志，不写入result，避免将统计计入问题数
                            # public.print_log(f"可疑IP（Top10）：{suspicious_ips}")
                            # 保留结果但不计入问题数：存入临时属性，供汇总阶段写入meta
                            self._last_weblog_ip_top = suspicious_ips

                    # URL攻击统计
                    # if url_stats:
                    #     result.append({
                    #         "name": f"检测到被攻击的URL ({len(url_stats)}个)",
                    #         "repair": "1.检查相关页面安全性 2.加强输入验证 3.更新相关组件 4.考虑隐藏敏感页面",
                    #         "dangerous": 2,
                    #         "type": "weblog",
                    #         "attacked_urls": url_stats[:10]  # 显示前10个被攻击URL
                    #     })
                        
            except Exception as e:
                result.append({
                    "name": "日志分析过程中出现错误",
                    "repair": f"检查日志文件权限和格式，错误信息：{str(e)}",
                    "dangerous": 1,
                    "type": "weblog"
                })
        else:
            result.append({
                "name": "未找到访问日志文件",
                "repair": "1.检查网站配置 2.确认日志记录已启用 3.检查日志文件路径设置",
                "dangerous": 0,
                "type": "weblog"
            })

        if '_ws' in get: 
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback, 
                "info": "扫描 %s 网站日志完成，发现 %d 个问题" % (get.name, len(result)),
                "type": "weblog",
                "results": result,
                "bar": self.bar
            }))

        return result

    def ScanSingleSite(self, get):
        '''
        @name 单站点扫描
        @author wpl<2025-11-4>
        @param get 请求参数
        @return dict 扫描结果
        '''
        # 记录扫描开始时间用于耗时统计
        self._scan_start_time = time.time()
        # 若不处于全站扫描上下文，重置全局累计风险计数，避免跨次扫描累加
        if not getattr(self, '_in_all_scan', False):
            self.risk_count = {"warning": 0, "low": 0, "middle": 0, "high": 0}
        # 重置当前扫描的风险计数器
        current_risk_count = {"warning": 0, "low": 0, "middle": 0, "high": 0}
        
        # 添加当前网站到扫描列表
        if not hasattr(self, 'web_count_list'):
            self.web_count_list = []
        if get.name not in self.web_count_list:
            self.web_count_list.append(get.name)
        
        webinfo = self.GetWebInfo(get)
        if not webinfo:
            return {'status': False, 'msg': '网站不存在', 'data': None}

        # 初始化结果结构
        scan_result = {
            'site_name': get.name,
            'scan_time': public.format_date(),
            'results': {
                'webscan': [],      # 网站配置安全性
                'fileleak': [],     # 文件泄露检测
                'webshell': [],     # 木马检测
                'backup': [],       # 备份文件
                'weakpass': [],     # 弱口令检测
                'weblog': []        # 网站日志
            },
            'risk_count': current_risk_count,
            'meta': {}
        }

        try:
            # 执行各项检测
            if hasattr(get, 'scan_types'):
                scan_types = get.scan_types if isinstance(get.scan_types, list) else [get.scan_types]
            else:
                scan_types = ['webscan', 'fileleak', 'webshell', 'backup', 'weakpass', 'weblog']
            # 计算当前站点将执行的模块数量（不包含未启用的 webshell）
            base_modules = ['webscan', 'fileleak', 'backup', 'weakpass', 'weblog']
            effective_modules = [m for m in base_modules if m in scan_types]
            _site_total = max(1, len(effective_modules))
            _site_done = 0
            # 网站配置安全性检测
            if 'webscan' in scan_types:
                scan_result['results']['webscan'] = self.WebConfigSecurity(webinfo, get)
                _site_done += 1
                if self._total_units > 0:
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)
                else:
                    self.bar = int((_site_done / _site_total) * 100)
            # 文件泄露检测
            if 'fileleak' in scan_types:
                scan_result['results']['fileleak'] = self.WebFileLeakDetection(webinfo, get)
                _site_done += 1
                if self._total_units > 0:
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)
                else:
                    self.bar = int((_site_done / _site_total) * 100)
            # 木马检测
            # if 'webshell' in scan_types:
            #     scan_result['results']['webshell'] = self.WebTrojanDetection(webinfo, get)
            # 备份文件检测
            if 'backup' in scan_types:
                scan_result['results']['backup'] = self.WebBackupFileDetection(webinfo, get)
                _site_done += 1
                if self._total_units > 0:
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)
                else:
                    self.bar = int((_site_done / _site_total) * 100)
            # 弱口令检测
            if 'weakpass' in scan_types:
                scan_result['results']['weakpass'] = self.WebWeakPasswordDetection(webinfo, get)
                _site_done += 1
                if self._total_units > 0:
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)
                else:
                    self.bar = int((_site_done / _site_total) * 100)
            # 网站日志检测
            if 'weblog' in scan_types:
                # 重置当前站点的IP Top10缓存，避免使用旧值
                self._last_weblog_ip_top = []
                scan_result['results']['weblog'] = self.WebLogDetection(webinfo, get)
                _site_done += 1
                if self._total_units > 0:
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)
                else:
                    self.bar = int((_site_done / _site_total) * 100)
            # 将本次站点的IP Top10写入meta，供全站聚合使用
            if hasattr(self, '_last_weblog_ip_top'):
                scan_result['meta']['weblog_ip_top'] = list(getattr(self, '_last_weblog_ip_top', []))

            for scan_type, results in scan_result['results'].items():
                for result in results:
                    dangerous = result.get('dangerous', 0)
                    if dangerous == 0:
                        current_risk_count['warning'] += 1
                        self.risk_count['warning'] += 1
                    elif dangerous == 1:
                        current_risk_count['low'] += 1
                        self.risk_count['low'] += 1
                    elif dangerous == 2:
                        current_risk_count['middle'] += 1
                        self.risk_count['middle'] += 1
                    elif dangerous == 3:
                        current_risk_count['high'] += 1
                        self.risk_count['high'] += 1

            scan_result['risk_count'] = current_risk_count
            # 评分计算（满分100，最低为0）
            # _warn = min(current_risk_count.get('warning', 0)* 1, 3) 
            # _low = min(current_risk_count.get('low', 0)* 1, 15) 
            # _mid = min(current_risk_count.get('middle', 0)* 2, 40) 
            # _high = min(current_risk_count.get('high', 0)* 5, 80) 
            # _total_deduct = _warn + _low + _mid + _high
            # scan_result['score'] = max(0, 100 - _total_deduct)
            # self._last_score = scan_result['score']

            # 保存扫描结果
            # self.SaveScanResult(scan_result)
            
            # 保存统计结果
            self.save_statistics_result(details=scan_result.get('results', {}))

            # if '_ws' in get: 
            #     get._ws.send(public.getJson({
            #         "end": True, 
            #         "ws_callback": get.ws_callback, 
            #         "info": "网站 %s 基础安全扫描完成" % get.name,
            #         "type": "complete",
            #         "result": scan_result
            #     }))

            return {'status': True, 'msg': '扫描完成', 'data': scan_result}

        except Exception as e:
            if '_ws' in get: 
                get._ws.send(public.getJson({
                    "end": True, "ws_callback": get.ws_callback, 
                    "info": "扫描过程中发生错误: %s" % str(e),
                    "type": "error",
                    "bar": self.bar
                }))
            return {'status': False, 'msg': '扫描失败: %s' % str(e), 'data': None}

    def ScanAllSite(self, get):
        '''
        @name 全站点扫描（按模块执行）
        @author wpl<2025-11-4>
        @param get 请求参数
        @return dict 扫描结果
        '''
        public.set_module_logs('webbasicscanning', 'ScanAllSite', 1)
        # 记录扫描开始时间用于耗时统计
        self._scan_start_time = time.time()
        # 获取全部站点
        sites = self.GetAllSite(get)
        if not sites:
            if '_ws' in get:
                get._ws.send(public.getJson({
                    "end": True, "ws_callback": get.ws_callback,
                    "info": "没有找到PHP网站",
                    "type": "complete",
                    "bar": 100
                }))
            return public.returnMsg(True, '没有找到PHP网站')

        total_sites = len(sites)
        # 固定模块顺序
        modules = ['webscan', 'fileleak', 'webshell', 'backup', 'weakpass', 'weblog']

        # 初始化聚合结构：details 按模块聚合
        aggregated_details = {m: [] for m in modules}
        aggregated_ips = {}  # 用于 weblog 模块的全站 IP Top10 聚合

        # 标记全站扫描上下文，并重置累计风险计数
        self._in_all_scan = True
        self.risk_count = {"warning": 0, "low": 0, "middle": 0, "high": 0}
        # 进度初始化：总任务数 = 站点数 × 模块数
        self._module_count_per_site = len(modules)
        self._total_units = total_sites * self._module_count_per_site
        self._done_units = 0
        self.bar = 0

        # 全局开始提示
        if '_ws' in get:
            get._ws.send(public.getJson({
                "end": False, "ws_callback": get.ws_callback,
                "info": "开始按模块扫描 %d 个网站" % total_sites,
                "type": "start",
                "bar": self.bar
            }))

        # 逐模块遍历所有站点
        for m in modules:
            # 模块开始提示
            if '_ws' in get:
                get._ws.send(public.getJson({
                    "end": False, "ws_callback": get.ws_callback,
                    "info": "开始执行 %s 模块，共 %d 个网站" % (m, total_sites),
                    "type": m,
                    "bar": self.bar
                }))

            for site in sites:
                try:
                    # 设置当前扫描的网站名，并记录到网站计数列表
                    get.name = site['name']
                    if not hasattr(self, 'web_count_list'):
                        self.web_count_list = []
                    if get.name not in self.web_count_list:
                        self.web_count_list.append(get.name)

                    # 获取网站信息
                    webinfo = self.GetWebInfo(get)

                    # 调用对应模块方法
                    if m == 'webscan':
                        result_items = self.WebConfigSecurity(webinfo, get)
                    elif m == 'fileleak':
                        result_items = self.WebFileLeakDetection(webinfo, get)
                    elif m == 'webshell':
                        result_items = self.WebRootTrojanDetection(webinfo, get)
                    elif m == 'backup':
                        result_items = self.WebBackupFileDetection(webinfo, get)
                    elif m == 'weakpass':
                        result_items = self.WebWeakPasswordDetection(webinfo, get)
                    elif m == 'weblog':
                        # 重置当前站点的IP Top10缓存，避免使用旧值
                        self._last_weblog_ip_top = []
                        result_items = self.WebLogDetection(webinfo, get)
                        # 聚合 weblog 的 IP Top10
                        try:
                            for item in getattr(self, '_last_weblog_ip_top', []):
                                if isinstance(item, str) and '|' in item:
                                    ip, cnt = item.split('|', 1)
                                    try:
                                        cnt = int(cnt)
                                    except ValueError:
                                        continue
                                    aggregated_ips[ip] = aggregated_ips.get(ip, 0) + cnt
                        except Exception:
                            pass
                    else:
                        result_items = []

                    # 累计风险计数（按当前模块的结果）
                    for r in result_items:
                        dangerous = r.get('dangerous', 0)
                        if dangerous == 0:
                            self.risk_count['warning'] += 1
                        elif dangerous == 1:
                            self.risk_count['low'] += 1
                        elif dangerous == 2:
                            self.risk_count['middle'] += 1
                        elif dangerous == 3:
                            self.risk_count['high'] += 1

                    # 进度更新（每完成一个站点的一个模块，进度 +1）
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)

                    # 按模块聚合写入详情
                    aggregated_details[m].append({
                        'site_name': get.name,
                        'items': result_items
                    })

                except Exception as e:
                    # 异常也记入详情，避免遗漏
                    aggregated_details[m].append({
                        'site_name': site.get('name'),
                        'error': str(e),
                        'items': []
                    })
                    # 进度也应计入
                    self._done_units += 1
                    self.bar = int((self._done_units / max(1, self._total_units)) * 100)

            # 模块结束提示
            if m == 'weblog' and aggregated_ips:
                # 根据聚合的IP统计生成全站Top10
                sorted_items = sorted(aggregated_ips.items(), key=lambda x: x[1], reverse=True)
                self._last_weblog_ip_top = [f"{ip}|{cnt}" for ip, cnt in sorted_items[:10]]

            if '_ws' in get:
                get._ws.send(public.getJson({
                    "end": False, "ws_callback": get.ws_callback,
                    "info": "%s 模块执行完成" % m,
                    "type": m,
                    "bar": self.bar
                }))

        # 计算全站分数（满分100，最低为0）
        _all_warn = min(self.risk_count.get('warning', 0) * 1, 3)
        _all_low = min(self.risk_count.get('low', 0) * 1, 15)
        _all_mid = min(self.risk_count.get('middle', 0) * 2, 40)
        _all_high = min(self.risk_count.get('high', 0) * 5, 10) # 注意：默认是60，测试站为10分
        _all_total_deduct = _all_warn + _all_low + _all_mid + _all_high
        self._last_all_score = max(0, 100 - _all_total_deduct)
        self._last_score = self._last_all_score

        # 保存统计结果
        self.save_statistics_result(details=aggregated_details)

        # 全局结束提示
        if '_ws' in get:
            get._ws.send(public.getJson({
                "end": True, "ws_callback": get.ws_callback,
                "info": "全站扫描完成，共扫描 %d 个网站" % total_sites,
                "type": "complete",
                "bar": 100
            }))

        # 结束全站扫描上下文
        self._in_all_scan = False
        final_result = {
            'scan_type': 'all_sites_by_module',
            'scan_time': public.format_date(),
            'total_sites': total_sites,
            'results': aggregated_details
        }
        return public.returnMsg(True, '全站扫描完成', final_result)

    def SaveScanResult(self, result, scan_type='single'):
        '''
        @name 保存扫描结果
        @author wpl<2025-11-4>
        @param result 扫描结果
        @param scan_type 扫描类型
        '''
        try:
            result_dir = '/www/server/panel/data/webbasic_scan_results'
            if not os.path.exists(result_dir):
                os.makedirs(result_dir)

            if scan_type == 'single':
                filename = 'webbasic_scan_%s.json' % (result['site_name'])
            else:
                filename = 'webbasic_scan_all_%s.json' % time.strftime('%Y%m%d')

            file_path = os.path.join(result_dir, filename)
            public.writeFile(file_path, json.dumps(result, indent=2, ensure_ascii=False))
            
        except Exception as e:
            public.WriteLog('网站基础安全扫描', '保存扫描结果失败: %s' % str(e))

    def save_statistics_result(self, details=None):
        '''
        @name 保存基础安全扫描统计结果
        @author wpl<2025-11-4>
        @return bool 保存是否成功
        '''
        try:
            # 准备保存目录
            save_path = '/www/server/panel/data/safeCloud'
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            # 计算耗时（单位：秒
            duration_sec = 0
            try:
                if hasattr(self, '_scan_start_time') and isinstance(self._scan_start_time, (int, float)):
                    duration_sec = int(time.time() - self._scan_start_time)
            except Exception:
                duration_sec = 0
            
            # 计算全站攻击类型总和（xss、sql_injection、file_traversal、php_execution、sensitive_files）
            allowed_types = ['xss', 'sql_injection', 'file_traversal', 'php_execution', 'sensitive_files']
            total_attack = {t: 0 for t in allowed_types}
            if isinstance(details, dict):
                weblog_sites = details.get('weblog')
                if isinstance(weblog_sites, list):
                    for site_entry in weblog_sites:
                        if not isinstance(site_entry, dict):
                            continue
                        items = site_entry.get('items', [])
                        for it in items:
                            if not isinstance(it, dict):
                                continue
                            if it.get('type') != 'weblog':
                                continue
                            atype = it.get('attack_type')
                            if atype not in total_attack:
                                continue
                            count = it.get('attack_count', 1)
                            try:
                                total_attack[atype] += int(count)
                            except Exception:
                                total_attack[atype] += 1
            
            # 规整 details：按模块扁平化，仅保留非空 items
            flattened_details = {}
            if isinstance(details, dict):
                for mod_key, entries in details.items():
                    if not isinstance(entries, list):
                        continue
                    flat_items = []
                    for en in entries:
                        if not isinstance(en, dict):
                            continue
                        items = en.get('items')
                        if isinstance(items, list) and items:
                            flat_items.extend([it for it in items if isinstance(it, dict)])
                    if flat_items:
                        flattened_details[mod_key] = flat_items
            elif isinstance(details, list):
                # 当 details 为列表时，按每条 item 的 type 进行归类到模块键
                flat_map = {}
                for en in details:
                    if not isinstance(en, dict):
                        continue
                    items = en.get('items')
                    if isinstance(items, list) and items:
                        for it in items:
                            if not isinstance(it, dict):
                                continue
                            typ = it.get('type')
                            if typ in ['webscan', 'fileleak', 'webshell','backup', 'weakpass', 'weblog']:
                                flat_map.setdefault(typ, []).append(it)
                flattened_details = flat_map
            else:
                flattened_details = {}

            # 固定包含所有模块键，空数据写入空数组
            for m in ['webscan', 'fileleak', 'webshell', 'backup', 'weakpass', 'weblog']:
                if m not in flattened_details:
                    flattened_details[m] = []
            
            # ip_top 仅保存前5个（字符串列表 ip|count）
            ip_top_all = getattr(self, '_last_weblog_ip_top', [])
            ip_top_top5 = list(ip_top_all)[:5] if isinstance(ip_top_all, list) else []
            
            # 准备保存数据
            result_data = {
                'scan_time': public.format_date(),
                'duration': duration_sec,
                'risk_count': {
                    'warning': self.risk_count.get('warning', 0),  # 告警
                    'low': self.risk_count.get('low', 0),          # 低危
                    'middle': self.risk_count.get('middle', 0),    # 中危
                    'high': self.risk_count.get('high', 0)         # 高危
                },
                'web_count': len(self.web_count_list) if hasattr(self, 'web_count_list') else 0,  # 扫描网站总数
                'ip_top': ip_top_top5,  # 全局IP排行（Top5，字符串列表 ip|count）
                'score': getattr(self, '_last_score', 100),  # 最近一次检测分数
                # 保存本次检测的详细结果（模块内为扁平化的 items 列表，并固定模块键）
                'details': flattened_details,
                # 全站攻击类型总和
                'total_attack': total_attack
            }
            
            # 保存到文件
            save_file = os.path.join(save_path, 'webbasic_scan_result.json')
            public.writeFile(save_file, json.dumps(result_data, indent=2, ensure_ascii=False))
            
            # 记录日志
            # public.WriteLog('网站基础安全扫描', '保存统计结果成功: %s' % str(result_data))
            return True
            
        except Exception as e:
            public.WriteLog('网站基础安全扫描', '保存统计结果失败: %s' % str(e))
            return False

    # 读取当前最近一次扫描结果
    def get_scan_result(self, get):
        '''
        @name 获取最近一次扫描结果
        @author wpl<2025-11-4>
        @return dict 最近一次网站安全扫描结果
        '''
        try:
            save_path = '/www/server/panel/data/safeCloud/webbasic_scan_result.json'
            if not os.path.exists(save_path):
                return None
            
            data = json.loads(public.readFile(save_path))

            # 仅保留前5，并转换为字典结构，附带封禁状态
            ip_list = data.get('ip_top', [])
            if isinstance(ip_list, list):
                # 读取IP封禁规则，判断是否封禁
                try:
                    ip_rules = json.loads(public.readFile('data/ssh_deny_ip_rules.json')) or []
                except Exception:
                    ip_rules = []

                transformed = []
                for item in ip_list[:5]:
                    if isinstance(item, dict):
                        ip = str(item.get('ip', '')).strip()
                        # count可能为字符串，统一转为int
                        count_val = item.get('count', 0)
                        try:
                            count = int(count_val)
                        except Exception:
                            count = 0
                    else:
                        # 默认格式 "ip|count"
                        parts = str(item).split('|', 1)
                        ip = parts[0].strip()
                        try:
                            count = int(parts[1]) if len(parts) > 1 else 0
                        except Exception:
                            count = 0

                    transformed.append({
                        'ip': ip,
                        'count': count,
                        'deny_status': 1 if ip in ip_rules else 0
                    })

                data['ip_top'] = transformed

            return data
        except Exception as e:
            public.WriteLog('网站基础安全扫描', '读取最近一次扫描结果失败: %s' % str(e))
            return None
    # 辅助方法
    def GetSiteRunPath(self, siteName, sitePath):
        """
        @name 获取网站运行目录
        @author wpl
        @param string siteName 网站名
        @param string sitePath 网站路径
        """
        if not siteName or os.path.isfile(sitePath):
            return "/"
        path = sitePath
        if public.get_webserver() == 'nginx':
            filename = '/www/server/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*root\s+(.+);'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]
        elif public.get_webserver() == 'apache':
            filename = '/www/server/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]

        if sitePath == path:
            return '/'
        else:
            return path.replace(sitePath, '')

    def GetDirList(self, path_data):
        '''
        @name 获取当前目录下所有PHP文件
        @author wpl<2025-11-4>
        @param path_data 目录路径
        @return list PHP文件列表
        '''
        if os.path.exists(str(path_data)):
            return self.Getdir(path_data)
        else:
            return False

    def Getdir(self, path):
        '''
        @name 获取目录下的所有php文件
        @author wpl<2025-11-4>
        @param path 文件目录
        @return list PHP文件列表
        '''
        return_data = []
        data2 = []
        [[return_data.append(os.path.join(root, file)) for file in files] for root, dirs, files in os.walk(path)]
        for i in return_data:
            if str(i.lower())[-4:] == '.php':
                data2.append(i)
        return data2

    def ReadFile(self, filename, mode='r'):
        '''
        @name 读取文件内容
        @author wpl<2025-11-4>
        @param filename 文件路径
        @param mode 读取模式
        @return 文件内容
        '''
        import os
        if not os.path.exists(filename): return False
        try:
            fp = open(filename, mode)
            f_body = fp.read()
            fp.close()
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(filename, mode, encoding="utf-8")
                    f_body = fp.read()
                    fp.close()
                except Exception as ex2:
                    return False
            else:
                return False
        return f_body

    def FileMd5(self, filename):
        '''
        @name 获取文件的md5值
        @author wpl<2025-11-4>
        @param filename 文件路径
        @return MD5值
        '''
        if os.path.exists(filename):
            with open(filename, 'rb') as fp:
                data = fp.read()
            file_md5 = hashlib.md5(data).hexdigest()
            return file_md5
        else:
            return False

    def UploadShell(self, data, get, webinfo):
        '''
        @name 上传文件进行木马检测
        @author wpl<2025-11-4>
        @param data 文件路径集合
        @param get 请求参数
        @param webinfo 网站信息
        @return 返回webshell路径列表
        '''
        if len(data) == 0: return []
        # 本地正则匹配检测，避免上传到云端
        self.__count = len(data)
        count = 0
        wubao = 0
        shell_data = []
        shell_files = []

        if os.path.exists(self.__shell):
            wubao = 1
            try:
                shell_data = json.loads(public.ReadFile(self.__shell))
            except:
                public.WriteFile(self.__shell, json.dumps([]))
                wubao = 0

        # 正则规则列表
        rules = [
            "@\\$\\_=", "eval\\(('|\")\\?>", "php_valueauto_append_file", "eval\\(gzinflate\\(",
            "eval\\(str_rot13\\(",
            "base64\\_decode\\(\\$\\_", "eval\\(gzuncompress\\(", "phpjm\\.net", "assert\\(('|\"|\\s*)\\$",
            "require_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "gzinflate\\(base64_decode\\(",
            "echo\\(file_get_contents\\(('|\")\\$_(POST|GET|REQUEST|COOKIE)", "c99shell", "cmd\\.php",
            "call_user_func\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "str_rot13", "webshell", "EgY_SpIdEr",
            "tools88\\.com", "SECFORCE", "eval\\(base64_decode\\(",
            "include\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "array_map[\\s]{0,20}\\(.{1,5}(eval|assert|ass\\x65rt).{1,20}\\$_(GET|POST|REQUEST).{0,15}",
            "call_user_func[\\s]{0,25}\\(.{0,25}\\$_(GET|POST|REQUEST).{0,15}",
            "gzdeflate|gzcompress|gzencode",
            "require_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "include_once\\(('|\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "call_user_func\\((\"|')assert(\"|')",
            "php_valueauto_prepend_file", "SetHandlerapplication\\/x-httpd-php",
            "file_put_contents\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\],('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "\\$_(POST|GET|REQUEST|COOKIE)\\[([^\\]]+)\\]\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)\\[",
            "require\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "assert\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)",
            "eval\\(('|'\"|\\s*)\\$_(POST|GET|REQUEST|COOKIE)", "base64_decode\\(gzuncompress\\(",
            "gzuncompress\\(base64_decode\\(", "ies\",gzuncompress\\(\\$", "eval\\(gzdecode\\(",
            "preg_replace\\(\"\\/\\.\\*\\/e\"", "Scanners", "phpspy", "cha88\\.cn",
            "chr\\((\\d)+\\)\\.chr\\((\\d)+\\)",
            "\\$\\_=\\$\\_", "\\$(\\w)+\\(\\${", "\\(array\\)\\$_(POST|GET|REQUEST|COOKIE)",
            "\\$(\\w)+\\(\"\\/(\\S)+\\/e",
            "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"", "\"e\"\\.\"v\"\\.\"a\"\\.\"l\"", "'e'\\.'v'\\.'a'\\.'l'",
            "@preg\\_replace\\((\")*\\/(\\S)*\\/e(\")*,\\$_POST\\[\\S*\\]", "\\${'\\_'", "@\\$\\_\\(\\$\\_",
            "\\$\\_=\"\""
        ]
        patterns = [re.compile(p, re.IGNORECASE) for p in rules]

        for i in data:
            count += 1
            if '_ws' in get:
                get._ws.send(public.getJson({
                    "end": False, "ws_callback": get.ws_callback,
                    "info": "正在扫描文件是否是木马%s" % i,
                    "type": "webshell", "count": self.__count, "is_count": count,
                    "bar": self.bar
                }))

            # 判断是否是误报的文件
            if wubao and i in shell_data:
                continue

            # 本地内容匹配
            try:
                with open(i, 'rb') as f:
                    data_bytes = f.read()
                try:
                    text = data_bytes.decode('utf-8', errors='ignore')
                except Exception:
                    text = data_bytes.decode('latin-1', errors='ignore')

                hit = False
                for pat in patterns:
                    if pat.search(text):
                        hit = True
                        break

                if hit:
                    shell_files.append(i)
                    if '_ws' in get:
                        get._ws.send(public.getJson({
                            "end": False, "ws_callback": get.ws_callback,
                            "info": "%s 网站木马扫描发现当前文件为木马文件" % get.name,
                            "type": "webshell", "count": self.__count, "is_count": count,
                            "is_error": True,
                            "bar": self.bar
                        }))
            except Exception:
                # 文件读取异常直接跳过
                continue

        return shell_files

    def UpdateWubao(self, filename):
        '''
        @name 更新误报文件
        @author wpl<2025-11-4>
        @param filename 误报文件路径
        '''
        if not os.path.exists(self.__shell):
            public.WriteFile(self.__shell, json.dumps([]))
            
        try:
            shell_data = json.loads(public.ReadFile(self.__shell))
            if filename not in shell_data:
                shell_data.append(filename)
                public.WriteFile(self.__shell, json.dumps(shell_data))
            return True
        except:
            return False

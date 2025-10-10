# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <2020-08-04>
# +-------------------------------------------------------------------

import os, sys, json, time, public, datetime


class panelWarning:
    __path = '/www/server/panel/data/warning'
    __ignore = __path + '/ignore'
    __result = __path + '/result'
    __risk = __path + '/risk'
    _vuln_ignore = __path + '/ignore.json'
    _vuln_result = __path + '/result.json'
    __repair_count = __path + '/repair_count.json'
    __vul_list = __path + '/high_risk_vul-9.json'  # 旧漏洞库
    __report = '/www/server/panel/data/warning_report'
    vul_num = 0
    discov_count = 0  # 扫描中发现的漏洞数
    score = 100  # 扫描中动态分数
    yum_time = __path + '/yum_time.pl'
    new_vul_list = __path + '/vul_centos7.json'
    product_version = __path + '/product_version.json'
    __repair_history = __path + '/repair_history.json'  # 修复历史记录

    def __init__(self):
        if not os.path.exists(self.__ignore):
            os.makedirs(self.__ignore, 384)
        if not os.path.exists(self.__result):
            os.makedirs(self.__result, 384)
        if not os.path.exists(self.__risk):
            os.makedirs(self.__risk, 384)
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, 384)
        if not os.path.exists(self.__report):
            os.makedirs(self.__report, 384)

        if not os.path.exists(self._vuln_ignore):
            result = []
            public.WriteFile(self._vuln_ignore, json.dumps(result))
        if not os.path.exists(self._vuln_result):
            result = []
            public.WriteFile(self._vuln_result, json.dumps(result))
        self.new_system_result = []
        # self.sys_version = self.get_sys_version()
        # self.sys_product = self.new_get_sys_product()

    def _get_list(self):
        # 最终输出结果
        self.data = {
            'security': [],
            'risk': [],
            'ignore': [],
            "is_autofix": [],
        }
        # 获取支持一键修复的列表
        try:
            is_autofix = public.read_config("safe_autofix")
        except:
            is_autofix = []
        # 临时扫描结果，中断的时候返回
        self.tmp_data = {
            'security': [],
            'risk': [],
            'ignore': [],
            'is_autofix': is_autofix,
            'check_time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }
        context = {"status": "正在扫描", "percentage": 0, "count": 0, "score": 100}
        public.WriteFile(self.__path + '/bar.txt', json.dumps(context))  # 扫描进度条归零
        bar_num = 0  # 进度条初始化
        bar_limit = 0  # 进度条限制
        self.discov_count = 0  # 扫描中发现漏洞数量初始化
        self.score = 100  # 扫描中分数变化
        sys_version = self.get_sys_version()  # 获取系统版本
        # self.compare_md5()  # 比较漏洞库版本
        self.init_new_vul()  # 初始化漏洞库文件
        # 若漏洞库超过90天，更新漏洞库
        if self.is_file_too_old(self.new_vul_list, 90):
            if os.path.exists(self.new_vul_list):
                os.remove(self.new_vul_list)
        # 下载新版漏洞库文件
        if not self.download_new_vulns():
            sys_version = None
        # redhat系列走新版1接口漏洞扫描
        if sys_version == 'centos_7' or sys_version == 'centos_8' or sys_version == 'centos_8_stream' or sys_version == 'alicloud_3' or sys_version == 'alicloud_2':
            self.new_system_scan()
        # debian系列走新版2接口
        elif sys_version == 'ubuntu_20.04' or sys_version == 'ubuntu_22.04' or sys_version == 'ubuntu_18.04' or sys_version == 'debian_12' or sys_version == 'debian_11' or sys_version == 'debian_10':
            self.new_system_scan2()
        # 旧版本漏洞检测
        # else:
        #     self.system_scan()  # 旧版本系统漏洞扫描
        # 加载安全风险模块
        p = public.get_modules('class/safe_warning')
        for m_name in p.__dict__.keys():
            ignore_file = self.__ignore + '/' + m_name + '.pl'
            # 忽略的检查项
            if p[m_name]._level == 0: continue

            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }
            try:
                m_info['remind'] = p[m_name]._remind
            except:
                pass
            result_file = self.__result + '/' + m_name + '.pl'

            try:
                s_time = time.time()
                m_info['status'], m_info['msg'] = p[m_name].check_run()
                m_info['taking'] = round(time.time() - s_time, 6)
                m_info['check_time'] = int(time.time())
                public.writeFile(result_file, json.dumps(
                    [m_info['status'], m_info['msg'], m_info['check_time'], m_info['taking']], ))
            except:
                continue

            m_info['ignore'] = os.path.exists(ignore_file)
            if m_info['ignore']:
                self.data['ignore'].append(m_info)
                self.tmp_data['ignore'].append(m_info)  # 临时扫描结果
            else:
                if m_info['status']:
                    self.data['security'].append(m_info)
                    self.tmp_data['security'].append(m_info)  # 临时扫描结果
                else:
                    risk_file = self.__risk + '/' + m_name + '.pl'
                    public.writeFile(risk_file, json.dumps(m_info))
                    self.data['risk'].append(m_info)
                    self.tmp_data['risk'].append(m_info)  # 临时扫描结果
                    self.discov_count += 1  # 扫描中发现风险数
                    self.score -= m_info['level']
                    if self.score < 0:
                        self.score = 0

            bar = ("%.2f" % (float(bar_num) / float(len(p.__dict__.keys())) * 50 + 50))
            #  通过进度条限制，防止写文件频繁占用高
            if int(float(bar)) >= bar_limit:
                context = {"status": "{}".format(m_info['title']), "percentage": int(float(bar)),
                           "count": self.discov_count, "score": self.score}
                public.WriteFile(self.__path + '/bar.txt', json.dumps(context))
                self.dump_tmp_result()  # 发现漏洞，先保存一份临时的
                bar_limit += 10
            bar_num += 1
        # 新版漏洞检测无需读文件
        # is_autofix被包含进tmp_data{}字典里，会动态增加
        self.data['is_autofix'] = is_autofix
        # self.data['is_autofix'] += is_autofix

        # if sys_version == 'centos_7' or sys_version == 'ubuntu_20.04' or sys_version == 'ubuntu_22.04' or sys_version == 'ubuntu_18.04' or sys_version == 'debian_12' or sys_version == 'debian_11' or sys_version == 'debian_10':
        #     self.data['is_autofix'] += is_autofix
        # 旧版本漏洞检测
        # else:
        #     vuln_result = self.get_vuln_result()
        #     self.data['risk'] = self.data['risk'] + vuln_result['risk']
        #     self.data['ignore'] = self.data['ignore'] + vuln_result['ignore']
        #     vuln_is_autofix = []
        #     for vr in vuln_result['risk']:
        #         if not vr["reboot"]:
        #             vuln_is_autofix.append(vr["cve_id"])
        #     self.data['is_autofix'] = is_autofix + vuln_is_autofix

        score = 100
        for d in self.data['risk']:
            score = score - d['level']
        if score < 0:
            self.data['score'] = 0
        else:
            self.data['score'] = score
        self.data['risk'] = sorted(self.data['risk'], key=lambda x: x['level'], reverse=True)
        self.data['security'] = sorted(self.data['security'], key=lambda x: x['level'], reverse=True)
        self.data['ignore'] = sorted(self.data['ignore'], key=lambda x: x['level'], reverse=True)
        self.data['check_time'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # 将结果输出一份到报告目录下
        with open("/www/server/panel/data/warning_report/data.json", "w") as f:
            json.dump(self.data, f)
        self.record_times()
        context = {"status": "检测完成", "percentage": 100, "count": self.discov_count, "score": self.score}
        public.WriteFile(self.__path + '/bar.txt', json.dumps(context))
        # public.WriteFile(self.__path + '/bar.txt', "100")  # 扫描进度条归零
        return self.data

    def download_new_vulns(self):
        '''
        根据系统版本确定漏洞库名，并初始化漏洞库名
        @return bool
        '''
        # 生成压缩包名
        try:
            zip_file = os.path.basename(self.new_vul_list).replace(".json", ".zip")
        except Exception as e:
            # public.print_log("报错：{}".format(e))
            return False
        # 检查漏洞库文件是否存在
        if not os.path.exists(self.new_vul_list):
            if zip_file != '':
                downfile = self.__path + '/' + zip_file
                public.downloadFile("{}/safe_warning/{}".format(public.get_url(), zip_file), downfile)
                o, e = public.ExecShell("unzip -o {} -d {}".format(downfile, self.__path))
                # 解压报错
                if e != "":
                    # public.print_log("解压报错：{}".format(e))
                    return False
            else:
                return False
        return True

    def get_list(self, args):
        '''
        @name 开始扫描并返回结果
        @param args:
        @return:
        '''
        import subprocess
        # public.set_module_logs("panelWarning", "get_list")
        public.WriteFile(self.__path + '/kill.pl', "False")  # 用来判断这次的扫描是否被中断，默认没中断
        command = "btpython /www/server/panel/class/panelWarning.py"
        process = subprocess.Popen(command, shell=True)
        # 获取进程ID
        pid = process.pid
        public.WriteFile(self.__path + "/pid.txt", str(pid))
        process.wait()
        result_file = self.__path + '/resultresult.json'
        output = {
            "score": 100,
            "check_time": public.format_date(),
            "interrupt": False,
            "security": [],
            "risk": [],
            "ignore": [],
            "is_autofix": []
        }
        if not os.path.exists(result_file):
            return output
        result_body = public.ReadFile(result_file)
        if not result_body:
            return output
        try:
            output = json.loads(result_body)
        except:
            return output
        # 给前端判断这次的扫描结果是否中断
        if public.ReadFile(self.__path + '/kill.pl') == "True":
            output["interrupt"] = True
        else:
            output["interrupt"] = False
        return output

    def get_result(self, args):
        '''
            @name 获取当前首页风险检测结果
            @return dict
        '''
        result_file = self.__path + '/resultresult.json'
        output = {
            "score": 100,
            "check_time": public.format_date(),
            "interrupt": False,
            "security": [],
            "risk": [],
            "ignore": [],
            "is_autofix": []
        }
        if not os.path.exists(result_file):
            return output
        result_body = public.ReadFile(result_file)
        if not result_body:
            return output
        try:
            output = json.loads(result_body)
        except:
            return output
        return output
        

    def sync_rule(self):
        '''
            @name 从云端同步规则
            @author hwliang<2020-08-05>
            @return void
        '''
        # try:
        #     dep_path = '/www/server/panel/class/safe_warning'
        #     local_version_file = self.__path + '/version.pl'
        #     last_sync_time = local_version_file = self.__path + '/last_sync.pl'
        #     if os.path.exists(dep_path):
        #         if os.path.exists(last_sync_time):
        #             if int(public.readFile(last_sync_time)) > time.time():
        #                 return
        #     else:
        #         if os.path.exists(local_version_file): os.remove(local_version_file)

        #     download_url = public.get_url()
        #     version_url = download_url + '/install/warning/version.txt'
        #     cloud_version = public.httpGet(version_url)
        #     if cloud_version: cloud_version = cloud_version.strip()

        #     local_version = public.readFile(local_version_file)
        #     if local_version:
        #         if cloud_version == local_version:
        #             return

        #     tmp_file = '/tmp/bt_safe_warning.zip'
        #     public.ExecShell('wget -O {} {} -T 5'.format(tmp_file,download_url + '/install/warning/safe_warning.zip'))
        #     if not os.path.exists(tmp_file):
        #         return

        #     if os.path.getsize(tmp_file) < 2129:
        #         os.remove(tmp_file)
        #         return

        #     if not os.path.exists(dep_path):
        #         os.makedirs(dep_path,384)
        #     public.ExecShell("unzip -o {} -d {}/ >/dev/null".format(tmp_file,dep_path))
        #     public.writeFile(local_version_file,cloud_version)
        #     public.writeFile(last_sync_time,str(int(time.time() + 7200)))
        #     if os.path.exists(tmp_file): os.remove(tmp_file)
        #     public.ExecShell("chmod -R 600 {}".format(dep_path))
        # except:
        #     pass

    def set_ignore(self, args):
        '''
            @name 设置指定项忽略状态
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        m_name = args.m_name.strip()
        ignore_file = self.__ignore + '/' + m_name + '.pl'
        if os.path.exists(ignore_file):
            os.remove(ignore_file)
        else:
            public.writeFile(ignore_file, '1')
        return public.returnMsg(True, '设置成功!')

    def set_ignore_list(self, args):
        """
        @name 批量设置指定项忽略状态
        @author lwh<2024-02-22>
        @param dict_obj{
            m_name_list<list> 模块名称列表
        }
        @return dict
        """
        m_name_list = json.loads(args.m_name_list)
        arg = public.dict_obj
        for m_name in m_name_list:
            arg.m_name = m_name
            # public.print_log("忽略对象{}".format(m_name))
            self.set_ignore(arg)
        return public.returnMsg(True, '设置成功!')

    def check_find(self, args):
        '''
            @name 检测指定项
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        try:
            m_name = args.m_name.strip()
            p = public.get_modules('class/safe_warning')
            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }

            # 解决已经在忽略列表中，但是如果仍然需要检查的话可以检查
            ignore_file = self.__ignore + '/' + m_name + '.pl'
            if os.path.exists(ignore_file):
                from cachelib import SimpleCache
                cache = SimpleCache(5000)
                ikey = 'warning_list'
                cache.delete(ikey)
                os.remove(ignore_file)

            result_file = self.__result + '/' + m_name + '.pl'
            s_time = time.time()
            m_info['status'], m_info['msg'] = p[m_name].check_run()
            m_info['taking'] = round(time.time() - s_time, 4)
            m_info['check_time'] = int(time.time())
            public.writeFile(result_file, json.dumps(
                [m_info['status'], m_info['msg'], m_info['check_time'], m_info['taking']]))
            return public.returnMsg(True, '已重新检测')
        except:
            return public.returnMsg(False, '检测失败')

    def system_scan(self):
        '''
        一键扫描系统漏洞（废弃）
        :param get:
        :return: dict
        '''
        self.compare_md5()
        sys_version = self.get_sys_version()

        # if sys_version == 'None':
        #     return public.returnMsg(False, '当前系统暂不支持')
        sys_product = self.get_sys_product()
        # if not os.path.exists(self.__vul_list):
        #     return public.returnMsg(False, "扫描失败")
        vul_list = self.get_vul_list()

        new_risk_list = []
        new_ignore_list = []
        # error_list = []
        result_dict = {}
        # cp_list = []
        vul_count = 0
        ignore_list = self.get_ignore_list()
        reboot_count = 0
        self.vul_num = len(vul_list)
        bar_num = 0  # 进度条初始化
        bar_limit = 0  # 进度条限制
        for vul in vul_list:
            bar = ("%.2f" % (float(bar_num) / float(self.vul_num) * 50))
            # 限制进度条，限制写文件频率
            if int(float(bar)) >= bar_limit:
                context = {"status": "{}".format(vul['cve_id']), "percentage": int(float(bar)),
                           "count": self.discov_count, "score": self.score}
                public.WriteFile(self.__path + '/bar.txt', json.dumps(context))
                self.dump_tmp_result()  # 发现漏洞，先保存一份临时的
                bar_limit += 10
            bar_num += 1
            vul_count += 1
            for v in vul["affected_list"]:
                if v["manufacturer"] == sys_version:
                    tmp = 1  # 默认命中
                    if not 'affected' in v: continue
                    arr = v['affected'].split("Up to (excluding)\n                                                ")
                    if len(arr) < 2: continue
                    vul_version = arr[1]
                    try:
                        for soft in v["softname"]:
                            compare_result = self.version_compare(sys_product[soft], vul_version)
                            if compare_result >= 0:
                                tmp = 0  # 当有一个软件包版本不在漏洞范围内，则不命中
                                break
                        if tmp == 1:
                            # softname_list = [soft+'-'+sys_product[soft] for soft in v["softname"]]
                            # softname_list = [{soft: sys_product[soft]} for soft in v["softname"]]
                            self.discov_count += 1  # 扫描中发现漏洞数
                            softname_dict = {}
                            for soft in v["softname"]:
                                softname_dict[soft] = sys_product[soft]
                            level = self.get_score_risk(vul["score"])
                            vul_dict = {key: vul[key] for key in ["cve_id", "vuln_name", "vuln_time", "vuln_solution"]}
                            vul_dict["level"] = level
                            self.score -= level  # 扫描中的动态分数
                            if self.score < 0:
                                self.score = 0
                            vul_dict["soft_name"] = softname_dict
                            vul_dict["vuln_version"] = vul_version
                            vul_dict["check_time"] = int(time.time())
                            vul_dict["reboot"] = ""
                            if "kernel" in [k for k in v["softname"]]:
                                vul_dict["reboot"] = "该漏洞属于内核漏洞，需要自行升级内核版本，建议升级之前做好快照以及备份\n可联系客服人工处理"
                                reboot_count += 1
                            if vul["cve_id"] in ignore_list:
                                new_ignore_list.append(vul_dict)
                                self.tmp_data['ignore'].append(vul_dict)  # 添加到临时字典
                                break
                            new_risk_list.append(vul_dict)
                            self.tmp_data['risk'].append(vul_dict)  # 添加到临时字典
                            if vul_dict["reboot"]:
                                self.tmp_data['is_autofix'].append(vul_dict["cve_id"])
                            break
                        # cp_list.append(vul["cve_id"]+':    '+str([soft+'-'+sys_product[soft] for soft in v["softname"]])+'  >=  '+vul_version)
                    except Exception as e:
                        # error_list.append(vul["cve_id"]+':    '+str(e))
                        break
            result_dict["vul_count"] = vul_count
        result_dict["risk"] = new_risk_list
        result_dict["ignore"] = new_ignore_list
        # result_dict["reboot"] = self.__need_reboot
        # result_dict["error"] = error_list
        # result_dict["compare"] = cp_list
        public.WriteFile(self.__path + '/system_scan_time', str(int(time.time())))
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        # try:
        #     public.WriteFile(self._vuln_result, json.dumps(result_dict))
        #     return public.returnMsg(True, "扫描完成")
        # except:
        #     return public.returnMsg(False, "扫描失败")

    # 版本比较
    def version_compare(self, ver_a, ver_b):
        '''
        比较版本大小
        :param ver_a: 软件版本
        :param ver_b: 漏洞版本
        :return: int 大于等于返回1或0，小于返回-1
        '''
        sys_version = self.get_sys_version()
        if "ubuntu" in sys_version or "debian" in sys_version:
            if ver_b.startswith("1:"):
                ver_b = ver_b[2:]
            # if ver_a.startswith("1:"):
            #     ver_a = ver_a[2:]
            result = public.ExecShell("dpkg --compare-versions " + ver_a + " ge " + ver_b + " && echo true")
            if 'warning' in result[1].strip(): return None
            if 'true' in result[0].strip():
                return 1
            else:
                return -1
        return self.vercmp(ver_a, ver_b)

    def vercmp(self, first, second):
        import re
        R_NONALNUMTILDE = re.compile(br"^([^a-zA-Z0-9~]*)(.*)$")
        R_NUM = re.compile(br"^([\d]+)(.*)$")
        R_ALPHA = re.compile(br"^([a-zA-Z]+)(.*)$")
        first = first.encode("ascii", "ignore")
        second = second.encode("ascii", "ignore")
        while first or second:
            m1 = R_NONALNUMTILDE.match(first)
            m2 = R_NONALNUMTILDE.match(second)
            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)
            if m1_head or m2_head:
                continue

            if first.startswith(b'~'):
                if not second.startswith(b'~'):
                    return -1
                first, second = first[1:], second[1:]
                continue
            if second.startswith(b'~'):
                return 1

            if not first or not second:
                break

            m1 = R_NUM.match(first)
            if m1:
                m2 = R_NUM.match(second)
                if not m2:
                    return 1
                isnum = True
            else:
                m1 = R_ALPHA.match(first)
                m2 = R_ALPHA.match(second)
                isnum = False

            if not m1:
                return -1
            if not m2:
                return 1 if isnum else -1

            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)

            if isnum:
                m1_head = m1_head.lstrip(b'0')
                m2_head = m2_head.lstrip(b'0')

                m1hlen = len(m1_head)
                m2hlen = len(m2_head)
                if m1hlen < m2hlen:
                    return -1
                if m1hlen > m2hlen:
                    return 1
            if m1_head < m2_head:
                return -1
            if m1_head > m2_head:
                return 1
            continue

        m1len = len(first)
        m2len = len(second)
        if m1len == m2len == 0:
            return 0
        if m1len != 0:
            return 1
        return -1

    # 取系统版本
    def get_sys_version(self):
        '''
        获取当前系统版本
        :return: string
        '''
        sys_version = "None"
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 7" in result:
                sys_version = "centos_7"
            elif "CentOS Linux release 8" in result:
                sys_version = "centos_8"
            elif "CentOS Stream release 8" in result:
                sys_version = "centos_8_stream"
            elif result.find("Alibaba Cloud Linux release 3") != -1:
                sys_version = "alicloud_3"
            elif result.find("Alibaba Cloud Linux (Aliyun Linux) release 2") != -1:
                sys_version = "alicloud_2"
        elif os.path.exists("/etc/lsb-release"):
            if "Ubuntu 20.04" in public.ReadFile("/etc/lsb-release"):
                sys_version = "ubuntu_20.04"
            elif "Ubuntu 22.04" in public.ReadFile("/etc/lsb-release"):
                sys_version = "ubuntu_22.04"
            elif "Ubuntu 18.04" in public.ReadFile("/etc/lsb-release"):
                sys_version = "ubuntu_18.04"
        elif os.path.exists("/etc/debian_version"):
            result = public.ReadFile("/etc/debian_version")
            if "10." in result:
                sys_version = "debian_10"
            elif "11." in result:
                sys_version = "debian_11"
            elif "12." in result:
                sys_version = "debian_12"
        return sys_version

    def new_get_sys_product(self, flag=False):
        '''
        新版获取系统软件包及版本{"name":"version"}
        @param flag bool 为True时直接扫一次
        '''
        # 修复完成需要重新获取一次软件包版本
        if flag:
            sys_product = self.get_sys_product()
            public.WriteFile(self.product_version, json.dumps(sys_product))

        sys_version = self.get_sys_version()
        if sys_version == "centos_7" or sys_version == "alicloud_2":
            # 根据yum日志判断是否用软件包更新
            yumlog = "/var/log/yum.log"
        elif sys_version == "centos_8" or sys_version == "centos_8_stream" or sys_version == "alicloud_3":
            yumlog = "/var/log/dnf.log"
        else:
            yumlog = "/var/log/apt/history.log"
        try:
            # 先判断有没有yum.log
            if os.path.exists(yumlog):
                # 第一次将yum.log修改时间记录在文件里
                if not os.path.exists(self.yum_time):
                    new_modi_time = str(int(os.path.getmtime(yumlog)))
                    public.WriteFile(self.yum_time, new_modi_time)
                    sys_product = self.get_sys_product()
                    public.WriteFile(self.product_version, json.dumps(sys_product))
                else:
                    old_modi_time = public.ReadFile(self.yum_time)
                    new_modi_time = str(int(os.path.getmtime(yumlog)))
                    # 比较上一次记录的时间和这次获取的修改时间，相等则根据rpm文件的修改时间
                    if old_modi_time == new_modi_time:
                        if os.path.exists(self.product_version):
                            # 若rpm文件修改日期大于十四天，则还是执行rpm检测
                            if self.is_file_too_old(self.product_version, 14):
                                sys_product = self.get_sys_product()
                                public.WriteFile(self.product_version, json.dumps(sys_product))
                            else:
                                sys_product = json.loads(public.ReadFile(self.product_version))
                        else:
                            sys_product = self.get_sys_product()
                            public.WriteFile(self.product_version, json.dumps(sys_product))
                    # 不相等证明最近有用yum安装过新软件，更新文件并检测
                    else:
                        sys_product = self.get_sys_product()
                        public.WriteFile(self.product_version, json.dumps(sys_product))  # 将软件包版本写入文件
                        public.WriteFile(self.yum_time, new_modi_time)
            # 没有yum.log，则直接根据rpm文件修改日期
            else:
                if os.path.exists(self.product_version):
                    if self.is_file_too_old(self.product_version, 14):
                        sys_product = self.get_sys_product()
                        public.WriteFile(self.product_version, json.dumps(sys_product))
                    else:
                        sys_product = json.loads(public.ReadFile(self.product_version))
                else:
                    sys_product = self.get_sys_product()
                    public.WriteFile(self.product_version, json.dumps(sys_product))
        except Exception as e:
            sys_product = self.get_sys_product()
            public.WriteFile(self.product_version, json.dumps(sys_product))
        # 其他系统版本
        return sys_product

    # 取软件包版本
    def get_sys_product(self):
        """
        获取系统软件包及版本
        {"name":"version"}
        :return dict 如果系统不支持则返回str None
        """
        product_version = {}
        sys_version = self.get_sys_version()

        # if sys_version == 'None':return public.returnMsg(False,'当前系统暂不支持')
        if "centos" in sys_version:
            result = public.ExecShell('rpm -qa --qf \'%{NAME};%{VERSION}-%{RELEASE}\\n\'')[0].strip().split('\n')
        elif "alicloud" in sys_version:
            result = public.ExecShell('rpm -qa --qf \'%{NAME};%{VERSION}-%{RELEASE}\\n\'')[0].strip().split('\n')
        elif "ubuntu" in sys_version:
            # result1 = subprocess.check_output(['dpkg-query', '-W', '-f=${Package};${Version}\n']).decode('utf-8').strip().split('\n')
            result = public.ExecShell('dpkg-query -W -f=\'${Package};${Version}\n\'')[0].strip().split('\n')
        elif "debian" in sys_version:
            result = public.ExecShell('dpkg-query -W -f=\'${Package};${Version}\n\'')[0].strip().split('\n')
        elif sys_version == "None":
            return None
        else:
            return None
        for pkg in result:
            try:
                product_version[pkg.split(";")[0]] = pkg.split(";")[1]
            except:
                return None
        # product_version["kernel"] = subprocess.check_output(['uname', '-r']).decode('utf-8').strip().replace(".x86_64", "")
        # product_version["kernel"] = public.ExecShell('uname -r')[0].strip()
        return product_version

    def get_vuln_result(self):
        '''
        获取上一次扫描结果
        :param get:
        :return: dict
        '''
        d_risk = 0
        h_risk = 0
        m_risk = 0
        vul_list = []
        if not os.path.exists(self.__vul_list):
            self.vul_num = 0
        else:
            self.vul_num = len(self.get_vul_list())
        if not os.path.exists(self._vuln_result):
            tmp_dict = {"vul_count": self.vul_num, "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict[
                        "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        if public.ReadFile(self._vuln_result) == '[]':
            tmp_dict = {"vul_count": self.vul_num, "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict[
                        "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        result_dict = json.loads(public.ReadFile(self._vuln_result))
        old_risk_list = result_dict["risk"]
        old_ignore_list = result_dict["ignore"]
        new_risk_list = old_risk_list.copy()
        new_ignore_list = old_ignore_list.copy()
        tmp_ignore_list = self.get_ignore_list()
        for cve in old_risk_list:
            if cve["cve_id"] in tmp_ignore_list:
                new_ignore_list.append(cve)
                new_risk_list.remove(cve)
        for cve_ig in old_ignore_list:
            if cve_ig["cve_id"] not in tmp_ignore_list:
                new_risk_list.append(cve_ig)
                new_ignore_list.remove(cve_ig)
        for vul in new_ignore_list + new_risk_list:
            vul_list.append(vul["cve_id"])
            if vul["cve_id"] in tmp_ignore_list:
                continue
            if vul["level"] == 3:
                d_risk += 1
            elif vul["level"] == 2:
                h_risk += 1
            elif vul["level"] == 1:
                m_risk += 1
        list_sort = [3, 2, 1]  # 排序列表
        # result_dict["risk"] = old_risk_list
        result_dict["risk"] = sorted(new_risk_list, key=lambda x: list_sort.index(x.get("level")))
        # result_dict["ignore"] = old_ignore_list
        result_dict["ignore"] = sorted(new_ignore_list, key=lambda x: list_sort.index(x.get("level")))
        # result_dict["reboot"] = self.__need_reboot
        result_dict["count"] = {"serious": d_risk, "high_risk": h_risk, "moderate_risk": m_risk}
        result_dict["msg"] = ""
        result_dict["repair_count"] = self.count_repair(vul_list)
        result_dict["all_check_time"] = public.ReadFile(self.__path + '/system_scan_time')
        result_dict["ignore_count"] = len(tmp_ignore_list)
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 8" in result:
                result_dict[
                    "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        return result_dict

    # 按分数评等级
    def get_score_risk(self, score):
        '''
        拿到分数，返回危险等级
        :param score:
        :return: int 若没有符合的分数就报错，需要捕获异常
        '''
        if float(score) >= 9.0:
            risk = 3
        elif float(score) >= 7.0:
            risk = 2
        elif float(score) >= 6.0:
            risk = 1
        return risk

    def get_vul_list(self):
        return json.loads(public.ReadFile(self.__vul_list))

    def get_ignore_list(self):
        return json.loads(public.ReadFile(self._vuln_ignore))

    def set_vuln_ignore(self, args):
        '''
        设置忽略指定cve，若已在列表里，则删除，不在列表里则添加
        :param args:
        :return: dict {status:true,msg:'设置成功/失败'}
        '''
        cve_list = json.loads(args.cve_list.strip())
        ignore_list = self.get_ignore_list()
        for cl in cve_list:
            if cl in ignore_list:
                ignore_list.remove(cl)
            else:
                ignore_list.append(cl)

        public.WriteFile(self._vuln_ignore, json.dumps(ignore_list))
        # public.WriteFile(self.__result, json.dumps(result_dict))
        return public.returnMsg(True, '设置成功!')
        # except:
        #     return public.returnMsg(False, '{}设置失败!'.format(cve_list))

    def count_repair(self, now_list):
        '''
        获取总共修复漏洞的数量以及今日修复漏洞数量
        :param now_list:
        :return: dict
        '''
        cve_dict = {}
        if not os.path.exists(self.__repair_count):
            cve_dict["all_cve"] = now_list
            cve_dict["today_cve"] = now_list
            cve_dict["time"] = int(time.time())
            public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        cve_dict = json.loads(public.ReadFile(self.__repair_count))
        cve_dict["all_cve"].extend(set(now_list) - set(cve_dict["all_cve"]))
        all_count = len(cve_dict["all_cve"]) - len(now_list)
        cve_dict["today_cve"].extend(set(now_list) - set(cve_dict["today_cve"]))
        today_count = len(cve_dict["today_cve"]) - len(now_list)
        # if cve_dict["time"].split(" ")[0] != self.get_time().split(" ")[0]:
        #     cve_dict["today_cve"] = now_list
        cve_dict["time"] = int(time.time())
        public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        return {"all_count": all_count, "today_count": today_count}

    def get_time(self):
        return public.format_date()

    def check_cve(self, args):
        '''
        检测单个漏洞
        :param args:
        :return: dict
        '''
        sys_product = self.get_sys_product()
        if not sys_product:
            return public.returnMsg(True, '检测失败')
        cve_id = args.cve_id.strip()
        result_dict = json.loads(public.ReadFile(self._vuln_result))
        risk_list = result_dict["risk"]
        ignore_list = result_dict["ignore"]
        tmptmp = 1
        for cve in risk_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = int(time.time())
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    risk_list.remove(cve)
        for cve in ignore_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = int(time.time())
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    ignore_list.remove(cve)
        result_dict["risk"] = risk_list
        result_dict["ignore"] = ignore_list
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        if tmptmp == 0:
            return public.returnMsg(True, '已重新检测')
        else:
            return public.returnMsg(True, '已重新检测')

    def compare_md5(self):
        '''
        对比md5，更新漏洞库
        :return:
        '''
        import requests
        # try:
        #    new_md5 = requests.get("https://www.bt.cn/vulscan_d11ad1fe99a5f078548b0ea355db42dc.txt").text
        # except:
        #    return 0
        # old_md5 = public.FileMd5(self.__vul_list)
        # if old_md5 != new_md5 or not os.path.exists(self.__vul_list):
        if not os.path.exists(self.__vul_list):
            try:
                public.downloadFile("{}/install/src/high_risk_vul.zip".format(public.get_url()),
                                    self.__path + "/high_risk_vul.zip")
                public.ExecShell("unzip -o {}/high_risk_vul.zip -d {}/".format(self.__path, self.__path))
            except:
                return 0
        return 1

    def get_logs(self, get):
        '''
        获取升级日志
        :param get:
        :return: dict
        '''
        import files
        return public.returnMsg(True, files.files().GetLastLine(self.__path + '/log.txt', 20))

    def record_times(self):
        '''
        记录近七日扫描次数
        '''
        date_obj = datetime.datetime.now()
        weekday = datetime.datetime.now().weekday()
        if not os.path.exists("/www/server/panel/data/warning_report/record.json"):
            tmp = {"scan": [], "repair": []}
            for i in range(6, -1, -1):
                last_date = (date_obj - datetime.timedelta(days=i)).strftime("%Y/%m/%d")
                tmp["scan"].append({"date": last_date, "times": 0})
                tmp["repair"].append({"date": last_date, "times": 0})
            public.WriteFile("/www/server/panel/data/warning_report/record.json", json.dumps(tmp))
        with open("/www/server/panel/data/warning_report/record.json", "r") as f:
            record = json.load(f)
        if record["scan"][weekday]["date"] == datetime.datetime.now().strftime("%Y/%m/%d"):
            record["scan"][weekday]["times"] += 1
        else:
            record["scan"][weekday]["date"] = datetime.datetime.now().strftime("%Y/%m/%d")
            record["scan"][weekday]["times"] = 1
        public.WriteFile("/www/server/panel/data/warning_report/record.json", json.dumps(record))

    def get_scan_bar(self, args):
        '''
        获取扫描进度条
        @param args:
        @return: int
        '''
        if not os.path.exists(self.__path + '/bar.txt'): return 0
        try:
            data = json.loads(public.ReadFile(self.__path + '/bar.txt'))
        except Exception as e:
            # public.print_log("获取扫描进度条报错{}".format(e))
            return {"status": "", "percentage": 0, "count": 0, "score": 100}
        return data

    def kill_get_list(self, args):
        '''
        杀掉扫描进程
        @param args:
        @return:
        '''
        if not os.path.exists(self.__path + '/pid.txt'):
            return {"status": False, "msg": "中断失败"}
        pid = public.ReadFile(self.__path + '/pid.txt')
        err = public.ExecShell("kill -9 {}".format(str(pid)))[1].strip()
        if err:
            return {"status": False, "msg": "中断失败"}
        else:
            public.WriteFile(self.__path + '/kill.pl', "True")
            return {"status": True, "msg": "中断成功"}

    def dump_tmp_result(self):
        '''
        动态保存结果
        @param args:
        @return:
        '''
        public.WriteFile(self.__path + '/tmp_result.json', json.dumps(self.tmp_data))

    def get_tmp_result(self, args):
        '''
        获取中途中断结果
        @param args:
        @return:
        '''
        if not os.path.exists(self.__path + '/tmp_result.json'):
            return "err"
        try:
            tmp_result = json.loads(public.ReadFile(self.__path + '/tmp_result.json'))
        except Exception as e:
            # public.print_log("首页获取中断结果报错：{}".format(e))
            return {"security": [], "risk": [], "ignore": [], "interrupt": True, "is_autofix": [], "score": 100, "check_time": ""}
        return tmp_result

    def new_system_scan2(self):
        '''
        新版系统dpkg软件包漏洞检测
        '''
        if not os.path.exists(self.new_vul_list):
            return
        # 初始化进度条
        context = {"status": "正在检查系统软件", "percentage": 0, "count": 0, "score": 100}
        public.WriteFile(self.__path + '/bar.txt', json.dumps(context))

        # 加载漏洞库文件
        try:
            vul_json = json.loads(public.ReadFile(self.new_vul_list))
            packages_rule = vul_json['Packages']
            detail = vul_json['Detail']
        except Exception as e:
            return
        sys_product = self.new_get_sys_product()
        if sys_product is None:
            return

        dpkg = Dpkg  # 获取DPKG对象
        # 符合
        systemscan_result = {}
        # 开始检测
        # 第一层遍历系统软件包
        for pk, ver in sys_product.items():
            # 跳过内核漏洞检测
            # if pk.startswith("kernel"):
            #     continue
            # 是否有历史漏洞
            if pk in packages_rule:
                # 第二层遍历比较软件包涉及的漏洞版本
                for rule in packages_rule[pk]:
                    # 判断软件包版本是否存在主版本号，有则漏洞版本一起保留主版本号，否则去掉漏洞版本的主版本号
                    pk_ver, vul_ver = self.adjust_ver(ver, rule[0])
                    try:
                        cp_result = dpkg.compare_versions(pk_ver, vul_ver)
                    except:
                        continue
                    # 任意一个命中
                    if cp_result == -1:
                        if rule[1] not in systemscan_result:
                            systemscan_result[rule[1]] = detail[str(rule[1])]
                            systemscan_result[rule[1]]["impact"] = [
                                {"package": pk, "version": pk_ver, "vul_ver": vul_ver}]
                        else:
                            systemscan_result[rule[1]]["impact"].append(
                                {"package": pk, "version": pk_ver, "vul_ver": vul_ver})

        # 为了兼容旧版本再次做处理
        for sr in systemscan_result.values():
            try:
                one_risk = {}
                one_risk["title"] = "【{}】Linux系统安全漏洞编号".format(sr["ref_id"])
                one_risk["date"] = "2023-12-08"
                one_risk["help"] = ""
                one_risk["ignore"] = False
                level = self.new_severity_to_num(sr["severity"])
                one_risk["level"] = level
                one_risk["m_name"] = sr["ref_id"]
                pk_list = []
                # 判断是否有内核漏洞在里面
                # is_kernel = False
                soft_list = []

                for impact in sr["impact"]:
                    soft_list.append(
                        "{} 版本低于 {}".format(impact["package"] + "-" + impact["version"], impact["vul_ver"]))
                    pk_list.append(impact["package"])
                one_risk["msg"] = "发现以下系统软件存在安全漏洞：<br>{}<br>涉及漏洞：{}<br>漏洞描述：{}<br>详情参考官方公告：{}".format(
                    '<br>'.join(soft_list), '、'.join(sr["cve"]), sr["description"][:280]+'......', sr["ref_url"])
                one_risk["ps"] = "【{}】Linux系统安全漏洞编号".format(sr["ref_id"])
                one_risk["remind"] = "修复漏洞具有一定的风险，建议做好系统快照，防止影响系统运行。"
                one_risk["status"] = False
                one_risk["taking"] = 0.000001
                one_risk["tips"] = ["根据风险描述，更新软件至安全版本", "或者点击【一键修复】解决所有安全问题"]
                one_risk["version"] = 1
                one_risk["type"] = "vulnerability"
                one_risk["package"] = pk_list

                # 存储结果
                # 是否被忽略
                ignore_file = self.__ignore + '/' + sr["ref_id"] + '.pl'
                if os.path.exists(ignore_file):
                    one_risk["ignore"] = True
                    self.data["ignore"].append(one_risk)
                    # 扫描中的动态风险
                    self.tmp_data['ignore'].append(one_risk)
                else:
                    self.data["risk"].append(one_risk)
                    # 扫描中的动态风险
                    self.tmp_data['risk'].append(one_risk)
                    # 扫描中发现的漏洞数
                    self.discov_count += 1
                    # 扫描中的动态分数
                    self.score -= level
                    if self.score < 0:
                        self.score = 0

                self.data["is_autofix"].append(one_risk["m_name"])
                # 可修复项
                self.tmp_data['is_autofix'].append(one_risk["m_name"])
            except:
                continue

    def new_system_scan(self):
        '''
        新版系统rpm软件包漏洞检测
        提升扫描速度
        :param get:
        :return: dict
        '''

        # 判断新漏洞库存不存在
        if not os.path.exists(self.new_vul_list):
            return

        context = {"status": "正在检查系统软件", "percentage": 0, "count": 0, "score": 100}
        public.WriteFile(self.__path + '/bar.txt', json.dumps(context))
        sys_product = self.new_get_sys_product()
        # 加载漏洞库文件
        try:
            vul_json = json.loads(public.ReadFile(self.new_vul_list))
            packages_rule = vul_json['Packages']
            detail = vul_json['Detail']
        except Exception as e:
            return
        if sys_product is None:
            return

        # 符合
        systemscan_result = {}
        # 开始检测
        # 第一层遍历系统软件包
        for pk, ver in sys_product.items():
            # 跳过内核漏洞检测
            # if pk.startswith("kernel"):
            #     continue
            # 是否有历史漏洞
            if pk in packages_rule:
                # 第二层遍历比较软件包涉及的漏洞版本
                for rule in packages_rule[pk]:
                    # 判断软件包版本是否存在主版本号，有则漏洞版本一起保留主版本号，否则去掉漏洞版本的主版本号
                    pk_ver, vul_ver = self.adjust_ver(ver, rule[0])
                    cp_result = self.vercmp(pk_ver, vul_ver)
                    if cp_result == -1:
                        if rule[1] not in systemscan_result:
                            systemscan_result[rule[1]] = detail[str(rule[1])]
                            systemscan_result[rule[1]]["impact"] = [
                                {"package": pk, "version": pk_ver, "vul_ver": vul_ver}]
                        else:
                            systemscan_result[rule[1]]["impact"].append(
                                {"package": pk, "version": pk_ver, "vul_ver": vul_ver})
        # public.WriteFile("/tmp/centos7_result.json", json.dumps(systemscan_result, indent=4))

        # 为了兼容旧版本再次做处理
        for sr in systemscan_result.values():
            try:
                one_risk = {}
                one_risk["title"] = "【{}】Linux系统漏洞安全通告".format(sr["ref_id"])
                one_risk["date"] = "2023-12-08"
                one_risk["help"] = ""
                one_risk["ignore"] = False
                level = self.new_severity_to_num(sr["severity"])
                one_risk["level"] = level
                one_risk["m_name"] = sr["ref_id"]
                pk_list = []
                # 判断是否有内核漏洞在里面
                is_kernel = False
                soft_list = []
                for impact in sr["impact"]:
                    if impact["package"].startswith("kernel"):
                        is_kernel = True
                        continue
                    soft_list.append(
                        "{} 版本低于 {}".format(impact["package"] + "-" + impact["version"], impact["vul_ver"]))
                    pk_list.append(impact["package"])
                if is_kernel:
                    continue
                one_risk["msg"] = "发现以下系统软件存在安全漏洞：<br>{}<br>涉及漏洞：{}<br>漏洞描述：{}<br>详情参考官方公告：{}".format(
                    '<br>'.join(soft_list), '、'.join(sr["cve"]), sr["description"][:280]+'......', sr["ref_url"])
                one_risk["ps"] = "【{}】Linux系统漏洞安全通告".format(sr["ref_id"])
                one_risk["remind"] = "修复漏洞具有一定的风险，建议做好系统快照，防止影响系统运行。"
                one_risk["status"] = False
                one_risk["taking"] = 0.000001
                one_risk["tips"] = ["根据风险描述，更新软件至安全版本", "或者点击【一键修复】解决所有安全问题"]
                one_risk["version"] = 1
                one_risk["type"] = "vulnerability"
                one_risk["package"] = pk_list

                # 存储结果
                # 是否被忽略
                ignore_file = self.__ignore + '/' + sr["ref_id"] + '.pl'
                if os.path.exists(ignore_file):
                    one_risk["ignore"] = True
                    self.data["ignore"].append(one_risk)
                    self.tmp_data['ignore'].append(one_risk)
                else:
                    self.data["risk"].append(one_risk)
                    # 扫描中的动态风险
                    self.tmp_data['risk'].append(one_risk)
                    # 扫描中发现的漏洞数
                    self.discov_count += 1
                    # 扫描中的动态分数
                    self.score -= level
                    if self.score < 0:
                        self.score = 0

                self.data["is_autofix"].append(one_risk["m_name"])
                # 临时结果
                self.tmp_data['is_autofix'].append(one_risk["m_name"])
            except:
                continue

        # result_json = {
        #     "vul_count": len(detail),
        #     "risk": [],
        #     "ignore": [],
        #     "all_check_time": "",
        #     "ignore_count": 0,
        #     "msg": "",
        #     "repair_count": {"all_count": 0, "today_vount": 0},
        # }
        # for sr in systemscan_result.values():
        #     one_risk = {
        #         "cve_id": "",
        #         "vuln_name": "",
        #         "vuln_time": "2021-12-16",
        #         "vuln_solution": "",
        #         "level": 1,
        #         "soft_name": {},
        #         "vuln_version": "",
        #         "check_time": 1701910962,
        #         "reboot": ""
        #     }
        #     one_risk["cve_id"] = sr["ref_id"]
        #     one_risk["vuln_name"] = "【{}】Linux软件安全公告".format(sr["ref_id"])
        #     one_risk["vuln_solution"] = "更新涉及软件补丁，具体信息参考官方公告{}".format(sr["ref_url"])
        #     level = self.new_severity_to_num(sr["severity"])
        #     one_risk["level"] = level
        #     # 处理受影响的软件包（为了兼容旧版本暂时这样）
        #     soft_name = {}
        #     vuln_version = ""
        #     for impact in sr["impact"]:
        #         soft_name[impact["package"]] = impact["version"]
        #         vuln_version = impact["vul_ver"]
        #     one_risk["soft_name"] = soft_name
        #     one_risk["vuln_version"] = vuln_version
        #     risk_list.append(one_risk)
        #
        #     # 扫描中发现的漏洞数
        #     self.discov_count += 1
        #     # 扫描中的动态分数
        #     self.score -= level
        #     if self.score < 0:
        #         self.score = 0
        #     # 扫描中的动态风险
        #     self.tmp_data['risk'].append(one_risk)
        #     # 可修复项
        #     self.tmp_data['is_autofix'].append(one_risk["cve_id"])
        #
        # result_json["risk"] = risk_list
        # public.WriteFile(self.__path + '/system_scan_time', int(time.time()))
        # public.WriteFile(self._vuln_result, json.dumps(result_json))

    def is_file_too_old(self, file_path, days):
        """
        判断文件是否过于陈旧
        :param file_path: 文件路径
        :param days: 超过的天数
        :return: bool
        """
        try:
            mtime = os.path.getmtime(file_path)
            mod_time = datetime.datetime.fromtimestamp(mtime)
            days_old = datetime.datetime.now() - mod_time
        except:
            return True
        return days_old.days > days

    def adjust_ver(self, ver_a, ver_b):
        '''
        确保两个版本主版本号统一，一方存在另一方不存在则删除主版本，要么都有，要么都没有
        '''
        if ":" in ver_a:
            if ":" in ver_b:
                ver_1 = ver_a
            else:
                ver_1 = ver_a.split(":")[1]
            ver_2 = ver_b
        else:
            if ":" in ver_b:
                ver_2 = ver_b.split(":")[1]
            else:
                ver_2 = ver_b
            ver_1 = ver_a
        return ver_1, ver_2

    def new_severity_to_num(self, severity):
        '''
        将漏洞级别转变成数字
        '''
        if severity == "Critical":
            return 3
        elif severity == "Important":
            return 2
        elif severity == "Moderate":
            return 1
        elif severity == "Low":
            return 1
        elif severity == "High":
            return 3
        elif severity == "Medium":
            return 2
        else:
            return 2

    # def new_rpmvercmp(self, sys_ver, vul_ver):
    #     output, err = public.ExecShell("rpmdev-vercmp {} {}".format(sys_ver, vul_ver))
    #     if err != '':
    #         return 1
    #     output = output.strip()
    #     if output == "{} > {}".format(sys_ver, vul_ver):
    #         return 1
    #     elif output == "{} == {}".format(sys_ver, vul_ver):
    #         return 0
    #     elif output == "{} < {}".format(sys_ver, vul_ver):
    #         return -1
    #     else:
    #         return 1
    def get_repair_logs(self, get):
        """
        @name 获取修复历史记录
        @param get.p string 页码
        @param get.tojs
        @return page string 前端页码
        @return data list 数据
        """
        data = {}
        # count = 0
        data['data'] = []

        if os.path.exists(self.__repair_history):
            try:
                history = json.loads(public.ReadFile(self.__repair_history))
            except:
                history = []
            data['data'] = history
        return data

    def init_new_vul(self):
        """
        @name 初始化漏洞库名
        @author lwh<2024-03-02>
        """
        sys_version = self.get_sys_version()
        if sys_version == "centos_7":
            self.new_vul_list = self.__path + '/vul_centos7.json'
        elif sys_version == "centos_8":
            self.new_vul_list = self.__path + '/vul_centos8.json'
        elif sys_version == "centos_8_stream":
            self.new_vul_list = self.__path + '/vul_centos8stream.json'
        elif sys_version == "alicloud_3":
            self.new_vul_list = self.__path + '/vul_alicloud3.json'
        elif sys_version == "alicloud_2":
            self.new_vul_list = self.__path + '/vul_alicloud2.json'
        elif sys_version == "ubuntu_20.04":
            self.new_vul_list = self.__path + '/vul_ubuntu2004.json'
        elif sys_version == "ubuntu_22.04":
            self.new_vul_list = self.__path + '/vul_ubuntu2204.json'
        elif sys_version == "ubuntu_18.04":
            self.new_vul_list = self.__path + '/vul_ubuntu1804.json'
        elif sys_version == "debian_12":
            self.new_vul_list = self.__path + '/vul_debian12.json'
        elif sys_version == "debian_11":
            self.new_vul_list = self.__path + '/vul_debian11.json'
        elif sys_version == "debian_10":
            self.new_vul_list = self.__path + '/vul_debian10.json'


class Dpkg:
    def __init__(self):
        self._fileinfo = None
        self._control_str = None
        self._headers = None
        self._message = None
        self._upstream_version = None
        self._debian_revision = None
        self._epoch = None

    @staticmethod
    def get_epoch(version_str):
        try:
            e_index = version_str.index(":")
        except ValueError:
            return 0, version_str

        try:
            epoch = int(version_str[0:e_index])
        except ValueError as ex:
            print(f"Corrupt dpkg version '{version_str}': epochs can only be ints, and "
                  "epochless versions cannot use the colon character.")
        return epoch, version_str[e_index + 1:]

    @staticmethod
    def get_upstream(version_str):
        try:
            d_index = version_str.rindex("-")
        except ValueError:
            return version_str, "0"

        return version_str[0:d_index], version_str[d_index + 1:]

    @staticmethod
    def split_full_version(version_str):
        epoch, full_ver = Dpkg.get_epoch(version_str)
        upstream_rev, debian_rev = Dpkg.get_upstream(full_ver)
        return epoch, upstream_rev, debian_rev

    @staticmethod
    def get_alphas(revision_str):
        for i, char in enumerate(revision_str):
            if char.isdigit():
                if i == 0:
                    return "", revision_str
                return revision_str[0:i], revision_str[i:]
        return revision_str, ""

    @staticmethod
    def get_digits(revision_str):
        if not revision_str:
            return 0, ""
        for i, char in enumerate(revision_str):
            if not char.isdigit():
                if i == 0:
                    return 0, revision_str
                return int(revision_str[0:i]), revision_str[i:]
        return int(revision_str), ""

    @staticmethod
    def listify(revision_str):
        result = []
        while revision_str:
            rev_1, remains = Dpkg.get_alphas(revision_str)
            rev_2, remains = Dpkg.get_digits(remains)
            result.extend([rev_1, rev_2])
            revision_str = remains
        return result

    @staticmethod
    def dstringcmp(a, b):
        if a == b:
            return 0
        try:
            for i, char in enumerate(a):
                if char == b[i]:
                    continue
                if char == "~":
                    return -1
                if b[i] == "~":
                    return 1
                if char.isalpha() and not b[i].isalpha():
                    return -1
                if not char.isalpha() and b[i].isalpha():
                    return 1
                if ord(char) > ord(b[i]):
                    return 1
                if ord(char) < ord(b[i]):
                    return -1
        except IndexError:
            if char == "~":
                return -1
            return 1
        if b[len(a)] == "~":
            return 1
        return -1

    @staticmethod
    def compare_revision_strings(rev1, rev2):
        if rev1 == rev2:
            return 0
        list1 = Dpkg.listify(rev1)
        list2 = Dpkg.listify(rev2)
        if list1 == list2:
            return 0
        try:
            for i, item in enumerate(list1):
                if i >= len(list2):
                    raise IndexError
                if not isinstance(item, list2[i].__class__):
                    print(f"Cannot compare '{item}' to {list2[i]}, something has gone horribly awry.")
                if item == list2[i]:
                    continue
                if isinstance(item, int):
                    if item > list2[i]:
                        return 1
                    if item < list2[i]:
                        return -1
                else:
                    return Dpkg.dstringcmp(item, list2[i])
        except IndexError:
            if list1[len(list2)][0][0] == "~":
                return -1
            return 1
        if list2[len(list1)][0][0] == "~":
            return 1
        return -1

    @staticmethod
    def compare_versions(ver1, ver2):
        if ver1 == ver2:
            return 0
        epoch1, upstream1, debian1 = Dpkg.split_full_version(str(ver1))
        epoch2, upstream2, debian2 = Dpkg.split_full_version(str(ver2))

        if epoch1 < epoch2:
            return -1
        if epoch1 > epoch2:
            return 1

        upstr_res = Dpkg.compare_revision_strings(upstream1, upstream2)
        if upstr_res != 0:
            return upstr_res

        debian_res = Dpkg.compare_revision_strings(debian1, debian2)
        if debian_res != 0:
            return debian_res

        return 0


if __name__ == "__main__":
    # st = time.time()
    # 核心执行函数，因为需要中断扫描，所以改为main执行
    panel = panelWarning()
    # 将扫描结果保存到json
    public.WriteFile('/www/server/panel/data/warning/resultresult.json', json.dumps(panel._get_list()))
    # et = time.time()

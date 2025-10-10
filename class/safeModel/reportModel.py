# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <2023-08-01>
# -------------------------------------------------------------------

# 首页安全风险，展示检测结果
# ------------------------------
import json
import os
import sys

from safeModel.base import safeBase

os.chdir("/www/server/panel")
sys.path.append("class/")
import public, config, datetime

class main(safeBase):
    __path = '/www/server/panel/data/warning_report'
    __risk = __path + '/risk'
    __data = __path + '/data.json'
    new_result = "/www/server/panel/data/warning/resultresult.json"
    data = []
    final_obj = {}
    all_cve = 0
    cve_num = 0
    high_cve = 0
    mid_cve = 0
    low_cve = 0
    cve_list = []
    high_warn = 0
    mid_warn = 0
    low_warn = 0
    high_warn_list = []
    mid_warn_list = []
    low_warn_list = []
    auto_fix = []  # 自动修复列表

    def __init__(self):
        self.configs = config.config()
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, 384)

    def get_report(self, get):
        '''
            将检测数据，填充到html，并展示检测报告数据
        '''
        public.set_module_logs("report", "get_report")
        self.cve_list = []
        self.high_warn_list = []
        self.mid_warn_list = []
        self.low_warn_list = []
        # if not os.path.exists(self.__data):
        #     return public.returnMsg(False, '导出失败，未发现扫描结果')
        # data = json.loads(public.readFile(self.__data))
        # 获取最新的检测结果
        if not os.path.exists(self.new_result):
            return public.returnMsg(False, "未找到检测结果，请先执行首页安全风险扫描")
        cve_result = json.loads(public.ReadFile(self.new_result))

        first = {}
        first["date"] = cve_result["check_time"]  # 带有时间的检测日期
        first["host"] = public.get_hostname()  # 主机名
        first["ip"] = public.get_server_ip()  # 外网IP
        first["local_ip"] = public.GetLocalIp()  # 内网IP
        # if os.path.exists("/www/server/panel/data/warning/result.json"):
        #     with open("/www/server/panel/data/warning/result.json") as f:
        #         cve_result = json.load(f)
        #         public.print_log(cve_result)
        #         self.cve_list = cve_result["risk"]
        #         self.high_cve = cve_result["count"]["serious"]
        #         self.mid_cve = cve_result["count"]["high_risk"]
        #         self.low_cve = cve_result["count"]["moderate_risk"]
        #         self.all_cve = cve_result["vul_count"]

        if "risk" not in cve_result:
            return public.returnMsg(False, "未找到risk字段")
        # 获取可自动修复列表
        if "is_autofix" in cve_result:
            self.auto_fix = cve_result["is_autofix"]
        for risk in cve_result["risk"]:
            # 若为漏洞
            if risk["title"].startswith("CVE") or risk["title"].startswith("RH"):
                self.cve_list.append(risk)
                self.cve_num += 1
                if risk["level"] == 3:
                    self.high_cve += 1
                elif risk["level"] == 2:
                    self.mid_cve += 1
                elif risk["level"] == 1:
                    self.low_cve += 1
                else:
                    self.cve_num -= 1
                    continue
            # 其余为风险
            else:
                if risk["level"] == 3:
                    self.high_warn += 1
                    self.high_warn_list.append(risk)
                elif risk["level"] == 2:
                    self.mid_warn += 1
                    self.mid_warn_list.append(risk)
                elif risk["level"] == 1:
                    self.low_warn += 1
                    self.low_warn_list.append(risk)
                else:
                    continue
        # for d in data["risk"]:
        #     if "title" in d:
        #         if d["level"] == 3:
        #             self.high_warn += 1
        #             self.high_warn_list.append(d)
        #         elif d["level"] == 2:
        #             self.mid_warn += 1
        #             self.mid_warn_list.append(d)
        #         else:
        #             self.low_warn += 1.
        #             self.low_warn_list.append(d)

        if self.high_warn + self.high_cve > 1:
            total_level = '差'
            level_color = '差'
        elif self.mid_warn + self.mid_cve > 10 or self.high_warn + self.high_cve == 1:
            total_level = '良'
            level_color = '良'
        else:
            total_level = '优'
            level_color = '优'
        # self.cve_num = self.high_cve + self.mid_cve + self.low_cve
        level_reason = "服务器未发现较大的安全风险，继续保持！"
        if total_level == "差":
            level_reason = "服务器存在高危安全风险或系统漏洞，可能会导致黑客入侵，<span style=\"" \
                           "font-size: 1.1em;font-weight: 700;color: red;\">请尽快修复！</span>"
        if total_level == "良":
            level_reason = "服务器发现潜在的安全风险，<span style=\"" \
                           "font-size: 1.1em;font-weight: 700;color: red;\">建议尽快修复！</span>"
        warn_level = '优'
        if self.high_warn > 0:
            warn_level = '差'
            first_warn = "发现高危安全风险{}个".format(self.high_warn)
        elif self.mid_warn > 5:
            warn_level = '良'
            first_warn = "发现较多中危安全风险"
        else:
            first_warn = "未发现较大的安全风险"
        cve_level = '优'
        if self.cve_num > 1:
            cve_level = '差'
            first_cve = "发现较多系统漏洞{}个".format(self.cve_num)
        elif self.cve_num == 1:
            cve_level = '良'
            first_cve = "发现少量系统漏洞"
        else:
            first_cve = "未发现存在系统漏洞"
        second = {}
        long_date = cve_result["check_time"]  # 带有时间的检测日期
        date_obj = datetime.datetime.strptime(long_date, "%Y/%m/%d %H:%M:%S")
        second["date"] = date_obj.strftime("%Y/%m/%d")
        second["last_date"] = (date_obj - datetime.timedelta(days=6)).strftime("%Y/%m/%d")
        second["level_color"] = level_color
        second["total_level"] = total_level
        second["level_reason"] = level_reason
        second["warn_level"] = warn_level
        second["first_warn"] = first_warn
        second["cve_level"] = cve_level
        second["first_cve"] = first_cve
        third = {}
        # 获取扫描记录
        warn_times = 0
        repair_times = 0
        record_file = self.__path + "/record.json"
        if os.path.exists(record_file):
            record = json.loads(public.ReadFile(record_file))
            for r in record["scan"]:
                warn_times += r["times"]
            for r in record["repair"]:
                repair_times += r["times"]
        # with open(self.__path+"/record.json", "r") as f:
        #     record = json.load(f)
        # for r in record["scan"]:
        #     warn_times += r["times"]
        # for r in record["repair"]:
        #     repair_times += r["times"]
        third["warn_times"] = warn_times
        third["cve_times"] = warn_times
        third["repair_times"] = repair_times
        third["last_month"] = (date_obj - datetime.timedelta(days=6)).strftime("%m")
        third["last_day"] = (date_obj - datetime.timedelta(days=6)).strftime("%d")
        third["month"] = date_obj.strftime("%m")
        third["day"] = date_obj.strftime("%d")
        third["second_warn"] = "每日登陆面板，例行服务器安全风险检测。"
        if self.cve_num > 0:
            third["second_cve"] = "对系统内核版本以及流行应用进行漏洞扫描，发现存在漏洞风险。"
        else:
            third["second_cve"] = "对系统内核版本以及流行应用进行漏洞扫描，未发现漏洞风险。"
        third["repair"] = "执行一键修复，解决安全问题。"
        fourth = {}

        fourth["warn_num"] = len(self.high_warn_list)
        fourth["cve_num"] = self.cve_num
        fourth["web_num"] = 41
        fourth["sys_num"] = 29
        fourth["cve_num"] = 5599
        fourth["kernel_num"] = 5
        fourth["high_cve"] = str(self.high_cve) + "个"
        if self.high_cve == 0:
            fourth["high_cve"] = "未发现"
        fourth["mid_cve"] = str(self.mid_cve) + "个"
        if self.mid_cve == 0:
            fourth["mid_cve"] = "未发现"
        fourth["low_cve"] = str(self.low_cve) + "个"
        if self.low_cve == 0:
            fourth["low_cve"] = "未发现"
        fourth["high_warn"] = str(self.high_warn) + "个"
        if self.high_warn == 0:
            fourth["high_warn"] = "无"
        fourth["mid_warn"] = str(self.mid_warn) + "个"
        if self.mid_warn == 0:
            fourth["mid_warn"] = "无"
        fourth["low_warn"] = str(int(self.low_warn)) + "个"
        if self.low_warn == 0:
            fourth["low_warn"] = "无"
        fifth = {}
        num = 1  # 序号
        focus_high_list = []
        for hwl in self.high_warn_list:
            focus_high_list.append(
                {
                    "num": str(num),
                    "name": str(hwl["msg"]),
                    "level": "高危",
                    "ps": str(hwl["ps"]),
                    "tips": '\n'.join(hwl["tips"]),
                    "auto": self.is_autofix1(hwl["m_name"])
                }
            )
            num += 1
        fifth["focus_high_list"] = focus_high_list
        focus_mid_list = []
        for mwl in self.mid_warn_list:
            focus_mid_list.append(
                {
                    "num": num,
                    "name": mwl["msg"],
                    "level": "中危",
                    "ps": mwl["ps"],
                    "tips": '\n'.join(mwl["tips"]),
                    "auto": self.is_autofix1(mwl["m_name"])
                }
            )
            num += 1
        fifth["focus_mid_list"] = focus_mid_list
        focus_cve_list = []
        for cl in self.cve_list:
            tmp_cve = {
                    "num": num,
                    "name": cl["m_name"],
                    "level": "高危",
                    "ps": cl["ps"],
                    "tips": '\n'.join(cl["tips"]),
                    "auto": "支持"
                }
            if cl["level"] == 2:
                tmp_cve["name"] = cl["m_name"]
                tmp_cve["level"] = "中危"
            elif cl["level"] == 1:
                tmp_cve["name"] = cl["m_name"]
                tmp_cve["level"] = "低危"
            focus_cve_list.append(tmp_cve)
            num += 1
        fifth["focus_cve_list"] = focus_cve_list
        sixth = {}
        num = 1  # 序号
        low_warn_list = []
        for lwl in self.low_warn_list:
            low_warn_list.append(
                {
                    "num": str(num),
                    "name": str(lwl["msg"]),
                    "level": "低危",
                    "ps": str(lwl["ps"]),
                    "tips": '\n'.join(lwl["tips"]),
                    "auto": self.is_autofix1(lwl["m_name"])
                }
            )
            num += 1
        sixth["low_warn_list"] = low_warn_list
        ignore_list = []
        for ig in cve_result["ignore"]:
            if "title" in ig:
                ignore_list.append(
                    {
                        "num": num,
                        "name": ig["msg"],
                        "level": "忽略项",
                        "ps": ig["ps"],
                        "tips": '\n'.join(ig["tips"]),
                        "auto": self.is_autofix(ig)
                    }
                )
            elif "cve_id" in ig:
                ignore_list.append(
                    {
                        "num": num,
                        "name": ig["cve_id"],
                        "level": "忽略项",
                        "ps": ig["vuln_name"],
                        "tips": "将【{}】版本升级至{}或更高版本。".format('、'.join(ig["soft_name"]), ig["vuln_version"]),
                        "auto": self.is_autofix(ig)
                    }
                )
            num += 1
        sixth["ignore_list"] = ignore_list
        self.final_obj = {"first": first, "second": second, "third": third, "fourth": fourth, "fifth": fifth, "sixth": sixth}
        return public.returnMsg(True, self.final_obj)

    def is_autofix(self, warn):
        data = json.loads(public.readFile(self.__data))
        if "title" in warn:
            if warn["m_name"] in data["is_autofix"]:
                return "支持"
            else:
                return "不支持"
        if "cve_id" in warn:
            if list(warn["soft_name"].keys())[0] == "kernel":
                return "不支持"
            else:
                return "支持"

    def is_autofix1(self, name):
        """
        @name 判断是否可以自动修复
        """
        if name in self.auto_fix:
            return "支持"
        else:
            return "不支持"

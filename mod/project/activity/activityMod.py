import json
import os

import requests
from flask import request

import public


class main:
    # 取操作日志
    def get_operation_log(self):
        try:
            logs = json.loads(public.readFile("data/activity_task_logs.json"))
        except:
            logs = {}
        return logs

    # 写操作日志
    def write_operation_log(self, task_id, log):
        logs = self.get_operation_log()
        if str(task_id) not in logs.keys():
            logs[str(task_id)] = []
        logs[str(task_id)].append(log)
        public.writeFile("data/activity_task_logs.json", json.dumps(logs))
        return True

    # 获取任务信息
    def get_task_info(self, get):
        task_info = {}
        if not get:
            # 先取缓存
            try:
                task_info = json.loads(public.readFile("data/activity_task_info.json"))
            except:
                pass
        # 从官网取任务
        if not task_info:
            from sslModel import certModel
            task_info = certModel.main().new_ssl_proxy_request({"url": "/api/v1/ssl/activity/get_task_list","1":1})
            if not isinstance(task_info, dict) or "tasks" not in task_info:
                task_info = {
                    "success": False,
                    "type_list": [],
                    "tasks": [],
                }
            public.writeFile("data/activity_task_info.json", json.dumps(task_info))
        logs = self.get_operation_log()
        for task in task_info.get("tasks", []):
            if "rule" not in task:
                continue
            if "progress" not in task["rule"]:
                continue
            current = len(logs[str(task["id"])] if str(task["id"]) in logs else [])
            task["rule"]["progress"]["current"] = current if current < task["rule"]["success"]["value"] and not task["success"] else task["rule"]["success"]["value"]
            task["rule"]["progress"]["last_time"] = logs[str(task["id"])][-1]["time"] if str(task["id"]) in logs and len(logs[str(task["id"])]) > 0 else 0

        return public.returnMsg(True, task_info)

    # 检查url是否匹配
    def is_url_match_task(self, req_url, urls, match_type):
        if req_url[-1] == "?":
            req_url = req_url[:-1]
        for i in range(len(urls)):
            if urls[i][-1] == "?":
                urls[i] = urls[i][:-1]
        # 监控报表特殊处理
        if "/monitor/" in req_url and len(req_url.split("/")) > 3:
            return False

        # 匹配条件：精准匹配
        if match_type == "exact":
            if req_url in urls:
                return True
        # 匹配条件：模糊匹配
        elif match_type == "fuzzy":
            for url in urls:
                if url in req_url:
                    return True
        return False

    # 检查并更新任务进度
    def update_task_progress(self, task):
        if task["rule"].get("params", False):
            # 校验参数
            for key in task["rule"]["params"].keys():
                req_value = request.form.get(key, None)
                if not req_value:
                    try:
                        req_value = request.json.get(key, None)
                    except:
                        req_value = None
                if req_value != task["rule"]["params"][key] and task["rule"]["params"][key] != "*":
                    return task

        success_rule = task["rule"]["success"]
        if success_rule["type"] == "count":  # 按次数计数任务
            import time
            current_time = int(time.time())
            reset = success_rule["reset"]
            last_time = task["rule"]["progress"]["last_time"]
            # 是否到可计数时间
            if current_time - last_time < reset:
                return task
            # todo 是否可记录重复路由
            # 记录操作日志
            log = {
                "time": current_time,
                "task_id": task["id"],
                "path": request.full_path,
                "message": "任务进度更新，当前进度：{}/{}".format(
                    task["rule"]["progress"]["current"] + 1,
                    success_rule["value"]
                )
            }
            self.write_operation_log(task["id"], log)

            # 检查是否完成任务
            if task["rule"]["progress"]["current"] + 1 >= success_rule["value"]:
                task["success"] = True
                self.submit_completed_task(task["id"])
        return task

    # 检查任务状态
    def check_task_status(self, response):
        # 检查是否绑定了官网账号
        if not os.path.exists("/www/server/panel/data/userInfo.json"):
            return
        # 检查是否有邀请码
        if os.path.exists("/www/server/panel/data/activity_inviter_id.pl"):
            inviter_id = public.readFile("/www/server/panel/data/activity_inviter_id.pl")
            if inviter_id:
                from sslModel import certModel
                certModel.main().new_ssl_proxy_request(
                    {"url": "/api/v1/ssl/activity/user_pull_new", "inviter_id": inviter_id})
                # 拉新成功，重命名邀请码文件，避免重复拉新
                os.rename("/www/server/panel/data/activity_inviter_id.pl", "/www/server/panel/data/activity_inviter_id")

        task_info = self.get_task_info(None)['msg']
        try:
            res = response.get_json()
        except:
            return
        if not task_info:
            return
        # 检查是否任务已全部完成
        if task_info["success"]:
            return
        # 任务积分
        req_url = request.full_path
        is_matched = False
        for task in task_info["tasks"]:
            if not task["rule"]:
                continue
            if task["success"]:
                continue
            if isinstance(res, dict) and "status" in res and not res["status"]:
                continue
            urls = task["rule"]["urls"]
            match_type = task["rule"]["match_type"]
            if not self.is_url_match_task(req_url, urls, match_type):
                continue
            is_matched = True

            # 任务匹配成功
            # 任务完成规则
            task = self.update_task_progress(task)

        # 任务匹配失败，直接返回
        if not is_matched:
            return task_info

        # 检查是否所有任务完成
        all_success = True
        for task in task_info["tasks"]:
            if not task["success"]:
                all_success = False
                break
        task_info["success"] = all_success
        # 写回缓存
        public.writeFile("data/activity_task_info.json", json.dumps(task_info))
        return task_info

    # 提交已经完成的任务id
    def submit_completed_task(self, task_id):
        try:
            from sslModel import certModel
            res = certModel.main().new_ssl_proxy_request({"task_id": task_id, "url": "/api/v1/ssl/activity/user_complete_task"})
            public.print_log(res)
            return res
        except Exception as e:
            public.print_log("提交已完成任务失败: {}".format(e))
            return public.returnMsg(False, "提交已完成任务失败！")


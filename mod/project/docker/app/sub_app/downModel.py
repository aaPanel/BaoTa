# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: wzz
# | email : wzz@bt.cn
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | docker sub_app 管理模型 -
# +-------------------------------------------------------------------
import json
import sys
import time
from collections import deque

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public

def download_model(service_name, model_name, model_version, ollama_url, app_cmd_log):
    """
    下载Ollama模型的具体实现
    @param service_name: 服务名称
    @param model_name: 模型名称
    @param model_version: 模型版本
    @param ollama_url: Ollama API URL
    @param app_cmd_log: 日志文件路径
    """
    def start_download():
        url = ollama_url + "/api/pull"

        # 准备请求数据
        data = {
            "model": "{}:{}".format(model_name, model_version),
            "stream": True
        }

        try:
            import requests
            response = requests.post(url, json=data, stream=True)

            with open(app_cmd_log, 'a') as log_file:
                log_file.write('正在下载 {} 模型，可能需要等待1-30分钟以上...\n'.format(model_name))

                download_tag = None
                last_completed = 0
                last_time = time.time()
                # 使用双端队列存储最近10秒的速度
                speed_history = deque(maxlen=60)

                count_sum = 0
                for line in response.iter_lines():
                    if line:
                        json_response = json.loads(line)
                        status = json_response.get("status", "")

                        # 记录下载进度
                        if "pulling" in status:
                            status = status.split(" ")
                            if download_tag is None or status[1] != download_tag:
                                download_tag = status[1]
                                last_completed = 0
                                last_time = time.time()
                                speed_history.clear()

                            completed = json_response.get("completed", 0)
                            total = json_response.get("total", 0)

                            if total > 0:
                                # 计算下载速度
                                current_time = time.time()
                                time_diff = current_time - last_time
                                if time_diff >= 1:  # 每秒更新一次
                                    bytes_diff = completed - last_completed
                                    speed = bytes_diff / time_diff  # bytes per second

                                    # 存储当前速度
                                    count_sum += 1
                                    if count_sum > 5:
                                        speed_history.append(speed)

                                    # 检查速度是否异常
                                    avg_speed = None
                                    if len(speed_history) >= 10:
                                        avg_speed = sum(list(speed_history)[:-1]) / (len(speed_history) - 1)
                                        current_speed = speed_history[-1]

                                        if current_speed < 1024000 and avg_speed < 1536000:  # 当前速度小于1.2MB/s且平均速度小于1.5MB/s
                                            log_file.write('检测到下载速度过低，正在尝试重置下载...\n')
                                            log_file.flush()
                                            return False  # 返回False表示需要重新下载

                                        if current_speed < (avg_speed / 4) and avg_speed > 1024:  # 确保有足够的平均速度
                                            log_file.write('检测到下载速度异常或CF降速，正在尝试重置下载...\n')
                                            log_file.flush()
                                            return False  # 返回False表示需要重新下载

                                    # 转换速度单位
                                    speed_str = ""
                                    if speed < 1024:
                                        speed_str = "{:.2f} B/s".format(speed)
                                    elif speed < 1024 * 1024:
                                        speed_str = "{:.2f} KB/s".format(speed / 1024)
                                    else:
                                        speed_str = "{:.2f} MB/s".format(speed / (1024 * 1024))

                                    avg_speed_str = ""
                                    if not avg_speed is None:
                                        if avg_speed < 1024:
                                            avg_speed_str = "{:.2f} B/s".format(avg_speed)
                                        elif avg_speed < 1024 * 1024:
                                            avg_speed_str = "{:.2f} KB/s".format(avg_speed / 1024)
                                        else:
                                            avg_speed_str = "{:.2f} MB/s".format(avg_speed / (1024 * 1024))

                                    progress = (completed / total) * 100
                                    log_file.write('文件: {}, 下载进度: {:.2f}%, 平均速度: {}, 当前速度: {}\n'.format(
                                        download_tag,
                                        progress,
                                        avg_speed_str,
                                        speed_str
                                    ))
                                    log_file.flush()

                                    # 更新上次的数据
                                    last_completed = completed
                                    last_time = current_time
                        else:
                            log_file.write(status + '\n')
                            log_file.flush()

                # 下载完成后验证模型是否存在
                verify_cmd = "docker-compose -p {service_name} exec -it {service_name_} ollama list | grep {model_name}:{model_version}".format(
                    service_name=service_name.lower(),
                    service_name_=service_name,
                    model_name=model_name,
                    model_version=model_version
                )
                result = public.ExecShell(verify_cmd)[0]

                if model_name in result:
                    log_file.write('bt_successful\n')
                    return True
                else:
                    public.writeFile("/tmp/{model_name}:{model_version}.failed".format(
                        model_name=model_name,
                        model_version=model_version,
                    ), "failed")
                    log_file.write('bt_failed\n')
                    return False

        except Exception as e:
            # 发生异常时记录错误并标记失败
            with open(app_cmd_log, 'a') as log_file:
                log_file.write('下载失败: {}\n'.format(str(e)))
                log_file.write('bt_failed\n')
            public.writeFile("/tmp/{model_name}:{model_version}.failed".format(
                model_name=model_name,
                model_version=model_version,
            ), "failed")
            return False

    # 设置下载状态标记
    public.ExecShell("echo 'downloading' > /tmp/{model_name}:{model_version}.pl".format(
        model_name=model_name,
        model_version=model_version
    ))
    public.ExecShell("echo 'downloading' > /tmp/nocandown.pl")
    public.ExecShell("rm -f /tmp/{model_name}:{model_version}.failed".format(
        model_name=model_name,
        model_version=model_version,
    ))

    try:
        max_retries = 30
        retry_count = 0

        while retry_count < max_retries:
            if retry_count > 0:
                with open(app_cmd_log, 'a') as log_file:
                    log_file.write('\n正在进行第{}次重试...\n'.format(retry_count + 1))

            if start_download():
                break

            retry_count += 1
            time.sleep(3)  # 重试前等待3秒
            
    finally:
        # 清理状态文件
        public.ExecShell("rm -f /tmp/{model_name}:{model_version}.pl".format(
            model_name=model_name,
            model_version=model_version,
        ))
        public.ExecShell("rm -f /tmp/nocandown.pl") 
#!/usr/bin/bash
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# +-------------------------------------------------------------------
# | (11.2+版本)通用面板升级和修复脚本
# | 支持升级环境,升级面板,修复面板；环境相关由shell部分处理，面板升级沿用python脚本处理
# +-------------------------------------------------------------------
r'''ead' << EOF
EOF
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8


PANEL_PATH='/www/server/panel'
DOWNLOAD_URL='https://download.bt.cn'
PY_BIN=${PANEL_PATH}/pyenv/bin/python3

function run_py() {
    if [ -f "${PY_BIN}" ] &&  ${PY_BIN} --version >/dev/null 2>&1; then
        exec "${PY_BIN}" "${0}" "${@}"
    else
        echo "没有面板python环境，调用失败，请执行[ bash ${0} repair_pyenv ] 进行环境修复"
        exit 1
    fi
}

function get_local_version() {
    local common_file="$PANEL_PATH/class/common.py"
    if [ ! -f "$common_file" ]; then
        echo ""  # 文件不存在时返回空字符串
    else
        local version=$(grep -E '^\s+g.version\s*=\s*.*$' "$common_file" | sed -n "s/.*['\"]\(.*\)['\"].*/\1/p")
        echo $version
    fi
}

function ver_to_num() {
    local ver_str=$1
    if echo "$ver_str" | grep -Eq "^[0-9]+\.[0-9]+\.[0-9]+$"; then
        local ver_num=$(echo "$ver_str" | awk -F. '{printf "%03d%03d%03d", $1, $2, $3}')
        echo $ver_num
    else
        echo 0
    fi
}

# 获取最优下载节点
function get_node_url(){
  local down_host_cache=${PANEL_PATH}/data/down_url.pl
  if [ -f "${down_host_cache}" ];then
      DOWNLOAD_URL=$(cat ${down_host_cache})
      if [ ! -z "$DOWNLOAD_URL" ]; then
          echo "Download node: $DOWNLOAD_URL"
          return 0
      fi
	fi
	if [ -f "/www/node.pl" ];then
      DOWNLOAD_URL=$(cat /www/node.pl)
      echo "Download node: $DOWNLOAD_URL"
      return 0
	fi

	echo "Selected download node..."
	nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn https://na1-node.bt.cn https://jp1-node.bt.cn https://cf1-node.aapanel.com https://download.bt.cn);

  CN_CHECK=$(curl -sS --connect-timeout 10 -m 10 https://api.bt.cn/api/isCN)
  if [ "${CN_CHECK}" == "True" ];then
      nodes=(https://dg2.bt.cn https://download.bt.cn https://ctcc1-node.bt.cn https://cmcc1-node.bt.cn https://ctcc2-node.bt.cn https://hk1-node.bt.cn);
  else
      PING6_CHECK=$(ping6 -c 2 -W 2 download.bt.cn &> /dev/null && echo "yes" || echo "no")
      if [ "${PING6_CHECK}" == "yes" ];then
          nodes=(https://dg2.bt.cn https://download.bt.cn https://cf1-node.aapanel.com);
      else
          nodes=(https://cf1-node.aapanel.com https://download.bt.cn https://na1-node.bt.cn https://jp1-node.bt.cn https://dg2.bt.cn);
      fi
  fi

	tmp_file1=/dev/shm/net_test1.pl
	tmp_file2=/dev/shm/net_test2.pl
	[ -f "${tmp_file1}" ] && rm -f ${tmp_file1}
	[ -f "${tmp_file2}" ] && rm -f ${tmp_file2}
	touch $tmp_file1
	touch $tmp_file2
	for node in ${nodes[@]};
	do
      if [ "${node}" == "https://cf1-node.aapanel.com" ];then
          NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/1net_test|xargs)
      else
          NODE_CHECK=$(curl --connect-timeout 3 -m 3 2>/dev/null -w "%{http_code} %{time_total}" ${node}/net_test|xargs)
      fi

      RES=$(echo ${NODE_CHECK}|awk '{print $1}')
      NODE_STATUS=$(echo ${NODE_CHECK}|awk '{print $2}')
      TIME_TOTAL=$(echo ${NODE_CHECK}|awk '{print $3 * 1000 - 500 }'|cut -d '.' -f 1)
      if [ "${NODE_STATUS}" == "200" ];then
          if [ $TIME_TOTAL -lt 300 ];then
              if [ $RES -ge 1500 ];then
                  echo "$RES $node" >> $tmp_file1
              fi
          else
              if [ $RES -ge 1500 ];then
                  echo "$TIME_TOTAL $node" >> $tmp_file2
              fi
          fi

          i=$(($i+1))
          if [ $TIME_TOTAL -lt 300 ];then
              if [ $RES -ge 2390 ];then
                  break;
              fi
          fi
      fi
	done

	local node_url=$(cat $tmp_file1|sort -r -g -t " " -k 1|head -n 1|awk '{print $2}')
	if [ -z "$node_url" ];then
      node_url=$(cat $tmp_file2|sort -g -t " " -k 1|head -n 1|awk '{print $2}')
      if [ -z "$node_url" ];then
          node_url='https://download.bt.cn';
      fi
	fi
	rm -f $tmp_file1
	rm -f $tmp_file2
	DOWNLOAD_URL=$node_url
	echo ${DOWNLOAD_URL:8} > ${down_host_cache}
	echo "Download node: $DOWNLOAD_URL";
}

function upgrade_env() {
    local wget_bin=$(which wget)
    if [ ! -f "${wget_bin}" ]; then
        if command -v yum >/dev/null 2>&1; then
            yum install wget -y
        elif command -v apt-get >/dev/null 2>&1; then
            apt-get install wget -y
        fi
    fi
    local pyenv_url="${DOWNLOAD_URL}/install/pyenv/upgrade_py313.sh"
    local tmp_sh_path="/tmp/upgrade_py313.sh"
    rm -f "${tmp_sh_path}"
    if ! wget -O "${tmp_sh_path}" "${pyenv_url}" -T 30; then
        echo "python环境安装脚本下载失败: "${pyenv_url}""
        return 0
    fi

    if \cp -rpa "${tmp_sh_path}" "${PANEL_PATH}/script/upgrade_py313.sh" ; then
        echo "python环境安装脚本下载成功"
    fi

    echo "开始执行环境修复..."
    bash "${PANEL_PATH}/script/upgrade_py313.sh"
    if [ -f "${PY_BIN}" ] &&  ${PY_BIN} --version >/dev/null 2>&1; then
        echo "面板python3.13环境修复成功"
        return 0
    fi
    echo "面板python3.13环境修复失败"
    return 1
}

function main() {
    get_node_url
    if [ "$1" == "repair_pyenv" ] ; then
        if [[ "$(ver_to_num $(get_local_version))" <  "$(ver_to_num "11.3.0")" ]]; then
            echo "当前面板版本不支持环境修复，请升级面板到11.3.0以上版本后再执行环境修复"
            exit 1
        fi
        echo "开始执行环境修复..."
        upgrade_env
        exit 0
    fi
    run_py "$@"
}

main "$@"

':\
'''

# coding: utf-8
import os
import sys
import time
import json
import re
import hashlib
import shutil
import socket
import argparse
import subprocess

import psutil
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, List

# 全局变量
UPGRADE_MODEL = 'python'
LOG_PATH = '/tmp/upgrade_panel.log'
PANEL_PATH = '/www/server/panel'


@dataclass
class _ArgsData:
    action: str = 'upgrade_panel'
    version: str = ""
    skip_tool_check: bool = False
    package_file: str = ""
    lts: Optional[bool] = None
    dry_run: bool = False

    @property
    def is_upgrade(self) -> bool:
        return self.action == 'upgrade_panel'


args_data = _ArgsData()


class Version:

    def __init__(self, version_str: str):
        if version_str and "-lts" in version_str:
            self.is_lts = True
            version_str = version_str.replace("-lts", "")
        else:
            self.is_lts = False

        self.major, self.minor, self.micro = self.normal_version(version_str)
        self.checksum = ""
        if self.major > 9:
            self.is_lts = not bool(self.major % 2)

        self.update_time = 0

    @staticmethod
    def normal_version(version_str: str):
        if version_str:
            try:
                tmp = version_str.split(".")
                if len(tmp) < 3:
                    tmp.extend(["0"] * (3 - len(tmp)))

                return int(tmp[0]), int(tmp[1]), int(tmp[2])
            except:
                return 0, 0, 0
        else:
            return 0, 0, 0

    def __str__(self):
        return "{}.{}.{}".format(self.major, self.minor, self.micro)

    def __bool__(self):
        return (self.major, self.minor, self.micro) != (0, 0, 0)

    # 返回当前安装的版本信息 否为稳定版本 和 版本号
    @classmethod
    def get_now_version(cls) -> "Version":
        comm = read_file('{}/class/common.py'.format(PANEL_PATH))
        res = re.search(r'''g\.version\s*=\s*["'](?P<ver>.*)['"]''', comm)
        if res:
            version = res.group("ver")
        else:
            version = ""
        try:
            main_ver = int(version.split(".")[0])
        except:
            return cls("0.0.0")

        config_content = read_file('{}/class/config.py'.format(PANEL_PATH))
        res = re.search(r'''version_number":\s*int\("(?P<upt>.*)"\)''', config_content).group("upt")
        if not res or not res.isdigit():
            try:
                update_time = os.path.getmtime('{}/class/config.py'.format(PANEL_PATH))
            except:
                update_time = 0
        else:
            update_time = int(res)

        if main_ver < 9:
            v = cls(version)
            v.update_time = update_time
            return v
        else:
            v = cls(version)
            v.is_lts = (main_ver % 2 == 0)  # 偶数版本为LTS版本 10, 12等
            v.update_time = update_time
            return v

    # 获取远程版本信息
    @classmethod
    def get_remote_version(cls, is_lts=False):
        url = "https://www.bt.cn/api/panel/get_panel_version_v3"
        if is_lts:
            url = "https://www.bt.cn/api/panel/get_stable_panel_version_v3"
        try:
            info = http_get(url)
            info_dict = json.loads(info)
            if info_dict.get("OfficialVersionLatest", None) and info_dict["OfficialVersionLatest"]["version"]:
                return cls(info_dict["OfficialVersionLatest"]["version"])
            return cls(info_dict["OfficialVersion"]["version"])
        except:
            return cls("0.0.0")

    def get_check_sum(self):
        if not self:
            return
        self.checksum = ""
        self.update_time = 0

        url = "http://download.bt.cn/install/update/LinuxPanel{}-{}.pl".format(
            "Stable" if self.is_lts else "", self
        )
        try:
            info = http_get(url)
            info_dict = json.loads(info)
            self.checksum = info_dict["hash"]
            self.update_time = int(info_dict["update_time"])
        except:
            pass

    def show_dry_run(self):
        lv = self.get_now_version()
        msg = "当前面版版本：{}".format(lv)
        if lv.is_lts:
            msg += "-LTS (稳定版)"
        else:
            msg += " (正式版)"
        if lv.update_time:
            msg += "，更新时间：{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lv.update_time)))
        msg += "\n即将{}：{}".format("升级到" if args_data.is_upgrade else "修复为", self)
        if self.is_lts:
            msg += "-LTS (稳定版)"
        else:
            msg += " (正式版)"
        if self.update_time:
            msg += "，远程包打包时间：{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.update_time)))
        else:
            msg += "，该版本无已发布的包，无法更新"

        print(msg, flush=True)

    def download_panel_zip(self, filename: str) -> bool:
        if not self.checksum:
            print("WARNING: 获取版本信息检查信息异常，请注意检查！")

        down_url = "http://download.bt.cn/install/update/LinuxPanel{}-{}.zip".format(
            "Stable" if self.is_lts else "", self
        )
        # 下载主文件
        if not download_with_progress(down_url, filename):
            return False

        if os.path.getsize(filename) < 5 * 1024 * 1024:
            print_x('ERROR：下载更新包失败，请检查服务器网络状况')
            return False

        if self.checksum:
            hash_val = file_hash(filename)
            if hash_val != self.checksum:
                file_time = os.path.getmtime(filename)
                print_x('下载文件修改时间：{}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))))
                print_x('云端hash：{}'.format(self.checksum))
                print_x('本地hash：{}'.format(hash_val))
                print_x('ERROR：下载文件校验失败，可能原因：下载不完整。')
                return False
        return True

    def run_pre_script(self) -> bool:
        if not self:
            print_x("没有版本信息，无法获执行预处理脚本")
            return False

        down_url = "http://download.bt.cn/install/update/update_prep_script.sh"
        try:
            sh_content = http_get(down_url)
            sh_content = sh_content.replace("\r\n", "\n")
            if len(sh_content) < 10:
                print_x("ERROR：预处理脚本下载失败")
                return False
        except:
            print_x("ERROR：预处理脚本下载失败")
            return False

        prep_sh_path = "{}/script/update_prep_script.sh".format(PANEL_PATH)
        write_file(prep_sh_path, sh_content)
        shell = "bash {} {} {} prepare".format(prep_sh_path, self, self.is_lts)

        update_ready = False

        def print_and_check(log: str):
            nonlocal update_ready
            print_x(log, end="")
            if log.find("BT-Panel Update Ready") != -1:
                update_ready=True

        run_command_with_call_log(shell, print_and_check)
        if update_ready:
            print_x("预处理脚本执行成功")
            return True
        print_x("ERROR：预处理脚本执行失败")
        return False

    def run_after_script(self):
        prep_sh_path = "{}/script/update_prep_script.sh".format(PANEL_PATH)
        shell = "bash {} {} {} after".format(prep_sh_path, self, self.is_lts)
        update_ready = False

        def print_and_check(log: str):
            nonlocal update_ready
            print_x(log, end="")
            if log.find("BT-Panel Update Ready") != -1:
                update_ready=True

        run_command_with_call_log(shell, print_and_check)
        if update_ready:
            print_x("启动检查脚本执行成功")
        else:
            print_x("Warning：启动检查脚本执行失败")


# 工具类函数
# 获取文件哈希值
def file_hash(filename, hash_type="sha256") -> str:
    hash_func = getattr(hashlib, hash_type)()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


# 获取运行时Python版本
def runtime_python() -> Dict:
    return {
        'version': "{}.{}".format(sys.version_info.major, sys.version_info.minor),
        'path': os.path.realpath(sys.executable)
    }


def read_file(filename, mode='r') -> Optional[str]:
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    if not os.path.exists(filename):
        return None

    fp = None
    f_body = None
    try:
        fp = open(filename, mode)
        f_body = fp.read()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode, encoding="utf-8", errors='ignore')
                f_body = fp.read()
            except:
                try:
                    fp = open(filename, mode, encoding="GBK", errors='ignore')
                    f_body = fp.read()
                except:
                    return None
    finally:
        if fp and hasattr(fp, 'close') and not fp.closed:
            fp.close()
    return f_body


def write_file(filename, content, mode='w') -> bool:
    """
    写入文件内容
    @filename 文件名
    @content 内容
    @mode 打开方式
    return boolean
    """
    try:
        fp = open(filename, mode)
        fp.write(content)
        fp.close()
        return True
    except:
        return False


def exec_shell(cmd_string, timeout=None, shell=True, cwd=None, env=None) -> Tuple[str, str]:
    sub = None
    try:
        sub = subprocess.Popen(
            cmd_string,
            close_fds=True,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=env)

        if timeout:
            stdout, stderr = sub.communicate(timeout=timeout)
        else:
            stdout, stderr = sub.communicate()
        return stdout, stderr
    except subprocess.TimeoutExpired:
        # 确保sub已定义
        if sub is not None:
            sub.kill()
        return "", "Timed out"
    except Exception as e:
        return "", str(e)


def run_command_with_call_log(cmd, call_log):
    """
    执行命令并实时输出日志
    @param cmd 命令
    @param call_log 日志回调函数
    """
    if not callable(call_log):
        raise TypeError("call_log must be callable")

    # 执行命令
    try:
        import pty
        master, slave = pty.openpty()
        process = subprocess.Popen(
            cmd,
            close_fds=True,
            shell=True,
            stdout=slave,
            stderr=slave,
            text=True,
        )
        os.close(slave)

        while True:
            try:
                output = os.read(master, 1024).decode()
                if output:
                    call_log(output)
                if not output and process.poll() is not None:
                    break
            except OSError:
                break

        os.close(master)
        # 等待进程结束
        process.wait()

        # 检查返回码
        if process.returncode != 0:
            error_msg = "执行失败，返回码：{}".format(process.returncode)
            call_log(error_msg)
            return False

        return True

    except Exception as e:
        error_msg = str(e)
        call_log(error_msg)
        return False


# 字节单位转换
def to_size(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return "{:.2f} {}".format(size, units[unit_index])


def print_x(msg: str, end='\n'):
    """
    打印消息并记录日志
    """
    # 简化print_x函数，只保留基本的日志记录功能
    if end and not msg.endswith(end):
        msg += end
    write_file(LOG_PATH, msg, 'a+')
    print(msg, end="", flush=True)


# 网络相关函数
# 获取CURL路径
def curl_bin():
    c_bin = [
        shutil.which('curl'),
        '/usr/local/curl2/bin/curl',
        '/usr/local/curl/bin/curl',
        '/usr/local/bin/curl',
        '/usr/bin/curl'
    ]
    for cb in c_bin:
        if cb and not os.path.exists(cb) and os.access(cb, os.X_OK):
            return cb
    return "curl"


# 格式化CURL响应
def curl_format(req: str):
    match = re.search("(?P<header>(.*\r?\n)+)\r?\n", req)
    if not match:
        return req, {}, 0
    header_str = match.group()
    body = req.replace(header_str, '')
    status_code = 0
    header_dict = {}
    try:
        header = match.group('header').replace('\r\n', '\n')
        for line in header.split('\n'):
            if line.find('HTTP/') != -1:
                if line.find('Continue') != -1:
                    continue
                search_result = re.search(r'HTTP/[\d.]+\s(\d+)', line)
                if search_result:
                    status_code = int(search_result.groups()[0])
            elif line.find(':') != -1:
                key, value = line.split(':', 1)
                header_dict[key.strip()] = value.strip()
        if status_code == 100:
            status_code = 200
    except:
        if body:
            status_code = 200
        else:
            status_code = 0
    return body, header_dict, status_code


# 替换下载节点
def get_home_node(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain not in ['www.bt.cn', 'api.bt.cn', 'download.bt.cn']:
        return url
    if os.path.isfile("{}/data/down_url.pl".format(PANEL_PATH)):
        host = read_file("{}/data/down_url.pl".format(PANEL_PATH))
        if host and host.strip() and domain == 'download.bt.cn':
            return parsed_url._replace(netloc=host.strip()).geturl()

    node_file = '{}/data/node_url.pl'.format(PANEL_PATH)
    if not os.path.exists(node_file):
        return url
    file_content = read_file(node_file)
    if not file_content:
        return url
    try:
        node_info = json.loads(file_content)
    except:
        return url

    taget_host = None
    for host_key, node_key in (('www.bt.cn', 'www-node'), ('api.bt.cn', 'api-node'), ('download.bt.cn', 'down-node')):
        if host_key == domain:
            taget_host = node_info.get(node_key, {}).get('url')
            break
    if not taget_host:
        return url

    return parsed_url._replace(netloc=taget_host).geturl()


# httpGet请求
def http_get(url, timeout=(3, 6), headers=None):
    """
    @name httpGet请求
    """
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"}
    url = get_home_node(url)
    try:
        import urllib.request
        # 确保url是字符串类型
        if url:
            req = urllib.request.Request(url, method='GET', headers=headers)
            response = urllib.request.urlopen(req, timeout=timeout[1])
            if response.status == 200:
                return response.read().decode('utf-8')
            return ""
    except:
        if isinstance(timeout, tuple):
            timeout = timeout[1]
        headers_str = ""
        if headers:
            for k, v in headers.items():
                headers_str += " -H '{}: {}'".format(k, v)
        out, err = exec_shell("{} -kisS --connect-timeout {} {} {}".format(curl_bin(), timeout, headers_str, url))
        if err:
            print_x(err)
            return ""
        r_body, r_headers, r_status_code = curl_format(out)
        if r_status_code != 200:
            return ""
        return r_body


# 工具检查相关函数
def check_tools(skip_check=False):
    """
    @name 检查必要工具
    @param skip_check 是否跳过检查
    """
    if skip_check:
        print_x('已跳过工具检查')
        return True

    tools = ['wget', 'unzip']
    missing_tools = []

    for tool in tools:
        # 检查工具是否存在
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        print_x('ERROR：缺少必要工具: {}'.format(', '.join(missing_tools)))
        print_x('请先安装缺少的工具再执行升级')
        return False

    print_x('必要工具检查通过: {}'.format(', '.join(tools)))
    return True


# 下载相关函数
def download_with_progress(url, filename, max_retries=3):
    """
    @name 下载文件并显示进度
    @param url 下载地址
    @param filename 保存文件名
    @param max_retries 最大重试次数
    @param timeout 超时时间(秒)
    """
    url = get_home_node(url)

    cmd = "wget -O '{}' '{}' --no-check-certificate -T 30 -t 3 --progress=bar:force:noscroll".format(filename, url)
    for retry_count in range(max_retries):
        if retry_count > 0:
            print_x('下载失败，正在进行第{}次重试...'.format(retry_count))
            time.sleep(1)  # 重试前等待2秒
            # 清理可能的残留文件
            if os.path.exists(filename):
                os.remove(filename)
        if retry_count >= 1:
            cmd = cmd.replace('download.bt.cn', 'download-dg-main.bt.cn')

        download_success = run_command_with_call_log(cmd, lambda line: print_x(line, end=""))

        # 如果下载成功，跳出重试循环
        if download_success:
            print_x('文件下载成功：{}'.format(filename))
            return True

    # 所有重试都失败
    print_x('ERROR：下载文件{}失败，已重试{}次，请检查网络连接或手动下载文件'.format(filename, max_retries))
    return False


# 拷贝的文件列表
def copy_dir(f_list: List[str], src_dir: str, dst_dir: str, per_str=""):
    """
    @name 备份面板
    @param f_list 需要拷贝的文件列表（不包含根目录）['task.py','config/databases.json']
    @param src_dir 源目录，如：/tmp/panel
    @param dst_dir 目标目录，如：/tmp/panel_bak
    """
    dst_dir = dst_dir.rstrip('/')
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    f_log = "%s {:>9}" % per_str + " .........." * 3 + " {:>6.2f}%     {}"
    file_num = len(f_list)
    for idx, f_name in enumerate(f_list):
        if idx % 504 == 0:
            num_text = "{}/{}".format(idx, file_num)
            print_x(f_log.format(num_text, round(idx / file_num * 100, 2), os.path.basename(f_name)))

        # 拷贝文件
        s_file = os.path.join(src_dir, f_name)
        if not os.path.isfile(s_file):
            continue
        d_file = os.path.join(dst_dir, f_name)
        root_dir = os.path.dirname(d_file)
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        try:
            shutil.copyfile(s_file, d_file)
        except:
            print_x('ERROR：拷贝文件{}失败'.format(s_file))
            return False

    print_x(f_log.format("{}/{}".format(file_num, file_num), 100.00, ""))
    return True


def check_hash(f_list, src_dir, dst_dir):
    """
    @name 校验文件
    """
    res = []
    for f in f_list:
        s_file = os.path.join(src_dir, f)
        if not os.path.exists(s_file):
            continue
        d_file = os.path.join(dst_dir, f)
        if not os.path.exists(d_file):
            if d_file.endswith('check_files.py'):  # 不清楚check_files.py含义，继承策略
                continue
            print_x('文件 {} 更新失败..'.format(d_file))
            res.append(s_file)
            continue

        # 校验文件hash
        if file_hash(s_file) != file_hash(d_file):
            f_name = os.path.basename(s_file)
            # 特定文件验证2次
            if f_name in ['BT-Panel', 'BT-Task', 'check_files.py']:
                try:
                    shutil.copyfile(s_file, d_file)
                except:
                    pass
                if file_hash(s_file) == file_hash(d_file):
                    continue
            print_x('文件 {} 更新失败...'.format(d_file))
            res.append(f)
    return res


def unzip(zipfile, dst_dir):
    """
    解压文件
    """
    sh = "unzip -q -o {} -d {}".format(zipfile, dst_dir)
    return run_command_with_call_log(sh, print_x)


# 检查进程是否存在
def process_exists(process_name):
    try:
        pids = psutil.pids()
        for pid in pids:
            if pid == os.getpid():
                continue
            try:
                p = psutil.Process(pid)
                if p.name() == process_name:
                    return True
            except:
                pass
    except:
        pass
    return False


# 面板相关函数
def get_panel_login_url():
    port = 8888
    try:
        port_file = '{}/data/port.pl'.format(PANEL_PATH)
        port_content = read_file(port_file)
        if port_content:
            return int(port_content.strip())
    except:
        pass

    login_path = 'login'
    try:
        auth_file = '{}/data/admin_path.pl'.format(PANEL_PATH)
        auth_content = read_file(auth_file)
        if auth_content:
            login_path = auth_content.strip('/').lstrip('/')
    except:
        pass

    schema = 'https' if os.path.exists("{}/data/ssl.pl".format(PANEL_PATH)) else 'http'

    return '{}://127.0.0.1:{}/{}'.format(schema, port, login_path)


# 检测面板是否正常
def check_panel_status():
    url = get_panel_login_url()
    panel_state = False
    start_time = time.time()
    while True:
        try:
            res = http_get(url=url)
            print('面板状态：{}'.format(res))
            if res:
                panel_state = True
                break
        except:
            pass
        if time.time() - start_time > 15:
            break
        time.sleep(0.5)

    if panel_state:
        return True

    # 检测到BT-Panel 和 BT-Task 进程存在，则认为面板已经启动
    for pname in ['BT-Panel', 'BT-Task']:
        if process_exists(pname):
            panel_state = True
            break

    if panel_state:
        return True
    else:
        print_x('ERROR：面板启动失败，请检查面板是否正常启动')
        return False


# 清理临时文件
def clear_tmp():
    try:
        tmp_panel_dirs = [f for f in os.listdir('/tmp') if f.startswith('panel_')]
        for dir_name in tmp_panel_dirs:
            dir_path = os.path.join('/tmp', dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
    except:
        pass

    try:
        panel_bak_dirs = [f for f in os.listdir('/www/server') if f.startswith('panel_bak_')]
        for dir_name in panel_bak_dirs:
            dir_path = os.path.join('/www/server', dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
    except:
        pass

    try:
        if os.path.exists('/tmp/panel.zip'):
            os.remove('/tmp/panel.zip')
    except:
        pass

    # free_site_total
    try:
        last_install_file = "{}/data/free_site_total.pl".format(PANEL_PATH)
        if os.path.exists(last_install_file):
            os.remove(last_install_file)
    except:
        pass


def update_panel_files(n_list, src_dir, retry_count=3, start_func=None):
    """
    @name 更新面板文件(独立函数，避免多级嵌套)
    """
    for i in range(retry_count):
        if copy_dir(n_list, src_dir, PANEL_PATH, '正在更新：'):
            print_x('正在校验面板文件完整性...')

            res = check_hash(n_list, src_dir, PANEL_PATH)
            if not res:
                print_x('正在重启面板...')
                if start_func and callable(start_func):
                    start_func()
                print_x('Stopping Bt-Panel ...') # <- 用于触发面板上终端的重载操作
                exec_shell('bash {}/init.sh restart'.format(PANEL_PATH))
                time.sleep(1)

                print_x('正在检测面板运行状态...')
                if check_panel_status():
                    print_x('正在清理旧残留文件...')
                    print_x('Success：面板更新成功')
                    return True
            else:
                if i == retry_count - 1:
                    for f in res:
                        dsc_file = os.path.join(PANEL_PATH, f)
                        print_x(dsc_file)
                    print_x('ERROR：校验失败，存在【{}】个文件无法更新，正在恢复备份。'.format(len(res)))
                else:
                    print_x('正在第【{}】重试更新面板，正在尝试解锁文件...'.format(i + 1))
                    for f in res:
                        dsc_file = os.path.join(PANEL_PATH, f)
                        exec_shell('chattr -a -i {}'.format(dsc_file))

    return False


def install_with_pkg_file(package_file: str, start_func=None):
    if not package_file:
        print_x('ERROR：升级包文件错误')
        return False
    tmp_dir = '/tmp/panel_{}'.format(str(int(time.time())))
    print_x('正在解压【{}】...'.format(package_file))

    unzip(package_file, tmp_dir)
    src_dir = tmp_dir + '/panel/'
    if not os.path.exists(src_dir):
        print_x('ERROR：解压失败')
        return

    # 使用os.walk遍历目录树, 收集会更新的文件列表
    f_list = []
    for root, _, filenames in os.walk(src_dir):
        for filename in filenames:
            # 构造相对路径
            full_path = os.path.join(root, filename)
            relative_path = full_path.replace(src_dir, '').lstrip('/')
            f_list.append(relative_path)

    if len(f_list) < 100:
        print_x('ERROR：解压失败, 文件数量异常！')
        return False

    bak_dir = PANEL_PATH.replace('panel', 'panel_bak_{}'.format(int(time.time())))
    if copy_dir(f_list, PANEL_PATH, bak_dir, '正在备份：'):
        print_x("备份成功...")
        if not update_panel_files(f_list, src_dir,start_func=start_func):
            # 恢复备份
            copy_dir(f_list, bak_dir, PANEL_PATH, "正在恢复备份文件：")
            print_x('操作失败，已成功恢复备份...')
    clear_tmp()
    return


def run() -> int:
    if args_data.package_file and os.path.exists(args_data.package_file):
        print_x('正在使用指定的升级包文件: {}'.format(args_data.package_file))
        install_with_pkg_file(args_data.package_file)
        return 1

    if args_data.action == 'repair_panel':
        v = Version.get_now_version()
        if v.major <= 9:
            print_x('ERROR：当前面板版本低于9.0.0，不在支持修复，请使用[ upgrade_panel ]进行升级')
            return 1
        if not v:
            print_x('ERROR：获取当前面板版本失败，尝试使用请使用[ upgrade_panel ]进行升级')
            return 1
    elif args_data.action == 'upgrade_panel':
        is_lts, v = args_data.lts, Version(args_data.version)
        if not v:
            v = Version.get_remote_version(is_lts)
            if not v:
                print_x('ERROR：获取最新版本失败，请检查网络连接')
                return 1

        if v.major <= 9:
            print_x('ERROR：不在支持升级或安装9.0.0之下面板')
            return 1
        # print('正在检查版本：{}'.format(v), is_lts)
        if is_lts is not None and v.is_lts != is_lts:
            print_x('ERROR：指定版本【{}】不是{}版,参数冲突'.format(v, 'LTS' if is_lts else '正式'))
            return 1

    else:
        print_x('ERROR：参数错误')
        return 1

    v.get_check_sum()
    v.show_dry_run()  # 展示升级信息
    if args_data.dry_run:  # 如果仅展示信息，则返回
        return 0 if v.checksum  else 1   # 如果获取校验信息成功则退出信号码为0

    if not v.checksum:
        print_x('ERROR：无远程版本校验信息')
        return 1

    if not v.run_pre_script():
        print_x('ERROR：预处理失败，无法执行升级，请检查网络连接')
        return 1

    tmp_file = '/tmp/panel.zip'
    if not v.download_panel_zip(tmp_file):
        return 1
    if not os.path.exists(tmp_file):
        print_x('ERROR：下载失败')
        return 1

    action_text = "修复" if args_data.action == 'repair_panel' else "升级"
    print_x('下载包文件: {} 成功，将进行{}...'.format(tmp_file,action_text))
    install_with_pkg_file(tmp_file, start_func=v.run_after_script)
    return 0


def main():
    try:
        if os.path.exists('/tmp/upgrade_panel.log'):
            write_file('/tmp/upgrade_panel.log', '')
    except:
        pass

    # run_python = runtime_python()
    # if not run_python["path"].find('/www/server/panel') >= 0:
    #     print_x(
    #         'ERROR：当前使用的Python环境不是官方环境，请使用[ btpython /www/server/panel/pyenv/bin/python3 ]进行操作.')
    #     return

    # 参数解析
    parser = argparse.ArgumentParser(description='宝塔面板升级脚本')
    parser.add_argument('action', nargs='?', default='upgrade_panel', help='操作类型: upgrade_panel|repair_panel|repair_pyenv')
    parser.add_argument('version', nargs='?', default=None, help='指定版本号')
    parser.add_argument('--skip-tool-check', action='store_true', help='跳过工具检查')
    parser.add_argument('--dry-run', action='store_true', help='仅展示计划，不实际执行')
    parser.add_argument('--lts', type=str, default="none", help='指定是否使用LTS版: none|true|false，默认none跟随版本号')
    parser.add_argument('--package-file', type=str, default="", help='指定本地升级包文件路径')

    args = parser.parse_args()
    clear_tmp()
    args_data.skip_tool_check = bool(args.skip_tool_check)
    if args.lts == "true":
        args_data.lts = True
    elif args.lts == "false":
        args_data.lts = False
    else:
        args_data.lts = None
    args_data.package_file = args.package_file
    args_data.version = args.version
    args_data.action = args.action
    args_data.dry_run = bool(args.dry_run)

    if args_data.action not in ('upgrade_panel', 'repair_panel'):
        print_x('ERROR：命令参数错误')
        return
    if args_data.package_file and not os.path.exists(args_data.package_file):
        print_x('ERROR：指定的升级包文件不存在')
        return

    if not args_data.dry_run:
        disk = psutil.disk_usage(PANEL_PATH)
        print_x('正在检测磁盘空间...')
        print_x('磁盘剩余【{}】'.format(to_size(disk.free)))

        if disk.free < 100 * 1024 * 1024:
            print_x('ERROR：磁盘空间不足 [100 MB]，无法继续操作.')
            return

    # 检查必要工具
    if not args_data.dry_run and not check_tools(args.skip_tool_check):
        return

    exit(run())


if __name__ == '__main__':
    main()

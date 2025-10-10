#coding: utf-8
import os,sys,time,json,re, psutil,hashlib,shutil,socket
from urllib.parse import urlparse, urlunparse

upgrade_model = 'python'
logPath = '/tmp/upgrade_panel.log'
try:
    import subprocess, tempfile
    panelPath = '/www/server/panel/'
    os.chdir(panelPath)
    sys.path.insert(0, panelPath + "class/")

    import public,http_requests
except:
    upgrade_model = 'shell'


def get_home_node(url):
    """
    @name 获取下载节点
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain in ['www.bt.cn', 'api.bt.cn', 'download.bt.cn']:
            if parsed_url.path in ['/api/index']:
                return url
            sfile = '{}/data/node_url.pl'.format(panelPath)
            node_info = json.loads(readFile(sfile))
            if domain == 'www.bt.cn':
                if not node_info['www-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['www-node']['url']))
            elif domain == 'api.bt.cn':
                if not node_info['api-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['api-node']['url']))
            elif domain == 'download.bt.cn':
                if not node_info['down-node']:
                    return url
                return urlunparse(parsed_url._replace(netloc=node_info['down-node']['url']))
    except:
        pass
    return url

def get_error_info():
    import traceback
    errorMsg = traceback.format_exc()
    return errorMsg

def GetRandomString(length):
    """
       @name 取随机字符串
       @author hwliang<hwl@bt.cn>
       @param length 要获取的长度
       @return string(length)
    """
    from random import Random
    strings = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    chrlen = len(chars) - 1
    random = Random()
    for i in range(length):
        strings += chars[random.randint(0, chrlen)]
    return strings

def get_file_hash(filename, hash_type="sha256"):
    hash_func = getattr(hashlib, hash_type)()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def print_x(msg):
    if msg.find('ERROR：') != -1 or msg.find('Success：') != -1:

        public.writeFile(logPath, '{}\n'.format(msg),'a+')
        status = False
        if msg.find('Success：') != -1:
            status = True
        data = {
            'status': status,
            'msg': msg,
            'data': public.GetNumLines(logPath,100)
        }
        public.writeFile(logPath, json.dumps(data))
    else:
        try:
            logs = public.readFile(logPath)
            data = json.loads(logs)
            data['data'] = '{}\n{}'.format(data['data'],msg)

            public.writeFile(logPath, json.dumps(data))
        except:
            public.writeFile(logPath, '{}\n'.format(msg),'a+')
    print(msg)

def ExecShell(cmdstring, timeout=None, shell=True, cwd=None, env=None, user=None):
    a = ''
    e = ''

    preexec_fn = None
    tmp_dir = '/dev/shm'
    try:
        rx = GetRandomString(32)
        succ_f = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_succ', prefix='btex_' + rx, dir=tmp_dir)
        err_f = tempfile.SpooledTemporaryFile(max_size=4096, mode='wb+', suffix='_err', prefix='btex_' + rx, dir=tmp_dir)
        sub = subprocess.Popen(cmdstring, close_fds=True, shell=shell, bufsize=128, stdout=succ_f, stderr=err_f, cwd=cwd, env=env, preexec_fn=preexec_fn)
        if timeout:
            s = 0
            d = 0.01
            while sub.poll() == None:
                time.sleep(d)
                s += d
                if s >= timeout:
                    if not err_f.closed: err_f.close()
                    if not succ_f.closed: succ_f.close()
                    return 'Timed out'
        else:
            sub.wait()

        err_f.seek(0)
        succ_f.seek(0)
        a = succ_f.read()
        e = err_f.read()
        if not err_f.closed: err_f.close()
        if not succ_f.closed: succ_f.close()
    except:
        return '', get_error_info()
    try:
        # 编码修正
        if type(a) == bytes: a = a.decode('utf-8')
        if type(e) == bytes: e = e.decode('utf-8')
    except:
        a = str(a)
        e = str(e)

    return a, e

def readFile(filename, mode='r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    if not os.path.exists(filename): return False
    fp = None
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
                    return False
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body

def get_request_iptype( get=None):
    '''
        @name 获取云端请求线路
        @author hwliang<2022-02-09>
        @return auto/ipv4/ipv6
    '''

    v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
    if not os.path.exists(v4_file): return 'auto'
    iptype = public.readFile(v4_file).strip()
    if not iptype: return 'auto'
    if iptype == '-4': return 'ipv4'
    return 'ipv6'

#取CURL路径
def _curl_bin():

    _ip_type = get_request_iptype()
    c_bin = ['/usr/local/curl2/bin/curl','/usr/local/curl/bin/curl','/usr/local/bin/curl','/usr/bin/curl']
    curl_bin = 'curl'
    for cb in c_bin:
        if os.path.exists(cb): curl_bin = cb

        v4_file = '{}/data/v4.pl'.format(panelPath)
        v4_body = readFile(v4_file)
        if v4_body: v4_body = v4_body.strip()

        if not _ip_type in v4_body:
            if _ip_type == 'ipv4':
                v4_body = '-4'
            else:
                v4_body = '-6'
        curl_bin += ' {}'.format(v4_body)
    return curl_bin
def _curl_format(req):
    match = re.search("(.|\n)+\r\n\r\n",req)
    if not match: return req,{},0
    tmp = match.group()
    body = req.replace(tmp,'')
    try:
        for line in tmp.split('\r\n'):
            if line.find('HTTP/') != -1:
                if line.find('Continue') != -1: continue
                status_code = int(re.search('HTTP/[\d\.]+\s(\d+)',line).groups()[0])
                break
        if status_code == 100:
            status_code = 200
    except:
        if body:
            status_code = 200
        else:
            status_code = 0
    return body,tmp,status_code



def download_log(filename,log_file):
    """
    @name 解析wget下载日志
    """
    total = 0
    if  os.path.exists(log_file):

        f = open(log_file, 'r')
        head = f.read(4096)
        content_length = re.findall(r"Length:\s+(\d+)", head)
        if content_length:
            total = int(content_length[0])

        speed_tmp = public.ExecShell("tail -n 2 {}".format(log_file))[0]
        speed_total = re.findall(
            r"([\d\.]+[BbKkMmGg]).+\s+(\d+)%\s+([\d\.]+[KMBGkmbg])\s+(\w+[sS])", speed_tmp)

        if speed_total:
            speed_total = speed_total[0]
            used = speed_total[0]
            if speed_total[0].lower().find('k') != -1:
                used = public.to_size(
                    float(speed_total[0].lower().replace('k', '')) * 1024)
                u_time = speed_total[3].replace(
                    'h', '小时').replace('m', '分').replace('s', '秒')
            data = {'name': '下载文件【{}】'.format(os.path.basename(filename)), 'total': total, 'used': used, 'pre': speed_total[1], 'speed': speed_total[2], 'time': u_time}
            print_x('{}  {} .......... .......... ..........  {}   速度:{}/s   剩余 {} '.format(data['name'], data['used'],public.to_size(data['total']), data['speed'], data['time']))

def download_file(url, filename, max_retries=2):
    """
    @name 下载文件
    @param max_retries 最大重试次数
    """
    url = get_home_node(url)
    
    for retry_count in range(max_retries):
        if retry_count > 0:
            print_x('下载失败，正在进行第{}次重试...'.format(retry_count))
            time.sleep(2)  # 重试前等待2秒
            # 清理可能的残留文件
            if os.path.exists(filename):
                os.remove(filename)
        
        success_log = '/tmp/down.panel'
        os.system('rm -f {}'.format(success_log))
        tmp_file = '/tmp/down_panel.log'
        shell = "nohup wget -O '{}' '{}' --no-check-certificate  -T 15 -t 2 -d &>{} && echo 'True' > {} &".format(filename, url, tmp_file, success_log)
        if retry_count >= 1:
            shell = shell.replace('download.bt.cn', 'download-dg-main.bt.cn')
        public.ExecShell(shell)

        total = 0
        download_success = False
        
        while True:
            total += 0.1
            time.sleep(0.1)
            download_log(filename, tmp_file)
            
            if total > 300:
                print_x('ERROR：下载文件{}失败，5分钟超时'.format(filename))
                break  # 跳出内层循环，进入下一次重试

            if not os.path.exists(filename):
                continue

            if os.path.exists(success_log):
                download_success = True
                break  # 下载成功，跳出内层循环

        os.system('rm -f {}'.format(success_log))
        
        # 如果下载成功，跳出重试循环
        if download_success:
            print_x('文件下载成功：{}'.format(filename))
            return True
    
    # 所有重试都失败
    print_x('ERROR：下载文件{}失败，已重试{}次，请检查连接download.bt.cn是否正常'.format(filename, max_retries))
    return False

def check_down_res(filename):
    """
    @name 检测是否下载完成
    """
    pass



def httpGet(url, timeout=(3, 6),headers= {}):
    """
    @name httpGet请求
    """
    url = get_home_node(url)
    if upgrade_model == 'python':
        return public.HttpGet(url, timeout,headers)
    else:
        if isinstance(timeout,tuple):
            timeout = timeout[1]
        result = ExecShell("{} -k -sS -i --connect-timeout {} {}  2>&1".format(_curl_bin(),timeout,url))[0]
        r_body,r_headers,r_status_code = _curl_format(result)
        return r_body

def get_file_list(path, flist,root_dir):
    """
    递归获取目录所有文件列表
    @path 目录路径
    @flist 返回文件列表
    """
    if not os.path.exists(path):
        return
    files = os.listdir(path)
    for file in files:
        file = file.replace('//','').lstrip('/')
        if os.path.isdir(path + '/' + file):
            get_file_list(path + '/' + file, flist,root_dir)
        else:
            sfile = (path + '/' + file).replace(root_dir,'')
            flist.append(sfile)


def copy_dir(f_list ,src_dir,dst_dir,title= None):
    """
    @name 备份面板
    @param f_list 需要拷贝的文件列表（不包含根目录）['task.py','config/databases.json']
    @param src_dir 源目录，如：/tmp/panel
    @param dst_dir 目标目录，如：/tmp/panel_bak
    """
    try:
        dst_dir = dst_dir.rstrip('/')
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        i = 0
        src_usd = 0
        max = len(f_list)

        for f in f_list:
            try:
                #计算进度
                i += 1
                usd  = int(i / max * 100)
                if usd > src_usd:
                    src_usd = usd
                    if title:
                        print_x('{} {}/{} .......... .......... ..........  {} %     {}'.format(title,i,max,src_usd,os.path.basename(f)))

                #拷贝文件
                if f == '/': continue
                sfile = '{}/{}'.format(src_dir.rstrip('/'),f)
                if not os.path.exists(sfile):
                    continue
                dfile = '{}/{}'.format(dst_dir,f)
                root_dir = os.path.dirname(dfile)
                if not os.path.exists(root_dir): os.makedirs(root_dir)

                if os.path.isfile(sfile):
                    shutil.copyfile(sfile,dfile)
            except:
                print(dfile,public.get_error_info())
                pass
        if max == i:
            return True
    except: pass

    return False

def check_hash(f_list,src_dir,dst_dir):
    """
    @name 校验文件
    """
    res = []

    for f in f_list:
        f = f.lstrip('/')

        sfile = '{}/{}'.format(src_dir,f).replace('//','/')
        if not os.path.exists(sfile):
            continue
        dfile = '{}/{}'.format(dst_dir,f).replace('//','/')
        if not os.path.exists(dfile):
            fname = os.path.basename(sfile)
            if fname in ['check_files.py']:
                continue
            print_x('文件 {} 更新失败..'.format(dfile))
            res.append(sfile)
            continue

        def check_file_hash(sfile,dfile):
            s_hash = get_file_hash(sfile)
            d_hash = get_file_hash(dfile)

            if  d_hash != s_hash:
                return False
            return True

        if not check_file_hash(sfile,dfile):
            fname = os.path.basename(sfile)
            try:
                #特定文件验证2次
                if fname in ['BT-Panel','BT-Task','check_files.py']:
                    shutil.copyfile(sfile,dfile)
                    if check_file_hash(sfile,dfile):
                        continue
            except: pass
            print_x('文件 {} 更新失败...'.format(dfile))
            res.append(f)
    return res



def check_panel_url():
    """
    @name 检测面板是否正常
    """
    auth_path = 'login'
    try:
        auth_file = '{}/data/admin_path.pl'.format(panelPath)
        if os.path.exists(auth_file):
            auth_path = public.readFile(auth_file).strip('/')
    except:pass
    _http = 'https' if os.path.exists("/www/server/panel/data/ssl.pl") else 'http'

    port = public.get_panel_port()

    status = public.check_port_stat(port)
    if not status:
        print_x('检测到面板没有启动，正在启动面板')
        public.ExecShell('/etc/init.d/bt reload')
        time.sleep(3)

    url = '{}://{}:{}/{}'.format(_http,'127.0.0.1',public.get_panel_port(),auth_path)
    panel_state = False
    total_time = 0
    while True:
        try:
            res = httpGet(url=url,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'})
            if res:
                panel_state = True
                break
        except:pass
        if total_time > 15:
            break

        total_time += 1
        time.sleep(1)

    if not panel_state:
        # 检测到BT-Panel 和 BT-Task 进程存在，则认为面板已经启动
        for pname in ['BT-Panel','BT-Task']:
            if public.process_exists(pname):
                panel_state = True
                break

    if not panel_state:
        print_x('ERROR：面板启动失败，请检查面板是否正常启动')
        # 检测自己的进程，并杀掉
        pname = os.path.basename(__file__)
        if public.process_exists(pname):
            public.ExecShell('pkill -9 {}'.format(pname))

    return panel_state


def unzip(zipfile,dst_dir):
    ExecShell('unzip -o {} -d {}'.format(zipfile,dst_dir))
    if not os.path.exists(dst_dir):
        return False
    return True


def download_panel(ver,tmp_file,info = None):
    """
    @下载面板文件
    """
    down_url = 'http://download.bt.cn/install/update/LinuxPanel-{}.zip'.format(ver)
    download_file(down_url, tmp_file)

    if not "hash" in info or not "update_time" in info:
        down_url = 'http://download.bt.cn/install/update/LinuxPanel-{}.pl'.format(ver)
        if os.path.exists("/tmp/LinuxPanel-{}.pl".format(ver)):
            os.remove("/tmp/LinuxPanel-{}.pl".format(ver))
        download_file(down_url, "/tmp/LinuxPanel-{}.pl".format(ver))
        try:
            pl_info = json.loads(readFile("/tmp/LinuxPanel-{}.pl".format(ver)))
        except:
            print_x('ERROR：下载校验文件失败，可能原因：下载不完整。')
            return False

        info['hash'] = pl_info['hash']
        info['update_time'] = pl_info['update_time']

    if os.path.getsize(tmp_file) < 5 * 1024 * 1024:
        print_x('ERROR：下载更新包失败，请检查服务器网络状况')
        return False

    if info:
        hash_val = get_file_hash(tmp_file)
        if hash_val.strip() != info['hash'].strip():
            file_time = os.path.getmtime(tmp_file)
            print_x('下载文件修改时间：{}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))))
            print_x('云端hash：{}'.format(info['hash']))
            print_x('本地hash：{}'.format(hash_val))
            print_x('ERROR：下载文件校验失败，可能原因：下载不完整。')

            return  False
    return True

def get_panel_info(v = None):
    """
    @name 获取面板版本
    """
    try:
        if v:
            if v.strip() == 'lts':
                info = httpGet('https://www.bt.cn/api/panel/get_panel_version?v=lts')
            else:
                info = json.dumps({
                    "version": v,
                })
        else:
            info = httpGet('https://www.bt.cn/api/panel/get_panel_version')
        if not info:
            return {"version": v}
        return json.loads(info)
    except:pass
    return {"version": v}

def clear_tmp():
    """
    @name 清理临时文件
    """
    os.system('rm -rf /tmp/panel_*')
    os.system('rm -rf /www/server/panel_bak_*')
    os.system('rm -rf /tmp/panel.zip')


def repair_panel(v = None):
    """
    @name 修复面板(对外接口)
    """
    public.writeFile(logPath, "")
    print_x('正在获取面板版本...')

    info = get_panel_info(v)
    if not info:
        print_x('ERROR：获取面板版本失败，请检查网络连接')
        return False
    if not info['version']:
        print_x('ERROR：获取面板版本失败，请检查网络连接')
        return False
    print_x('面板最新版本【{}】'.format(info['version']))
    db_repair = '{}/data/db/update'.format(panelPath)
    if os.path.exists(db_repair):
        #设置为3，会执行一次修复数据库
        public.writeFile(db_repair,'3')

    if upgrade_model == 'shell':
        url = get_home_node('http://download.bt.cn/install/update6.sh')
        os.system('curl -k {}|bash'.format(url))
        return

    tmp_file = '/tmp/panel.zip'
    print_x('正在下载【panel-{}.zip】...'.format(info['version']))
    if download_panel(info['version'],tmp_file,info):
        tmp_dir = '/tmp/panel_{}'.format(info['version'])
        print_x('正在解压【{}】...'.format(info['version']))
        if unzip(tmp_file,tmp_dir):

            f_list = []
            src_dir = tmp_dir + '/panel/'
            get_file_list(tmp_dir,f_list,src_dir)

            bak_dir = panelPath.replace('panel','panel_bak_{}'.format(int(time.time())))
            if copy_dir(f_list,panelPath,bak_dir,'正在备份：'):
                def update_panel_files(n_list,src_dir,retry_count = 1):
                    """
                    @name 更新面板文件
                    """
                    if copy_dir(n_list,src_dir,panelPath,'正在更新：'):
                        print_x('正在校验面板文件完整性...')

                        res = check_hash(n_list,src_dir,panelPath)
                        if not res:
                            print_x('正在重启面板...')
                            os.system('/etc/init.d/bt restart')

                            print_x('正在检测面板运行状态...')
                            if check_panel_url():
                                print_x('正在清理旧残留文件...')
                                print_x('Success：面板更新成功，已成功升级到【{}】'.format(info['version']))

                                clear_tmp()
                                return True
                        else:
                            if retry_count < 3:
                                print_x('正在第【{}】重试更新面板，正在尝试解锁文件...'.format(retry_count + 1))
                                for f in res:
                                    dsc_file = '{}/{}'.format(panelPath,f).replace('//','/')

                                    public.ExecShell('chattr -a -i {}'.format(dsc_file))
                                return update_panel_files(res,src_dir,retry_count + 1)
                            else:
                                for f in res:
                                    dsc_file = '{}/{}'.format(panelPath,f).replace('//','/')
                                    print_x(dsc_file)
                                print_x('ERROR：校验失败，存在【{}】个文件无法更新，正在恢复备份。'.format(len(res)))
                    return False

                if not update_panel_files(f_list,src_dir):
                    #恢复备份
                    copy_dir(f_list,bak_dir,panelPath,None)
                    print_x('操作失败，已成功恢复备份...')
    clear_tmp()
    return

def upgrade_panel(version = None):
    """
    @name 更新面板(对外接口)
    """
    repair_panel(version)




def repair_pyenv():
    """
    @name 修复pyenv(对外接口)
    """
    pass


if __name__ == '__main__':

    clear_tmp()
    os.system('rm -rf /tmp/upgrade_panel.log')
    disk = psutil.disk_usage(panelPath)
    print_x('正在检测磁盘空间...')
    print_x('磁盘剩余【{}】'.format(public.to_size(disk.free)))
    if disk.free >= 100 * 1024 * 1024:
        v = None
        if len(sys.argv) > 0:
            try:
                nkey = sys.argv[1]
            except:
                nkey = None

            if nkey == 'repair_panel':
                try:
                    v = sys.argv[2]
                except:pass
                repair_panel(v)
                exit()
            elif nkey == 'repair_pyenv':
                #修复pyenv
                pass
                exit()
        try:
            v = sys.argv[2]
        except: pass
        upgrade_panel(v)
    else:
        print_x('ERROR：磁盘空间不足 [100 MB]，无法继续操作.')

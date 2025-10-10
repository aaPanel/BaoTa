import os,sys,json,time
panelPath = '/www/server/panel/'
os.chdir(panelPath)

sys.path.insert(0, panelPath + "class/")
import public

"""
@name 检测节点是否可用
"""
down_url = None
down_list = [
    'download.bt.cn',
    'cmcc1-node.bt.cn',
    'ctcc1-node.bt.cn',
    'hk1-node.bt.cn',
    'down-node1.bt.cn',
    'down-node2.bt.cn'
]
node_list = '{}/data/node_list.pl'.format(panelPath)
node_path = '{}/data/node_url.pl'.format(panelPath)

"""
@name 打印调试信息
"""
def print_debug(msg):
    #if public.is_debug():
    print(msg)




def httpGet(url, timeout=(3, 6), headers={}):
    import http_requests
    res = http_requests.node_check(url, timeout=timeout, headers=headers)
    if res.status_code == 0:
        if headers: return False
        s_body = res.text
        return s_body
    s_body = res.text
    del res
    return s_body
"""
@name 检测节点是否可以访问
"""
def check_url(url,timeout = 0.5):
    try:
        res = httpGet(url,timeout=timeout)
        if res == 'True':
            return True
    except:pass
    return False


"""
@name 检测下载节点可用
"""
def check_down_url():
    global down_url
    if down_url:
        return down_url

    #0.5秒检测一次
    for url in down_list:
        print_debug("检测节点(0.5s)：{}".format(url))
        if check_url('http://{}/check.txt'.format(url),timeout=0.5):
            down_url = url
            return down_url

    #3秒检测一次
    for url in down_list:
        print_debug("检测节点(2s)：{}".format(url))
        if check_url('http://{}/check.txt'.format(url),timeout=2):
            down_url = url
            return down_url
    return False

"""
@name 检测节点列表是否有变化
"""
def check_node_list():
    data = {}
    res = public.httpGet('https://{}/node.json'.format(down_url))
    try:
        res = json.loads(res)
        if 'www-node' in res:
            data['www-node'] = res['www-node']
        if 'api-node' in res:
            data['api-node'] = res['api-node']

        if data:
            public.writeFile(node_list,json.dumps(data))
    except:
        print_debug("获取节点列表失败,错误如下：")
        print_debug(res)
    print_debug('  ')

"""
@name   检测节点是否可以访问
"""
def check_node_url():

    if not check_down_url():
        print_debug("无可用下载节点")
        exit()
    print_debug("当前可用下载节点：{}".format(down_url))

    check_node_list()

    if not os.path.exists(node_list):
        return False

    data = {}
    try:
        data = json.loads(public.readFile(node_list))
    except:pass

    node_url = {}
    www_node = False
    api_node = False

    #检测www节点
    if 'www-node' in data:
        #0.5秒检测一次
        for node in data['www-node']:
            print_debug("检测www节点(0.5S)：{}".format(node))
            if check_url('https://{}/node/check'.format(node['url']),0.5):
                www_node = node
                break
        #2秒检测一次
        if not www_node:
            for node in data['www-node']:
                print_debug("检测www节点(2s)：{}".format(node))
                if check_url('https://{}/node/check'.format(node['url']),2):
                    www_node = node
                    break
        if not www_node:
            print_debug("无可用www节点")
    #检测api节点
    if 'api-node' in data:
        #0.5秒检测一次
        for node in data['api-node']:
            print_debug("检测api节点(0.5S)：{}".format(node))
            if check_url('https://{}/node/check'.format(node['url']),0.5):
                api_node = node
                break
        #2秒检测一次
        if not api_node:
            for node in data['api-node']:
                print_debug("检测api节点(2s)：{}".format(node))
                if check_url('https://{}/node/check'.format(node['url']),2):
                    api_node = node
                    break
        if not api_node:
            print_debug("无可用api节点")

    node_url['api-node'] = api_node
    node_url['www-node'] = www_node
    node_url['down-node'] = {'url':down_url,'name':'官方下载节点'}

    if down_url:
        public.writeFile('{}/data/down_url.pl'.format(panelPath),down_url)

    public.writeFile(node_path,json.dumps(node_url))
    get_node_hostname()


"""
@name 获取域名解析的地址
"""
def get_node_hostname():

    data = {}
    try:
        data = json.loads(public.readFile(node_path))
    except:pass

    if not 'www-node' in data: return False

    for n in ['www-node','api-node','down-node']:
        if not n in data: continue
        if not data[n]: continue

        data[n]['ip'] = get_hostbyname(data[n]['url'])

    if not data: return False
    public.writeFile(node_path,json.dumps(data))


"""
@name 检测当前节点是否可用
"""
def check_curr_node():
    node_info = {}
    try:
        node_info = json.loads(public.readFile(node_path))
    except:
        if os.path.exists(node_path):
            os.remove(node_path)

    if not os.path.exists(node_path) or not node_info:
        return False

    if not node_info['api-node'] or not node_info['www-node']:
        return False

    n_list = ['api-node','www-node']
    for n in n_list:
        if not check_url('https://{}/node/check'.format(node_info[n]['url']),0.5):
            if not check_url('https://{}/node/check'.format(node_info[n]['url']),2):
                return False
        print_debug("当前[{}]节点连接正常,{}".format(n,node_info[n]))

    if 'down-node' in node_info:
        if not check_url('http://{}/check.txt'.format(node_info['down-node']['url']),timeout=0.5):
            if not check_url('https://{}/check.txt'.format(node_info['down-node']['url']),2):
                return False
        print_debug("下载[down-node]节点连接正常,{}".format(node_info['down-node']))

    get_node_hostname()
    return True

"""
@name 清理面板所有host
"""
def clear_host():
    print_debug("清理面板所有host")
    public.ExecShell("sed -i '/www.bt.cn/d' /etc/hosts")


"""
@name 获取域名的ip地址
"""
def get_hostbyname(hostname):
    try:
        import socket
        socket.setdefaulttimeout(10)
        ip_address = socket.gethostbyname(hostname)
        socket.setdefaulttimeout(None)
        return ip_address
    except:
        return False

"""
@name 开始修复
@param  nType 1:定期检测 2:每次检测
"""
def start_check(nType = 0):
    """
    @name 开始检测
    """
    mtime = 0
    if not os.path.exists(node_path):
        check_node_url()
        exit()

    try:
        mtime = os.path.getmtime(node_path)
    except: pass

    limit_time = time.time() - mtime
    if nType == 'auto_day':
            if limit_time > 86400:
                if check_curr_node():
                    exit('当前节点可用，跳过检测!')
                check_node_url()
    elif nType == 'repair':
        #修复面板，每次都检测
        check_node_url()
    elif nType == 'hour':
        if limit_time > 3600:
            if check_curr_node():
                exit('当前节点可用，跳过检测!')
            check_node_url()
    else:
        if limit_time < 60:
            print_debug("距离上次检测不足60s，跳过检测!")
            exit()

        if check_curr_node():
            print_debug("当前节点可用，跳过检测!")
            exit()

        check_node_url()

if __name__ == '__main__':
    print_debug(" ")
    clear_host()

    check_type = 0
    try:
        check_type = sys.argv[1]
    except:pass

    start_check(check_type)


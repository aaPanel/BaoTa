import re, json, os, sys, time, socket, requests
import public

from mailModel.base import Base


class main(Base):
    __APIURL2 = public.GetConfigValue('home') + '/api/v2/product/email'
    __PDATA = None
    _check_url = None
    __request_url = None
    __UPATH = 'data/userInfo.json'
    __userInfo = None

    def __init__(self):
        super().__init__()
        self.__PDATA = {}
        self.connect_to_database('').execute("""CREATE TABLE IF NOT EXISTS `email_send_record` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,        
          `addresser` varchar(320) NOT NULL,    -- 发件人
          `recipient` varchar(320) NOT NULL,    -- 收件人
          `date` INTEGER NOT NULL,  -- 日期  20240101  
          `is_admin` tinyint(1) NOT NULL DEFAULT 0,   -- 是否上传  0  
          `created` INTEGER NOT NULL
          );""", ())

    def connect_to_database(self, table_name, month=None):
        import db
        if not os.path.exists(public.get_plugin_path() + '/mail_sys/data'):
            os.makedirs(public.get_plugin_path() + '/mail_sys/data')
        if not month:
            month = time.strftime('%Y%m', time.localtime())

        sql = db.Sql()
        sql._Sql__DB_FILE = public.get_plugin_path() + '/mail_sys/data/send_record_{}.db'.format(month)
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def request(self, dname):

        request_url = self.__APIURL2 + '/' + dname
        self.__request_url = public.get_home_node(request_url)
        msg = '接口请求失败（{}）'.format(self.__request_url)
        try:

            res = public.httpPost(request_url, self.__PDATA)
            if res == False:
                raise public.error_conn_cloud(msg)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))

        result = public.returnMsg(False, msg)
        try:
            result = json.loads(res)
        except:
            pass
        return result

    # 获取用户信息
    def get_user_info(self):
        upath = public.get_panel_path() + "/" + self.__UPATH
        try:
            self.__userInfo = json.loads(public.readFile(upath))
        except:
            self.__userInfo = {}

    # 获取从产品信息
    def get_product_info(self, get):
        self.__PDATA['id'] = 31
        result = self.request('product_info')
        if not result['success']:
            return public.returnMsg(False, result['res'])
        return public.returnMsg(True, result['res'])

    # 创建订单
    def create_order(self, get):
        self.get_user_info()
        self.__PDATA['spec_id'] = get.spec_id
        self.__PDATA['pid'] = get.pid
        self.__PDATA['access_key'] = self.__userInfo.get('access_key')
        self.__PDATA['serverid'] = self.__userInfo.get('serverid')
        self.__PDATA['uid'] = self.__userInfo.get('uid')

        result = self.request('product_buy')
        result['res']['uid'] = self.__userInfo.get('uid')
        if not result['success']:
            return public.returnMsg(False, result['res'])
        return public.returnMsg(True, result['res'])

    # 支付状态
    def pay_status(self, get):
        self.__PDATA['oid'] = get.oid
        result = self.request('product_buy_state')
        return result['res']

    # 获取用户余量
    def user_surplus(self, get=None):
        path = "{}/data/user_surplus.pl".format(public.get_panel_path())
        if not "fresh" in get or not get.fresh:
            try:
                json_data = json.loads(public.readFile(path))
                return public.returnMsg(True, json_data)
            except:
                pass
        # 上传发件数量
        self.upload_send_num()
        # 获取用户余量
        result = self.request('user_surplus')
        if not result['success']:
            return public.returnMsg(False, result['res'])
        public.writeFile(path, json.dumps(result['res']))
        return public.returnMsg(True, result['res'])

    # 余额支付
    def product_credit_buy(self, get):
        self.get_user_info()
        spec_id = get.spec_id
        pid = get.pid
        self.__PDATA = self.__userInfo
        self.__PDATA['spec_id'] = spec_id
        self.__PDATA['pid'] = pid
        result = self.request('product_credit_buy')
        if not result['success']:
            return public.returnMsg(False, result['res'])
        return public.returnMsg(True, "支付成功")

    # 上送
    def use_the(self, num=1):
        self.__PDATA['num'] = num
        result = self.request('use_the')
        return result

    # 设置发送记录
    def set_send_record(self, addresser, recipient):
        table_name = 'email_send_record'
        sql = self.connect_to_database(table_name)
        today = time.strftime('%Y%m%d', time.localtime())
        pdata = {
            'addresser': addresser,
            'recipient': recipient,
            'date': today,
            'created': int(time.time()),
        }
        sql.insert(pdata)

    # 获取可发送状态
    def get_can_send(self):
        # 获取剩余数量
        surplus = self.user_surplus()
        if not surplus['status']:
            return public.returnMsg(False, surplus['msg'])
        surplus_num = int(surplus['msg']['period']['surplus']) + int(surplus['msg']['free']['surplus'])

        # 获取今日已发送数量
        sql = self.connect_to_database("email_send_record")
        today = time.strftime('%Y%m%d', time.localtime())
        count = sql.where("is_admin=0", ()).count()
        if count >= surplus_num:
            return public.returnMsg(False, "发送数量已达上限")
        return public.returnMsg(True, "可以发送" + str(surplus_num - count) + "封邮件")

    # 上传发送数量
    def upload_send_num(self, get=None):
        pl_path = public.get_plugin_path() + '/mail_sys/upload_send_num.pl'
        if os.path.exists(pl_path):
            os.remove(pl_path)
        today = time.strftime('%Y%m%d', time.localtime())

        sql = self.connect_to_database("email_send_record")
        count = sql.where("is_admin=0", ()).count()

        self.get_user_info()
        self.__userInfo['ip'] = self.__userInfo.get('address')
        self.__PDATA = self.__userInfo

        if count == 0:
            public.writeFile(pl_path, str(int(time.time())))
            return public.returnMsg(True, "无需上传")
        result = self.use_the(count)
        if not result['success']:
            public.writeFile(pl_path, str(int(time.time())))
            return public.returnMsg(False, result['res'])
        sql.where("is_admin=0", ()).limit(count).update({'is_admin': 1})
        # 标记文件
        public.writeFile(pl_path, str(int(time.time())))
        return public.returnMsg(True, "上传成功")

    # 2024/12/21 11:36 安装宝塔邮局
    def install_service(self, get):
        '''
            @name 安装宝塔邮局
        '''
        public.httpPost(public.GetConfigValue('home') + '/api/panel/plugin_total', {"pid": "403", 'p_name': "mailmod"}, 3)

        # download_url = "{}/install/plugin/mail_sys/mail_install.sh".format(public.get_url())
        # install_path = "{}/panel/install".format(public.get_setup_path())
        # install_file = install_path + "/mail_install.sh"
        # if os.path.exists(install_file): os.remove(install_file)
        # public.ExecShell("rm -f /www/server/panel/install/mail_install.sh;wget -O " + install_file + " " + download_url + " --no-check-certificate")
        # if not os.path.exists(install_file): return public.returnMsg(False, '下载安装脚本失败')
        if public.M('tasks').where('name=? and status=?', ('安装 [宝塔邮局]', '0')).count() > 0:
            return public.returnMsg(False, '安装任务已存在')
        else:
            execstr = "cd /www/server/panel/class/mailModel/script && /bin/bash install.sh install"
            public.M('tasks').add('id,name,type,status,addtime,execstr', (
            None, '安装 [宝塔邮局]', 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
            public.writeFile('/tmp/panelTask.pl', 'True')
            return public.returnMsg(True, '安装任务已添加到任务队列中')

    def install_status(self, get):
        '''
        @name 安装状态
        '''
        if os.path.exists("/www/server/panel/plugin/mail_sys"):
            try:
                from mailModel.mainModel import main as mail_main
                mail_main().get_service_status(None)
            except:
                return public.returnMsg(False, '')
            return public.returnMsg(True, '')
        else:
            return public.returnMsg(False, '')

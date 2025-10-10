import os, sys, json, psutil
import time

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')

import public

from sslModel.base import sslBase


class main(sslBase):
    __APIURL2 = public.GetConfigValue('home') + '/api/v2/synchron'
    # __APIURL2 = "https://dev.bt.cn" + '/api/v2/synchron'
    __PDATA = None
    _check_url = None
    __request_url = None
    __UPATH = 'data/userInfo.json'
    __userInfo = None
    def __init__(self):
        super().__init__()
        if not os.path.exists(public.get_panel_path() + '/data/auto_deploy'):
            os.makedirs(public.get_panel_path() + '/data/auto_deploy')

        # 本地任务表
        self.M("").execute("""CREATE TABLE IF NOT EXISTS `autodeploy_task` (
          `id` INTEGER  PRIMARY KEY AUTOINCREMENT,        
          `task_name` varchar(320) NOT NULL,    -- 任务名称
          `cloud_id` INTEGER NOT NULL,    -- 云端任务ID
          `access_id` INTEGER NOT NULL,    -- 接入ID
          `private_key` varchar(320) NOT NULL,    -- 密钥
          `sites` varchar(320) NOT NULL,    -- 网站
          `cycle` INTEGER NOT NULL DEFAULT 12,    -- 检测周期
          `deploy_time` INTEGER NOT NULL DEFAULT 0,    -- 最近部署时间
          `deploy_status` INTEGER NOT NULL DEFAULT 0,    -- 最近部署状态 0等待部署 1=部署成功 -1部署失败
          `ssl_hash` varchar(320) NOT NULL DEFAULT '',   -- 证书hash
          `ssl_cloud_id` varchar(320) NOT NULL DEFAULT ''   -- 云端证书id
          );""", ())

        self.get_user_info()

        # 云端任务表
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

    def get_user_info(self):
        upath = public.get_panel_path() + "/" + self.__UPATH
        try:
            self.__userInfo = json.loads(public.readFile(upath))
        except:
            self.__userInfo = {}
        self.__PDATA = self.__userInfo

    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = public.get_panel_path() + '/data/db/ssl_data.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def plane_synchron_list(self, get):
        res = self.request('plane_synchron_list')
        if not res["success"]:
            public.returnMsg(False, res["res"])
        return public.returnMsg(True, res["res"])

    def plane_synchron_access_list(self):
        # path = public.get_panel_path() + '/data/auto_deploy/plane_synchron_list.json'
        # try:
        #     data = json.loads(public.readFile(path))
        #     return public.returnMsg(True, data)
        # except:
        #     pass
        res = self.request('plane_synchron_access_list')

        if not res["success"]:
            public.returnMsg(False, res["res"])
        # public.writeFile(path, json.dumps(res["res"]))
        return public.returnMsg(True, res["res"])

    def plane_synchron_access_set(self, get):
        self.__PDATA["key"] = get.private_key
        self.__PDATA["synid"] = int(get.cloud_id)
        # self.__PDATA["url"] = "https://www.bt.cn"
        res = self.request('plane_synchron_access_set')
        if not res["success"]:
            return public.returnMsg(False, res["res"])
        return public.returnMsg(True, res["res"])

    def get_task_list(self, get=None):

        p = 1
        if 'p' in get:
            p = int(get.p)
        collback = ''
        if 'collback' in get:
            collback = get.collback
        limit = 999999999
        if 'limit' in get:
            limit = int(get.limit)
        f_sql = '1=1'
        if 'search' in get and get.search:
            f_sql = "task_name like '%{}%' or sites like '%{}%' ".format(get.search, get.search)

        count = self.M("autodeploy_task").where(f_sql, ()).count()
        page_data = public.get_page(count, p, limit, collback)

        data = self.M("autodeploy_task").where(f_sql, ()).limit(page_data["shift"]+","+page_data["row"]).order("id desc").select()
        # public.print_log(data)

        try:
            cloud_data = self.plane_synchron_access_list()
        except:
            cloud_data = None
        # public.print_log(cloud_data)

        deploy = []
        for i in data:
            i["access_state"] = 0
            i["synchron_info"] = {}
            if not cloud_data:
                continue
            for j in cloud_data["msg"]:
                if i["access_id"] == j["id"]:
                    i["access_state"] = j["access_state"]
                    if j["access_state"] == 2 and str(i["ssl_cloud_id"]) != str(j["synchron_info"]["ca_id"]):
                        self.M("autodeploy_task").where("cloud_id=?", (i["cloud_id"],)).update({"ssl_cloud_id": j["synchron_info"]["ca_id"]})
                        # 写需要更新证书的任务到队列
                        deploy.append(i["id"])
                    i["synchron_info"] = j["synchron_info"]
        if deploy:
            public.ExecShell("nohup btpython {}/class/sslModel/autodeployModel.py --task_ids={} > /dev/null 2>&1 &".format(public.get_panel_path(), ",".join(str(i) for i in deploy)))
        page_data["data"] = data

        return {"status": True, "msg": page_data, "deploy": deploy}

    def add_task(self, get):
        task_name = get.task_name
        cloud_id = get.cloud_id
        private_key = get.private_key
        sites = get.sites
        # cycle = get.cycle
        cycle = 1
        data = self.M("autodeploy_task").where("cloud_id=?", (cloud_id,)).find()
        if data:
            return public.returnMsg(False, "选择的证书部署任务在本服务器已存在对应的任务【{}】请勿重复添加！".format(data["task_name"]))

        res = self.plane_synchron_access_set(get)
        if not res["status"]:
            return public.returnMsg(False, res["msg"])

        self.M("autodeploy_task").add('task_name,cloud_id,access_id,private_key,sites,cycle', (task_name, cloud_id, res["msg"]["id"], private_key, sites, cycle))
        if not res["status"]:
            return public.returnMsg(False, res["msg"])
        return public.returnMsg(True, "添加成功")

    def plane_synchron_access_delte(self, get):
        self.__PDATA["id"] = int(get.access_id)
        res = self.request('plane_synchron_access_delte')
        if not res["success"]:
            return public.returnMsg(False, res["res"])
        return public.returnMsg(True, res["res"])

    def del_task(self, get):
        data = self.M("autodeploy_task").where("id=?", (get.task_id,)).find()
        if not data:
            return public.returnMsg(False, "未找到任务")
        self.M("autodeploy_task").where("id=?", (get.task_id,)).delete()
        self.plane_synchron_access_delte(public.to_dict_obj({"access_id": data["access_id"]}))
        return public.returnMsg(True, "删除成功")

    def batch_del_task(self, get):
        task_id_list = get.task_ids.split(",")
        data = self.M("autodeploy_task").where("id in ({})".format(get.task_ids), ()).select()
        self.M("autodeploy_task").where("id in ({})".format(get.task_ids), ()).delete()

        total = len(data)
        faild = 0
        success = 0
        faildList = []
        successList = []
        for i in data:
            if str(i["id"]) not in task_id_list:
                faild += 1
                faildList.append({"task_id": i["id"], "task_name":i["task_name"],"error_msg": "任务不存在", "status": False})
                continue
            self.plane_synchron_access_delte(public.to_dict_obj({"access_id": i["access_id"]}))
            success += 1
            successList.append({"task_id": i["id"], "task_name":i["task_name"],"error_msg": "删除成功", "status": True})

        return public.returnMsg(True, {"total": total, "success": success, "faild": faild, "faildList": faildList, "successList": successList})

    def edit_task(self, get):
        task_id = get.task_id
        task_name = get.task_name
        cloud_id = int(get.cloud_id)
        private_key = get.private_key
        sites = get.sites
        # cycle = get.cycle
        cycle = 1

        data = self.M("autodeploy_task").where("id=?", (task_id,)).find()
        if not data:
            return public.returnMsg(False, "未找到任务")
        update_data = {"task_name": task_name, "cloud_id": cloud_id, "private_key": private_key, "sites": sites, "cycle": cycle}

        if data["cloud_id"] != cloud_id:
            cloud_data = self.M("autodeploy_task").where("cloud_id=?", (cloud_id)).find()
            if cloud_data:
                return public.returnMsg(False, "选择的证书部署任务在本服务器已存在对应的任务【{}】请勿重复添加！".format(cloud_data["task_name"]))
            res = self.plane_synchron_access_set(get)
            if not res["status"]:
                return public.returnMsg(False, res["msg"])
            update_data["access_id"] = res["msg"]["id"]
        elif data["private_key"] != private_key:
            res = self.plane_synchron_access_set(get)
            if not res["status"]:
                return public.returnMsg(False, res["msg"])

        if data["sites"] != sites:
            update_data["ssl_cloud_id"] = ""

        self.M("autodeploy_task").where("id=?", (get.task_id,)).update(update_data)
        return public.returnMsg(True, "修改成功")

    def plane_synchron_get_cert(self, access_id):
        self.__PDATA["id"] = int(access_id)
        res = self.request('plane_synchron_get_cert')
        if not res["success"]:
            return public.returnMsg(False, res["res"])
        return public.returnMsg(True, res["res"])

    def set_cert_to_database(self, access_id):
        cert_data = self.plane_synchron_get_cert(access_id)
        if not cert_data["status"]:
            return public.returnMsg(False, cert_data["msg"])
        cert_data = cert_data["msg"]["cert"]

        from sslModel import certModel
        get = public.dict_obj()
        get.key = cert_data["privateCert"]
        get.csr = cert_data["cert"]

        try:
            cert = certModel.main().save_cert(get)
            if not cert["status"]:
                return False
        except:
            return False
        self.M("autodeploy_task").where("access_id=?", (access_id,)).update({"ssl_hash": cert["ssl_hash"]})
        return True

    def deploy_cert(self, get):
        data = self.M("autodeploy_task").where("id=?", (int(get.task_id),)).find()
        if not data:
            return public.returnMsg(False, "未找到任务")
        sites = data["sites"].split(",")
        ssl_hash = data["ssl_hash"]
        get.BatchInfo = json.dumps([
            {"ssl_hash": ssl_hash, "siteName": i}
            for i in sites
        ])
        import panelSSL
        res = panelSSL.panelSSL().SetBatchCertToSite(get)

        deploy_time = int(time.time())
        if res["total"] == res["success"]:
            self.write_deploy_detail(get.task_id, json.dumps(res), data["access_id"], 1, 1)
            deploy_status = 1
        else:
            self.write_deploy_detail(get.task_id, json.dumps(res), data["access_id"], -1, 1)
            deploy_status = -1
        self.M("autodeploy_task").where("id=?", (int(get.task_id),)).update({"deploy_time": deploy_time, "deploy_status": deploy_status})

    def upload_deploy_msg(self, get):
        self.__PDATA["msg"] = get.error_msg
        self.__PDATA["id"] = get.access_id
        self.__PDATA["state"] = get.state
        self.__PDATA["type"] = get.msg_type

        # print(self.__PDATA)

        res = self.request('plane_synchron_deploy_state')
        if not res["success"]:
            return public.returnMsg(False, res["res"])
        return public.returnMsg(True, res["res"])

    def write_deploy_detail(self, task_id, error_msg, access_id, state, msg_type):
        path = public.get_panel_path() + '/data/auto_deploy/deploy_detail'
        if not os.path.exists(path):
            os.makedirs(path)
        public.writeFile(path + "/{}.json".format(task_id), error_msg)
        # print(access_id, state, msg_type)
        res = self.upload_deploy_msg(public.to_dict_obj({"access_id": access_id, "error_msg": error_msg, "state": state, "msg_type": msg_type}))
        # print(res)

    def get_task_deploy_detail(self, get):
        try:
            res = json.loads(public.readFile(public.get_panel_path() + '/data/auto_deploy/deploy_detail/{}.json'.format(get.task_id)))
        except:
            res = None
        return public.returnMsg(True, res)



if __name__ == '__main__':
    try:
        if os.path.exists("/www/server/panel/data/auto_deploy.pl"):
            exit()
        public.writeFile("/www/server/panel/data/auto_deploy.pl", "")
        m = main()
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--task_ids', default=None, help="任务id列表，用逗号分隔", dest="task_ids")
        args = p.parse_args()
        if not args.task_ids:
            exit()
        task_ids = args.task_ids.split(",")
        for i in task_ids:
            task_data = m.M("autodeploy_task").where("id=?", (int(i),)).find()
            if not task_data:
                continue
            set_cert_status = m.set_cert_to_database(task_data["access_id"])
            if not set_cert_status:
                sites = task_data["sites"].split(",")
                error_msg = json.dumps({
                    "total": len(sites),
                    "success": 0,
                    "faild": len(sites),
                    "faildList": [{"siteName": site, "error_msg": "证书保存失败", "status": False} for site in sites],
                    "successList": []
                })
                m.write_deploy_detail(i, error_msg, task_data["access_id"], -1, 1)
                m.M("autodeploy_task").where("id=?", (int(i),)).update(
                    {"deploy_time": int(time.time()), "deploy_status": -1})
                continue
            m.deploy_cert(public.to_dict_obj({"task_id": i}))
            print("部署成功：", task_data["task_name"])
        exit()
    finally:
        os.remove("/www/server/panel/data/auto_deploy.pl")


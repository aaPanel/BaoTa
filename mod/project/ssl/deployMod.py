import json
import os
import time

import public
import requests

from mod.project.ssl import plugin

class main:
    def __init__(self):
        if not os.path.exists("/www/server/deploy_plugin"):
            os.makedirs("/www/server/deploy_plugin")

        # 部署授权表
        self.M("").execute("""create table if not exists deploy_auths
(
    `id`          integer not null
        constraint deploy_auths_pk
            primary key autoincrement,
    `name`        TEXT    not null,
    `config`      TEXT    not null,
    `type`        TEXT    not null,
    `create_time` TEXT,
    `update_time` TEXT
);""", ())

        # 部署目标表
        self.M("").execute("""create table if not exists deploy_targets
(
    `id`          integer not null
        constraint deploy_targets_pk
            primary key autoincrement,
    `auth_id`    integer not null,
    `name`        TEXT    not null,
    `action`      TEXT    not null,
    `params`      TEXT    not null,
    `type`        TEXT    not null,
    `create_time` TEXT,
    `update_time` TEXT
);""",())

    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = public.get_panel_path() + '/data/db/ssl_data.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def get_plugins(self, get):
        try:
            cloud_plugins = requests.get("{}/thirdparty_deploy/deploy_plugins.json".format(public.get_url()), timeout=10).json()
            if type(cloud_plugins) != list:
                cloud_plugins = []
        except:
            cloud_plugins = []
        local_plugins = plugin.get_plugins()
        plugins = []
        for cp in cloud_plugins:
            cp['install'] = True
            cp['update'] = False

            for lp in local_plugins:
                if cp['name'] == lp['name']:
                    cp['install'] = False
                    cp['path'] = lp['path']
                    if cp['version'] != lp['version']:
                        cp['update'] = True
                    break
            plugins.append(cp)
        for lp in local_plugins:
            exist = False
            for cp in cloud_plugins:
                if cp['name'] == lp['name']:
                    exist = True
                    break
            if not exist:
                lp['install'] = False
                lp['update'] = False
                plugins.append(lp)
        # 排序：已安装的在前，未安装的在后；btpanel插件排第一
        plugins.sort(key=lambda x: (x['install']))

        return plugins

    def install_plugin(self, get):
        if 'plugin_name' not in get or not get.plugin_name:
            return {'status': False, 'msg': '缺少参数plugin_name'}
        name = get.plugin_name

        if public.M('tasks').where('name=? and status=?', ('安装SSL证书部署插件[{}]'.format(get.plugin_name), '0')).count() > 0:
            return public.returnMsg(False, '安装任务已存在')
        else:
            # 判断系统架构
            arch = public.ExecShell("uname -m")[0].strip()
            if arch == 'x86_64':
                get.plugin_name += '-x86_64'
            elif arch in ['aarch64']:
                get.plugin_name += '-aarch64'
            else:
                return public.returnMsg(False, '不支持当前系统架构：{}'.format(arch))

            execstr = "wget -O /www/server/deploy_plugin/{} {}/thirdparty_deploy/deploy_plugin/{} -T 10 && chmod 755 /www/server/deploy_plugin/{}".format(
                name, public.get_url(), get.plugin_name, name)
            public.M('tasks').add('id,name,type,status,addtime,execstr', (
            None, '安装SSL证书部署插件[{}]'.format(get.plugin_name), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
            public.writeFile('/tmp/panelTask.pl', 'True')
            return public.returnMsg(True, '安装任务已添加到任务队列中')

    def uninstall_plugin(self, get):
        if 'plugin_name' not in get or not get.plugin_name:
            return {'status': False, 'msg': '缺少参数plugin_name'}
        local_plugins = plugin.get_plugins()
        for lp in local_plugins:
            if lp['name'] == get.plugin_name:
                if self.M('deploy_auths').where("type=?", (get.plugin_name,)).count() > 0:
                    return {'status': False, 'msg': '请先删除该插件相关的授权配置'}
                try:
                    os.remove(lp['path'])
                    return {'status': True, 'msg': '卸载成功'}
                except Exception as e:
                    return {'status': False, 'msg': '卸载失败：{}'.format(str(e))}
        return {'status': False, 'msg': '插件未安装'}

    # 新增授权
    def add_deploy_auth(self, get):
        if 'name' not in get or not get.name:
            return {'status': False, 'msg': '缺少参数name'}
        if 'config' not in get or not get.config:
            return {'status': False, 'msg': '缺少参数config'}
        if 'type' not in get or not get.type:
            return {'status': False, 'msg': '缺少参数type'}
        # 获取插件配置
        local_plugins = plugin.get_plugins()
        plugin_config = None
        for lp in local_plugins:
            if lp['name'] == get.type:
                plugin_config = lp['config']
                break
        if not plugin_config:
            return {'status': False, 'msg': '未知的授权类型'}
        # 检查config
        try:
            config = json.loads(get.config)
        except Exception as e:
            return {'status': False, 'msg': '参数config格式错误，必须为JSON格式'}
        for key in plugin_config.keys():
            if key not in config:
                return {'status': False, 'msg': '参数config缺少字段{}'.format(key)}

        # 检查同名授权是否存在
        exist = self.M('deploy_auths').where('name=?', (get.name,)).count()
        if exist > 0:
            return {'status': False, 'msg': '同名授权已存在'}

        data = {
            'name': get.name,
            'config': get.config,
            'type': get.type,
            'create_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'update_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        self.M('deploy_auths').insert(data)
        return {'status': True, 'msg': '添加成功'}

    # 修改授权
    def edit_deploy_auth(self, get):
        if 'auth_id' not in get or not get.auth_id:
            return {'status': False, 'msg': '缺少参数id'}
        if 'name' not in get or not get.name:
            return {'status': False, 'msg': '缺少参数name'}
        if 'config' not in get or not get.config:
            return {'status': False, 'msg': '缺少参数config'}
        if 'type' not in get or not get.type:
            return {'status': False, 'msg': '缺少参数type'}
        # 获取插件配置
        local_plugins = plugin.get_plugins()
        plugin_config = None
        for lp in local_plugins:
            if lp['name'] == get.type:
                plugin_config = lp['config']
                break
        if not plugin_config:
            return {'status': False, 'msg': '未知的授权类型'}
        # 检查config
        try:
            config = json.loads(get.config)
        except Exception as e:
            return {'status': False, 'msg': '参数config格式错误，必须为JSON格式'}
        for key in plugin_config.keys():
            if key not in config:
                return {'status': False, 'msg': '参数config缺少字段{}'.format(key)}

        # 检查同名授权是否存在
        exist = self.M('deploy_auths').where('name=? AND id!=?', (get.name, get.auth_id)).count()
        if exist > 0:
            return {'status': False, 'msg': '同名授权已存在'}

        data = {
            'name': get.name,
            'config': get.config,
            'type': get.type,
            'update_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        self.M('deploy_auths').where('id=?', (get.auth_id,)).update(data)
        return {'status': True, 'msg': '修改成功'}

    # 删除授权
    def delete_deploy_auth(self, get):
        if 'auth_id' not in get or not get.auth_id:
            return {'status': False, 'msg': '缺少参数id'}

        if self.M('deploy_targets').where('auth_id=?', (get.auth_id,)).count() > 0:
            return {'status': False, 'msg': '请先删除该授权相关的部署目标'}

        self.M('deploy_auths').where('id=?', (get.auth_id,)).delete()
        return {'status': True, 'msg': '删除成功'}

    # 获取授权列表
    def get_deploy_auths(self, get):
        w_sql = ""
        if "search" in get and get.search:
            w_sql += " and name like'%{}%'".format(get.search)
        local_plugins = plugin.get_plugins()
        plugin_name_dic = {lp['name']: lp["description"] for lp in local_plugins}
        w_sql += " and type in ('{}')".format("','".join(plugin_name_dic.keys()))

        p = 1
        if "p" in get and get.p:
            p = int(get.p)
        limit = 10
        if "limit" in get and get.limit:
            limit = int(get.limit)
        if p == -1:
            data = self.M("deploy_auths").where("1=1 {}".format(w_sql), ()).order('create_time desc').select()
        else:
            data = self.M("deploy_auths").where("1=1 {}".format(w_sql), ()).order('create_time desc').limit('{},{}'.format((p - 1) * limit, limit)).select()
        count = self.M("deploy_auths").where("1=1 {}".format(w_sql), ()).count()
        for d in data:
            try:
                d['config'] = json.loads(d['config'])
            except:
                d['config'] = {}
            d["description"] = plugin_name_dic[d["type"]]
        return {'data': data, 'count': count}

    # 新增部署目标
    def add_deploy_target(self, get):
        if 'auth_id' not in get or not get.auth_id:
            return {'status': False, 'msg': '缺少参数auth_id'}
        if 'name' not in get or not get.name:
            return {'status': False, 'msg': '缺少参数name'}
        if 'method' not in get or not get.method:
            return {'status': False, 'msg': '缺少参数method'}
        if 'params' not in get or not get.params:
            return {'status': False, 'msg': '缺少参数params'}
        if 'type' not in get or not get.type:
            return {'status': False, 'msg': '缺少参数type'}

        # 检查同名目标是否存在
        exist = self.M('deploy_targets').where('name=?', (get.name,)).count()
        if exist > 0:
            return {'status': False, 'msg': '同名部署目标已存在'}
        # 检查授权是否存在
        auth = self.M('deploy_auths').where('id=? and type=?', (get.auth_id, get.type)).find()
        if not auth:
            return {'status': False, 'msg': '授权不存在'}
        # 检查插件和部署方法是否存在
        local_plugins = plugin.get_plugins()
        plugin_found = False
        for lp in local_plugins:
            if lp['name'] == get.type:
                plugin_found = True
                action_found = False
                for action in lp['actions']:
                    if action['name'] == get.method.strip():
                        action_found = True
                        # 检查params格式
                        if action['params'] is None:
                            if get.params.strip() != '{}' and get.params.strip() != '':
                                return {'status': False, 'msg': '参数params格式错误，该方法不需要参数'}
                            break
                        try:
                            params = json.loads(get.params)
                        except Exception as e:
                            return {'status': False, 'msg': '参数params格式错误，必须为JSON格式'}
                        for key in action['params'].keys():
                            if key not in params:
                                return {'status': False, 'msg': '参数params缺少字段{}'.format(key)}
                        break
                if not action_found:
                    return {'status': False, 'msg': '部署方法不存在'}
                break
        if not plugin_found:
            return {'status': False, 'msg': '插件不存在'}

        data = {
            'auth_id': get.auth_id,
            'name': get.name,
            'action': get.method,
            'params': get.params,
            'type': get.type,
            'create_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'update_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        self.M('deploy_targets').insert(data)
        return {'status': True, 'msg': '添加成功'}

    # 修改部署目标
    def edit_deploy_target(self, get):
        if 'target_id' not in get or not get.target_id:
            return {'status': False, 'msg': '缺少参数id'}
        if 'auth_id' not in get or not get.auth_id:
            return {'status': False, 'msg': '缺少参数auth_id'}
        if 'name' not in get or not get.name:
            return {'status': False, 'msg': '缺少参数name'}
        if 'method' not in get or not get.method:
            return {'status': False, 'msg': '缺少参数method'}
        if 'params' not in get or not get.params:
            return {'status': False, 'msg': '缺少参数params'}
        if 'type' not in get or not get.type:
            return {'status': False, 'msg': '缺少参数type'}

        # 检查同名目标是否存在
        exist = self.M('deploy_targets').where('name=? AND id!=?', (get.name, get.target_id)).count()
        if exist > 0:
            return {'status': False, 'msg': '同名部署目标已存在'}
        # 检查授权是否存在
        auth = self.M('deploy_auths').where('id=? and type=?', (get.auth_id, get.type)).find()
        if not auth:
            return {'status': False, 'msg': '授权不存在'}
        # 检查插件和部署方法是否存在
        local_plugins = plugin.get_plugins()
        plugin_found = False
        for lp in local_plugins:
            if lp['name'] == get.type:
                plugin_found = True
                action_found = False
                for action in lp['actions']:
                    if action['name'] == get.method:
                        action_found = True
                        # 检查params格式
                        if action['params'] is None:
                            if get.params.strip() != '{}' and get.params.strip() != '':
                                return {'status': False, 'msg': '参数params格式错误，该方法不需要参数'}
                            break
                        try:
                            params = json.loads(get.params)
                        except Exception as e:
                            return {'status': False, 'msg': '参数params格式错误，必须为JSON格式'}
                        for key in action['params'].keys():
                            if key not in params:
                                return {'status': False, 'msg': '参数params缺少字段{}'.format(key)}
                        break
                if not action_found:
                    return {'status': False, 'msg': '部署方法不存在'}
                break
        if not plugin_found:
            return {'status': False, 'msg': '插件不存在'}
        data = {
            'auth_id': get.auth_id,
            'name': get.name,
            'action': get.method,
            'params': get.params,
            'type': get.type,
            'update_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        self.M('deploy_targets').where('id=?', (get.target_id,)).update(data)
        return {'status': True, 'msg': '修改成功'}

    # 删除部署目标
    def delete_deploy_target(self, get):
        if 'target_id' not in get or not get.target_id:
            return {'status': False, 'msg': '缺少参数id'}
        self.M('deploy_targets').where('id=?', (get.target_id,)).delete()
        return {'status': True, 'msg': '删除成功'}

    # 获取部署目标列表
    def get_deploy_targets(self, get):
        w_sql = ""
        if "search" in get and get.search:
            w_sql += " and name like'%{}%'".format(get.search)
        if "type" in get and get.type:
            w_sql += " and type='{}'".format(get.type)
        local_plugins = plugin.get_plugins()
        plugin_name_dic = {lp['name']: {"description": lp["description"], "actions": { a["name"]: a["description"] for a in lp["actions"]}} for lp in local_plugins}
        w_sql += " and type in ('{}')".format("','".join(plugin_name_dic.keys()))

        p = 1
        if "p" in get and get.p:
            p = int(get.p)
        limit = 10
        if "limit" in get and get.limit:
            limit = int(get.limit)
        if p == -1:
            data = self.M("deploy_targets").where("1=1 {}".format(w_sql), ()).order('create_time desc').select()
        else:
            data = self.M("deploy_targets").where("1=1 {}".format(w_sql), ()).limit('{},{}'.format((p - 1) * limit, limit)).order('create_time desc').select()
        count = self.M("deploy_targets").where("1=1 {}".format(w_sql), ()).count()
        for d in data:
            try:
                d['params'] = json.loads(d['params'])
            except:
                d['params'] = {}

            auth_name = self.M('deploy_auths').where('id=?', (d['auth_id'],)).getField('name')
            if auth_name:
                d["description"] = auth_name+" - "+plugin_name_dic[d["type"]]["description"]
            else:
                d["description"] = plugin_name_dic[d["type"]]["description"]
            d["action_description"] = plugin_name_dic[d["type"]]["actions"].get(d["action"], "")
        return {'data': data, 'count': count}

    def get_actions(self, get):
        if 'plugin_name' not in get or not get.plugin_name:
            return {'status': False, 'msg': '缺少参数plugin_name'}
        return plugin.get_actions(get.plugin_name)

    def execute_action(self, get):
        # 获取证书来源
        if "cert" in get and get.cert and "key" in get and get.key:
            cert = get.cert
            key = get.key
        elif "oid" in get and get.oid:
            import panelSSL
            ssl_obj = panelSSL.panelSSL()
            rep = ssl_obj.get_order_find(get)
            cert = rep['certificate']+"\n"+rep['caCertificate']
            key = rep['privateKey']
        elif ("ssl_hash" in get and get.ssl_hash) or ("index" in get and get.index):
            from sslModel import certModel
            cert_obj = certModel.main()
            cert_info = cert_obj.GetCert(get)
            if 'privkey' not in cert_info or not cert_info['privkey']:
                return {'status': False, 'msg': '证书私钥不存在'}
            cert = cert_info['fullchain']
            key = cert_info['privkey']
        else:
            return {'status': False, 'msg': '缺少证书参数'}
        if "target_id" not in get or not get.target_id:
            return {'status': False, 'msg': '缺少参数target_id'}
        # 获取部署目标
        target = self.M('deploy_targets').where('id=?', (get.target_id,)).find()
        if not target:
            return {'status': False, 'msg': '部署目标不存在'}
        # 获取授权
        auth = self.M('deploy_auths').where('id=?', (target['auth_id'],)).find()
        if not auth:
            return {'status': False, 'msg': '部署授权不存在'}
        # 组装参数
        try:
            params = json.loads(target['params'])
            config = json.loads(auth['config'])
        except Exception as e:
            return {'status': False, 'msg': '部署目标参数格式错误'}
        params.update(config)
        params["cert"] = cert
        params["key"] = key

        return plugin.call_plugin(auth["type"], target["action"], params)
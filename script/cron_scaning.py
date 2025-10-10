import sys, os
import time
os.chdir('/www/server/panel')
sys.path.insert(0, "class/")
sys.path.insert(0, '/www/server/panel')
import public
from mod.base.push_mod import push_by_task_keyword

class main:

    def __check_auth(self):
        from pluginAuth import Plugin
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        return int(plugin_list['ltd']) > time.time()

    def run(self):
        pay = self.__check_auth()
        msg_list = []
        if not pay:
            from panelSite import panelSite
            site_obj = panelSite()
            res = site_obj.get_Scan(None)
            if int(res['loophole_num']):
                msg_list.append('扫描网站【{}】，发现【{}】条漏洞'.format(res['site_num'], res['loophole_num']))
            else:
                msg_list.append('扫描网站【{}】个，状态【安全】'.format(res['site_num']))
        else:
            import PluginLoader
            args = public.dict_obj()
            args.model_index = 'project'
            res = PluginLoader.module_run('scanning', 'startScan', args)
            if int(res['loophole_num']):
                msg_list.append('扫描网站【{}】，发现【{}】条漏洞'.format(res['site_num'], res['loophole_num']))
                for i in res['info']:
                    msg_list.append('网站【{}】，存在【{}】个风险项，请及时处理'.format(
                        i['rname'] if i['rname'] else i['name'],
                        len(i['cms'])
                    ))
            else:
                msg_list.append('扫描网站【{}】个，状态【安全】'.format(res['site_num']))
        return {"msg_list": msg_list}


if __name__ == '__main__':
    channels = sys.argv[1]
    main = main()
    msg = main.run()
    push_by_task_keyword("vulnerability_scanning", "vulnerability_scanning", push_data=msg)

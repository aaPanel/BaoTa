#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <2020-08-04>
# +-------------------------------------------------------------------

import os,sys,json,time,public

class panelWarning:
    __path = '/www/server/panel/data/warning'
    __ignore = __path + '/ignore'
    __result = __path + '/result'
    def __init__(self):
        if not os.path.exists(self.__ignore):
            os.makedirs(self.__ignore,384)
        if not os.path.exists(self.__result):
            os.makedirs(self.__result,384)
        


    def get_list(self,args):
        self.sync_rule()
        p = public.get_modules('class/safe_warning')
        
        data = {
            'security':[],
            'risk':[],
            'ignore':[]
        }

        for m_name in p.__dict__.keys():
            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }
            result_file = self.__result + '/' + m_name + '.pl'

            not_force = True
            if 'force' in args:
                not_force = m_info['ignore']

            if os.path.exists(result_file) and not_force:
                m_info['status'],m_info['msg'],m_info['check_time'],m_info['taking'] = json.loads(public.readFile(result_file))
            else:
                try:
                    s_time = time.time()
                    m_info['status'],m_info['msg'] = p[m_name].check_run()
                    m_info['taking'] = round(time.time() - s_time,6)
                    m_info['check_time'] = int(time.time())
                    public.writeFile(result_file,json.dumps([m_info['status'],m_info['msg'],m_info['check_time'],m_info['taking']],))
                except:
                    continue

            
            if m_info['ignore']:
                data['ignore'].append(m_info)
            else:
                if m_info['status']:
                    data['security'].append(m_info)
                else:
                    data['risk'].append(m_info)

        data['risk'] = sorted(data['risk'],key=lambda x: x['level'],reverse=True)
        data['security'] = sorted(data['security'],key=lambda x: x['level'],reverse=True)
        data['ignore'] = sorted(data['ignore'],key=lambda x: x['level'],reverse=True)
        return data


    def sync_rule(self):
        '''
            @name 从云端同步规则
            @author hwliang<2020-08-05>
            @return void
        '''
        try:
            dep_path = '/www/server/panel/class/safe_warning'
            local_version_file = self.__path + '/version.pl'
            last_sync_time = local_version_file = self.__path + '/last_sync.pl'
            if os.path.exists(dep_path):
                if os.path.exists(last_sync_time):
                    if int(public.readFile(last_sync_time)) > time.time():
                        return
            else:
                if os.path.exists(local_version_file): os.remove(local_version_file)

            download_url = public.get_url()
            version_url = download_url + '/install/warning/version.txt'
            cloud_version = public.httpGet(version_url)
            if cloud_version: cloud_version = cloud_version.strip()

            local_version = public.readFile(local_version_file)
            if local_version:
                if cloud_version == local_version:
                    return
            
            tmp_file = '/tmp/bt_safe_warning.zip'
            public.ExecShell('wget -O {} {} -T 5'.format(tmp_file,download_url + '/install/warning/safe_warning.zip'))
            if not os.path.exists(tmp_file):
                return

            if os.path.getsize(tmp_file) < 2129:
                os.remove(tmp_file)
                return
            
            if not os.path.exists(dep_path):
                os.makedirs(dep_path,384)
            public.ExecShell("unzip -o {} -d {}/ >/dev/null".format(tmp_file,dep_path))
            public.writeFile(local_version_file,cloud_version)
            public.writeFile(last_sync_time,str(int(time.time() + 7200)))
            if os.path.exists(tmp_file): os.remove(tmp_file)
            public.ExecShell("chmod -R 600 {}".format(dep_path))
        except:
            pass



    def set_ignore(self,args):
        '''
            @name 设置指定项忽略状态
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        m_name = args.m_name.strip()
        ignore_file = self.__ignore + '/' + m_name + '.pl'
        if os.path.exists(ignore_file):
            os.remove(ignore_file)
        else:
            public.writeFile(ignore_file,'1')
        return public.returnMsg(True,'设置成功!')

    
    def check_find(self,args):
        '''
            @name 检测指定项
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        try:
            m_name = args.m_name.strip()
            p = public.get_modules('class/safe_warning')
            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }

            result_file = self.__result + '/' + m_name + '.pl'
            s_time = time.time()
            m_info['status'],m_info['msg'] = p[m_name].check_run()
            m_info['taking'] = round(time.time() - s_time,4)
            m_info['check_time'] = int(time.time())
            public.writeFile(result_file,json.dumps([m_info['status'],m_info['msg'],m_info['check_time'],m_info['taking']]))
            return public.returnMsg(True,'已重新检测')
        except:
            return public.returnMsg(False,'错误的模块名称')

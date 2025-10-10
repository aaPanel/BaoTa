#coding: utf-8
import public,os


class filesBase:


    __upload_objs = ['bos','alioss','obs','upyun','txcos']  #支持下载的云存储
    __down_objs = ['bos','alioss','txcos','obs']  #支持上传的云存储

    def __init__(self):
        pass


    #************************ start 对象存储 ************************
    def get_base_objects(self,objs):
        """
        @name 获取可上传的对象存储
        """
        import panelPlugin
        plu_obj = panelPlugin.panelPlugin()
        res = []
        for name in objs:
            is_conf = 0
            info = plu_obj.get_soft_find(name)
            if not info: continue
            if info['setup']:
                is_conf = self._check_objects_conf(info['name'])
            res.append({'name':info['name'],'title':info['title'],'setup':info['setup'],'is_conf':is_conf})
        return res

    def get_all_objects(self,get):
        """
        @name 获取可上传的对象存储
        """
        result = {}
        result['upload'] = []
        result['down'] = self.get_base_objects(self.__down_objs)
        for info in result['down']:
            if info['name'] in self.__upload_objs:
                result['upload'].append(info)
        return result



    def get_upload_objects(self,get):

        """
        @name 获取可上传的对象存储
        """
        return self.get_base_objects(self.__upload_objs)

    def get_down_objects(self,get):
        """
        @name 获取可下载的对象存储
        """
        return self.get_base_objects(self.__down_objs)


    def _check_objects_conf(self,plu_name):
        """
        @name 获取插件是否配置
        """
        plugin_obj = self.get_plugin_main_object(plu_name)

        args = public.dict_obj()
        args.path = '/bt_upload/'

        res = plugin_obj.get_config(args)
        if 'status' in res and not res['status']:
            return 0
        for key in res:
            if not isinstance(res[key], str): continue
            if not str(res[key]).strip(): return 0
        return 1


    def get_plugin_main_object(self,plugin_name):
        """
        @name 获取插件主对象
        @param plugin_name 插件名称
        """
        sys_path = '{}/plugin/{}'.format(public.get_panel_path(),plugin_name)
        if not os.path.exists(sys_path): return False
        public.sys_path_append(sys_path)

        os_file = '{}/{}_main.py'.format(sys_path,plugin_name)

        plugin_obj = __import__(plugin_name + '_main')
        plugin_obj = getattr(plugin_obj, plugin_name + '_main')()

        return plugin_obj


    def get_soft_find(self,name):
        """
        @获取插件详细
        """
        import panelPlugin
        plu_obj = panelPlugin.panelPlugin()

        return plu_obj.get_soft_find(name)


    #************************ end 对象存储 ************************
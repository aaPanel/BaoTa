# WP Toolkit security
# author: hzh<2024-07-02>
import public_wp as public
from public_wp import Param


# WP安全模块类
class wp_security:
        
    # 开启文件防护
    def open_file_protection(self, get):
        # 校验参数
        try:
            get.validate([
                Param('paths').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        tamper_core_status = public.run_plugin('tamper_core', 'get_service_status', public.to_dict_obj({}))
        if not (tamper_core_status["kernel_module_status"] and tamper_core_status["controller_status"]):
            return public.return_message(-1, 0, public.lang("打开失败请到应用商店-企业级防篡改查看详情"))

        result= public.run_plugin('tamper_core', 'multi_create', public.to_dict_obj({
            'paths': get.paths,
        }))
        if 'status' in result:
            return public.return_message(-1,0,result[0]['msg'])
        if type(result)==list:
            # for i in result:
                
            public.run_plugin('tamper_core', 'assign_rule_to_directory', public.to_dict_obj({
            'rule_group_name': 'WordPress Normal',
            'path_id': result[0]['pid'],
        })) 
            return public.return_message(0, 0, public.lang("开启成功"))
    
    #取安全防护配置
    def get_security_info(self, get):

        # 校验参数
        try:
            get.validate([
                Param('path').Require().String(),
                Param('site_name').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        return_result={
            'hotlink_status':0,
            'file_status':0,
            'firewall_status':0,
            'file_count':0,
            'firewall_count':0,
        }
        if get.path[-1] !='/':
            get.path+='/'
        #取文件防护配置
        try:
            tamper_core_status = public.run_plugin('tamper_core', 'get_service_status', public.to_dict_obj({}))
            if tamper_core_status["kernel_module_status"] and tamper_core_status["controller_status"]:
                result= public.run_plugin('tamper_core', 'get_tamper_paths', public.to_dict_obj({}))
                if type(result)==list:
                    for i in result:
                        if i['path']==get.path and i['status']==1:
                            return_result['file_status']=1
                            today=i['total']['today']
                            return_result['file_count']=int(today['create'])+int(today['modify'])+int(today['unlink'])+int(today['rename'])+int(today['mkdir'])+int(today['rmdir'])+int(today['chmod'])+int(today['chown'])+int(today['link'])
                            break
        except:pass

        #取防火墙配置
        result= public.run_plugin('btwaf', 'get_site_config_byname', public.to_dict_obj({'siteName':get.site_name}))
        try:
            if result['open']:
                return_result['firewall_status']=1
        except:
            pass
        result= public.run_plugin('btwaf', 'get_site_config3', public.to_dict_obj({'siteName':get.site_name}))
        try:
            if type(result['data'])==list:
                for i in result['data']:
                    if i['siteName']!=get.site_name:
                        continue
                    if type(i['total'])==list:
                        for total in i['total']:
                            return_result['firewall_count']+=int(total['value'])
        except:
            pass
                        
        return public.return_message(0,0,return_result)

   #关闭文件保护
    def close_file_protection(self, get):
        # 校验参数
        try:
            get.validate([
                Param('path_id').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        tamper_core_status = public.run_plugin('tamper_core', 'get_service_status', public.to_dict_obj({}))
        if not (tamper_core_status["kernel_module_status"] and tamper_core_status["controller_status"]):
            return public.return_message(-1, 0, public.lang("打开失败请到应用商店-企业级防篡改查看详情"))

        result= public.run_plugin('tamper_core', 'remove_path_config', public.to_dict_obj({
            'path_id': get.path_id,
        }))
        status=0
        if not result['status']:
            status=-1
        return public.return_message(status,0,result['msg'])
        
        
        
    # 开启防火墙防护
    def open_firewall_protection(self, get):
        # 校验参数
        try:
            get.validate([
                Param('site_name').Require().String(),
                Param('obj').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        
        result= public.run_plugin('btwaf', 'get_total_all', public.to_dict_obj({
        }))
        if not result['open']:
            result= public.run_plugin('btwaf', 'set_open', public.to_dict_obj({
            }))
            if not result['status']:
                return public.return_message(-1, 0, public.lang("开启失败"))
        
        result= public.run_plugin('btwaf', 'get_site_config_byname', public.to_dict_obj({
            'siteName': get.site_name,
        }))
        if not result['open']:
            result= public.run_plugin('btwaf', 'set_site_obj_open', public.to_dict_obj({
                    'siteName': get.site_name,
                    'obj': get.obj,
                }))
            if not result['status']:
                return public.return_message(-1, 0, public.lang("开启失败"))
        return public.return_message(0, 0, public.lang("开启成功"))
        
        
    # 关闭防火墙防护
    def close_firewall_protection(self, get):
        # 校验参数
        try:
            get.validate([
                Param('site_name').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        
        result= public.run_plugin('btwaf', 'set_site_obj_open', public.to_dict_obj({
            'siteName': get.site_name,
            'obj': 'open',
        }))
        if not result['status']:
            return public.return_message(-1, 0, public.lang("关闭失败"))
        return public.return_message(0, 0, public.lang("关闭成功"))
        
    # 获取防火墙防护配置
    def get_firewall_info(self, get):
        # 校验参数
        try:
            get.validate([
                Param('site_name').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        
        result= public.run_plugin('btwaf', 'get_site_config_byname', public.to_dict_obj({
            'siteName':get.site_name,
        }))
        return public.return_message(0,0,result)
        
        
    # 获取文件防护配置
    def get_file_info(self, get):
        # 校验参数
        try:
            get.validate([
                Param('path').Require().String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        if get.path[-1] !='/':
            get.path+='/'
        result= public.run_plugin('tamper_core', 'get_tamper_paths', public.to_dict_obj({
            'path':get.path,
        }))
        for i in result:
            if i['path']==get.path:
                return public.return_message(0,0,i)
        return public.return_message(0,0,{})
        
        
        
    

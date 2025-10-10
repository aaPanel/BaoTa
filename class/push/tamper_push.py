#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | Author: baozi
# +-------------------------------------------------------------------
import sys,os,re,json

import public,panelPush, time
from datetime import datetime, timedelta

try:
    from BTPanel import cache
except :
    from cachelib import SimpleCache
    cache = SimpleCache()

class base_push:

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data
    
    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError
    
    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        raise NotImplementedError
    
    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError
    
class tamper_push(base_push):
    __tamper_path = "{}/tamper".format(public.get_setup_path())
    __total_path = "{}/total/total.json".format(__tamper_path)
    __config_file = "{}/tamper.conf".format(__tamper_path)
    __push_conf =  "{}/class/push/push.json".format(public.get_panel_path())
    __logs_path = "{}/logs".format(__tamper_path)

    def __init__(self) -> None:
        self.__push = panelPush.panelPush()
        try:
            config = public.readFile(self.__config_file)
            config_dict = json.loads(config)
            self.__config = {}
            for i in config_dict["paths"]:
                self.__config[i["pid"]] = i
        except:
            self.__config  = None
      

        # 版本信息 目前无作用
    def get_version_info(self, get=None):
        data = {}
        data['ps'] = '宝塔企业版防篡改'
        data['version'] = '1.0'
        data['date'] = '2023-03-24'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(push = ["mail",'dingding','weixin',"feishu", "wx_account"], project = 'tamper',type = '')
        item['cycle'] = 30
        item['title'] = '防篡改'
        data.append(item)
        return data

        
    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        id = get.id
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        push_list = self.__push._get_conf()

        if not id in push_list["tamper_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["tamper_push"][id]
        return result
    

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        if self.__config is None:
            return public.returnMsg(False, '防篡改配置出错，无法设置，请尝试修复企业版防篡改.')
        try:
            id = int(get.id)
            if id != 0 and id not in self.__config:
                return public.returnMsg(False, '没有指定的保护目录')
        except ValueError:
            return public.returnMsg(False, '没有指定的保护目录')
            
        pdata = json.loads(get.data)
        data = self.__push._get_conf()
        if "tamper_push" not in data: data["tamper_push"] = {}
        if not str(id) in data["tamper_push"]:
            if id != 0:
                public.WriteLog("防篡改","保护目录:{} 设置了防篡改告警 ".format(self.__config[id]["path"]))
            else:
                public.WriteLog("防篡改","全目录设置了防篡改告警 ")
        else:
            if id != 0:
                public.WriteLog("防篡改","保护目录:{} 更改了告警配置".format(self.__config[id]["path"]))
            else:
                public.WriteLog("防篡改"," 全目录告警配置已更改")
            self._del_today_push_count(id)
        pdata["status"] = True
        pdata["pid"] = id
        pdata["project"] = "tamper_core"
        data["tamper_push"][str(id)] = pdata
        return data
    
    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        id = get.id
        data = self.__push._get_conf()
        if str(id).strip() in data["tamper_push"]:
            del data["tamper_push"][id]
        public.writeFile(self.__push_conf,json.dumps(data))
        return public.returnMsg(True, '删除成功.')

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # 返回内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        """
        @检测推送数据
        @data dict 推送数据
            title:标题
            count:触发次数
            cycle:周期 天、小时
            keys:检测键值
        """
        if not self._log_check(data["id"], data["cycle"], data["count"]): return None
        if data["push_count"] <= self._get_today_push_count(data["id"]):return None
        result = {'index': time.time(), }
        tamper_path = "所有保护目录" if not int(data["id"]) else "保护目录:{}".format(self.__config[int(data["id"])]["path"])
        for m_module in data['module'].split(','):
            if m_module == 'sms': continue
            s_list = [">通知类型：企业版防篡改告警", ">告警内容：<font color=#ff0000>在最近的{}分钟内{}被篡改攻击超过{}次，目前以成功拦截，请关注网站情况，并及时处理。</font> ".format(data['cycle'], tamper_path, data['count'])]
            sdata = public.get_push_info('企业版防篡改告警', s_list)
            result[m_module] = sdata
        self._set_total()
        self._set_today_push_count(data["id"])
        return result

    def _log_check(self, id, cycle, count):
        target_time = datetime.now() - timedelta(minutes=cycle)
        tday, yday = datetime.now().strftime('%Y-%m-%d'), (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        files = []
        if id == "0":
            for i in self.__config.keys():
                files.append("{}/{}/{}.log".format(self.__logs_path,i,tday))
                files.append("{}/{}/{}.log".format(self.__logs_path,i,yday))
        else:
            files.append("{}/{}/{}.log".format(self.__logs_path,id,tday))
            files.append("{}/{}/{}.log".format(self.__logs_path,id,yday))
        
        _count = 0
        _f = '%Y-%m-%d %H:%M:%S'
        for i in self._get_logs(files):
            if _count >= count:
                return True
            if datetime.strptime(i, _f) > target_time:
                _count += 1
            else:
                return _count >= count
        return _count >= count
    
    def _get_logs(self, files):
        def the_generator(self):
            _buf = b""
            for fp in self._get_fp():
                is_start = True
                while is_start:
                    buf = b''
                    while True:
                        pos = fp.tell()
                        read_size = pos if pos <= 38 else 38
                        fp.seek(-read_size, 1)
                        _buf = fp.read(read_size) + _buf
                        fp.seek(-read_size, 1)
                        nl_idx = _buf.rfind(ord('\n'))
                        if nl_idx == -1:
                            if pos <= 38: 
                                buf,  _buf = _buf, b''
                                is_start = False
                                break
                        else:
                            buf = _buf[nl_idx+1:]
                            _buf = _buf[:nl_idx]
                            break
                    yield self._get_time(buf.decode("utf-8"))
        
        def the_init(self,log_files):
            self.log_files = log_files

        def the_get_fp(self):
            for i in self.log_files:
                if not os.path.exists(i): continue
                with open(i, 'rb') as fp:
                    fp.seek(-1, 2)
                    yield fp
        
        def the_get_time(self, log: str):
            return log.split("] [", 1)[0].strip("[").strip()

        attr = {
            "__init__": the_init, 
            "_get_fp": the_get_fp, 
            "__iter__": the_generator,
            "_get_time": the_get_time,
        }
        return type("LogContent", (object, ), attr)(files)  

    def _set_total(self):
        try:
            total = json.loads(public.readFile(self.__total_path))
            if "warning_msg" not in total:
                total["warning_msg"] = 1
            else:
                total["warning_msg"] += 1
            public.writeFile(self.__total_path, json.dumps(total))
        except:
            pass
    
    def _get_today_push_count(self, id):
        t_day = datetime.now().strftime('%Y-%m-%d')
        today_tip = '{}/data/push/tips/tamper_today.json'.format(public.get_panel_path())
        if os.path.exists(today_tip):
            tip = json.loads(public.readFile(today_tip))
            if tip["t_day"] != t_day:
                tip = {"t_day": t_day}
                res = 0
            elif id in tip:
                res = tip[id]
            else:
                res = 0
        else:
            tip = {"t_day": t_day}
            res = 0

        public.writeFile(today_tip, json.dumps(tip))
        setattr(self, "_tip_", tip)
        return res


    def _set_today_push_count(self, id):
        today_tip = '{}/data/push/tips/tamper_today.json'.format(public.get_panel_path())
        if hasattr(self, "_tip_"):
            tip = getattr(self, "_tip_")
        else:
            tip = json.loads(public.readFile(today_tip))
        if id in tip:
            tip[id] += 1
        else:
            tip[id] = 1

        public.writeFile(today_tip, json.dumps(tip))
    
    def _del_today_push_count(self, id):
        t_day = datetime.now().strftime('%Y-%m-%d')
        today_tip = '{}/data/push/tips/tamper_today.json'.format(public.get_panel_path())
        if os.path.exists(today_tip):
            tip = json.loads(public.readFile(today_tip))
            if tip["t_day"] != t_day:
                tip = {"t_day": t_day}
            elif id in tip:
                del tip[id]

            public.writeFile(today_tip, json.dumps(tip))
        
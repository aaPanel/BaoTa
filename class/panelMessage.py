#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <2020-05-18>
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# | 消息提醒
# +-------------------------------------------------------------------
import time
import json
import public
try:
    from BTPanel import cache
except :
    import cachelib
    cache = cachelib.SimpleCache()

class panelMessage:
    os = 'linux'

    def set_send_status(self, id, data):
        '''
            @name 设置消息发送状态
            @author cjxin <2021-04-12>
            @param args dict_obj{
                id: 消息标识,
                data
            }
            @return dict
        '''

        public.M('messages').where('id=?',id).update(data)
        return public.returnMsg(True,'设置成功!')


    """
    获取官网推送消息，一天获取一次
    """
    def get_cloud_messages(self,args):

        try:
            ret = cache.get('get_cloud_messages')
            if ret: return public.returnMsg(True,'同步成功1!')
            data = {}
            data['version'] = public.version()
            data['os'] = self.os
            sUrl = public.GetConfigValue('home') + '/api/wpanel/get_messages'
            import http_requests
            http_requests.DEFAULT_TYPE = 'src'
            info = http_requests.post(sUrl,data).json()
            # info = json.loads(public.httpPost(sUrl,data))
            for x in info:
                count = public.M('messages').where('level=? and msg=?',(x['level'],x['msg'],)).count()
                if count: continue

                pdata = {
                    "level":x['level'],
                    "msg":x['msg'],
                    "state":1,
                    "expire":int(time.time()) + (int(x['expire']) * 86400),
                    "addtime": int(time.time())
                }
                public.M('messages').insert(pdata)
            cache.set('get_cloud_messages',86400)
            return public.returnMsg(True,'同步成功!')
        except:
            return public.returnMsg(False,'同步失败!')

    def get_messages(self,args = None):
        '''
            @name 获取消息列表
            @author hwliang <2020-05-18>
            @return list
        '''
        ikey = 'get_message'
        data = cache.get(ikey)
        if not data:
            if not public.is_aarch():
                public.run_thread(self.get_cloud_messages,args=(args,))
            data = public.M('messages').where('state=? and expire>?',(1,int(time.time()))).order("id desc").select()
            cache.set(ikey,data,86400)
        return data

    def get_messages_all(self,args = None):
        '''
            @name 获取所有消息列表
            @author hwliang <2020-05-18>
            @return list
        '''
        public.run_thread(self.get_cloud_messages,args=(args,))
        data = public.M('messages').order("id desc").select()
        return data

    def get_message_find(self,args = None,id = None):
        '''
            @name 获取指定消息
            @author hwliang <2020-05-18>
            @param args dict_obj{
                id: 消息标识
            }
            @return dict
        '''
        if args:
            id = int(args.id)
        data = public.M('messages').where('id=?',id).find()
        return data


    def create_message(self,args = None,level=None,msg=None,expire=None):
        '''
            @name 创建新的消息
            @author hwliang <2020-05-18>
            @param args dict_obj{
                level: 消息级别(info/warning/danger/error),
                msg: 消息内容
                expire: 过期时间
            }
            @return dict
        '''
        if args:
            level = args.level
            msg = args.msg
            expire = args.expire
        pdata = {
            "level":level,
            "msg":msg,
            "state":1,
            "expire":int(time.time()) + (int(expire) * 86400),
            "addtime": int(time.time())
        }

        public.M('messages').insert(pdata)
        return public.returnMsg(True,'创建成功!')

    def status_message(self,args = None,id = None,state = None):
        '''
            @name 设置消息状态
            @author hwliang <2020-05-18>
            @param args dict_obj{
                id: 消息标识,
                state: 消息状态(0.已忽略, 1.正常)
            }
            @return dict
        '''
        if args:
            id = int(args.id)
            state = int(args.state)
        public.M('messages').where('id=?',id).setField('state',state)
        return public.returnMsg(True,'设置成功!')


    def remove_message(self,args = None,id = None):
        '''
            @name 删除指定消息
            @author hwliang <2020-05-18>
            @param args dict_obj{
                id: 消息标识
            }
            @return dict
        '''
        if args:
            id = int(args.id)
        public.M('messages').where('id=?',id).delete()
        return public.returnMsg(True,'删除成功!')

    def remove_message_level(self,level):
        '''
            @name 删除指定消息
            @author hwliang <2020-05-18>
            @param level string(指定级别或标识)
            @return bool
        '''
        public.M('messages').where('(level=? or level=? or level=? or level=?) and state=?',(level,level+'15',level+'7',level+'3',1)).delete()
        return True

    def remove_message_all(self):
        public.M('messages').where('state=?',(1,)).delete()
        return True

    def is_level(self,level):
        '''
            @name 指定消息是否忽略
            @author hwliang <2020-05-18>
            @param level string(指定级别或标识)
            @return bool
        '''
        if public.M('messages').where('level=? and state=?',(level,0)).count():
            return False
        else:
            return True

    def init_msg_module(self, module):
        """
        初始化消息通道, 迁移自windows
        @module 消息通道模块名称
        @author lx
        """
        try:
            # 统一使用public中的方式处理
            ret = public.init_msg(module)
            if ret and hasattr(ret, "send_msg"):
                return ret
            import os, sys
            if not os.path.exists('class/msg'): os.makedirs('class/msg')
            panelPath = "/www/server/panel"

            if  "{}/class/msg".format(panelPath) not in sys.path:
                sys.path.insert(0, "{}/class/msg".format(panelPath))

            if module in ("dingding", "feishu", "mail", "sms", "weixin", "wx_account"):
                sfile = 'class/msg/{}_msg.py'.format(module)
                if not os.path.exists(sfile):
                    return False
                msg_main = __import__('{}_msg'.format(module))
                is_hook = False
            else:
                sfile = 'class/msg/web_hook_msg.py'
                if not os.path.exists(sfile):
                    return False
                msg_main = __import__('web_hook_msg')
                is_hook = True
            try:
                public.reload_mod(msg_main)
            except:
                pass
            if is_hook:
                if module == "web_hook":
                    module = None
                msg_cls_obj = getattr(msg_main, "web_hook_msg")(module)
                return msg_cls_obj
            return eval('msg_main.{}_msg()'.format(module))
        except:
            return None

    def get_default_channel(self, args=None):
        """获取面板默认消息通道
        Returns:
            channel: str/None，没有安装消息通道的情况下返回None。
        """
        default_channel_pl = "/www/server/panel/data/default_msg_channel.pl"
        default_channel = public.readFile(default_channel_pl)
        if default_channel:
            return public.returnMsg(True, default_channel)
        return public.returnMsg(False, "")

    # def get_default_channel(self):
    #     """获取面板默认消息通道，默认是邮箱，其次默认选择已安装的第一个消息通道

    #     Returns:
    #         channel: str/None，没有安装消息通道的情况下返回None。
    #     """
    #     from config import config
    #     c = config()
    #     get = public.dict_obj()
    #     configs = c.get_msg_configs(get)
    #     installed = []
    #     for channel, obj in configs.items():
    #         if "setup" in obj and obj["setup"]:
    #             installed.append(channel)
    #             if "default" in obj and obj["default"]:
    #                 return channel
    #     if "mail" in installed:
    #         return "mail"
    #     if installed:
    #         return installed[0]
    #     return None

    def notify(self, args):
        """发送通知

        Args:
            args (dict):
            title: 消息标题
            msg: 消息内容
            channel: 消息通道
        """

        msg = ""
        if "msg" in args:
            body = args.msg
        title = ""
        if "title" in args:
            title = args.title
        sm_type = None
        if "sm_type" in args:
            sm_type = args.sm_type
        sm_args = {}
        if "sm_args" in args:
            sm_args = json.loads(args.sm_args)
        channel = None
        channels = []
        if "channel" in args:
            channel = args.channel
            if channel.find(",") != -1:
                channels = channel.split(",")
            else:
                channels = [channel]
        if not channel:
            channel_res = self.get_default_channel()
            if "msg" in channel_res:
                channels = [channel_res["msg"]]
        if not channels:
            return False
        try:
            from config import config
            c = config()
            get = public.dict_obj()
            msg_channels = c.get_msg_configs(get)

            error_channel = []
            channel_data = {}
            for ch in channels:
                msg_data = {}
                # 根据不同的消息通道准备不同的内容
                if ch == "mail":
                    # 如果邮箱通知，没有标题直接跳过
                    if not title: continue
                    msg_data = {
                        "msg": body.replace("\n", "<br/>"),
                        "title": title
                    }
                if ch in ["dingding", "weixin", "feishu"]:
                    # 钉钉类必须有消息内容
                    if not body: continue
                    msg_data["msg"] = body
                if ch in ["sms"]:
                    # 短信必须指定短信模板名
                    if not sm_type: continue
                    msg_data["sm_type"] = sm_type
                    msg_data["sm_args"] = sm_args
                if not msg_data:
                    channel_data[ch] = args
            # print("channel data:")
            # print(channel_data)
            # 即时推送

            from panelPush import panelPush
            pp = panelPush()
            error_count = 0
            push_res = pp.push_message_immediately(channel_data)
            if push_res["status"]:
                channel_res = push_res["msg"]
                for ch, res in channel_res.items():
                    if not res["status"]:
                        if ch in msg_channels:
                            error_channel.append(msg_channels[ch]["title"])
                            error_count +=1
            if error_count == len(channels):
                return False
            return True
        except Exception as e:
            return False
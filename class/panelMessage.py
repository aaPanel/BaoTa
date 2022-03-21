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
import os,sys,time
import public,json
if os.environ.get('BT_TASK') != '1':
    from BTPanel import cache
else:
    import cachelib
    cache = cachelib.SimpleCache()

class panelMessage:
    os = 'linux'

    def __init__(self):
        if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'messages','%retry_num%')).count():
            public.M('messages').execute("alter TABLE messages add send integer DEFAULT 0",())
            public.M('messages').execute("alter TABLE messages add retry_num integer DEFAULT 0",())
        pass


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
    获取官网推送消息，一小时获取一次
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
            cache.set('get_cloud_messages',3600)
            return public.returnMsg(True,'同步成功!')
        except:
            return public.returnMsg(False,'同步失败!')

    def get_messages(self,args = None):
        '''
            @name 获取消息列表
            @author hwliang <2020-05-18>
            @return list
        '''
        public.run_thread(self.get_cloud_messages,args=(args,))
        data = public.M('messages').where('state=? and expire>?',(1,int(time.time()))).order("id desc").select()
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




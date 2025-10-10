#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lotk
# | 邮局调用退订接口(免登录)
# +-------------------------------------------------------------------
from mod.base import public_aap as public
import os,sys,db,time,json,re


try:
    import jwt
except:
    public.ExecShell('btpip install pyjwt')
    import jwt


class mailUnsubscribe:

    postfix_recipient_blacklist = '/etc/postfix/blacklist'
    # 获取 SECRET_KEY
    def get_SECRET_KEY(self):
        path = '/www/server/panel/data/mail/jwt-secret.txt'
        if not os.path.exists(path):
            secretKey = public.GetRandomString(64)
            public.writeFile(path, secretKey)
        secretKey = public.readFile(path)
        return secretKey
    def M(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/postfixadmin.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)
    def M3(self, table_name):
        import db
        sql = db.Sql()
        sql._Sql__DB_FILE = '/www/vmail/mail_unsubscribe.db'
        sql._Sql__encrypt_keys = []
        return sql.table(table_name)

    def Unsubscribe(self, get):
        token = get.get('jwt', '')
        if not token:
            return 'There is no token'
        SECRET_KEY = self.get_SECRET_KEY()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            email = payload['email']
            # etypename = payload['etypename']  # 邮件类型名

            # 兼容旧退订 邮件类型id
            etypes = payload.get('etypes', '')
            if not etypes:
                etypes = payload.get('etype', '')

            task_id = payload.get('task_id', 0)  # 群发任务
            self.submit_recipient_blacklist(email, etypes, task_id)

            return public.lang("The unsubscribe of email {} is successful", email)
            # return public.lang("Email [{}] has successfully unsubscribed [{}] type email", email, etypename)
        except jwt.ExpiredSignatureError:
            return public.lang('Operation failed,The token expires')
        except jwt.InvalidTokenError:
            return public.lang('Operation failed,Invalid tokens')
        except Exception as e:
            return False

    # 订阅调用  获取类型和邮箱  判断邮箱可用?(邮箱校验 校验后插入)  可用插入数据库   (邮箱校验和邮箱发送营销邮件)
    def Subscribe(self, get):
        etype = get.get('etype', '')
        public.print_log('etype   {}'.format(etype))

        email = get.get('email', '')
        public.print_log('email   {}'.format(email))

        # todo 验证邮箱   生成验证链接


        # 查询类型存在
        etype = int(etype)
        with self.M('mail_type') as obj:
            etype_exit = obj.where('id =?', etype).count()
        if not etype_exit:
            # 无对应类型跳过
            return

        # 插入邮箱
        with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
            # 有退订 改为订阅
            exit_un = obj.where('recipient', email).where('etype', etype).where('active', 0).count()
            if exit_un:
                obj.where('recipient', email).where('etype', etype).update({'active': 1})
                return

            # 不存在 新增
            exit = obj.where('recipient', email).where('etype', etype).where('active', 1).count()
            if not exit:
                created = int(time.time())
                insert = {
                    'created': created,
                    'recipient': email,
                    'etype': etype,
                    'active': 1,
                }
                obj.insert(insert)
        return


    # 退订接口调用的提交黑名单
    def submit_recipient_blacklist(self, email, etypes, task_id):
        created = int(time.time())
        etype_list = etypes.split(",")

        with self.M('mail_type') as obj:
            data_list = obj.select()
        types = {str(item["id"]): item["mail_type"] for item in data_list}
        try:
            with public.S("mail_unsubscribe", '/www/vmail/mail_unsubscribe.db') as obj:
                for etype in etype_list:
                    etype = int(etype)
                    if not types.get(str(etype), None):
                        continue

                    # 有退订 跳过
                    exit_un = obj.where('recipient', email).where('etype', etype).where('active', 0).count()
                    if exit_un:
                        continue

                    # 有订阅 改为退订记录任务    无订阅 新增退订
                    exit = obj.where('recipient', email).where('etype', etype).where('active', 1).count()
                    if not exit:
                        insert = {
                            'created': created,
                            'recipient': email,
                            'etype': etype,
                            'task_id': task_id,
                        }
                        aa = obj.insert(insert)
                        public.print_log(f"  sdsssc1  {aa}")
                    else:
                        bb = obj.where('recipient', email).where('etype', etype).update({'active': 0, 'task_id': task_id})
                        public.print_log(f"  sdsssc3  {bb}")
                        continue
            return True
        except Exception as e:
            return False
#!/usr/bin/python
import json #line:4
import os ,time #line:5
from projectModel .base import projectBase #line:6
import public #line:7
from BTPanel import cache #line:8
class main (projectBase ):#line:10
    __O000OO000OOOOOO00 =public .Md5 ('clear'+time .strftime ('%Y-%m-%d'))#line:11
    __OOOO0O0OOO00O0O0O ='/www/server/panel/config/clear_log.json'#line:12
    __OO000OOOOO0OOO0OO ='/www/server/panel/data/clear'#line:13
    __OO00O000000OO0000 =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:16
    def __init__ (OO0OO000O0OO0000O ):#line:18
        if not os .path .exists (OO0OO000O0OO0000O .__OO000OOOOO0OOO0OO ):#line:19
            os .makedirs (OO0OO000O0OO0000O .__OO000OOOOO0OOO0OO ,384 )#line:20
    def __O000OO00O0OO0O00O (O0O00O00O00OO0OO0 ):#line:22
        # from pluginAuth import Plugin #line:23
        import PluginLoader
        O00000O0O0OOOOOOO =PluginLoader.get_plugin_list (0)#line:25
        return int (O00000O0O0OOOOOOO ['ltd'])>time .time ()#line:26
    def get_config (O0OO0O00OOOOO00OO ):#line:30
        ""#line:35
        if not os .path .exists (O0OO0O00OOOOO00OO .__OOOO0O0OOO00O0O0O ):#line:36
            O0OO0O00OOOOO00OO .write_config ()#line:37
            return O0OO0O00OOOOO00OO .default_config ()#line:38
        else :#line:39
            try :#line:40
                O00OOOOO0O0O00000 =json .loads (public .ReadFile (O0OO0O00OOOOO00OO .__OOOO0O0OOO00O0O0O ))#line:41
            except :#line:42
                O0OO0O00OOOOO00OO .write_config ()#line:43
                return O0OO0O00OOOOO00OO .default_config ()#line:44
        if not cache .get (O0OO0O00OOOOO00OO .__O000OO000OOOOOO00 ):#line:45
            try :#line:46
                import requests #line:47
                O00OOOOO0O0O00000 =requests .get ("https://www.bt.cn/api/bt_waf/clearLog").json ()#line:48
                cache .set (O0OO0O00OOOOO00OO .__O000OO000OOOOOO00 ,'1',1800 )#line:49
                O0OO0O00OOOOO00OO .write_config (O00OOOOO0O0O00000 )#line:50
            except :#line:51
                return O0OO0O00OOOOO00OO .default_config ()#line:52
            return O00OOOOO0O0O00000 #line:53
        else :#line:54
            return O00OOOOO0O0O00000 #line:55
    def write_config (O0O0O0OOOO000O0O0 ,config =False ):#line:57
        ""#line:63
        if config :#line:64
            public .WriteFile (O0O0O0OOOO000O0O0 .__OOOO0O0OOO00O0O0O ,json .dumps (config ))#line:65
        else :#line:66
            public .WriteFile (O0O0O0OOOO000O0O0 .__OOOO0O0OOO00O0O0O ,json .dumps (O0O0O0OOOO000O0O0 .default_config ()))#line:67
    def default_config (O0O0OO0OO00O00O0O ):#line:70
        ""#line:75
        return [{"name":"recycle1","ps":"面板备份文件","path":"/www/backup/panel","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"recycle2","ps":"面板文件备份","path":"/www/backup/file_history","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"docker","ps":"Docker容器日志","path":"/var/lib/docker/containers","type":"file","is_del":False ,"find":["-json.log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"openrasp","ps":"openrasp日志","path":["/opt/rasp55/logs/alarm","/opt/rasp55/logs/policy","/opt/rasp55/logs/plugin","/opt/rasp56/logs/alarm","/opt/rasp56/logs/policy","/opt/rasp56/logs/plugin","/opt/rasp70/logs/alarm","/opt/rasp70/logs/policy","/opt/rasp70/logs/plugin","/opt/rasp71/logs/alarm","/opt/rasp71/logs/policy","/opt/rasp72/logs/plugin","/opt/rasp73/logs/alarm","/opt/rasp73/logs/policy","/opt/rasp73/logs/plugin","/opt/rasp74/logs/alarm","/opt/rasp74/logs/policy","/opt/rasp74/logs/plugin"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"springboot","ps":"springboot日志","path":"/var/tmp/springboot/vhost/logs","type":"file","is_del":False ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"aliyun","ps":"阿里云Agent日志","path":["/usr/local/share/aliyun-assist/2.2.3.247/log","/usr/local/share/aliyun-assist/2.2.3.256/log"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"qcloud","ps":"腾讯云Agent日志","path":["/usr/local/qcloud/tat_agent/log","/usr/local/qcloud/YunJing/log","/usr/local/qcloud/stargate/logs","/usr/local/qcloud/monitor/barad/log"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"crontab","ps":"计划任务日志","path":"/www/server/cron","type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"tomcat","ps":"tomcat日志","path":["/usr/local/bttomcat/tomcat8/logs","/usr/local/bttomcat/tomcat9/logs","/usr/local/bttomcat/tomcat7/logs"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"panellog","ps":"面板日志","path":"/www/server/panel/logs/request","type":"file","is_del":True ,"find":[".json.gz"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"recycle3","ps":"回收站","path":"/www/Recycle_bin","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"maillog","ps":"邮件日志","path":"/var/spool/mail","type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"btwaflog","ps":"防火墙日志","path":["/www/wwwlogs/btwaf","/www/server/btwaf/totla_db/http_log"],"type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"weblog","ps":"网站日志","path":"/www/wwwlogs","type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"syslog","ps":"系统日志","path":["/var/log/audit","/var/log"],"type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"package","ps":"面板遗留文件","path":"/www/server/panel/package","type":"file","is_del":True ,"find":[".zip"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"mysqllog","ps":"数据库日志","path":"/www/server/data","type":"file","is_del":True ,"find":["mysql-bin.00"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"session","ps":"session日志","path":"/tmp","type":"file","is_del":True ,"find":["sess_"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"bttotal","ps":"网站监控报表日志","path":"/www/server/total/logs","type":"file","is_del":True ,"find":["_bt_"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 }]#line:96
    def tosize (O00O00O00O000O0OO ,O0OOO00O00OOOOOO0 ):#line:98
        ""#line:104
        O000O0O0OOOO0O0OO =['b','KB','MB','GB','TB']#line:105
        for OO0O00OOO000O0O0O in O000O0O0OOOO0O0OO :#line:106
            if O0OOO00O00OOOOOO0 <1024 :#line:107
                return str (int (O0OOO00O00OOOOOO0 ))+OO0O00OOO000O0O0O #line:108
            O0OOO00O00OOOOOO0 =O0OOO00O00OOOOOO0 /1024 #line:109
        return '0b'#line:110
    def any_size (OO00O0OOO0O0OOOOO ,OOOO0O000O000O0O0 ):#line:112
        ""#line:118
        OOOO0O000O000O0O0 =str (OOOO0O000O000O0O0 )#line:119
        OO0OOO0OOOO0OO0O0 =OOOO0O000O000O0O0 [-1 ]#line:120
        try :#line:121
            OOO00OO0O00OO000O =float (OOOO0O000O000O0O0 [0 :-1 ])#line:122
        except :#line:123
            OOO00OO0O00OO000O =0 #line:124
            return OOOO0O000O000O0O0 #line:125
        O00000O0O0000OOOO =['b','K','M','G','T']#line:126
        if OO0OOO0OOOO0OO0O0 in O00000O0O0000OOOO :#line:127
            if OO0OOO0OOOO0OO0O0 =='b':#line:128
                return int (OOO00OO0O00OO000O )#line:129
            elif OO0OOO0OOOO0OO0O0 =='K':#line:130
                OOO00OO0O00OO000O =OOO00OO0O00OO000O *1024 #line:131
                return int (OOO00OO0O00OO000O )#line:132
            elif OO0OOO0OOOO0OO0O0 =='M':#line:133
                OOO00OO0O00OO000O =OOO00OO0O00OO000O *1024 *1024 #line:134
                return int (OOO00OO0O00OO000O )#line:135
            elif OO0OOO0OOOO0OO0O0 =='G':#line:136
                OOO00OO0O00OO000O =OOO00OO0O00OO000O *1024 *1024 *1024 #line:137
                return int (OOO00OO0O00OO000O )#line:138
            elif OO0OOO0OOOO0OO0O0 =='T':#line:139
                OOO00OO0O00OO000O =OOO00OO0O00OO000O *1024 *1024 *1024 *1024 #line:140
                return int (OOO00OO0O00OO000O )#line:141
            else :#line:142
                return int (OOO00OO0O00OO000O )#line:143
        else :#line:144
            return '0b'#line:145
    def get_path_file (O000OO0OO0OOOO0OO ,O00O000O0OOOOO0OO ):#line:148
        ""#line:154
        if type (O00O000O0OOOOO0OO ['path'])==list :#line:155
            for O00000OO0000OO00O in O00O000O0OOOOO0OO ['path']:#line:156
                if os .path .exists (O00000OO0000OO00O ):#line:157
                    for OOOO0OOO0OOOO0OO0 in os .listdir (O00000OO0000OO00O ):#line:158
                        OOOO0O0000OOOO0OO =O00000OO0000OO00O +'/'+OOOO0OOO0OOOO0OO0 #line:159
                        if O00O000O0OOOOO0OO ['type']=='file':#line:160
                            if os .path .isfile (OOOO0O0000OOOO0OO ):#line:161
                                O000O000O0O0OOOO0 ={}#line:162
                                O0OOO0O000O0O0OOO =os .path .getsize (OOOO0O0000OOOO0OO )#line:163
                                if O0OOO0O000O0O0OOO >=100 :#line:164
                                    O000O000O0O0OOOO0 ['size']=O000OO0OO0OOOO0OO .tosize (O0OOO0O000O0O0OOO )#line:165
                                    O000O000O0O0OOOO0 ['count_size']=O0OOO0O000O0O0OOO #line:166
                                    O00O000O0OOOOO0OO ['size']+=O0OOO0O000O0O0OOO #line:167
                                    O000O000O0O0OOOO0 ['name']=OOOO0O0000OOOO0OO #line:168
                                    O00O000O0OOOOO0OO ['result'].append (O000O000O0O0OOOO0 )#line:169
        else :#line:170
            if os .path .exists (O00O000O0OOOOO0OO ['path']):#line:171
                for OOOO0OOO0OOOO0OO0 in os .listdir (O00O000O0OOOOO0OO ['path']):#line:172
                    OOOO0O0000OOOO0OO =O00O000O0OOOOO0OO ['path']+'/'+OOOO0OOO0OOOO0OO0 #line:173
                    if O00O000O0OOOOO0OO ['type']=='file':#line:174
                        if os .path .isfile (OOOO0O0000OOOO0OO ):#line:175
                            O000O000O0O0OOOO0 ={}#line:176
                            O0OOO0O000O0O0OOO =os .path .getsize (OOOO0O0000OOOO0OO )#line:177
                            if O0OOO0O000O0O0OOO >=100 :#line:178
                                O000O000O0O0OOOO0 ['size']=O000OO0OO0OOOO0OO .tosize (O0OOO0O000O0O0OOO )#line:179
                                O000O000O0O0OOOO0 ['count_size']=O0OOO0O000O0O0OOO #line:180
                                O00O000O0OOOOO0OO ['size']+=O0OOO0O000O0O0OOO #line:181
                                O000O000O0O0OOOO0 ['name']=OOOO0O0000OOOO0OO #line:182
                                O00O000O0OOOOO0OO ['result'].append (O000O000O0O0OOOO0 )#line:183
                    elif O00O000O0OOOOO0OO ['type']=='dir':#line:184
                        if os .path .isdir (OOOO0O0000OOOO0OO ):#line:185
                            O0OOO0O000O0O0OOO =public .ExecShell ('du -sh  %s'%OOOO0O0000OOOO0OO )[0 ].split ()[0 ]#line:186
                            O000O000O0O0OOOO0 ={}#line:187
                            O000O000O0O0OOOO0 ['dir']='dir'#line:188
                            O000O000O0O0OOOO0 ['size']=O0OOO0O000O0O0OOO #line:189
                            O000O000O0O0OOOO0 ['count_size']=O000OO0OO0OOOO0OO .any_size (O0OOO0O000O0O0OOO )#line:190
                            if O000O000O0O0OOOO0 ['count_size']<100 :continue #line:191
                            if O00O000O0OOOOO0OO ['path']=='/www/Recycle_bin':#line:192
                                OOOO0O0000OOOO0OO =OOOO0OOO0OOOO0OO0 .split ('_t_')[0 ].replace ('_bt_','/')#line:193
                                O000O000O0O0OOOO0 ['filename']=O00O000O0OOOOO0OO ['path']+'/'+OOOO0OOO0OOOO0OO0 #line:194
                                O000O000O0O0OOOO0 ['name']=OOOO0O0000OOOO0OO #line:195
                            else :#line:196
                                O000O000O0O0OOOO0 ['filename']=O00O000O0OOOOO0OO ['path']+'/'+OOOO0OOO0OOOO0OO0 #line:197
                                O000O000O0O0OOOO0 ['name']=os .path .basename (OOOO0O0000OOOO0OO )#line:198
                            O00O000O0OOOOO0OO ['size']+=O000O000O0O0OOOO0 ['count_size']#line:199
                            O00O000O0OOOOO0OO ['result'].append (O000O000O0O0OOOO0 )#line:200
                        else :#line:201
                            O0OO000O0OO000000 =os .path .getsize (OOOO0O0000OOOO0OO )#line:202
                            if O0OO000O0OO000000 <100 :continue #line:204
                            O000O000O0O0OOOO0 ={}#line:205
                            O000O000O0O0OOOO0 ['filename']=OOOO0O0000OOOO0OO #line:206
                            OOOO0O0000OOOO0OO =os .path .basename (OOOO0O0000OOOO0OO )#line:208
                            O000O000O0O0OOOO0 ['count_size']=O0OO000O0OO000000 #line:209
                            if O00O000O0OOOOO0OO ['path']=='/www/Recycle_bin':#line:210
                                OOOO0O0000OOOO0OO =OOOO0OOO0OOOO0OO0 .split ('_t_')[0 ].replace ('_bt_','/')#line:211
                                O000O000O0O0OOOO0 ['name']=OOOO0O0000OOOO0OO #line:212
                            else :#line:213
                                O000O000O0O0OOOO0 ['name']=OOOO0O0000OOOO0OO #line:214
                            O000O000O0O0OOOO0 ['size']=O000OO0OO0OOOO0OO .tosize (O0OO000O0OO000000 )#line:215
                            O00O000O0OOOOO0OO ['size']+=O000O000O0O0OOOO0 ['count_size']#line:216
                            O00O000O0OOOOO0OO ['result'].append (O000O000O0O0OOOO0 )#line:217
        return O00O000O0OOOOO0OO #line:218
    def get_path_find (OO0O0OO0O00OO0000 ,O00O00000OOOO0O00 ):#line:221
        ""#line:228
        if type (O00O00000OOOO0O00 ['path'])==list :#line:229
            for O000000OO00OO00O0 in O00O00000OOOO0O00 ['path']:#line:230
                if os .path .exists (O000000OO00OO00O0 ):#line:231
                    for OOOOOOO00O00O0O0O in os .listdir (O000000OO00OO00O0 ):#line:232
                        for O0000O0OOOO0OO0O0 in O00O00000OOOO0O00 ['find']:#line:233
                            if OOOOOOO00O00O0O0O .find (O0000O0OOOO0OO0O0 )==-1 :continue #line:234
                            O0OOOOO00O0O00O0O =O000000OO00OO00O0 +'/'+OOOOOOO00O00O0O0O #line:235
                            if not os .path .exists (O0OOOOO00O0O00O0O ):continue #line:236
                            OO000OOO00OOO0O00 =os .path .getsize (O0OOOOO00O0O00O0O )#line:237
                            if OO000OOO00OOO0O00 <1024 :continue #line:238
                            OO00OOOOOO0000000 ={}#line:239
                            OO00OOOOOO0000000 ['name']=O0OOOOO00O0O00O0O #line:240
                            OO00OOOOOO0000000 ['count_size']=OO000OOO00OOO0O00 #line:241
                            O00O00000OOOO0O00 ['size']+=OO000OOO00OOO0O00 #line:242
                            OO00OOOOOO0000000 ['size']=OO0O0OO0O00OO0000 .tosize (OO000OOO00OOO0O00 )#line:243
                            O00O00000OOOO0O00 ['result'].append (OO00OOOOOO0000000 )#line:244
        else :#line:245
            if os .path .exists (O00O00000OOOO0O00 ['path']):#line:246
                for OOOOOOO00O00O0O0O in os .listdir (O00O00000OOOO0O00 ['path']):#line:247
                    for O0000O0OOOO0OO0O0 in O00O00000OOOO0O00 ['find']:#line:248
                        O0OOOOO00O0O00O0O =O00O00000OOOO0O00 ['path']+'/'+OOOOOOO00O00O0O0O #line:249
                        if O00O00000OOOO0O00 ['path']=='/var/lib/docker/containers':#line:250
                            O0OOOOO00O0O00O0O =O0OOOOO00O0O00O0O +'/'+OOOOOOO00O00O0O0O +'-json.log'#line:251
                            if os .path .exists (O0OOOOO00O0O00O0O ):#line:252
                                OO000OOO00OOO0O00 =os .path .getsize (O0OOOOO00O0O00O0O )#line:253
                                if OO000OOO00OOO0O00 <1024 :continue #line:254
                                OO00OOOOOO0000000 ={}#line:255
                                OO00OOOOOO0000000 ['name']=O0OOOOO00O0O00O0O #line:256
                                OO00OOOOOO0000000 ['count_size']=OO000OOO00OOO0O00 #line:257
                                O00O00000OOOO0O00 ['size']+=OO000OOO00OOO0O00 #line:258
                                OO00OOOOOO0000000 ['size']=OO0O0OO0O00OO0000 .tosize (OO000OOO00OOO0O00 )#line:259
                                O00O00000OOOO0O00 ['result'].append (OO00OOOOOO0000000 )#line:260
                        else :#line:261
                            if OOOOOOO00O00O0O0O .find (O0000O0OOOO0OO0O0 )==-1 :continue #line:262
                            if not os .path .exists (O0OOOOO00O0O00O0O ):continue #line:263
                            OO000OOO00OOO0O00 =os .path .getsize (O0OOOOO00O0O00O0O )#line:264
                            if OO000OOO00OOO0O00 <1024 :continue #line:265
                            OO00OOOOOO0000000 ={}#line:266
                            OO00OOOOOO0000000 ['name']=O0OOOOO00O0O00O0O #line:267
                            OO00OOOOOO0000000 ['count_size']=OO000OOO00OOO0O00 #line:268
                            O00O00000OOOO0O00 ['size']+=OO000OOO00OOO0O00 #line:269
                            OO00OOOOOO0000000 ['size']=OO0O0OO0O00OO0000 .tosize (OO000OOO00OOO0O00 )#line:270
                            O00O00000OOOO0O00 ['result'].append (OO00OOOOOO0000000 )#line:271
        return O00O00000OOOO0O00 #line:272
    def scanning (O0000O0O000OO000O ,OO0O0O0O000O00OOO ):#line:274
        ""#line:278
        if not O0000O0O000OO000O .__O000OO00O0OO0O00O ():return public .returnMsg (False ,O0000O0O000OO000O .__OO00O000000OO0000 )#line:279
        O0000O000OO0OO00O =0 #line:280
        O0OOO000O0OOOO00O =O0000O0O000OO000O .get_config ()#line:281
        OOOO0O0OOO00O0O0O =int (time .time ())#line:282
        public .WriteFile (O0000O0O000OO000O .__OO000OOOOO0OOO0OO +'/scanning',str (OOOO0O0OOO00O0O0O ))#line:283
        for O00OOO00O0O00O000 in O0OOO000O0OOOO00O :#line:284
            O0O0OOOO0O000O0O0 =O0000O0O000OO000O .__OO000OOOOO0OOO0OO +'/'+O00OOO00O0O00O000 ['name']+'.pl'#line:285
            if not O00OOO00O0O00O000 ['find']and not O00OOO00O0O00O000 ['exclude']and not O00OOO00O0O00O000 ['is_config']:#line:286
                O0000O0O000OO000O .get_path_file (O00OOO00O0O00O000 )#line:287
                O00OOO00O0O00O000 ['time']=int (time .time ())#line:288
                O0000O000OO0OO00O +=O00OOO00O0O00O000 ['size']#line:289
                O00OOO00O0O00O000 ['size_info']=O0000O0O000OO000O .tosize (O00OOO00O0O00O000 ['size'])#line:290
            if O00OOO00O0O00O000 ['find']and not O00OOO00O0O00O000 ['exclude']and not O00OOO00O0O00O000 ['is_config']:#line:291
                O0000O0O000OO000O .get_path_find (O00OOO00O0O00O000 )#line:292
                O00OOO00O0O00O000 ['time']=int (time .time ())#line:293
                O0000O000OO0OO00O +=O00OOO00O0O00O000 ['size']#line:294
                O00OOO00O0O00O000 ['size_info']=O0000O0O000OO000O .tosize (O00OOO00O0O00O000 ['size'])#line:295
            public .WriteFile (O0O0OOOO0O000O0O0 ,json .dumps (O00OOO00O0O00O000 ))#line:296
        O0O0OOOOOO0OO0OO0 ={"info":O0OOO000O0OOOO00O ,"size":O0000O000OO0OO00O ,"time":OOOO0O0OOO00O0O0O }#line:297
        return O0O0OOOOOO0OO0OO0 #line:298
    def list (O0O0O0O00O0OO0OO0 ,OO0OO0OOOOOOO0OOO ):#line:301
        ""#line:305
        O00O00O0O000OO0OO =0 #line:307
        OO0O0OOO0O0O0OO0O =[]#line:308
        O0O0OOOO0O0O00OOO =O0O0O0O00O0OO0OO0 .get_config ()#line:309
        for O0000OOOOO0OOO00O in O0O0OOOO0O0O00OOO :#line:310
            OOO000O00OOO0O0O0 =O0O0O0O00O0OO0OO0 .__OO000OOOOO0OOO0OO +'/'+O0000OOOOO0OOO00O ['name']+'.pl'#line:311
            if os .path .exists (OOO000O00OOO0O0O0 ):#line:312
                OO00O0OO000O0OO0O =json .loads (public .readFile (OOO000O00OOO0O0O0 ))#line:313
                OO0O0OOO0O0O0OO0O .append (OO00O0OO000O0OO0O )#line:314
                O00O00O0O000OO0OO +=OO00O0OO000O0OO0O ['size']#line:315
            else :#line:316
                if not O0000OOOOO0OOO00O ['find']and not O0000OOOOO0OOO00O ['exclude']and not O0000OOOOO0OOO00O ['is_config']:#line:317
                    O0O0O0O00O0OO0OO0 .get_path_file (O0000OOOOO0OOO00O )#line:318
                    O0000OOOOO0OOO00O ['size_info']=O0O0O0O00O0OO0OO0 .tosize (O0000OOOOO0OOO00O ['size'])#line:319
                    O00O00O0O000OO0OO +=O0000OOOOO0OOO00O ['size']#line:320
                if O0000OOOOO0OOO00O ['find']and not O0000OOOOO0OOO00O ['exclude']and not O0000OOOOO0OOO00O ['is_config']:#line:321
                    O0O0O0O00O0OO0OO0 .get_path_find (O0000OOOOO0OOO00O )#line:322
                    O0000OOOOO0OOO00O ['time']=time .time ()#line:323
                    O00O00O0O000OO0OO +=O0000OOOOO0OOO00O ['size']#line:324
                    O0000OOOOO0OOO00O ['size_info']=O0O0O0O00O0OO0OO0 .tosize (O0000OOOOO0OOO00O ['size'])#line:325
                public .WriteFile (OOO000O00OOO0O0O0 ,json .dumps (O0000OOOOO0OOO00O ))#line:326
                OO0O0OOO0O0O0OO0O .append (O0000OOOOO0OOO00O )#line:327
        if os .path .exists (O0O0O0O00O0OO0OO0 .__OO000OOOOO0OOO0OO +'/scanning'):#line:328
            OOOO0O0OOO0000O0O =int (public .ReadFile (O0O0O0O00O0OO0OO0 .__OO000OOOOO0OOO0OO +'/scanning'))#line:329
        else :#line:330
            OOOO0O0OOO0000O0O =int (time .time ())#line:331
        OOOO000OO0O0000O0 ={"info":OO0O0OOO0O0O0OO0O ,"size":O00O00O0O000OO0OO ,"time":OOOO0O0OOO0000O0O }#line:332
        return OOOO000OO0O0000O0 #line:333
    def remove_file (OO0OOOO00OO000OO0 ,OO0OOOO00000OO00O ):#line:336
        ""#line:340
        if not OO0OOOO00OO000OO0 .__O000OO00O0OO0O00O ():return public .returnMsg (False ,OO0OOOO00OO000OO0 .__OO00O000000OO0000 )#line:341
        O0OOO0000000O000O =0 #line:342
        O0O0O00000000OOOO =OO0OOOO00000OO00O .san_info #line:344
        for O00OOO00OOOO0OOOO in O0O0O00000000OOOO :#line:346
            if len (O00OOO00OOOO0OOOO ['result'])<=0 :return #line:347
            for O0O00O0O0000OO000 in O00OOO00OOOO0OOOO ['result']:#line:348
                try :#line:349
                    if O00OOO00OOOO0OOOO ['type']=='dir':#line:350
                        if 'filename'in O0O00O0O0000OO000 :#line:351
                            if os .path .isfile (O0O00O0O0000OO000 ['filename']):#line:352
                                if O00OOO00OOOO0OOOO ['is_del']:#line:353
                                    os .remove (O0O00O0O0000OO000 ['filename'])#line:354
                                else :#line:355
                                    public .ExecShell ("echo " ">%s"%O0O00O0O0000OO000 ['filename'])#line:356
                                O0OOO0000000O000O +=O0O00O0O0000OO000 ['count_size']#line:357
                            else :#line:358
                                O0OOO0000000O000O +=O0O00O0O0000OO000 ['count_size']#line:359
                                public .ExecShell ("rm -rf %s"%O0O00O0O0000OO000 ['filename'])#line:360
                        else :#line:362
                            return '22'#line:363
                    else :#line:364
                        if os .path .isfile (O0O00O0O0000OO000 ['name']):#line:365
                            if O00OOO00OOOO0OOOO ['is_del']:#line:366
                                os .remove (O0O00O0O0000OO000 ['name'])#line:367
                            else :#line:368
                                public .ExecShell ("echo " ">%s"%O0O00O0O0000OO000 ['name'])#line:369
                            O0OOO0000000O000O +=O0O00O0O0000OO000 ['count_size']#line:370
                        else :#line:371
                            O0OOO0000000O000O +=O0O00O0O0000OO000 ['count_size']#line:373
                            os .rmdir (O0O00O0O0000OO000 ['name'])#line:374
                except :continue #line:375
        OO0OOOO00OO000OO0 .scanning (None )#line:376
        return public .returnMsg (True ,OO0OOOO00OO000OO0 .tosize (O0OOO0000000O000O ))
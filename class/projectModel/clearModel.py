#!/usr/bin/python
import json #line:4
import os ,time #line:5
from projectModel .base import projectBase #line:6
import public #line:7
from BTPanel import cache #line:8
class main (projectBase ):#line:10
    __OO0OOO0OO00OO0O0O =public .Md5 ('clear'+time .strftime ('%Y-%m-%d'))#line:11
    __OO0O0OO0O00000000 ='/www/server/panel/config/clear_log.json'#line:12
    __OO0O0OOO0OO0000O0 ='/www/server/panel/data/clear'#line:13
    __O0OOOOO00OO00000O =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:16
    def __init__ (O0O0O00OO000O0O0O ):#line:18
        if not os .path .exists (O0O0O00OO000O0O0O .__OO0O0OOO0OO0000O0 ):#line:19
            os .makedirs (O0O0O00OO000O0O0O .__OO0O0OOO0OO0000O0 ,384 )#line:20
    def __OOOOOOOOOOO00OO00 (OOO00OOOOO000O00O ):#line:22
        from pluginAuth import Plugin #line:23
        O0OOO00OO0000000O =Plugin (False )#line:24
        OOO00O00O000OO0O0 =O0OOO00OO0000000O .get_plugin_list ()#line:25
        return int (OOO00O00O000OO0O0 ['ltd'])>time .time ()#line:26
    def get_config (OO0OOO000O000OO0O ):#line:30
        ""#line:35
        if not os .path .exists (OO0OOO000O000OO0O .__OO0O0OO0O00000000 ):#line:36
            OO0OOO000O000OO0O .write_config ()#line:37
            return OO0OOO000O000OO0O .default_config ()#line:38
        else :#line:39
            try :#line:40
                OOO0O0O0000O000O0 =json .loads (public .ReadFile (OO0OOO000O000OO0O .__OO0O0OO0O00000000 ))#line:41
            except :#line:42
                OO0OOO000O000OO0O .write_config ()#line:43
                return OO0OOO000O000OO0O .default_config ()#line:44
        if not cache .get (OO0OOO000O000OO0O .__OO0OOO0OO00OO0O0O ):#line:45
            try :#line:46
                import requests #line:47
                OOO0O0O0000O000O0 =requests .get ("https://www.bt.cn/api/bt_waf/clearLog").json ()#line:48
            except :#line:49
                return OO0OOO000O000OO0O .default_config ()#line:50
            OO0OOO000O000OO0O .write_config (OOO0O0O0000O000O0 )#line:51
            return OOO0O0O0000O000O0 #line:52
        else :#line:53
            return OOO0O0O0000O000O0 #line:54
    def write_config (OOO0OOO0OO00000OO ,config =False ):#line:56
        ""#line:62
        if config :#line:63
            public .WriteFile (OOO0OOO0OO00000OO .__OO0O0OO0O00000000 ,json .dumps (config ))#line:64
        else :#line:65
            public .WriteFile (OOO0OOO0OO00000OO .__OO0O0OO0O00000000 ,json .dumps (OOO0OOO0OO00000OO .default_config ()))#line:66
    def default_config (O00O00OOOOO0OOOOO ):#line:69
        ""#line:74
        return [{"name":"recycle1","ps":"面板备份文件","path":"/www/backup/panel","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"recycle2","ps":"面板文件备份","path":"/www/backup/file_history","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"docker","ps":"Docker容器日志","path":"/var/lib/docker/containers","type":"file","is_del":False ,"find":["-json.log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"openrasp","ps":"openrasp日志","path":["/opt/rasp55/logs/alarm","/opt/rasp55/logs/policy","/opt/rasp55/logs/plugin","/opt/rasp56/logs/alarm","/opt/rasp56/logs/policy","/opt/rasp56/logs/plugin","/opt/rasp70/logs/alarm","/opt/rasp70/logs/policy","/opt/rasp70/logs/plugin","/opt/rasp71/logs/alarm","/opt/rasp71/logs/policy","/opt/rasp72/logs/plugin","/opt/rasp73/logs/alarm","/opt/rasp73/logs/policy","/opt/rasp73/logs/plugin","/opt/rasp74/logs/alarm","/opt/rasp74/logs/policy","/opt/rasp74/logs/plugin"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"springboot","ps":"springboot日志","path":"/var/tmp/springboot/vhost/logs","type":"file","is_del":False ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"aliyun","ps":"阿里云Agent日志","path":["/usr/local/share/aliyun-assist/2.2.3.247/log","/usr/local/share/aliyun-assist/2.2.3.256/log"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"qcloud","ps":"腾讯云Agent日志","path":["/usr/local/qcloud/tat_agent/log","/usr/local/qcloud/YunJing/log","/usr/local/qcloud/stargate/logs","/usr/local/qcloud/monitor/barad/log"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"crontab","ps":"计划任务日志","path":"/www/server/cron","type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"tomcat","ps":"tomcat日志","path":["/usr/local/bttomcat/tomcat8/logs","/usr/local/bttomcat/tomcat9/logs","/usr/local/bttomcat/tomcat7/logs"],"type":"file","is_del":True ,"find":[".log"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"panellog","ps":"面板日志","path":"/www/server/panel/logs/request","type":"file","is_del":True ,"find":[".json.gz"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"recycle3","ps":"回收站","path":"/www/Recycle_bin","type":"dir","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"maillog","ps":"邮件日志","path":"/var/spool/mail","type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"btwaflog","ps":"防火墙日志","path":["/www/wwwlogs/btwaf","/www/server/btwaf/totla_db/http_log"],"type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"weblog","ps":"网站日志","path":"/www/wwwlogs","type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"syslog","ps":"系统日志","path":["/var/log/audit","/var/log"],"type":"file","is_del":True ,"find":[],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"package","ps":"面板遗留文件","path":"/www/server/panel/package","type":"file","is_del":True ,"find":[".zip"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"mysqllog","ps":"数据库日志","path":"/www/server/data","type":"file","is_del":True ,"find":["mysql-bin.00"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"session","ps":"session日志","path":"/tmp","type":"file","is_del":True ,"find":["sess_"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 },{"name":"bttotal","ps":"网站监控报表日志","path":"/www/server/total/logs","type":"file","is_del":True ,"find":["_bt_"],"exclude":[],"is_config":False ,"regular":"","subdirectory":False ,"result":[],"size":0 }]#line:95
    def tosize (OO0O0O000OOOOO000 ,O000O0000O00OOOO0 ):#line:97
        ""#line:103
        OO00OOO00OOOOO000 =['b','KB','MB','GB','TB']#line:104
        for O000OO0000OOO0000 in OO00OOO00OOOOO000 :#line:105
            if O000O0000O00OOOO0 <1024 :#line:106
                return str (int (O000O0000O00OOOO0 ))+O000OO0000OOO0000 #line:107
            O000O0000O00OOOO0 =O000O0000O00OOOO0 /1024 #line:108
        return '0b'#line:109
    def any_size (OO00O0OOOOOOOO0O0 ,O0O00O0OOOOO00O0O ):#line:111
        ""#line:117
        O0O00O0OOOOO00O0O =str (O0O00O0OOOOO00O0O )#line:118
        O0O0O00O0OOO0OO00 =O0O00O0OOOOO00O0O [-1 ]#line:119
        try :#line:120
            O00O00OOOOO0000O0 =float (O0O00O0OOOOO00O0O [0 :-1 ])#line:121
        except :#line:122
            O00O00OOOOO0000O0 =0 #line:123
            return O0O00O0OOOOO00O0O #line:124
        OOOOO0O00OO0O0000 =['b','K','M','G','T']#line:125
        if O0O0O00O0OOO0OO00 in OOOOO0O00OO0O0000 :#line:126
            if O0O0O00O0OOO0OO00 =='b':#line:127
                return int (O00O00OOOOO0000O0 )#line:128
            elif O0O0O00O0OOO0OO00 =='K':#line:129
                O00O00OOOOO0000O0 =O00O00OOOOO0000O0 *1024 #line:130
                return int (O00O00OOOOO0000O0 )#line:131
            elif O0O0O00O0OOO0OO00 =='M':#line:132
                O00O00OOOOO0000O0 =O00O00OOOOO0000O0 *1024 *1024 #line:133
                return int (O00O00OOOOO0000O0 )#line:134
            elif O0O0O00O0OOO0OO00 =='G':#line:135
                O00O00OOOOO0000O0 =O00O00OOOOO0000O0 *1024 *1024 *1024 #line:136
                return int (O00O00OOOOO0000O0 )#line:137
            elif O0O0O00O0OOO0OO00 =='T':#line:138
                O00O00OOOOO0000O0 =O00O00OOOOO0000O0 *1024 *1024 *1024 *1024 #line:139
                return int (O00O00OOOOO0000O0 )#line:140
            else :#line:141
                return int (O00O00OOOOO0000O0 )#line:142
        else :#line:143
            return '0b'#line:144
    def get_path_file (OO00O0OO0000O00OO ,OO0000O0OOOOO0O00 ):#line:147
        ""#line:153
        if type (OO0000O0OOOOO0O00 ['path'])==list :#line:154
            for O0O0O00OO00O0OO0O in OO0000O0OOOOO0O00 ['path']:#line:155
                if os .path .exists (O0O0O00OO00O0OO0O ):#line:156
                    for O0O00OOOO00OO00O0 in os .listdir (O0O0O00OO00O0OO0O ):#line:157
                        OO0000O00OO0OOO00 =O0O0O00OO00O0OO0O +'/'+O0O00OOOO00OO00O0 #line:158
                        if OO0000O0OOOOO0O00 ['type']=='file':#line:159
                            if os .path .isfile (OO0000O00OO0OOO00 ):#line:160
                                OO0OO000O0O00OOOO ={}#line:161
                                O0OOOO000OO0000O0 =os .path .getsize (OO0000O00OO0OOO00 )#line:162
                                if O0OOOO000OO0000O0 >=100 :#line:163
                                    OO0OO000O0O00OOOO ['size']=OO00O0OO0000O00OO .tosize (O0OOOO000OO0000O0 )#line:164
                                    OO0OO000O0O00OOOO ['count_size']=O0OOOO000OO0000O0 #line:165
                                    OO0000O0OOOOO0O00 ['size']+=O0OOOO000OO0000O0 #line:166
                                    OO0OO000O0O00OOOO ['name']=OO0000O00OO0OOO00 #line:167
                                    OO0000O0OOOOO0O00 ['result'].append (OO0OO000O0O00OOOO )#line:168
        else :#line:169
            if os .path .exists (OO0000O0OOOOO0O00 ['path']):#line:170
                for O0O00OOOO00OO00O0 in os .listdir (OO0000O0OOOOO0O00 ['path']):#line:171
                    OO0000O00OO0OOO00 =OO0000O0OOOOO0O00 ['path']+'/'+O0O00OOOO00OO00O0 #line:172
                    if OO0000O0OOOOO0O00 ['type']=='file':#line:173
                        if os .path .isfile (OO0000O00OO0OOO00 ):#line:174
                            OO0OO000O0O00OOOO ={}#line:175
                            O0OOOO000OO0000O0 =os .path .getsize (OO0000O00OO0OOO00 )#line:176
                            if O0OOOO000OO0000O0 >=100 :#line:177
                                OO0OO000O0O00OOOO ['size']=OO00O0OO0000O00OO .tosize (O0OOOO000OO0000O0 )#line:178
                                OO0OO000O0O00OOOO ['count_size']=O0OOOO000OO0000O0 #line:179
                                OO0000O0OOOOO0O00 ['size']+=O0OOOO000OO0000O0 #line:180
                                OO0OO000O0O00OOOO ['name']=OO0000O00OO0OOO00 #line:181
                                OO0000O0OOOOO0O00 ['result'].append (OO0OO000O0O00OOOO )#line:182
                    elif OO0000O0OOOOO0O00 ['type']=='dir':#line:183
                        if os .path .isdir (OO0000O00OO0OOO00 ):#line:184
                            O0OOOO000OO0000O0 =public .ExecShell ('du -sh  %s'%OO0000O00OO0OOO00 )[0 ].split ()[0 ]#line:185
                            OO0OO000O0O00OOOO ={}#line:186
                            OO0OO000O0O00OOOO ['dir']='dir'#line:187
                            OO0OO000O0O00OOOO ['size']=O0OOOO000OO0000O0 #line:188
                            OO0OO000O0O00OOOO ['count_size']=OO00O0OO0000O00OO .any_size (O0OOOO000OO0000O0 )#line:189
                            if OO0OO000O0O00OOOO ['count_size']<100 :continue #line:190
                            if OO0000O0OOOOO0O00 ['path']=='/www/Recycle_bin':#line:191
                                OO0000O00OO0OOO00 =O0O00OOOO00OO00O0 .split ('_t_')[0 ].replace ('_bt_','/')#line:192
                                OO0OO000O0O00OOOO ['filename']=OO0000O0OOOOO0O00 ['path']+'/'+O0O00OOOO00OO00O0 #line:193
                                OO0OO000O0O00OOOO ['name']=OO0000O00OO0OOO00 #line:194
                            else :#line:195
                                OO0OO000O0O00OOOO ['filename']=OO0000O0OOOOO0O00 ['path']+'/'+O0O00OOOO00OO00O0 #line:196
                                OO0OO000O0O00OOOO ['name']=os .path .basename (OO0000O00OO0OOO00 )#line:197
                            OO0000O0OOOOO0O00 ['size']+=OO0OO000O0O00OOOO ['count_size']#line:198
                            OO0000O0OOOOO0O00 ['result'].append (OO0OO000O0O00OOOO )#line:199
                        else :#line:200
                            OOO000OO00OO00OOO =os .path .getsize (OO0000O00OO0OOO00 )#line:201
                            if OOO000OO00OO00OOO <100 :continue #line:203
                            OO0OO000O0O00OOOO ={}#line:204
                            OO0OO000O0O00OOOO ['filename']=OO0000O00OO0OOO00 #line:205
                            OO0000O00OO0OOO00 =os .path .basename (OO0000O00OO0OOO00 )#line:207
                            OO0OO000O0O00OOOO ['count_size']=OOO000OO00OO00OOO #line:208
                            if OO0000O0OOOOO0O00 ['path']=='/www/Recycle_bin':#line:209
                                OO0000O00OO0OOO00 =O0O00OOOO00OO00O0 .split ('_t_')[0 ].replace ('_bt_','/')#line:210
                                OO0OO000O0O00OOOO ['name']=OO0000O00OO0OOO00 #line:211
                            else :#line:212
                                OO0OO000O0O00OOOO ['name']=OO0000O00OO0OOO00 #line:213
                            OO0OO000O0O00OOOO ['size']=OO00O0OO0000O00OO .tosize (OOO000OO00OO00OOO )#line:214
                            OO0000O0OOOOO0O00 ['size']+=OO0OO000O0O00OOOO ['count_size']#line:215
                            OO0000O0OOOOO0O00 ['result'].append (OO0OO000O0O00OOOO )#line:216
        return OO0000O0OOOOO0O00 #line:217
    def get_path_find (OOOOO0O00O000O00O ,OO00000O000000O00 ):#line:220
        ""#line:227
        if type (OO00000O000000O00 ['path'])==list :#line:228
            for O0OO000OOO0O000OO in OO00000O000000O00 ['path']:#line:229
                if os .path .exists (O0OO000OOO0O000OO ):#line:230
                    for OOO0000OOO00OOOOO in os .listdir (O0OO000OOO0O000OO ):#line:231
                        for O0O00OO00O00O0000 in OO00000O000000O00 ['find']:#line:232
                            if OOO0000OOO00OOOOO .find (O0O00OO00O00O0000 )==-1 :continue #line:233
                            OOO00O00OOOO0000O =O0OO000OOO0O000OO +'/'+OOO0000OOO00OOOOO #line:234
                            if not os .path .exists (OOO00O00OOOO0000O ):continue #line:235
                            O0OO0O0O0O0OOO0OO =os .path .getsize (OOO00O00OOOO0000O )#line:236
                            if O0OO0O0O0O0OOO0OO <1024 :continue #line:237
                            OO0O00O0OOO0OOOO0 ={}#line:238
                            OO0O00O0OOO0OOOO0 ['name']=OOO00O00OOOO0000O #line:239
                            OO0O00O0OOO0OOOO0 ['count_size']=O0OO0O0O0O0OOO0OO #line:240
                            OO00000O000000O00 ['size']+=O0OO0O0O0O0OOO0OO #line:241
                            OO0O00O0OOO0OOOO0 ['size']=OOOOO0O00O000O00O .tosize (O0OO0O0O0O0OOO0OO )#line:242
                            OO00000O000000O00 ['result'].append (OO0O00O0OOO0OOOO0 )#line:243
        else :#line:244
            if os .path .exists (OO00000O000000O00 ['path']):#line:245
                for OOO0000OOO00OOOOO in os .listdir (OO00000O000000O00 ['path']):#line:246
                    for O0O00OO00O00O0000 in OO00000O000000O00 ['find']:#line:247
                        OOO00O00OOOO0000O =OO00000O000000O00 ['path']+'/'+OOO0000OOO00OOOOO #line:248
                        if OO00000O000000O00 ['path']=='/var/lib/docker/containers':#line:249
                            OOO00O00OOOO0000O =OOO00O00OOOO0000O +'/'+OOO0000OOO00OOOOO +'-json.log'#line:250
                            if os .path .exists (OOO00O00OOOO0000O ):#line:251
                                O0OO0O0O0O0OOO0OO =os .path .getsize (OOO00O00OOOO0000O )#line:252
                                if O0OO0O0O0O0OOO0OO <1024 :continue #line:253
                                OO0O00O0OOO0OOOO0 ={}#line:254
                                OO0O00O0OOO0OOOO0 ['name']=OOO00O00OOOO0000O #line:255
                                OO0O00O0OOO0OOOO0 ['count_size']=O0OO0O0O0O0OOO0OO #line:256
                                OO00000O000000O00 ['size']+=O0OO0O0O0O0OOO0OO #line:257
                                OO0O00O0OOO0OOOO0 ['size']=OOOOO0O00O000O00O .tosize (O0OO0O0O0O0OOO0OO )#line:258
                                OO00000O000000O00 ['result'].append (OO0O00O0OOO0OOOO0 )#line:259
                        else :#line:260
                            if OOO0000OOO00OOOOO .find (O0O00OO00O00O0000 )==-1 :continue #line:261
                            if not os .path .exists (OOO00O00OOOO0000O ):continue #line:262
                            O0OO0O0O0O0OOO0OO =os .path .getsize (OOO00O00OOOO0000O )#line:263
                            if O0OO0O0O0O0OOO0OO <1024 :continue #line:264
                            OO0O00O0OOO0OOOO0 ={}#line:265
                            OO0O00O0OOO0OOOO0 ['name']=OOO00O00OOOO0000O #line:266
                            OO0O00O0OOO0OOOO0 ['count_size']=O0OO0O0O0O0OOO0OO #line:267
                            OO00000O000000O00 ['size']+=O0OO0O0O0O0OOO0OO #line:268
                            OO0O00O0OOO0OOOO0 ['size']=OOOOO0O00O000O00O .tosize (O0OO0O0O0O0OOO0OO )#line:269
                            OO00000O000000O00 ['result'].append (OO0O00O0OOO0OOOO0 )#line:270
        return OO00000O000000O00 #line:271
    def scanning (O0O0O000000O00O0O ,OOOO0O00OOOOO00OO ):#line:273
        ""#line:277
        if not O0O0O000000O00O0O .__OOOOOOOOOOO00OO00 ():return public .returnMsg (False ,O0O0O000000O00O0O .__O0OOOOO00OO00000O )#line:278
        OO0O0OOO00OOOO0OO =0 #line:279
        OOO00O0O00000O000 =O0O0O000000O00O0O .get_config ()#line:280
        OO0OOOO0O00O00OO0 =int (time .time ())#line:281
        public .WriteFile (O0O0O000000O00O0O .__OO0O0OOO0OO0000O0 +'/scanning',str (OO0OOOO0O00O00OO0 ))#line:282
        for OO0O0O0OOOO00O0OO in OOO00O0O00000O000 :#line:283
            O0O0000OO0OO0OO0O =O0O0O000000O00O0O .__OO0O0OOO0OO0000O0 +'/'+OO0O0O0OOOO00O0OO ['name']+'.pl'#line:284
            if not OO0O0O0OOOO00O0OO ['find']and not OO0O0O0OOOO00O0OO ['exclude']and not OO0O0O0OOOO00O0OO ['is_config']:#line:285
                O0O0O000000O00O0O .get_path_file (OO0O0O0OOOO00O0OO )#line:286
                OO0O0O0OOOO00O0OO ['time']=int (time .time ())#line:287
                OO0O0OOO00OOOO0OO +=OO0O0O0OOOO00O0OO ['size']#line:288
                OO0O0O0OOOO00O0OO ['size_info']=O0O0O000000O00O0O .tosize (OO0O0O0OOOO00O0OO ['size'])#line:289
            if OO0O0O0OOOO00O0OO ['find']and not OO0O0O0OOOO00O0OO ['exclude']and not OO0O0O0OOOO00O0OO ['is_config']:#line:290
                O0O0O000000O00O0O .get_path_find (OO0O0O0OOOO00O0OO )#line:291
                OO0O0O0OOOO00O0OO ['time']=int (time .time ())#line:292
                OO0O0OOO00OOOO0OO +=OO0O0O0OOOO00O0OO ['size']#line:293
                OO0O0O0OOOO00O0OO ['size_info']=O0O0O000000O00O0O .tosize (OO0O0O0OOOO00O0OO ['size'])#line:294
            public .WriteFile (O0O0000OO0OO0OO0O ,json .dumps (OO0O0O0OOOO00O0OO ))#line:295
        O00000O0000O0O0OO ={"info":OOO00O0O00000O000 ,"size":OO0O0OOO00OOOO0OO ,"time":OO0OOOO0O00O00OO0 }#line:296
        return O00000O0000O0O0OO #line:297
    def list (O000OO0O00O000OO0 ,O0OOOOO0OOOO0O0O0 ):#line:300
        ""#line:304
        O0O0O0OO0OO0O000O =0 #line:306
        O000000OO0OOOOOOO =[]#line:307
        O000O00O0OO00O00O =O000OO0O00O000OO0 .get_config ()#line:308
        for OOO000O00OOO0000O in O000O00O0OO00O00O :#line:309
            OOOOO0OO00OO0O0O0 =O000OO0O00O000OO0 .__OO0O0OOO0OO0000O0 +'/'+OOO000O00OOO0000O ['name']+'.pl'#line:310
            if os .path .exists (OOOOO0OO00OO0O0O0 ):#line:311
                O00OO0OOOO00OO00O =json .loads (public .readFile (OOOOO0OO00OO0O0O0 ))#line:312
                O000000OO0OOOOOOO .append (O00OO0OOOO00OO00O )#line:313
                O0O0O0OO0OO0O000O +=O00OO0OOOO00OO00O ['size']#line:314
            else :#line:315
                if not OOO000O00OOO0000O ['find']and not OOO000O00OOO0000O ['exclude']and not OOO000O00OOO0000O ['is_config']:#line:316
                    O000OO0O00O000OO0 .get_path_file (OOO000O00OOO0000O )#line:317
                    OOO000O00OOO0000O ['size_info']=O000OO0O00O000OO0 .tosize (OOO000O00OOO0000O ['size'])#line:318
                    O0O0O0OO0OO0O000O +=OOO000O00OOO0000O ['size']#line:319
                if OOO000O00OOO0000O ['find']and not OOO000O00OOO0000O ['exclude']and not OOO000O00OOO0000O ['is_config']:#line:320
                    O000OO0O00O000OO0 .get_path_find (OOO000O00OOO0000O )#line:321
                    OOO000O00OOO0000O ['time']=time .time ()#line:322
                    O0O0O0OO0OO0O000O +=OOO000O00OOO0000O ['size']#line:323
                    OOO000O00OOO0000O ['size_info']=O000OO0O00O000OO0 .tosize (OOO000O00OOO0000O ['size'])#line:324
                public .WriteFile (OOOOO0OO00OO0O0O0 ,json .dumps (OOO000O00OOO0000O ))#line:325
                O000000OO0OOOOOOO .append (OOO000O00OOO0000O )#line:326
        if os .path .exists (O000OO0O00O000OO0 .__OO0O0OOO0OO0000O0 +'/scanning'):#line:327
            OOOO00OO000O0O00O =int (public .ReadFile (O000OO0O00O000OO0 .__OO0O0OOO0OO0000O0 +'/scanning'))#line:328
        else :#line:329
            OOOO00OO000O0O00O =int (time .time ())#line:330
        O00O0OO00OO00O0O0 ={"info":O000000OO0OOOOOOO ,"size":O0O0O0OO0OO0O000O ,"time":OOOO00OO000O0O00O }#line:331
        return O00O0OO00OO00O0O0 #line:332
    def remove_file (OO0O0O0OOOO00OO0O ,OOO0OOOO0000O000O ):#line:335
        ""#line:339
        if not OO0O0O0OOOO00OO0O .__OOOOOOOOOOO00OO00 ():return public .returnMsg (False ,OO0O0O0OOOO00OO0O .__O0OOOOO00OO00000O )#line:340
        OOO0O0OO0O0OOOO00 =0 #line:341
        OOO0O000OO0O0O00O =OOO0OOOO0000O000O .san_info #line:343
        for OO000O0O00O000000 in OOO0O000OO0O0O00O :#line:345
            if len (OO000O0O00O000000 ['result'])<=0 :return #line:346
            for O0O00OOO0O00000OO in OO000O0O00O000000 ['result']:#line:347
                try :#line:348
                    if OO000O0O00O000000 ['type']=='dir':#line:349
                        if 'filename'in O0O00OOO0O00000OO :#line:350
                            if os .path .isfile (O0O00OOO0O00000OO ['filename']):#line:351
                                if OO000O0O00O000000 ['is_del']:#line:352
                                    os .remove (O0O00OOO0O00000OO ['filename'])#line:353
                                else :#line:354
                                    public .ExecShell ("echo " ">%s"%O0O00OOO0O00000OO ['filename'])#line:355
                                OOO0O0OO0O0OOOO00 +=O0O00OOO0O00000OO ['count_size']#line:356
                            else :#line:357
                                OOO0O0OO0O0OOOO00 +=O0O00OOO0O00000OO ['count_size']#line:358
                                public .ExecShell ("rm -rf %s"%O0O00OOO0O00000OO ['filename'])#line:359
                        else :#line:361
                            return '22'#line:362
                    else :#line:363
                        if os .path .isfile (O0O00OOO0O00000OO ['name']):#line:364
                            if OO000O0O00O000000 ['is_del']:#line:365
                                os .remove (O0O00OOO0O00000OO ['name'])#line:366
                            else :#line:367
                                public .ExecShell ("echo " ">%s"%O0O00OOO0O00000OO ['name'])#line:368
                            OOO0O0OO0O0OOOO00 +=O0O00OOO0O00000OO ['count_size']#line:369
                        else :#line:370
                            OOO0O0OO0O0OOOO00 +=O0O00OOO0O00000OO ['count_size']#line:372
                            os .rmdir (O0O00OOO0O00000OO ['name'])#line:373
                except :continue #line:374
        OO0O0O0OOOO00OO0O .scanning (None )#line:375
        return public .returnMsg (True ,OO0O0O0OOOO00OO0O .tosize (OOO0O0OO0O0OOOO00 ))
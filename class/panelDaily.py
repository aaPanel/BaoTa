import os #line:14
import sys #line:15
import time #line:16
import psutil #line:17
os .chdir ("/www/server/panel")#line:19
sys .path .insert (0 ,"/www/server/panel")#line:20
sys .path .insert (0 ,"class/")#line:21
import public #line:23
from system import system #line:24
from panelPlugin import panelPlugin #line:25
from BTPanel import auth ,cache #line:26
class panelDaily :#line:28
    def check_databases (O00000OO000O0OO00 ):#line:30
        ""#line:31
        O0000O0OOOOOO00O0 =["app_usage","server_status","backup_status","daily"]#line:32
        import sqlite3 #line:33
        O0OOOOO0OO0OO0OOO =sqlite3 .connect ("/www/server/panel/data/system.db")#line:34
        O0O00O00O0O0O00OO =O0OOOOO0OO0OO0OOO .cursor ()#line:35
        O0OO00OO0OO0O0O0O =",".join (["'"+OO0O0OOO0O0000O00 +"'"for OO0O0OOO0O0000O00 in O0000O0OOOOOO00O0 ])#line:36
        O000OO0O00000O00O =O0O00O00O0O0O00OO .execute ("SELECT name FROM sqlite_master WHERE type='table' and name in ({})".format (O0OO00OO0OO0O0O0O ))#line:37
        OO0O000OOO000OO0O =O000OO0O00000O00O .fetchall ()#line:38
        OOO0OO00000O0O00O =False #line:41
        OO0OO00O0000O0OOO =[]#line:42
        if OO0O000OOO000OO0O :#line:43
            OO0OO00O0000O0OOO =[OO0OOO000OOOOOO00 [0 ]for OO0OOO000OOOOOO00 in OO0O000OOO000OO0O ]#line:44
        if "app_usage"not in OO0OO00O0000O0OOO :#line:46
            OO0000O0000OO00O0 ='''CREATE TABLE IF NOT EXISTS `app_usage` (
                    `time_key` INTEGER PRIMARY KEY,
                    `app` TEXT,
                    `disks` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:52
            O0O00O00O0O0O00OO .execute (OO0000O0000OO00O0 )#line:53
            OOO0OO00000O0O00O =True #line:54
        if "server_status"not in OO0OO00O0000O0OOO :#line:56
            print ("创建server_status表:")#line:57
            OO0000O0000OO00O0 ='''CREATE TABLE IF NOT EXISTS `server_status` (
                    `status` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:61
            O0O00O00O0O0O00OO .execute (OO0000O0000OO00O0 )#line:62
            OOO0OO00000O0O00O =True #line:63
        if "backup_status"not in OO0OO00O0000O0OOO :#line:65
            print ("创建备份状态表:")#line:66
            OO0000O0000OO00O0 ='''CREATE TABLE IF NOT EXISTS `backup_status` (
                    `id` INTEGER,
                    `target` TEXT,
                    `status` INTEGER,
                    `msg` TEXT DEFAULT "",
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:73
            O0O00O00O0O0O00OO .execute (OO0000O0000OO00O0 )#line:74
            OOO0OO00000O0O00O =True #line:75
        if "daily"not in OO0OO00O0000O0OOO :#line:77
            OO0000O0000OO00O0 ='''CREATE TABLE IF NOT EXISTS `daily` (
                    `time_key` INTEGER,
                    `evaluate` INTEGER,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:82
            O0O00O00O0O0O00OO .execute (OO0000O0000OO00O0 )#line:83
            OOO0OO00000O0O00O =True #line:84
        if OOO0OO00000O0O00O :#line:86
            O0OOOOO0OO0OO0OOO .commit ()#line:87
        O0O00O00O0O0O00OO .close ()#line:88
        O0OOOOO0OO0OO0OOO .close ()#line:89
        return True #line:90
    def get_time_key (OO0000000OO000OOO ,date =None ):#line:92
        if date is None :#line:93
            date =time .localtime ()#line:94
        O000OO0OOO0OO0OOO =0 #line:95
        O000000000000000O ="%Y%m%d"#line:96
        if type (date )==time .struct_time :#line:97
            O000OO0OOO0OO0OOO =int (time .strftime (O000000000000000O ,date ))#line:98
        if type (date )==str :#line:99
            O000OO0OOO0OO0OOO =int (time .strptime (date ,O000000000000000O ))#line:100
        return O000OO0OOO0OO0OOO #line:101
    def store_app_usage (OO0OO0OOO0O0OOOO0 ,time_key =None ):#line:103
        ""#line:111
        OO0OO0OOO0O0OOOO0 .check_databases ()#line:113
        if time_key is None :#line:115
            time_key =OO0OO0OOO0O0OOOO0 .get_time_key ()#line:116
        O0O000O00OO0OOO00 =public .M ("system").dbfile ("system").table ("app_usage")#line:118
        OOOOO000OO0000000 =O0O000O00OO0OOO00 .field ("time_key").where ("time_key=?",(time_key )).find ()#line:119
        if OOOOO000OO0000000 and "time_key"in OOOOO000OO0000000 :#line:120
            if OOOOO000OO0000000 ["time_key"]==time_key :#line:121
                return True #line:123
        O0000O00000O00O00 =public .M ('sites').field ('path').select ()#line:125
        OO0OOO0O0O0OO0OOO =0 #line:126
        for O00OO0OO0O00O0OOO in O0000O00000O00O00 :#line:127
            OOOOOOOO0O00OO000 =O00OO0OO0O00O0OOO ["path"]#line:128
            if OOOOOOOO0O00OO000 :#line:129
                OO0OOO0O0O0OO0OOO +=public .get_path_size (OOOOOOOO0O00OO000 )#line:130
        O0OO0OO00000O0O0O =public .get_path_size ("/www/server/data")#line:132
        OOOOO00O00OO0OO00 =public .M ("ftps").field ("path").select ()#line:134
        O00000000O0OO0OOO =0 #line:135
        for O00OO0OO0O00O0OOO in OOOOO00O00OO0OO00 :#line:136
            O0OOO0OOOOOO00O00 =O00OO0OO0O00O0OOO ["path"]#line:137
            if O0OOO0OOOOOO00O00 :#line:138
                O00000000O0OO0OOO +=public .get_path_size (O0OOO0OOOOOO00O00 )#line:139
        O0O0000OO0OOO0000 =public .get_path_size ("/www/server/panel/plugin")#line:141
        O00OOOOO0000OOOO0 =["/www/server/total","/www/server/btwaf","/www/server/coll","/www/server/nginx","/www/server/apache","/www/server/redis"]#line:149
        for O0OOO0O0OO0OOOO0O in O00OOOOO0000OOOO0 :#line:150
            O0O0000OO0OOO0000 +=public .get_path_size (O0OOO0O0OO0OOOO0O )#line:151
        O000O00OO00OOOOO0 =system ().GetDiskInfo2 (human =False )#line:153
        OOOO0O00OOO00O0OO =""#line:154
        OOOO0OOO0O0OOO00O =0 #line:155
        O00O0O00O00O00O0O =0 #line:156
        for O0O0O000O000OO0O0 in O000O00OO00OOOOO0 :#line:157
            O0OO000O0OOO0O0O0 =O0O0O000O000OO0O0 ["path"]#line:158
            if OOOO0O00OOO00O0OO :#line:159
                OOOO0O00OOO00O0OO +="-"#line:160
            OOOOOOOO0OO000000 ,OO0OO00000000OO0O ,OO0O0O0O0O0000000 ,O0OO00000OOO00OOO =O0O0O000O000OO0O0 ["size"]#line:161
            O0OO000O000OO00O0 ,OOOO0000OO000OO00 ,_OOOO0OO0O000000OO ,_OO00O0O0O00O0000O =O0O0O000O000OO0O0 ["inodes"]#line:162
            OOOO0O00OOO00O0OO ="{},{},{},{},{}".format (O0OO000O0OOO0O0O0 ,OO0OO00000000OO0O ,OOOOOOOO0OO000000 ,OOOO0000OO000OO00 ,O0OO000O000OO00O0 )#line:163
            if O0OO000O0OOO0O0O0 =="/":#line:164
                OOOO0OOO0O0OOO00O =OOOOOOOO0OO000000 #line:165
                O00O0O00O00O00O0O =OO0OO00000000OO0O #line:166
        O0O0O00O000O00000 ="{},{},{},{},{},{}".format (OOOO0OOO0O0OOO00O ,O00O0O00O00O00O0O ,OO0OOO0O0O0OO0OOO ,O0OO0OO00000O0O0O ,O00000000O0OO0OOO ,O0O0000OO0OOO0000 )#line:171
        O00OO0O00OO0OOOOO =public .M ("system").dbfile ("system").table ("app_usage").add ("time_key,app,disks",(time_key ,O0O0O00O000O00000 ,OOOO0O00OOO00O0OO ))#line:173
        if O00OO0O00OO0OOOOO ==time_key :#line:174
            return True #line:175
        return False #line:178
    def parse_app_usage_info (O000000000OO0OO00 ,O00OO0O0OOO00O000 ):#line:180
        ""#line:181
        if not O00OO0O0OOO00O000 :#line:182
            return {}#line:183
        print (O00OO0O0OOO00O000 )#line:184
        OO0OOOO00O0OO000O ,O0O0000OOO0000000 ,O0OOO0OO00OO0O0O0 ,OO0O00OO0O0O0OO00 ,OOO0OO0OOOOO00O0O ,OOO00O0OO00OO0O0O =O00OO0O0OOO00O000 ["app"].split (",")#line:185
        OO00OO000OO00000O =O00OO0O0OOO00O000 ["disks"].split ("-")#line:186
        OOOOOOO0O00O0OOOO ={}#line:187
        for OOOOOO000OOO00OOO in OO00OO000OO00000O :#line:188
            O00O00OOO00O00O0O ,OO0OOO0O0O0000000 ,O0000OO00000OO000 ,O0O0O00OOO00O0OOO ,OOO00O00000000OO0 =OOOOOO000OOO00OOO .split (",")#line:189
            O0O000OOO0O00O0O0 ={}#line:190
            O0O000OOO0O00O0O0 ["usage"]=OO0OOO0O0O0000000 #line:191
            O0O000OOO0O00O0O0 ["total"]=O0000OO00000OO000 #line:192
            O0O000OOO0O00O0O0 ["iusage"]=O0O0O00OOO00O0OOO #line:193
            O0O000OOO0O00O0O0 ["itotal"]=OOO00O00000000OO0 #line:194
            OOOOOOO0O00O0OOOO [O00O00OOO00O00O0O ]=O0O000OOO0O00O0O0 #line:195
        return {"apps":{"disk_total":OO0OOOO00O0OO000O ,"disk_usage":O0O0000OOO0000000 ,"sites":O0OOO0OO00OO0O0O0 ,"databases":OO0O00OO0O0O0OO00 ,"ftps":OOO0OO0OOOOO00O0O ,"plugins":OOO00O0OO00OO0O0O },"disks":OOOOOOO0O00O0OOOO }#line:206
    def get_app_usage (OO0O000O0O0O0OO0O ,O0O00OOOOOO0000O0 ):#line:208
        O00OO00OO0O0O000O =time .localtime ()#line:210
        O0OOOOO00OO000000 =OO0O000O0O0O0OO0O .get_time_key ()#line:211
        O00OOOOOO0O0O0000 =time .localtime (time .mktime ((O00OO00OO0O0O000O .tm_year ,O00OO00OO0O0O000O .tm_mon ,O00OO00OO0O0O000O .tm_mday -1 ,0 ,0 ,0 ,0 ,0 ,0 )))#line:214
        O00O000OOOO0OOO0O =OO0O000O0O0O0OO0O .get_time_key (O00OOOOOO0O0O0000 )#line:215
        O00OO00OOOOOOOOO0 =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key =? or time_key=?",(O0OOOOO00OO000000 ,O00O000OOOO0OOO0O ))#line:217
        O00O00O0OO00OOO00 =O00OO00OOOOOOOOO0 .select ()#line:218
        if type (O00O00O0OO00OOO00 )==str or not O00O00O0OO00OOO00 :#line:221
            return {}#line:222
        OOO000O0OOOOOOOOO ={}#line:223
        O0O0OOO00OO00OO00 ={}#line:224
        for OOO0000OOO0OOOO00 in O00O00O0OO00OOO00 :#line:225
            if OOO0000OOO0OOOO00 ["time_key"]==O0OOOOO00OO000000 :#line:226
                OOO000O0OOOOOOOOO =OO0O000O0O0O0OO0O .parse_app_usage_info (OOO0000OOO0OOOO00 )#line:227
            if OOO0000OOO0OOOO00 ["time_key"]==O00O000OOOO0OOO0O :#line:228
                O0O0OOO00OO00OO00 =OO0O000O0O0O0OO0O .parse_app_usage_info (OOO0000OOO0OOOO00 )#line:229
        if not OOO000O0OOOOOOOOO :#line:231
            return {}#line:232
        for O0OOO00000O00O000 ,OO0OOO00O0OO0OOO0 in OOO000O0OOOOOOOOO ["disks"].items ():#line:235
            OOO0OOO0O0OOOO00O =int (OO0OOO00O0OO0OOO0 ["total"])#line:236
            OO00O000O0O00OO00 =int (OO0OOO00O0OO0OOO0 ["usage"])#line:237
            OO0OOOO0O0O0OOOO0 =int (OO0OOO00O0OO0OOO0 ["itotal"])#line:239
            O0OO0O0O0O000OO00 =int (OO0OOO00O0OO0OOO0 ["iusage"])#line:240
            if O0O0OOO00OO00OO00 and O0OOO00000O00O000 in O0O0OOO00OO00OO00 ["disks"].keys ():#line:242
                OOOO0OO0OOO00O00O =O0O0OOO00OO00OO00 ["disks"]#line:243
                O0O0OO000000OOOOO =OOOO0OO0OOO00O00O [O0OOO00000O00O000 ]#line:244
                O00OO00O000OO00OO =int (O0O0OO000000OOOOO ["total"])#line:245
                if O00OO00O000OO00OO ==OOO0OOO0O0OOOO00O :#line:246
                    OO0O0OOOOOOO0OO0O =int (O0O0OO000000OOOOO ["usage"])#line:247
                    OO0000000OOOO0OO0 =0 #line:248
                    OOOOOO00O00O000OO =OO00O000O0O00OO00 -OO0O0OOOOOOO0OO0O #line:249
                    if OOOOOO00O00O000OO >0 :#line:250
                        OO0000000OOOO0OO0 =round (OOOOOO00O00O000OO /OOO0OOO0O0OOOO00O ,2 )#line:251
                    OO0OOO00O0OO0OOO0 ["incr"]=OO0000000OOOO0OO0 #line:252
                O000OOOO0O00OOOO0 =int (O0O0OO000000OOOOO ["itotal"])#line:255
                if True :#line:256
                    O000000OOO00OOO0O =int (O0O0OO000000OOOOO ["iusage"])#line:257
                    OOO0O0OO00OOO0000 =0 #line:258
                    OOOOOO00O00O000OO =O0OO0O0O0O000OO00 -O000000OOO00OOO0O #line:259
                    if OOOOOO00O00O000OO >0 :#line:260
                        OOO0O0OO00OOO0000 =round (OOOOOO00O00O000OO /OO0OOOO0O0O0OOOO0 ,2 )#line:261
                    OO0OOO00O0OO0OOO0 ["iincr"]=OOO0O0OO00OOO0000 #line:262
        O00OOO0O0O0O00O0O =OOO000O0OOOOOOOOO ["apps"]#line:266
        O0O0O0OOOOO00OOO0 =int (O00OOO0O0O0O00O0O ["disk_total"])#line:267
        if O0O0OOO00OO00OO00 and O0O0OOO00OO00OO00 ["apps"]["disk_total"]==O00OOO0O0O0O00O0O ["disk_total"]:#line:268
            O0O0OOOO000OO000O =O0O0OOO00OO00OO00 ["apps"]#line:269
            for O00OO00000OOO000O ,O000OO0O00O00OO0O in O00OOO0O0O0O00O0O .items ():#line:270
                if O00OO00000OOO000O =="disks":continue #line:271
                if O00OO00000OOO000O =="disk_total":continue #line:272
                if O00OO00000OOO000O =="disk_usage":continue #line:273
                O00O0OO0OO0000000 =0 #line:274
                O0O0O0OOO0000O000 =int (O000OO0O00O00OO0O )-int (O0O0OOOO000OO000O [O00OO00000OOO000O ])#line:275
                if O0O0O0OOO0000O000 >0 :#line:276
                    O00O0OO0OO0000000 =round (O0O0O0OOO0000O000 /O0O0O0OOOOO00OOO0 ,2 )#line:277
                O00OOO0O0O0O00O0O [O00OO00000OOO000O ]={"val":O000OO0O00O00OO0O ,"incr":O00O0OO0OO0000000 }#line:282
        return OOO000O0OOOOOOOOO #line:283
    def get_timestamp_interval (O0OOO00000OO0O00O ,OO0O0O000O0O0OO00 ):#line:285
        OOOO0OO00O00O000O =None #line:286
        O0O00O000OOOO00OO =None #line:287
        OOOO0OO00O00O000O =time .mktime ((OO0O0O000O0O0OO00 .tm_year ,OO0O0O000O0O0OO00 .tm_mon ,OO0O0O000O0O0OO00 .tm_mday ,0 ,0 ,0 ,0 ,0 ,0 ))#line:289
        O0O00O000OOOO00OO =time .mktime ((OO0O0O000O0O0OO00 .tm_year ,OO0O0O000O0O0OO00 .tm_mon ,OO0O0O000O0O0OO00 .tm_mday ,23 ,59 ,59 ,0 ,0 ,0 ))#line:291
        return OOOO0OO00O00O000O ,O0O00O000OOOO00OO #line:292
    def check_server (O0OO0OOOOO0O0O0O0 ):#line:295
        try :#line:296
            O000000OOOO00OO00 =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:299
            O00000O0OOOO000OO =panelPlugin ()#line:300
            OOO0000OOO000O0OO =public .dict_obj ()#line:301
            O0OO0O0O0O0OO0O00 =""#line:302
            for O0000O0O000O0O0OO in O000000OOOO00OO00 :#line:303
                OOO000OO000OO0OOO =False #line:304
                OOO00O0O0OOOOOO0O =False #line:305
                OOO0000OOO000O0OO .name =O0000O0O000O0O0OO #line:306
                OO00O00O0O000OOO0 =O00000O0OOOO000OO .getPluginInfo (OOO0000OOO000O0OO )#line:307
                if not OO00O00O0O000OOO0 :#line:308
                    continue #line:309
                O00O0O0000O0O00OO =OO00O00O0O000OOO0 ["versions"]#line:310
                for O0O0O00OOO0O0O0O0 in O00O0O0000O0O00OO :#line:312
                    if O0O0O00OOO0O0O0O0 ["status"]:#line:315
                        OOO00O0O0OOOOOO0O =True #line:316
                    if "run"in O0O0O00OOO0O0O0O0 .keys ()and O0O0O00OOO0O0O0O0 ["run"]:#line:317
                        OOO00O0O0OOOOOO0O =True #line:319
                        OOO000OO000OO0OOO =True #line:320
                        break #line:321
                O0O0O000O00O00O00 =0 #line:322
                if OOO00O0O0OOOOOO0O :#line:323
                    O0O0O000O00O00O00 =1 #line:324
                    if not OOO000OO000OO0OOO :#line:326
                        O0O0O000O00O00O00 =2 #line:327
                O0OO0O0O0O0OO0O00 +=str (O0O0O000O00O00O00 )#line:328
            if '2'in O0OO0O0O0O0OO0O00 :#line:332
                public .M ("system").dbfile ("server_status").add ("status, addtime",(O0OO0O0O0O0OO0O00 ,time .time ()))#line:334
        except Exception as O000OO0000OO00OOO :#line:335
            return True #line:337
    def get_daily_data (OOO000OOO00O000OO ,O0O00OO0OOOO0000O ):#line:339
        ""#line:340
        O00OO0OO00OOOO00O ="IS_PRO_OR_LTD_FOR_PANEL_DAILY"#line:342
        O0OOO0OOOOO00O0OO =cache .get (O00OO0OO00OOOO00O )#line:343
        if not O0OOO0OOOOO00O0OO :#line:344
            try :#line:345
                O0OOO0O000O00OOOO =panelPlugin ()#line:346
                OO000OO0OOOOOOO00 =O0OOO0O000O00OOOO .get_soft_list (O0O00OO0OOOO0000O )#line:347
                if OO000OO0OOOOOOO00 ["pro"]<0 and OO000OO0OOOOOOO00 ["ltd"]<0 :#line:348
                    if os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:349
                        os .remove ("/www/server/panel/data/start_daily.pl")#line:350
                    return {"status":False ,"msg":"No authorization.","data":[],"date":O0O00OO0OOOO0000O .date }#line:356
                cache .set (O00OO0OO00OOOO00O ,True ,86400 )#line:357
            except :#line:358
                return {"status":False ,"msg":"获取不到授权信息，请检查网络是否正常","data":[],"date":O0O00OO0OOOO0000O .date }#line:364
        if not os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:367
            public .writeFile ("/www/server/panel/data/start_daily.pl",O0O00OO0OOOO0000O .date )#line:368
        return OOO000OOO00O000OO .get_daily_data_local (O0O00OO0OOOO0000O .date )#line:369
    def get_daily_data_local (OOO0OO0O00O0OOOO0 ,O00O000OOOO000O0O ):#line:371
        O00000000OOO0000O =time .strptime (O00O000OOOO000O0O ,"%Y%m%d")#line:372
        O0O000O0OOOO00OOO =OOO0OO0O00O0OOOO0 .get_time_key (O00000000OOO0000O )#line:373
        OOO0OO0O00O0OOOO0 .check_databases ()#line:375
        OO0OOO00OOO00OOO0 =time .strftime ("%Y-%m-%d",O00000000OOO0000O )#line:377
        OOO0O00O00O0O00OO =0 #line:378
        O0000OO00O0O0OOO0 ,O0O0OO00000OO0000 =OOO0OO0O00O0OOOO0 .get_timestamp_interval (O00000000OOO0000O )#line:379
        O0O0OOO0O0000OO00 =public .M ("system").dbfile ("system")#line:380
        O0000OO000OO0O0O0 =O0O0OOO0O0000OO00 .table ("process_high_percent")#line:381
        O0O00000OOOOO00OO =O0000OO000OO0O0O0 .where ("addtime>=? and addtime<=?",(O0000OO00O0O0OOO0 ,O0O0OO00000OO0000 )).order ("addtime").select ()#line:382
        O0000OOO00O00O00O =[]#line:386
        if len (O0O00000OOOOO00OO )>0 :#line:387
            for OOOO0O0OO000OOO0O in O0O00000OOOOO00OO :#line:389
                OO000O0OOO0OOOOOO =int (OOOO0O0OO000OOO0O ["cpu_percent"])#line:391
                if OO000O0OOO0OOOOOO >=80 :#line:392
                    O0000OOO00O00O00O .append ({"time":OOOO0O0OO000OOO0O ["addtime"],"name":OOOO0O0OO000OOO0O ["name"],"pid":OOOO0O0OO000OOO0O ["pid"],"percent":OO000O0OOO0OOOOOO })#line:400
        OOO0OO000O00000O0 =len (O0000OOO00O00O00O )#line:402
        OO00OOOOOO0O0O0OO =0 #line:403
        OOOO0OO0OO0O0O0OO =""#line:404
        if OOO0OO000O00000O0 ==0 :#line:405
            OO00OOOOOO0O0O0OO =20 #line:406
        else :#line:407
            OOOO0OO0OO0O0O0OO ="CPU出现过载情况"#line:408
        O0OOO0O0O0O000O00 ={"ex":OOO0OO000O00000O0 ,"detail":O0000OOO00O00O00O }#line:412
        O000O00O0O0OO0000 =[]#line:415
        if len (O0O00000OOOOO00OO )>0 :#line:416
            for OOOO0O0OO000OOO0O in O0O00000OOOOO00OO :#line:418
                OO0OOO000O0OO0OOO =float (OOOO0O0OO000OOO0O ["memory"])#line:420
                O0OOOO00OO0OO0000 =psutil .virtual_memory ().total #line:421
                OOOOO000OOOO0000O =round (100 *OO0OOO000O0OO0OOO /O0OOOO00OO0OO0000 ,2 )#line:422
                if OOOOO000OOOO0000O >=80 :#line:423
                    O000O00O0O0OO0000 .append ({"time":OOOO0O0OO000OOO0O ["addtime"],"name":OOOO0O0OO000OOO0O ["name"],"pid":OOOO0O0OO000OOO0O ["pid"],"percent":OOOOO000OOOO0000O })#line:431
        O000OOO0O0O0OOOOO =len (O000O00O0O0OO0000 )#line:432
        O000O00O0OO0O0000 =""#line:433
        OO0O0OOO00O0OO0O0 =0 #line:434
        if O000OOO0O0O0OOOOO ==0 :#line:435
            OO0O0OOO00O0OO0O0 =20 #line:436
        else :#line:437
            if O000OOO0O0O0OOOOO >1 :#line:438
                O000O00O0OO0O0000 ="内存在多个时间点出现占用80%"#line:439
            else :#line:440
                O000O00O0OO0O0000 ="内存出现占用超过80%"#line:441
        O0OO0OOO0OO000OO0 ={"ex":O000OOO0O0O0OOOOO ,"detail":O000O00O0O0OO0000 }#line:445
        OO00O0000OOO00OOO =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key=?",(O0O000O0OOOO00OOO ,))#line:449
        OOO0OO0O0OOO0OO00 =OO00O0000OOO00OOO .select ()#line:450
        O00O00000OO00OOO0 ={}#line:451
        if OOO0OO0O0OOO0OO00 and type (OOO0OO0O0OOO0OO00 )!=str :#line:452
            O00O00000OO00OOO0 =OOO0OO0O00O0OOOO0 .parse_app_usage_info (OOO0OO0O0OOO0OO00 [0 ])#line:453
        O0000OO0O000OOOOO =[]#line:454
        if O00O00000OO00OOO0 :#line:455
            O0O00O00O00OO0O0O =O00O00000OO00OOO0 ["disks"]#line:456
            for O0O0O0000OO0000OO ,O00OO0OO0OO000OO0 in O0O00O00O00OO0O0O .items ():#line:457
                O0OO0OO00OO00O0OO =int (O00OO0OO0OO000OO0 ["usage"])#line:458
                O0OOOO00OO0OO0000 =int (O00OO0OO0OO000OO0 ["total"])#line:459
                OO0O00O0OOOO0OOO0 =round (O0OO0OO00OO00O0OO /O0OOOO00OO0OO0000 ,2 )#line:460
                O00OOOOO0OOO0O000 =int (O00OO0OO0OO000OO0 ["iusage"])#line:462
                O0O00000O0000OOOO =int (O00OO0OO0OO000OO0 ["itotal"])#line:463
                OOO0O0OOO00OOO0OO =round (O00OOOOO0OOO0O000 /O0O00000O0000OOOO ,2 )#line:464
                if OO0O00O0OOOO0OOO0 >=0.8 :#line:468
                    O0000OO0O000OOOOO .append ({"name":O0O0O0000OO0000OO ,"percent":OO0O00O0OOOO0OOO0 *100 ,"ipercent":OOO0O0OOO00OOO0OO *100 ,"usage":O0OO0OO00OO00O0OO ,"total":O0OOOO00OO0OO0000 ,"iusage":O00OOOOO0OOO0O000 ,"itotal":O0O00000O0000OOOO })#line:477
        O0O0O0O0O0O00OOO0 =len (O0000OO0O000OOOOO )#line:479
        O00OO0OOOOO0O0O00 =""#line:480
        O0O0000O0OO00O00O =0 #line:481
        if O0O0O0O0O0O00OOO0 ==0 :#line:482
            O0O0000O0OO00O00O =20 #line:483
        else :#line:484
            O00OO0OOOOO0O0O00 ="有磁盘空间占用已经超过80%"#line:485
        OO000000O000000OO ={"ex":O0O0O0O0O0O00OOO0 ,"detail":O0000OO0O000OOOOO }#line:490
        OOO0OOO0OOO0O000O =public .M ("system").dbfile ("system").table ("server_status").where ("addtime>=? and addtime<=?",(O0000OO00O0O0OOO0 ,O0O0OO00000OO0000 ,)).order ("addtime desc").select ()#line:494
        O0O0000O0O00000OO =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:499
        OO000O0O0OO0OOOOO ={}#line:501
        OO0OOO0O00OOOO0O0 =0 #line:502
        O000O000000OOO000 =""#line:503
        for O0O00O0OOO000OOOO ,OOOOOOOO000000O0O in enumerate (O0O0000O0O00000OO ):#line:504
            if OOOOOOOO000000O0O =="pure-ftpd":#line:505
                OOOOOOOO000000O0O ="ftpd"#line:506
            OOO000O0OOO0OOOOO =0 #line:507
            O000OO0OO0OO0O0OO =[]#line:508
            for OOO00OOOO000OO0O0 in OOO0OOO0OOO0O000O :#line:509
                _OOO000OOOOOOOO0OO =OOO00OOOO000OO0O0 ["status"]#line:512
                if O0O00O0OOO000OOOO <len (_OOO000OOOOOOOO0OO ):#line:513
                    if _OOO000OOOOOOOO0OO [O0O00O0OOO000OOOO ]=="2":#line:514
                        O000OO0OO0OO0O0OO .append ({"time":OOO00OOOO000OO0O0 ["addtime"],"desc":"退出"})#line:515
                        OOO000O0OOO0OOOOO +=1 #line:516
                        OO0OOO0O00OOOO0O0 +=1 #line:517
            OO000O0O0OO0OOOOO [OOOOOOOO000000O0O ]={"ex":OOO000O0OOO0OOOOO ,"detail":O000OO0OO0OO0O0OO }#line:522
        O00OO0OOOO0O0O00O =0 #line:524
        if OO0OOO0O00OOOO0O0 ==0 :#line:525
            O00OO0OOOO0O0O00O =20 #line:526
        else :#line:527
            O000O000000OOO000 ="系统级服务有出现异常退出情况"#line:528
        O0O0OOOOOOOOOO00O =public .M ("crontab").field ("sName,sType").where ("sType in (?, ?)",("database","site",)).select ()#line:531
        OO00O00OOOO0OO0O0 =set (O00O00O00OOOO0O0O ["sName"]for O00O00O00OOOO0O0O in O0O0OOOOOOOOOO00O if O00O00O00OOOO0O0O ["sType"]=="database")#line:534
        O00OOO00OO000O0OO ="ALL"in OO00O00OOOO0OO0O0 #line:535
        O0OOO0O00OO0OOOO0 =set (O0OOOO0OO000O0O0O ["sName"]for O0OOOO0OO000O0O0O in O0O0OOOOOOOOOO00O if O0OOOO0OO000O0O0O ["sType"]=="site")#line:536
        OO0O0O00OO0OOO0O0 ="ALL"in O0OOO0O00OO0OOOO0 #line:537
        OOO0000OO0OOOOO00 =[]#line:538
        O0000O00000O000OO =[]#line:539
        if not O00OOO00OO000O0OO :#line:540
            O0000O0OOO00O00OO =public .M ("databases").field ("name").select ()#line:541
            for OOO0O0OO0O0000O00 in O0000O0OOO00O00OO :#line:542
                O0O000OO00OOO0O0O =OOO0O0OO0O0000O00 ["name"]#line:543
                if O0O000OO00OOO0O0O not in OO00O00OOOO0OO0O0 :#line:544
                    OOO0000OO0OOOOO00 .append ({"name":O0O000OO00OOO0O0O })#line:545
        if not OO0O0O00OO0OOO0O0 :#line:547
            OO0OO00O00OO000OO =public .M ("sites").field ("name").select ()#line:548
            for OO000OOOO0OOOOO00 in OO0OO00O00OO000OO :#line:549
                O00000O0OOO000O00 =OO000OOOO0OOOOO00 ["name"]#line:550
                if O00000O0OOO000O00 not in O0OOO0O00OO0OOOO0 :#line:551
                    O0000O00000O000OO .append ({"name":O00000O0OOO000O00 })#line:552
        OO00OOOO00O0OOO00 =public .M ("system").dbfile ("system").table ("backup_status").where ("addtime>=? and addtime<=?",(O0000OO00O0O0OOO0 ,O0O0OO00000OO0000 )).select ()#line:555
        O0OOOO0O0000000O0 ={"database":{"no_backup":OOO0000OO0OOOOO00 ,"backup":[]},"site":{"no_backup":O0000O00000O000OO ,"backup":[]},"path":{"no_backup":[],"backup":[]}}#line:570
        O0O000OOO0O0OOO00 =0 #line:571
        for OO0OOOOO00O0O0000 in OO00OOOO00O0OOO00 :#line:572
            O0OOOOOOO0OOOO0OO =OO0OOOOO00O0O0000 ["status"]#line:573
            if O0OOOOOOO0OOOO0OO :#line:574
                continue #line:575
            O0O000OOO0O0OOO00 +=1 #line:577
            OO000O000OO0OOO00 =OO0OOOOO00O0O0000 ["id"]#line:578
            OOO0000O0OOOOOO00 =public .M ("crontab").where ("id=?",(OO000O000OO0OOO00 )).find ()#line:579
            if not OOO0000O0OOOOOO00 :#line:580
                continue #line:581
            O0OO00O0O0000O0O0 =OOO0000O0OOOOOO00 ["sType"]#line:582
            if not O0OO00O0O0000O0O0 :#line:583
                continue #line:584
            O0O0O00000OOO00OO =OOO0000O0OOOOOO00 ["name"]#line:585
            OOO00O00O00OOO000 =OO0OOOOO00O0O0000 ["addtime"]#line:586
            OOOO0OO000OO0O000 =OO0OOOOO00O0O0000 ["target"]#line:587
            if O0OO00O0O0000O0O0 not in O0OOOO0O0000000O0 .keys ():#line:588
                O0OOOO0O0000000O0 [O0OO00O0O0000O0O0 ]={}#line:589
                O0OOOO0O0000000O0 [O0OO00O0O0000O0O0 ]["backup"]=[]#line:590
                O0OOOO0O0000000O0 [O0OO00O0O0000O0O0 ]["no_backup"]=[]#line:591
            O0OOOO0O0000000O0 [O0OO00O0O0000O0O0 ]["backup"].append ({"name":O0O0O00000OOO00OO ,"target":OOOO0OO000OO0O000 ,"status":O0OOOOOOO0OOOO0OO ,"target":OOOO0OO000OO0O000 ,"time":OOO00O00O00OOO000 })#line:598
        O0000OOOO00O0O0OO =""#line:600
        OOOO0OO00OO0000O0 =0 #line:601
        if O0O000OOO0O0OOO00 ==0 :#line:602
            OOOO0OO00OO0000O0 =20 #line:603
        else :#line:604
            O0000OOOO00O0O0OO ="有计划任务备份失败"#line:605
        if len (OOO0000OO0OOOOO00 )==0 :#line:607
            OOOO0OO00OO0000O0 +=10 #line:608
        else :#line:609
            if O0000OOOO00O0O0OO :#line:610
                O0000OOOO00O0O0OO +=";"#line:611
            O0000OOOO00O0O0OO +="有数据库未及时备份"#line:612
        if len (O0000O00000O000OO )==0 :#line:614
            OOOO0OO00OO0000O0 +=10 #line:615
        else :#line:616
            if O0000OOOO00O0O0OO :#line:617
                O0000OOOO00O0O0OO +=";"#line:618
            O0000OOOO00O0O0OO +="有网站未备份"#line:619
        OO00OOOOO0O0O00O0 =0 #line:622
        OOO00OO00O0OO000O =public .M ('logs').where ('addtime like "{}%" and type=?'.format (OO0OOO00OOO00OOO0 ),('用户登录',)).select ()#line:623
        OO0OO0OO0O0000OOO =[]#line:624
        if OOO00OO00O0OO000O and type (OOO00OO00O0OO000O )==list :#line:625
            for OO00OOO0OO0O0O0O0 in OOO00OO00O0OO000O :#line:626
                O0OO0OOO0O00O00O0 =OO00OOO0OO0O0O0O0 ["log"]#line:627
                if O0OO0OOO0O00O00O0 .find ("失败")>=0 or O0OO0OOO0O00O00O0 .find ("错误")>=0 :#line:628
                    OO00OOOOO0O0O00O0 +=1 #line:629
                    OO0OO0OO0O0000OOO .append ({"time":time .mktime (time .strptime (OO00OOO0OO0O0O0O0 ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":OO00OOO0OO0O0O0O0 ["log"],"username":OO00OOO0OO0O0O0O0 ["username"],})#line:634
            OO0OO0OO0O0000OOO .sort (key =lambda O0OO0000O0OOOOO00 :O0OO0000O0OOOOO00 ["time"])#line:635
        OO0O00O0000OOO00O =public .M ('logs').where ('type=?',('SSH安全',)).where ("addtime like '{}%'".format (OO0OOO00OOO00OOO0 ),()).select ()#line:637
        O00O00OO00000OOO0 =[]#line:639
        O000O0O00OOOO0OOO =0 #line:640
        if OO0O00O0000OOO00O :#line:641
            for OO00OOO0OO0O0O0O0 in OO0O00O0000OOO00O :#line:642
                O0OO0OOO0O00O00O0 =OO00OOO0OO0O0O0O0 ["log"]#line:643
                if O0OO0OOO0O00O00O0 .find ("存在异常")>=0 :#line:644
                    O000O0O00OOOO0OOO +=1 #line:645
                    O00O00OO00000OOO0 .append ({"time":time .mktime (time .strptime (OO00OOO0OO0O0O0O0 ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":OO00OOO0OO0O0O0O0 ["log"],"username":OO00OOO0OO0O0O0O0 ["username"]})#line:650
            O00O00OO00000OOO0 .sort (key =lambda OO0O000OO0O00OOOO :OO0O000OO0O00OOOO ["time"])#line:651
        O0O00OOOO00OO0000 =""#line:653
        OOOOOOOO000O000O0 =0 #line:654
        if O000O0O00OOOO0OOO ==0 :#line:655
            OOOOOOOO000O000O0 =10 #line:656
        else :#line:657
            O0O00OOOO00OO0000 ="SSH有异常登录"#line:658
        if OO00OOOOO0O0O00O0 ==0 :#line:660
            OOOOOOOO000O000O0 +=10 #line:661
        else :#line:662
            if OO00OOOOO0O0O00O0 >10 :#line:663
                OOOOOOOO000O000O0 -=10 #line:664
            if O0O00OOOO00OO0000 :#line:665
                O0O00OOOO00OO0000 +=";"#line:666
            O0O00OOOO00OO0000 +="面板登录有错误".format (OO00OOOOO0O0O00O0 )#line:667
        OOO0OOO0OOO0O000O ={"panel":{"ex":OO00OOOOO0O0O00O0 ,"detail":OO0OO0OO0O0000OOO },"ssh":{"ex":O000O0O00OOOO0OOO ,"detail":O00O00OO00000OOO0 }}#line:677
        OOO0O00O00O0O00OO =OO00OOOOOO0O0O0OO +OO0O0OOO00O0OO0O0 +O0O0000O0OO00O00O +O00OO0OOOO0O0O00O +OOOO0OO00OO0000O0 +OOOOOOOO000O000O0 #line:679
        OO00O0O0OOO00OO0O =[OOOO0OO0OO0O0O0OO ,O000O00O0OO0O0000 ,O00OO0OOOOO0O0O00 ,O000O000000OOO000 ,O0000OOOO00O0O0OO ,O0O00OOOO00OO0000 ]#line:680
        OOOO00000OO0OO0O0 =[]#line:681
        for O00OOOO000O0O0000 in OO00O0O0OOO00OO0O :#line:682
            if O00OOOO000O0O0000 :#line:683
                if O00OOOO000O0O0000 .find (";")>=0 :#line:684
                    for OOO0000OO0OOO000O in O00OOOO000O0O0000 .split (";"):#line:685
                        OOOO00000OO0OO0O0 .append (OOO0000OO0OOO000O )#line:686
                else :#line:687
                    OOOO00000OO0OO0O0 .append (O00OOOO000O0O0000 )#line:688
        if not OOOO00000OO0OO0O0 :#line:690
            OOOO00000OO0OO0O0 .append ("服务器运行正常，请继续保持！")#line:691
        O00O0000OO00OOOOO =OOO0OO0O00O0OOOO0 .evaluate (OOO0O00O00O0O00OO )#line:695
        return {"data":{"cpu":O0OOO0O0O0O000O00 ,"ram":O0OO0OOO0OO000OO0 ,"disk":OO000000O000000OO ,"server":OO000O0O0OO0OOOOO ,"backup":O0OOOO0O0000000O0 ,"exception":OOO0OOO0OOO0O000O ,},"evaluate":O00O0000OO00OOOOO ,"score":OOO0O00O00O0O00OO ,"date":O0O000O0OOOO00OOO ,"summary":OOOO00000OO0OO0O0 ,"status":True }#line:712
    def evaluate (O0OOO000OO0000O0O ,OOOOO0O00000O00O0 ):#line:714
        OO00O00O0OO0OOO00 =""#line:715
        if OOOOO0O00000O00O0 >=100 :#line:716
            OO00O00O0OO0OOO00 ="正常"#line:717
        elif OOOOO0O00000O00O0 >=80 :#line:718
            OO00O00O0OO0OOO00 ="良好"#line:719
        else :#line:720
            OO00O00O0OO0OOO00 ="一般"#line:721
        return OO00O00O0OO0OOO00 #line:722
    def get_daily_list (O0OO0O000OOOOO0O0 ,OO0O0O0OO0OOO00O0 ):#line:724
        O0O0O0O0O00000O00 =public .M ("system").dbfile ("system").table ("daily").where ("time_key>?",0 ).select ()#line:725
        OO00O0OOO0O0OOO00 =[]#line:726
        for O0O0000OOO0O000OO in O0O0O0O0O00000O00 :#line:727
            O0O0000OOO0O000OO ["evaluate"]=O0OO0O000OOOOO0O0 .evaluate (O0O0000OOO0O000OO ["evaluate"])#line:728
            OO00O0OOO0O0OOO00 .append (O0O0000OOO0O000OO )#line:729
        return OO00O0OOO0O0OOO00 
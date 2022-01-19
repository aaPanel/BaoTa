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
    def check_databases (O0O0OO0O00O00OOOO ):#line:30
        ""#line:31
        O00O0O0O0O00OO0OO =["app_usage","server_status","backup_status","daily"]#line:32
        import sqlite3 #line:33
        OOO0O000O0O0OO000 =sqlite3 .connect ("/www/server/panel/data/system.db")#line:34
        OOO00O0000OO0000O =OOO0O000O0O0OO000 .cursor ()#line:35
        O00OOO00OOO00OOOO =",".join (["'"+OOOO0O0OO0O0O0000 +"'"for OOOO0O0OO0O0O0000 in O00O0O0O0O00OO0OO ])#line:36
        OOOO0O000OOOOOOOO =OOO00O0000OO0000O .execute ("SELECT name FROM sqlite_master WHERE type='table' and name in ({})".format (O00OOO00OOO00OOOO ))#line:37
        OOOOOO00OOOO0O0OO =OOOO0O000OOOOOOOO .fetchall ()#line:38
        OO00O00000OOO0O00 =False #line:41
        O00OO0000O0O000O0 =[]#line:42
        if OOOOOO00OOOO0O0OO :#line:43
            O00OO0000O0O000O0 =[O0OOOOOO0O0OO00O0 [0 ]for O0OOOOOO0O0OO00O0 in OOOOOO00OOOO0O0OO ]#line:44
        if "app_usage"not in O00OO0000O0O000O0 :#line:46
            O0O0000O00O000OO0 ='''CREATE TABLE IF NOT EXISTS `app_usage` (
                    `time_key` INTEGER PRIMARY KEY,
                    `app` TEXT,
                    `disks` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:52
            OOO00O0000OO0000O .execute (O0O0000O00O000OO0 )#line:53
            OO00O00000OOO0O00 =True #line:54
        if "server_status"not in O00OO0000O0O000O0 :#line:56
            print ("创建server_status表:")#line:57
            O0O0000O00O000OO0 ='''CREATE TABLE IF NOT EXISTS `server_status` (
                    `status` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:61
            OOO00O0000OO0000O .execute (O0O0000O00O000OO0 )#line:62
            OO00O00000OOO0O00 =True #line:63
        if "backup_status"not in O00OO0000O0O000O0 :#line:65
            print ("创建备份状态表:")#line:66
            O0O0000O00O000OO0 ='''CREATE TABLE IF NOT EXISTS `backup_status` (
                    `id` INTEGER,
                    `target` TEXT,
                    `status` INTEGER,
                    `msg` TEXT DEFAULT "",
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:73
            OOO00O0000OO0000O .execute (O0O0000O00O000OO0 )#line:74
            OO00O00000OOO0O00 =True #line:75
        if "daily"not in O00OO0000O0O000O0 :#line:77
            O0O0000O00O000OO0 ='''CREATE TABLE IF NOT EXISTS `daily` (
                    `time_key` INTEGER,
                    `evaluate` INTEGER,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:82
            OOO00O0000OO0000O .execute (O0O0000O00O000OO0 )#line:83
            OO00O00000OOO0O00 =True #line:84
        if OO00O00000OOO0O00 :#line:86
            OOO0O000O0O0OO000 .commit ()#line:87
        OOO00O0000OO0000O .close ()#line:88
        OOO0O000O0O0OO000 .close ()#line:89
        return True #line:90
    def get_time_key (O00O0OO0O0OOO00OO ,date =None ):#line:92
        if date is None :#line:93
            date =time .localtime ()#line:94
        O0O0OOOO0OO0O00OO =0 #line:95
        O00OOO0000OOOO0O0 ="%Y%m%d"#line:96
        if type (date )==time .struct_time :#line:97
            O0O0OOOO0OO0O00OO =int (time .strftime (O00OOO0000OOOO0O0 ,date ))#line:98
        if type (date )==str :#line:99
            O0O0OOOO0OO0O00OO =int (time .strptime (date ,O00OOO0000OOOO0O0 ))#line:100
        return O0O0OOOO0OO0O00OO #line:101
    def store_app_usage (O0O0OO0O00OO00OO0 ,time_key =None ):#line:103
        ""#line:111
        O0O0OO0O00OO00OO0 .check_databases ()#line:113
        if time_key is None :#line:115
            time_key =O0O0OO0O00OO00OO0 .get_time_key ()#line:116
        O0O0OOO0O000OO000 =public .M ("system").dbfile ("system").table ("app_usage")#line:118
        OO0OO0OO0OOO00O00 =O0O0OOO0O000OO000 .field ("time_key").where ("time_key=?",(time_key )).find ()#line:119
        if OO0OO0OO0OOO00O00 and "time_key"in OO0OO0OO0OOO00O00 :#line:120
            if OO0OO0OO0OOO00O00 ["time_key"]==time_key :#line:121
                return True #line:123
        OO0O0OOO000O0O0O0 =public .M ('sites').field ('path').select ()#line:125
        O00OOOOOOOOOOO0OO =0 #line:126
        for O0O00O0000O0OO00O in OO0O0OOO000O0O0O0 :#line:127
            O00OOO0O00OO0OOO0 =O0O00O0000O0OO00O ["path"]#line:128
            if O00OOO0O00OO0OOO0 :#line:129
                O00OOOOOOOOOOO0OO +=public .get_path_size (O00OOO0O00OO0OOO0 )#line:130
        OO00O0O00000O00O0 =public .get_path_size ("/www/server/data")#line:132
        OO0OOOOOOOOOOOOOO =public .M ("ftps").field ("path").select ()#line:134
        O0O0OOOO0O0O0OOO0 =0 #line:135
        for O0O00O0000O0OO00O in OO0OOOOOOOOOOOOOO :#line:136
            OO00OOO0O0OOOOO0O =O0O00O0000O0OO00O ["path"]#line:137
            if OO00OOO0O0OOOOO0O :#line:138
                O0O0OOOO0O0O0OOO0 +=public .get_path_size (OO00OOO0O0OOOOO0O )#line:139
        OOO000OOOOOOOOOO0 =public .get_path_size ("/www/server/panel/plugin")#line:141
        OO00O00OO000OO0OO =["/www/server/total","/www/server/btwaf","/www/server/coll","/www/server/nginx","/www/server/apache","/www/server/redis"]#line:149
        for OO00O000OOOOOO000 in OO00O00OO000OO0OO :#line:150
            OOO000OOOOOOOOOO0 +=public .get_path_size (OO00O000OOOOOO000 )#line:151
        OOOOO00OO0OO00OOO =system ().GetDiskInfo2 (human =False )#line:153
        O00OO0O0OO000O0O0 =""#line:154
        O000OO00O0000OOOO =0 #line:155
        OO00000O000O0OOO0 =0 #line:156
        for O00O0000000O0O0OO in OOOOO00OO0OO00OOO :#line:157
            O0O000O000O00O000 =O00O0000000O0O0OO ["path"]#line:158
            if O00OO0O0OO000O0O0 :#line:159
                O00OO0O0OO000O0O0 +="-"#line:160
            O0OOO0O0000OOO0O0 ,OO00O000O00OO0OOO ,O0O0O0OOOOOO0O000 ,O000OOO0000O00O00 =O00O0000000O0O0OO ["size"]#line:161
            O00O000OOO0OO0000 ,OOO0000O000OOO000 ,_OOO00000OO00OO000 ,_OO0O0O0O0OOOO000O =O00O0000000O0O0OO ["inodes"]#line:162
            O00OO0O0OO000O0O0 ="{},{},{},{},{}".format (O0O000O000O00O000 ,OO00O000O00OO0OOO ,O0OOO0O0000OOO0O0 ,OOO0000O000OOO000 ,O00O000OOO0OO0000 )#line:163
            if O0O000O000O00O000 =="/":#line:164
                O000OO00O0000OOOO =O0OOO0O0000OOO0O0 #line:165
                OO00000O000O0OOO0 =OO00O000O00OO0OOO #line:166
        OO00O0O0O00O00OO0 ="{},{},{},{},{},{}".format (O000OO00O0000OOOO ,OO00000O000O0OOO0 ,O00OOOOOOOOOOO0OO ,OO00O0O00000O00O0 ,O0O0OOOO0O0O0OOO0 ,OOO000OOOOOOOOOO0 )#line:171
        OOO00O00O000OO00O =public .M ("system").dbfile ("system").table ("app_usage").add ("time_key,app,disks",(time_key ,OO00O0O0O00O00OO0 ,O00OO0O0OO000O0O0 ))#line:173
        if OOO00O00O000OO00O ==time_key :#line:174
            return True #line:175
        return False #line:178
    def parse_app_usage_info (OOO0OO00OOOO00000 ,OO0O0OO00OOO0OOO0 ):#line:180
        ""#line:181
        if not OO0O0OO00OOO0OOO0 :#line:182
            return {}#line:183
        print (OO0O0OO00OOO0OOO0 )#line:184
        OO00O0OO000O00OO0 ,OO00OOO00O000000O ,O0000OOO0O0O000O0 ,O0O0O0O000O00OOO0 ,O00O000O00OO0000O ,OO0000000OOO0O0OO =OO0O0OO00OOO0OOO0 ["app"].split (",")#line:185
        OO0OOOO00OOOO00O0 =OO0O0OO00OOO0OOO0 ["disks"].split ("-")#line:186
        O0OOOO0OOOOOOO0O0 ={}#line:187
        for O000O0OOOOOO000O0 in OO0OOOO00OOOO00O0 :#line:188
            O000OOOOO0O00OO00 ,OOOOO00O000OO00OO ,OOO0O000O0O0OOOOO ,OOOOOOO0OOOO0O00O ,OO0O0O00OO0O00O00 =O000O0OOOOOO000O0 .split (",")#line:189
            OOOOOOOOO00OO000O ={}#line:190
            OOOOOOOOO00OO000O ["usage"]=OOOOO00O000OO00OO #line:191
            OOOOOOOOO00OO000O ["total"]=OOO0O000O0O0OOOOO #line:192
            OOOOOOOOO00OO000O ["iusage"]=OOOOOOO0OOOO0O00O #line:193
            OOOOOOOOO00OO000O ["itotal"]=OO0O0O00OO0O00O00 #line:194
            O0OOOO0OOOOOOO0O0 [O000OOOOO0O00OO00 ]=OOOOOOOOO00OO000O #line:195
        return {"apps":{"disk_total":OO00O0OO000O00OO0 ,"disk_usage":OO00OOO00O000000O ,"sites":O0000OOO0O0O000O0 ,"databases":O0O0O0O000O00OOO0 ,"ftps":O00O000O00OO0000O ,"plugins":OO0000000OOO0O0OO },"disks":O0OOOO0OOOOOOO0O0 }#line:206
    def get_app_usage (OOOO000O000OO00O0 ,O000O00O000O0OOO0 ):#line:208
        O000O00OOOO00000O =time .localtime ()#line:210
        OOOO00O0OO0O0O00O =OOOO000O000OO00O0 .get_time_key ()#line:211
        OO0OOO0OOOOOO0OO0 =time .localtime (time .mktime ((O000O00OOOO00000O .tm_year ,O000O00OOOO00000O .tm_mon ,O000O00OOOO00000O .tm_mday -1 ,0 ,0 ,0 ,0 ,0 ,0 )))#line:214
        OO00O0OOOO0000000 =OOOO000O000OO00O0 .get_time_key (OO0OOO0OOOOOO0OO0 )#line:215
        O0O0OO000OOO0OOOO =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key =? or time_key=?",(OOOO00O0OO0O0O00O ,OO00O0OOOO0000000 ))#line:217
        OO0O00O00O0OO0O00 =O0O0OO000OOO0OOOO .select ()#line:218
        if type (OO0O00O00O0OO0O00 )==str or not OO0O00O00O0OO0O00 :#line:221
            return {}#line:222
        OOOOOOOOOO0O000OO ={}#line:223
        O0OOO00OOOO0OO00O ={}#line:224
        for O00000OO0OOO000O0 in OO0O00O00O0OO0O00 :#line:225
            if O00000OO0OOO000O0 ["time_key"]==OOOO00O0OO0O0O00O :#line:226
                OOOOOOOOOO0O000OO =OOOO000O000OO00O0 .parse_app_usage_info (O00000OO0OOO000O0 )#line:227
            if O00000OO0OOO000O0 ["time_key"]==OO00O0OOOO0000000 :#line:228
                O0OOO00OOOO0OO00O =OOOO000O000OO00O0 .parse_app_usage_info (O00000OO0OOO000O0 )#line:229
        if not OOOOOOOOOO0O000OO :#line:231
            return {}#line:232
        for O000OOOO0OO00OO0O ,OO00O0O0O0OO0O0OO in OOOOOOOOOO0O000OO ["disks"].items ():#line:235
            O0OOO000O00OOO0OO =int (OO00O0O0O0OO0O0OO ["total"])#line:236
            O000O00O000O000OO =int (OO00O0O0O0OO0O0OO ["usage"])#line:237
            OO0OOOOOOOO00OOO0 =int (OO00O0O0O0OO0O0OO ["itotal"])#line:239
            O0OOO0O0000OO0OO0 =int (OO00O0O0O0OO0O0OO ["iusage"])#line:240
            if O0OOO00OOOO0OO00O and O000OOOO0OO00OO0O in O0OOO00OOOO0OO00O ["disks"].keys ():#line:242
                O0O0OO00O0O0OOO00 =O0OOO00OOOO0OO00O ["disks"]#line:243
                OOO0OOOO0OOOO00OO =O0O0OO00O0O0OOO00 [O000OOOO0OO00OO0O ]#line:244
                O00O00O00O000000O =int (OOO0OOOO0OOOO00OO ["total"])#line:245
                if O00O00O00O000000O ==O0OOO000O00OOO0OO :#line:246
                    O0O000O00OOOO00O0 =int (OOO0OOOO0OOOO00OO ["usage"])#line:247
                    O0OO00OO0OO0O0O00 =0 #line:248
                    OOOO00O0OOO0000OO =O000O00O000O000OO -O0O000O00OOOO00O0 #line:249
                    if OOOO00O0OOO0000OO >0 :#line:250
                        O0OO00OO0OO0O0O00 =round (OOOO00O0OOO0000OO /O0OOO000O00OOO0OO ,2 )#line:251
                    OO00O0O0O0OO0O0OO ["incr"]=O0OO00OO0OO0O0O00 #line:252
                OO0OO0OOOOO0OOO0O =int (OOO0OOOO0OOOO00OO ["itotal"])#line:255
                if True :#line:256
                    O00OO0OO0OO000OOO =int (OOO0OOOO0OOOO00OO ["iusage"])#line:257
                    O0OOOO000OOOOOO00 =0 #line:258
                    OOOO00O0OOO0000OO =O0OOO0O0000OO0OO0 -O00OO0OO0OO000OOO #line:259
                    if OOOO00O0OOO0000OO >0 :#line:260
                        O0OOOO000OOOOOO00 =round (OOOO00O0OOO0000OO /OO0OOOOOOOO00OOO0 ,2 )#line:261
                    OO00O0O0O0OO0O0OO ["iincr"]=O0OOOO000OOOOOO00 #line:262
        OO0OO000OOO00OOO0 =OOOOOOOOOO0O000OO ["apps"]#line:266
        OOOO000OO0OOOOO00 =int (OO0OO000OOO00OOO0 ["disk_total"])#line:267
        if O0OOO00OOOO0OO00O and O0OOO00OOOO0OO00O ["apps"]["disk_total"]==OO0OO000OOO00OOO0 ["disk_total"]:#line:268
            O0O00O00O000OOO00 =O0OOO00OOOO0OO00O ["apps"]#line:269
            for O0OO0OO0OO00OOO0O ,O00O0O00O00OOOOO0 in OO0OO000OOO00OOO0 .items ():#line:270
                if O0OO0OO0OO00OOO0O =="disks":continue #line:271
                if O0OO0OO0OO00OOO0O =="disk_total":continue #line:272
                if O0OO0OO0OO00OOO0O =="disk_usage":continue #line:273
                OOO0OO0000O0OOO0O =0 #line:274
                OOOO00O0O0OO0O0O0 =int (O00O0O00O00OOOOO0 )-int (O0O00O00O000OOO00 [O0OO0OO0OO00OOO0O ])#line:275
                if OOOO00O0O0OO0O0O0 >0 :#line:276
                    OOO0OO0000O0OOO0O =round (OOOO00O0O0OO0O0O0 /OOOO000OO0OOOOO00 ,2 )#line:277
                OO0OO000OOO00OOO0 [O0OO0OO0OO00OOO0O ]={"val":O00O0O00O00OOOOO0 ,"incr":OOO0OO0000O0OOO0O }#line:282
        return OOOOOOOOOO0O000OO #line:283
    def get_timestamp_interval (OO0OO0O0OOO00OOOO ,O0O00O00OO0O000O0 ):#line:285
        O0OOOOOOOOOO00O0O =None #line:286
        O0O000OO00OOO0000 =None #line:287
        O0OOOOOOOOOO00O0O =time .mktime ((O0O00O00OO0O000O0 .tm_year ,O0O00O00OO0O000O0 .tm_mon ,O0O00O00OO0O000O0 .tm_mday ,0 ,0 ,0 ,0 ,0 ,0 ))#line:289
        O0O000OO00OOO0000 =time .mktime ((O0O00O00OO0O000O0 .tm_year ,O0O00O00OO0O000O0 .tm_mon ,O0O00O00OO0O000O0 .tm_mday ,23 ,59 ,59 ,0 ,0 ,0 ))#line:291
        return O0OOOOOOOOOO00O0O ,O0O000OO00OOO0000 #line:292
    def check_server (O00O00OOO0OOO0O00 ):#line:295
        try :#line:296
            O0O0000O0000OO0OO =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:299
            OOOO0OOOOOO00OOOO =panelPlugin ()#line:300
            O0OOO0O0O000OOO0O =public .dict_obj ()#line:301
            OOOO0OO0O000O0000 =""#line:302
            for O00O0000OOOOO0O0O in O0O0000O0000OO0OO :#line:303
                OOO0OOO000O0OO0OO =False #line:304
                O000OO000O0OO0000 =False #line:305
                O0OOO0O0O000OOO0O .name =O00O0000OOOOO0O0O #line:306
                OOO00OOO00OO0OO00 =OOOO0OOOOOO00OOOO .getPluginInfo (O0OOO0O0O000OOO0O )#line:307
                if not OOO00OOO00OO0OO00 :#line:308
                    continue #line:309
                OO0O0000OO000OO0O =OOO00OOO00OO0OO00 ["versions"]#line:310
                for OO0O0OOO0000OO0O0 in OO0O0000OO000OO0O :#line:312
                    if OO0O0OOO0000OO0O0 ["status"]:#line:315
                        O000OO000O0OO0000 =True #line:316
                    if "run"in OO0O0OOO0000OO0O0 .keys ()and OO0O0OOO0000OO0O0 ["run"]:#line:317
                        O000OO000O0OO0000 =True #line:319
                        OOO0OOO000O0OO0OO =True #line:320
                        break #line:321
                O0OO0O0OOOO00O000 =0 #line:322
                if O000OO000O0OO0000 :#line:323
                    O0OO0O0OOOO00O000 =1 #line:324
                    if not OOO0OOO000O0OO0OO :#line:326
                        O0OO0O0OOOO00O000 =2 #line:327
                OOOO0OO0O000O0000 +=str (O0OO0O0OOOO00O000 )#line:328
            if '2'in OOOO0OO0O000O0000 :#line:332
                public .M ("system").dbfile ("server_status").add ("status, addtime",(OOOO0OO0O000O0000 ,time .time ()))#line:334
        except Exception as OO0OOOO0OO0OOO0OO :#line:335
            return True #line:337
    def get_daily_data (OO0000O0O00O0OOO0 ,OOOOOOOOO00O00OO0 ):#line:339
        ""#line:340
        O00OOOO0O000OO000 ="IS_PRO_OR_LTD_FOR_PANEL_DAILY"#line:342
        O0OOOOOOO000O0O00 =cache .get (O00OOOO0O000OO000 )#line:343
        if not O0OOOOOOO000O0O00 :#line:344
            try :#line:345
                OO0000OO00000O000 =panelPlugin ()#line:346
                OO00O00O000O0O000 =OO0000OO00000O000 .get_soft_list (OOOOOOOOO00O00OO0 )#line:347
                if OO00O00O000O0O000 ["pro"]<0 and OO00O00O000O0O000 ["ltd"]<0 :#line:348
                    if os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:349
                        os .remove ("/www/server/panel/data/start_daily.pl")#line:350
                    return {"status":False ,"msg":"No authorization.","data":[],"date":OOOOOOOOO00O00OO0 .date }#line:356
                cache .set (O00OOOO0O000OO000 ,True ,86400 )#line:357
            except :#line:358
                return {"status":False ,"msg":"获取不到授权信息，请检查网络是否正常","data":[],"date":OOOOOOOOO00O00OO0 .date }#line:364
        if not os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:367
            public .writeFile ("/www/server/panel/data/start_daily.pl",OOOOOOOOO00O00OO0 .date )#line:368
        return OO0000O0O00O0OOO0 .get_daily_data_local (OOOOOOOOO00O00OO0 .date )#line:369
    def get_daily_data_local (OO0OO0000000000OO ,O00OO00O00OOOO0O0 ):#line:371
        O0000O0OOOO0OO0OO =time .strptime (O00OO00O00OOOO0O0 ,"%Y%m%d")#line:372
        OO0000O0O000OOOO0 =OO0OO0000000000OO .get_time_key (O0000O0OOOO0OO0OO )#line:373
        OO0OO0000000000OO .check_databases ()#line:375
        OOO0O00OOOO0OOOO0 =time .strftime ("%Y-%m-%d",O0000O0OOOO0OO0OO )#line:377
        OOO0OOO0O0O0OO00O =0 #line:378
        O000O0OOO0OO0O00O ,O0OOO00OO0O0OO000 =OO0OO0000000000OO .get_timestamp_interval (O0000O0OOOO0OO0OO )#line:379
        O00OOOO00OOOO0OO0 =public .M ("system").dbfile ("system")#line:380
        OOO0OOOO00O00OO0O =O00OOOO00OOOO0OO0 .table ("process_high_percent")#line:381
        O0000O0000000O000 =OOO0OOOO00O00OO0O .where ("addtime>=? and addtime<=?",(O000O0OOO0OO0O00O ,O0OOO00OO0O0OO000 )).order ("addtime").select ()#line:382
        O0O0O00OOOO0000OO =[]#line:386
        if len (O0000O0000000O000 )>0 :#line:387
            for O0O0O000OOOO0OO0O in O0000O0000000O000 :#line:389
                O000O000OOOO000OO =int (O0O0O000OOOO0OO0O ["cpu_percent"])#line:391
                if O000O000OOOO000OO >=80 :#line:392
                    O0O0O00OOOO0000OO .append ({"time":O0O0O000OOOO0OO0O ["addtime"],"name":O0O0O000OOOO0OO0O ["name"],"pid":O0O0O000OOOO0OO0O ["pid"],"percent":O000O000OOOO000OO })#line:400
        OO0OO0O00OOO0O0O0 =len (O0O0O00OOOO0000OO )#line:402
        OOOOO0O00O000OOO0 =0 #line:403
        OO0O0O0OO000000O0 =""#line:404
        if OO0OO0O00OOO0O0O0 ==0 :#line:405
            OOOOO0O00O000OOO0 =20 #line:406
        else :#line:407
            OO0O0O0OO000000O0 ="CPU出现过载情况"#line:408
        OOO0000O0O00OO000 ={"ex":OO0OO0O00OOO0O0O0 ,"detail":O0O0O00OOOO0000OO }#line:412
        OOO0O00OOOOOOO0OO =[]#line:415
        if len (O0000O0000000O000 )>0 :#line:416
            for O0O0O000OOOO0OO0O in O0000O0000000O000 :#line:418
                OOOOOOO000O000O00 =float (O0O0O000OOOO0OO0O ["memory"])#line:420
                OOOO0O00O0000O0O0 =psutil .virtual_memory ().total #line:421
                OOOO0O00OOO00O0O0 =round (100 *OOOOOOO000O000O00 /OOOO0O00O0000O0O0 ,2 )#line:422
                if OOOO0O00OOO00O0O0 >=80 :#line:423
                    OOO0O00OOOOOOO0OO .append ({"time":O0O0O000OOOO0OO0O ["addtime"],"name":O0O0O000OOOO0OO0O ["name"],"pid":O0O0O000OOOO0OO0O ["pid"],"percent":OOOO0O00OOO00O0O0 })#line:431
        O0000000O00OOO000 =len (OOO0O00OOOOOOO0OO )#line:432
        O0O00OO0OO0O00O00 =""#line:433
        OO0000O0OOO0O000O =0 #line:434
        if O0000000O00OOO000 ==0 :#line:435
            OO0000O0OOO0O000O =20 #line:436
        else :#line:437
            if O0000000O00OOO000 >1 :#line:438
                O0O00OO0OO0O00O00 ="内存在多个时间点出现占用80%"#line:439
            else :#line:440
                O0O00OO0OO0O00O00 ="内存出现占用超过80%"#line:441
        O00O00O0OOO0OOOOO ={"ex":O0000000O00OOO000 ,"detail":OOO0O00OOOOOOO0OO }#line:445
        O00O00OO0000000O0 =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key=?",(OO0000O0O000OOOO0 ,))#line:449
        O00O00OO00O0O0OOO =O00O00OO0000000O0 .select ()#line:450
        OOO0OO00O00O0O0OO ={}#line:451
        if O00O00OO00O0O0OOO and type (O00O00OO00O0O0OOO )!=str :#line:452
            OOO0OO00O00O0O0OO =OO0OO0000000000OO .parse_app_usage_info (O00O00OO00O0O0OOO [0 ])#line:453
        O000O00000OOOOOOO =[]#line:454
        if OOO0OO00O00O0O0OO :#line:455
            OO00OOOO0OOOOOO0O =OOO0OO00O00O0O0OO ["disks"]#line:456
            for O00O00O00OO0O0000 ,OO0OOO0000OO0O000 in OO00OOOO0OOOOOO0O .items ():#line:457
                OOOOO00OO0OOOO0OO =int (OO0OOO0000OO0O000 ["usage"])#line:458
                OOOO0O00O0000O0O0 =int (OO0OOO0000OO0O000 ["total"])#line:459
                OO0OOOO0OO0O00O00 =round (OOOOO00OO0OOOO0OO /OOOO0O00O0000O0O0 ,2 )#line:460
                O00OOOO0000OO0000 =int (OO0OOO0000OO0O000 ["iusage"])#line:462
                O00O000O000OOOOOO =int (OO0OOO0000OO0O000 ["itotal"])#line:463
                OO0OOOO0O00OOOO0O =round (O00OOOO0000OO0000 /O00O000O000OOOOOO ,2 )#line:464
                if OO0OOOO0OO0O00O00 >=0.8 :#line:468
                    O000O00000OOOOOOO .append ({"name":O00O00O00OO0O0000 ,"percent":OO0OOOO0OO0O00O00 *100 ,"ipercent":OO0OOOO0O00OOOO0O *100 ,"usage":OOOOO00OO0OOOO0OO ,"total":OOOO0O00O0000O0O0 ,"iusage":O00OOOO0000OO0000 ,"itotal":O00O000O000OOOOOO })#line:477
        OO00OO0O0OOOO0O0O =len (O000O00000OOOOOOO )#line:479
        OO0O0O00OO0000000 =""#line:480
        OOO0O0OO000OO0OO0 =0 #line:481
        if OO00OO0O0OOOO0O0O ==0 :#line:482
            OOO0O0OO000OO0OO0 =20 #line:483
        else :#line:484
            OO0O0O00OO0000000 ="有磁盘空间占用已经超过80%"#line:485
        OOO0O00O000OOO000 ={"ex":OO00OO0O0OOOO0O0O ,"detail":O000O00000OOOOOOO }#line:490
        O0000000OO00OO00O =public .M ("system").dbfile ("system").table ("server_status").where ("addtime>=? and addtime<=?",(O000O0OOO0OO0O00O ,O0OOO00OO0O0OO000 ,)).order ("addtime desc").select ()#line:494
        O0O0O0O00OO000OOO =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:499
        O000O000OO000000O ={}#line:501
        O00O00O000000OOO0 =0 #line:502
        OO00O0OOO0OOOOOO0 =""#line:503
        for OO0OO00OOOOO0OOO0 ,OO00OOOOOO00OO000 in enumerate (O0O0O0O00OO000OOO ):#line:504
            if OO00OOOOOO00OO000 =="pure-ftpd":#line:505
                OO00OOOOOO00OO000 ="ftpd"#line:506
            OOOO0OOOOOO0O00OO =0 #line:507
            OOOOO0000OOOO0O00 =[]#line:508
            for O0O00OO00O0O0OOO0 in O0000000OO00OO00O :#line:509
                _OO0OOO000OO000O00 =O0O00OO00O0O0OOO0 ["status"]#line:512
                if OO0OO00OOOOO0OOO0 <len (_OO0OOO000OO000O00 ):#line:513
                    if _OO0OOO000OO000O00 [OO0OO00OOOOO0OOO0 ]=="2":#line:514
                        OOOOO0000OOOO0O00 .append ({"time":O0O00OO00O0O0OOO0 ["addtime"],"desc":"退出"})#line:515
                        OOOO0OOOOOO0O00OO +=1 #line:516
                        O00O00O000000OOO0 +=1 #line:517
            O000O000OO000000O [OO00OOOOOO00OO000 ]={"ex":OOOO0OOOOOO0O00OO ,"detail":OOOOO0000OOOO0O00 }#line:522
        O0O0OO0O0000000OO =0 #line:524
        if O00O00O000000OOO0 ==0 :#line:525
            O0O0OO0O0000000OO =20 #line:526
        else :#line:527
            OO00O0OOO0OOOOOO0 ="系统级服务有出现异常退出情况"#line:528
        OO00O00OO000O0O00 =public .M ("crontab").field ("sName,sType").where ("sType in (?, ?)",("database","site",)).select ()#line:531
        O0O0O00O00000O0O0 =set (OOOO0OOOO0O000O0O ["sName"]for OOOO0OOOO0O000O0O in OO00O00OO000O0O00 if OOOO0OOOO0O000O0O ["sType"]=="database")#line:534
        O00OO0OOO0O0OOOO0 =set (O0O000O00OOOOO0OO ["sName"]for O0O000O00OOOOO0OO in OO00O00OO000O0O00 if O0O000O00OOOOO0OO ["sType"]=="site")#line:535
        O000OO00O00O00O00 =[]#line:536
        O0O0O0OO0OOO0O0O0 =[]#line:537
        OO0O0OO00O0O000O0 =public .M ("databases").field ("name").select ()#line:538
        for O00000OO00O00O000 in OO0O0OO00O0O000O0 :#line:539
            OO0OOOO0000O0OO00 =O00000OO00O00O000 ["name"]#line:540
            if OO0OOOO0000O0OO00 not in O0O0O00O00000O0O0 :#line:541
                O000OO00O00O00O00 .append ({"name":OO0OOOO0000O0OO00 })#line:542
        O0O000O0OOO000OO0 =public .M ("sites").field ("name").select ()#line:544
        for OOOO0OOOOOO000OO0 in O0O000O0OOO000OO0 :#line:545
            OO0OO00OOO00O0O0O =OOOO0OOOOOO000OO0 ["name"]#line:546
            if OO0OO00OOO00O0O0O not in O00OO0OOO0O0OOOO0 :#line:547
                O0O0O0OO0OOO0O0O0 .append ({"name":OO0OO00OOO00O0O0O })#line:548
        O0000O0O0O0O00O0O =public .M ("system").dbfile ("system").table ("backup_status").where ("addtime>=? and addtime<=?",(O000O0OOO0OO0O00O ,O0OOO00OO0O0OO000 )).select ()#line:551
        O00OOO0O0OO000OOO ={"database":{"no_backup":O000OO00O00O00O00 ,"backup":[]},"site":{"no_backup":O0O0O0OO0OOO0O0O0 ,"backup":[]},"path":{"no_backup":[],"backup":[]}}#line:566
        OOO00O0O000O00OOO =0 #line:567
        for OO0O00O00OOOO0000 in O0000O0O0O0O00O0O :#line:568
            O000OOOO0O0O00O0O =OO0O00O00OOOO0000 ["status"]#line:569
            if O000OOOO0O0O00O0O :#line:570
                continue #line:571
            OOO00O0O000O00OOO +=1 #line:573
            OO0000OO0OO0OOO0O =OO0O00O00OOOO0000 ["id"]#line:574
            OOOOOO0OOOO00O0O0 =public .M ("crontab").where ("id=?",(OO0000OO0OO0OOO0O )).find ()#line:575
            if not OOOOOO0OOOO00O0O0 :#line:576
                continue #line:577
            OO0000000O0OOO0OO =OOOOOO0OOOO00O0O0 ["sType"]#line:578
            if not OO0000000O0OOO0OO :#line:579
                continue #line:580
            O0OO0OO0O000OOOOO =OOOOOO0OOOO00O0O0 ["name"]#line:581
            O00O00O000OO0OOOO =OO0O00O00OOOO0000 ["addtime"]#line:582
            OO0000OOOOO00OOOO =OO0O00O00OOOO0000 ["target"]#line:583
            if OO0000000O0OOO0OO not in O00OOO0O0OO000OOO .keys ():#line:584
                O00OOO0O0OO000OOO [OO0000000O0OOO0OO ]={}#line:585
                O00OOO0O0OO000OOO [OO0000000O0OOO0OO ]["backup"]=[]#line:586
                O00OOO0O0OO000OOO [OO0000000O0OOO0OO ]["no_backup"]=[]#line:587
            O00OOO0O0OO000OOO [OO0000000O0OOO0OO ]["backup"].append ({"name":O0OO0OO0O000OOOOO ,"target":OO0000OOOOO00OOOO ,"status":O000OOOO0O0O00O0O ,"target":OO0000OOOOO00OOOO ,"time":O00O00O000OO0OOOO })#line:594
        OOO00OO0O0OOOOO0O =""#line:596
        OOO0OO0OOO0OO0OO0 =0 #line:597
        if OOO00O0O000O00OOO ==0 :#line:598
            OOO0OO0OOO0OO0OO0 =20 #line:599
        else :#line:600
            OOO00OO0O0OOOOO0O ="有计划任务备份失败"#line:601
        if len (O000OO00O00O00O00 )==0 :#line:603
            OOO0OO0OOO0OO0OO0 +=10 #line:604
        else :#line:605
            if OOO00OO0O0OOOOO0O :#line:606
                OOO00OO0O0OOOOO0O +=";"#line:607
            OOO00OO0O0OOOOO0O +="有数据库未及时备份"#line:608
        if len (O0O0O0OO0OOO0O0O0 )==0 :#line:610
            OOO0OO0OOO0OO0OO0 +=10 #line:611
        else :#line:612
            if OOO00OO0O0OOOOO0O :#line:613
                OOO00OO0O0OOOOO0O +=";"#line:614
            OOO00OO0O0OOOOO0O +="有网站未备份"#line:615
        OOOO0OOOO0OOOO0O0 =0 #line:618
        OOOOO000O0O0O0OO0 =public .M ('logs').where ('addtime like "{}%" and type=?'.format (OOO0O00OOOO0OOOO0 ),('用户登录',)).select ()#line:619
        O0000O00OOO0O00OO =[]#line:620
        if OOOOO000O0O0O0OO0 and type (OOOOO000O0O0O0OO0 )==list :#line:621
            for O00OO0000000OOO00 in OOOOO000O0O0O0OO0 :#line:622
                O0O00O000OOO0000O =O00OO0000000OOO00 ["log"]#line:623
                if O0O00O000OOO0000O .find ("失败")>=0 or O0O00O000OOO0000O .find ("错误")>=0 :#line:624
                    OOOO0OOOO0OOOO0O0 +=1 #line:625
                    O0000O00OOO0O00OO .append ({"time":time .mktime (time .strptime (O00OO0000000OOO00 ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":O00OO0000000OOO00 ["log"],"username":O00OO0000000OOO00 ["username"],})#line:630
            O0000O00OOO0O00OO .sort (key =lambda O0OOOOOO00O00O0OO :O0OOOOOO00O00O0OO ["time"])#line:631
        O000O00O0OO00000O =public .M ('logs').where ('type=?',('SSH安全',)).where ("addtime like '{}%'".format (OOO0O00OOOO0OOOO0 ),()).select ()#line:633
        O000OO000OOOO0000 =[]#line:635
        O0OOOO0OO0000O000 =0 #line:636
        if O000O00O0OO00000O :#line:637
            for O00OO0000000OOO00 in O000O00O0OO00000O :#line:638
                O0O00O000OOO0000O =O00OO0000000OOO00 ["log"]#line:639
                if O0O00O000OOO0000O .find ("存在异常")>=0 :#line:640
                    O0OOOO0OO0000O000 +=1 #line:641
                    O000OO000OOOO0000 .append ({"time":time .mktime (time .strptime (O00OO0000000OOO00 ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":O00OO0000000OOO00 ["log"],"username":O00OO0000000OOO00 ["username"]})#line:646
            O000OO000OOOO0000 .sort (key =lambda O0O0OO00O00OO0000 :O0O0OO00O00OO0000 ["time"])#line:647
        O0OO0O0OO000O00OO =""#line:649
        OOOO000OO0OOOOOOO =0 #line:650
        if O0OOOO0OO0000O000 ==0 :#line:651
            OOOO000OO0OOOOOOO =10 #line:652
        else :#line:653
            O0OO0O0OO000O00OO ="SSH有异常登录"#line:654
        if OOOO0OOOO0OOOO0O0 ==0 :#line:656
            OOOO000OO0OOOOOOO +=10 #line:657
        else :#line:658
            if OOOO0OOOO0OOOO0O0 >10 :#line:659
                OOOO000OO0OOOOOOO -=10 #line:660
            if O0OO0O0OO000O00OO :#line:661
                O0OO0O0OO000O00OO +=";"#line:662
            O0OO0O0OO000O00OO +="面板登录有错误".format (OOOO0OOOO0OOOO0O0 )#line:663
        O0000000OO00OO00O ={"panel":{"ex":OOOO0OOOO0OOOO0O0 ,"detail":O0000O00OOO0O00OO },"ssh":{"ex":O0OOOO0OO0000O000 ,"detail":O000OO000OOOO0000 }}#line:673
        OOO0OOO0O0O0OO00O =OOOOO0O00O000OOO0 +OO0000O0OOO0O000O +OOO0O0OO000OO0OO0 +O0O0OO0O0000000OO +OOO0OO0OOO0OO0OO0 +OOOO000OO0OOOOOOO #line:675
        O00000OO0O000O0OO =[OO0O0O0OO000000O0 ,O0O00OO0OO0O00O00 ,OO0O0O00OO0000000 ,OO00O0OOO0OOOOOO0 ,OOO00OO0O0OOOOO0O ,O0OO0O0OO000O00OO ]#line:676
        OO0OO00OOO0O000O0 =[]#line:677
        for OO0O0O0O0000O0OOO in O00000OO0O000O0OO :#line:678
            if OO0O0O0O0000O0OOO :#line:679
                if OO0O0O0O0000O0OOO .find (";")>=0 :#line:680
                    for OO00OOO0000O00OOO in OO0O0O0O0000O0OOO .split (";"):#line:681
                        OO0OO00OOO0O000O0 .append (OO00OOO0000O00OOO )#line:682
                else :#line:683
                    OO0OO00OOO0O000O0 .append (OO0O0O0O0000O0OOO )#line:684
        if not OO0OO00OOO0O000O0 :#line:686
            OO0OO00OOO0O000O0 .append ("服务器运行正常，请继续保持！")#line:687
        O0O0OO0OO00OO00O0 =OO0OO0000000000OO .evaluate (OOO0OOO0O0O0OO00O )#line:691
        return {"data":{"cpu":OOO0000O0O00OO000 ,"ram":O00O00O0OOO0OOOOO ,"disk":OOO0O00O000OOO000 ,"server":O000O000OO000000O ,"backup":O00OOO0O0OO000OOO ,"exception":O0000000OO00OO00O ,},"evaluate":O0O0OO0OO00OO00O0 ,"score":OOO0OOO0O0O0OO00O ,"date":OO0000O0O000OOOO0 ,"summary":OO0OO00OOO0O000O0 ,"status":True }#line:708
    def evaluate (OO00O0O0000OOOO0O ,OOOOOO0OOOOOOOO0O ):#line:710
        OOO00O0O0O000O0O0 =""#line:711
        if OOOOOO0OOOOOOOO0O >=100 :#line:712
            OOO00O0O0O000O0O0 ="正常"#line:713
        elif OOOOOO0OOOOOOOO0O >=80 :#line:714
            OOO00O0O0O000O0O0 ="良好"#line:715
        else :#line:716
            OOO00O0O0O000O0O0 ="一般"#line:717
        return OOO00O0O0O000O0O0 #line:718
    def get_daily_list (O00O0O0000OO0OOO0 ,OOOOO00O000000O0O ):#line:720
        O0O0O00000O0O000O =public .M ("system").dbfile ("system").table ("daily").where ("time_key>?",0 ).select ()#line:721
        OOO00OOO00000OOO0 =[]#line:722
        for OO0O0O0OOO0O00OO0 in O0O0O00000O0O000O :#line:723
            OO0O0O0OOO0O00OO0 ["evaluate"]=O00O0O0000OO0OOO0 .evaluate (OO0O0O0OOO0O00OO0 ["evaluate"])#line:724
            OOO00OOO00000OOO0 .append (OO0O0O0OOO0O00OO0 )#line:725
        return OOO00OOO00000OOO0 
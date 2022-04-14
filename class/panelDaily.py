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
    def check_databases (O000OOOO0OOOO00O0 ):#line:30
        ""#line:31
        OOOO000000OO0000O =["app_usage","server_status","backup_status","daily"]#line:32
        import sqlite3 #line:33
        OOO00OOO00000O0OO =sqlite3 .connect ("/www/server/panel/data/system.db")#line:34
        O0OOOOOO000000OOO =OOO00OOO00000O0OO .cursor ()#line:35
        O00O0O000OOOO0OOO =",".join (["'"+OOO0O0000O0OO0O00 +"'"for OOO0O0000O0OO0O00 in OOOO000000OO0000O ])#line:36
        OO0O0OOOO0000O0O0 =O0OOOOOO000000OOO .execute ("SELECT name FROM sqlite_master WHERE type='table' and name in ({})".format (O00O0O000OOOO0OOO ))#line:37
        OOOO000OO000OO00O =OO0O0OOOO0000O0O0 .fetchall ()#line:38
        O000O0OOO0O0OOOO0 =False #line:41
        OO0OOO00OOO000OO0 =[]#line:42
        if OOOO000OO000OO00O :#line:43
            OO0OOO00OOO000OO0 =[O000O0OOO000OO00O [0 ]for O000O0OOO000OO00O in OOOO000OO000OO00O ]#line:44
        if "app_usage"not in OO0OOO00OOO000OO0 :#line:46
            O000O0O000000O0OO ='''CREATE TABLE IF NOT EXISTS `app_usage` (
                    `time_key` INTEGER PRIMARY KEY,
                    `app` TEXT,
                    `disks` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:52
            O0OOOOOO000000OOO .execute (O000O0O000000O0OO )#line:53
            O000O0OOO0O0OOOO0 =True #line:54
        if "server_status"not in OO0OOO00OOO000OO0 :#line:56
            print ("创建server_status表:")#line:57
            O000O0O000000O0OO ='''CREATE TABLE IF NOT EXISTS `server_status` (
                    `status` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:61
            O0OOOOOO000000OOO .execute (O000O0O000000O0OO )#line:62
            O000O0OOO0O0OOOO0 =True #line:63
        if "backup_status"not in OO0OOO00OOO000OO0 :#line:65
            print ("创建备份状态表:")#line:66
            O000O0O000000O0OO ='''CREATE TABLE IF NOT EXISTS `backup_status` (
                    `id` INTEGER,
                    `target` TEXT,
                    `status` INTEGER,
                    `msg` TEXT DEFAULT "",
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:73
            O0OOOOOO000000OOO .execute (O000O0O000000O0OO )#line:74
            O000O0OOO0O0OOOO0 =True #line:75
        if "daily"not in OO0OOO00OOO000OO0 :#line:77
            O000O0O000000O0OO ='''CREATE TABLE IF NOT EXISTS `daily` (
                    `time_key` INTEGER,
                    `evaluate` INTEGER,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''#line:82
            O0OOOOOO000000OOO .execute (O000O0O000000O0OO )#line:83
            O000O0OOO0O0OOOO0 =True #line:84
        if O000O0OOO0O0OOOO0 :#line:86
            OOO00OOO00000O0OO .commit ()#line:87
        O0OOOOOO000000OOO .close ()#line:88
        OOO00OOO00000O0OO .close ()#line:89
        return True #line:90
    def get_time_key (OO00000O0000OOO00 ,date =None ):#line:92
        if date is None :#line:93
            date =time .localtime ()#line:94
        OO00O0OO0OO0OO0O0 =0 #line:95
        OO0000OO00000O00O ="%Y%m%d"#line:96
        if type (date )==time .struct_time :#line:97
            OO00O0OO0OO0OO0O0 =int (time .strftime (OO0000OO00000O00O ,date ))#line:98
        if type (date )==str :#line:99
            OO00O0OO0OO0OO0O0 =int (time .strptime (date ,OO0000OO00000O00O ))#line:100
        return OO00O0OO0OO0OO0O0 #line:101
    def store_app_usage (OOOO0O00O000O0O00 ,time_key =None ):#line:103
        ""#line:111
        OOOO0O00O000O0O00 .check_databases ()#line:113
        if time_key is None :#line:115
            time_key =OOOO0O00O000O0O00 .get_time_key ()#line:116
        OOO0OOO0O00OO0000 =public .M ("system").dbfile ("system").table ("app_usage")#line:118
        OOOO0OOO0O0OOOO00 =OOO0OOO0O00OO0000 .field ("time_key").where ("time_key=?",(time_key )).find ()#line:119
        if OOOO0OOO0O0OOOO00 and "time_key"in OOOO0OOO0O0OOOO00 :#line:120
            if OOOO0OOO0O0OOOO00 ["time_key"]==time_key :#line:121
                return True #line:123
        O000OOO00OOO0O0OO =public .M ('sites').field ('path').select ()#line:125
        O00OOO00000OO00O0 =0 #line:126
        for O00O0O0OOOOO0OO00 in O000OOO00OOO0O0OO :#line:127
            OO00O0OO00OO0O000 =O00O0O0OOOOO0OO00 ["path"]#line:128
            if OO00O0OO00OO0O000 :#line:129
                O00OOO00000OO00O0 +=public .get_path_size (OO00O0OO00OO0O000 )#line:130
        O00000OOOOO0O0O0O =public .get_path_size ("/www/server/data")#line:132
        O0O000000O0OO00O0 =public .M ("ftps").field ("path").select ()#line:134
        OOO00O0OOO00OO0OO =0 #line:135
        for O00O0O0OOOOO0OO00 in O0O000000O0OO00O0 :#line:136
            O0OOO000O0O0O0OO0 =O00O0O0OOOOO0OO00 ["path"]#line:137
            if O0OOO000O0O0O0OO0 :#line:138
                OOO00O0OOO00OO0OO +=public .get_path_size (O0OOO000O0O0O0OO0 )#line:139
        O000OO0OOOOOO0OOO =public .get_path_size ("/www/server/panel/plugin")#line:141
        O0OOO00000OOOOOOO =["/www/server/total","/www/server/btwaf","/www/server/coll","/www/server/nginx","/www/server/apache","/www/server/redis"]#line:149
        for OO0O000O0O0OO0000 in O0OOO00000OOOOOOO :#line:150
            O000OO0OOOOOO0OOO +=public .get_path_size (OO0O000O0O0OO0000 )#line:151
        OOO000O000OOO00O0 =system ().GetDiskInfo2 (human =False )#line:153
        OO0O000OOO0O0OO00 =""#line:154
        O00O0O0O000O00000 =0 #line:155
        O000O00O0O0O0O0OO =0 #line:156
        for OOO00OO00000OO0O0 in OOO000O000OOO00O0 :#line:157
            O0OOO0OOO00000OOO =OOO00OO00000OO0O0 ["path"]#line:158
            if OO0O000OOO0O0OO00 :#line:159
                OO0O000OOO0O0OO00 +="-"#line:160
            O0O0OOOO0OO0OOOO0 ,OOO0OO00O000O0O00 ,O0OOOOOOOOO0OO0O0 ,O0O00OO00O000OOO0 =OOO00OO00000OO0O0 ["size"]#line:161
            OOO00OOOOO00OOO0O ,O00000OO00OO0OOO0 ,_O00O00OO0OOO00OO0 ,_O0OOOOO0O0OOO000O =OOO00OO00000OO0O0 ["inodes"]#line:162
            OO0O000OOO0O0OO00 ="{},{},{},{},{}".format (O0OOO0OOO00000OOO ,OOO0OO00O000O0O00 ,O0O0OOOO0OO0OOOO0 ,O00000OO00OO0OOO0 ,OOO00OOOOO00OOO0O )#line:163
            if O0OOO0OOO00000OOO =="/":#line:164
                O00O0O0O000O00000 =O0O0OOOO0OO0OOOO0 #line:165
                O000O00O0O0O0O0OO =OOO0OO00O000O0O00 #line:166
        OOOO00O0O0O0OOO00 ="{},{},{},{},{},{}".format (O00O0O0O000O00000 ,O000O00O0O0O0O0OO ,O00OOO00000OO00O0 ,O00000OOOOO0O0O0O ,OOO00O0OOO00OO0OO ,O000OO0OOOOOO0OOO )#line:171
        OOO0O0OO000000OOO =public .M ("system").dbfile ("system").table ("app_usage").add ("time_key,app,disks",(time_key ,OOOO00O0O0O0OOO00 ,OO0O000OOO0O0OO00 ))#line:173
        if OOO0O0OO000000OOO ==time_key :#line:174
            return True #line:175
        return False #line:178
    def parse_app_usage_info (O00O0OO0000O00O00 ,O00OOO0O0OOOOOOOO ):#line:180
        ""#line:181
        if not O00OOO0O0OOOOOOOO :#line:182
            return {}#line:183
        print (O00OOO0O0OOOOOOOO )#line:184
        O0000OOO0O00OOOOO ,OO00O00OO0OO0OO0O ,O0OOO00O0O0000000 ,OO0O00O00OOOOO000 ,OO00O0000OO00000O ,O0OOOOOOO0000OOO0 =O00OOO0O0OOOOOOOO ["app"].split (",")#line:185
        OOO0O00O0O0OO0000 =O00OOO0O0OOOOOOOO ["disks"].split ("-")#line:186
        OOO00OOO0O0O00OOO ={}#line:187
        for OOO0O0OO0OOO000OO in OOO0O00O0O0OO0000 :#line:188
            O00OO00000O000000 ,OOOO0OOOOOO00OOOO ,O0O00000O00OO0OO0 ,O00000OO00OO0OO00 ,O0000OOOOOOO0O0O0 =OOO0O0OO0OOO000OO .split (",")#line:189
            OOO0O0O000OO000O0 ={}#line:190
            OOO0O0O000OO000O0 ["usage"]=OOOO0OOOOOO00OOOO #line:191
            OOO0O0O000OO000O0 ["total"]=O0O00000O00OO0OO0 #line:192
            OOO0O0O000OO000O0 ["iusage"]=O00000OO00OO0OO00 #line:193
            OOO0O0O000OO000O0 ["itotal"]=O0000OOOOOOO0O0O0 #line:194
            OOO00OOO0O0O00OOO [O00OO00000O000000 ]=OOO0O0O000OO000O0 #line:195
        return {"apps":{"disk_total":O0000OOO0O00OOOOO ,"disk_usage":OO00O00OO0OO0OO0O ,"sites":O0OOO00O0O0000000 ,"databases":OO0O00O00OOOOO000 ,"ftps":OO00O0000OO00000O ,"plugins":O0OOOOOOO0000OOO0 },"disks":OOO00OOO0O0O00OOO }#line:206
    def get_app_usage (O0O00O0OO0OO0OO00 ,O00O0O000OO0O0O0O ):#line:208
        O000000OO0OO0O0O0 =time .localtime ()#line:210
        O00OOOOO00000OOOO =O0O00O0OO0OO0OO00 .get_time_key ()#line:211
        O00OOO0000OO00O00 =time .localtime (time .mktime ((O000000OO0OO0O0O0 .tm_year ,O000000OO0OO0O0O0 .tm_mon ,O000000OO0OO0O0O0 .tm_mday -1 ,0 ,0 ,0 ,0 ,0 ,0 )))#line:214
        O0OO0O0OO0OO0O0O0 =O0O00O0OO0OO0OO00 .get_time_key (O00OOO0000OO00O00 )#line:215
        O0O000OO0O0OOOO00 =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key =? or time_key=?",(O00OOOOO00000OOOO ,O0OO0O0OO0OO0O0O0 ))#line:217
        OO00O00O000OO00OO =O0O000OO0O0OOOO00 .select ()#line:218
        if type (OO00O00O000OO00OO )==str or not OO00O00O000OO00OO :#line:221
            return {}#line:222
        OO00O000O00OO00OO ={}#line:223
        OO00O0O0OOO0O0O0O ={}#line:224
        for O0OOO00O0OOO0OOOO in OO00O00O000OO00OO :#line:225
            if O0OOO00O0OOO0OOOO ["time_key"]==O00OOOOO00000OOOO :#line:226
                OO00O000O00OO00OO =O0O00O0OO0OO0OO00 .parse_app_usage_info (O0OOO00O0OOO0OOOO )#line:227
            if O0OOO00O0OOO0OOOO ["time_key"]==O0OO0O0OO0OO0O0O0 :#line:228
                OO00O0O0OOO0O0O0O =O0O00O0OO0OO0OO00 .parse_app_usage_info (O0OOO00O0OOO0OOOO )#line:229
        if not OO00O000O00OO00OO :#line:231
            return {}#line:232
        for O000O0000OO0OOO00 ,OO0O0OOOO0O0O0000 in OO00O000O00OO00OO ["disks"].items ():#line:235
            O0000OO0O0OO0O00O =int (OO0O0OOOO0O0O0000 ["total"])#line:236
            OOOOOOOO000O00OOO =int (OO0O0OOOO0O0O0000 ["usage"])#line:237
            OOO00O0OOO00O0OO0 =int (OO0O0OOOO0O0O0000 ["itotal"])#line:239
            O0O0OOOOOO0000O00 =int (OO0O0OOOO0O0O0000 ["iusage"])#line:240
            if OO00O0O0OOO0O0O0O and O000O0000OO0OOO00 in OO00O0O0OOO0O0O0O ["disks"].keys ():#line:242
                OO0OO0O0OOO0000O0 =OO00O0O0OOO0O0O0O ["disks"]#line:243
                OO00OOO00OO00O0OO =OO0OO0O0OOO0000O0 [O000O0000OO0OOO00 ]#line:244
                O0OOO00OO0O00OOO0 =int (OO00OOO00OO00O0OO ["total"])#line:245
                if O0OOO00OO0O00OOO0 ==O0000OO0O0OO0O00O :#line:246
                    OOO0O0OOOO00OOO0O =int (OO00OOO00OO00O0OO ["usage"])#line:247
                    OO0000O0O00OOOOO0 =0 #line:248
                    OO00000OOOOO0OO00 =OOOOOOOO000O00OOO -OOO0O0OOOO00OOO0O #line:249
                    if OO00000OOOOO0OO00 >0 :#line:250
                        OO0000O0O00OOOOO0 =round (OO00000OOOOO0OO00 /O0000OO0O0OO0O00O ,2 )#line:251
                    OO0O0OOOO0O0O0000 ["incr"]=OO0000O0O00OOOOO0 #line:252
                OOO00000OOO000OO0 =int (OO00OOO00OO00O0OO ["itotal"])#line:255
                if True :#line:256
                    O0O0O0OOOOOOO0O0O =int (OO00OOO00OO00O0OO ["iusage"])#line:257
                    OOOO00O000000O000 =0 #line:258
                    OO00000OOOOO0OO00 =O0O0OOOOOO0000O00 -O0O0O0OOOOOOO0O0O #line:259
                    if OO00000OOOOO0OO00 >0 :#line:260
                        OOOO00O000000O000 =round (OO00000OOOOO0OO00 /OOO00O0OOO00O0OO0 ,2 )#line:261
                    OO0O0OOOO0O0O0000 ["iincr"]=OOOO00O000000O000 #line:262
        OO0O000OO0OO00OO0 =OO00O000O00OO00OO ["apps"]#line:266
        O000OOOOOO0000O00 =int (OO0O000OO0OO00OO0 ["disk_total"])#line:267
        if OO00O0O0OOO0O0O0O and OO00O0O0OOO0O0O0O ["apps"]["disk_total"]==OO0O000OO0OO00OO0 ["disk_total"]:#line:268
            OO00O0OOO0OO0O000 =OO00O0O0OOO0O0O0O ["apps"]#line:269
            for OOO0OO0OOO00O000O ,O0O0O0OO0O000OO00 in OO0O000OO0OO00OO0 .items ():#line:270
                if OOO0OO0OOO00O000O =="disks":continue #line:271
                if OOO0OO0OOO00O000O =="disk_total":continue #line:272
                if OOO0OO0OOO00O000O =="disk_usage":continue #line:273
                OO00O000O000OO0O0 =0 #line:274
                O000OO0O0000OO000 =int (O0O0O0OO0O000OO00 )-int (OO00O0OOO0OO0O000 [OOO0OO0OOO00O000O ])#line:275
                if O000OO0O0000OO000 >0 :#line:276
                    OO00O000O000OO0O0 =round (O000OO0O0000OO000 /O000OOOOOO0000O00 ,2 )#line:277
                OO0O000OO0OO00OO0 [OOO0OO0OOO00O000O ]={"val":O0O0O0OO0O000OO00 ,"incr":OO00O000O000OO0O0 }#line:282
        return OO00O000O00OO00OO #line:283
    def get_timestamp_interval (O0O0O00000OO0O000 ,O0O0O0000O0OO00OO ):#line:285
        OOOO000000O0O0OO0 =None #line:286
        O0OOOO0O0000000O0 =None #line:287
        OOOO000000O0O0OO0 =time .mktime ((O0O0O0000O0OO00OO .tm_year ,O0O0O0000O0OO00OO .tm_mon ,O0O0O0000O0OO00OO .tm_mday ,0 ,0 ,0 ,0 ,0 ,0 ))#line:289
        O0OOOO0O0000000O0 =time .mktime ((O0O0O0000O0OO00OO .tm_year ,O0O0O0000O0OO00OO .tm_mon ,O0O0O0000O0OO00OO .tm_mday ,23 ,59 ,59 ,0 ,0 ,0 ))#line:291
        return OOOO000000O0O0OO0 ,O0OOOO0O0000000O0 #line:292
    def check_server (OOO0O0O00O00OO000 ):#line:295
        try :#line:296
            O000O0OO0OOO0OO00 =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:299
            O0O0O0O000OOOOOO0 =panelPlugin ()#line:300
            OO00O00OO000O00OO =public .dict_obj ()#line:301
            O00OOO00OO00OO0OO =""#line:302
            for OO0O0OOO0OO0O0OOO in O000O0OO0OOO0OO00 :#line:303
                OOO0OO000OO00OOO0 =False #line:304
                OO0OOOO0O0OO0000O =False #line:305
                OO00O00OO000O00OO .name =OO0O0OOO0OO0O0OOO #line:306
                O0O000O00000OO00O =O0O0O0O000OOOOOO0 .getPluginInfo (OO00O00OO000O00OO )#line:307
                if not O0O000O00000OO00O :#line:308
                    continue #line:309
                OOO00OOOO0O00OO00 =O0O000O00000OO00O ["versions"]#line:310
                for O000O0OOO0O00OOO0 in OOO00OOOO0O00OO00 :#line:312
                    if O000O0OOO0O00OOO0 ["status"]:#line:315
                        OO0OOOO0O0OO0000O =True #line:316
                    if "run"in O000O0OOO0O00OOO0 .keys ()and O000O0OOO0O00OOO0 ["run"]:#line:317
                        OO0OOOO0O0OO0000O =True #line:319
                        OOO0OO000OO00OOO0 =True #line:320
                        break #line:321
                OOO00OO0000000O0O =0 #line:322
                if OO0OOOO0O0OO0000O :#line:323
                    OOO00OO0000000O0O =1 #line:324
                    if not OOO0OO000OO00OOO0 :#line:326
                        OOO00OO0000000O0O =2 #line:327
                O00OOO00OO00OO0OO +=str (OOO00OO0000000O0O )#line:328
            if '2'in O00OOO00OO00OO0OO :#line:332
                public .M ("system").dbfile ("server_status").add ("status, addtime",(O00OOO00OO00OO0OO ,time .time ()))#line:334
        except Exception as O00OO00OOOO0000O0 :#line:335
            return True #line:337
    def get_daily_data (OOOOO00OO0O0OO0OO ,OO0OOOO0O000OOO00 ):#line:339
        ""#line:340
        O00O000O000OOOOOO ="IS_PRO_OR_LTD_FOR_PANEL_DAILY"#line:342
        O00OOOOOOO0O0O0OO =cache .get (O00O000O000OOOOOO )#line:343
        if not O00OOOOOOO0O0O0OO :#line:344
            try :#line:345
                O0O0O0O00O00OOO00 =panelPlugin ()#line:346
                O0OOOOOOO0OO0000O =O0O0O0O00O00OOO00 .get_soft_list (OO0OOOO0O000OOO00 )#line:347
                if O0OOOOOOO0OO0000O ["pro"]<0 and O0OOOOOOO0OO0000O ["ltd"]<0 :#line:348
                    if os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:349
                        os .remove ("/www/server/panel/data/start_daily.pl")#line:350
                    return {"status":False ,"msg":"No authorization.","data":[],"date":OO0OOOO0O000OOO00 .date }#line:356
                cache .set (O00O000O000OOOOOO ,True ,86400 )#line:357
            except :#line:358
                return {"status":False ,"msg":"获取不到授权信息，请检查网络是否正常","data":[],"date":OO0OOOO0O000OOO00 .date }#line:364
        if not os .path .exists ("/www/server/panel/data/start_daily.pl"):#line:367
            public .writeFile ("/www/server/panel/data/start_daily.pl",OO0OOOO0O000OOO00 .date )#line:368
        return OOOOO00OO0O0OO0OO .get_daily_data_local (OO0OOOO0O000OOO00 .date )#line:369
    def get_daily_data_local (OOO00O00O000O0O00 ,OO0OOO0OO0000O000 ):#line:371
        OO00OOO00OOO00OO0 =time .strptime (OO0OOO0OO0000O000 ,"%Y%m%d")#line:372
        O0O000OO0OOOOO00O =OOO00O00O000O0O00 .get_time_key (OO00OOO00OOO00OO0 )#line:373
        OOO00O00O000O0O00 .check_databases ()#line:375
        O0O0O00OO00OO0OOO =time .strftime ("%Y-%m-%d",OO00OOO00OOO00OO0 )#line:377
        O0OOO00O0O00OOOO0 =0 #line:378
        OOOOOO000O00OO00O ,O0O00O000O0O00OOO =OOO00O00O000O0O00 .get_timestamp_interval (OO00OOO00OOO00OO0 )#line:379
        O0OO0OOO0O0OOOOO0 =public .M ("system").dbfile ("system")#line:380
        OO0OO00O00OOOOOO0 =O0OO0OOO0O0OOOOO0 .table ("process_high_percent")#line:381
        O00O0OOO00O0O0000 =OO0OO00O00OOOOOO0 .where ("addtime>=? and addtime<=?",(OOOOOO000O00OO00O ,O0O00O000O0O00OOO )).order ("addtime").select ()#line:382
        O00O0O000O0OO0000 =[]#line:386
        if len (O00O0OOO00O0O0000 )>0 :#line:387
            for OOO0000OO0OOOOO0O in O00O0OOO00O0O0000 :#line:389
                OOO000O000O00O00O =int (OOO0000OO0OOOOO0O ["cpu_percent"])#line:391
                if OOO000O000O00O00O >=80 :#line:392
                    O00O0O000O0OO0000 .append ({"time":OOO0000OO0OOOOO0O ["addtime"],"name":OOO0000OO0OOOOO0O ["name"],"pid":OOO0000OO0OOOOO0O ["pid"],"percent":OOO000O000O00O00O })#line:400
        O0O0OOOO00O0O0O00 =len (O00O0O000O0OO0000 )#line:402
        OO0000O00O0OOO00O =0 #line:403
        OOO0O0O0O0000OOO0 =""#line:404
        if O0O0OOOO00O0O0O00 ==0 :#line:405
            OO0000O00O0OOO00O =20 #line:406
        else :#line:407
            OOO0O0O0O0000OOO0 ="CPU出现过载情况"#line:408
        O0OOOOO000O0OOOOO ={"ex":O0O0OOOO00O0O0O00 ,"detail":O00O0O000O0OO0000 }#line:412
        O000000OO0O00000O =[]#line:415
        if len (O00O0OOO00O0O0000 )>0 :#line:416
            for OOO0000OO0OOOOO0O in O00O0OOO00O0O0000 :#line:418
                O0O000O0OOOOO00O0 =float (OOO0000OO0OOOOO0O ["memory"])#line:420
                O0O0O0O0O0000O0OO =psutil .virtual_memory ().total #line:421
                OO0000OOO00O0000O =round (100 *O0O000O0OOOOO00O0 /O0O0O0O0O0000O0OO ,2 )#line:422
                if OO0000OOO00O0000O >=80 :#line:423
                    O000000OO0O00000O .append ({"time":OOO0000OO0OOOOO0O ["addtime"],"name":OOO0000OO0OOOOO0O ["name"],"pid":OOO0000OO0OOOOO0O ["pid"],"percent":OO0000OOO00O0000O })#line:431
        O0000OOO000O0OO00 =len (O000000OO0O00000O )#line:432
        OOO00O0OOOOOO0OO0 =""#line:433
        O0OO000O00O0O0000 =0 #line:434
        if O0000OOO000O0OO00 ==0 :#line:435
            O0OO000O00O0O0000 =20 #line:436
        else :#line:437
            if O0000OOO000O0OO00 >1 :#line:438
                OOO00O0OOOOOO0OO0 ="内存在多个时间点出现占用80%"#line:439
            else :#line:440
                OOO00O0OOOOOO0OO0 ="内存出现占用超过80%"#line:441
        O0OOO0OOOOOO00O00 ={"ex":O0000OOO000O0OO00 ,"detail":O000000OO0O00000O }#line:445
        OOO0OOOOOO0OO0O00 =public .M ("system").dbfile ("system").table ("app_usage").where ("time_key=?",(O0O000OO0OOOOO00O ,))#line:449
        O0000OO0OO0OOOO0O =OOO0OOOOOO0OO0O00 .select ()#line:450
        O000000O0OO00OO0O ={}#line:451
        if O0000OO0OO0OOOO0O and type (O0000OO0OO0OOOO0O )!=str :#line:452
            O000000O0OO00OO0O =OOO00O00O000O0O00 .parse_app_usage_info (O0000OO0OO0OOOO0O [0 ])#line:453
        OOO0O000OOO00O0O0 =[]#line:454
        if O000000O0OO00OO0O :#line:455
            OOOO000O00O0OO0O0 =O000000O0OO00OO0O ["disks"]#line:456
            for OOOOO000OOO000OO0 ,OOO0OO0O0OO0OOOOO in OOOO000O00O0OO0O0 .items ():#line:457
                O000OO0OOOOO000O0 =int (OOO0OO0O0OO0OOOOO ["usage"])#line:458
                O0O0O0O0O0000O0OO =int (OOO0OO0O0OO0OOOOO ["total"])#line:459
                O00OO00OOO00000O0 =round (O000OO0OOOOO000O0 /O0O0O0O0O0000O0OO ,2 )#line:460
                O000OOOOOO0O0O0OO =int (OOO0OO0O0OO0OOOOO ["iusage"])#line:462
                O000000O0O0OO0000 =int (OOO0OO0O0OO0OOOOO ["itotal"])#line:463
                if O000000O0O0OO0000 >0 :#line:464
                    OO0OOO0OOO0O00000 =round (O000OOOOOO0O0O0OO /O000000O0O0OO0000 ,2 )#line:465
                else :#line:466
                    OO0OOO0OOO0O00000 =0 #line:467
                if O00OO00OOO00000O0 >=0.8 :#line:471
                    OOO0O000OOO00O0O0 .append ({"name":OOOOO000OOO000OO0 ,"percent":O00OO00OOO00000O0 *100 ,"ipercent":OO0OOO0OOO0O00000 *100 ,"usage":O000OO0OOOOO000O0 ,"total":O0O0O0O0O0000O0OO ,"iusage":O000OOOOOO0O0O0OO ,"itotal":O000000O0O0OO0000 })#line:480
        OOOO0OO0OO00OO0O0 =len (OOO0O000OOO00O0O0 )#line:482
        OO0O00OOO0OOOO0O0 =""#line:483
        OO0O0O000000O0O00 =0 #line:484
        if OOOO0OO0OO00OO0O0 ==0 :#line:485
            OO0O0O000000O0O00 =20 #line:486
        else :#line:487
            OO0O00OOO0OOOO0O0 ="有磁盘空间占用已经超过80%"#line:488
        O00O000O000O00O00 ={"ex":OOOO0OO0OO00OO0O0 ,"detail":OOO0O000OOO00O0O0 }#line:493
        O00O0O0OO000O0OOO =public .M ("system").dbfile ("system").table ("server_status").where ("addtime>=? and addtime<=?",(OOOOOO000O00OO00O ,O0O00O000O0O00OOO ,)).order ("addtime desc").select ()#line:497
        OO00OO000OOO000O0 =["php","nginx","apache","mysql","tomcat","pure-ftpd","redis","memcached"]#line:502
        OO00000000O0000O0 ={}#line:504
        O0O000OO000O000OO =0 #line:505
        O00O0O0OOOOOOOOO0 =""#line:506
        for OO0O0000OO0OO0OO0 ,OO00OO0O00O00OO0O in enumerate (OO00OO000OOO000O0 ):#line:507
            if OO00OO0O00O00OO0O =="pure-ftpd":#line:508
                OO00OO0O00O00OO0O ="ftpd"#line:509
            O0000O0000000O0OO =0 #line:510
            O0O00000OO00OOOOO =[]#line:511
            for OOO0O00000O000O0O in O00O0O0OO000O0OOO :#line:512
                _O0OOO0O000000OOOO =OOO0O00000O000O0O ["status"]#line:515
                if OO0O0000OO0OO0OO0 <len (_O0OOO0O000000OOOO ):#line:516
                    if _O0OOO0O000000OOOO [OO0O0000OO0OO0OO0 ]=="2":#line:517
                        O0O00000OO00OOOOO .append ({"time":OOO0O00000O000O0O ["addtime"],"desc":"退出"})#line:518
                        O0000O0000000O0OO +=1 #line:519
                        O0O000OO000O000OO +=1 #line:520
            OO00000000O0000O0 [OO00OO0O00O00OO0O ]={"ex":O0000O0000000O0OO ,"detail":O0O00000OO00OOOOO }#line:525
        OOOOO0OO00O00O0O0 =0 #line:527
        if O0O000OO000O000OO ==0 :#line:528
            OOOOO0OO00O00O0O0 =20 #line:529
        else :#line:530
            O00O0O0OOOOOOOOO0 ="系统级服务有出现异常退出情况"#line:531
        O0OO00O0O00OOO0OO =public .M ("crontab").field ("sName,sType").where ("sType in (?, ?)",("database","site",)).select ()#line:534
        O0000O0O000O0O0OO =set (O0OO0O0O0OO000O00 ["sName"]for O0OO0O0O0OO000O00 in O0OO00O0O00OOO0OO if O0OO0O0O0OO000O00 ["sType"]=="database")#line:537
        OO0O0OOO000O000O0 ="ALL"in O0000O0O000O0O0OO #line:538
        OOO00O0OOOOOO0O00 =set (O0O0OOOOOOO0000O0 ["sName"]for O0O0OOOOOOO0000O0 in O0OO00O0O00OOO0OO if O0O0OOOOOOO0000O0 ["sType"]=="site")#line:539
        O0OO00O0O0OOO0000 ="ALL"in OOO00O0OOOOOO0O00 #line:540
        O0000OOO00OO00OOO =[]#line:541
        OOOO00OOO0O000O0O =[]#line:542
        if not OO0O0OOO000O000O0 :#line:543
            O000OO00000000O00 =public .M ("databases").field ("name").select ()#line:544
            for OO000O00O00O00OOO in O000OO00000000O00 :#line:545
                O0000000OO0000000 =OO000O00O00O00OOO ["name"]#line:546
                if O0000000OO0000000 not in O0000O0O000O0O0OO :#line:547
                    O0000OOO00OO00OOO .append ({"name":O0000000OO0000000 })#line:548
        if not O0OO00O0O0OOO0000 :#line:550
            O0OO000000O00O0O0 =public .M ("sites").field ("name").select ()#line:551
            for O0O00OOO0OOOO000O in O0OO000000O00O0O0 :#line:552
                OOO0O0OO00O000O00 =O0O00OOO0OOOO000O ["name"]#line:553
                if OOO0O0OO00O000O00 not in OOO00O0OOOOOO0O00 :#line:554
                    OOOO00OOO0O000O0O .append ({"name":OOO0O0OO00O000O00 })#line:555
        O00OO0O00OOO0O0OO =public .M ("system").dbfile ("system").table ("backup_status").where ("addtime>=? and addtime<=?",(OOOOOO000O00OO00O ,O0O00O000O0O00OOO )).select ()#line:558
        OOO000O00OO0O000O ={"database":{"no_backup":O0000OOO00OO00OOO ,"backup":[]},"site":{"no_backup":OOOO00OOO0O000O0O ,"backup":[]},"path":{"no_backup":[],"backup":[]}}#line:573
        O00OOOO0O0OOO0OOO =0 #line:574
        for O000OOO00O0OOO00O in O00OO0O00OOO0O0OO :#line:575
            OO00OOO0OOO0O0OOO =O000OOO00O0OOO00O ["status"]#line:576
            if OO00OOO0OOO0O0OOO :#line:577
                continue #line:578
            O00OOOO0O0OOO0OOO +=1 #line:580
            O0000OO0O00O00000 =O000OOO00O0OOO00O ["id"]#line:581
            O00OO0O00OOOOO000 =public .M ("crontab").where ("id=?",(O0000OO0O00O00000 )).find ()#line:582
            if not O00OO0O00OOOOO000 :#line:583
                continue #line:584
            O000O000OO00OOO00 =O00OO0O00OOOOO000 ["sType"]#line:585
            if not O000O000OO00OOO00 :#line:586
                continue #line:587
            OO000O0OOOOOOO000 =O00OO0O00OOOOO000 ["name"]#line:588
            OOOOOO0000OO000O0 =O000OOO00O0OOO00O ["addtime"]#line:589
            O0OO0O00O000OO00O =O000OOO00O0OOO00O ["target"]#line:590
            if O000O000OO00OOO00 not in OOO000O00OO0O000O .keys ():#line:591
                OOO000O00OO0O000O [O000O000OO00OOO00 ]={}#line:592
                OOO000O00OO0O000O [O000O000OO00OOO00 ]["backup"]=[]#line:593
                OOO000O00OO0O000O [O000O000OO00OOO00 ]["no_backup"]=[]#line:594
            OOO000O00OO0O000O [O000O000OO00OOO00 ]["backup"].append ({"name":OO000O0OOOOOOO000 ,"target":O0OO0O00O000OO00O ,"status":OO00OOO0OOO0O0OOO ,"target":O0OO0O00O000OO00O ,"time":OOOOOO0000OO000O0 })#line:601
        O0OO0OO00O000O0O0 =""#line:603
        O0O000O0OOO0OOO0O =0 #line:604
        if O00OOOO0O0OOO0OOO ==0 :#line:605
            O0O000O0OOO0OOO0O =20 #line:606
        else :#line:607
            O0OO0OO00O000O0O0 ="有计划任务备份失败"#line:608
        if len (O0000OOO00OO00OOO )==0 :#line:610
            O0O000O0OOO0OOO0O +=10 #line:611
        else :#line:612
            if O0OO0OO00O000O0O0 :#line:613
                O0OO0OO00O000O0O0 +=";"#line:614
            O0OO0OO00O000O0O0 +="有数据库未及时备份"#line:615
        if len (OOOO00OOO0O000O0O )==0 :#line:617
            O0O000O0OOO0OOO0O +=10 #line:618
        else :#line:619
            if O0OO0OO00O000O0O0 :#line:620
                O0OO0OO00O000O0O0 +=";"#line:621
            O0OO0OO00O000O0O0 +="有网站未备份"#line:622
        OO00OOOOOOO0O0OO0 =0 #line:625
        O0O000O0OOOOOO0O0 =public .M ('logs').where ('addtime like "{}%" and type=?'.format (O0O0O00OO00OO0OOO ),('用户登录',)).select ()#line:626
        OOO0000O0OO00O00O =[]#line:627
        if O0O000O0OOOOOO0O0 and type (O0O000O0OOOOOO0O0 )==list :#line:628
            for OOOO00O0OO0O00OOO in O0O000O0OOOOOO0O0 :#line:629
                O0O00O00OO00O0O00 =OOOO00O0OO0O00OOO ["log"]#line:630
                if O0O00O00OO00O0O00 .find ("失败")>=0 or O0O00O00OO00O0O00 .find ("错误")>=0 :#line:631
                    OO00OOOOOOO0O0OO0 +=1 #line:632
                    OOO0000O0OO00O00O .append ({"time":time .mktime (time .strptime (OOOO00O0OO0O00OOO ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":OOOO00O0OO0O00OOO ["log"],"username":OOOO00O0OO0O00OOO ["username"],})#line:637
            OOO0000O0OO00O00O .sort (key =lambda O000O00OOOOOOOO0O :O000O00OOOOOOOO0O ["time"])#line:638
        O0O00OO0O0OO0OO0O =public .M ('logs').where ('type=?',('SSH安全',)).where ("addtime like '{}%'".format (O0O0O00OO00OO0OOO ),()).select ()#line:640
        O000O000OOOOO000O =[]#line:642
        OO00O0000OOOO0OOO =0 #line:643
        if O0O00OO0O0OO0OO0O :#line:644
            for OOOO00O0OO0O00OOO in O0O00OO0O0OO0OO0O :#line:645
                O0O00O00OO00O0O00 =OOOO00O0OO0O00OOO ["log"]#line:646
                if O0O00O00OO00O0O00 .find ("存在异常")>=0 :#line:647
                    OO00O0000OOOO0OOO +=1 #line:648
                    O000O000OOOOO000O .append ({"time":time .mktime (time .strptime (OOOO00O0OO0O00OOO ["addtime"],"%Y-%m-%d %H:%M:%S")),"desc":OOOO00O0OO0O00OOO ["log"],"username":OOOO00O0OO0O00OOO ["username"]})#line:653
            O000O000OOOOO000O .sort (key =lambda O000OOOO0000O00O0 :O000OOOO0000O00O0 ["time"])#line:654
        O0O0OO0OO000O000O =""#line:656
        O0000O0O0OOO0O0O0 =0 #line:657
        if OO00O0000OOOO0OOO ==0 :#line:658
            O0000O0O0OOO0O0O0 =10 #line:659
        else :#line:660
            O0O0OO0OO000O000O ="SSH有异常登录"#line:661
        if OO00OOOOOOO0O0OO0 ==0 :#line:663
            O0000O0O0OOO0O0O0 +=10 #line:664
        else :#line:665
            if OO00OOOOOOO0O0OO0 >10 :#line:666
                O0000O0O0OOO0O0O0 -=10 #line:667
            if O0O0OO0OO000O000O :#line:668
                O0O0OO0OO000O000O +=";"#line:669
            O0O0OO0OO000O000O +="面板登录有错误".format (OO00OOOOOOO0O0OO0 )#line:670
        O00O0O0OO000O0OOO ={"panel":{"ex":OO00OOOOOOO0O0OO0 ,"detail":OOO0000O0OO00O00O },"ssh":{"ex":OO00O0000OOOO0OOO ,"detail":O000O000OOOOO000O }}#line:680
        O0OOO00O0O00OOOO0 =OO0000O00O0OOO00O +O0OO000O00O0O0000 +OO0O0O000000O0O00 +OOOOO0OO00O00O0O0 +O0O000O0OOO0OOO0O +O0000O0O0OOO0O0O0 #line:682
        OOO00OO00000O0OO0 =[OOO0O0O0O0000OOO0 ,OOO00O0OOOOOO0OO0 ,OO0O00OOO0OOOO0O0 ,O00O0O0OOOOOOOOO0 ,O0OO0OO00O000O0O0 ,O0O0OO0OO000O000O ]#line:683
        O00000OOO00O0O000 =[]#line:684
        for OO0OO0O0OOOO0000O in OOO00OO00000O0OO0 :#line:685
            if OO0OO0O0OOOO0000O :#line:686
                if OO0OO0O0OOOO0000O .find (";")>=0 :#line:687
                    for O000O0OO00000OOO0 in OO0OO0O0OOOO0000O .split (";"):#line:688
                        O00000OOO00O0O000 .append (O000O0OO00000OOO0 )#line:689
                else :#line:690
                    O00000OOO00O0O000 .append (OO0OO0O0OOOO0000O )#line:691
        if not O00000OOO00O0O000 :#line:693
            O00000OOO00O0O000 .append ("服务器运行正常，请继续保持！")#line:694
        OO00O0OOOOO00000O =OOO00O00O000O0O00 .evaluate (O0OOO00O0O00OOOO0 )#line:698
        return {"data":{"cpu":O0OOOOO000O0OOOOO ,"ram":O0OOO0OOOOOO00O00 ,"disk":O00O000O000O00O00 ,"server":OO00000000O0000O0 ,"backup":OOO000O00OO0O000O ,"exception":O00O0O0OO000O0OOO ,},"evaluate":OO00O0OOOOO00000O ,"score":O0OOO00O0O00OOOO0 ,"date":O0O000OO0OOOOO00O ,"summary":O00000OOO00O0O000 ,"status":True }#line:715
    def evaluate (O0O0000O0000OO000 ,O0O0OOO00OO00O0OO ):#line:717
        O0OO0000OOO0000O0 =""#line:718
        if O0O0OOO00OO00O0OO >=100 :#line:719
            O0OO0000OOO0000O0 ="正常"#line:720
        elif O0O0OOO00OO00O0OO >=80 :#line:721
            O0OO0000OOO0000O0 ="良好"#line:722
        else :#line:723
            O0OO0000OOO0000O0 ="一般"#line:724
        return O0OO0000OOO0000O0 #line:725
    def get_daily_list (O00O00OO00OOO0OOO ,O0000O0O0O000O0O0 ):#line:727
        OO0O0OO0000OO0O00 =public .M ("system").dbfile ("system").table ("daily").where ("time_key>?",0 ).select ()#line:728
        O000O0OOOO0O0000O =[]#line:729
        for O0OO000000OOO0OOO in OO0O0OO0000OO0O00 :#line:730
            O0OO000000OOO0OOO ["evaluate"]=O00O00OO00OOO0OOO .evaluate (O0OO000000OOO0OOO ["evaluate"])#line:731
            O000O0OOOO0O0000O .append (O0OO000000OOO0OOO )#line:732
        return O000O0OOOO0O0000O 
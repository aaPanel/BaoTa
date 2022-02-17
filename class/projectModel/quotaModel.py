import os ,public ,psutil ,json ,time #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __OOOO00OO000OO0OOO ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __OOO000O0OO0O00000 ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __OO0O0O0O00000O000 =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (OOOOOO0000000OO0O )->None :#line:21
        O0OOOOO00O0O00OO0 ='/usr/sbin/xfs_quota'#line:22
        if not os .path .exists (O0OOOOO00O0O00OO0 ):#line:23
            if os .path .exists ('/usr/bin/apt-get'):#line:24
                public .ExecShell ('apt-get install xfsprogs -y')#line:25
            else :#line:26
                public .ExecShell ('yum install xfsprogs -y')#line:27
    def __O0000O00O000OO00O (OOO0O00O000OO00O0 ,args =None ):#line:30
        ""#line:35
        O0000OO00OO00OO00 =[]#line:36
        for O00O0O0OOO00000OO in psutil .disk_partitions ():#line:37
            if O00O0O0OOO00000OO .fstype =='xfs':#line:38
                O0000OO00OO00OO00 .append ((O00O0O0OOO00000OO .mountpoint ,O00O0O0OOO00000OO .device ,psutil .disk_usage (O00O0O0OOO00000OO .mountpoint ).free ,O00O0O0OOO00000OO .opts .split (',')))#line:46
        return O0000OO00OO00OO00 #line:48
    def __O0OO000000O0O0O0O (OO0OOO0OOOOO0O00O ,args =None ):#line:50
        ""#line:56
        return OO0OOO0OOOOO0O00O .__OO00O00O0O0000000 (args .path )#line:57
    def __O000O0OOO00000000 (OOO0OOOOO00000OO0 ,O00O00O00OO0OOO00 ):#line:59
        ""#line:65
        OOOOOO000O000O0O0 =OOO0OOOOO00000OO0 .__O0000O00O000OO00O ()#line:66
        for OOO00OO0OO00OO0O0 in OOOOOO000O000O0O0 :#line:67
            if O00O00O00OO0OOO00 .find (OOO00OO0OO00OO0O0 [0 ]+'/')==0 :#line:68
                if not 'prjquota'in OOO00OO0OO00OO0O0 [3 ]:#line:69
                    return OOO00OO0OO00OO0O0 #line:70
                return OOO00OO0OO00OO0O0 [1 ]#line:71
        return ''#line:72
    def __OO00O00O0O0000000 (OO00O0OO00OOOOO0O ,OOO00OOO0OOOOO0O0 ):#line:76
        ""#line:82
        if not os .path .exists (OOO00OOO0OOOOO0O0 ):return -1 #line:83
        if not os .path .isdir (OOO00OOO0OOOOO0O0 ):return -2 #line:84
        OO00OO00OOOOOO0O0 =OO00O0OO00OOOOO0O .__O0000O00O000OO00O ()#line:85
        for OO0OOO0OOOO0O0O00 in OO00OO00OOOOOO0O0 :#line:86
            if OOO00OOO0OOOOO0O0 .find (OO0OOO0OOOO0O0O00 [0 ]+'/')==0 :#line:87
                return OO0OOO0OOOO0O0O00 [2 ]/1024 /1024 #line:88
        return -3 #line:89
    def get_quota_path_list (O0OO0O000O0OOO0OO ,args =None ,get_path =None ):#line:92
        ""#line:98
        if not os .path .exists (O0OO0O000O0OOO0OO .__OOOO00OO000OO0OOO ):#line:99
            public .writeFile (O0OO0O000O0OOO0OO .__OOOO00OO000OO0OOO ,'[]')#line:100
        OOOO00O00OOOO00O0 =json .loads (public .readFile (O0OO0O000O0OOO0OO .__OOOO00OO000OO0OOO ))#line:102
        O0000O0O0000OO00O =[]#line:104
        for O0OOOOO0O00000O0O in OOOO00O00OOOO00O0 :#line:105
            if not os .path .exists (O0OOOOO0O00000O0O ['path'])or not os .path .isdir (O0OOOOO0O00000O0O ['path'])or os .path .islink (O0OOOOO0O00000O0O ['path']):continue #line:106
            if get_path :#line:107
                if O0OOOOO0O00000O0O ['path']==get_path :#line:108
                    O000O00O0OOO0OOOO =psutil .disk_usage (O0OOOOO0O00000O0O ['path'])#line:109
                    O0OOOOO0O00000O0O ['used']=O000O00O0OOO0OOOO .used #line:110
                    O0OOOOO0O00000O0O ['free']=O000O00O0OOO0OOOO .free #line:111
                    return O0OOOOO0O00000O0O #line:112
                else :#line:113
                    continue #line:114
            O000O00O0OOO0OOOO =psutil .disk_usage (O0OOOOO0O00000O0O ['path'])#line:115
            O0OOOOO0O00000O0O ['used']=O000O00O0OOO0OOOO .used #line:116
            O0OOOOO0O00000O0O ['free']=O000O00O0OOO0OOOO .free #line:117
            O0000O0O0000OO00O .append (O0OOOOO0O00000O0O )#line:118
        if get_path :#line:120
            return {'size':0 ,'used':0 ,'free':0 }#line:121
        if len (O0000O0O0000OO00O )!=len (OOOO00O00OOOO00O0 ):#line:123
            public .writeFile (O0OO0O000O0OOO0OO .__OOOO00OO000OO0OOO ,json .dumps (O0000O0O0000OO00O ))#line:124
        return OOOO00O00OOOO00O0 #line:126
    def get_quota_mysql_list (OOO0OOO0OO0OOO000 ,args =None ,get_name =None ):#line:129
        ""#line:135
        if not os .path .exists (OOO0OOO0OO0OOO000 .__OOO000O0OO0O00000 ):#line:136
            public .writeFile (OOO0OOO0OO0OOO000 .__OOO000O0OO0O00000 ,'[]')#line:137
        O0OO0000OO00O00OO =json .loads (public .readFile (OOO0OOO0OO0OOO000 .__OOO000O0OO0O00000 ))#line:139
        O0OO0OOO00OO000O0 =[]#line:140
        O000O0OO0OO0O0O00 =public .M ('databases')#line:141
        for OO00O0OO00O00O0O0 in O0OO0000OO00O00OO :#line:142
            if get_name :#line:143
                if OO00O0OO00O00O0O0 ['db_name']==get_name :#line:144
                    OO00O0OO00O00O0O0 ['used']=OO00O0OO00O00O0O0 ['used']=int (public .get_database_size_by_name (OO00O0OO00O00O0O0 ['db_name']))#line:145
                    _O000OOOOOO0OOOOOO =OO00O0OO00O00O0O0 ['size']*1024 *1024 #line:146
                    if (OO00O0OO00O00O0O0 ['used']>_O000OOOOOO0OOOOOO and OO00O0OO00O00O0O0 ['insert_accept'])or (OO00O0OO00O00O0O0 ['used']<_O000OOOOOO0OOOOOO and not OO00O0OO00O00O0O0 ['insert_accept']):#line:147
                        OOO0OOO0OO0OOO000 .mysql_quota_check ()#line:148
                    return OO00O0OO00O00O0O0 #line:149
            else :#line:150
                if O000O0OO0OO0O0O00 .where ('name=?',OO00O0OO00O00O0O0 ['db_name']).count ():#line:151
                    if args :OO00O0OO00O00O0O0 ['used']=int (public .get_database_size_by_name (OO00O0OO00O00O0O0 ['db_name']))#line:152
                    O0OO0OOO00OO000O0 .append (OO00O0OO00O00O0O0 )#line:153
        O000O0OO0OO0O0O00 .close ()#line:154
        if get_name :#line:155
            return {'size':0 ,'used':0 }#line:156
        if len (O0OO0OOO00OO000O0 )!=len (O0OO0000OO00O00OO ):#line:157
            public .writeFile (OOO0OOO0OO0OOO000 .__OOO000O0OO0O00000 ,json .dumps (O0OO0OOO00OO000O0 ))#line:158
        return O0OO0OOO00OO000O0 #line:159
    def __OOOO0OO00O000O0O0 (O000OOOOOO0OOO00O ,O0O0O0OOO0OOO0OOO ,OO00OO00O00O00000 ,O00O0OOOOOOOOOOOO ,O0OOOOOOOO00000OO ):#line:161
        ""#line:170
        OO00O0OOOOOOOOO0O =O0O0O0OOO0OOO0OOO .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O00O0OOOOOOOOOOOO ,OO00OO00O00O00000 ,O0OOOOOOOO00000OO ))#line:171
        if OO00O0OOOOOOOOO0O :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OO00O0OOOOOOOOO0O ))#line:172
        OO00O0OOOOOOOOO0O =O0O0O0OOO0OOO0OOO .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (O00O0OOOOOOOOOOOO ,OO00OO00O00O00000 ,O0OOOOOOOO00000OO ))#line:173
        if OO00O0OOOOOOOOO0O :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OO00O0OOOOOOOOO0O ))#line:174
        O0O0O0OOO0OOO0OOO .execute ("FLUSH PRIVILEGES;")#line:175
        return True #line:176
    def __O0OOOO0OO0OOO0OO0 (O00OO0OO0O0O0O000 ,OOOO0OOO0000000OO ,OO0O0O00O0OO0O000 ,O0OO0OOOO0O0OOO0O ,O0O0O00O000OO00OO ):#line:178
        ""#line:187
        OO00O0OOO00OO0000 =OOOO0OOO0000000OO .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0OO0OOOO0O0OOO0O ,OO0O0O00O0OO0O000 ,O0O0O00O000OO00OO ))#line:188
        if OO00O0OOO00OO0000 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OO00O0OOO00OO0000 ))#line:189
        OO00O0OOO00OO0000 =OOOO0OOO0000000OO .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (O0OO0OOOO0O0OOO0O ,OO0O0O00O0OO0O000 ,O0O0O00O000OO00OO ))#line:190
        if OO00O0OOO00OO0000 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OO00O0OOO00OO0000 ))#line:191
        OOOO0OOO0000000OO .execute ("FLUSH PRIVILEGES;")#line:192
        return True #line:193
    def mysql_quota_service (O00O0OOO00OO00OOO ):#line:196
        ""#line:201
        while 1 :#line:202
            time .sleep (600 )#line:203
            O00O0OOO00OO00OOO .mysql_quota_check ()#line:204
    def __OOOO0O0OOO00O0000 (OOO0OOOO0OO0000O0 ,O0000OO000O0O000O ):#line:207
        try :#line:208
            if type (O0000OO000O0O000O )!=list and type (O0000OO000O0O000O )!=str :O0000OO000O0O000O =list (O0000OO000O0O000O )#line:209
            return O0000OO000O0O000O #line:210
        except :return []#line:211
    def mysql_quota_check (O0O0OO0000OO0O00O ):#line:213
        ""#line:218
        if not O0O0OO0000OO0O00O .__O0O0OO000OO0OO00O ():return public .returnMsg (False ,O0O0OO0000OO0O00O .__OO0O0O0O00000O000 )#line:219
        O0O0OO0OO00O0OOOO =O0O0OO0000OO0O00O .get_quota_mysql_list ()#line:220
        for OOOO0OO00O00OOO0O in O0O0OO0OO00O0OOOO :#line:221
            try :#line:222
                OO00000OOO000O000 =public .get_database_size_by_name (OOOO0OO00O00OOO0O ['db_name'])/1024 /1024 #line:223
                OO0000O0OO0OOO0OO =public .M ('databases').where ('name=?',(OOOO0OO00O00OOO0O ['db_name'],)).getField ('username')#line:224
                O0OO0OOOOOO00O00O =public .get_mysql_obj (OOOO0OO00O00OOO0O ['db_name'])#line:225
                O0O0000000OO00OO0 =O0O0OO0000OO0O00O .__OOOO0O0OOO00O0000 (O0OO0OOOOOO00O00O .query ("select Host from mysql.user where User='"+OO0000O0OO0OOO0OO +"'"))#line:226
                if OO00000OOO000O000 <OOOO0OO00O00OOO0O ['size']:#line:227
                    if not OOOO0OO00O00OOO0O ['insert_accept']:#line:228
                        for OO0000O000O0O00O0 in O0O0000000OO00OO0 :#line:229
                            O0O0OO0000OO0O00O .__O0OOOO0OO0OOO0OO0 (O0OO0OOOOOO00O00O ,OO0000O0OO0OOO0OO ,OOOO0OO00O00OOO0O ['db_name'],OO0000O000O0O00O0 [0 ])#line:230
                        OOOO0OO00O00OOO0O ['insert_accept']=True #line:231
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (OOOO0OO00O00OOO0O ['db_name'],OOOO0OO00O00OOO0O ['size']))#line:232
                    if hasattr (O0OO0OOOOOO00O00O ,'close'):O0OO0OOOOOO00O00O .close ()#line:233
                    continue #line:234
                for OO0000O000O0O00O0 in O0O0000000OO00OO0 :#line:236
                    O0O0OO0000OO0O00O .__OOOO0OO00O000O0O0 (O0OO0OOOOOO00O00O ,OO0000O0OO0OOO0OO ,OOOO0OO00O00OOO0O ['db_name'],OO0000O000O0O00O0 [0 ])#line:237
                OOOO0OO00O00OOO0O ['insert_accept']=False #line:238
                public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (OOOO0OO00O00OOO0O ['db_name'],OOOO0OO00O00OOO0O ['size']))#line:239
                if hasattr (O0OO0OOOOOO00O00O ,'close'):O0OO0OOOOOO00O00O .close ()#line:240
            except :#line:241
                public .print_log (public .get_error_info ())#line:242
        public .writeFile (O0O0OO0000OO0O00O .__OOO000O0OO0O00000 ,json .dumps (O0O0OO0OO00O0OOOO ))#line:243
    def __O0000000OOO0OO0OO (OOOOO0O00O0O0000O ,O0OO0O0000OO0OOO0 ):#line:245
        ""#line:254
        if not OOOOO0O00O0O0000O .__O0O0OO000OO0OO00O ():return public .returnMsg (False ,OOOOO0O00O0O0000O .__OO0O0O0O00000O000 )#line:255
        if not os .path .exists (OOOOO0O00O0O0000O .__OOO000O0OO0O00000 ):#line:256
            public .writeFile (OOOOO0O00O0O0000O .__OOO000O0OO0O00000 ,'[]')#line:257
        O00OOO0O000000O0O =int (O0OO0O0000OO0OOO0 ['size'])#line:258
        OO00O0000O0O00O00 =O0OO0O0000OO0OOO0 .db_name .strip ()#line:259
        O0O0OOO0OO00000O0 =json .loads (public .readFile (OOOOO0O00O0O0000O .__OOO000O0OO0O00000 ))#line:260
        for O0O000OO0OO0000O0 in O0O0OOO0OO00000O0 :#line:261
            if O0O000OO0OO0000O0 ['db_name']==OO00O0000O0O00O00 :#line:262
                return public .returnMsg (False ,'数据库配额已存在')#line:263
        O0O0OOO0OO00000O0 .append ({'db_name':OO00O0000O0O00O00 ,'size':O00OOO0O000000O0O ,'insert_accept':True })#line:269
        public .writeFile (OOOOO0O00O0O0000O .__OOO000O0OO0O00000 ,json .dumps (O0O0OOO0OO00000O0 ))#line:270
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =OO00O0000O0O00O00 ,size =O00OOO0O000000O0O ))#line:271
        OOOOO0O00O0O0000O .mysql_quota_check ()#line:272
        return public .returnMsg (True ,'添加成功')#line:273
    def __O0O0OO000OO0OO00O (OO0O0O0O00O00000O ):#line:276
        from pluginAuth import Plugin #line:277
        OOO0O00O0O000000O =Plugin (False )#line:278
        OOO0OOOO0OO0O00O0 =OOO0O00O0O000000O .get_plugin_list ()#line:279
        return int (OOO0OOOO0OO0O00O0 ['ltd'])>time .time ()#line:280
    def modify_mysql_quota (OO00000OOOO00O0OO ,OO0OOO000OOOOO00O ):#line:282
        ""#line:291
        if not OO00000OOOO00O0OO .__O0O0OO000OO0OO00O ():return public .returnMsg (False ,OO00000OOOO00O0OO .__OO0O0O0O00000O000 )#line:292
        if not os .path .exists (OO00000OOOO00O0OO .__OOO000O0OO0O00000 ):#line:293
            public .writeFile (OO00000OOOO00O0OO .__OOO000O0OO0O00000 ,'[]')#line:294
        OO0OO0000OOOO00O0 =int (OO0OOO000OOOOO00O ['size'])#line:295
        OO000000O000OO00O =OO0OOO000OOOOO00O .db_name .strip ()#line:296
        O00OO0O000O00OO00 =json .loads (public .readFile (OO00000OOOO00O0OO .__OOO000O0OO0O00000 ))#line:297
        OOO00OOO0O0OO00O0 =False #line:298
        for O000OOO000O00O0O0 in O00OO0O000O00OO00 :#line:299
            if O000OOO000O00O0O0 ['db_name']==OO000000O000OO00O :#line:300
                O000OOO000O00O0O0 ['size']=OO0OO0000OOOO00O0 #line:301
                OOO00OOO0O0OO00O0 =True #line:302
                break #line:303
        if OOO00OOO0O0OO00O0 :#line:305
            public .writeFile (OO00000OOOO00O0OO .__OOO000O0OO0O00000 ,json .dumps (O00OO0O000O00OO00 ))#line:306
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =OO000000O000OO00O ,size =OO0OO0000OOOO00O0 ))#line:307
            OO00000OOOO00O0OO .mysql_quota_check ()#line:308
            return public .returnMsg (True ,'修改成功')#line:309
        return OO00000OOOO00O0OO .__O0000000OOO0OO0OO (OO0OOO000OOOOO00O )#line:310
    def __O0000O00OOOOOO000 (OOOO00000OOO0OO00 ,OOO0OO0O00O00OO0O ):#line:314
        ""#line:320
        OO00O000OOOOOOOO0 =[]#line:321
        OOOOO0000O0OO0O00 =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =OOO0OO0O00O00OO0O ))[0 ]#line:322
        if not OOOOO0000O0OO0O00 :return OO00O000OOOOOOOO0 #line:323
        for O000O0O0O0OOO0OOO in OOOOO0000O0OO0O00 .split ('\n'):#line:324
            if O000O0O0O0OOO0OOO :OO00O000OOOOOOOO0 .append (int (O000O0O0O0OOO0OOO .split ('#')[-1 ]))#line:325
        return OO00O000OOOOOOOO0 #line:326
    def __O00O000OO0O0O0O00 (O0OOOOOOO0OOO00OO ,OOOOO0000O0OOO0OO ,O0OOOO00O0O00OOOO ):#line:328
        ""#line:334
        OO00OO00OO0OOO000 =1001 #line:335
        if not OOOOO0000O0OOO0OO :return OO00OO00OO0OOO000 #line:336
        OO00OO00OO0OOO000 =OOOOO0000O0OOO0OO [-1 ]['id']+1 #line:337
        OO000O0O0OO00O0O0 =sorted (O0OOOOOOO0OOO00OO .__O00O000OO0O0O0O00 (O0OOOO00O0O00OOOO ))#line:338
        if OO000O0O0OO00O0O0 :#line:339
            if OO000O0O0OO00O0O0 [-1 ]>OO00OO00OO0OOO000 :#line:340
                OO00OO00OO0OOO000 =OO000O0O0OO00O0O0 [-1 ]+1 #line:341
        return OO00OO00OO0OOO000 #line:342
    def __O000OOOO0O00O0000 (OO00OO0O00000O0O0 ,OOO0OO0O0O00O0OO0 ):#line:345
        ""#line:354
        if not OO00OO0O00000O0O0 .__O0O0OO000OO0OO00O ():return public .returnMsg (False ,OO00OO0O00000O0O0 .__OO0O0O0O00000O000 )#line:355
        OOOOO0O0OO00O00O0 =OOO0OO0O0O00O0OO0 .path .strip ()#line:356
        O0OO0OOO00O0O0O0O =int (OOO0OO0O0O00O0OO0 .size )#line:357
        if not os .path .exists (OOOOO0O0OO00O00O0 ):return public .returnMsg (False ,'指定目录不存在')#line:358
        if os .path .isfile (OOOOO0O0OO00O00O0 ):return public .returnMsg (False ,'指定目录不是目录!')#line:359
        if os .path .islink (OOOOO0O0OO00O00O0 ):return public .returnMsg (False ,'指定目录是软链接!')#line:360
        O0OO0O0O0OO00OO0O =OO00OO0O00000O0O0 .get_quota_path_list ()#line:361
        for O0O00O0OOO0000OO0 in O0OO0O0O0OO00OO0O :#line:362
            if O0O00O0OOO0000OO0 ['path']==OOOOO0O0OO00O00O0 :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:363
        O0OO0OO0OO0OOOOOO =OO00OO0O00000O0O0 .__OO00O00O0O0000000 (OOOOO0O0OO00O00O0 )#line:365
        if O0OO0OO0OO0OOOOOO ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:366
        if O0OO0OO0OO0OOOOOO ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:367
        if O0OO0OO0OO0OOOOOO ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:368
        if O0OO0OOO00O0O0O0O >O0OO0OO0OO0OOOOOO :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:370
        O00O0OO0O000000O0 =OO00OO0O00000O0O0 .__O000O0OOO00000000 (OOOOO0O0OO00O00O0 )#line:372
        if not O00O0OO0O000000O0 :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:373
        if isinstance (O00O0OO0O000000O0 ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =O00O0OO0O000000O0 [1 ],path =O00O0OO0O000000O0 [0 ]))#line:375
        O0OO00OO0OOO0000O =OO00OO0O00000O0O0 .__O00O000OO0O0O0O00 (O0OO0O0O0OO00OO0O ,O00O0OO0O000000O0 )#line:376
        O0O00OO000OOO0O0O =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OOOOO0O0OO00O00O0 ,quota_id =O0OO00OO0OOO0000O ))#line:378
        if O0O00OO000OOO0O0O [1 ]:return public .returnMsg (False ,O0O00OO000OOO0O0O [1 ])#line:379
        O0O00OO000OOO0O0O =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O0OO00OO0OOO0000O ,size =O0OO0OOO00O0O0O0O ,mountpoint =O00O0OO0O000000O0 ))#line:380
        if O0O00OO000OOO0O0O [1 ]:return public .returnMsg (False ,O0O00OO000OOO0O0O [1 ])#line:381
        O0OO0O0O0OO00OO0O .append ({'path':OOO0OO0O0O00O0OO0 .path ,'size':O0OO0OOO00O0O0O0O ,'id':O0OO00OO0OOO0000O })#line:386
        public .writeFile (OO00OO0O00000O0O0 .__OOOO00OO000OO0OOO ,json .dumps (O0OO0O0O0OO00OO0O ))#line:387
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =OOOOO0O0OO00O00O0 ,size =O0OO0OOO00O0O0O0O ))#line:388
        return public .returnMsg (True ,'添加成功')#line:389
    def modify_path_quota (O00O00000OOO00O00 ,O000O0000O0OO0O00 ):#line:392
        ""#line:401
        if not O00O00000OOO00O00 .__O0O0OO000OO0OO00O ():return public .returnMsg (False ,O00O00000OOO00O00 .__OO0O0O0O00000O000 )#line:402
        OOO0000OOO0O0O00O =O000O0000O0OO0O00 .path .strip ()#line:403
        OOO0O0O0O0OO00000 =int (O000O0000O0OO0O00 .size )#line:404
        if not os .path .exists (OOO0000OOO0O0O00O ):return public .returnMsg (False ,'指定目录不存在')#line:405
        if os .path .isfile (OOO0000OOO0O0O00O ):return public .returnMsg (False ,'指定目录不是目录!')#line:406
        if os .path .islink (OOO0000OOO0O0O00O ):return public .returnMsg (False ,'指定目录是软链接!')#line:407
        O000O0OO0OOOO00OO =O00O00000OOO00O00 .get_quota_path_list ()#line:408
        O00OO0O000O0O00OO =0 #line:409
        for O0000O000O000O0OO in O000O0OO0OOOO00OO :#line:410
            if O0000O000O000O0OO ['path']==OOO0000OOO0O0O00O :#line:411
                O00OO0O000O0O00OO =O0000O000O000O0OO ['id']#line:412
                break #line:413
        if not O00OO0O000O0O00OO :return O00O00000OOO00O00 .__O000OOOO0O00O0000 (O000O0000O0OO0O00 )#line:414
        O0O0O0O000OO00O0O =O00O00000OOO00O00 .__OO00O00O0O0000000 (OOO0000OOO0O0O00O )#line:416
        if O0O0O0O000OO00O0O ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:417
        if O0O0O0O000OO00O0O ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:418
        if O0O0O0O000OO00O0O ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:419
        if OOO0O0O0O0OO00000 >O0O0O0O000OO00O0O :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:420
        O0OOOOO00O0O000OO =O00O00000OOO00O00 .__O000O0OOO00000000 (OOO0000OOO0O0O00O )#line:422
        if not O0OOOOO00O0O000OO :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:423
        if isinstance (O0OOOOO00O0O000OO ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =O0OOOOO00O0O000OO [1 ],path =O0OOOOO00O0O000OO [0 ]))#line:425
        OOO000OOOOOOO00OO =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OOO0000OOO0O0O00O ,quota_id =O00OO0O000O0O00OO ))#line:426
        if OOO000OOOOOOO00OO [1 ]:return public .returnMsg (False ,OOO000OOOOOOO00OO [1 ])#line:427
        OOO000OOOOOOO00OO =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O00OO0O000O0O00OO ,size =OOO0O0O0O0OO00000 ,mountpoint =O0OOOOO00O0O000OO ))#line:428
        if OOO000OOOOOOO00OO [1 ]:return public .returnMsg (False ,OOO000OOOOOOO00OO [1 ])#line:429
        for O0000O000O000O0OO in O000O0OO0OOOO00OO :#line:430
            if O0000O000O000O0OO ['path']==OOO0000OOO0O0O00O :#line:431
                O0000O000O000O0OO ['size']=OOO0O0O0O0OO00000 #line:432
                break #line:433
        public .writeFile (O00O00000OOO00O00 .__OOOO00OO000OO0OOO ,json .dumps (O000O0OO0OOOO00OO ))#line:434
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =OOO0000OOO0O0O00O ,size =OOO0O0O0O0OO00000 ))#line:435
        return public .returnMsg (True ,'修改成功')#line:436

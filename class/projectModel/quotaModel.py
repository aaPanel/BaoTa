import os ,public ,psutil ,json ,time ,re #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __OO0O0OO0OOOOOO000 ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __O000O0OOOOOO000O0 ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __OO0000000000OO0O0 =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (OO0O0OO000OO000O0 )->None :#line:21
        O00OO0O0O000000O0 ='/usr/sbin/xfs_quota'#line:22
        if not os .path .exists (O00OO0O0O000000O0 ):#line:23
            if os .path .exists ('/usr/bin/apt-get'):#line:24
                public .ExecShell ('apt-get install xfsprogs -y')#line:25
            else :#line:26
                public .ExecShell ('yum install xfsprogs -y')#line:27
    def __OOO0OO0O0O0O00000 (O000O000O00O00O00 ,args =None ):#line:30
        ""#line:35
        OO0000OO00OO0O0O0 =[]#line:36
        for O0O0OOOOO0O0OO0O0 in psutil .disk_partitions ():#line:37
            if O0O0OOOOO0O0OO0O0 .fstype =='xfs':#line:38
                OO0000OO00OO0O0O0 .append ((O0O0OOOOO0O0OO0O0 .mountpoint ,O0O0OOOOO0O0OO0O0 .device ,psutil .disk_usage (O0O0OOOOO0O0OO0O0 .mountpoint ).free ,O0O0OOOOO0O0OO0O0 .opts .split (',')))#line:46
        return OO0000OO00OO0O0O0 #line:48
    def __O00O0O00O00O0O000 (O000OOO00O0OOOOO0 ,args =None ):#line:50
        ""#line:56
        return O000OOO00O0OOOOO0 .__O0OO0O0OOOO00O0OO (args .path )#line:57
    def __OOO0000OO0OOO00OO (O0OOOO00OOOO000O0 ,OO000O0OOO0O0O00O ):#line:59
        ""#line:65
        OO00O0OO0OOOOO00O =O0OOOO00OOOO000O0 .__OOO0OO0O0O0O00000 ()#line:66
        for OOOO00O00O00O0O00 in OO00O0OO0OOOOO00O :#line:67
            if OO000O0OOO0O0O00O .find (OOOO00O00O00O0O00 [0 ]+'/')==0 :#line:68
                if not 'prjquota'in OOOO00O00O00O0O00 [3 ]:#line:69
                    return OOOO00O00O00O0O00 #line:70
                return OOOO00O00O00O0O00 [1 ]#line:71
        return ''#line:72
    def __O0OO0O0OOOO00O0OO (O0OO0OO00OOOO0O00 ,O00O000OOOO00000O ):#line:76
        ""#line:82
        if not os .path .exists (O00O000OOOO00000O ):return -1 #line:83
        if not os .path .isdir (O00O000OOOO00000O ):return -2 #line:84
        O000O0O000OO0O000 =O0OO0OO00OOOO0O00 .__OOO0OO0O0O0O00000 ()#line:85
        for O00O0O0OO0OOO0000 in O000O0O000OO0O000 :#line:86
            if O00O000OOOO00000O .find (O00O0O0OO0OOO0000 [0 ]+'/')==0 :#line:87
                return O00O0O0OO0OOO0000 [2 ]/1024 /1024 #line:88
        return -3 #line:89
    def get_quota_path_list (O0OOOOOO00O0O0O00 ,args =None ,get_path =None ):#line:92
        ""#line:98
        if not os .path .exists (O0OOOOOO00O0O0O00 .__OO0O0OO0OOOOOO000 ):#line:99
            public .writeFile (O0OOOOOO00O0O0O00 .__OO0O0OO0OOOOOO000 ,'[]')#line:100
        OOO000OOO0O00O00O =json .loads (public .readFile (O0OOOOOO00O0O0O00 .__OO0O0OO0OOOOOO000 ))#line:102
        O0OO0OO0O0OOO00O0 =[]#line:104
        for O00OO000OOO000OOO in OOO000OOO0O00O00O :#line:105
            if not os .path .exists (O00OO000OOO000OOO ['path'])or not os .path .isdir (O00OO000OOO000OOO ['path'])or os .path .islink (O00OO000OOO000OOO ['path']):continue #line:106
            if get_path :#line:107
                if O00OO000OOO000OOO ['path']==get_path :#line:108
                    OO00O0O0OOOO0000O =psutil .disk_usage (O00OO000OOO000OOO ['path'])#line:109
                    O00OO000OOO000OOO ['used']=OO00O0O0OOOO0000O .used #line:110
                    O00OO000OOO000OOO ['free']=OO00O0O0OOOO0000O .free #line:111
                    return O00OO000OOO000OOO #line:112
                else :#line:113
                    continue #line:114
            OO00O0O0OOOO0000O =psutil .disk_usage (O00OO000OOO000OOO ['path'])#line:115
            O00OO000OOO000OOO ['used']=OO00O0O0OOOO0000O .used #line:116
            O00OO000OOO000OOO ['free']=OO00O0O0OOOO0000O .free #line:117
            O0OO0OO0O0OOO00O0 .append (O00OO000OOO000OOO )#line:118
        if get_path :#line:120
            return {'size':0 ,'used':0 ,'free':0 }#line:121
        if len (O0OO0OO0O0OOO00O0 )!=len (OOO000OOO0O00O00O ):#line:123
            public .writeFile (O0OOOOOO00O0O0O00 .__OO0O0OO0OOOOOO000 ,json .dumps (O0OO0OO0O0OOO00O0 ))#line:124
        return OOO000OOO0O00O00O #line:126
    def get_quota_mysql_list (O00OO00O0OO00O0O0 ,args =None ,get_name =None ):#line:129
        ""#line:135
        if not os .path .exists (O00OO00O0OO00O0O0 .__O000O0OOOOOO000O0 ):#line:136
            public .writeFile (O00OO00O0OO00O0O0 .__O000O0OOOOOO000O0 ,'[]')#line:137
        OOOOOO0OO0OOOO0O0 =json .loads (public .readFile (O00OO00O0OO00O0O0 .__O000O0OOOOOO000O0 ))#line:139
        O0OO0O00000O00O00 =[]#line:140
        OO000O0OOOOOOOO00 =public .M ('databases')#line:141
        for OO0OO0OO00O0OOO0O in OOOOOO0OO0OOOO0O0 :#line:142
            if get_name :#line:143
                if OO0OO0OO00O0OOO0O ['db_name']==get_name :#line:144
                    OO0OO0OO00O0OOO0O ['used']=OO0OO0OO00O0OOO0O ['used']=int (public .get_database_size_by_name (OO0OO0OO00O0OOO0O ['db_name']))#line:145
                    _OO00O00O0O0000OOO =OO0OO0OO00O0OOO0O ['size']*1024 *1024 #line:146
                    if (OO0OO0OO00O0OOO0O ['used']>_OO00O00O0O0000OOO and OO0OO0OO00O0OOO0O ['insert_accept'])or (OO0OO0OO00O0OOO0O ['used']<_OO00O00O0O0000OOO and not OO0OO0OO00O0OOO0O ['insert_accept']):#line:147
                        O00OO00O0OO00O0O0 .mysql_quota_check ()#line:148
                    return OO0OO0OO00O0OOO0O #line:149
            else :#line:150
                if OO000O0OOOOOOOO00 .where ('name=?',OO0OO0OO00O0OOO0O ['db_name']).count ():#line:151
                    if args :OO0OO0OO00O0OOO0O ['used']=int (public .get_database_size_by_name (OO0OO0OO00O0OOO0O ['db_name']))#line:152
                    O0OO0O00000O00O00 .append (OO0OO0OO00O0OOO0O )#line:153
        OO000O0OOOOOOOO00 .close ()#line:154
        if get_name :#line:155
            return {'size':0 ,'used':0 }#line:156
        if len (O0OO0O00000O00O00 )!=len (OOOOOO0OO0OOOO0O0 ):#line:157
            public .writeFile (O00OO00O0OO00O0O0 .__O000O0OOOOOO000O0 ,json .dumps (O0OO0O00000O00O00 ))#line:158
        return O0OO0O00000O00O00 #line:159
    def __O00O0O0O00OOO00OO (OOOOOOO0O0OOOOOOO ,OO0OO0OO0O00O000O ,O0O0O000000000OO0 ,OOO0OOOOO000000OO ,O000O0O0O0OOO0OOO ):#line:161
        ""#line:170
        OO00000O0000000OO =OO0OO0OO0O00O000O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (OOO0OOOOO000000OO ,O0O0O000000000OO0 ,O000O0O0O0OOO0OOO ))#line:171
        if OO00000O0000000OO :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OO00000O0000000OO ))#line:172
        OO00000O0000000OO =OO0OO0OO0O00O000O .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (OOO0OOOOO000000OO ,O0O0O000000000OO0 ,O000O0O0O0OOO0OOO ))#line:173
        if OO00000O0000000OO :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OO00000O0000000OO ))#line:174
        OO0OO0OO0O00O000O .execute ("FLUSH PRIVILEGES;")#line:175
        return True #line:176
    def __O00OOO0O000O0OOO0 (O00O00OOO00O00OOO ,O0O0OO0O000OOO00O ,OOOO0O000O00OO0OO ,OO0OO0000OO000O00 ,OO0OO00OO0OOO0OO0 ):#line:178
        ""#line:187
        OOO0OO0000OO0O0OO =O0O0OO0O000OOO00O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (OO0OO0000OO000O00 ,OOOO0O000O00OO0OO ,OO0OO00OO0OOO0OO0 ))#line:188
        if OOO0OO0000OO0O0OO :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OOO0OO0000OO0O0OO ))#line:189
        OOO0OO0000OO0O0OO =O0O0OO0O000OOO00O .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (OO0OO0000OO000O00 ,OOOO0O000O00OO0OO ,OO0OO00OO0OOO0OO0 ))#line:190
        if OOO0OO0000OO0O0OO :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OOO0OO0000OO0O0OO ))#line:191
        O0O0OO0O000OOO00O .execute ("FLUSH PRIVILEGES;")#line:192
        return True #line:193
    def mysql_quota_service (O00O0OO0O0000O0OO ):#line:196
        ""#line:201
        while 1 :#line:202
            time .sleep (600 )#line:203
            O00O0OO0O0000O0OO .mysql_quota_check ()#line:204
    def __O0OOOOO0O0000O00O (O00OOOOO00OO0000O ,OO00OO0000OO000O0 ):#line:207
        try :#line:208
            if type (OO00OO0000OO000O0 )!=list and type (OO00OO0000OO000O0 )!=str :OO00OO0000OO000O0 =list (OO00OO0000OO000O0 )#line:209
            return OO00OO0000OO000O0 #line:210
        except :return []#line:211
    def mysql_quota_check (O0O00OOOO0OOOOO0O ):#line:213
        ""#line:218
        if not O0O00OOOO0OOOOO0O .__O00OOOO0O0OO00O00 ():return public .returnMsg (False ,O0O00OOOO0OOOOO0O .__OO0000000000OO0O0 )#line:219
        O0000O000O00000O0 =O0O00OOOO0OOOOO0O .get_quota_mysql_list ()#line:220
        for O00OOOOOOOO0O0000 in O0000O000O00000O0 :#line:221
            try :#line:222
                OOO0000OO0OOO00OO =public .get_database_size_by_name (O00OOOOOOOO0O0000 ['db_name'])/1024 /1024 #line:223
                OO00OOOO0O00O0000 =public .M ('databases').where ('name=?',(O00OOOOOOOO0O0000 ['db_name'],)).getField ('username')#line:224
                O0OOOOOOO0O00O00O =public .get_mysql_obj (O00OOOOOOOO0O0000 ['db_name'])#line:225
                O0OO0O0OO0O0OOO0O =O0O00OOOO0OOOOO0O .__O0OOOOO0O0000O00O (O0OOOOOOO0O00O00O .query ("select Host from mysql.user where User='"+OO00OOOO0O00O0000 +"'"))#line:226
                if OOO0000OO0OOO00OO <O00OOOOOOOO0O0000 ['size']:#line:227
                    if not O00OOOOOOOO0O0000 ['insert_accept']:#line:228
                        for O00000000O00OO0OO in O0OO0O0OO0O0OOO0O :#line:229
                            O0O00OOOO0OOOOO0O .__O00OOO0O000O0OOO0 (O0OOOOOOO0O00O00O ,OO00OOOO0O00O0000 ,O00OOOOOOOO0O0000 ['db_name'],O00000000O00OO0OO [0 ])#line:230
                        O00OOOOOOOO0O0000 ['insert_accept']=True #line:231
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (O00OOOOOOOO0O0000 ['db_name'],O00OOOOOOOO0O0000 ['size']))#line:232
                    if hasattr (O0OOOOOOO0O00O00O ,'close'):O0OOOOOOO0O00O00O .close ()#line:233
                    continue #line:234
                for O00000000O00OO0OO in O0OO0O0OO0O0OOO0O :#line:236
                    O0O00OOOO0OOOOO0O .__O00O0O0O00OOO00OO (O0OOOOOOO0O00O00O ,OO00OOOO0O00O0000 ,O00OOOOOOOO0O0000 ['db_name'],O00000000O00OO0OO [0 ])#line:237
                O00OOOOOOOO0O0000 ['insert_accept']=False #line:238
                public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (O00OOOOOOOO0O0000 ['db_name'],O00OOOOOOOO0O0000 ['size']))#line:239
                if hasattr (O0OOOOOOO0O00O00O ,'close'):O0OOOOOOO0O00O00O .close ()#line:240
            except :#line:241
                public .print_log (public .get_error_info ())#line:242
        public .writeFile (O0O00OOOO0OOOOO0O .__O000O0OOOOOO000O0 ,json .dumps (O0000O000O00000O0 ))#line:243
    def __O000O00OOOO00OO0O (O000000000OOOOO00 ,OOO0OOOO000O0O0O0 ):#line:245
        ""#line:254
        if not O000000000OOOOO00 .__O00OOOO0O0OO00O00 ():return public .returnMsg (False ,O000000000OOOOO00 .__OO0000000000OO0O0 )#line:255
        if not os .path .exists (O000000000OOOOO00 .__O000O0OOOOOO000O0 ):#line:256
            public .writeFile (O000000000OOOOO00 .__O000O0OOOOOO000O0 ,'[]')#line:257
        O0OOO0O0O0OO0OO00 =int (OOO0OOOO000O0O0O0 ['size'])#line:258
        OO0OO0OO0O0000OO0 =OOO0OOOO000O0O0O0 .db_name .strip ()#line:259
        O00O0OOO00O0OOO0O =json .loads (public .readFile (O000000000OOOOO00 .__O000O0OOOOOO000O0 ))#line:260
        for OO0OOO0O0O000000O in O00O0OOO00O0OOO0O :#line:261
            if OO0OOO0O0O000000O ['db_name']==OO0OO0OO0O0000OO0 :#line:262
                return public .returnMsg (False ,'数据库配额已存在')#line:263
        O00O0OOO00O0OOO0O .append ({'db_name':OO0OO0OO0O0000OO0 ,'size':O0OOO0O0O0OO0OO00 ,'insert_accept':True })#line:269
        public .writeFile (O000000000OOOOO00 .__O000O0OOOOOO000O0 ,json .dumps (O00O0OOO00O0OOO0O ))#line:270
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =OO0OO0OO0O0000OO0 ,size =O0OOO0O0O0OO0OO00 ))#line:271
        O000000000OOOOO00 .mysql_quota_check ()#line:272
        return public .returnMsg (True ,'添加成功')#line:273
    def __O00OOOO0O0OO00O00 (OO0OO0OOOOO0O0000 ):#line:276
        from pluginAuth import Plugin #line:277
        OOOO00OO0OOO0OOOO =Plugin (False )#line:278
        O0000O0OOO000OO0O =OOOO00OO0OOO0OOOO .get_plugin_list ()#line:279
        return int (O0000O0OOO000OO0O ['ltd'])>time .time ()#line:280
    def modify_mysql_quota (OOO0OOO000OOOO000 ,O0OOO00O0OOOO0O00 ):#line:282
        ""#line:291
        if not OOO0OOO000OOOO000 .__O00OOOO0O0OO00O00 ():return public .returnMsg (False ,OOO0OOO000OOOO000 .__OO0000000000OO0O0 )#line:292
        if not os .path .exists (OOO0OOO000OOOO000 .__O000O0OOOOOO000O0 ):#line:293
            public .writeFile (OOO0OOO000OOOO000 .__O000O0OOOOOO000O0 ,'[]')#line:294
        if not re .match (r"^\d+$",O0OOO00O0OOOO0O00 .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:295
        OO0O00OO0OOOOOO0O =int (O0OOO00O0OOOO0O00 ['size'])#line:296
        O0O0O0O00000OO000 =O0OOO00O0OOOO0O00 .db_name .strip ()#line:297
        O0000OOO00OOO0OO0 =json .loads (public .readFile (OOO0OOO000OOOO000 .__O000O0OOOOOO000O0 ))#line:298
        OO00O0000OO0000OO =False #line:299
        for OOO00O0O0OO0O0OOO in O0000OOO00OOO0OO0 :#line:300
            if OOO00O0O0OO0O0OOO ['db_name']==O0O0O0O00000OO000 :#line:301
                OOO00O0O0OO0O0OOO ['size']=OO0O00OO0OOOOOO0O #line:302
                OO00O0000OO0000OO =True #line:303
                break #line:304
        if OO00O0000OO0000OO :#line:306
            public .writeFile (OOO0OOO000OOOO000 .__O000O0OOOOOO000O0 ,json .dumps (O0000OOO00OOO0OO0 ))#line:307
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0O0O0O00000OO000 ,size =OO0O00OO0OOOOOO0O ))#line:308
            OOO0OOO000OOOO000 .mysql_quota_check ()#line:309
            return public .returnMsg (True ,'修改成功')#line:310
        return OOO0OOO000OOOO000 .__O000O00OOOO00OO0O (O0OOO00O0OOOO0O00 )#line:311
    def __OOO0O00OOO00OO0O0 (OOOOOO0O00O00OOOO ,OOOO0OOOOOOO0OOO0 ):#line:315
        ""#line:321
        O00OO0O0O0OO0OOO0 =[]#line:322
        O0OOO00000000000O =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =OOOO0OOOOOOO0OOO0 ))[0 ]#line:323
        if not O0OOO00000000000O :return O00OO0O0O0OO0OOO0 #line:324
        for OO0000OO000OO0O00 in O0OOO00000000000O .split ('\n'):#line:325
            if OO0000OO000OO0O00 :O00OO0O0O0OO0OOO0 .append (int (OO0000OO000OO0O00 .split ('#')[-1 ]))#line:326
        return O00OO0O0O0OO0OOO0 #line:327
    def __O0OO0O0OO0000O000 (O000OOO0O00000O0O ,OOO0OOO0O000O0O00 ,O000OOOO00OO00OOO ):#line:329
        ""#line:335
        O000OOO0O0O0O0OO0 =1001 #line:336
        if not OOO0OOO0O000O0O00 :return O000OOO0O0O0O0OO0 #line:337
        O000OOO0O0O0O0OO0 =OOO0OOO0O000O0O00 [-1 ]['id']+1 #line:338
        O000OO00OOOO0O00O =sorted (O000OOO0O00000O0O .__OOO0O00OOO00OO0O0 (O000OOOO00OO00OOO ))#line:339
        if O000OO00OOOO0O00O :#line:340
            if O000OO00OOOO0O00O [-1 ]>O000OOO0O0O0O0OO0 :#line:341
                O000OOO0O0O0O0OO0 =O000OO00OOOO0O00O [-1 ]+1 #line:342
        return O000OOO0O0O0O0OO0 #line:343
    def __OO0OO00OO0O0000OO (OOO00O0000O0O00O0 ,O0OOO00OOO000000O ):#line:346
        ""#line:355
        if not OOO00O0000O0O00O0 .__O00OOOO0O0OO00O00 ():return public .returnMsg (False ,OOO00O0000O0O00O0 .__OO0000000000OO0O0 )#line:356
        O0OOOOO00O00O0O0O =O0OOO00OOO000000O .path .strip ()#line:357
        O00OO00O00OO0O000 =int (O0OOO00OOO000000O .size )#line:358
        if not os .path .exists (O0OOOOO00O00O0O0O ):return public .returnMsg (False ,'指定目录不存在')#line:359
        if os .path .isfile (O0OOOOO00O00O0O0O ):return public .returnMsg (False ,'指定目录不是目录!')#line:360
        if os .path .islink (O0OOOOO00O00O0O0O ):return public .returnMsg (False ,'指定目录是软链接!')#line:361
        OO00OO0O0OOOOO00O =OOO00O0000O0O00O0 .get_quota_path_list ()#line:362
        for O0O0OOOOO0OO0O0OO in OO00OO0O0OOOOO00O :#line:363
            if O0O0OOOOO0OO0O0OO ['path']==O0OOOOO00O00O0O0O :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:364
        OOO00OOOO00OOOO0O =OOO00O0000O0O00O0 .__O0OO0O0OOOO00O0OO (O0OOOOO00O00O0O0O )#line:366
        if OOO00OOOO00OOOO0O ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:367
        if OOO00OOOO00OOOO0O ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:368
        if OOO00OOOO00OOOO0O ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:369
        if O00OO00O00OO0O000 >OOO00OOOO00OOOO0O :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:371
        OOOOO0OO0O0O0O000 =OOO00O0000O0O00O0 .__OOO0000OO0OOO00OO (O0OOOOO00O00O0O0O )#line:373
        if not OOOOO0OO0O0O0O000 :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:374
        if isinstance (OOOOO0OO0O0O0O000 ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OOOOO0OO0O0O0O000 [1 ],path =OOOOO0OO0O0O0O000 [0 ]))#line:376
        OO00O0O0OO0OOOO0O =OOO00O0000O0O00O0 .__O0OO0O0OO0000O000 (OO00OO0O0OOOOO00O ,OOOOO0OO0O0O0O000 )#line:377
        OO00OO00O0O00OO0O =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O0OOOOO00O00O0O0O ,quota_id =OO00O0O0OO0OOOO0O ))#line:379
        if OO00OO00O0O00OO0O [1 ]:return public .returnMsg (False ,OO00OO00O0O00OO0O [1 ])#line:380
        OO00OO00O0O00OO0O =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =OO00O0O0OO0OOOO0O ,size =O00OO00O00OO0O000 ,mountpoint =OOOOO0OO0O0O0O000 ))#line:381
        if OO00OO00O0O00OO0O [1 ]:return public .returnMsg (False ,OO00OO00O0O00OO0O [1 ])#line:382
        OO00OO0O0OOOOO00O .append ({'path':O0OOO00OOO000000O .path ,'size':O00OO00O00OO0O000 ,'id':OO00O0O0OO0OOOO0O })#line:387
        public .writeFile (OOO00O0000O0O00O0 .__OO0O0OO0OOOOOO000 ,json .dumps (OO00OO0O0OOOOO00O ))#line:388
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =O0OOOOO00O00O0O0O ,size =O00OO00O00OO0O000 ))#line:389
        return public .returnMsg (True ,'添加成功')#line:390
    def modify_path_quota (OO0O0O0OOOOOO0O00 ,O00O0O0O000OOOOOO ):#line:393
        ""#line:402
        if not OO0O0O0OOOOOO0O00 .__O00OOOO0O0OO00O00 ():return public .returnMsg (False ,OO0O0O0OOOOOO0O00 .__OO0000000000OO0O0 )#line:403
        OOO00O0O0OOO00OOO =O00O0O0O000OOOOOO .path .strip ()#line:404
        if not re .match (r"^\d+$",O00O0O0O000OOOOOO .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:405
        O000000O0OO00O00O =int (O00O0O0O000OOOOOO .size )#line:406
        if not os .path .exists (OOO00O0O0OOO00OOO ):return public .returnMsg (False ,'指定目录不存在')#line:407
        if os .path .isfile (OOO00O0O0OOO00OOO ):return public .returnMsg (False ,'指定目录不是目录!')#line:408
        if os .path .islink (OOO00O0O0OOO00OOO ):return public .returnMsg (False ,'指定目录是软链接!')#line:409
        O00OO00OO0O0000O0 =OO0O0O0OOOOOO0O00 .get_quota_path_list ()#line:410
        OO00O0OO00O0O0O0O =0 #line:411
        for OO00OO0OOO0O0OOOO in O00OO00OO0O0000O0 :#line:412
            if OO00OO0OOO0O0OOOO ['path']==OOO00O0O0OOO00OOO :#line:413
                OO00O0OO00O0O0O0O =OO00OO0OOO0O0OOOO ['id']#line:414
                break #line:415
        if not OO00O0OO00O0O0O0O :return OO0O0O0OOOOOO0O00 .__OO0OO00OO0O0000OO (O00O0O0O000OOOOOO )#line:416
        O00OO00O0O00000O0 =OO0O0O0OOOOOO0O00 .__O0OO0O0OOOO00O0OO (OOO00O0O0OOO00OOO )#line:418
        if O00OO00O0O00000O0 ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:419
        if O00OO00O0O00000O0 ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:420
        if O00OO00O0O00000O0 ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:421
        if O000000O0OO00O00O >O00OO00O0O00000O0 :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:422
        O00O000OO0OO00O00 =OO0O0O0OOOOOO0O00 .__OOO0000OO0OOO00OO (OOO00O0O0OOO00OOO )#line:424
        if not O00O000OO0OO00O00 :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:425
        if isinstance (O00O000OO0OO00O00 ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =O00O000OO0OO00O00 [1 ],path =O00O000OO0OO00O00 [0 ]))#line:427
        O0O0OOOOOO0OO0000 =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OOO00O0O0OOO00OOO ,quota_id =OO00O0OO00O0O0O0O ))#line:428
        if O0O0OOOOOO0OO0000 [1 ]:return public .returnMsg (False ,O0O0OOOOOO0OO0000 [1 ])#line:429
        O0O0OOOOOO0OO0000 =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =OO00O0OO00O0O0O0O ,size =O000000O0OO00O00O ,mountpoint =O00O000OO0OO00O00 ))#line:430
        if O0O0OOOOOO0OO0000 [1 ]:return public .returnMsg (False ,O0O0OOOOOO0OO0000 [1 ])#line:431
        for OO00OO0OOO0O0OOOO in O00OO00OO0O0000O0 :#line:432
            if OO00OO0OOO0O0OOOO ['path']==OOO00O0O0OOO00OOO :#line:433
                OO00OO0OOO0O0OOOO ['size']=O000000O0OO00O00O #line:434
                break #line:435
        public .writeFile (OO0O0O0OOOOOO0O00 .__OO0O0OO0OOOOOO000 ,json .dumps (O00OO00OO0O0000O0 ))#line:436
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =OOO00O0O0OOO00OOO ,size =O000000O0OO00O00O ))#line:437
        return public .returnMsg (True ,'修改成功')#line:438

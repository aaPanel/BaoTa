import os ,public ,psutil ,json ,time #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __OOO0OO00OO0O00O0O ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __O0OOO0000OO000OOO ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __OOO0O0O0OOOO00000 =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (OO000OOO00O00OO00 )->None :#line:21
        OOO0O00O00O000OO0 ='/usr/sbin/xfs_quota'#line:22
        if not os .path .exists (OOO0O00O00O000OO0 ):#line:23
            if os .path .exists ('/usr/bin/apt-get'):#line:24
                public .ExecShell ('apt-get install xfsprogs -y')#line:25
            else :#line:26
                public .ExecShell ('yum install xfsprogs -y')#line:27
    def __OO0O0O00OOO0OO00O (O000O0O0O00OO0OO0 ,args =None ):#line:30
        ""#line:35
        O0OO0OOO00OOO00OO =[]#line:36
        for O0OOO00OOOOOO0O00 in psutil .disk_partitions ():#line:37
            if O0OOO00OOOOOO0O00 .fstype =='xfs':#line:38
                O0OO0OOO00OOO00OO .append ((O0OOO00OOOOOO0O00 .mountpoint ,O0OOO00OOOOOO0O00 .device ,psutil .disk_usage (O0OOO00OOOOOO0O00 .mountpoint ).free ))#line:39
        return O0OO0OOO00OOO00OO #line:40
    def __OOO0O0OOO000O0OO0 (O0O000O00O00OO00O ,args =None ):#line:42
        ""#line:48
        return O0O000O00O00OO00O .__O00OOOO0OOO0OOO00 (args .path )#line:49
    def __O0OO0O000O0OOO00O (O0O000OOO00OO00O0 ,O0OO0O0O000OOO00O ):#line:51
        ""#line:57
        OO0000O00O0O0O0O0 =O0O000OOO00OO00O0 .__OO0O0O00OOO0OO00O ()#line:58
        for OOOOO0OOOOOOOOO00 in OO0000O00O0O0O0O0 :#line:59
            if O0OO0O0O000OOO00O .find (OOOOO0OOOOOOOOO00 [0 ]+'/')==0 :#line:60
                return OOOOO0OOOOOOOOO00 [1 ]#line:61
        return ''#line:62
    def __O00OOOO0OOO0OOO00 (O0OO0OOOOOOOOOO00 ,O0000000O00O00OO0 ):#line:66
        ""#line:72
        if not os .path .exists (O0000000O00O00OO0 ):return -1 #line:73
        if not os .path .isdir (O0000000O00O00OO0 ):return -2 #line:74
        OO00000OO00OOOOOO =O0OO0OOOOOOOOOO00 .__OO0O0O00OOO0OO00O ()#line:75
        for OO00OOOO00OO000OO in OO00000OO00OOOOOO :#line:76
            if O0000000O00O00OO0 .find (OO00OOOO00OO000OO [0 ]+'/')==0 :#line:77
                return OO00OOOO00OO000OO [2 ]/1024 /1024 #line:78
        return -3 #line:79
    def get_quota_path_list (OOO0O00O0O000O000 ,args =None ,get_path =None ):#line:82
        ""#line:88
        if not os .path .exists (OOO0O00O0O000O000 .__OOO0OO00OO0O00O0O ):#line:89
            public .writeFile (OOO0O00O0O000O000 .__OOO0OO00OO0O00O0O ,'[]')#line:90
        OO000000OO00O0OO0 =json .loads (public .readFile (OOO0O00O0O000O000 .__OOO0OO00OO0O00O0O ))#line:92
        O0OOO00000O0OO0O0 =[]#line:94
        for OO000OOOOOOO0OO0O in OO000000OO00O0OO0 :#line:95
            if not os .path .exists (OO000OOOOOOO0OO0O ['path'])or not os .path .isdir (OO000OOOOOOO0OO0O ['path'])or os .path .islink (OO000OOOOOOO0OO0O ['path']):continue #line:96
            if get_path :#line:97
                if OO000OOOOOOO0OO0O ['path']==get_path :#line:98
                    OO00OOOO0O000000O =psutil .disk_usage (OO000OOOOOOO0OO0O ['path'])#line:99
                    OO000OOOOOOO0OO0O ['used']=OO00OOOO0O000000O .used #line:100
                    OO000OOOOOOO0OO0O ['free']=OO00OOOO0O000000O .free #line:101
                    return OO000OOOOOOO0OO0O #line:102
                else :#line:103
                    continue #line:104
            OO00OOOO0O000000O =psutil .disk_usage (OO000OOOOOOO0OO0O ['path'])#line:105
            OO000OOOOOOO0OO0O ['used']=OO00OOOO0O000000O .used #line:106
            OO000OOOOOOO0OO0O ['free']=OO00OOOO0O000000O .free #line:107
            O0OOO00000O0OO0O0 .append (OO000OOOOOOO0OO0O )#line:108
        if get_path :#line:110
            return {'size':0 ,'used':0 ,'free':0 }#line:111
        if len (O0OOO00000O0OO0O0 )!=len (OO000000OO00O0OO0 ):#line:113
            public .writeFile (OOO0O00O0O000O000 .__OOO0OO00OO0O00O0O ,json .dumps (O0OOO00000O0OO0O0 ))#line:114
        return OO000000OO00O0OO0 #line:116
    def get_quota_mysql_list (O0O0OOO00000O0O0O ,args =None ,get_name =None ):#line:119
        ""#line:125
        if not os .path .exists (O0O0OOO00000O0O0O .__O0OOO0000OO000OOO ):#line:126
            public .writeFile (O0O0OOO00000O0O0O .__O0OOO0000OO000OOO ,'[]')#line:127
        O0O0O0O0000OO00O0 =json .loads (public .readFile (O0O0OOO00000O0O0O .__O0OOO0000OO000OOO ))#line:129
        O0000O00O0O000O00 =[]#line:130
        OO0OO00OOOOO0000O =public .M ('databases')#line:131
        for O0OOOOO00OO00OOOO in O0O0O0O0000OO00O0 :#line:132
            if get_name :#line:133
                if O0OOOOO00OO00OOOO ['db_name']==get_name :#line:134
                    O0OOOOO00OO00OOOO ['used']=O0OOOOO00OO00OOOO ['used']=int (public .get_database_size_by_name (O0OOOOO00OO00OOOO ['db_name']))#line:135
                    _OOO00O0OOOOOO0OOO =O0OOOOO00OO00OOOO ['size']*1024 *1024 #line:136
                    if (O0OOOOO00OO00OOOO ['used']>_OOO00O0OOOOOO0OOO and O0OOOOO00OO00OOOO ['insert_accept'])or (O0OOOOO00OO00OOOO ['used']<_OOO00O0OOOOOO0OOO and not O0OOOOO00OO00OOOO ['insert_accept']):#line:137
                        O0O0OOO00000O0O0O .mysql_quota_check ()#line:138
                    return O0OOOOO00OO00OOOO #line:139
            else :#line:140
                if OO0OO00OOOOO0000O .where ('name=?',O0OOOOO00OO00OOOO ['db_name']).count ():#line:141
                    if args :O0OOOOO00OO00OOOO ['used']=int (public .get_database_size_by_name (O0OOOOO00OO00OOOO ['db_name']))#line:142
                    O0000O00O0O000O00 .append (O0OOOOO00OO00OOOO )#line:143
        OO0OO00OOOOO0000O .close ()#line:144
        if get_name :#line:145
            return {'size':0 ,'used':0 }#line:146
        if len (O0000O00O0O000O00 )!=len (O0O0O0O0000OO00O0 ):#line:147
            public .writeFile (O0O0OOO00000O0O0O .__O0OOO0000OO000OOO ,json .dumps (O0000O00O0O000O00 ))#line:148
        return O0000O00O0O000O00 #line:149
    def __OO00OO0O0OO0OO0O0 (OOOOOO000OOOO0O00 ,OO0OOOO00OO0O0O00 ,O0OOOO0O00000O0OO ,O0O0OOO0000000OO0 ,O00O00OOOOOO0O000 ):#line:151
        ""#line:160
        OOO0O000O000OO0OO =OO0OOOO00OO0O0O00 .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0O0OOO0000000OO0 ,O0OOOO0O00000O0OO ,O00O00OOOOOO0O000 ))#line:161
        if OOO0O000O000OO0OO :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOO0O000O000OO0OO ))#line:162
        OOO0O000O000OO0OO =OO0OOOO00OO0O0O00 .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (O0O0OOO0000000OO0 ,O0OOOO0O00000O0OO ,O00O00OOOOOO0O000 ))#line:163
        if OOO0O000O000OO0OO :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOO0O000O000OO0OO ))#line:164
        OO0OOOO00OO0O0O00 .execute ("FLUSH PRIVILEGES;")#line:165
        return True #line:166
    def __O000O00000O0000O0 (OOO000OO000OOOO00 ,O0O000O0O0O0O0O0O ,OO00O0O0O0O00O0OO ,O00OO00O0OOO0OO0O ,O000O0OOO0000O0O0 ):#line:168
        ""#line:177
        OOOOOOOO0O0OOOO0O =O0O000O0O0O0O0O0O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O00OO00O0OOO0OO0O ,OO00O0O0O0O00O0OO ,O000O0OOO0000O0O0 ))#line:178
        if OOOOOOOO0O0OOOO0O :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OOOOOOOO0O0OOOO0O ))#line:179
        OOOOOOOO0O0OOOO0O =O0O000O0O0O0O0O0O .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (O00OO00O0OOO0OO0O ,OO00O0O0O0O00O0OO ,O000O0OOO0000O0O0 ))#line:180
        if OOOOOOOO0O0OOOO0O :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OOOOOOOO0O0OOOO0O ))#line:181
        O0O000O0O0O0O0O0O .execute ("FLUSH PRIVILEGES;")#line:182
        return True #line:183
    def mysql_quota_service (OO00O0O0OO000OOOO ):#line:186
        ""#line:191
        while 1 :#line:192
            time .sleep (600 )#line:193
            OO00O0O0OO000OOOO .mysql_quota_check ()#line:194
    def __O0OO00OO0OOO000O0 (O00000O0O0OO00O00 ,O00O0O000O0OO000O ):#line:197
        try :#line:198
            if type (O00O0O000O0OO000O )!=list and type (O00O0O000O0OO000O )!=str :O00O0O000O0OO000O =list (O00O0O000O0OO000O )#line:199
            return O00O0O000O0OO000O #line:200
        except :return []#line:201
    def mysql_quota_check (OOO0000000O00OOOO ):#line:203
        ""#line:208
        if not OOO0000000O00OOOO .__O0O0OO00O000O0OO0 ():return public .returnMsg (False ,OOO0000000O00OOOO .__OOO0O0O0OOOO00000 )#line:209
        O0O0OO0O00O0OO0O0 =OOO0000000O00OOOO .get_quota_mysql_list ()#line:210
        for O000OOO0OO00OOOO0 in O0O0OO0O00O0OO0O0 :#line:211
            try :#line:212
                O0OO0O0OO00OOO00O =public .get_database_size_by_name (O000OOO0OO00OOOO0 ['db_name'])/1024 /1024 #line:213
                OO00O000OOOOOO00O =public .M ('databases').where ('name=?',(O000OOO0OO00OOOO0 ['db_name'],)).getField ('username')#line:214
                OOO0OOO0O00O0000O =public .get_mysql_obj (O000OOO0OO00OOOO0 ['db_name'])#line:215
                O0OO000O00OO0OO0O =OOO0000000O00OOOO .__O0OO00OO0OOO000O0 (OOO0OOO0O00O0000O .query ("select Host from mysql.user where User='"+OO00O000OOOOOO00O +"'"))#line:216
                if O0OO0O0OO00OOO00O <O000OOO0OO00OOOO0 ['size']:#line:217
                    if not O000OOO0OO00OOOO0 ['insert_accept']:#line:218
                        for O0O0OO0O0OOOO00OO in O0OO000O00OO0OO0O :#line:219
                            OOO0000000O00OOOO .__O000O00000O0000O0 (OOO0OOO0O00O0000O ,OO00O000OOOOOO00O ,O000OOO0OO00OOOO0 ['db_name'],O0O0OO0O0OOOO00OO [0 ])#line:220
                        O000OOO0OO00OOOO0 ['insert_accept']=True #line:221
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (O000OOO0OO00OOOO0 ['db_name'],O000OOO0OO00OOOO0 ['size']))#line:222
                    if hasattr (OOO0OOO0O00O0000O ,'close'):OOO0OOO0O00O0000O .close ()#line:223
                    continue #line:224
                for O0O0OO0O0OOOO00OO in O0OO000O00OO0OO0O :#line:226
                    OOO0000000O00OOOO .__OO00OO0O0OO0OO0O0 (OOO0OOO0O00O0000O ,OO00O000OOOOOO00O ,O000OOO0OO00OOOO0 ['db_name'],O0O0OO0O0OOOO00OO [0 ])#line:227
                O000OOO0OO00OOOO0 ['insert_accept']=False #line:228
                public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (O000OOO0OO00OOOO0 ['db_name'],O000OOO0OO00OOOO0 ['size']))#line:229
                if hasattr (OOO0OOO0O00O0000O ,'close'):OOO0OOO0O00O0000O .close ()#line:230
            except :#line:231
                public .print_log (public .get_error_info ())#line:232
        public .writeFile (OOO0000000O00OOOO .__O0OOO0000OO000OOO ,json .dumps (O0O0OO0O00O0OO0O0 ))#line:233
    def __OOOOOO0OO000O0OO0 (O0OO00O0000O0O0O0 ,O0O00O00000O00O00 ):#line:235
        ""#line:244
        if not O0OO00O0000O0O0O0 .__O0O0OO00O000O0OO0 ():return public .returnMsg (False ,O0OO00O0000O0O0O0 .__OOO0O0O0OOOO00000 )#line:245
        if not os .path .exists (O0OO00O0000O0O0O0 .__O0OOO0000OO000OOO ):#line:246
            public .writeFile (O0OO00O0000O0O0O0 .__O0OOO0000OO000OOO ,'[]')#line:247
        O000O0000O000OO0O =int (O0O00O00000O00O00 ['size'])#line:248
        OO00OO000OOO0O00O =O0O00O00000O00O00 .db_name .strip ()#line:249
        O0OO00OO000OOOO00 =json .loads (public .readFile (O0OO00O0000O0O0O0 .__O0OOO0000OO000OOO ))#line:250
        for O0OOOO0OOOO0OO0OO in O0OO00OO000OOOO00 :#line:251
            if O0OOOO0OOOO0OO0OO ['db_name']==OO00OO000OOO0O00O :#line:252
                return public .returnMsg (False ,'数据库配额已存在')#line:253
        O0OO00OO000OOOO00 .append ({'db_name':OO00OO000OOO0O00O ,'size':O000O0000O000OO0O ,'insert_accept':True })#line:259
        public .writeFile (O0OO00O0000O0O0O0 .__O0OOO0000OO000OOO ,json .dumps (O0OO00OO000OOOO00 ))#line:260
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =OO00OO000OOO0O00O ,size =O000O0000O000OO0O ))#line:261
        O0OO00O0000O0O0O0 .mysql_quota_check ()#line:262
        return public .returnMsg (True ,'添加成功')#line:263
    def __O0O0OO00O000O0OO0 (OO00O0OOOOOO00O0O ):#line:266
        from pluginAuth import Plugin #line:267
        OOO00OOO00O000O0O =Plugin (False )#line:268
        O0OO0OOOO00O0000O =OOO00OOO00O000O0O .get_plugin_list ()#line:269
        return int (O0OO0OOOO00O0000O ['ltd'])>time .time ()#line:270
    def modify_mysql_quota (O0OO0OO00OOOOOOO0 ,O0O000O0OOOOO0O0O ):#line:272
        ""#line:281
        if not O0OO0OO00OOOOOOO0 .__O0O0OO00O000O0OO0 ():return public .returnMsg (False ,O0OO0OO00OOOOOOO0 .__OOO0O0O0OOOO00000 )#line:282
        if not os .path .exists (O0OO0OO00OOOOOOO0 .__O0OOO0000OO000OOO ):#line:283
            public .writeFile (O0OO0OO00OOOOOOO0 .__O0OOO0000OO000OOO ,'[]')#line:284
        OO0000O0OOOO0000O =int (O0O000O0OOOOO0O0O ['size'])#line:285
        O0O0OO0O0OO0O0000 =O0O000O0OOOOO0O0O .db_name .strip ()#line:286
        OOOO0OO000O0O000O =json .loads (public .readFile (O0OO0OO00OOOOOOO0 .__O0OOO0000OO000OOO ))#line:287
        OO0OO00000OOO0O0O =False #line:288
        for O0OOOOOOO0OOO0O00 in OOOO0OO000O0O000O :#line:289
            if O0OOOOOOO0OOO0O00 ['db_name']==O0O0OO0O0OO0O0000 :#line:290
                O0OOOOOOO0OOO0O00 ['size']=OO0000O0OOOO0000O #line:291
                OO0OO00000OOO0O0O =True #line:292
                break #line:293
        if OO0OO00000OOO0O0O :#line:295
            public .writeFile (O0OO0OO00OOOOOOO0 .__O0OOO0000OO000OOO ,json .dumps (OOOO0OO000O0O000O ))#line:296
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0O0OO0O0OO0O0000 ,size =OO0000O0OOOO0000O ))#line:297
            O0OO0OO00OOOOOOO0 .mysql_quota_check ()#line:298
            return public .returnMsg (True ,'修改成功')#line:299
        return O0OO0OO00OOOOOOO0 .__OOOOOO0OO000O0OO0 (O0O000O0OOOOO0O0O )#line:300
    def __O0O0OOOO0O0OOO0O0 (OOO00O0OOOOO0O0O0 ,O0O0O0O0OOOO00OOO ):#line:304
        ""#line:310
        OOOO00OO0OOOOOOO0 =[]#line:311
        OO0O000OO00O0OOOO =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =O0O0O0O0OOOO00OOO ))[0 ]#line:312
        if not OO0O000OO00O0OOOO :return OOOO00OO0OOOOOOO0 #line:313
        for O00OOOO00OO0O000O in OO0O000OO00O0OOOO .split ('\n'):#line:314
            if O00OOOO00OO0O000O :OOOO00OO0OOOOOOO0 .append (int (O00OOOO00OO0O000O .split ('#')[-1 ]))#line:315
        return OOOO00OO0OOOOOOO0 #line:316
    def __OOO0O0OO0000OO0O0 (O0O0O00OOOO0OOO0O ,O00O00OOO0O0OO000 ,OOOOO00O00OOOO000 ):#line:318
        ""#line:324
        O0000OO00O0OO00OO =1001 #line:325
        if not O00O00OOO0O0OO000 :return O0000OO00O0OO00OO #line:326
        O0000OO00O0OO00OO =O00O00OOO0O0OO000 [-1 ]['id']+1 #line:327
        O0OO00OO0OO000O0O =sorted (O0O0O00OOOO0OOO0O .__OOO0O0OO0000OO0O0 (OOOOO00O00OOOO000 ))#line:328
        if O0OO00OO0OO000O0O :#line:329
            if O0OO00OO0OO000O0O [-1 ]>O0000OO00O0OO00OO :#line:330
                O0000OO00O0OO00OO =O0OO00OO0OO000O0O [-1 ]+1 #line:331
        return O0000OO00O0OO00OO #line:332
    def __OOOO00OO0O0O0O00O (O00O0000O00000O00 ,O0O0O0O0O00O0O00O ):#line:335
        ""#line:344
        if not O00O0000O00000O00 .__O0O0OO00O000O0OO0 ():return public .returnMsg (False ,O00O0000O00000O00 .__OOO0O0O0OOOO00000 )#line:345
        OOOOO0OO0OOO0O0OO =O0O0O0O0O00O0O00O .path .strip ()#line:346
        O000OOOOO0OOOO00O =int (O0O0O0O0O00O0O00O .size )#line:347
        if not os .path .exists (OOOOO0OO0OOO0O0OO ):return public .returnMsg (False ,'指定目录不存在')#line:348
        if os .path .isfile (OOOOO0OO0OOO0O0OO ):return public .returnMsg (False ,'指定目录不是目录!')#line:349
        if os .path .islink (OOOOO0OO0OOO0O0OO ):return public .returnMsg (False ,'指定目录是软链接!')#line:350
        O0O00OOO000O0O000 =O00O0000O00000O00 .get_quota_path_list ()#line:351
        for O0OO000OO00OOOO0O in O0O00OOO000O0O000 :#line:352
            if O0OO000OO00OOOO0O ['path']==OOOOO0OO0OOO0O0OO :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:353
        OOOOOO000O00O00OO =O00O0000O00000O00 .__O00OOOO0OOO0OOO00 (OOOOO0OO0OOO0O0OO )#line:355
        if OOOOOO000O00O00OO ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:356
        if OOOOOO000O00O00OO ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:357
        if OOOOOO000O00O00OO ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:358
        if O000OOOOO0OOOO00O >OOOOOO000O00O00OO :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:360
        OOO00O00O00OOO00O =O00O0000O00000O00 .__O0OO0O000O0OOO00O (OOOOO0OO0OOO0O0OO )#line:362
        if not OOO00O00O00OOO00O :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:363
        O00OOO000OOOO0000 =O00O0000O00000O00 .__OOO0O0OO0000OO0O0 (O0O00OOO000O0O000 ,OOO00O00O00OOO00O )#line:364
        O0OOO0000OOOOOOOO =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OOOOO0OO0OOO0O0OO ,quota_id =O00OOO000OOOO0000 ))#line:366
        if O0OOO0000OOOOOOOO [1 ]:return public .returnMsg (False ,O0OOO0000OOOOOOOO [1 ])#line:367
        O0OOO0000OOOOOOOO =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O00OOO000OOOO0000 ,size =O000OOOOO0OOOO00O ,mountpoint =OOO00O00O00OOO00O ))#line:368
        if O0OOO0000OOOOOOOO [1 ]:return public .returnMsg (False ,O0OOO0000OOOOOOOO [1 ])#line:369
        O0O00OOO000O0O000 .append ({'path':O0O0O0O0O00O0O00O .path ,'size':O000OOOOO0OOOO00O ,'id':O00OOO000OOOO0000 })#line:374
        public .writeFile (O00O0000O00000O00 .__OOO0OO00OO0O00O0O ,json .dumps (O0O00OOO000O0O000 ))#line:375
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =OOOOO0OO0OOO0O0OO ,size =O000OOOOO0OOOO00O ))#line:376
        return public .returnMsg (True ,'添加成功')#line:377
    def modify_path_quota (O0OOOO0000O0OO000 ,O00OOOOO0OO0O0O00 ):#line:380
        ""#line:389
        if not O0OOOO0000O0OO000 .__O0O0OO00O000O0OO0 ():return public .returnMsg (False ,O0OOOO0000O0OO000 .__OOO0O0O0OOOO00000 )#line:390
        O0O0O0OO000OOOO0O =O00OOOOO0OO0O0O00 .path .strip ()#line:391
        O00000O0OO0O0000O =int (O00OOOOO0OO0O0O00 .size )#line:392
        if not os .path .exists (O0O0O0OO000OOOO0O ):return public .returnMsg (False ,'指定目录不存在')#line:393
        if os .path .isfile (O0O0O0OO000OOOO0O ):return public .returnMsg (False ,'指定目录不是目录!')#line:394
        if os .path .islink (O0O0O0OO000OOOO0O ):return public .returnMsg (False ,'指定目录是软链接!')#line:395
        OOO0000000OOO0O0O =O0OOOO0000O0OO000 .get_quota_path_list ()#line:396
        OO0000000O0OOO00O =0 #line:397
        for OO0OO0OO0O000OO0O in OOO0000000OOO0O0O :#line:398
            if OO0OO0OO0O000OO0O ['path']==O0O0O0OO000OOOO0O :#line:399
                OO0000000O0OOO00O =OO0OO0OO0O000OO0O ['id']#line:400
                break #line:401
        if not OO0000000O0OOO00O :return O0OOOO0000O0OO000 .__OOOO00OO0O0O0O00O (O00OOOOO0OO0O0O00 )#line:402
        O0O00OOO0O0OOOO00 =O0OOOO0000O0OO000 .__O00OOOO0OOO0OOO00 (O0O0O0OO000OOOO0O )#line:404
        if O0O00OOO0O0OOOO00 ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:405
        if O0O00OOO0O0OOOO00 ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:406
        if O0O00OOO0O0OOOO00 ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:407
        if O00000O0OO0O0000O >O0O00OOO0O0OOOO00 :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:408
        OO0O0O00OO0OO00OO =O0OOOO0000O0OO000 .__O0OO0O000O0OOO00O (O0O0O0OO000OOOO0O )#line:410
        if not OO0O0O00OO0OO00OO :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:411
        OOOOOO00O0OO0O000 =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O0O0O0OO000OOOO0O ,quota_id =OO0000000O0OOO00O ))#line:412
        if OOOOOO00O0OO0O000 [1 ]:return public .returnMsg (False ,OOOOOO00O0OO0O000 [1 ])#line:413
        OOOOOO00O0OO0O000 =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =OO0000000O0OOO00O ,size =O00000O0OO0O0000O ,mountpoint =OO0O0O00OO0OO00OO ))#line:414
        if OOOOOO00O0OO0O000 [1 ]:return public .returnMsg (False ,OOOOOO00O0OO0O000 [1 ])#line:415
        for OO0OO0OO0O000OO0O in OOO0000000OOO0O0O :#line:416
            if OO0OO0OO0O000OO0O ['path']==O0O0O0OO000OOOO0O :#line:417
                OO0OO0OO0O000OO0O ['size']=O00000O0OO0O0000O #line:418
                break #line:419
        public .writeFile (O0OOOO0000O0OO000 .__OOO0OO00OO0O00O0O ,json .dumps (OOO0000000OOO0O0O ))#line:420
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =O0O0O0OO000OOOO0O ,size =O00000O0OO0O0000O ))#line:421
        return public .returnMsg (True ,'修改成功')#line:422

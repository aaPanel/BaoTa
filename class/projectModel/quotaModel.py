import os ,public ,psutil ,json ,time ,re #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __O00O0OOOO000OO0O0 ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __O00O0OOOO00O00OO0 ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __OOO00O000OO00O0OO =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (OOOOOO00O0OOOOO00 ):#line:21
        _OO0OOO0OOO00000OO ='{}/data/quota_install.pl'.format (public .get_panel_path ())#line:22
        if not os .path .exists (_OO0OOO0OOO00000OO ):#line:23
            O00000OO0000O0O0O ='/usr/sbin/xfs_quota'#line:24
            if not os .path .exists (O00000OO0000O0O0O ):#line:25
                if os .path .exists ('/usr/bin/apt-get'):#line:26
                    public .ExecShell ('nohup apt-get install xfsprogs -y > /dev/null &')#line:27
                else :#line:28
                    public .ExecShell ('nohup yum install xfsprogs -y > /dev/null &')#line:29
            public .writeFile (_OO0OOO0OOO00000OO ,'True')#line:30
    def __O00000O0O0O0000O0 (O0OOO0O0OO0OO0O00 ,args =None ):#line:33
        ""#line:38
        O0O0OOOOO0OO00000 =[]#line:39
        for O0O0OOOO0OO00O000 in psutil .disk_partitions ():#line:40
            if O0O0OOOO0OO00O000 .fstype =='xfs':#line:41
                O0O0OOOOO0OO00000 .append ((O0O0OOOO0OO00O000 .mountpoint ,O0O0OOOO0OO00O000 .device ,psutil .disk_usage (O0O0OOOO0OO00O000 .mountpoint ).free ,O0O0OOOO0OO00O000 .opts .split (',')))#line:49
        return O0O0OOOOO0OO00000 #line:51
    def __O000O0O0000000O00 (O0O000O0O0000OOO0 ,args =None ):#line:53
        ""#line:59
        return O0O000O0O0000OOO0 .__OO0000OO00O00O0OO (args .path )#line:60
    def __O0000O00O0OO00OOO (OOO0O0O00OOOO0O0O ,OOOOOOO00O000OOOO ):#line:62
        ""#line:68
        O0O0OOOO0O0OO0O00 =OOO0O0O00OOOO0O0O .__O00000O0O0O0000O0 ()#line:69
        for OOOOO000O0O00OOO0 in O0O0OOOO0O0OO0O00 :#line:70
            if OOOOOOO00O000OOOO .find (OOOOO000O0O00OOO0 [0 ]+'/')==0 :#line:71
                if not 'prjquota'in OOOOO000O0O00OOO0 [3 ]:#line:72
                    return OOOOO000O0O00OOO0 #line:73
                return OOOOO000O0O00OOO0 [1 ]#line:74
        return ''#line:75
    def __OO0000OO00O00O0OO (OOO00O00OO00OO00O ,OOOO0OO0O00O00OOO ):#line:79
        ""#line:85
        if not os .path .exists (OOOO0OO0O00O00OOO ):return -1 #line:86
        if not os .path .isdir (OOOO0OO0O00O00OOO ):return -2 #line:87
        OOOO0OOO0O0OO000O =OOO00O00OO00OO00O .__O00000O0O0O0000O0 ()#line:88
        for OO0OOO0O00O0O0OO0 in OOOO0OOO0O0OO000O :#line:89
            if OOOO0OO0O00O00OOO .find (OO0OOO0O00O0O0OO0 [0 ]+'/')==0 :#line:90
                return OO0OOO0O00O0O0OO0 [2 ]/1024 /1024 #line:91
        return -3 #line:92
    def get_quota_path_list (O0O00O0O000000O00 ,args =None ,get_path =None ):#line:95
        ""#line:101
        if not os .path .exists (O0O00O0O000000O00 .__O00O0OOOO000OO0O0 ):#line:102
            public .writeFile (O0O00O0O000000O00 .__O00O0OOOO000OO0O0 ,'[]')#line:103
        OOOOO0O00O0O0OOO0 =json .loads (public .readFile (O0O00O0O000000O00 .__O00O0OOOO000OO0O0 ))#line:105
        OOO000O0O0O00OOO0 =[]#line:107
        for OO0O0O0O000OO0OOO in OOOOO0O00O0O0OOO0 :#line:108
            if not os .path .exists (OO0O0O0O000OO0OOO ['path'])or not os .path .isdir (OO0O0O0O000OO0OOO ['path'])or os .path .islink (OO0O0O0O000OO0OOO ['path']):continue #line:109
            if get_path :#line:110
                if OO0O0O0O000OO0OOO ['path']==get_path :#line:111
                    O0OOO0OO00O0O0O00 =psutil .disk_usage (OO0O0O0O000OO0OOO ['path'])#line:112
                    OO0O0O0O000OO0OOO ['used']=O0OOO0OO00O0O0O00 .used #line:113
                    OO0O0O0O000OO0OOO ['free']=O0OOO0OO00O0O0O00 .free #line:114
                    return OO0O0O0O000OO0OOO #line:115
                else :#line:116
                    continue #line:117
            O0OOO0OO00O0O0O00 =psutil .disk_usage (OO0O0O0O000OO0OOO ['path'])#line:118
            OO0O0O0O000OO0OOO ['used']=O0OOO0OO00O0O0O00 .used #line:119
            OO0O0O0O000OO0OOO ['free']=O0OOO0OO00O0O0O00 .free #line:120
            OOO000O0O0O00OOO0 .append (OO0O0O0O000OO0OOO )#line:121
        if get_path :#line:123
            return {'size':0 ,'used':0 ,'free':0 }#line:124
        if len (OOO000O0O0O00OOO0 )!=len (OOOOO0O00O0O0OOO0 ):#line:126
            public .writeFile (O0O00O0O000000O00 .__O00O0OOOO000OO0O0 ,json .dumps (OOO000O0O0O00OOO0 ))#line:127
        return OOOOO0O00O0O0OOO0 #line:129
    def get_quota_mysql_list (OOO000OO00OO00OO0 ,args =None ,get_name =None ):#line:132
        ""#line:138
        if not os .path .exists (OOO000OO00OO00OO0 .__O00O0OOOO00O00OO0 ):#line:139
            public .writeFile (OOO000OO00OO00OO0 .__O00O0OOOO00O00OO0 ,'[]')#line:140
        OO0000OO0O0OOOO00 =json .loads (public .readFile (OOO000OO00OO00OO0 .__O00O0OOOO00O00OO0 ))#line:142
        O00O00O00O00O00OO =[]#line:143
        OOO00O0O00O0OOO00 =public .M ('databases')#line:144
        for OO000OOOOO0000OO0 in OO0000OO0O0OOOO00 :#line:145
            if get_name :#line:146
                if OO000OOOOO0000OO0 ['db_name']==get_name :#line:147
                    OO000OOOOO0000OO0 ['used']=OO000OOOOO0000OO0 ['used']=int (public .get_database_size_by_name (OO000OOOOO0000OO0 ['db_name']))#line:148
                    _O000OO0000O000OO0 =OO000OOOOO0000OO0 ['size']*1024 *1024 #line:149
                    if (OO000OOOOO0000OO0 ['used']>_O000OO0000O000OO0 and OO000OOOOO0000OO0 ['insert_accept'])or (OO000OOOOO0000OO0 ['used']<_O000OO0000O000OO0 and not OO000OOOOO0000OO0 ['insert_accept']):#line:150
                        OOO000OO00OO00OO0 .mysql_quota_check ()#line:151
                    return OO000OOOOO0000OO0 #line:152
            else :#line:153
                if OOO00O0O00O0OOO00 .where ('name=?',OO000OOOOO0000OO0 ['db_name']).count ():#line:154
                    if args :OO000OOOOO0000OO0 ['used']=int (public .get_database_size_by_name (OO000OOOOO0000OO0 ['db_name']))#line:155
                    O00O00O00O00O00OO .append (OO000OOOOO0000OO0 )#line:156
        OOO00O0O00O0OOO00 .close ()#line:157
        if get_name :#line:158
            return {'size':0 ,'used':0 }#line:159
        if len (O00O00O00O00O00OO )!=len (OO0000OO0O0OOOO00 ):#line:160
            public .writeFile (OOO000OO00OO00OO0 .__O00O0OOOO00O00OO0 ,json .dumps (O00O00O00O00O00OO ))#line:161
        return O00O00O00O00O00OO #line:162
    def __O00000O00OO00OOO0 (OOOOOO0O0000OO000 ,OOO00OOO000O000OO ,O000OO0O00OO00OOO ,O0000OO000O0OO00O ,OOO000OO00OOOO00O ):#line:164
        ""#line:173
        O00O0OO00OO000O00 =OOO00OOO000O000OO .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0000OO000O0OO00O ,O000OO0O00OO00OOO ,OOO000OO00OOOO00O ))#line:174
        if O00O0OO00OO000O00 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (O00O0OO00OO000O00 ))#line:175
        O00O0OO00OO000O00 =OOO00OOO000O000OO .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (O0000OO000O0OO00O ,O000OO0O00OO00OOO ,OOO000OO00OOOO00O ))#line:176
        if O00O0OO00OO000O00 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (O00O0OO00OO000O00 ))#line:177
        OOO00OOO000O000OO .execute ("FLUSH PRIVILEGES;")#line:178
        return True #line:179
    def __O00OOOOOOOOOO0000 (O000O0O00O0OOOOO0 ,OOO000OOOO00O000O ,O0OOO0OO00O00OOO0 ,OOO00000O0O0OO0O0 ,O0O0OOOOO0OOOO000 ):#line:181
        ""#line:190
        O0000O00O000O0OOO =OOO000OOOO00O000O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (OOO00000O0O0OO0O0 ,O0OOO0OO00O00OOO0 ,O0O0OOOOO0OOOO000 ))#line:191
        if O0000O00O000O0OOO :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (O0000O00O000O0OOO ))#line:192
        O0000O00O000O0OOO =OOO000OOOO00O000O .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (OOO00000O0O0OO0O0 ,O0OOO0OO00O00OOO0 ,O0O0OOOOO0OOOO000 ))#line:193
        if O0000O00O000O0OOO :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (O0000O00O000O0OOO ))#line:194
        OOO000OOOO00O000O .execute ("FLUSH PRIVILEGES;")#line:195
        return True #line:196
    def mysql_quota_service (O0000OOO00O000000 ):#line:199
        ""#line:204
        while 1 :#line:205
            time .sleep (600 )#line:206
            O0000OOO00O000000 .mysql_quota_check ()#line:207
    def __OOO0O000OO0O0OOO0 (O0OOOO000O0OOO0OO ,O0OO0O00OOO0O000O ):#line:210
        try :#line:211
            if type (O0OO0O00OOO0O000O )!=list and type (O0OO0O00OOO0O000O )!=str :O0OO0O00OOO0O000O =list (O0OO0O00OOO0O000O )#line:212
            return O0OO0O00OOO0O000O #line:213
        except :return []#line:214
    def mysql_quota_check (O00000O00O0O00O00 ):#line:216
        ""#line:221
        if not O00000O00O0O00O00 .__O0OO00O00OOOO0O00 ():return public .returnMsg (False ,O00000O00O0O00O00 .__OOO00O000OO00O0OO )#line:222
        O0000OO0O0O0OOOO0 =O00000O00O0O00O00 .get_quota_mysql_list ()#line:223
        for O0OOO000O0OOO00OO in O0000OO0O0O0OOOO0 :#line:224
            try :#line:225
                if O0OOO000O0OOO00OO ['size']<1 :#line:226
                    if not O0OOO000O0OOO00OO ['insert_accept']:#line:227
                        O00000O00O0O00O00 .__O00OOOOOOOOOO0000 (OO0000O0000000O0O ,OOOOOOOO00O00O00O ,O0OOO000O0OOO00OO ['db_name'],OOO00000O000OO0OO [0 ])#line:228
                        O0OOO000O0OOO00OO ['insert_accept']=True #line:229
                        public .WriteLog ('磁盘配额','已关闭数据库[{}]配额,恢复插入权限'.format (O0OOO000O0OOO00OO ['db_name']))#line:230
                        continue #line:231
                OO00O0OO00000OO00 =public .get_database_size_by_name (O0OOO000O0OOO00OO ['db_name'])/1024 /1024 #line:232
                OOOOOOOO00O00O00O =public .M ('databases').where ('name=?',(O0OOO000O0OOO00OO ['db_name'],)).getField ('username')#line:233
                OO0000O0000000O0O =public .get_mysql_obj (O0OOO000O0OOO00OO ['db_name'])#line:234
                OO00OOO00OOOOO0O0 =O00000O00O0O00O00 .__OOO0O000OO0O0OOO0 (OO0000O0000000O0O .query ("select Host from mysql.user where User='"+OOOOOOOO00O00O00O +"'"))#line:235
                if OO00O0OO00000OO00 <O0OOO000O0OOO00OO ['size']:#line:236
                    if not O0OOO000O0OOO00OO ['insert_accept']:#line:237
                        for OOO00000O000OO0OO in OO00OOO00OOOOO0O0 :#line:238
                            O00000O00O0O00O00 .__O00OOOOOOOOOO0000 (OO0000O0000000O0O ,OOOOOOOO00O00O00O ,O0OOO000O0OOO00OO ['db_name'],OOO00000O000OO0OO [0 ])#line:239
                        O0OOO000O0OOO00OO ['insert_accept']=True #line:240
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (O0OOO000O0OOO00OO ['db_name'],O0OOO000O0OOO00OO ['size']))#line:241
                    if hasattr (OO0000O0000000O0O ,'close'):OO0000O0000000O0O .close ()#line:242
                    continue #line:243
                if O0OOO000O0OOO00OO ['insert_accept']:#line:245
                    for OOO00000O000OO0OO in OO00OOO00OOOOO0O0 :#line:246
                        O00000O00O0O00O00 .__O00000O00OO00OOO0 (OO0000O0000000O0O ,OOOOOOOO00O00O00O ,O0OOO000O0OOO00OO ['db_name'],OOO00000O000OO0OO [0 ])#line:247
                    O0OOO000O0OOO00OO ['insert_accept']=False #line:248
                    public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (O0OOO000O0OOO00OO ['db_name'],O0OOO000O0OOO00OO ['size']))#line:249
                if hasattr (OO0000O0000000O0O ,'close'):OO0000O0000000O0O .close ()#line:250
            except :#line:251
                public .print_log (public .get_error_info ())#line:252
        public .writeFile (O00000O00O0O00O00 .__O00O0OOOO00O00OO0 ,json .dumps (O0000OO0O0O0OOOO0 ))#line:253
    def __O0OOOO0OO000OO0OO (O000OOO0OOO0OO0O0 ,OO0OO0OOOOOO0OOOO ):#line:255
        ""#line:264
        if not O000OOO0OOO0OO0O0 .__O0OO00O00OOOO0O00 ():return public .returnMsg (False ,O000OOO0OOO0OO0O0 .__OOO00O000OO00O0OO )#line:265
        if not os .path .exists (O000OOO0OOO0OO0O0 .__O00O0OOOO00O00OO0 ):#line:266
            public .writeFile (O000OOO0OOO0OO0O0 .__O00O0OOOO00O00OO0 ,'[]')#line:267
        O0OO00O0OO0O0OO00 =int (OO0OO0OOOOOO0OOOO ['size'])#line:268
        OOO0O00OOO00O0O00 =OO0OO0OOOOOO0OOOO .db_name .strip ()#line:269
        O0O0O0000OOOOO00O =json .loads (public .readFile (O000OOO0OOO0OO0O0 .__O00O0OOOO00O00OO0 ))#line:270
        for O0000O0OO0000O00O in O0O0O0000OOOOO00O :#line:271
            if O0000O0OO0000O00O ['db_name']==OOO0O00OOO00O0O00 :#line:272
                return public .returnMsg (False ,'数据库配额已存在')#line:273
        O0O0O0000OOOOO00O .append ({'db_name':OOO0O00OOO00O0O00 ,'size':O0OO00O0OO0O0OO00 ,'insert_accept':True })#line:279
        public .writeFile (O000OOO0OOO0OO0O0 .__O00O0OOOO00O00OO0 ,json .dumps (O0O0O0000OOOOO00O ))#line:280
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =OOO0O00OOO00O0O00 ,size =O0OO00O0OO0O0OO00 ))#line:281
        O000OOO0OOO0OO0O0 .mysql_quota_check ()#line:282
        return public .returnMsg (True ,'添加成功')#line:283
    def __O0OO00O00OOOO0O00 (OO0000OO0OOO0OO0O ):#line:286
        from pluginAuth import Plugin #line:287
        OOO0OO0O000O0O00O =Plugin (False )#line:288
        O000OOO0O0OOOO0OO =OOO0OO0O000O0O00O .get_plugin_list ()#line:289
        return int (O000OOO0O0OOOO0OO ['ltd'])>time .time ()#line:290
    def modify_mysql_quota (OO000OO0O0000O00O ,OOO0OOOOO00OOOOOO ):#line:292
        ""#line:301
        if not OO000OO0O0000O00O .__O0OO00O00OOOO0O00 ():return public .returnMsg (False ,OO000OO0O0000O00O .__OOO00O000OO00O0OO )#line:302
        if not os .path .exists (OO000OO0O0000O00O .__O00O0OOOO00O00OO0 ):#line:303
            public .writeFile (OO000OO0O0000O00O .__O00O0OOOO00O00OO0 ,'[]')#line:304
        if not re .match (r"^\d+$",OOO0OOOOO00OOOOOO .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:305
        O0O0OO0OOO0O0OOO0 =int (OOO0OOOOO00OOOOOO ['size'])#line:306
        O0O0OOO0O00O00O0O =OOO0OOOOO00OOOOOO .db_name .strip ()#line:307
        OOO0O0OOOO0O000OO =json .loads (public .readFile (OO000OO0O0000O00O .__O00O0OOOO00O00OO0 ))#line:308
        OO0O00O00O000O0OO =False #line:309
        for O00O0000000000000 in OOO0O0OOOO0O000OO :#line:310
            if O00O0000000000000 ['db_name']==O0O0OOO0O00O00O0O :#line:311
                O00O0000000000000 ['size']=O0O0OO0OOO0O0OOO0 #line:312
                OO0O00O00O000O0OO =True #line:313
                break #line:314
        if OO0O00O00O000O0OO :#line:316
            public .writeFile (OO000OO0O0000O00O .__O00O0OOOO00O00OO0 ,json .dumps (OOO0O0OOOO0O000OO ))#line:317
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0O0OOO0O00O00O0O ,size =O0O0OO0OOO0O0OOO0 ))#line:318
            OO000OO0O0000O00O .mysql_quota_check ()#line:319
            return public .returnMsg (True ,'修改成功')#line:320
        return OO000OO0O0000O00O .__O0OOOO0OO000OO0OO (OOO0OOOOO00OOOOOO )#line:321
    def __OOOO00OOO0O00OO00 (O000O0000OO00O000 ,O0O00O00O0OO0O00O ):#line:325
        ""#line:331
        O00OOOO00OO0O0000 =[]#line:332
        OO000O0000O0OOOOO =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =O0O00O00O0OO0O00O ))[0 ]#line:333
        if not OO000O0000O0OOOOO :return O00OOOO00OO0O0000 #line:334
        for O0O0O0O0OO0O000O0 in OO000O0000O0OOOOO .split ('\n'):#line:335
            if O0O0O0O0OO0O000O0 :O00OOOO00OO0O0000 .append (int (O0O0O0O0OO0O000O0 .split ('#')[-1 ]))#line:336
        return O00OOOO00OO0O0000 #line:337
    def __O0O00OOOOO0O0OO0O (O00OOO00OOOO00000 ,O000OO00OOOOO0000 ,O0O00OO0000O000OO ):#line:339
        ""#line:345
        O00O00O00O000OOOO =1001 #line:346
        if not O000OO00OOOOO0000 :return O00O00O00O000OOOO #line:347
        O00O00O00O000OOOO =O000OO00OOOOO0000 [-1 ]['id']+1 #line:348
        OO0OO0O00OOOOOOOO =sorted (O00OOO00OOOO00000 .__OOOO00OOO0O00OO00 (O0O00OO0000O000OO ))#line:349
        if OO0OO0O00OOOOOOOO :#line:350
            if OO0OO0O00OOOOOOOO [-1 ]>O00O00O00O000OOOO :#line:351
                O00O00O00O000OOOO =OO0OO0O00OOOOOOOO [-1 ]+1 #line:352
        return O00O00O00O000OOOO #line:353
    def __O0O0OOO000OOO0000 (OOO0OO00OO0OO00OO ,OO0OOO0OO00000O00 ):#line:356
        ""#line:365
        if not OOO0OO00OO0OO00OO .__O0OO00O00OOOO0O00 ():return public .returnMsg (False ,OOO0OO00OO0OO00OO .__OOO00O000OO00O0OO )#line:366
        O00OO00OOO00OO00O =OO0OOO0OO00000O00 .path .strip ()#line:367
        O0O0O00OO0000O000 =int (OO0OOO0OO00000O00 .size )#line:368
        if not os .path .exists (O00OO00OOO00OO00O ):return public .returnMsg (False ,'指定目录不存在')#line:369
        if os .path .isfile (O00OO00OOO00OO00O ):return public .returnMsg (False ,'指定目录不是目录!')#line:370
        if os .path .islink (O00OO00OOO00OO00O ):return public .returnMsg (False ,'指定目录是软链接!')#line:371
        O0O0O0O0OO0OO0OOO =OOO0OO00OO0OO00OO .get_quota_path_list ()#line:372
        for OOO0O0OOOOOO0O0OO in O0O0O0O0OO0OO0OOO :#line:373
            if OOO0O0OOOOOO0O0OO ['path']==O00OO00OOO00OO00O :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:374
        OO00OO00000OO0O00 =OOO0OO00OO0OO00OO .__OO0000OO00O00O0OO (O00OO00OOO00OO00O )#line:376
        if OO00OO00000OO0O00 ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:377
        if OO00OO00000OO0O00 ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:378
        if OO00OO00000OO0O00 ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:379
        if O0O0O00OO0000O000 >OO00OO00000OO0O00 :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:381
        OO000000O0000OOO0 =OOO0OO00OO0OO00OO .__O0000O00O0OO00OOO (O00OO00OOO00OO00O )#line:383
        if not OO000000O0000OOO0 :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:384
        if isinstance (OO000000O0000OOO0 ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OO000000O0000OOO0 [1 ],path =OO000000O0000OOO0 [0 ]))#line:386
        O00O0OO0O000O0OO0 =OOO0OO00OO0OO00OO .__O0O00OOOOO0O0OO0O (O0O0O0O0OO0OO0OOO ,OO000000O0000OOO0 )#line:387
        OOO0000OO0000O000 =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O00OO00OOO00OO00O ,quota_id =O00O0OO0O000O0OO0 ))#line:389
        if OOO0000OO0000O000 [1 ]:return public .returnMsg (False ,OOO0000OO0000O000 [1 ])#line:390
        OOO0000OO0000O000 =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O00O0OO0O000O0OO0 ,size =O0O0O00OO0000O000 ,mountpoint =OO000000O0000OOO0 ))#line:391
        if OOO0000OO0000O000 [1 ]:return public .returnMsg (False ,OOO0000OO0000O000 [1 ])#line:392
        O0O0O0O0OO0OO0OOO .append ({'path':OO0OOO0OO00000O00 .path ,'size':O0O0O00OO0000O000 ,'id':O00O0OO0O000O0OO0 })#line:397
        public .writeFile (OOO0OO00OO0OO00OO .__O00O0OOOO000OO0O0 ,json .dumps (O0O0O0O0OO0OO0OOO ))#line:398
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =O00OO00OOO00OO00O ,size =O0O0O00OO0000O000 ))#line:399
        return public .returnMsg (True ,'添加成功')#line:400
    def modify_path_quota (OOOO000O0OOO000OO ,O0O0OOOOO0O0O0000 ):#line:403
        ""#line:412
        if not OOOO000O0OOO000OO .__O0OO00O00OOOO0O00 ():return public .returnMsg (False ,OOOO000O0OOO000OO .__OOO00O000OO00O0OO )#line:413
        O0000000O0OOOOO0O =O0O0OOOOO0O0O0000 .path .strip ()#line:414
        if not re .match (r"^\d+$",O0O0OOOOO0O0O0000 .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:415
        O0OOO00OOO0OO0000 =int (O0O0OOOOO0O0O0000 .size )#line:416
        if not os .path .exists (O0000000O0OOOOO0O ):return public .returnMsg (False ,'指定目录不存在')#line:417
        if os .path .isfile (O0000000O0OOOOO0O ):return public .returnMsg (False ,'指定目录不是目录!')#line:418
        if os .path .islink (O0000000O0OOOOO0O ):return public .returnMsg (False ,'指定目录是软链接!')#line:419
        O0OOO000OO0OO0O0O =OOOO000O0OOO000OO .get_quota_path_list ()#line:420
        O0OO00OOO00O0O00O =0 #line:421
        for O00OOO00OOO0000OO in O0OOO000OO0OO0O0O :#line:422
            if O00OOO00OOO0000OO ['path']==O0000000O0OOOOO0O :#line:423
                O0OO00OOO00O0O00O =O00OOO00OOO0000OO ['id']#line:424
                break #line:425
        if not O0OO00OOO00O0O00O :return OOOO000O0OOO000OO .__O0O0OOO000OOO0000 (O0O0OOOOO0O0O0000 )#line:426
        O0O0O0OOOO000O00O =OOOO000O0OOO000OO .__OO0000OO00O00O0OO (O0000000O0OOOOO0O )#line:428
        if O0O0O0OOOO000O00O ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:429
        if O0O0O0OOOO000O00O ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:430
        if O0O0O0OOOO000O00O ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:431
        if O0OOO00OOO0OO0000 >O0O0O0OOOO000O00O :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:432
        O0000OOOO00O00O0O =OOOO000O0OOO000OO .__O0000O00O0OO00OOO (O0000000O0OOOOO0O )#line:434
        if not O0000OOOO00O00O0O :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:435
        if isinstance (O0000OOOO00O00O0O ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =O0000OOOO00O00O0O [1 ],path =O0000OOOO00O00O0O [0 ]))#line:437
        O0OOO00O0OO00000O =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O0000000O0OOOOO0O ,quota_id =O0OO00OOO00O0O00O ))#line:438
        if O0OOO00O0OO00000O [1 ]:return public .returnMsg (False ,O0OOO00O0OO00000O [1 ])#line:439
        O0OOO00O0OO00000O =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O0OO00OOO00O0O00O ,size =O0OOO00OOO0OO0000 ,mountpoint =O0000OOOO00O00O0O ))#line:440
        if O0OOO00O0OO00000O [1 ]:return public .returnMsg (False ,O0OOO00O0OO00000O [1 ])#line:441
        for O00OOO00OOO0000OO in O0OOO000OO0OO0O0O :#line:442
            if O00OOO00OOO0000OO ['path']==O0000000O0OOOOO0O :#line:443
                O00OOO00OOO0000OO ['size']=O0OOO00OOO0OO0000 #line:444
                break #line:445
        public .writeFile (OOOO000O0OOO000OO .__O00O0OOOO000OO0O0 ,json .dumps (O0OOO000OO0OO0O0O ))#line:446
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =O0000000O0OOOOO0O ,size =O0OOO00OOO0OO0000 ))#line:447
        return public .returnMsg (True ,'修改成功')#line:448

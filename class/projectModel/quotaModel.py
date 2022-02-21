import os ,public ,psutil ,json ,time ,re #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __OOOOO0O00O0OOO0O0 ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __O000O00OO00OO00O0 ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __OO0OO0OOO0O0O00O0 =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (OO0OOO00OO0O00OOO ):#line:21
        _OOO0O00000OO00O0O ='{}/data/quota_install.pl'.format (public .get_panel_path ())#line:22
        if not os .path .exists (_OOO0O00000OO00O0O ):#line:23
            OOOO000O00O000OO0 ='/usr/sbin/xfs_quota'#line:24
            if not os .path .exists (OOOO000O00O000OO0 ):#line:25
                if os .path .exists ('/usr/bin/apt-get'):#line:26
                    public .ExecShell ('nohup apt-get install xfsprogs -y > /dev/null &')#line:27
                else :#line:28
                    public .ExecShell ('nohup yum install xfsprogs -y > /dev/null &')#line:29
            public .writeFile (_OOO0O00000OO00O0O ,'True')#line:30
    def __OO0O0O0O00O0O0O0O (OO0O000OO00O00OOO ,args =None ):#line:33
        ""#line:38
        OO00O00OOOOOOO0O0 =[]#line:39
        for O0OO0O0000OO00OO0 in psutil .disk_partitions ():#line:40
            if O0OO0O0000OO00OO0 .fstype =='xfs':#line:41
                OO00O00OOOOOOO0O0 .append ((O0OO0O0000OO00OO0 .mountpoint ,O0OO0O0000OO00OO0 .device ,psutil .disk_usage (O0OO0O0000OO00OO0 .mountpoint ).free ,O0OO0O0000OO00OO0 .opts .split (',')))#line:49
        return OO00O00OOOOOOO0O0 #line:51
    def __OO0OO0OO000O0000O (O000O0OO00O0OOOO0 ,args =None ):#line:53
        ""#line:59
        return O000O0OO00O0OOOO0 .__OOO0OOO000000O00O (args .path )#line:60
    def __OOOO00OO0O0OO0000 (OOOO0O00000000OOO ,O00OO0O000000O0O0 ):#line:62
        ""#line:68
        O0O000O0000O00OO0 =OOOO0O00000000OOO .__OO0O0O0O00O0O0O0O ()#line:69
        for OO0O0OO00OOOOOO00 in O0O000O0000O00OO0 :#line:70
            if O00OO0O000000O0O0 .find (OO0O0OO00OOOOOO00 [0 ]+'/')==0 :#line:71
                if not 'prjquota'in OO0O0OO00OOOOOO00 [3 ]:#line:72
                    return OO0O0OO00OOOOOO00 #line:73
                return OO0O0OO00OOOOOO00 [1 ]#line:74
        return ''#line:75
    def __OOO0OOO000000O00O (O0O00O00OOOOO000O ,O0O00OO0O0O0O0O00 ):#line:79
        ""#line:85
        if not os .path .exists (O0O00OO0O0O0O0O00 ):return -1 #line:86
        if not os .path .isdir (O0O00OO0O0O0O0O00 ):return -2 #line:87
        OO0O000OO0OO000O0 =O0O00O00OOOOO000O .__OO0O0O0O00O0O0O0O ()#line:88
        for O0OO000OO0OO00O00 in OO0O000OO0OO000O0 :#line:89
            if O0O00OO0O0O0O0O00 .find (O0OO000OO0OO00O00 [0 ]+'/')==0 :#line:90
                return O0OO000OO0OO00O00 [2 ]/1024 /1024 #line:91
        return -3 #line:92
    def get_quota_path_list (OO0OOO0000OOO0O0O ,args =None ,get_path =None ):#line:95
        ""#line:101
        if not os .path .exists (OO0OOO0000OOO0O0O .__OOOOO0O00O0OOO0O0 ):#line:102
            public .writeFile (OO0OOO0000OOO0O0O .__OOOOO0O00O0OOO0O0 ,'[]')#line:103
        O000000O00O00000O =json .loads (public .readFile (OO0OOO0000OOO0O0O .__OOOOO0O00O0OOO0O0 ))#line:105
        O0000O0000OO0OO00 =[]#line:107
        for O0O00O00O0OO0000O in O000000O00O00000O :#line:108
            if not os .path .exists (O0O00O00O0OO0000O ['path'])or not os .path .isdir (O0O00O00O0OO0000O ['path'])or os .path .islink (O0O00O00O0OO0000O ['path']):continue #line:109
            if get_path :#line:110
                if O0O00O00O0OO0000O ['path']==get_path :#line:111
                    OOOO0OOO0000OOO0O =psutil .disk_usage (O0O00O00O0OO0000O ['path'])#line:112
                    O0O00O00O0OO0000O ['used']=OOOO0OOO0000OOO0O .used #line:113
                    O0O00O00O0OO0000O ['free']=OOOO0OOO0000OOO0O .free #line:114
                    return O0O00O00O0OO0000O #line:115
                else :#line:116
                    continue #line:117
            OOOO0OOO0000OOO0O =psutil .disk_usage (O0O00O00O0OO0000O ['path'])#line:118
            O0O00O00O0OO0000O ['used']=OOOO0OOO0000OOO0O .used #line:119
            O0O00O00O0OO0000O ['free']=OOOO0OOO0000OOO0O .free #line:120
            O0000O0000OO0OO00 .append (O0O00O00O0OO0000O )#line:121
        if get_path :#line:123
            return {'size':0 ,'used':0 ,'free':0 }#line:124
        if len (O0000O0000OO0OO00 )!=len (O000000O00O00000O ):#line:126
            public .writeFile (OO0OOO0000OOO0O0O .__OOOOO0O00O0OOO0O0 ,json .dumps (O0000O0000OO0OO00 ))#line:127
        return O000000O00O00000O #line:129
    def get_quota_mysql_list (OO0OO000O0O0O0O0O ,args =None ,get_name =None ):#line:132
        ""#line:138
        if not os .path .exists (OO0OO000O0O0O0O0O .__O000O00OO00OO00O0 ):#line:139
            public .writeFile (OO0OO000O0O0O0O0O .__O000O00OO00OO00O0 ,'[]')#line:140
        OOO0OO0O00OO00000 =json .loads (public .readFile (OO0OO000O0O0O0O0O .__O000O00OO00OO00O0 ))#line:142
        OO00OOOOO0OO00O00 =[]#line:143
        OOO00OO0OOO0O0OOO =public .M ('databases')#line:144
        for OOO0OO00OO000OOO0 in OOO0OO0O00OO00000 :#line:145
            if get_name :#line:146
                if OOO0OO00OO000OOO0 ['db_name']==get_name :#line:147
                    OOO0OO00OO000OOO0 ['used']=OOO0OO00OO000OOO0 ['used']=int (public .get_database_size_by_name (OOO0OO00OO000OOO0 ['db_name']))#line:148
                    _O0O0OO00OOO00O00O =OOO0OO00OO000OOO0 ['size']*1024 *1024 #line:149
                    if (OOO0OO00OO000OOO0 ['used']>_O0O0OO00OOO00O00O and OOO0OO00OO000OOO0 ['insert_accept'])or (OOO0OO00OO000OOO0 ['used']<_O0O0OO00OOO00O00O and not OOO0OO00OO000OOO0 ['insert_accept']):#line:150
                        OO0OO000O0O0O0O0O .mysql_quota_check ()#line:151
                    return OOO0OO00OO000OOO0 #line:152
            else :#line:153
                if OOO00OO0OOO0O0OOO .where ('name=?',OOO0OO00OO000OOO0 ['db_name']).count ():#line:154
                    if args :OOO0OO00OO000OOO0 ['used']=int (public .get_database_size_by_name (OOO0OO00OO000OOO0 ['db_name']))#line:155
                    OO00OOOOO0OO00O00 .append (OOO0OO00OO000OOO0 )#line:156
        OOO00OO0OOO0O0OOO .close ()#line:157
        if get_name :#line:158
            return {'size':0 ,'used':0 }#line:159
        if len (OO00OOOOO0OO00O00 )!=len (OOO0OO0O00OO00000 ):#line:160
            public .writeFile (OO0OO000O0O0O0O0O .__O000O00OO00OO00O0 ,json .dumps (OO00OOOOO0OO00O00 ))#line:161
        return OO00OOOOO0OO00O00 #line:162
    def __OO00O00O00000O0OO (O0OOOO0O0OO00O0OO ,OO0O0O0000000O0O0 ,O0O0OO0OO0O0O0000 ,O0OO0OO0000OO00OO ,OOO0OOO000O00O0OO ):#line:164
        ""#line:173
        OOO00O0OO00OO0OO0 =OO0O0O0000000O0O0 .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0OO0OO0000OO00OO ,O0O0OO0OO0O0O0000 ,OOO0OOO000O00O0OO ))#line:174
        if OOO00O0OO00OO0OO0 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOO00O0OO00OO0OO0 ))#line:175
        OOO00O0OO00OO0OO0 =OO0O0O0000000O0O0 .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (O0OO0OO0000OO00OO ,O0O0OO0OO0O0O0000 ,OOO0OOO000O00O0OO ))#line:176
        if OOO00O0OO00OO0OO0 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOO00O0OO00OO0OO0 ))#line:177
        OO0O0O0000000O0O0 .execute ("FLUSH PRIVILEGES;")#line:178
        return True #line:179
    def __OOOO0O0O000OO0000 (O0OOO000O00O00O00 ,OOOO0OO000OO0OO0O ,O000O000O000OOO0O ,O0O00OOO0OO000OOO ,OO0O0OOO0000O0O0O ):#line:181
        ""#line:190
        OO0O0OOO00OOO0000 =OOOO0OO000OO0OO0O .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (O0O00OOO0OO000OOO ,O000O000O000OOO0O ,OO0O0OOO0000O0O0O ))#line:191
        if OO0O0OOO00OOO0000 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OO0O0OOO00OOO0000 ))#line:192
        OO0O0OOO00OOO0000 =OOOO0OO000OO0OO0O .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (O0O00OOO0OO000OOO ,O000O000O000OOO0O ,OO0O0OOO0000O0O0O ))#line:193
        if OO0O0OOO00OOO0000 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (OO0O0OOO00OOO0000 ))#line:194
        OOOO0OO000OO0OO0O .execute ("FLUSH PRIVILEGES;")#line:195
        return True #line:196
    def mysql_quota_service (OOO00O000000O0OO0 ):#line:199
        ""#line:204
        while 1 :#line:205
            time .sleep (600 )#line:206
            OOO00O000000O0OO0 .mysql_quota_check ()#line:207
    def __O0OOOO000O0OOO000 (OOO0O0OO0OO0OOOO0 ,OOO0O0000OOOO00OO ):#line:210
        try :#line:211
            if type (OOO0O0000OOOO00OO )!=list and type (OOO0O0000OOOO00OO )!=str :OOO0O0000OOOO00OO =list (OOO0O0000OOOO00OO )#line:212
            return OOO0O0000OOOO00OO #line:213
        except :return []#line:214
    def mysql_quota_check (O00OO0OO0O0O0O0OO ):#line:216
        ""#line:221
        if not O00OO0OO0O0O0O0OO .__OO00O0OO0OOO000O0 ():return public .returnMsg (False ,O00OO0OO0O0O0O0OO .__OO0OO0OOO0O0O00O0 )#line:222
        OOO000000OO0O0O0O =O00OO0OO0O0O0O0OO .get_quota_mysql_list ()#line:223
        for O00O0O0O0OOO0O0OO in OOO000000OO0O0O0O :#line:224
            try :#line:225
                OOO0O0OO00OO0O00O =public .get_database_size_by_name (O00O0O0O0OOO0O0OO ['db_name'])/1024 /1024 #line:226
                OO00O0000O0O0000O =public .M ('databases').where ('name=?',(O00O0O0O0OOO0O0OO ['db_name'],)).getField ('username')#line:227
                O00O000OOO000OOO0 =public .get_mysql_obj (O00O0O0O0OOO0O0OO ['db_name'])#line:228
                O0O00O0000O0O0O0O =O00OO0OO0O0O0O0OO .__O0OOOO000O0OOO000 (O00O000OOO000OOO0 .query ("select Host from mysql.user where User='"+OO00O0000O0O0000O +"'"))#line:229
                if OOO0O0OO00OO0O00O <O00O0O0O0OOO0O0OO ['size']:#line:230
                    if not O00O0O0O0OOO0O0OO ['insert_accept']:#line:231
                        for OOOOO0OOOO00000OO in O0O00O0000O0O0O0O :#line:232
                            O00OO0OO0O0O0O0OO .__OOOO0O0O000OO0000 (O00O000OOO000OOO0 ,OO00O0000O0O0000O ,O00O0O0O0OOO0O0OO ['db_name'],OOOOO0OOOO00000OO [0 ])#line:233
                        O00O0O0O0OOO0O0OO ['insert_accept']=True #line:234
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (O00O0O0O0OOO0O0OO ['db_name'],O00O0O0O0OOO0O0OO ['size']))#line:235
                    if hasattr (O00O000OOO000OOO0 ,'close'):O00O000OOO000OOO0 .close ()#line:236
                    continue #line:237
                for OOOOO0OOOO00000OO in O0O00O0000O0O0O0O :#line:239
                    O00OO0OO0O0O0O0OO .__OO00O00O00000O0OO (O00O000OOO000OOO0 ,OO00O0000O0O0000O ,O00O0O0O0OOO0O0OO ['db_name'],OOOOO0OOOO00000OO [0 ])#line:240
                O00O0O0O0OOO0O0OO ['insert_accept']=False #line:241
                public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (O00O0O0O0OOO0O0OO ['db_name'],O00O0O0O0OOO0O0OO ['size']))#line:242
                if hasattr (O00O000OOO000OOO0 ,'close'):O00O000OOO000OOO0 .close ()#line:243
            except :#line:244
                public .print_log (public .get_error_info ())#line:245
        public .writeFile (O00OO0OO0O0O0O0OO .__O000O00OO00OO00O0 ,json .dumps (OOO000000OO0O0O0O ))#line:246
    def __O000O0OOOOOO00O00 (O00O0O00OOO00O000 ,OO0O0OO0O0O0O0O0O ):#line:248
        ""#line:257
        if not O00O0O00OOO00O000 .__OO00O0OO0OOO000O0 ():return public .returnMsg (False ,O00O0O00OOO00O000 .__OO0OO0OOO0O0O00O0 )#line:258
        if not os .path .exists (O00O0O00OOO00O000 .__O000O00OO00OO00O0 ):#line:259
            public .writeFile (O00O0O00OOO00O000 .__O000O00OO00OO00O0 ,'[]')#line:260
        O0O0000OOOOO0OO00 =int (OO0O0OO0O0O0O0O0O ['size'])#line:261
        O0OO0000O00O0OO0O =OO0O0OO0O0O0O0O0O .db_name .strip ()#line:262
        OOOO0OOOOO0OO00OO =json .loads (public .readFile (O00O0O00OOO00O000 .__O000O00OO00OO00O0 ))#line:263
        for O0OOOO000OO000000 in OOOO0OOOOO0OO00OO :#line:264
            if O0OOOO000OO000000 ['db_name']==O0OO0000O00O0OO0O :#line:265
                return public .returnMsg (False ,'数据库配额已存在')#line:266
        OOOO0OOOOO0OO00OO .append ({'db_name':O0OO0000O00O0OO0O ,'size':O0O0000OOOOO0OO00 ,'insert_accept':True })#line:272
        public .writeFile (O00O0O00OOO00O000 .__O000O00OO00OO00O0 ,json .dumps (OOOO0OOOOO0OO00OO ))#line:273
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0OO0000O00O0OO0O ,size =O0O0000OOOOO0OO00 ))#line:274
        O00O0O00OOO00O000 .mysql_quota_check ()#line:275
        return public .returnMsg (True ,'添加成功')#line:276
    def __OO00O0OO0OOO000O0 (OOOOOO000000OO0OO ):#line:279
        from pluginAuth import Plugin #line:280
        O0O00000O0O0OOO00 =Plugin (False )#line:281
        OO0O0O0O00O000O00 =O0O00000O0O0OOO00 .get_plugin_list ()#line:282
        return int (OO0O0O0O00O000O00 ['ltd'])>time .time ()#line:283
    def modify_mysql_quota (O0OO00O00OOOO00O0 ,OO00OO0OO00OO000O ):#line:285
        ""#line:294
        if not O0OO00O00OOOO00O0 .__OO00O0OO0OOO000O0 ():return public .returnMsg (False ,O0OO00O00OOOO00O0 .__OO0OO0OOO0O0O00O0 )#line:295
        if not os .path .exists (O0OO00O00OOOO00O0 .__O000O00OO00OO00O0 ):#line:296
            public .writeFile (O0OO00O00OOOO00O0 .__O000O00OO00OO00O0 ,'[]')#line:297
        if not re .match (r"^\d+$",OO00OO0OO00OO000O .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:298
        O000OO00OO0O0000O =int (OO00OO0OO00OO000O ['size'])#line:299
        O0O0O0O00O00OOOOO =OO00OO0OO00OO000O .db_name .strip ()#line:300
        OO0OOO0000OOO0OO0 =json .loads (public .readFile (O0OO00O00OOOO00O0 .__O000O00OO00OO00O0 ))#line:301
        O00O0OOO0OO0OOOO0 =False #line:302
        for OO0O0000OOO0O00O0 in OO0OOO0000OOO0OO0 :#line:303
            if OO0O0000OOO0O00O0 ['db_name']==O0O0O0O00O00OOOOO :#line:304
                OO0O0000OOO0O00O0 ['size']=O000OO00OO0O0000O #line:305
                O00O0OOO0OO0OOOO0 =True #line:306
                break #line:307
        if O00O0OOO0OO0OOOO0 :#line:309
            public .writeFile (O0OO00O00OOOO00O0 .__O000O00OO00OO00O0 ,json .dumps (OO0OOO0000OOO0OO0 ))#line:310
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0O0O0O00O00OOOOO ,size =O000OO00OO0O0000O ))#line:311
            O0OO00O00OOOO00O0 .mysql_quota_check ()#line:312
            return public .returnMsg (True ,'修改成功')#line:313
        return O0OO00O00OOOO00O0 .__O000O0OOOOOO00O00 (OO00OO0OO00OO000O )#line:314
    def __OOO0OO00OOOO000OO (OO00O0O000OO0OO0O ,O000OO00OOO0O0O00 ):#line:318
        ""#line:324
        O000O0OO0O0O0O0OO =[]#line:325
        OOOOO000O000O0OOO =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =O000OO00OOO0O0O00 ))[0 ]#line:326
        if not OOOOO000O000O0OOO :return O000O0OO0O0O0O0OO #line:327
        for OO000O000O00O0O0O in OOOOO000O000O0OOO .split ('\n'):#line:328
            if OO000O000O00O0O0O :O000O0OO0O0O0O0OO .append (int (OO000O000O00O0O0O .split ('#')[-1 ]))#line:329
        return O000O0OO0O0O0O0OO #line:330
    def __O0O0O0OO0000OOO0O (O00O0OOOO00O0O0O0 ,OO0O000O0O00OOO00 ,O0OOOOOOOO0000O0O ):#line:332
        ""#line:338
        OOOOOOO000OO00O00 =1001 #line:339
        if not OO0O000O0O00OOO00 :return OOOOOOO000OO00O00 #line:340
        OOOOOOO000OO00O00 =OO0O000O0O00OOO00 [-1 ]['id']+1 #line:341
        O000O00O0OO0O0O00 =sorted (O00O0OOOO00O0O0O0 .__OOO0OO00OOOO000OO (O0OOOOOOOO0000O0O ))#line:342
        if O000O00O0OO0O0O00 :#line:343
            if O000O00O0OO0O0O00 [-1 ]>OOOOOOO000OO00O00 :#line:344
                OOOOOOO000OO00O00 =O000O00O0OO0O0O00 [-1 ]+1 #line:345
        return OOOOOOO000OO00O00 #line:346
    def __OOO0000OOO0OO0000 (O000OOO0O00OO000O ,OOOO00O0O0O0O0000 ):#line:349
        ""#line:358
        if not O000OOO0O00OO000O .__OO00O0OO0OOO000O0 ():return public .returnMsg (False ,O000OOO0O00OO000O .__OO0OO0OOO0O0O00O0 )#line:359
        O0OOO0O000OO0O0O0 =OOOO00O0O0O0O0000 .path .strip ()#line:360
        OO0OO00O000O0OOOO =int (OOOO00O0O0O0O0000 .size )#line:361
        if not os .path .exists (O0OOO0O000OO0O0O0 ):return public .returnMsg (False ,'指定目录不存在')#line:362
        if os .path .isfile (O0OOO0O000OO0O0O0 ):return public .returnMsg (False ,'指定目录不是目录!')#line:363
        if os .path .islink (O0OOO0O000OO0O0O0 ):return public .returnMsg (False ,'指定目录是软链接!')#line:364
        O0O00O00000O0OOO0 =O000OOO0O00OO000O .get_quota_path_list ()#line:365
        for OO0OOO00O00O00OO0 in O0O00O00000O0OOO0 :#line:366
            if OO0OOO00O00O00OO0 ['path']==O0OOO0O000OO0O0O0 :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:367
        OO0OOOO0OOO00O0O0 =O000OOO0O00OO000O .__OOO0OOO000000O00O (O0OOO0O000OO0O0O0 )#line:369
        if OO0OOOO0OOO00O0O0 ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:370
        if OO0OOOO0OOO00O0O0 ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:371
        if OO0OOOO0OOO00O0O0 ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:372
        if OO0OO00O000O0OOOO >OO0OOOO0OOO00O0O0 :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:374
        OO0OOO0OO0000O0OO =O000OOO0O00OO000O .__OOOO00OO0O0OO0000 (O0OOO0O000OO0O0O0 )#line:376
        if not OO0OOO0OO0000O0OO :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:377
        if isinstance (OO0OOO0OO0000O0OO ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OO0OOO0OO0000O0OO [1 ],path =OO0OOO0OO0000O0OO [0 ]))#line:379
        O00000OO00O00O0OO =O000OOO0O00OO000O .__O0O0O0OO0000OOO0O (O0O00O00000O0OOO0 ,OO0OOO0OO0000O0OO )#line:380
        O0O0OO0000O000OOO =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O0OOO0O000OO0O0O0 ,quota_id =O00000OO00O00O0OO ))#line:382
        if O0O0OO0000O000OOO [1 ]:return public .returnMsg (False ,O0O0OO0000O000OOO [1 ])#line:383
        O0O0OO0000O000OOO =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O00000OO00O00O0OO ,size =OO0OO00O000O0OOOO ,mountpoint =OO0OOO0OO0000O0OO ))#line:384
        if O0O0OO0000O000OOO [1 ]:return public .returnMsg (False ,O0O0OO0000O000OOO [1 ])#line:385
        O0O00O00000O0OOO0 .append ({'path':OOOO00O0O0O0O0000 .path ,'size':OO0OO00O000O0OOOO ,'id':O00000OO00O00O0OO })#line:390
        public .writeFile (O000OOO0O00OO000O .__OOOOO0O00O0OOO0O0 ,json .dumps (O0O00O00000O0OOO0 ))#line:391
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =O0OOO0O000OO0O0O0 ,size =OO0OO00O000O0OOOO ))#line:392
        return public .returnMsg (True ,'添加成功')#line:393
    def modify_path_quota (OOOO0OO0000000O00 ,OOO00O0O00OO0O00O ):#line:396
        ""#line:405
        if not OOOO0OO0000000O00 .__OO00O0OO0OOO000O0 ():return public .returnMsg (False ,OOOO0OO0000000O00 .__OO0OO0OOO0O0O00O0 )#line:406
        OO0OOO00OO0OOOO00 =OOO00O0O00OO0O00O .path .strip ()#line:407
        if not re .match (r"^\d+$",OOO00O0O00OO0O00O .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:408
        OOO00O00O0000O000 =int (OOO00O0O00OO0O00O .size )#line:409
        if not os .path .exists (OO0OOO00OO0OOOO00 ):return public .returnMsg (False ,'指定目录不存在')#line:410
        if os .path .isfile (OO0OOO00OO0OOOO00 ):return public .returnMsg (False ,'指定目录不是目录!')#line:411
        if os .path .islink (OO0OOO00OO0OOOO00 ):return public .returnMsg (False ,'指定目录是软链接!')#line:412
        O00O0O00OO0O0OO0O =OOOO0OO0000000O00 .get_quota_path_list ()#line:413
        O000O00O0O000O000 =0 #line:414
        for OOOOOOOO000OOOO0O in O00O0O00OO0O0OO0O :#line:415
            if OOOOOOOO000OOOO0O ['path']==OO0OOO00OO0OOOO00 :#line:416
                O000O00O0O000O000 =OOOOOOOO000OOOO0O ['id']#line:417
                break #line:418
        if not O000O00O0O000O000 :return OOOO0OO0000000O00 .__OOO0000OOO0OO0000 (OOO00O0O00OO0O00O )#line:419
        OO0O00OOOOOO0O0OO =OOOO0OO0000000O00 .__OOO0OOO000000O00O (OO0OOO00OO0OOOO00 )#line:421
        if OO0O00OOOOOO0O0OO ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:422
        if OO0O00OOOOOO0O0OO ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:423
        if OO0O00OOOOOO0O0OO ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:424
        if OOO00O00O0000O000 >OO0O00OOOOOO0O0OO :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:425
        OO0O0O00OO0O000O0 =OOOO0OO0000000O00 .__OOOO00OO0O0OO0000 (OO0OOO00OO0OOOO00 )#line:427
        if not OO0O0O00OO0O000O0 :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:428
        if isinstance (OO0O0O00OO0O000O0 ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OO0O0O00OO0O000O0 [1 ],path =OO0O0O00OO0O000O0 [0 ]))#line:430
        O0OOOO0O0O00O00OO =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OO0OOO00OO0OOOO00 ,quota_id =O000O00O0O000O000 ))#line:431
        if O0OOOO0O0O00O00OO [1 ]:return public .returnMsg (False ,O0OOOO0O0O00O00OO [1 ])#line:432
        O0OOOO0O0O00O00OO =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O000O00O0O000O000 ,size =OOO00O00O0000O000 ,mountpoint =OO0O0O00OO0O000O0 ))#line:433
        if O0OOOO0O0O00O00OO [1 ]:return public .returnMsg (False ,O0OOOO0O0O00O00OO [1 ])#line:434
        for OOOOOOOO000OOOO0O in O00O0O00OO0O0OO0O :#line:435
            if OOOOOOOO000OOOO0O ['path']==OO0OOO00OO0OOOO00 :#line:436
                OOOOOOOO000OOOO0O ['size']=OOO00O00O0000O000 #line:437
                break #line:438
        public .writeFile (OOOO0OO0000000O00 .__OOOOO0O00O0OOO0O0 ,json .dumps (O00O0O00OO0O0OO0O ))#line:439
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =OO0OOO00OO0OOOO00 ,size =OOO00O00O0000O000 ))#line:440
        return public .returnMsg (True ,'修改成功')#line:441

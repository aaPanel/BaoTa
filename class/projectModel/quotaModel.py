import os ,public ,psutil ,json ,time ,re #line:13
from projectModel .base import projectBase #line:14
class main (projectBase ):#line:16
    __O00OO0O00O0O000O0 ='{}/config/quota.json'.format (public .get_panel_path ())#line:17
    __OOOOOOOO0O00O0OOO ='{}/config/mysql_quota.json'.format (public .get_panel_path ())#line:18
    __O0000000OO00O000O =public .to_string ([27492 ,21151 ,33021 ,20026 ,20225 ,19994 ,29256 ,19987 ,20139 ,21151 ,33021 ,65292 ,35831 ,20808 ,36141 ,20080 ,20225 ,19994 ,29256 ])#line:19
    def __init__ (O0OO0O0OO0O00OO0O ):#line:21
        _O00O000000000O00O ='{}/data/quota_install.pl'.format (public .get_panel_path ())#line:22
        if not os .path .exists (_O00O000000000O00O ):#line:23
            O00OO000OO00O0O0O ='/usr/sbin/xfs_quota'#line:24
            if not os .path .exists (O00OO000OO00O0O0O ):#line:25
                if os .path .exists ('/usr/bin/apt-get'):#line:26
                    public .ExecShell ('nohup apt-get install xfsprogs -y > /dev/null &')#line:27
                else :#line:28
                    public .ExecShell ('nohup yum install xfsprogs -y > /dev/null &')#line:29
            public .writeFile (_O00O000000000O00O ,'True')#line:30
    def __OO0O0O000O0O00O00 (OO000OOOO0OO0O0O0 ,args =None ):#line:33
        ""#line:38
        OOO0OO0O0OOO00O0O =[]#line:39
        for O00OOO0OO00OOOO00 in psutil .disk_partitions ():#line:40
            if O00OOO0OO00OOOO00 .fstype =='xfs':#line:41
                OOO0OO0O0OOO00O0O .append ((O00OOO0OO00OOOO00 .mountpoint ,O00OOO0OO00OOOO00 .device ,psutil .disk_usage (O00OOO0OO00OOOO00 .mountpoint ).free ,O00OOO0OO00OOOO00 .opts .split (',')))#line:49
        return OOO0OO0O0OOO00O0O #line:51
    def __O000O00O0O0OO00OO (O0OO0000OOOO0OO0O ,args =None ):#line:53
        ""#line:59
        return O0OO0000OOOO0OO0O .__O00OO0OOOO0O00OO0 (args .path )#line:60
    def __O0O0O0OO0OO00O000 (O0O0O00O00O0OO0OO ,O0OO0O0O0O0OOO0OO ):#line:62
        ""#line:68
        O00000000000OO000 =O0O0O00O00O0OO0OO .__OO0O0O000O0O00O00 ()#line:69
        for OOOO00OOO0O0OOO0O in O00000000000OO000 :#line:70
            if O0OO0O0O0O0OOO0OO .find (OOOO00OOO0O0OOO0O [0 ]+'/')==0 :#line:71
                if not 'prjquota'in OOOO00OOO0O0OOO0O [3 ]:#line:72
                    return OOOO00OOO0O0OOO0O #line:73
                return OOOO00OOO0O0OOO0O [1 ]#line:74
        return ''#line:75
    def __O00OO0OOOO0O00OO0 (OOO0O0OOOO0000OO0 ,OOO0O00O000OO0OOO ):#line:79
        ""#line:85
        if not os .path .exists (OOO0O00O000OO0OOO ):return -1 #line:86
        if not os .path .isdir (OOO0O00O000OO0OOO ):return -2 #line:87
        OOO0O00OO0OOOO0O0 =OOO0O0OOOO0000OO0 .__OO0O0O000O0O00O00 ()#line:88
        for OO0O0O0OOOO00O0O0 in OOO0O00OO0OOOO0O0 :#line:89
            if OOO0O00O000OO0OOO .find (OO0O0O0OOOO00O0O0 [0 ]+'/')==0 :#line:90
                return OO0O0O0OOOO00O0O0 [2 ]/1024 /1024 #line:91
        return -3 #line:92
    def get_quota_path_list (OOOO0OOOOOOOO0OO0 ,args =None ,get_path =None ):#line:95
        ""#line:101
        if not os .path .exists (OOOO0OOOOOOOO0OO0 .__O00OO0O00O0O000O0 ):#line:102
            public .writeFile (OOOO0OOOOOOOO0OO0 .__O00OO0O00O0O000O0 ,'[]')#line:103
        OOOOOOO00OOO00O0O =json .loads (public .readFile (OOOO0OOOOOOOO0OO0 .__O00OO0O00O0O000O0 ))#line:105
        OOO0O00O00OO00OO0 =[]#line:107
        for OOOO00OO000OO0O00 in OOOOOOO00OOO00O0O :#line:108
            if not os .path .exists (OOOO00OO000OO0O00 ['path'])or not os .path .isdir (OOOO00OO000OO0O00 ['path'])or os .path .islink (OOOO00OO000OO0O00 ['path']):continue #line:109
            if get_path :#line:110
                if OOOO00OO000OO0O00 ['path']==get_path :#line:111
                    OOO0OO0O0O00OO00O =psutil .disk_usage (OOOO00OO000OO0O00 ['path'])#line:112
                    OOOO00OO000OO0O00 ['used']=OOO0OO0O0O00OO00O .used #line:113
                    OOOO00OO000OO0O00 ['free']=OOO0OO0O0O00OO00O .free #line:114
                    return OOOO00OO000OO0O00 #line:115
                else :#line:116
                    continue #line:117
            OOO0OO0O0O00OO00O =psutil .disk_usage (OOOO00OO000OO0O00 ['path'])#line:118
            OOOO00OO000OO0O00 ['used']=OOO0OO0O0O00OO00O .used #line:119
            OOOO00OO000OO0O00 ['free']=OOO0OO0O0O00OO00O .free #line:120
            OOO0O00O00OO00OO0 .append (OOOO00OO000OO0O00 )#line:121
        if get_path :#line:123
            return {'size':0 ,'used':0 ,'free':0 }#line:124
        if len (OOO0O00O00OO00OO0 )!=len (OOOOOOO00OOO00O0O ):#line:126
            public .writeFile (OOOO0OOOOOOOO0OO0 .__O00OO0O00O0O000O0 ,json .dumps (OOO0O00O00OO00OO0 ))#line:127
        return OOOOOOO00OOO00O0O #line:129
    def get_quota_mysql_list (OO0O0OOO0OOOO000O ,args =None ,get_name =None ):#line:132
        ""#line:138
        if not os .path .exists (OO0O0OOO0OOOO000O .__OOOOOOOO0O00O0OOO ):#line:139
            public .writeFile (OO0O0OOO0OOOO000O .__OOOOOOOO0O00O0OOO ,'[]')#line:140
        OOO0O000000OOO0OO =json .loads (public .readFile (OO0O0OOO0OOOO000O .__OOOOOOOO0O00O0OOO ))#line:142
        O000OOO0OOOO0OOO0 =[]#line:143
        O0O00OO0000OO0OO0 =public .M ('databases')#line:144
        for O0O0OOOO0OOO0OOOO in OOO0O000000OOO0OO :#line:145
            if get_name :#line:146
                if O0O0OOOO0OOO0OOOO ['db_name']==get_name :#line:147
                    O0O0OOOO0OOO0OOOO ['used']=O0O0OOOO0OOO0OOOO ['used']=int (public .get_database_size_by_name (O0O0OOOO0OOO0OOOO ['db_name']))#line:148
                    _O000O0000OOOO0OO0 =O0O0OOOO0OOO0OOOO ['size']*1024 *1024 #line:149
                    if (O0O0OOOO0OOO0OOOO ['used']>_O000O0000OOOO0OO0 and O0O0OOOO0OOO0OOOO ['insert_accept'])or (O0O0OOOO0OOO0OOOO ['used']<_O000O0000OOOO0OO0 and not O0O0OOOO0OOO0OOOO ['insert_accept']):#line:150
                        OO0O0OOO0OOOO000O .mysql_quota_check ()#line:151
                    return O0O0OOOO0OOO0OOOO #line:152
            else :#line:153
                if O0O00OO0000OO0OO0 .where ('name=?',O0O0OOOO0OOO0OOOO ['db_name']).count ():#line:154
                    if args :O0O0OOOO0OOO0OOOO ['used']=int (public .get_database_size_by_name (O0O0OOOO0OOO0OOOO ['db_name']))#line:155
                    O000OOO0OOOO0OOO0 .append (O0O0OOOO0OOO0OOOO )#line:156
        O0O00OO0000OO0OO0 .close ()#line:157
        if get_name :#line:158
            return {'size':0 ,'used':0 }#line:159
        if len (O000OOO0OOOO0OOO0 )!=len (OOO0O000000OOO0OO ):#line:160
            public .writeFile (OO0O0OOO0OOOO000O .__OOOOOOOO0O00O0OOO ,json .dumps (O000OOO0OOOO0OOO0 ))#line:161
        return O000OOO0OOOO0OOO0 #line:162
    def __O00OOO0O0O00OOOO0 (OO0OO0O0OOOO0OOO0 ,OO00O00O0OOOOOOOO ,O00O0O00OO0000OO0 ,OOO00OOO0OO0000O0 ,OO000OO00O000OOOO ):#line:164
        ""#line:173
        OOOO0O000000O00O0 =OO00O00O0OOOOOOOO .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (OOO00OOO0OO0000O0 ,O00O0O00OO0000OO0 ,OO000OO00O000OOOO ))#line:174
        if OOOO0O000000O00O0 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOOO0O000000O00O0 ))#line:175
        OOOO0O000000O00O0 =OO00O00O0OOOOOOOO .execute ("GRANT SELECT, DELETE, CREATE, DROP, REFERENCES, INDEX, CREATE TEMPORARY TABLES, LOCK TABLES, CREATE VIEW, EVENT, TRIGGER, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EXECUTE ON `{}`.* TO '{}'@'{}';".format (OOO00OOO0OO0000O0 ,O00O0O00OO0000OO0 ,OO000OO00O000OOOO ))#line:176
        if OOOO0O000000O00O0 :raise public .PanelError ('移除数据库用户的插入权限失败: {}'.format (OOOO0O000000O00O0 ))#line:177
        OO00O00O0OOOOOOOO .execute ("FLUSH PRIVILEGES;")#line:178
        return True #line:179
    def __O0OOO00OO0000O000 (OO000O0O00OO0O0OO ,OOO0O00O00O0000O0 ,O00OO00O0OO00OO0O ,OOO0O00OOO00O00OO ,O0OOO00O0OOOOOOOO ):#line:181
        ""#line:190
        O0O0OOOOO0OOOO0O0 =OOO0O00O00O0000O0 .execute ("REVOKE ALL PRIVILEGES ON `{}`.* FROM '{}'@'{}';".format (OOO0O00OOO00O00OO ,O00OO00O0OO00OO0O ,O0OOO00O0OOOOOOOO ))#line:191
        if O0O0OOOOO0OOOO0O0 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (O0O0OOOOO0OOOO0O0 ))#line:192
        O0O0OOOOO0OOOO0O0 =OOO0O00O00O0000O0 .execute ("GRANT ALL PRIVILEGES ON `{}`.* TO '{}'@'{}';".format (OOO0O00OOO00O00OO ,O00OO00O0OO00OO0O ,O0OOO00O0OOOOOOOO ))#line:193
        if O0O0OOOOO0OOOO0O0 :raise public .PanelError ('恢复数据库用户的插入权限失败: {}'.format (O0O0OOOOO0OOOO0O0 ))#line:194
        OOO0O00O00O0000O0 .execute ("FLUSH PRIVILEGES;")#line:195
        return True #line:196
    def mysql_quota_service (O0OOOO0O0O00000OO ):#line:199
        ""#line:204
        while 1 :#line:205
            time .sleep (600 )#line:206
            O0OOOO0O0O00000OO .mysql_quota_check ()#line:207
    def __OOOOO0OO000OO0O00 (O00OO000O000O0OO0 ,OOOO0OO0OOOO0000O ):#line:210
        try :#line:211
            if type (OOOO0OO0OOOO0000O )!=list and type (OOOO0OO0OOOO0000O )!=str :OOOO0OO0OOOO0000O =list (OOOO0OO0OOOO0000O )#line:212
            return OOOO0OO0OOOO0000O #line:213
        except :return []#line:214
    def mysql_quota_check (OOOOOOOOOOOO0O0O0 ):#line:216
        ""#line:221
        if not OOOOOOOOOOOO0O0O0 .__O0OO0O0O000O0OO00 ():return public .returnMsg (False ,OOOOOOOOOOOO0O0O0 .__O0000000OO00O000O )#line:222
        O00O0O00OO00O0OOO =OOOOOOOOOOOO0O0O0 .get_quota_mysql_list ()#line:223
        for OOO00OOO0O000OOO0 in O00O0O00OO00O0OOO :#line:224
            try :#line:225
                O0O0O000000OO0OOO =public .get_database_size_by_name (OOO00OOO0O000OOO0 ['db_name'])/1024 /1024 #line:226
                O0OOO0OOO00O000OO =public .M ('databases').where ('name=?',(OOO00OOO0O000OOO0 ['db_name'],)).getField ('username')#line:227
                OO0OOOO0O00000000 =public .get_mysql_obj (OOO00OOO0O000OOO0 ['db_name'])#line:228
                O0O0OO0O00OO0O00O =OOOOOOOOOOOO0O0O0 .__OOOOO0OO000OO0O00 (OO0OOOO0O00000000 .query ("select Host from mysql.user where User='"+O0OOO0OOO00O000OO +"'"))#line:229
                if O0O0O000000OO0OOO <OOO00OOO0O000OOO0 ['size']:#line:230
                    if not OOO00OOO0O000OOO0 ['insert_accept']:#line:231
                        for OO0O000OOO0O00OO0 in O0O0OO0O00OO0O00O :#line:232
                            OOOOOOOOOOOO0O0O0 .__O0OOO00OO0000O000 (OO0OOOO0O00000000 ,O0OOO0OOO00O000OO ,OOO00OOO0O000OOO0 ['db_name'],OO0O000OOO0O00OO0 [0 ])#line:233
                        OOO00OOO0O000OOO0 ['insert_accept']=True #line:234
                        public .WriteLog ('磁盘配额','数据库[{}]因低于配额[{}MB],恢复插入权限'.format (OOO00OOO0O000OOO0 ['db_name'],OOO00OOO0O000OOO0 ['size']))#line:235
                    if hasattr (OO0OOOO0O00000000 ,'close'):OO0OOOO0O00000000 .close ()#line:236
                    continue #line:237
                if OOO00OOO0O000OOO0 ['insert_accept']:#line:239
                    for OO0O000OOO0O00OO0 in O0O0OO0O00OO0O00O :#line:240
                        OOOOOOOOOOOO0O0O0 .__O00OOO0O0O00OOOO0 (OO0OOOO0O00000000 ,O0OOO0OOO00O000OO ,OOO00OOO0O000OOO0 ['db_name'],OO0O000OOO0O00OO0 [0 ])#line:241
                    OOO00OOO0O000OOO0 ['insert_accept']=False #line:242
                    public .WriteLog ('磁盘配额','数据库[{}]因超出配额[{}MB],移除插入权限'.format (OOO00OOO0O000OOO0 ['db_name'],OOO00OOO0O000OOO0 ['size']))#line:243
                if hasattr (OO0OOOO0O00000000 ,'close'):OO0OOOO0O00000000 .close ()#line:244
            except :#line:245
                public .print_log (public .get_error_info ())#line:246
        public .writeFile (OOOOOOOOOOOO0O0O0 .__OOOOOOOO0O00O0OOO ,json .dumps (O00O0O00OO00O0OOO ))#line:247
    def __OOOOOO00O00O0OOO0 (OOO0OO00OOO0OOO0O ,OO0OOO0O000OOOOOO ):#line:249
        ""#line:258
        if not OOO0OO00OOO0OOO0O .__O0OO0O0O000O0OO00 ():return public .returnMsg (False ,OOO0OO00OOO0OOO0O .__O0000000OO00O000O )#line:259
        if not os .path .exists (OOO0OO00OOO0OOO0O .__OOOOOOOO0O00O0OOO ):#line:260
            public .writeFile (OOO0OO00OOO0OOO0O .__OOOOOOOO0O00O0OOO ,'[]')#line:261
        OO000O0OO0OOOOO00 =int (OO0OOO0O000OOOOOO ['size'])#line:262
        O00O00O0O00OO00O0 =OO0OOO0O000OOOOOO .db_name .strip ()#line:263
        O0000OO000000O00O =json .loads (public .readFile (OOO0OO00OOO0OOO0O .__OOOOOOOO0O00O0OOO ))#line:264
        for O0OO0OOOO0OO0O0O0 in O0000OO000000O00O :#line:265
            if O0OO0OOOO0OO0O0O0 ['db_name']==O00O00O0O00OO00O0 :#line:266
                return public .returnMsg (False ,'数据库配额已存在')#line:267
        O0000OO000000O00O .append ({'db_name':O00O00O0O00OO00O0 ,'size':OO000O0OO0OOOOO00 ,'insert_accept':True })#line:273
        public .writeFile (OOO0OO00OOO0OOO0O .__OOOOOOOO0O00O0OOO ,json .dumps (O0000OO000000O00O ))#line:274
        public .WriteLog ('磁盘配额','创建数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O00O00O0O00OO00O0 ,size =OO000O0OO0OOOOO00 ))#line:275
        OOO0OO00OOO0OOO0O .mysql_quota_check ()#line:276
        return public .returnMsg (True ,'添加成功')#line:277
    def __O0OO0O0O000O0OO00 (OO00O00OO000OOOO0 ):#line:280
        from pluginAuth import Plugin #line:281
        O0OOO00OOOOOOOOO0 =Plugin (False )#line:282
        OO0OOOO0OO0O0O00O =O0OOO00OOOOOOOOO0 .get_plugin_list ()#line:283
        return int (OO0OOOO0OO0O0O00O ['ltd'])>time .time ()#line:284
    def modify_mysql_quota (O0OOO00OOO00O00O0 ,O00O0000OO0O00OO0 ):#line:286
        ""#line:295
        if not O0OOO00OOO00O00O0 .__O0OO0O0O000O0OO00 ():return public .returnMsg (False ,O0OOO00OOO00O00O0 .__O0000000OO00O000O )#line:296
        if not os .path .exists (O0OOO00OOO00O00O0 .__OOOOOOOO0O00O0OOO ):#line:297
            public .writeFile (O0OOO00OOO00O00O0 .__OOOOOOOO0O00O0OOO ,'[]')#line:298
        if not re .match (r"^\d+$",O00O0000OO0O00OO0 .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:299
        O000O00O00O0O00O0 =int (O00O0000OO0O00OO0 ['size'])#line:300
        O0OOOOOO00OO000OO =O00O0000OO0O00OO0 .db_name .strip ()#line:301
        OO0000OOOOOO0OOOO =json .loads (public .readFile (O0OOO00OOO00O00O0 .__OOOOOOOO0O00O0OOO ))#line:302
        OOO0O00O0OO0O00O0 =False #line:303
        for O0000OOO0OOOOO000 in OO0000OOOOOO0OOOO :#line:304
            if O0000OOO0OOOOO000 ['db_name']==O0OOOOOO00OO000OO :#line:305
                O0000OOO0OOOOO000 ['size']=O000O00O00O0O00O0 #line:306
                OOO0O00O0OO0O00O0 =True #line:307
                break #line:308
        if OOO0O00O0OO0O00O0 :#line:310
            public .writeFile (O0OOO00OOO00O00O0 .__OOOOOOOO0O00O0OOO ,json .dumps (OO0000OOOOOO0OOOO ))#line:311
            public .WriteLog ('磁盘配额','修改数据库[{db_name}]的配额限制为: {size}MB'.format (db_name =O0OOOOOO00OO000OO ,size =O000O00O00O0O00O0 ))#line:312
            O0OOO00OOO00O00O0 .mysql_quota_check ()#line:313
            return public .returnMsg (True ,'修改成功')#line:314
        return O0OOO00OOO00O00O0 .__OOOOOO00O00O0OOO0 (O00O0000OO0O00OO0 )#line:315
    def __OO00O0OOO00OOOOO0 (O0O00OO000O0O0000 ,OO0OOOO0OO0OOOO00 ):#line:319
        ""#line:325
        OOO0O0OO0O0O000OO =[]#line:326
        OOOOO000OOOO0O0O0 =public .ExecShell ("xfs_quota -x -c report {mountpoint}|awk '{{print $1}}'|grep '#'".format (mountpoint =OO0OOOO0OO0OOOO00 ))[0 ]#line:327
        if not OOOOO000OOOO0O0O0 :return OOO0O0OO0O0O000OO #line:328
        for O0O000OO0OOO0O000 in OOOOO000OOOO0O0O0 .split ('\n'):#line:329
            if O0O000OO0OOO0O000 :OOO0O0OO0O0O000OO .append (int (O0O000OO0OOO0O000 .split ('#')[-1 ]))#line:330
        return OOO0O0OO0O0O000OO #line:331
    def __O00O000000000O0O0 (OOOO00OO0O0O00O00 ,O00OOO0O0O0O00OO0 ,O0O0OOOOOOOOO000O ):#line:333
        ""#line:339
        OO0O000O0O0O0OOO0 =1001 #line:340
        if not O00OOO0O0O0O00OO0 :return OO0O000O0O0O0OOO0 #line:341
        OO0O000O0O0O0OOO0 =O00OOO0O0O0O00OO0 [-1 ]['id']+1 #line:342
        O0O000OOOOO00O00O =sorted (OOOO00OO0O0O00O00 .__OO00O0OOO00OOOOO0 (O0O0OOOOOOOOO000O ))#line:343
        if O0O000OOOOO00O00O :#line:344
            if O0O000OOOOO00O00O [-1 ]>OO0O000O0O0O0OOO0 :#line:345
                OO0O000O0O0O0OOO0 =O0O000OOOOO00O00O [-1 ]+1 #line:346
        return OO0O000O0O0O0OOO0 #line:347
    def __O00OOOOO0O000OOO0 (OO00O00000000000O ,O0O0O0O0OO000O0OO ):#line:350
        ""#line:359
        if not OO00O00000000000O .__O0OO0O0O000O0OO00 ():return public .returnMsg (False ,OO00O00000000000O .__O0000000OO00O000O )#line:360
        OO000000OOO00O00O =O0O0O0O0OO000O0OO .path .strip ()#line:361
        O000O00OO0O0OO00O =int (O0O0O0O0OO000O0OO .size )#line:362
        if not os .path .exists (OO000000OOO00O00O ):return public .returnMsg (False ,'指定目录不存在')#line:363
        if os .path .isfile (OO000000OOO00O00O ):return public .returnMsg (False ,'指定目录不是目录!')#line:364
        if os .path .islink (OO000000OOO00O00O ):return public .returnMsg (False ,'指定目录是软链接!')#line:365
        O000OOO00O0O00O0O =OO00O00000000000O .get_quota_path_list ()#line:366
        for OOOOOOO0O00000O0O in O000OOO00O0O00O0O :#line:367
            if OOOOOOO0O00000O0O ['path']==OO000000OOO00O00O :return public .returnMsg (False ,'指定目录已经设置过配额!')#line:368
        OO0OOO0000O0OO0OO =OO00O00000000000O .__O00OO0OOOO0O00OO0 (OO000000OOO00O00O )#line:370
        if OO0OOO0000O0OO0OO ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:371
        if OO0OOO0000O0OO0OO ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:372
        if OO0OOO0000O0OO0OO ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:373
        if O000O00OO0O0OO00O >OO0OOO0000O0OO0OO :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:375
        OO0OOOOO0000O0OOO =OO00O00000000000O .__O0O0O0OO0OO00O000 (OO000000OOO00O00O )#line:377
        if not OO0OOOOO0000O0OOO :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:378
        if isinstance (OO0OOOOO0000O0OOO ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OO0OOOOO0000O0OOO [1 ],path =OO0OOOOO0000O0OOO [0 ]))#line:380
        O0O00O00OOO000O00 =OO00O00000000000O .__O00O000000000O0O0 (O000OOO00O0O00O0O ,OO0OOOOO0000O0OOO )#line:381
        OO0OO00OOO0O000O0 =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =OO000000OOO00O00O ,quota_id =O0O00O00OOO000O00 ))#line:383
        if OO0OO00OOO0O000O0 [1 ]:return public .returnMsg (False ,OO0OO00OOO0O000O0 [1 ])#line:384
        OO0OO00OOO0O000O0 =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O0O00O00OOO000O00 ,size =O000O00OO0O0OO00O ,mountpoint =OO0OOOOO0000O0OOO ))#line:385
        if OO0OO00OOO0O000O0 [1 ]:return public .returnMsg (False ,OO0OO00OOO0O000O0 [1 ])#line:386
        O000OOO00O0O00O0O .append ({'path':O0O0O0O0OO000O0OO .path ,'size':O000O00OO0O0OO00O ,'id':O0O00O00OOO000O00 })#line:391
        public .writeFile (OO00O00000000000O .__O00OO0O00O0O000O0 ,json .dumps (O000OOO00O0O00O0O ))#line:392
        public .WriteLog ('磁盘配额','创建目录[{path}]的配额限制为: {size}MB'.format (path =OO000000OOO00O00O ,size =O000O00OO0O0OO00O ))#line:393
        return public .returnMsg (True ,'添加成功')#line:394
    def modify_path_quota (O0O0OO00OOO0O0000 ,OOOO0O000OOOOO0O0 ):#line:397
        ""#line:406
        if not O0O0OO00OOO0O0000 .__O0OO0O0O000O0OO00 ():return public .returnMsg (False ,O0O0OO00OOO0O0000 .__O0000000OO00O000O )#line:407
        O00O0OOOO0000OO00 =OOOO0O000OOOOO0O0 .path .strip ()#line:408
        if not re .match (r"^\d+$",OOOO0O000OOOOO0O0 .size ):return public .returnMsg (False ,'配额大小必须是整数!')#line:409
        O0O0O00OO0000000O =int (OOOO0O000OOOOO0O0 .size )#line:410
        if not os .path .exists (O00O0OOOO0000OO00 ):return public .returnMsg (False ,'指定目录不存在')#line:411
        if os .path .isfile (O00O0OOOO0000OO00 ):return public .returnMsg (False ,'指定目录不是目录!')#line:412
        if os .path .islink (O00O0OOOO0000OO00 ):return public .returnMsg (False ,'指定目录是软链接!')#line:413
        OO000O0O000OOO00O =O0O0OO00OOO0O0000 .get_quota_path_list ()#line:414
        O00O000OO00000OOO =0 #line:415
        for OO00O00O00OO000O0 in OO000O0O000OOO00O :#line:416
            if OO00O00O00OO000O0 ['path']==O00O0OOOO0000OO00 :#line:417
                O00O000OO00000OOO =OO00O00O00OO000O0 ['id']#line:418
                break #line:419
        if not O00O000OO00000OOO :return O0O0OO00OOO0O0000 .__O00OOOOO0O000OOO0 (OOOO0O000OOOOO0O0 )#line:420
        OOOOOOO00OO00OO00 =O0O0OO00OOO0O0000 .__O00OO0OOOO0O00OO0 (O00O0OOOO0000OO00 )#line:422
        if OOOOOOO00OO00OO00 ==-3 :return public .returnMsg (False ,'指定目录所在分区不是XFS分区,不支持目录配额!')#line:423
        if OOOOOOO00OO00OO00 ==-2 :return public .returnMsg (False ,'这不是一个有效的目录!')#line:424
        if OOOOOOO00OO00OO00 ==-1 :return public .returnMsg (False ,'指定目录不存在!')#line:425
        if O0O0O00OO0000000O >OOOOOOO00OO00OO00 :return public .returnMsg (False ,'指定磁盘可用的配额容量不足!')#line:426
        OO0O00OOO0000O00O =O0O0OO00OOO0O0000 .__O0O0O0OO0OO00O000 (O00O0OOOO0000OO00 )#line:428
        if not OO0O00OOO0000O00O :return public .returnMsg (False ,'指定目录不在xfs磁盘分区中!')#line:429
        if isinstance (OO0O00OOO0000O00O ,tuple ):return public .returnMsg (False ,'指定xfs分区未开启目录配额功能,请在挂载该分区时增加prjquota参数<p>/etc/fstab文件配置示例：<pre>{mountpoint}       {path}           xfs             defaults,prjquota       0 0</pre></p><p>注意：配置好后需重新挂载分区或重启服务器才能生效</p>'.format (mountpoint =OO0O00OOO0000O00O [1 ],path =OO0O00OOO0000O00O [0 ]))#line:431
        O000O000OO00OOOO0 =public .ExecShell ("xfs_quota -x -c 'project -s -p {path} {quota_id}'".format (path =O00O0OOOO0000OO00 ,quota_id =O00O000OO00000OOO ))#line:432
        if O000O000OO00OOOO0 [1 ]:return public .returnMsg (False ,O000O000OO00OOOO0 [1 ])#line:433
        O000O000OO00OOOO0 =public .ExecShell ("xfs_quota -x -c 'limit -p bhard={size}m {quota_id}' {mountpoint}".format (quota_id =O00O000OO00000OOO ,size =O0O0O00OO0000000O ,mountpoint =OO0O00OOO0000O00O ))#line:434
        if O000O000OO00OOOO0 [1 ]:return public .returnMsg (False ,O000O000OO00OOOO0 [1 ])#line:435
        for OO00O00O00OO000O0 in OO000O0O000OOO00O :#line:436
            if OO00O00O00OO000O0 ['path']==O00O0OOOO0000OO00 :#line:437
                OO00O00O00OO000O0 ['size']=O0O0O00OO0000000O #line:438
                break #line:439
        public .writeFile (O0O0OO00OOO0O0000 .__O00OO0O00O0O000O0 ,json .dumps (OO000O0O000OOO00O ))#line:440
        public .WriteLog ('磁盘配额','修改目录[{path}]的配额限制为: {size}MB'.format (path =O00O0OOOO0000OO00 ,size =O0O0O00OO0000000O ))#line:441
        return public .returnMsg (True ,'修改成功')#line:442

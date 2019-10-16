
var database = {
    get_list: function (page, search) {
        if (page == undefined) page = 1;
        if (!search) search = $("#SearchValue").val();
        bt.database.get_list(page, search, function (rdata) {
            $('#databasePage').html(rdata.page);
            var _tab = bt.render({
                table: '#DataBody',
                columns: [
                    { field: 'id', type: 'checkbox', width: 30 },
                    {
                        field: 'name', title: '数据库名', width: '20%'
                    },
                    {
                        field: 'username', title: '用户名', sort: function () {
                            database.get_list();
                        }
                    },
                    {
                        field: 'password', width: '15%', title: '密码', templet: function (item) {
                            var _html = '<span class="password" data-pw="' + item.password + '">**********</span>';
                            _html += '<span onclick="bt.pub.show_hide_pass(this)" class="glyphicon glyphicon-eye-open cursor pw-ico" style="margin-left:10px"></span>';
                            _html += '<span class="ico-copy cursor btcopy" style="margin-left:10px" title="复制密码" data-pw="' + item.password + '" onclick="bt.pub.copy_pass(\'' + item.password + '\')"></span>';
                            return _html;
                        }
                    },
                    {
                        field: 'backup', title: '备份', templet: function (item) {
                            var backup = '';
                            var _msg = lan.database.backup_empty;
                            if (item.backup_count > 0) _msg = lan.database.backup_ok;
                            backup = "<a href='javascript:;' class='btlink' onclick=\"database.database_detail('" + item.id + "','" + item.name + "')\">" + _msg + "</a> | "
                            backup += "<a class='btlink' href=\"javascript:database.input_database('" + item.name + "');\" title='" + lan.database.input_title + "'>" + lan.database.input + "</a>";
                            return backup;
                        }
                    },
                    {
                        field: 'ps', title: '备注', templet: function (item) {
                            var _ps = "<span class='c9 input-edit' onclick=\"bt.pub.set_data_by_key('databases','ps',this)\" >"
                            if (item.password) {
                                _ps += item.ps
                            } else {
                                _ps += '无法获取到密码，请通过<span style="color:red">改密</span>按钮设置密码!';
                            }
                            _ps += "</span>";
                            return _ps;
                        }
                    },
                    {
                        field: 'opt', width: 260, title: '操作', align: 'right', templet: function (item) {
                            var option = "<a href=\"javascript:;\" class=\"btlink\" onclick=\"bt.database.open_phpmyadmin('" + item.name + "','" + item.username + "','" + item.password + "')\" title=\"数据库管理\">管理</a> | ";
                            option += "<a href=\"javascript:;\" class=\"btlink\" onclick=\"database.rep_tools('" + item.name + "')\" title=\"MySQL优化修复工具\">工具</a> | ";
                            option += "<a href=\"javascript:;\" class=\"btlink\" onclick=\"bt.database.set_data_access('" + item.username + "')\" title=\"设置数据库权限\">权限</a> | ";
                            option += "<a href=\"javascript:;\" class=\"btlink\" onclick=\"database.set_data_pass(" + item.id + ",'" + item.username + "','" + item.password + "')\" title=\"修改数据库密码\">改密</a> | ";
                            option += "<a href=\"javascript:;\" class=\"btlink\" onclick=\"database.del_database(" + item.id + ",'" + item.name + "')\" title=\"删除数据库\">删除</a>";
                            return option;
                        }
                    },
                ],
                data: rdata.data
            })
        })
    },
    rep_tools: function (db_name, res) {
        var loadT = layer.msg('正在获取数据,请稍候...', { icon: 16, time: 0 });
        bt.send('GetInfo', 'database/GetInfo', { db_name: db_name }, function (rdata) {
            layer.close(loadT)
            if (rdata.status === false) {
                layer.msg(rdata.msg, { icon: 2 });
                return;
            }
            var types = { InnoDB: "MyISAM", MyISAM: "InnoDB" };
            var tbody = '';
            for (var i = 0; i < rdata.tables.length; i++) {
                if (!types[rdata.tables[i].type]) continue;
                tbody += '<tr>\
                        <td><input value="dbtools_' + rdata.tables[i].table_name + '" class="check" onclick="database.selected_tools(null,\'' + db_name + '\');" type="checkbox"></td>\
                        <td><span style="width:220px;"> ' + rdata.tables[i].table_name + '</span></td>\
                        <td>' + rdata.tables[i].type + '</td>\
                        <td><span style="width:90px;"> ' + rdata.tables[i].collation + '</span></td>\
                        <td>' + rdata.tables[i].rows_count + '</td>\
                        <td>' + rdata.tables[i].data_size + '</td>\
                        <td style="text-align: right;">\
                            <a class="btlink" onclick="database.rep_database(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\')">修复</a> |\
                            <a class="btlink" onclick="database.op_database(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\')">优化</a> |\
                            <a class="btlink" onclick="database.to_database_type(\''+ db_name + '\',\'' + rdata.tables[i].table_name + '\',\'' + types[rdata.tables[i].type] + '\')">转为' + types[rdata.tables[i].type] + '</a>\
                        </td>\
                    </tr> '
            }

            if (res) {
                $(".gztr").html(tbody);
                $("#db_tools").html('');
                $("input[type='checkbox']").attr("checked", false);
                $(".tools_size").html('大小：' + rdata.data_size);
                return;
            }

            layer.open({
                type: 1,
                title: "MySQL工具箱【" + db_name + "】",
                area: ['780px', '580px'],
                closeBtn: 2,
                shadeClose: false,
                content: '<div class="pd15">\
                                <div class="db_list">\
                                    <span><a>数据库名称：'+ db_name + '</a>\
                                    <a class="tools_size">大小：'+ rdata.data_size + '</a></span>\
                                    <span id="db_tools" style="float: right;"></span>\
                                </div >\
                                <div class="divtable">\
                                <div  id="database_fix"  style="height:360px;overflow:auto;border:#ddd 1px solid">\
                                <table class="table table-hover "style="border:none">\
                                    <thead>\
                                        <tr>\
                                            <th><input class="check" onclick="database.selected_tools(this,\''+ db_name + '\');" type="checkbox"></th>\
                                            <th>表名</th>\
                                            <th>引擎</th>\
                                            <th>字符集</th>\
                                            <th>行数</th>\
                                            <th>大小</th>\
                                            <th style="text-align: right;">操作</th>\
                                        </tr>\
                                    </thead>\
                                    <tbody class="gztr">' + tbody + '</tbody>\
                                </table>\
                                </div>\
                            </div>\
                            <ul class="help-info-text c7">\
                                <li>【修复】尝试使用REPAIR命令修复损坏的表，仅能做简单修复，若修复不成功请考虑使用myisamchk工具</li>\
                                <li>【优化】执行OPTIMIZE命令，可回收未释放的磁盘空间，建议每月执行一次</li>\
                                <li>【转为InnoDB/MyISAM】转换数据表引擎，建议将所有表转为InnoDB</li>\
                            </ul></div>'
            });
            tableFixed('database_fix');
            //表格头固定
            function tableFixed(name) {
                var tableName = document.querySelector('#' + name);
                tableName.addEventListener('scroll', scrollHandle);
            }
            function scrollHandle(e) {
                var scrollTop = this.scrollTop;
                //this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
                $(this).find("thead").css({ "transform": "translateY(" + scrollTop + "px)", "position": "relative", "z-index": "1" });
            }
        });
    },
    selected_tools: function (my_obj, db_name) {
        var is_checked = false

        if (my_obj) is_checked = my_obj.checked;
        var db_tools = $("input[value^='dbtools_']");
        var n = 0;
        for (var i = 0; i < db_tools.length; i++) {
            if (my_obj) db_tools[i].checked = is_checked;
            if (db_tools[i].checked) n++;
        }
        if (n > 0) {
            var my_btns = '<button class="btn btn-default btn-sm" onclick="database.rep_database(\'' + db_name + '\',null)">修复</button><button class="btn btn-default btn-sm" onclick="database.op_database(\'' + db_name + '\',null)">优化</button><button class="btn btn-default btn-sm" onclick="database.to_database_type(\'' + db_name + '\',null,\'InnoDB\')">转为InnoDB</button></button><button class="btn btn-default btn-sm" onclick="database.to_database_type(\'' + db_name + '\',null,\'MyISAM\')">转为MyISAM</button>'
            $("#db_tools").html(my_btns);
        } else {
            $("#db_tools").html('');
        }
    },
    rep_database: function (db_name, tables) {
        dbs = database.rep_checkeds(tables)
        var loadT = layer.msg('已送修复指令,请稍候...', { icon: 16, time: 0 });
        bt.send('ReTable', 'database/ReTable', { db_name: db_name, tables: JSON.stringify(dbs) }, function (rdata) {
            layer.close(loadT)
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            database.rep_tools(db_name, true);
        });
    },
    op_database: function (db_name, tables) {
        dbs = database.rep_checkeds(tables)
        var loadT = layer.msg('已送优化指令,请稍候...', { icon: 16, time: 0 });
        bt.send('OpTable', 'database/OpTable', { db_name: db_name, tables: JSON.stringify(dbs) }, function (rdata) {
            layer.close(loadT)
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            database.rep_tools(db_name, true);
        });
    },
    to_database_type: function (db_name, tables, type) {
        dbs = database.rep_checkeds(tables)
        var loadT = layer.msg('已送引擎转换指令,请稍候...', { icon: 16, time: 0, shade: [0.3, "#000"] });
        bt.send('AlTable', 'database/AlTable', { db_name: db_name, tables: JSON.stringify(dbs), table_type: type }, function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            database.rep_tools(db_name, true);
        });
    },
    rep_checkeds: function (tables) {
        var dbs = []
        if (tables) {
            dbs.push(tables)
        } else {
            var db_tools = $("input[value^='dbtools_']");
            for (var i = 0; i < db_tools.length; i++) {
                if (db_tools[i].checked) dbs.push(db_tools[i].value.replace('dbtools_', ''));
            }
        }

        if (dbs.length < 1) {
            layer.msg('请至少选择一张表!', { icon: 2 });
            return false;
        }
        return dbs;
    },
    sync_to_database: function (type) {
        var data = [];
        $('input[type="checkbox"].check:checked').each(function () {
            if (!isNaN($(this).val())) data.push($(this).val());
        });
        bt.database.sync_to_database({ type: type, ids: JSON.stringify(data) }, function (rdata) {
            if (rdata.status) database.get_list();
        });
    },
    sync_database: function () {
        bt.database.sync_database(function (rdata) {
            if (rdata.status) database.get_list();
        })
    },
    add_database: function () {
        bt.database.add_database(function (rdata) {
            if (rdata.status) database.get_list();
        })
    },
    batch_database: function (type, arr, result) {
        if (arr == undefined) {
            arr = [];
            result = { count: 0, error_list: [] };
            $('input[type="checkbox"].check:checked').each(function () {
                var _val = $(this).val();
                if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
            })
            bt.show_confirm(lan.database.del_all_title, "<a style='color:red;'>" + lan.get('del_all_database', [arr.length]) + "</a>", function () {
                bt.closeAll();
                database.batch_database(type, arr, result);
            });
            return;
        }
        var item = arr[0];
        switch (type) {
            case 'del':
                if (arr.length < 1) {
                    database.get_list();
                    bt.msg({ msg: lan.get('del_all_database_ok', [result.count]), icon: 1, time: 5000 });
                    return;
                }
                bt.database.del_database({ id: item.id, name: item.name }, function (rdata) {
                    if (rdata.status) {
                        result.count += 1;
                    } else {
                        result.error_list.push({ name: item.item, err_msg: rdata.msg });
                    }
                    arr.splice(0, 1)
                    database.batch_database(type, arr, result);
                })
                break;
        }
    },
    del_database: function (id, name) {
        bt.show_confirm(lan.get('del', [name]), lan.get('confirm_del', [name]), function () {
            bt.database.del_database({ id: id, name: name }, function (rdata) {
                if (rdata.status) database.get_list();
                bt.msg(rdata);
            })
        });
    },
    set_data_pass: function (id, username, password) {
        var bs = bt.database.set_data_pass(function (rdata) {
            if (rdata.status) database.get_list();
            bt.msg(rdata);
        })
        $('.name' + bs).val(username);
        $('.id' + bs).val(id);
        $('.password' + bs).val(password);
    },
    database_detail: function (id, dataname, page) {
        if (page == undefined) page = '1';
        var loadT = bt.load(lan.public.the_get);
        bt.pub.get_data('table=backup&search=' + id + '&limit=5&type=1&tojs=database.database_detail&p=' + page, function (frdata) {
            loadT.close();
            var ftpdown = '';
            var body = '';
            var port;
            frdata.page = frdata.page.replace(/'/g, '"').replace(/database.database_detail\(/g, "database.database_detail(" + id + ",'" + dataname + "',");
            if ($('#DataBackupList').length <= 0) {
                bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '700px',
                    title: lan.database.backup_title,
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: "<div class='divtable pd15 style='padding-bottom: 0'><button id='btn_data_backup' class='btn btn-success btn-sm' type='button' style='margin-bottom:10px'>" + lan.database.backup + "</button><table width='100%' id='DataBackupList' class='table table-hover'></table><div class='page databackup_page'></div></div>"
                });
            }
            setTimeout(function () {
                $('.databackup_page').html(frdata.page);
                var _tab = bt.render({
                    table: '#DataBackupList',
                    columns: [
                        { field: 'name', title: '文件名称' },
                        {
                            field: 'size', title: '文件大小', templet: function (item) {
                                return bt.format_size(item.size);
                            }
                        },
                        { field: 'addtime', title: '备份时间' },
                        {
                            field: 'opt', title: '操作', align: 'right', templet: function (item) {
                                var _opt = '<a class="btlink" herf="javascrpit:;" onclick="bt.database.input_sql(\'' + item.filename + '\',\'' + dataname + '\')">恢复</a> | ';
                                _opt += '<a class="btlink" href="/download?filename=' + item.filename + '&amp;name=' + item.name + '" target="_blank">下载</a> | ';
                                _opt += '<a class="btlink" herf="javascrpit:;" onclick="bt.database.del_backup(\'' + item.id + '\',\'' + id + '\',\'' + dataname + '\')">删除</a>'
                                return _opt;
                            }
                        },
                    ],
                    data: frdata.data
                });
                $('#btn_data_backup').unbind('click').click(function () {
                    bt.database.backup_data(id, dataname, function (rdata) {
                        if (rdata.status) database.database_detail(id, dataname);
                    })
                })
            }, 100)
        });
    },
    upload_files: function (name) {
        var path = bt.get_cookie('backup_path') + "/database/";
        bt_upload_file.open(path, '.sql,.gz,.tar.gz,.zip', lan.database.input_up_type, function () {
            database.input_database(name);
        });

        /*
        var index = layer.open({
            type: 1,
            closeBtn: 2,
            title: lan.files.up_title + ' --- <span style="color:red;">' + lan.database.input_up_type + '</span>',
            area: ['500px', '500px'],
            shadeClose: false,
            content: '<div class="fileUploadDiv"><input type="hidden" id="input-val" value="' + path + '" />\
						<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
						<button type="button"  id="opt" autocomplete="off">'+ lan.files.up_add + '</button>\
						<button type="button" id="up" autocomplete="off" >'+ lan.files.up_start + '</button>\
						<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
						<span style="float:right;margin-top: 9px;">\
						<font>'+ lan.files.up_coding + ':</font>\
						<select id="fileCodeing" >\
							<option value="byte">'+ lan.files.up_bin + '</option>\
							<option value="utf-8">UTF-8</option>\
							<option value="gb18030">GB2312</option>\
						</select>\
						</span>\
						<button type="button" id="filesClose" autocomplete="off">'+ lan.public.close + '</button>\
						<ul id="up_box"></ul></div>'
            , end: function () {
                database.input_database(name);
            }
        });
        $("#filesClose").click(function () {
            layer.close(index);
            database.input_database(name);
        });
        UploadStart(true);
        */
    },
    input_database: function (name) {
        var path = bt.get_cookie('backup_path') + "/database";
        bt.send('get_files', 'files/GetDir', 'reverse=True&sort=mtime&tojs=GetFiles&p=1&showRow=100&path=' + path, function (rdata) {
            var data = [];
            for (var i = 0; i < rdata.FILES.length; i++) {
                if (rdata.FILES[i] == null) continue;
                var fmp = rdata.FILES[i].split(";");
                var ext = bt.get_file_ext(fmp[0]);
                if (ext != 'sql' && ext != 'zip' && ext != 'gz' && ext != 'tgz') continue;
                data.push({ name: fmp[0], size: fmp[1], etime: fmp[2], })
            }
            if ($('#DataInputList').length <= 0) {
                bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '600px',
                    title: lan.database.input_title_file+'['+name+']',
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: '<div class="pd15"><button class="btn btn-default btn-sm" onclick="database.upload_files(\'' + name + '\')">' + lan.database.input_local_up + '</button><div class="divtable mtb15" style="max-height:300px; overflow:auto">'
                        + '<table id="DataInputList" class="table table-hover"></table>'
                        + '</div>'
                        + bt.render_help([lan.database.input_ps1, lan.database.input_ps2, (bt.os != 'Linux' ? lan.database.input_ps3.replace(/\/www.*\/database/, path) : lan.database.input_ps3)])
                        + '</div>'
                });
            }
            setTimeout(function () {
                var _tab = bt.render({
                    table: '#DataInputList',
                    columns: [
                        { field: 'name', title: lan.files.file_name },
                        {
                            field: 'etime', title: lan.files.file_etime, templet: function (item) {
                                return bt.format_data(item.etime);
                            }
                        },
                        {
                            field: 'size', title: lan.files.file_size, templet: function (item) {
                                return bt.format_size(item.size)
                            }
                        },
                        {
                            field: 'opt', title: '操作', align: 'right', templet: function (item) {
                                return '<a class="btlink" herf="javascrpit:;" onclick="bt.database.input_sql(\'' + bt.rtrim(rdata.PATH, '/') + "/" + item.name + '\',\'' + name + '\')">导入</a>  | <a class="btlink" onclick="database.remove_input_file(\'' + bt.rtrim(rdata.PATH, '/') + "/" + item.name + '\',\'' + name + '\')">删除</a>';
                            }
                        },
                    ],
                    data: data
                });
            }, 100)
        })
    },
    remove_input_file: function (fileName,name) {
        layer.confirm(lan.get('recycle_bin_confirm', [fileName]), { title: lan.files.del_file, closeBtn: 2, icon: 3 }, function (index) {
            layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.post('/files?action=DeleteFile', 'path=' + encodeURIComponent(fileName), function (rdata) {
                layer.close(index);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                database.input_database(name);
            });
        });
    }
}
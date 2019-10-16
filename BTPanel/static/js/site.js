

var site = {
    get_list: function (page, search, type) {
        if (page == undefined) page = 1;
        if (type == '-1' || type == undefined) {
            type = $('.site_type select').val();
        }
        if (!search) search = $("#SearchValue").val();
        bt.site.get_list(page, search, type, function (rdata) {
            $('.dataTables_paginate').html(rdata.page);
                var data = rdata.data;
                var _tab = bt.render({
                    table: '#webBody',
                    columns: [
                        { field: 'id', type: 'checkbox', width: 30 },
                        {
                            field: 'name', title: '网站名', width: 150, templet: function (item) {
                                return '<a class="btlink webtips" onclick="site.web_edit(this)" href="javascript:;">' + item.name + '</a>';
                            }, sort: function () { site.get_list(); }
                        },
                        {
                            field: 'status', title: '状态', width: 98, templet: function (item) {
                                var _status = '<a href="javascript:;" ';
                                if (item.status == '1' || item.status == '正常' || item.status == '正在运行') {
                                    _status += ' onclick="bt.site.stop(' + item.id + ',\'' + item.name + '\') " >';
                                    _status += '<span style="color:#5CB85C">运行中 </span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>';
                                }
                                else {
                                    _status += ' onclick="bt.site.start(' + item.id + ',\'' + item.name + '\')"';
                                    _status += '<span style="color:red">已停止  </span><span style="color:red" class="glyphicon glyphicon-pause"></span>';
                                }
                                return _status;
                            }, sort: function () { site.get_list(); }
                        },
                        {
                            field: 'backup', title: '备份', width: 58, templet: function (item) {
                                var backup = lan.site.backup_no;
                                if (item.backup_count > 0) backup = lan.site.backup_yes;
                                return '<a href="javascript:;" class="btlink" onclick="site.site_detail(' + item.id + ',\'' + item.name + '\')">' + backup + '</a>';
                            }
                        },
                        {
                            field: 'path', title: '根目录', width: '26%', templet: function (item) {
                                var _path = bt.format_path(item.path);
                                return '<a class="btlink" title="打开目录" href="javascript:openPath(\'' + _path + '\');">' + _path + '</a>';
                            }
                        },
                        {
                            field: 'edate', title: '到期时间', width: 86, templet: function (item) {
                                var _endtime = '';
                                if (item.edate) _endtime = item.edate;
                                if (item.endtime) _endtime = item.endtime;
                                _endtime = (_endtime == "0000-00-00") ? lan.site.web_end_time : _endtime
                                return '<a class="btlink setTimes" id="site_endtime_' + item.id + '" >' + _endtime + '</a>';
                            },
                            sort: function () { site.get_list(); }
                        },
                        {
                            field: 'ps', title: '备注', templet: function (item) {
                                return "<span class='c9 input-edit'  onclick=\"bt.pub.set_data_by_key('sites','ps',this)\">" + item.ps + "</span>";
                            }
                        },

                        {
                            field: 'opt', width: 260, title: '操作', align: 'right', templet: function (item) {
                                var opt = '';
                                var _check = ' onclick="site.site_waf(\'' + item.name + '\')"';

                                if (bt.os == 'Linux') opt += '<a href="javascript:;" ' + _check + ' class="btlink ">防火墙</a> | ';
                                opt += '<a href="javascript:;" class="btlink" onclick="site.web_edit(this)">设置 </a> | ';
                                opt += '<a href="javascript:;" class="btlink" onclick="site.del_site(' + item.id + ',\'' + item.name + '\')" title="删除站点">删除</a>';
                                return opt;
                            }
                        },
                    ],
                    data: data
                })

                //设置到期时间
                $('a.setTimes').each(function () {
                    var _this = $(this);
                    var _tr = _this.parents('tr');
                    var id = _this.attr('id');
                    laydate.render({
                        elem: '#' + id //指定元素
                        , min: bt.get_date(1)
                        , max: '2099-12-31'
                        , vlue: bt.get_date(365)
                        , type: 'date'
                        , format: 'yyyy-MM-dd'
                        , trigger: 'click'
                        , btns: ['perpetual', 'confirm']
                        , theme: '#20a53a'
                        , done: function (dates) {
                            var item = _tr.data('item');
                            bt.site.set_endtime(item.id, dates, function () { })
                        }
                    });
                })
           //})
        });

    },
    site_waf: function (siteName) {
        try {
            site_waf_config(siteName);
        } catch (err) {
            site.no_firewall();
        }
        
    },
    html_encode: function (html) {
        var temp = document.createElement("div");
        //2.然后将要转换的字符串设置为这个元素的innerText(ie支持)或者textContent(火狐，google支持)
        (temp.textContent != undefined) ? (temp.textContent = html) : (temp.innerText = html);
        //3.最后返回这个元素的innerHTML，即得到经过HTML编码转换的字符串了
        var output = temp.innerHTML;
        temp = null;
        return output;
    },
    get_types: function (callback) {
        bt.site.get_type(function (rdata) {
            var optionList = '';
            for (var i = 0; i < rdata.length; i++) {
                optionList += '<option value="' + rdata[i].id + '">' + rdata[i].name + '</option>'
            }
            if($('.dataTables_paginate').next().hasClass('site_type')) $('.site_type').remove();
            $('.dataTables_paginate').after('<div class="site_type"><span>站点分类:</span><select class="bt-input-text mr5"  style="width:100px"><option value="-1">全部分类</option>' + optionList + '</select></div>');
            $('.site_type select').change(function () {
                var val = $(this).val();
                site.get_list(0, '', val);
                bt.set_cookie('site_type', val);
            })
            if(callback) callback(rdata);
        });
	},
    no_firewall: function (obj) {
        var typename = bt.get_cookie('serverType');
        layer.confirm(typename + '防火墙暂未开通，<br>请到&quot;<a href="/soft" class="btlink">软件管理>付费插件>' + typename + '防火墙</a>&quot;<br>开通安装使用。', {
            title: typename + '防火墙未开通', icon: 7, closeBtn: 2,
            cancel: function () {
                if (obj) $(obj).prop('checked', false)
            }
        }, function () {
            window.location.href = '/soft';
        }, function () {
            if (obj) $(obj).prop('checked', false)
        })
    },
    site_detail: function (id, siteName, page) {
        if (page == undefined) page = '1';
        var loadT = bt.load(lan.public.the_get);
        bt.pub.get_data('table=backup&search=' + id + '&limit=5&type=0&tojs=site.site_detail&p=' + page, function (frdata) {
            loadT.close();
            var ftpdown = '';
            var body = '';
            var port;
            frdata.page = frdata.page.replace(/'/g, '"').replace(/site.site_detail\(/g, "site.site_detail(" + id + ",'" + siteName + "',");
            if ($('#SiteBackupList').length <= 0) {
                bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '700px',
                    title: lan.site.backup_title,
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: "<div class='divtable pd15 style='padding-bottom: 0'><button id='btn_data_backup' class='btn btn-success btn-sm' type='button' style='margin-bottom:10px'>" + lan.database.backup + "</button><table width='100%' id='SiteBackupList' class='table table-hover'></table><div class='page sitebackup_page'></div></div>"
                });
            }
            setTimeout(function () {
                $('.sitebackup_page').html(frdata.page);
                var _tab = bt.render({
                    table: '#SiteBackupList',
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
                                var _opt = '<a class="btlink" href="/download?filename=' + item.filename + '&amp;name=' + item.name + '" target="_blank">下载</a> | ';
                                _opt += '<a class="btlink" herf="javascrpit:;" onclick="bt.site.del_backup(\'' + item.id + '\',\'' + id + '\',\'' + siteName + '\')">删除</a>'
                                return _opt;
                            }
                        },
                    ],
                    data: frdata.data
                });
                $('#btn_data_backup').unbind('click').click(function () {
                    bt.site.backup_data(id, function (rdata) {
                        if (rdata.status) site.site_detail(id, siteName);
                    })
                })
            }, 100)
        });
    },
    add_site: function () {
        bt.site.add_site(function (rdata) {
            if (rdata.siteStatus) {
                site.get_list();
                var html = '';
                var ftpData = '';
                if (rdata.ftpStatus) {
                    var list = [];
                    list.push({ title: lan.site.user, val: rdata.ftpUser });
                    list.push({ title: lan.site.password, val: rdata.ftpPass });
                    var item = {};
                    item.title = lan.site.ftp;
                    item.list = list;
                    ftpData = bt.render_ps(item);
                }
                var sqlData = '';
                if (rdata.databaseStatus) {
                    var list = [];
                    list.push({ title: lan.site.database_name, val: rdata.databaseUser });
                    list.push({ title: lan.site.user, val: rdata.databaseUser });
                    list.push({ title: lan.site.password, val: rdata.databasePass });
                    var item = {};
                    item.title = lan.site.database_txt;
                    item.list = list;
                    sqlData = bt.render_ps(item);
                }
                if (ftpData == '' && sqlData == '') {
                    bt.msg({ msg: lan.site.success_txt, icon: 1 })
                }
                else {
                    bt.open({
                        type: 1,
                        area: '600px',
                        title: lan.site.success_txt,
                        closeBtn: 2,
                        shadeClose: false,
                        content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + ftpData + sqlData + "</div></div>",
                    });

                    if ($(".success-msg").height() < 150) {
                        $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                    }
                }
            }
            else {
                bt.msg(rdata);
            }
        })
    },
    set_default_page: function () {
        bt.open({
            type: 1,
            area: '460px',
            title: lan.site.change_defalut_page,
            closeBtn: 2,
            shift: 0,
            content: '<div class="change-default pd20"><button  class="btn btn-default btn-sm ">' + lan.site.default_doc + '</button><button  class="btn btn-default btn-sm">' + lan.site.err_404 + '</button>	<button  class="btn btn-default btn-sm ">' + lan.site.empty_page + '</button><button  class="btn btn-default btn-sm ">' + lan.site.default_page_stop + '</button></div>'
        });
        setTimeout(function () {
            $('.change-default button').click(function () {
                bt.site.get_default_path($(this).index(), function (path) {
                    bt.pub.on_edit_file(0, path);
                })
            })
        }, 100)
    },
    set_default_site: function () {
        bt.site.get_default_site(function (rdata) {
            var arrs = [];
            arrs.push({title:"未设置默认站点",value:'0'})
            for (var i = 0; i < rdata.sites.length; i++) arrs.push({ title: rdata.sites[i].name, value: rdata.sites[i].name })
            var form = {
                title: lan.site.default_site_yes,
                area: '530px',
                list: [{ title: lan.site.default_site, name: 'defaultSite', width: '300px', value: rdata.defaultSite, type: 'select', items: arrs }],
                btns: [
                    bt.form.btn.close(),
                    bt.form.btn.submit('提交', function (rdata, load) {
                        bt.site.set_default_site(rdata.defaultSite, function (rdata) {
                            load.close();
                            bt.msg(rdata);
                        })
                    })
                ]
            }
            bt.render_form(form);
            $('.line').after($(bt.render_help([lan.site.default_site_help_1, lan.site.default_site_help_2])).addClass('plr20'));
        })
    },
    //PHP-CLI
    get_cli_version: function () {
        $.post('/config?action=get_cli_php_version', {}, function (rdata) {
            if (rdata.status === false) {
                layer.msg(rdata.msg, { icon: 2 });
                return;
            }
            var _options = '';
            for (var i = rdata.versions.length - 1; i >= 0; i--) {
                var ed = '';
                if (rdata.select.version == rdata.versions[i].version) ed = 'selected'
                _options += '<option value="' + rdata.versions[i].version + '" '+ed+'>' + rdata.versions[i].name + '</option>';
            }
            var body = '<div class="bt-form bt-form pd20 pb70">\
                <div class="line">\
                    <span class="tname">PHP-CLI版本</span>\
                    <div class="info-r ">\
                        <select class="bt-input-text mr5" name="php_version" style="width:300px">'+ _options + '</select>\
                    </div>\
                </div >\
                <ul class="help-info-text c7 plr20">\
                    <li>此处可设置命令行运行php时使用的PHP版本</li>\
                    <li>安装新的PHP版本后此处需要重新设置</li>\
                </ul>\
                <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger" onclick="layer.closeAll()">关闭</button><button type="button" class="btn btn-sm btn-success" onclick="site.set_cli_version()">提交</button></div></div>';

            layer.open({
                type: 1,
                title: "设置PHP-CLI(命令行)版本" ,
                area: '560px',
                closeBtn: 2,
                shadeClose: false,
                content: body
            });

        });

    },
    set_cli_version: function () {
        var php_version = $("select[name='php_version']").val();
        var loading = bt.load();
        $.post('/config?action=set_cli_php_version', { php_version: php_version }, function (rdata) {
            loading.close();
            if (rdata.status) {
                layer.closeAll();
            }
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        });
    },
    del_site: function (wid, wname) {
        var thtml = "<div class='options'><label><input type='checkbox' id='delftp' name='ftp'><span>FTP</span></label><label><input type='checkbox' id='deldata' name='data'><span>" + lan.site.database + "</span></label><label><input type='checkbox' id='delpath' name='path'><span>" + lan.site.root_dir + "</span></label></div>";
        bt.show_confirm(lan.site.site_del_title + "[" + wname + "]", lan.site.site_del_info, function () {
            var ftp = '', data = '', path = '';
            var data = { id: wid, webname: wname }
            if ($("#delftp").is(":checked")) data.ftp = 1;
            if ($("#deldata").is(":checked")) data.database = 1;
            if ($("#delpath").is(":checked")) data.path = 1;

            bt.site.del_site(data, function (rdata) {
                if (rdata.status) site.get_list();
                bt.msg(rdata);
            })

        }, thtml);
    },
    batch_site: function (type, obj, result) {
        if (obj == undefined) {
            obj = {};
            var arr = [];
            result = { count: 0, error_list: [] };
            $('input[type="checkbox"].check:checked').each(function () {
                var _val = $(this).val();
                if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
            })
            if (type == 'site_type') {
                bt.site.get_type(function (tdata) {
                    var types = [];
                    for (var i = 0; i < tdata.length; i++) types.push({ title: tdata[i].name, value: tdata[i].id })
                    var form = {
                        title: '设置站点分类',
                        area: '530px',
                        list: [{ title: lan.site.default_site, name: 'type_id', width: '300px', type: 'select', items: types }],
                        btns: [
                            bt.form.btn.close(),
                            bt.form.btn.submit('提交', function (rdata, load) {
                                var ids = []
                                for (var x = 0; x < arr.length; x++) ids.push(arr[x].id);
                                bt.site.set_site_type({ id: rdata.type_id, site_array: JSON.stringify(ids) }, function (rrdata) {
                                    if (rrdata.status) {
                                        load.close();
                                        site.get_list();
                                    }
                                    bt.msg(rrdata);
                                })
                            })
                        ]
                    }
                    bt.render_form(form);
                })
                return;
            }
            var thtml = "<div class='options'><label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>" + lan.site.all_del_info + "</span></label></div>";
            bt.show_confirm(lan.site.all_del_site, "<a style='color:red;'>" + lan.get('del_all_site', [arr.length]) + "</a>", function () {
                if ($("#delpath").is(":checked")) obj.path = '1';
                obj.data = arr;
                bt.closeAll();
                site.batch_site(type, obj, result);
            }, thtml);

            return;
        }
        var item = obj.data[0];
        switch (type) {
            case 'del':
                if (obj.data.length < 1) {
                    site.get_list();
                    bt.msg({ msg: lan.get('del_all_site_ok', [result.count]), icon: 1, time: 5000 });
                    return;
                }
                var data = { id: item.id, webname: item.name, path: obj.path }
                bt.site.del_site(data, function (rdata) {
                    if (rdata.status) {
                        result.count += 1;
                    } else {
                        result.error_list.push({ name: item.item, err_msg: rdata.msg });
                    }
                    obj.data.splice(0, 1)
                    site.batch_site(type, obj, result);
                })
                break;

        }
    },
    set_class_type: function () {
        var _form_data = bt.render_form_line({
            title: '',
            items: [
                { placeholder: '请填写分类名称', name: 'type_name', width: '50%', type: 'text' },
                {
                    name: 'btn_submit', text: '添加', type: 'button', callback: function (sdata) {
                        bt.site.add_type(sdata.type_name, function (ldata) {
                            if (ldata.status){
                                $('[name="type_name"]').val('');
                                site.get_class_type();
                            }
                            bt.msg(ldata);
                        })
                    }
                }
            ]
        });
        bt.open({
            type: 1,
            area: '350px',
            title: '网站分类管理',
            closeBtn: 2,
            shift: 5,
            shadeClose: true,
            content: "<div class='bt-form edit_site_type'><div class='divtable mtb15' style='overflow:auto'>" + _form_data.html + "<table id='type_table' class='table table-hover' width='100%'></table></div></div>",
            success:function(){
                bt.render_clicks(_form_data.clicks);
                site.get_class_type(function(res){
                    $('#type_table').on('click','.del_type',function(){
                        var _this = $(this);
                        var item = _this.parents('tr').data('item');
                        if (item.id == 0) {
                            bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
                            return;
                        }
                        bt.confirm({ msg: "是否确定删除分类？", title: '删除分类【'+ item.name +'】' }, function () {
                            bt.site.del_type(item.id, function (ret) {
                                if (ret.status) {
                                    site.get_class_type();
                                    bt.set_cookie('site_type', '-1');
                                }
                                bt.msg(ret);
                            })
                        })
                    });
                    $('#type_table').on('click','.edit_type',function(){
                        var item = $(this).parents('tr').data('item');
                        if (item.id == 0) {
                            bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
                            return;
                        }
                        bt.render_form({
                            title: '修改分类管理【' + item.name + '】',
                            area: '350px',
                            list: [{ title: '分类名称', width: '150px', name: 'name', value: item.name }],
                            btns: [
                                { title: '关闭', name: 'close' },
                                {
                                    title: '提交', 
                                    name: 'submit', 
                                    css: 'btn-success', 
                                    callback: function (rdata, load, callback) {
                                        bt.site.edit_type({ id: item.id, name: rdata.name }, function (edata) {
                                            if (edata.status) {
                                                load.close();
                                                site.get_class_type();
                                            }
                                            bt.msg(edata);
                                        })
                                    }
                                }
                            ]
                        });
                    });
                });
            }
        });
    },
    get_class_type: function(callback){
      site.get_types(function(rdata){
        bt.render({
          table: '#type_table',
          columns: [
            { field: 'name', title: '名称' },
            { field: 'opt', width: '80px', title: '操作', templet: function (item) { return '<a class="btlink edit_type" href="javascript:;">编辑</a> | <a class="btlink del_type" href="javascript:;">删除</a>'; } }
          ],
          data: rdata
        });
        $('.layui-layer-page').css({ 'margin-top':'-' + ($('.layui-layer-page').height() / 2) +'px','top':'50%' });
        if(callback) callback(rdata);
      });
  	},
    ssl: {
        my_ssl_msg : null,
        renew_ssl: function (siteName) {
            data = {}
            if (siteName != undefined) data = { siteName: siteName }
            var loadT = bt.load("正在一键续订证书.")
            bt.send("renew_lets_ssl", 'ssl/renew_lets_ssl', data, function (rdata) {
                loadT.close();
                if (rdata.status) {
                    if (siteName != undefined) {
                        if (rdata.err_list.length > 0) {
                            bt.msg({ status: false, msg: rdata.err_list[0].msg })
                        }
                        else {
                            site.reload();
                            bt.msg({ status: true, time: 6, msg: '网站【' + siteName + '】续订证书成功.' })
                        }
                    }
                    else {
                        var ehtml = '', shtml = ''

                        if (rdata.sucess_list.length > 0) {
                            var sucess = {};
                            sucess.title = "成功续签 " + rdata.sucess_list.length + " 张证书";
                            sucess.list = [{ title: "域名列表", val: rdata.sucess_list.join() }];
                            shtml = bt.render_ps(sucess);
                        }

                        if (rdata.err_list.length > 0) {
                            var error = {};
                            error.title = "续签失败 " + rdata.err_list.length + " 张证书";
                            error.list = []
                            for (var i = 0; i < rdata.err_list.length; i++) {
                                error.list.push({ title: rdata.err_list[i]['siteName'], val: rdata.err_list[i]['msg'] })
                            }
                            ehtml = bt.render_ps(error);
                        }

                        bt.open({
                            type: 1,
                            area: '600px',
                            title: "续签证书成功",
                            closeBtn: 2,
                            shadeClose: false,
                            content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + shtml + ehtml + "</div></div>",
                        });

                        if ($(".success-msg").height() < 150) {
                            $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                        }
                    }
                }
                else {
                    bt.msg(rdata)
                }
            })
        },
        get_renew_stat: function () {
            $.post('/ssl?action=Get_Renew_SSL', {}, function (task_list) {
                if (!task_list.status) return;
                var s_body = '';
                var b_stat = false;
                for (var i = 0; i < task_list.data.length; i++) {
                    s_body += '<p>' + task_list.data[i].subject + ' >> ' + task_list.data[i].msg + '</p>';
                    if (task_list.data[i].status !== true && task_list.data[i].status !== false) {
                        b_stat = true;
                    }
                }

                if (site.ssl.my_ssl_msg) {
                    $(".my-renew-ssl").html(s_body);
                } else {
                    site.ssl.my_ssl_msg = layer.msg('<div class="my-renew-ssl">' + s_body + '</div>', { time: 0 ,icon:16,shade:0.3});
                }
                
                if (!b_stat) {
                    setTimeout(function () {
                        layer.close(site.ssl.my_ssl_msg);
                        site.ssl.my_ssl_msg = null;
                    }, 3000);
                    return;
                }
                
                setTimeout(function () { site.ssl.get_renew_stat(); }, 1000);
                

            });
        },
        onekey_ssl: function (partnerOrderId, siteName) {
            bt.site.get_ssl_info(partnerOrderId, siteName, function (rdata) {
                bt.msg(rdata);
                if (rdata.status) site.reload(7);
            })
        },
        set_ssl_status: function (action, siteName) {
            bt.site.set_ssl_status(action, siteName, function (rdata) {
                bt.msg(rdata);
                if (rdata.status) {
                    site.reload(7);
                    if (action == 'CloseSSLConf') {
                        layer.msg(lan.site.ssl_close_info, { icon: 1, time: 5000 });
                    }
                }
            })
        },
        verify_domain: function (partnerOrderId, siteName) {
            bt.site.verify_domain(partnerOrderId, siteName, function (vdata) {
                bt.msg(vdata);
                if (vdata.status) {
                    if (vdata.data.stateCode == 'COMPLETED') {
                        site.ssl.onekey_ssl(partnerOrderId, siteName)
                    } else {
                        layer.msg('等待CA验证中，若长时间未能成功验证，请登录官网使用DNS方式重新申请...');
                    }
                    
                }
            })
        },
        reload: function (index) {
            if (index == undefined) index = 0
            var _sel = $('#ssl_tabs .on');
            if (_sel.length == 0) _sel = $('#ssl_tabs span:eq(0)');
            _sel.trigger('click');
        }
    },
    edit: {
        set_domains: function (web) {
            var _this = this;
            bt.site.get_domains(web.id, function (rdata) {
                var list = [
                    {
                        items: [
                            { name: 'newdomain', width: '340px', type: 'textarea', placeholder: '每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88' },
                            {
                                name: 'btn_submit_domain', text: '添加', type: 'button', callback: function (sdata) {
                                    var arrs = sdata.newdomain.split("\n");
                                    var domins = "";
                                    for (var i = 0; i < arrs.length; i++) domins += arrs[i] + ",";
                                    bt.site.add_domains(web.id, web.name, bt.rtrim(domins, ','), function (ret) {
                                        if (ret.status) site.reload(0)
                                    })
                                }
                            }
                        ]
                    }
                ]
                var _form_data = bt.render_form_line(list[0]);
                $('#webedit-con').html(_form_data.html + "<div class='divtable mtb15' style='height:350px;overflow:auto'><table id='domain_table' class='table table-hover' width='100%'></table></div>");
                bt.render_clicks(_form_data.clicks);
                $('.placeholder').css({ 'width':'340px', 'heigth':'100px','left': '0px', 'top': '0px',  'padding-top': '10px','padding-left': '15px'});
                $('.btn_submit_domain').addClass('pull-right').css("margin", "30px 35px 0 0")
                $(".placeholder").click(function () {
                    $(this).hide();
                    $('.newdomain').focus();
                })
                $('.domains').focus(function () { $(".placeholder").hide(); });
                $('.domains').blur(function () {
                    if ($(this).val().length == 0) $(".placeholder").show();
                });

                bt.render({
                    table: '#domain_table',
                    columns: [
                        { field: 'name', title: '域名', templet: function (item) { return "<a title='" + lan.site.click_access + "' target='_blank' href='http://" + item.name + ":" + item.port + "' class='btlinkbed'>" + item.name + "</a>" } },
                        { field: 'port', width: '70px', title: '端口' },
                        { field: 'opt', width: '50px', title: '操作', templet: function (item) { return '<a class="table-btn-del domain_del" href="javascript:;"><span class="glyphicon glyphicon-trash"></span></a>'; } }
                    ],
                    data: rdata
                })
                setTimeout(function () {
                    $('.domain_del').click(function () {
                        if ($(this).parents('tbody').find('tr').length == 1) {
                            bt.msg({ msg: lan.site.domain_last_cannot, icon: 2 });
                            return;
                        }
                        var item = $(this).parents('tr').data('item');
                        bt.confirm({title:'删除域名【'+ item.name +'】', msg: lan.site.domain_del_confirm }, function () {
                            bt.site.del_domain(web.id, web.name, item.name, item.port, function (ret) {
                                if (ret.status) site.reload(0)
                            })
                        })
                    })
                }, 100)
            })
        },
        set_dirbind: function (web) {
            var _this = this;
            bt.site.get_dirbind(web.id, function (rdata) {
                var dirs = [];
                for (var n = 0; n < rdata.dirs.length; n++) dirs.push({ title: rdata.dirs[n], value: rdata.dirs[n] });
                var data = {
                    title: '', items: [
                        { title: '域名', width: '140px', name: 'domain' },
                        { title: '子目录', name: 'dirName', type: 'select', items: dirs },
                        {
                            text: '添加', type: 'button', name: 'btn_add_subdir', callback: function (sdata) {
                                if (!sdata.domain || !sdata.dirName) {
                                    layer.msg(lan.site.d_s_empty, { icon: 2 });
                                    return;
                                }
                                bt.site.add_dirbind(web.id, sdata.domain, sdata.dirName, function (ret) {
                                    layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                    if (ret.status) site.reload(1)
                                })
                            }
                        }
                    ]
                }
                var _form_data = bt.render_form_line(data);
                $('#webedit-con').html(_form_data.html + '<div class="divtable mtb15" style="height:450px;overflow:auto"><table id="sub_dir_table" class="table table-hover" width="100%" style="margin-bottom:0"></table></div>');
                bt.render_clicks(_form_data.clicks);
                bt.render({
                    table: '#sub_dir_table',
                    columns: [
                        { field: 'domain', title: '域名' },
                        { field: 'port', width: '70px', title: '端口' },
                        { field: 'path', width: '100px', title: '子目录' },
                        {
                            field: 'opt', width: '100px', align: 'right', title: '操作', templet: function (item) {
                                return '<a class="btlink rewrite" href="javascript:;">伪静态</a> | <a class="btlink del" href="javascript:;">删除</a>';
                            }
                        }
                    ],
                    data: rdata.binding
                })
                setTimeout(function () {
                    $('#sub_dir_table td a').click(function () {
                        var item = $(this).parents('tr').data('item');
                        if ($(this).hasClass('del')) {
                            bt.confirm({ msg: lan.site.s_bin_del }, function () {
                                bt.site.del_dirbind(item.id, function (ret) {
                                    if (ret.status) site.reload(1)
                                })
                            })
                        } else {
                            bt.site.get_dir_rewrite({ id: item.id }, function (ret) {
                                if (!ret.status) {
                                    var confirmObj = layer.confirm(lan.site.url_rewrite_alter, { icon: 3, closeBtn: 2 }, function () {
                                        bt.site.get_dir_rewrite({ id: item.id, add: 1 }, function (ret) {
                                            layer.close(confirmObj);
                                            show_dir_rewrite(ret);
                                        });
                                    });
                                    return;
                                }
                                show_dir_rewrite(ret);

                                function show_dir_rewrite(ret) {
                                    var arrs = [];
                                    for (var i = 0; i < ret.rlist.length; i++) arrs.push({ title: ret.rlist[i], value: ret.rlist[i] });
                                    var datas = [{
                                        name: 'dir_rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                                            var spath = '/www/server/panel/rewrite/' + bt.get_cookie('serverType') + '/' + obj.val() + '.conf';
                                            bt.files.get_file_body(spath, function (sdata) {
                                                $('.dir_config').text(sdata.data);
                                            })
                                        }
                                    },
                                    { items: [{ name: 'dir_config', type: 'textarea', value: ret.data, width: '470px', height: '260px' }] },
                                    {
                                        items: [{
                                            name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                                                bt.files.set_file_body(ret.filename, ldata.dir_config, 'utf-8', function (sdata) {
                                                    if (sdata.status) load_form.close();
                                                    bt.msg(sdata);
                                                })
                                            }
                                        }]
                                    }]
                                    var load_form = bt.open({
                                        type: 1,
                                        area: '510px',
                                        title: lan.site.config_url,
                                        closeBtn: 2,
                                        shift: 5,
                                        skin: 'bt-w-con',
                                        shadeClose: true,
                                        content: "<div class='bt-form webedit-dir-box dir-rewrite-man-con'></div>"
                                    });

                                    setTimeout(function () {
                                        var _html = $(".webedit-dir-box")
                                        var clicks = [];
                                        for (var i = 0; i < datas.length; i++) {
                                            var _form_data = bt.render_form_line(datas[i]);
                                            _html.append(_form_data.html);
                                            var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
                                            _html.find('.info-r').append(_other)
                                            clicks = clicks.concat(_form_data.clicks);
                                        }
                                        _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
                                        bt.render_clicks(clicks);
                                    }, 100)
                                }
                            })
                        }
                    })
                }, 100)
            })
        },
        set_dirpath: function (web) {
            var loading = bt.load();
            bt.site.get_site_path(web.id, function (path) {
                bt.site.get_dir_userini(web.id, path, function (rdata) {
                    loading.close();
                    var dirs = [];
                    var is_n = false;
                    for (var n = 0; n < rdata.runPath.dirs.length; n++) {
                        dirs.push({ title: rdata.runPath.dirs[n], value: rdata.runPath.dirs[n] });
                        if (rdata.runPath.runPath === rdata.runPath.dirs[n]) is_n = true;
                    }
                    if (!is_n) dirs.push({ title: rdata.runPath.runPath, value: rdata.runPath.runPath });
                    var datas = [
                        {
                            title: '', items: [
                                {
                                    name: 'userini', type: 'checkbox', text: '防跨站攻击(open_basedir)', value: rdata.userini, callback: function (sdata) {
                                        bt.site.set_dir_userini(path, function (ret) {
                                            if (ret.status) site.reload(2)
                                            layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        })
                                    }
                                },
                                {
                                    name: 'logs', type: 'checkbox', text: '写访问日志', value: rdata.logs, callback: function (sdata) {
                                        bt.site.set_logs_status(web.id, function (ret) {
                                            if (ret.status) site.reload(2)
                                            layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        })
                                    }
                                }
                            ]
                        },
                        {
                            title: '', items: [
                                { name: 'path', title: '网站目录', width: '50%', value: path, event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
                                {
                                    name: 'btn_site_path', type: 'button', text: '保存', callback: function (pdata) {
                                        bt.site.set_site_path(web.id, pdata.path, function (ret) {
                                            if (ret.status) site.reload(2)
                                            layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        })
                                    }
                                }
                            ]
                        },
                        {
                            title: '', items: [
                                { title: '运行目录', width: '50%', value: rdata.runPath.runPath, name: 'dirName', type: 'select', items: dirs },
                                {
                                    name: 'btn_run_path', type: 'button', text: '保存', callback: function (pdata) {
                                        bt.site.set_site_runpath(web.id, pdata.dirName, function (ret) {
                                            if (ret.status) site.reload(2)
                                            layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        })
                                    }
                                }
                            ]
                        }
                    ]
                    var _html = $("<div class='webedit-box soft-man-con'></div>")
                    var clicks = [];
                    for (var i = 0; i < datas.length; i++) {
                        var _form_data = bt.render_form_line(datas[i]);
                        _html.append($(_form_data.html).addClass('line mtb10'));
                        clicks = clicks.concat(_form_data.clicks);
                    }
                    _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
                    _html.find('button[name="btn_run_path"]').addClass('ml45');
                    _html.find('button[name="btn_site_path"]').addClass('ml33');
                    _html.append(bt.render_help(['部分程序需要指定二级目录作为运行目录，如ThinkPHP5，Laravel', '选择您的运行目录，点保存即可']));
                    if (bt.os == 'Linux') _html.append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;"><span class="tit">密码访问</span><span class="btswitch-p"><input class="btswitch btswitch-ios" id="pathSafe" type="checkbox"><label class="btswitch-btn phpmyadmin-btn" for="pathSafe" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>')

                    $('#webedit-con').append(_html);
                    bt.render_clicks(clicks);
                    $('#pathSafe').click(function () {
                        var val = $(this).prop('checked');
                        var _div = $('.user_pw')
                        if (val) {
                            var dpwds = [
                                { title: '授权账号', width: '200px', name: 'username_get', placeholder: '不修改请留空' },
                                { title: '访问密码', width: '200px', type: 'password', name: 'password_get_1', placeholder: '不修改请留空' },
                                { title: '重复密码', width: '200px', type: 'password', name: 'password_get_2', placeholder: '不修改请留空' },
                                {
                                    name: 'btn_password_get', text: '保存', type: 'button', callback: function (rpwd) {
                                        if (rpwd.password_get_1 != rpwd.password_get_2) {
                                            layer.msg(lan.bt.pass_err_re, { icon: 2 });
                                            return;
                                        }
                                        bt.site.set_site_pwd(web.id, rpwd.username_get, rpwd.password_get_1, function (ret) {
                                            layer.msg(ret.msg, {icon:ret.status?1:2})
                                            if (ret.status) site.reload(2)
                                        })
                                    }
                                }
                            ]
                            for (var i = 0; i < dpwds.length; i++) {
                                var _from_pwd = bt.render_form_line(dpwds[i]);
                                _div.append("<div class='line'>" + _from_pwd.html + "</div>");
                                bt.render_clicks(_from_pwd.clicks);
                            }
                        } else {
                            bt.site.close_site_pwd(web.id, function (rdata) {
                                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                                _div.html('');
                            })
                        }
                    })
                    if (rdata.pass) $('#pathSafe').trigger('click');
                })
            })
        },
        set_dirguard: function(web){
        	String.prototype.myReplace = function (f, e) {//吧f替换成e
                var reg = new RegExp(f, "g"); //创建正则RegExp对象
                return this.replace(reg, e);
            }
        	bt.site.get_dir_auth(web.id,function(res) {
        		var datas = {
        			items: [{ name: 'add_dir_guard',text:'添加目录保护',type: 'button',callback: function(data){site.edit.template_Dir(web.id,true)}}]
        		}
        		var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="dir_guard" class="table table-hover"></table>');
                setTimeout(function() {
                	var data = [];
            		var _tab = bt.render({
                		table: '#dir_guard',
                		columns: [
                			{
                				field: 'name', title: '名称', template: function(item) {
                					return '<span style="width:60px;" title="'+ item.name +'">'+ item.name +'</span>'
                				}
                			},
                			{
                				field: 'site_dir', title: '保护的目录', template: function(item) {
                					return '<span style="width:60px;" title="'+ item.site_dir +'">'+ item.site_dir +'</span>'
                				}
                			},
                			{
                                field: 'dname', title: '操作', align: 'right', templet: function (item) {
                                var dirName = item.name
                                item = JSON.stringify(item).myReplace('"', '\'');
	                                var conter = '<a class="btlink" onclick="site.edit.template_Dir(\'' + web.id + '\',false,' + item + ')" href="javascript:;">编辑</a> ' +
	                                    '| <a class="btlink" onclick="bt.site.delete_dir_guard(\'' + web.id + '\',\'' + dirName + '\',function(rdata){if(rdata.status)site.reload()})" href="javascript:;">删除</a>';
	                                return conter
                            	}
                            }
                		],
                		data:res[web.name] || []
                	})

                })
        	});
        },
        limit_network: function (web) {
            bt.site.get_limitnet(web.id, function (rdata) {
                var limits = [
                    { title: '论坛/博客', value: 1, items: { perserver: 300, perip: 25, limit_rate: 512 } },
                    { title: '图片站', value: 2, items: { perserver: 200, perip: 10, limit_rate: 1024 } },
                    { title: '下载站', value: 3, items: { perserver: 50, perip: 3, limit_rate: 2048 } },
                    { title: '商城', value: 4, items: { perserver: 500, perip: 10, limit_rate: 2048 } },
                    { title: '门户', value: 5, items: { perserver: 400, perip: 15, limit_rate: 1024 } },
                    { title: '企业', value: 6, items: { perserver: 60, perip: 10, limit_rate: 512 } },
                    { title: '视频', value: 7, items: { perserver: 150, perip: 4, limit_rate: 1024 } }
                ]
                var datas = [
                    {
                        items: [{
                            name: 'status', type: 'checkbox', value: rdata.perserver != 0 ? true : false, text: '启用流量控制', callback: function (ldata) {
                                if (ldata.status) {
                                    bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
                                        layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        if (ret.status) site.reload(3)
                                    })
                                } else {
                                    bt.site.close_limitnet(web.id, function (ret) {
                                        layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                        if (ret.status) site.reload(3)
                                    })
                                }
                            }
                        }]
                    },
                    {
                        items: [{
                            title: '限制方案  ', width: '160px', name: 'limit', type: 'select', items: limits, callback: function (obj) {
                                var data = limits.filter(function (p) { return p.value === parseInt(obj.val()); })[0]
                                for (var key in data.items) $('input[name="' + key + '"]').val(data.items[key]);
                            }
                        }]
                    },
                    { items: [{ title: '并发限制   ', type: 'number', width: '200px', value: rdata.perserver, name: 'perserver' }] },
                    { items: [{ title: '单IP限制   ', type: 'number', width: '200px', value: rdata.perip, name: 'perip' }] },
                    { items: [{ title: '流量限制   ', type: 'number', width: '200px', value: rdata.limit_rate, name: 'limit_rate' }] },
                    {
                        name: 'btn_limit_get', text: '保存', type: 'button', callback: function (ldata) {
                            bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
                                layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                                if (ret.status) site.reload(3)
                            })
                        }
                    }
                ]
                var _html = $("<div class='webedit-box soft-man-con'></div>")
                var clicks = [];
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    _html.append(_form_data.html);
                    clicks = clicks.concat(_form_data.clicks);
                }
                _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
                _html.append(bt.render_help(['限制当前站点最大并发数', '限制单个IP访问最大并发数', '限制每个请求的流量上限（单位：KB）']));
                $('#webedit-con').append(_html);
                bt.render_clicks(clicks);
                if (rdata.perserver == 0) $("select[name='limit']").trigger("change")
            })
        },
        get_rewrite_list: function (web) {
            var filename = '/www/server/panel/vhost/rewrite/' + web.name + '.conf';
            
            bt.site.get_rewrite_list(web.name, function (rdata) {
                if (bt.get_cookie('serverType') == 'apache') filename = rdata.sitePath + '/.htaccess';
                var arrs = [];
                for (var i = 0; i < rdata.rewrite.length; i++) arrs.push({ title: rdata.rewrite[i], value: rdata.rewrite[i] });

                var datas = [{
                    name: 'rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                        if (bt.os == 'Linux') {
                            var spath = filename;
                            if (obj.val() != lan.site.rewritename) spath = '/www/server/panel/rewrite/' + bt.get_cookie('serverType') + '/' + obj.val() + '.conf';
                            bt.files.get_file_body(spath, function (ret) {
                                editor.setValue(ret.data);
                            })
                        }
                    }
                },
                { items: [{ name: 'config', type: 'textarea', value: rdata.data, widht: '340px', height: '200px' }] },
                {
                    items: [{
                        name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                            bt.files.set_file_body(filename, editor.getValue(), 'utf-8', function (ret) {
                                if (ret.status) site.reload(4)
                                bt.msg(ret);
                            })
                        }
                    },
                    {
                        name: 'btn_save_to', text: '另存为模板', type: 'button', callback: function (ldata) {
                            var temps = {
                                title: lan.site.save_rewrite_temp,
                                area: '330px',
                                list: [
                                    { title: '模板名称', placeholder: '模板名称', width: '160px', name: 'tempname' }
                                ],
                                btns: [
                                    { title: '关闭', name: 'close' },
                                    {
                                        title: '提交', name: 'submit', css: 'btn-success', callback: function (rdata, load, callback) {
                                            bt.site.set_rewrite_tel(rdata.tempname, editor.getValue(), function (rRet) {
                                                if (rRet.status) {
                                                    load.close();
                                                    site.reload(4)
                                                }
                                                bt.msg(rRet);
                                            })
                                        }
                                    }
                                ]
                            }
                            bt.render_form(temps);
                        }
                    }]
                }
                ]
                var _html = $("<div class='webedit-box soft-man-con'></div>")
                var clicks = [];
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    _html.append(_form_data.html);
                    var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
                    _html.find('.info-r').append(_other)
                    clicks = clicks.concat(_form_data.clicks);
                }
                _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
                $('#webedit-con').append(_html);
                bt.render_clicks(clicks);

                $('textarea.config').attr('id', 'config_rewrite');
                var editor = CodeMirror.fromTextArea(document.getElementById("config_rewrite"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true,
                });

                $(".CodeMirror-scroll").css({ "height": "340px", "margin": 0, "padding": 0 });
                $(".soft-man-con .CodeMirror").css({ "height": "342px" });
                setTimeout(function () {
                    editor.refresh();
                }, 250);

                $('select.rewrite').trigger('change')

                

            })
        },
        set_default_index: function (web) {
            bt.site.get_index(web.id, function (rdata) {
                rdata = rdata.replace(new RegExp(/(,)/g), "\n");
                var data = {
                    items: [
                        { name: 'Dindex', height: '230px', width: '50%', type: 'textarea', value: rdata },
                        {
                            name: 'btn_submit', text: '添加', type: 'button', callback: function (ddata) {
                                var Dindex = ddata.Dindex.replace(new RegExp(/(\n)/g), ",");
                                bt.site.set_index(web.id, Dindex, function (ret) {
                                    if (ret.status) site.reload(5)
                                })
                            }
                        }
                    ]
                }
                var _form_data = bt.render_form_line(data);
                var _html = $(_form_data.html)
                _html.append(bt.render_help([lan.site.default_doc_help]))
                $('#webedit-con').append(_html);
                $('.btn_submit').addClass('pull-right').css("margin", "90px 100px 0 0")
                bt.render_clicks(_form_data.clicks);
            })
        },
        set_config: function (web) {
            bt.site.get_site_config(web.name, function (rdata) {
                if (!rdata.status) {
                    bt.msg(rdata);
                    return;
                }
                var datas = [
                    { items: [{ name: 'site_config', type: 'textarea', value: rdata.data, widht: '340px', height: '200px' }] },
                    {
                        name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {
                            bt.site.set_site_config(web.name, editor.getValue(), rdata.encoding, function (ret) {
                                if (ret.status) site.reload(6)
                                bt.msg(ret);
                            })
                        }
                    }
                ]
                var robj = $('#webedit-con');
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                }
                robj.append(bt.render_help([lan.site.web_config_help]));
                $('textarea.site_config').attr('id', 'configBody');
                var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true,
                });
                $(".CodeMirror-scroll").css({ "height": "400px", "margin": 0, "padding": 0 });
            })
        },
        set_ssl: function (web) {
            $('#webedit-con').html("<div id='ssl_tabs'></div><div class=\"tab-con\" style=\"padding:10px 0px;\"></div>");
            bt.site.get_site_ssl(web.name, function (rdata) {
                var _tabs = [
                    {
                        title: '宝塔SSL', on: true, callback: function (robj) {
                            bt.pub.get_user_info(function (udata) {
                                if (udata.status) {
                                    bt.site.get_domains(web.id, function (ddata) {
                                        var domains = [];
                                        for (var i = 0; i < ddata.length; i++) {
                                            if (ddata[i].name.indexOf('*') == -1) domains.push({ title: ddata[i].name, value: ddata[i].name });
                                        }
                                        var arrs1 = [
                                            { title: '域名', width: '200px', name: 'domains', type: 'select', items: domains },
                                            {
                                                title: ' ', name: 'btsslApply', text: '申请', type: 'button', callback: function (sdata) {
                                                    if (sdata.domains.indexOf('www.') != -1) {
                                                        var rootDomain = sdata.domains.split(/www\./)[1];
                                                        if (!$.inArray(domains, rootDomain)) {
                                                            layer.msg('您为域名[' + sdata.domains + ']申请证书，但程序检测到您没有将其根域名[' + rootDomain + ']绑定并解析到站点，这会导致证书签发失败!', { icon: 2, time: 5000 });
                                                            return;
                                                        }
                                                    }
                                                    bt.site.get_dv_ssl(sdata.domains, web.path, function (tdata) {
                                                        bt.msg(tdata);
                                                        if (tdata.status) site.ssl.verify_domain(tdata.data.partnerOrderId, web.name);
                                                    })
                                                }
                                            }
                                        ]
                                        for (var i = 0; i < arrs1.length; i++) {
                                            var _form_data = bt.render_form_line(arrs1[i]);
                                            robj.append(_form_data.html);
                                            bt.render_clicks(_form_data.clicks);
                                        }
                                        var loading = bt.load()
                                        bt.site.get_order_list(web.name, function (odata) {
                                            loading.close();
                                            if (odata.status === false) {
                                                layer.msg(odata.msg, { icon: 2 });
                                                return;
                                            }
                                            robj.append("<div class=\"divtable mtb15 table-fixed-box\" style=\"max-height:200px;overflow-y: auto;\"><table id='bt_order_list' class='table table-hover'></table></div>");
                                            bt.render({
                                                table: '#bt_order_list',
                                                columns: [
                                                    { field: 'commonName', title: '域名' },
                                                    {
                                                        field: 'endtime', width: '70px', title: '到期时间', templet: function (item) {
                                                            return bt.format_data(item.endtime, 'yyyy/MM/dd');
                                                        }
                                                    },
                                                    { field: 'stateName', width: '100px', title: '状态' },
                                                    {
                                                        field: 'opt', align: 'right', width: '100px', title: '操作', templet: function (item) {
                                                            var opt = '<a class="btlink" onclick="site.ssl.onekey_ssl(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">部署</a>'
                                                            if (item.stateCode == 'WF_DOMAIN_APPROVAL') {
                                                                opt = '<a class="btlink" onclick="site.ssl.verify_domain(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">验证域名</a>';
                                                            }
                                                            else {
                                                                if (item.setup) opt = '已部署 | <a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\'' + web.name + '\')">关闭</a>'
                                                            }
                                                            return opt;
                                                        }
                                                    }
                                                ],
                                                data: odata.data
                                            })
                                            bt.fixed_table('bt_order_list');
                                            var helps = [
                                                '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
                                                '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
                                                '有效期1年，不支持续签，到期后需要重新申请',
                                                '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
                                                '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                                '<a style="color:red;">如果重新申请证书时提示【订单已存在】请登录宝塔官网删除对应SSL订单</a>',
                                                '<a style="color:red;">如果您的站点有使用CDN、高防IP、反向代理、301重定向等功能，可能导致验证失败</a>',
                                                '<a style="color:red;">申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</a>',
                                            ]
                                            robj.append(bt.render_help(helps));
                                        })
                                    })
                                }
                                else {
                                    robj.append('<div class="alert alert-warning" style="padding:10px">未绑定宝塔账号，请注册绑定，绑定宝塔账号(非论坛账号)可实现一键部署SSL</div>');

                                    var datas = [
                                        { title: '宝塔账号', name: 'bt_username', value: rdata.email, width: '260px', placeholder: '请输入手机号码' },
                                        { title: '密码', type: 'password', name: 'bt_password', value: rdata.email, width: '260px' },
                                        {
                                            title: ' ', items: [
                                                {
                                                    text: '登录', name: 'btn_ssl_login', type: 'button', callback: function (sdata) {
                                                        bt.pub.login_btname(sdata.bt_username, sdata.bt_password, function (ret) {
                                                            if (ret.status) site.reload(7);
                                                        })
                                                    }
                                                },
                                                {
                                                    text: '注册宝塔账号', name: 'bt_register', type: 'button', callback: function (sdata) {
                                                        window.open('https://www.bt.cn/register.html')
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                    for (var i = 0; i < datas.length; i++) {
                                        var _form_data = bt.render_form_line(datas[i]);
                                        robj.append(_form_data.html);
                                        bt.render_clicks(_form_data.clicks);
                                    }
                                    robj.append(bt.render_help(['宝塔SSL证书为亚洲诚信证书，需要实名认证才能申请使用', '已有宝塔账号请登录绑定', '宝塔SSL申请的是TrustAsia DV SSL CA - G5 原价：1900元/1年，宝塔用户免费！', '一年满期后免费颁发']));
                                }
                            })

                        }
                    },
                    {
                        title: "Let's Encrypt", callback: function (robj) {
                            if (rdata.status && rdata.type == 1) {
                                var cert_info = '';
                                if (rdata.cert_data['notBefore']) {
                                    cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;"><b>已部署成功：</b>将在距离到期时间1个月内尝试自动续签</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 140px;width: 140px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer+'</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
                                }
                                robj.append('<div>' + cert_info + '<div><span>密钥(KEY)</span><span style="padding-left:194px">证书(PEM格式)</span></div></div>');
                                var datas = [
                                    {
                                        items: [
                                            { name: 'key', width: '45%', height: '220px', type: 'textarea', value: rdata.key },
                                            { name: 'csr', width: '45%', height: '220px', type: 'textarea', value: rdata.csr }
                                        ]
                                    },
                                    {
                                        items: [
                                            {
                                                text: '关闭SSL', name: 'btn_ssl_close', hide: !rdata.status, type: 'button', callback: function (sdata) {
                                                    site.ssl.set_ssl_status('CloseSSLConf', web.name);
                                                }
                                            },
                                            {
                                                text: '续签', name: 'btn_ssl_renew', hide: !rdata.status, type: 'button', callback: function (sdata) {
                                                    site.ssl.renew_ssl();
                                                }
                                            }
                                        ]
                                    }
                                ]
                                for (var i = 0; i < datas.length; i++) {
                                    var _form_data = bt.render_form_line(datas[i]);
                                    robj.append(_form_data.html);
                                    bt.render_clicks(_form_data.clicks);
                                }
                                robj.find('textarea').css('background-color', '#f6f6f6').attr('readonly', true);
                                var helps = [
                                    '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
                                    '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
                                    '有效期1年，不支持续签，到期后需要重新申请',
                                    '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                    '如果重新申请证书时提示【订单已存在】请登录宝塔官网删除对应SSL订单',
                                ]
                                robj.append(bt.render_help(['已为您自动生成Let\'s Encrypt免费证书；', '如需使用其他SSL,请切换其他证书后粘贴您的KEY以及PEM内容，然后保存即可。']));
                                return;
                            }
                            bt.site.get_site_domains(web.id, function (ddata) {
                                var helps = [[
                                    '申请之前，请确保域名已解析，如未解析会导致审核失败',
                                    'Let\'s Encrypt免费证书，有效期3个月，支持多域名。默认会自动续签',
                                    '若您的站点使用了CDN或301重定向会导致续签失败',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点'
                                ], [
                                    '在DNS验证中，我们提供了3个自动化DNS-API，并提供了手动模式',
                                    '使用DNS接口申请证书可自动续期，手动模式下证书到期后手需重新申请',
                                    '使用【DnsPod/阿里云DNS】接口前您需要先在弹出的窗口中设置对应接口的API'
                                ]]
                                var datas = [
                                    {
                                        title: '验证方式', items: [
                                            {
                                                name: 'check_file', text: '文件验证', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove()
                                                    $(obj).siblings().removeAttr('checked');

                                                    $('.help-info-text').html($(bt.render_help(helps[0])));
                                                    var _form_data = bt.render_form_line({ title: ' ', class: 'checks_line label-input-group', items: [{ name: 'force', type: 'checkbox', value: true, text: '提前校验域名(提前发现问题,减少失败率)' }] });
                                                    $(obj).parents('.line').append(_form_data.html);

                                                    $('#ymlist li input[type="checkbox"]').each(function () {
                                                        if ($(this).val().indexOf('*') >= 0) {
                                                            $(this).parents('li').hide();
                                                        }
                                                    })
                                                }
                                            },
                                            {
                                                name: 'check_dns', text: 'DNS验证', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove();
                                                    $(obj).siblings().removeAttr('checked');
                                                    $('.help-info-text').html($(bt.render_help(helps[1])));
                                                    $('#ymlist li').show();

                                                    var arrs_list = [], arr_obj = {};
                                                    bt.site.get_dns_api(function (api) {
                                                        for (var x = 0; x < api.length; x++) {
                                                            arrs_list.push({ title: api[x].title, value: api[x].name });
                                                            arr_obj[api[x].name] = api[x];
                                                        }
                                                        var data = [{
                                                            title: '选择DNS接口', class: 'checks_line', items: [
                                                                {
                                                                    name: 'dns_select', width: '120px', type: 'select', items: arrs_list, callback: function (obj) {
                                                                        var _val = obj.val();
                                                                        $('.set_dns_config').remove();
                                                                        var _val_obj = arr_obj[_val];
                                                                        var _form = {
                                                                            title: '',
                                                                            area: '530px',
                                                                            list: [],
                                                                            btns: [{ title: '关闭', name: 'close' }]
                                                                        };

                                                                        var helps = [];
                                                                        if (_val_obj.data !== false) {
                                                                            _form.title = '设置【' + _val_obj.title + '】接口';
                                                                            helps.push(_val_obj.help);
                                                                            var is_hide = true;
                                                                            for (var i = 0; i < _val_obj.data.length; i++) {
                                                                                _form.list.push({ title: _val_obj.data[i].name, name: _val_obj.data[i].key, value: _val_obj.data[i].value })
                                                                                if (!_val_obj.data[i].value) is_hide = false;
                                                                            }
                                                                            _form.btns.push({
                                                                                title: '保存', css: 'btn-success', name: 'btn_submit_save', callback: function (ldata, load) {
                                                                                    bt.site.set_dns_api({ pdata: JSON.stringify(ldata) }, function (ret) {
                                                                                        if (ret.status) {
                                                                                            load.close();
                                                                                            robj.find('input[type="radio"]:eq(0)').trigger('click')
                                                                                            robj.find('input[type="radio"]:eq(1)').trigger('click')
                                                                                        }
                                                                                        bt.msg(ret);
                                                                                    })
                                                                                }
                                                                            })
                                                                            if (is_hide) {
                                                                                obj.after('<button class="btn btn-default btn-sm mr5 set_dns_config">设置</button>');
                                                                                $('.set_dns_config').click(function () {
                                                                                    var _bs = bt.render_form(_form);
                                                                                    $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                                                                })
                                                                            } else {
                                                                                var _bs = bt.render_form(_form);
                                                                                $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                                                            }
                                                                        }
                                                                    }
                                                                },
                                                            ]
                                                        }
                                                            , {
                                                                title: ' ', class: 'checks_line label-input-group', items:
                                                                    [
                                                                        { css: 'label-input-group ptb10', text: '自动组合泛域名', name: 'app_root', type: 'checkbox' }
                                                                    ]
                                                            }
                                                       ]
                                                        for (var i = 0; i < data.length; i++) {
                                                            var _form_data = bt.render_form_line(data[i]);
                                                            $(obj).parents('.line').append(_form_data.html)
                                                            bt.render_clicks(_form_data.clicks);
                                                        }
                                                    })
                                                }
                                            },
                                        ]
                                    },
                                    { title: '管理员邮箱', name: 'admin_email', value: rdata.email, width: '260px' }
                                ]

                                for (var i = 0; i < datas.length; i++) {
                                    var _form_data = bt.render_form_line(datas[i]);
                                    robj.append(_form_data.html);
                                    bt.render_clicks(_form_data.clicks);
                                }
                                var _ul = $('<ul id="ymlist" class="domain-ul-list"></ul>');
                                for (var i = 0; i < ddata.domains.length; i++) {
                                    if (ddata.domains[i].binding === true) continue
                                    _ul.append('<li style="cursor: pointer;"><input class="checkbox-text" type="checkbox" value="' + ddata.domains[i].name + '">' + ddata.domains[i].name + '</li>');
                                }
                                var _line = $("<div class='line mtb10'></div>");
                                _line.append('<span class="tname text-center">域名</span>');
                                _line.append(_ul);
                                robj.append(_line);
                                robj.find('input[type="radio"]').parent().addClass('label-input-group ptb10');
                                $("#ymlist li input").click(function (e) {
                                    e.stopPropagation();
                                })
                                $("#ymlist li").click(function () {

                                    var o = $(this).find("input");
                                    if (o.prop("checked")) {
                                        o.prop("checked", false)
                                    }
                                    else {
                                        o.prop("checked", true);
                                    }
                                })
                                var _btn_data = bt.render_form_line({
                                    title: ' ', text: '申请', name: 'letsApply', type: 'button', callback: function (ldata) {
                                        ldata['domains'] = [];
                                        $('#ymlist input[type="checkbox"]:checked').each(function () {
                                            ldata['domains'].push($(this).val())
                                        })
                                        var ddata = {
                                            siteName: web.name,
                                            email: ldata.admin_email,
                                            updateOf: 1,
                                            domains: JSON.stringify(ldata['domains'])
                                        }
                                        if (ddata.email.indexOf('@') === -1) {
                                            layer.msg('管理员邮箱不能为空!', {icon:2});
                                            return;
                                        }

                                        if (ldata.check_file) {
                                            ddata['force'] = ldata.force;
                                            site.create_let(ddata, function (res) {
                                                if (res.status === true) {
                                                    site.reload();
                                                } else {
                                                    var area_size = '500px';
                                                    console.log(res.msg[1])
                                                    var err_info = "";
                                                    if (res.msg[1].status === 'invalid') {
                                                        area_size = '600px';
                                                        var check_url = "http://" + res.msg[1].identifier.value + '/.well-known/acme-challenge/' + res.msg[1].challenges[0].token
                                                        err_info += "<p><span>验证域名:</span>" + res.msg[1].identifier.value + "</p>"
                                                        err_info += "<p><span>验证URL:</span><a class='btlink' href='" + check_url+"' target='_blank'>点击查看</a></p>"
                                                        err_info += "<p><span>验证内容:</span>" + res.msg[1].challenges[0].token + "</p>"
                                                        err_info += "<p><span>验证结果:</span> <a style='color:red;'>验证失败</a></p>"
                                                        err_info += "<p><span>错误代码:</span>" + site.html_encode(res.msg[1].challenges[0].error.detail) + "</p>"
                                                    }
                                                    
                                                    layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + res.msg[0]+ '</a>' + err_info + '</div>', {
                                                        icon: 2, time: 0,
                                                        shade:0.3,
                                                        shadeClose: true,
                                                        area: area_size
                                                    });
                                                }

                                            });
                                        }
                                        else {
                                            ddata['dnsapi'] = ldata.dns_select;
                                            ddata['dnssleep'] = ldata.dnssleep;
                                            ddata['app_root'] = ldata.app_root ? 1 : 0;
                                            site.create_let(ddata, function (ret) {
                                                if (ldata.dns_select == 'dns') {
                                                    if (ret.key) {
                                                        site.reload();
                                                        bt.msg(ret);
                                                        return;
                                                    }
                                                    var b_load = bt.open({
                                                        type: 1,
                                                        area: '700px',
                                                        title: '手动解析TXT记录',
                                                        closeBtn: 2,
                                                        shift: 5,
                                                        shadeClose: false,
                                                        content: "<div class='divtable pd15 div_txt_jx'><p class='mb15' >请按以下列表做TXT解析:</p><table id='dns_txt_jx' class='table table-hover'></table><div class='text-right mt10'><button class='btn btn-success btn-sm btn_check_txt' >验证</button></div></div>"
                                                    });
                                                    setTimeout(function () {
                                                        var data = [];
                                                        for (var j = 0; j < ret.dns_names.length; j++) data.push({ name: ret.dns_names[j].acme_name, txt: ret.dns_names[j].domain_dns_value });
                                                        bt.render({
                                                            table: '#dns_txt_jx',
                                                            columns: [
                                                                { field: 'name', width: '220px', title: '解析域名' },
                                                                { field: 'txt', title: 'TXT记录值' },
                                                            ],
                                                            data: data
                                                        })
                                                        if (ret.dns_names.length == 0) ret.dns_names.append('_acme-challenge.bt.cn')
                                                        $('.div_txt_jx').append(bt.render_help(['解析域名需要一定时间来生效,完成所以上所有解析操作后,请等待1分钟后再点击验证按钮', '可通过CMD命令来手动验证域名解析是否生效: nslookup -q=txt ' + ret.dns_names[0].acme_name, '若您使用的是宝塔云解析插件,阿里云DNS,DnsPod作为DNS,可使用DNS接口自动解析']));

                                                        $('.btn_check_txt').click(function () {
                                                            var new_data = {
                                                                siteName: web.name,
                                                                domains: ddata.domains,
                                                                updateOf: 1,
                                                                email: ldata.email,
                                                                renew: 'True',
                                                                dnsapi:'dns'
                                                            }
                                                            site.create_let(new_data, function (ldata) {
                                                                if (ldata.status) {
                                                                    b_load.close();
                                                                    site.ssl.reload(1);
                                                                } else {
                                                                    var area_size = '500px';
                                                                    var err_info = "";

                                                                    if (!new_data.msg[1].challenges[1]) {
                                                                        if (new_data.msg[1].challenges[0]) {
                                                                            new_data.msg[1].challenges[1] = new_data.msg[1].challenges[0]
                                                                        }
                                                                    }

                                                                    if (ldata.msg[1].status === 'invalid') {
                                                                        area_size = '600px';
                                                                        var trs = $("#dns_txt_jx tbody tr");
                                                                        var dns_value = "";
                                                                        for (var imd = 0; imd < trs.length; imd++) {
                                                                            if (trs[imd].outerText.indexOf(ldata.msg[1].identifier.value) == -1) continue;
                                                                            var s_tmp = trs[imd].outerText.split("\t")
                                                                            if (s_tmp.length > 1) {
                                                                                dns_value = s_tmp[1]
                                                                                break;
                                                                            }
                                                                        }
                                                                        var check_url = "_acme-challenge." + ldata.msg[1].identifier.value
                                                                        err_info += "<p><span>验证域名:</span>" + ldata.msg[1].identifier.value + "</p>"
                                                                        err_info += "<p><span>验证解析:</span>"+check_url+"</p>"
                                                                        err_info += "<p><span>验证内容:</span>" + dns_value + "</p>"
                                                                        err_info += "<p><span>验证结果:</span> <a style='color:red;'>验证失败</a></p>"
                                                                        err_info += "<p><span>错误代码:</span>" + site.html_encode(ldata.msg[1].challenges[1].error.detail) + "</p>"
                                                                    }

                                                                    layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + ldata.msg[0] + '</a>' + err_info + '</div>', {
                                                                        icon: 2, time: 0,
                                                                        shade: 0.3,
                                                                        shadeClose: true,
                                                                        area: area_size
                                                                    });
                                                                }
                                                            });
                                                        })
                                                    }, 100)
                                                }
                                                else {
                                                    if (ret.status) {
                                                        site.reload();
                                                        bt.msg(ret);
                                                    } else {
                                                        if (!ret.msg[1].challenges[1]) {
                                                            if (ret.msg[1].challenges[0]) {
                                                                ret.msg[1].challenges[1] = ret.msg[1].challenges[0]
                                                            }
                                                        }
                                                        var area_size = '500px';
                                                        var err_info = "";

                                                        if (ret.msg[1].status === 'invalid') {
                                                            area_size = '600px';
                                                            var check_url = "_acme-challenge." + ret.msg[1].identifier.value
                                                            err_info += "<p><span>验证域名:</span>" + ret.msg[1].identifier.value + "</p>"
                                                            err_info += "<p><span>验证解析:</span>" + check_url + "</p>"
                                                            err_info += "<p><span>验证结果:</span> <a style='color:red;'>验证失败</a></p>"
                                                            err_info += "<p><span>错误代码:</span>" + site.html_encode(ret.msg[1].challenges[1].error.detail) + "</p>"
                                                        }

                                                        layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + ret.msg[0] + '</a>' + err_info + '</div>', {
                                                            icon: 2, time: 0,
                                                            shade: 0.3,
                                                            shadeClose: true,
                                                            area: area_size
                                                        });
                                                    }

                                                    
                                                }
                                            })
                                        }
                                    }
                                });
                                robj.append(_btn_data.html);
                                bt.render_clicks(_btn_data.clicks);

                                robj.append(bt.render_help(helps[0]));
                                robj.find('input[type="radio"]:eq(0)').trigger('click')
                            })
                        }
                    },
                    {
                        title: "其他证书", callback: function (robj) {
                            var cert_info = '';
                            if (rdata.cert_data['notBefore']) {
                                cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;">'+ (rdata.status ? '<b>已部署成功：</b>请在证书到期之前更换新的证书' :'<b style="color:red;">当前未部署：</b>请点击【保存】按钮完成此证书的部署')+'</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 138px;width: 140px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
                            }
                            robj.append('<div>' + cert_info+'<div><span>密钥(KEY)</span><span style="padding-left:194px">证书(PEM格式)</span></div></div>');
                            var datas = [
                                {
                                    items: [
                                        { name: 'key', width: '45%', height: '220px', type: 'textarea', value: rdata.key },
                                        { name: 'csr', width: '45%', height: '220px', type: 'textarea', value: rdata.csr }
                                    ]
                                },
                                {
                                    items: [
                                        {
                                            text: '保存', name: 'btn_ssl_save', type: 'button', callback: function (sdata) {
                                                bt.site.set_ssl(web.name, sdata, function (ret) {
                                                    if (ret.status) site.reload(7);
                                                    bt.msg(ret);
                                                })
                                            }
                                        },
                                        {
                                            text: '关闭SSL', name: 'btn_ssl_close', hide: !rdata.status, type: 'button', callback: function (sdata) {
                                                site.ssl.set_ssl_status('CloseSSLConf', web.name);
                                            }
                                        }
                                    ]
                                }
                            ]
                            for (var i = 0; i < datas.length; i++) {
                                var _form_data = bt.render_form_line(datas[i]);
                                robj.append(_form_data.html);
                                bt.render_clicks(_form_data.clicks);
                            }
                            var helps = [
                                '粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。',
                                '如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书',
                                'PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt',
                                '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                            ]
                            robj.append(bt.render_help(helps));

                        }
                    },
                    {
                        title: "关闭", callback: function (robj) {
                            if (rdata.type == -1) {
                                robj.html("<div class='mtb15' style='line-height:30px'>" + lan.site.ssl_help_1 + "</div>");
                                return;
                            };
                            var txt = '';
                            switch (rdata.type) {
                                case 1:
                                    txt = "Let's Encrypt";
                                    break;
                                case 0:
                                    txt = '其他证书';
                                    break;
                                case 2:
                                    txt = lan.site.bt_ssl;
                                    break;
                            }
                            $(".tab-con").html("<div class='line mtb15'>" + lan.get('ssl_enable', [txt]) + "</div><div class='line mtb15'><button class='btn btn-success btn-sm' onclick=\"site.ssl.set_ssl_status('CloseSSLConf','" + web.name + "')\">" + lan.site.ssl_close + "</button></div>");

                        }
                    },
                    {
                        title: "证书夹", callback: function (robj) {
                            robj.html("<div class='divtable' style='height:510px;'><table id='cer_list_table' class='table table-hover'></table></div>");
                            bt.site.get_cer_list(function (rdata) {
                                bt.render({
                                    table: '#cer_list_table',
                                    columns: [
                                        {
                                            field: 'subject', title: '域名', templet: function (item) {
                                                return item.dns.join('<br>')
                                            }
                                        },
                                        { field: 'notAfter', width: '83px', title: '到期时间' },
                                        { field: 'issuer', width: '150px', title: '品牌' },
                                        {
                                            field: 'opt', width: '75px', align: 'right', title: '操作', templet: function (item) {
                                                var opt = '<a class="btlink" onclick="bt.site.set_cert_ssl(\'' + item.subject + '\',\'' + web.name + '\',function(rdata){if(rdata.status){site.ssl.reload(2);}})" href="javascript:;">部署</a> | ';
                                                opt += '<a class="btlink" onclick="bt.site.remove_cert_ssl(\'' + item.subject + '\',function(rdata){if(rdata.status){site.ssl.reload(4);}})" href="javascript:;">删除</a>'
                                                return opt;
                                            }
                                        }
                                    ],
                                    data: rdata
                                })
                            })
                        }
                    }
                ]
                bt.render_tab('ssl_tabs', _tabs);
                $('#ssl_tabs').append('<div class="ss-text pull-right mr30" style="position: relative;top:-4px"><em>强制HTTPS</em><div class="ssh-item"><input class="btswitch btswitch-ios" id="toHttps" type="checkbox"><label class="btswitch-btn" for="toHttps"></label></div></div>');
                $("#toHttps").attr('checked', rdata.httpTohttps);
                $('#toHttps').click(function (sdata) {
                    var isHttps = $("#toHttps").attr('checked');
                    if (isHttps) {
                        layer.confirm('关闭强制HTTPS后需要清空浏览器缓存才能看到效果,继续吗?', { icon: 3, title: "关闭强制HTTPS" }, function () {
                            bt.site.close_http_to_https(web.name, function (rdata) {
                                if (rdata.status) {
                                    setTimeout(function () {
                                        site.reload(7);
                                    }, 3000);
                                }
                            })
                        });
                    }
                    else {
                        bt.site.set_http_to_https(web.name, function (rdata) {
                            if (!rdata.status) {
                                setTimeout(function () {
                                    site.reload(7);
                                }, 3000);
                            }
                            
                        })
                    }
                })
                switch (rdata.type) {
                    case 1:
                        $('#ssl_tabs span:eq(1)').trigger('click');
                        break;
                    case 0:
                        $('#ssl_tabs span:eq(2)').trigger('click');
                        break;
                    default:
                        $('#ssl_tabs span:eq(0)').trigger('click');
                        break;
                }

            })
        },
        set_php_version: function (web) {
            bt.site.get_site_phpversion(web.name, function (sdata) {
                if (sdata.status === false) {
                    bt.msg(sdata);
                    return;
                }
                bt.site.get_all_phpversion(function (vdata) {
                    var versions = [];
                    for (var j = vdata.length - 1; j >= 0; j--) {
                        var o = vdata[j];
                        o.value = o.version;
                        o.title = o.name;
                        versions.push(o);
                    }
                    var data = {
                        items: [
                            { title: 'PHP版本', name: 'versions', value: sdata.phpversion, type: 'select', items: versions },
                            {
                                text: '切换', name: 'btn_change_phpversion', type: 'button', callback: function (pdata) {
                                    bt.site.set_phpversion(web.name, pdata.versions, function (ret) {
                                        if (ret.status) site.reload(8)
                                        bt.msg(ret);
                                    })
                                }
                            }
                        ]
                    }
                    var _form_data = bt.render_form_line(data);
                    var _html = $(_form_data.html);
                    _html.append(bt.render_help(['请根据您的程序需求选择版本', '若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；', 'PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo。']));
                    $('#webedit-con').append(_html);
                    bt.render_clicks(_form_data.clicks);
                    $('#webedit-con').append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;border-top: #ccc 1px dashed;"><span class="tit">session隔离</span><span class="btswitch-p"style="display: inline-flex;"><input class="btswitch btswitch-ios" id="session_switch" type="checkbox"><label class="btswitch-btn session-btn" for="session_switch" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>'
                        + bt.render_help(['开启后将会把session文件存放到独立文件夹独立文件夹，不与其他站点公用存储位置','若您在PHP配置中将session保存到memcache/redis等缓存器时，请不要开启此选项']));
                    function get_session_status(){
                    	var loading = bt.load('正在获取session状态请稍后');
                    	bt.send('get_php_session_path','config/get_php_session_path',{id:web.id},function(tdata){
							loading.close();
							$('#session_switch').prop("checked",tdata);
						})
                    };
                    get_session_status()
                    $('#session_switch').click(function() {
                        var val = $(this).prop('checked');
                        bt.send('set_php_session_path','config/set_php_session_path',{id:web.id,act:val? 1:0},function(rdata){
                        	bt.msg(rdata)
                        })
                        setTimeout(function () {
	                        get_session_status();
	                    }, 500)
                    })
                })
            })
        },
        templet_301: function (sitename, id, types, obj) {
            if (types) {
                obj = {
                    redirectname:(new Date()).valueOf(),
                    tourl: 'http://',
                    redirectdomain: [],
                    redirectpath: '',
                    redirecttype: '',
                    type: 1,
                    domainorpath: 'domain',
                    holdpath: 1
                }
            }
            var helps = [
                '重定向类型：表示访问选择的“域名”或输入的“路径”时将会重定向到指定URL',
                '目标URL：可以填写你需要重定向到的站点，目标URL必须为可正常访问的URL，否则将返回错误',
                '重定向方式：使用301表示永久重定向，使用302表示临时重定向',
                '保留URI参数：表示重定向后访问的URL是否带有子路径或参数如设置访问http://b.com 重定向到http://a.com',
                '保留URI参数：  http://b.com/1.html ---> http://a.com/1.html',
                '不保留URI参数：http://b.com/1.html ---> http://a.com'
            ];
            bt.site.get_domains(id, function (rdata) {
                var domain_html = ''
                for (var i = 0; i < rdata.length; i++) {
                    domain_html += '<option value="' + rdata[i].name + '">' + rdata[i].name + '</option>';
                }
                var form_redirect = bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '650px',
                    title: types ? '创建重定向' : '修改重定向[' + obj.redirectname + ']',
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: "<form id='form_redirect' class='divtable pd20' style='padding-bottom: 60px'>" +
                        "<div class='line' style='overflow:hidden;height: 40px;'>" +
                        "<span class='tname' style='position: relative;top: -5px;'>开启重定向</span>" +
                        "<div class='info-r  ml0 mt5' >" +
                        "<input class='btswitch btswitch-ios' id='type' type='checkbox' name='type' " + (obj.type == 1 ? 'checked="checked"' : '') + " /><label class='btswitch-btn phpmyadmin-btn' for='type' style='float:left'></label>" +
                        "<div style='display: inline-block;'>" +
                        "<span class='tname' style='margin-left:10px;position: relative;top: -5px;'>保留URI参数</span>" +
                        "<input class='btswitch btswitch-ios' id='holdpath' type='checkbox' name='holdpath' " + (obj.holdpath == 1 ? 'checked="checked"' : '') + " /><label class='btswitch-btn phpmyadmin-btn' for='holdpath' style='float:left'></label>" +
                        "</div>" +
                        "</div>" +
                        "</div>" +
                        "<div class='line' style='clear:both;display:none;'>" +
                        "<span class='tname'>重定向名称</span>" +
                        "<div class='info-r  ml0'><input name='redirectname' class='bt-input-text mr5' " + (types ? '' : 'disabled="disabled"') + " type='text' style='width:300px' value='" + obj.redirectname + "'></div>" +
                        "</div>" +
                        "<div class='line' style='clear:both;'>" +
                        "<span class='tname'>重定向类型</span>" +
                        "<div class='info-r  ml0'>" +
                        "<select class='bt-input-text mr5' name='domainorpath' style='width:100px'><option value='domain' " + (obj.domainorpath == 'domain' ? 'selected ="selected"' : "") + ">域名</option><option value='path'  " + (obj.domainorpath == 'path' ? 'selected ="selected"' : "") + ">路径</option></select>" +
                        "<span class='mlr15'>重定向方式</span>" +
                        "<select class='bt-input-text ml10' name='redirecttype' style='width:100px'><option value='301' " + (obj.redirecttype == '301' ? 'selected ="selected"' : "") + " >301</option><option value='302' " + (obj.redirecttype == '302' ? 'selected ="selected"' : "") + ">302</option></select></div>" +
                        "</div>" +
                        "<div class='line redirectdomain' style='display:" + (obj.domainorpath == 'domain' ? 'block' : 'none') + "'>" +
                        "<span class='tname'>重定向域名</span>" +
                        "<div class='info-r  ml0'>" +
                        "<select id='usertype' name='redirectdomain' data-actions-box='true' class='selectpicker show-tick form-control' multiple data-live-search='false'>" + domain_html + "</select>" +
                        "<span class='tname' style='width:90px'>目标URL</span>" +
                        "<input  name='tourl' class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.tourl + "'>" +
                        "</div>" +
                        "</div>" +
                        "<div class='line redirectpath' style='display:" + (obj.domainorpath == 'path' ? 'block' : 'none') + "'>" +
                        "<span class='tname'>重定向路径</span>" +
                        "<div class='info-r  ml0'>" +
                        "<input  name='redirectpath' class='bt-input-text mr5' type='text' style='width:200px;float: left;margin-right:0px' value='" + obj.redirectpath + "'>" +
                        "<span class='tname' style='width:90px'>目标URL</span>" +
                        "<input  name='tourl1' class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.tourl + "'>" +
                        "</div>" +
                        "</div>" +
                        "<ul class='help-info-text c7'>" + bt.render_help(helps) + '</ul>' +
                        "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-redirect'>" + (types ? " 提交" : "保存") + "</button></div>" +
                        "</form>"
                });
                setTimeout(function () {
                    $('.selectpicker').selectpicker({
                        'noneSelectedText': '请选择域名...',
                        'selectAllText': '全选',
                        'deselectAllText': '取消全选'
                    });
                    $('.selectpicker').selectpicker('val', obj.redirectdomain);
                    $('#form_redirect').parent().css('overflow', 'inherit');
                    $('[name="domainorpath"]').change(function () {
                        if ($(this).val() == 'path') {
                            $('.redirectpath').show();
                            $('.redirectdomain').hide();
                            $('.selectpicker').selectpicker('val', []);
                        } else {
                            $('.redirectpath').hide();
                            $('.redirectdomain').show();
                            $('[name="redirectpath"]').val('')
                        }
                    });
                    $('.btn-colse-prosy').click(function () {
                        form_redirect.close();
                    });
                    $('.btn-submit-redirect').click(function () {
                        var type = $('[name="type"]').prop('checked') ? 1 : 0;
                        var holdpath = $('[name="holdpath"]').prop('checked') ? 1 : 0;
                        var redirectname = $('[name="redirectname"]').val();
                        var redirecttype = $('[name="redirecttype"]').val();
                        var domainorpath = $('[name="domainorpath"]').val();
                        var redirectpath = $('[name="redirectpath"]').val();
                        var redirectdomain = JSON.stringify($('.selectpicker').val() || []);
                        var tourl = $(domainorpath == 'path' ? '[name="tourl1"]' : '[name="tourl"]').val();
                        if (!types) {
                            bt.site.modify_redirect({
                                type: type,
                                sitename: sitename,
                                holdpath: holdpath,
                                redirectname: redirectname,
                                redirecttype: redirecttype,
                                domainorpath: domainorpath,
                                redirectpath: redirectpath,
                                redirectdomain: redirectdomain,
                                tourl: tourl
                            }, function (rdata) {
                                if (rdata.status) {
                                    form_redirect.close();
                                    site.reload(11);
                                }
                                bt.msg(rdata);
                            });
                        } else {
                            bt.site.create_redirect({
                                type: type,
                                sitename: sitename,
                                holdpath: holdpath,
                                redirectname: redirectname,
                                redirecttype: redirecttype,
                                domainorpath: domainorpath,
                                redirectpath: redirectpath,
                                redirectdomain: redirectdomain,
                                tourl: tourl
                            }, function (rdata) {
                                if (rdata.status) {
                                    form_redirect.close();
                                    site.reload(11);
                                }
                                bt.msg(rdata);
                            });
                        }
                    });
                }, 100);
            });

        },
        template_Dir: function(id,type,obj){
        	if(type){
        		obj = {"name":"","sitedir": "", "username":"","password":""};
        	}else{
        		obj = {"name":obj.name,"sitedir": obj.site_dir, "username":"","password":""};
        	}
        	var form_directory = bt.open({
        		type: 1,
        		skin: 'demo-class',
        		area: '550px',
        		title: type ? '添加目录保护' : '修改目录目录',
        		closeBtn:  2,
        		shift: 5,
        		shadeClose: false,
        		content: "<form id='form_dir' class='divtable pd15' style='padding: 40px 0 90px 60px'>" +
        			"<div class='line'>" +
                    "<span class='tname'>名称</span>" +
                    "<div class='info-r ml0'><input name='dir_name' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.name + "'>" +
                    "</div></div>" +
        			"<div class='line'>" +
                    "<span class='tname'>保护的目录</span>" +
                    "<div class='info-r ml0'><input name='dir_sitedir' placeholder='输入需要保护的目录，如：/text/' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.sitedir + "'>" +
                    "</div></div>" +
        			"<div class='line'>" +
                    "<span class='tname'>用户名</span>" +
                    "<div class='info-r ml0'><input name='dir_username' AUTOCOMPLETE='off' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.username + "'>" +
                    "</div></div>" +
        			"<div class='line'>" +
                    "<span class='tname'>密码</span>" +
                    "<div class='info-r ml0'><input name='dir_password' AUTOCOMPLETE='off' class='bt-input-text mr10' type='password' style='width:270px' value='" + obj.password + "'>" +
                    "</div></div>"+
                    "<ul class='help-info-text c7 plr20'>"+
                        "<li>目录设置保护后，访问时需要输入账号密码才能访问</li>"+
                        "<li>例如我设置了保护目录 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>"+
                    "</ul>"+
                    "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-guard'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-guard'>" + (type ? '提交' : '保存') + "</button></div></form>"
        	});
        	$('.btn-colse-guard').click(function () {
                form_directory.close();
            });
            $('.btn-submit-guard').click(function() {
            	var guardData = {};
            	guardData['id'] = id;
            	guardData['name'] = $('input[name="dir_name"]').val();
            	guardData['site_dir'] = $('input[name="dir_sitedir"]').val();
            	guardData['username'] = $('input[name="dir_username"]').val();
            	guardData['password'] = $('input[name="dir_password"]').val();
            	if(type){
            		bt.site.create_dir_guard(guardData, function (rdata) {
                        if (rdata.status) {
                            form_directory.close();
                        	site.reload()
                        }
                        bt.msg(rdata);
                    });
            	}else{
            		bt.site.edit_dir_account(guardData, function (rdata) {
                        if (rdata.status) {
                            form_directory.close();
                        	site.reload()
                        }
                        bt.msg(rdata);
                    });
            	}
            });
        	setTimeout(function(){
        		if(!type){
        			$('input[name="dir_name"]').attr('disabled', 'disabled');
        			$('input[name="dir_sitedir"]').attr('disabled', 'disabled');
        		}
        	},500)

        },
        set_301_old:function(web){				
            bt.site.get_domains(web.id,function(rdata){							
                var domains = [{title:'整站',value:'all'}];
                for(var i=0;i<rdata.length;i++) domains.push({title:rdata[i].name,value:rdata[i].name});
                
                bt.site.get_site_301(web.name,function(pdata){
                    var _val = pdata.src==''?'all':pdata.src
                    var datas = [
                        {title:'访问域名',width:'360px',name:'domains',value:_val,disabled:pdata.status,type:'select',items:domains},
                        {title:'目标URL',width:'360px',name:'toUrl',value:pdata.url},	
                        {title:' ', text:'启用301',value:pdata.status,name:'status',class:'label-input-group',type:'checkbox',callback:function(sdata){								
                            bt.site.set_site_301(web.name,sdata.domains,sdata.toUrl,sdata.status?'1':'0',function(ret){
                                if(ret.status) site.reload(10)
                                bt.msg(ret);
                            })
                        }},
                    ]
                    var robj = $('#webedit-con');
                    for(var i=0;i<datas.length;i++){
                        var _form_data = bt.render_form_line(datas[i]);							
                        robj.append(_form_data.html);	
                        bt.render_clicks(_form_data.clicks);
                    }					
                    robj.append(bt.render_help(['选择[整站]时请不要将目标URL设为同一站点下的域名.','取消301重定向后，需清空浏览器缓存才能看到生效结果.']));
                })					
            })				
        },
        set_301: function (web) {
            bt.site.get_redirect_list(web.name, function (rdata) {
                var datas = {
                    items: [{ name: 'add_proxy', text: '添加重定向', type: 'button', callback: function (data) { site.edit.templet_301(web.name, web.id, true) } }]
                }
                var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="proxy_list" class="table table-hover"></table>');
                setTimeout(function () {
                    var _tab = bt.render({
                        table: '#proxy_list',
                        columns: [
                            // { field: 'redirectname', title: '名称' },
                            {
                                field: '', title: '重定向类型', templet: function (item) {
                                    var conter = '';
                                    if (item.domainorpath == 'path') {
                                        conter = item.redirectpath;
                                    } else {
                                        conter = item.redirectdomain ? item.redirectdomain.join('、') : '空'
                                    }
                                    return '<span style="width:100px;" title="' + conter + '">' + conter + '</span>';
                                }
                            },
                            { field: 'redirecttype', title: '重定向方式' },
                            {
                                field: 'holdpath', index: true, title: '保留URI参数', templet: function (item) {
                                    return '<a href="javascript:;" class="btlink set_path_state" style="display:" data-stuats="' + (item.holdpath == 1 ? 0 : 1) + '">' + (item.holdpath == 1 ? '<span style="color:#20a53a;" class="set_path_state">开启</span>' : '<span style="color:red;" class="set_path_state">关闭</span>') + '</a>';
                                }
                            },
                            {
                                field: 'type', title: '状态', index: true, templet: function (item) {
                                    return '<a href="javascript:;" class="btlink set_type_state" style="display:" data-stuats="' + (item.type == 1 ? 0 : 1) + '">' + (item.type == 1 ? '<span style="color:#20a53a;">运行中</span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>' : '<span style="color:red;">已暂停</span><span style="color:red" class="glyphicon glyphicon-pause"></span>') + '</a>'
                                }
                            },
                            {
                                field: '', title: '操作', align: 'right', index: true, templet: function (item) {
                                    var redirectname = item.redirectname;
                                    var sitename = item.sitename;
                                    var conter = '<a class="btlink open_config_file" href="javascript:;">配置文件</a> ' +
                                        '| <a class="btlink edit_redirect"  href="javascript:;">编辑</a> ' +
                                        '| <a class="btlink" onclick="bt.site.remove_redirect(\'' + sitename + '\',\'' + redirectname + '\',function(rdata){if(rdata.status)site.reload(11)})" href="javascript:;">删除</a>';
                                    return conter
                                }
                            }
                        ],
                        data: rdata
                    });

                    $('.edit_redirect').click(function () {
                        var index = parseInt($(this).parent().attr('data-index'));
                        site.edit.templet_301(web.name, web.id, false, rdata[index]);
                    });
                    $('.open_config_file').click(function () {
                        var index = $(this).parent().attr('data-index');
                        var sitename = web.name;
                        var redirectname = rdata[index].redirectname;
                        var redirect_config = '';
                        bt.site.get_redirect_config({
                            sitename: sitename,
                            redirectname: redirectname,
                            webserver: bt.get_cookie('serverType')
                        }, function (rdata) {
                            if (typeof rdata == 'object' && rdata.constructor == Array) {
                                if (!rdata[0].status) bt.msg(rdata)
                            } else {
                                if (!rdata.status) bt.msg(rdata)
                            }
                            var datas = [
                                { items: [{ name: 'redirect_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                                {
                                    name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {
                                        bt.site.save_redirect_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                                            if (ret.status) {
                                                site.reload(11);
                                                redirect_config.close();
                                            }
                                            bt.msg(ret);
                                        })
                                    }
                                }
                            ]
                            redirect_config = bt.open({
                                type: 1,
                                area: ['550px', '550px'],
                                title: '编辑配置文件[' + redirectname + ']',
                                closeBtn: 2,
                                shift: 0,
                                content: "<div class='bt-form'><div id='redirect_config_con' class='pd15'></div></div>"
                            })
                            var robj = $('#redirect_config_con');
                            for (var i = 0; i < datas.length; i++) {
                                var _form_data = bt.render_form_line(datas[i]);
                                robj.append(_form_data.html);
                                bt.render_clicks(_form_data.clicks);
                            }
                            robj.append(bt.render_help(['此处为该负载均衡的配置文件，若您不了解配置规则,请勿随意修改。']));
                            $('textarea.redirect_configs').attr('id', 'configBody');
                            var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                                extraKeys: { "Ctrl-Space": "autocomplete" },
                                lineNumbers: true,
                                matchBrackets: true
                            });
                            $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                            setTimeout(function () {
                                editor.refresh();
                            }, 250);
                        });
                    });
                    $('.set_path_state').click(function () {
                        type_edit_redirect($(this), 'holdpath')
                    });
                    $('.set_type_state').click(function () {
                        type_edit_redirect($(this), 'type');
                    });
                    function type_edit_redirect(_this, type) {
                        var index = _this.parent().attr('data-index');
                        var status = _this.attr('data-stuats');
                        var item = rdata[index];
                        item[type] = status;
                        item['redirectdomain'] = JSON.stringify(item['redirectdomain']);
                        // item['redirectdomain'] = JSON.stringify(['redirectdomain']);
                        bt.site.modify_redirect(item, function (res) {
                            if (res.status) site.reload(11);
                            bt.msg(res);
                        });
                    }
                }, 100);
            });
        },
        templet_proxy: function (sitename, type, obj) {
            if (type) {
                obj = { "type": 1, "cache": 0, "proxyname": "", "proxydir": "/", "proxysite": "http://", "cachetime": 1, "todomain": "$host", "subfilter": [{ "sub1": "", "sub2": "" }] };
            }
            var sub_conter = '';
            for (var i = 0; i < obj.subfilter.length; i++) {
                if (i == 0 || obj.subfilter[i]['sub1'] != '') {
                    sub_conter += "<div class='sub-groud'>" +
                        "<input name='rep" + ((i + 1) * 2 - 1) + "' class='bt-input-text mr10' placeholder='被替换的文本,可留空' type='text' style='width:200px' value='" + obj.subfilter[i]['sub1'] + "'>" +
                        "<input name='rep" + ((i + 1) * 2) + "' class='bt-input-text ml10' placeholder='替换为,可留空' type='text' style='width:200px' value='" + obj.subfilter[i]['sub2'] + "'>" +
                        "<a href='javascript:;' class='proxy_del_sub' style='color:red;'>删除</a>" +
                        "</div>";
                }
                if (i == 2) $('.add-replace-prosy').attr('disabled', 'disabled')
            }
            var helps = [
                '代理目录：访问这个目录时将会把目标URL的内容返回并显示(需要开启高级功能)',
                '目标URL：可以填写你需要代理的站点，目标URL必须为可正常访问的URL，否则将返回错误',
                '发送域名：将域名添加到请求头传递到代理服务器，默认为目标URL域名，若设置不当可能导致代理无法正常运行',
                '内容替换：只能在使用nginx时提供，最多可以添加3条替换内容,如果不需要替换请留空'
            ];
            var form_proxy = bt.open({
                type: 1,
                skin: 'demo-class',
                area: '650px',
                title: type ? '创建反向代理' : '修改反向代理[' + obj.proxyname + ']',
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: "<form id='form_proxy' class='divtable pd15' style='padding-bottom: 60px'>" +
                    "<div class='line' style='overflow:hidden'>" +
                    "<span class='tname' style='position: relative;top: -5px;'>开启代理</span>" +
                    "<div class='info-r  ml0 mt5' >" +
                    "<input class='btswitch btswitch-ios' id='openVpn' type='checkbox' name='type' " + (obj.type == 1 ? 'checked="checked"' : '') + "><label class='btswitch-btn phpmyadmin-btn' for='openVpn' style='float:left'></label>" +
                    "<div style='display:" + (bt.get_cookie('serverType') == 'nginx' ? ' inline-block' : 'none') + "'>" +
                    "<span class='tname' style='margin-left:15px;position: relative;top: -5px;'>开启缓存</span>" +
                    "<input class='btswitch btswitch-ios' id='openNginx' type='checkbox' name='cache' " + (obj.cache == 1 ? 'checked="checked"' : '') + "'><label class='btswitch-btn phpmyadmin-btn' for='openNginx'></label>" +
                    "</div>" +
                    "<div style='display: inline-block;'>" +
                    "<span class='tname' style='margin-left:10px;position: relative;top: -5px;'>高级功能</span>" +
                    "<input class='btswitch btswitch-ios' id='openAdvanced' type='checkbox' name='advanced' " + (obj.advanced == 1 ? 'checked="checked"' : '') + "'><label class='btswitch-btn phpmyadmin-btn' for='openAdvanced'></label>" +
                    "</div>" +
                    "</div>" +
                    "</div>" +
                    "<div class='line' style='clear:both;'>" +
                    "<span class='tname'>代理名称</span>" +
                    "<div class='info-r  ml0'><input name='proxyname'" + (type ? "" : "readonly='readonly'") + " class='bt-input-text mr5 " + (type ? "" : " disabled") + "' type='text' style='width:200px' value='" + obj.proxyname + "'></div>" +
                    "</div>" +
                    "<div class='line cachetime' style='display:" + (obj.cache == 1 ? 'block' : 'none') + "'>" +
                    "<span class='tname'>缓存时间</span>" +
                    "<div class='info-r  ml0'><input name='cachetime'class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.cachetime + "'>分钟</div>" +
                    "</div>" +
                    "<div class='line advanced'  style='display:" + (obj.advanced == 1 ? 'block' : 'none') + "'>" +
                    "<span class='tname'>代理目录</span>" +
                    "<div class='info-r  ml0'><input id='proxydir' name='proxydir' class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.proxydir + "'>" +
                    "</div>" +
                    "</div>" +
                    "<div class='line'>" +
                    "<span class='tname'>目标URL</span>" +
                    "<div class='info-r  ml0'>" +
                    "<input name='proxysite' class='bt-input-text mr10' type='text' style='width:200px' value='" + obj.proxysite + "'>" +
                    "<span class='mlr15'>发送域名</span><input name='todomain' class='bt-input-text ml10' type='text' style='width:200px' value='" + obj.todomain + "'>" +
                    "</div>" +
                    "</div>" +
                    "<div class='line replace_conter' style='display:" + (bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') + "'>" +
                    "<span class='tname'>内容替换</span>" +
                    "<div class='info-r  ml0 '>" + sub_conter + "</div>" +
                    "</div>" +
                    "<div class='line' style='display:" + (bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') + "'>" +
                    "<div class='info-r  ml0'>" +
                    "<button class='btn btn-success btn-sm btn-title add-replace-prosy' type='button'><span class='glyphicon cursor glyphicon-plus  mr5' ></span>添加内容替换</button>" +
                    "</div>" +
                    "</div>" +
                    "<ul class='help-info-text c7'>" + bt.render_help(helps) +
                    "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-prosy'>" + (type ? " 提交" : "保存") + "</button></div>" +
                    "</form>"
            });
            bt.set_cookie('form_proxy', form_proxy);
            $('.add-replace-prosy').click(function () {
                var length = $(".replace_conter .sub-groud").length;
                if (length == 2) $(this).attr('disabled', 'disabled')
                var conter = "<div class='sub-groud'>" +
                    "<input name='rep" + (length * 2 + 1) + "' class='bt-input-text mr10' placeholder='被替换的文本,可留空' type='text' style='width:200px' value=''>" +
                    "<input name='rep" + (length * 2 + 2) + "' class='bt-input-text ml10' placeholder='替换为,可留空' type='text' style='width:200px' value=''>" +
                    "<a href='javascript:;' class='proxy_del_sub' style='color:red;'>删除</a>" +
                    "</div>"
                $(".replace_conter .info-r").append(conter);
            });
            $('[name="proxysite"]').keyup(function () {
                var val = $(this).val(),ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
                val = val.replace(/^http[s]?:\/\//, '');
				val = val.replace(/:([0-9]*)$/,'');
				if(ip_reg.test(val)){
                	 $("[name='todomain']").val('$host');
				}else{
					 $("[name='todomain']").val(val);
				}
            });
            $('#openAdvanced').click(function () {
                if ($(this).prop('checked')) {
                    $('.advanced').show();
                } else {
                    $('.advanced').hide();
                }
            });
            $('#openNginx').click(function () {
                if ($(this).prop('checked')) {
                    $('.cachetime').show();
                } else {
                    $('.cachetime').hide();
                }
            });
            $('.btn-colse-prosy').click(function () {
                form_proxy.close();
            });
            $('.replace_conter').on('click', '.proxy_del_sub', function () {
                $(this).parent().remove();
                $('.add-replace-prosy').removeAttr('disabled')
            });
            $(".btn-submit-prosy").click(function () {
                var form_proxy_data = {};
                $.each($('#form_proxy').serializeArray(), function () {
                    if (form_proxy_data[this.name]) {
                        if (!form_proxy_data[this.name].push) {
                            form_proxy_data[this.name] = [form_proxy_data[this.name]];
                        }
                        form_proxy_data[this.name].push(this.value || '');
                    } else {
                        form_proxy_data[this.name] = this.value || '';
                    }
                });
                form_proxy_data['type'] = (form_proxy_data['type'] == undefined ? 0 : 1);
                form_proxy_data['cache'] = (form_proxy_data['cache'] == undefined ? 0 : 1);
                form_proxy_data['advanced'] = (form_proxy_data['advanced'] == undefined ? 0 : 1);
                form_proxy_data['sitename'] = sitename;
                form_proxy_data['subfilter'] = JSON.stringify([
                    { 'sub1': form_proxy_data['rep1'] || '', 'sub2': form_proxy_data['rep2'] || '' },
                    { 'sub1': form_proxy_data['rep3'] || '', 'sub2': form_proxy_data['rep4'] || '' },
                    { 'sub1': form_proxy_data['rep5'] || '', 'sub2': form_proxy_data['rep6'] || '' },
                ]);
                for (var i in form_proxy_data) {
                    if (i.indexOf('rep') != -1) {
                        delete form_proxy_data[i];
                    }
                }
                if (type) {
                    bt.site.create_proxy(form_proxy_data, function (rdata) {
                        if (rdata.status) {
                            form_proxy.close();
                            site.reload(12);
                        }
                        bt.msg(rdata);
                    });
                } else {
                    bt.site.modify_proxy(form_proxy_data, function (rdata) {
                        if (rdata.status) {
                            form_proxy.close();
                            site.reload(12);
                        }
                        bt.msg(rdata);
                    });
                }
            });
        },
        set_proxy: function (web) {
            String.prototype.myReplace = function (f, e) {//吧f替换成e
                var reg = new RegExp(f, "g"); //创建正则RegExp对象   
                return this.replace(reg, e);
            }
            bt.site.get_proxy_list(web.name, function (rdata) {
                var datas = {
                    items: [{ name: 'add_proxy', text: '添加反向代理', type: 'button', callback: function (data) { site.edit.templet_proxy(web.name, true) } }]
                }
                var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="proxy_list" class="table table-hover"></table>');
                setTimeout(function () {
                    var _tab = bt.render({
                        table: '#proxy_list',
                        columns: [
                            {
                                field: 'proxyname', title: '名称', templet: function (item) {
                                    return '<span style="width:60px;" title="' + item.proxyname + '">' + item.proxyname + '</span>'
                                }
                            },
                            {
                                field: 'proxydir', title: '代理目录', templet: function (item) {
                                    return '<span style="width:60px;" title="' + item.proxydir + '">' + item.proxydir + '</span>'
                                }
                            },
                            {
                                field: 'proxysite', title: '目标url', templet: function (item) {
                                    return '<span style="width:130px;" title="' + item.proxysite + '">' + item.proxysite + '</span>'
                                }
                            },
                            bt.get_cookie('serverType') == 'nginx' ? {
                                field: 'cache', title: '缓存', index: true, templet: function (item, index) {
                                    return '<a href="javascript:;" class="btlink set_nginx_state" data-stuats="' + (item.cache == 1 ? 0 : 1) + '">' + (item.cache == 1 ? '<span style="color:#20a53a;">已开启</span>' : '<span style="color:red;">已关闭</span>') + '</a>'
                                }
                            } : '',
                            {
                                field: 'type', title: '状态', index: true, templet: function (item) {
                                    return '<a href="javascript:;" class="btlink set_type_state" style="display:" data-stuats="' + (item.type == 1 ? 0 : 1) + '">' + (item.type == 1 ? '<span style="color:#20a53a;">运行中</span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>' : '<span style="color:red;">已暂停</span><span style="color:red" class="glyphicon glyphicon-pause"></span>') + '</a>'
                                }
                            },
                            {
                                field: 'dname', title: '操作', align: 'right', templet: function (item) {
                                    var proxyname = item.proxyname;
                                    var sitename = item.sitename;
                                    item = JSON.stringify(item).myReplace('"', '\'');
                                    var conter = '<a class="btlink open_config_file" data-name="' + sitename + '" data-proxyname="' + proxyname + '" href="javascript:;">配置文件</a> ' +
                                        '| <a class="btlink" onclick="site.edit.templet_proxy(\'' + web.name + '\',false,' + item + ')" href="javascript:;">编辑</a> ' +
                                        '| <a class="btlink" onclick="bt.site.remove_proxy(\'' + web.name + '\',\'' + proxyname + '\',function(rdata){if(rdata.status)site.reload(12)})" href="javascript:;">删除</a>';
                                    return conter
                                }
                            }
                        ],
                        data: rdata
                    });
                    $('.open_config_file').click(function () {
                        var sitename = $(this).attr('data-name');
                        var proxyname = $(this).attr('data-proxyname');
                        var proxy_config = '';
                        bt.site.get_proxy_config({
                            sitename: sitename,
                            proxyname: proxyname,
                            webserver: bt.get_cookie('serverType')
                        }, function (rdata) {
                            if (typeof rdata == 'object' && rdata.constructor == Array) {
                                if (!rdata[0].status) bt.msg(rdata)
                            } else {
                                if (!rdata.status) bt.msg(rdata)
                            }
                            var datas = [
                                { items: [{ name: 'proxy_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                                {
                                    name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {
                                        bt.site.save_proxy_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                                            if (ret.status) {
                                                site.reload(12);
                                                proxy_config.close();
                                            }
                                            bt.msg(ret);
                                        })
                                    }
                                }
                            ]
                            proxy_config = bt.open({
                                type: 1,
                                area: ['550px', '550px'],
                                title: '编辑配置文件[' + proxyname + ']',
                                closeBtn: 2,
                                shift: 0,
                                content: "<div class='bt-form'><div id='proxy_config_con' class='pd15'></div></div>"
                            })
                            var robj = $('#proxy_config_con');
                            for (var i = 0; i < datas.length; i++) {
                                var _form_data = bt.render_form_line(datas[i]);
                                robj.append(_form_data.html);
                                bt.render_clicks(_form_data.clicks);
                            }
                            robj.append(bt.render_help(['此处为该负载均衡的配置文件，若您不了解配置规则,请勿随意修改。']));
                            $('textarea.proxy_configs').attr('id', 'configBody');
                            var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                                extraKeys: { "Ctrl-Space": "autocomplete" },
                                lineNumbers: true,
                                matchBrackets: true
                            });
                            $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                            setTimeout(function () {
                                editor.refresh();
                            }, 250);
                        });
                    });
                    $('.set_nginx_state').click(function () {
                        type_edit_proxy($(this), 'cache')
                    });
                    $('.set_type_state').click(function () {
                        type_edit_proxy($(this), 'type');
                    });
                    function type_edit_proxy(_this, type) {
                        var index = _this.parent().attr('data-index');
                        var status = _this.attr('data-stuats');
                        var item = rdata[index];
                        item[type] = status;
                        item['subfilter'] = JSON.stringify(item['subfilter']);
                        bt.site.modify_proxy(item, function (rdata) {
                            if (rdata.status) site.reload(12);
                            bt.msg(rdata);
                        });
                    }
                }, 100);
            });
        },
        set_security: function (web) {
            bt.site.get_site_security(web.id, web.name, function (rdata) {
                var robj = $('#webedit-con');
                var datas = [
                    { title: 'URL后缀', name: 'sec_fix', value: rdata.fix, disabled: rdata.status, width: '360px' },
                    { title: '许可域名', name: 'sec_domains', value: rdata.domains, disabled: rdata.status, width: '360px' },

                    {
                        title: ' ', class: 'label-input-group', items: [
                            {
                                text: '启用防盗链', name: 'status', value: rdata.status, type: 'checkbox', callback: function (sdata) {
                                    bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains, sdata.status, function (ret) {
                                        if (ret.status) site.reload(13)
                                        bt.msg(ret);
                                    })
                                }
                            }
                        ]
                    }
                ]
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                }
                var helps = ['默认允许资源被直接访问,即不限制HTTP_REFERER为空的请求', '多个URL后缀与域名请使用逗号(,)隔开,如: png,jpeg,zip,js', '当触发防盗链时,将直接返回404状态']
                robj.append(bt.render_help(helps));
            })
        },
        set_tomact: function (web) {
            bt.site.get_site_phpversion(web.name, function (rdata) {
                var robj = $('#webedit-con');
                if (!rdata.tomcatversion) {
                    robj.html('<font>' + lan.site.tomcat_err_msg1 + '</font>');
                    layer.msg(lan.site.tomcat_err_msg, { icon: 2 });
                    return;
                }
                var data = {
                    class: 'label-input-group', items: [{
                        text: lan.site.enable_tomcat, name: 'tomcat', value: rdata.tomcat == -1 ? false : true, type: 'checkbox', callback: function (sdata) {
                            bt.site.set_tomcat(web.name, function (ret) {
                                if (ret.status) site.reload(9)
                                bt.msg(ret);
                            })
                        }
                    }]
                }
                var _form_data = bt.render_form_line(data);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
                var helps = [lan.site.tomcat_help1 + ' ' + rdata.tomcatversion + ',' + lan.site.tomcat_help2, lan.site.tomcat_help3, lan.site.tomcat_help4, lan.site.tomcat_help5]
                robj.append(bt.render_help(helps));
            })
        },
        get_site_logs: function (web) {
            bt.site.get_site_logs(web.name, function (rdata) {
                var robj = $('#webedit-con');
                var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '520px', value: rdata.msg, width: '100%', type: 'textarea' }] };
                var _form_data = bt.render_form_line(logs);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
                $('textarea[name="site_logs"]').attr('readonly', true);
            })
        }
    },
    create_let: function (ddata, callback) {
        bt.site.create_let(ddata, function (ret) {
            if (ret.status) {
                if (callback) {
                    callback(ret);
                }
                else {
                    site.ssl.reload(1);
                    bt.msg(ret);
                    return;
                }
            } else {
                if (ret.msg) {
                    if (typeof (ret.msg) == 'string') {
                        ret.msg = [ret.msg, ""];
                    }
                }
                if (!ret.out) {
                    if (callback) {
                        callback(ret);
                        return;
                    }
                    bt.msg(ret);
                    return;
                }
                var data = "<p>" + ret.msg + "</p><hr />"
                if (ret.err[0].length > 10) data += '<p style="color:red;">' + ret.err[0].replace(/\n/g, '<br>') + '</p>';
                if (ret.err[1].length > 10) data += '<p style="color:red;">' + ret.err[1].replace(/\n/g, '<br>') + '</p>';

                layer.msg(data, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
            }
        })
    },
    reload: function (index) {
        if (index == undefined) index = 0

        var _sel = $('.site-menu p.bgw');
        if (_sel.length == 0) _sel = $('.site-menu p:eq(0)');
        _sel.trigger('click');
    },
    plugin_firewall: function () {
        var typename = bt.get_cookie('serverType');
        var name = 'btwaf_httpd';
        if (typename == "nginx") name = 'btwaf'

        bt.plugin.get_plugin_byhtml(name, function (rhtml) {
            if (rhtml.status === false) return;

            var list = rhtml.split('<script type="javascript/text">');
            if (list.length > 1) {
                rcode = rhtml.split('<script type="javascript/text">')[1].replace("<\/script>", "");
            }
            else {
                list = rhtml.split('<script type="text/javascript">');
                rcode = rhtml.split('<script type="text/javascript">')[1].replace("<\/script>", "");
            }
            rcss = rhtml.split('<style>')[1].split('</style>')[0];
            rcode = rcode.replace('    wafview()','')
            $("body").append('<div style="display:none"><style>' + rcss + '</style><script type="javascript/text">' + rcode + '<\/script></div>');

            setTimeout(function () {
                if (!!(window.attachEvent && !window.opera)) {
                    execScript(rcode);
                } else {
                    window.eval(rcode);
                }
            }, 200)
        })

    },
    web_edit: function (obj) {
        var _this = this;
        var item = $(obj).parents('tr').data('item');
        bt.open({
            type: 1,
            area: ['700px', '690px'],
            title: lan.site.website_change + '[' + item.name + ']  --  ' + lan.site.addtime + '[' + item.addtime + ']',
            closeBtn: 2,
            shift: 0,
            content: "<div class='bt-form'><div class='bt-w-menu site-menu pull-left' style='height: 100%;'></div><div id='webedit-con' class='bt-w-con webedit-con pd15'></div></div>"
        })
        setTimeout(function () {
            var menus = [
                { title: '域名管理', callback: site.edit.set_domains },
                { title: '子目录绑定', callback: site.edit.set_dirbind },
                { title: '网站目录', callback: site.edit.set_dirpath },
                { title: '目录保护', callback: site.edit.set_dirguard },
                { title: '流量限制', callback: site.edit.limit_network },
                { title: '伪静态', callback: site.edit.get_rewrite_list },
                { title: '默认文档', callback: site.edit.set_default_index },
                { title: '配置文件', callback: site.edit.set_config },
                { title: 'SSL', callback: site.edit.set_ssl },
                { title: 'PHP版本', callback: site.edit.set_php_version },
                { title: 'Tomcat', callback: site.edit.set_tomact },
                { title: '重定向', callback: site.edit.set_301_old },
                { title: '重定向(测试版)', callback: site.edit.set_301 },
                { title: '反向代理', callback: site.edit.set_proxy },
                { title: '防盗链', callback: site.edit.set_security },
                { title: '响应日志', callback: site.edit.get_site_logs }
            ]
            for (var i = 0; i < menus.length; i++) {
                var men = menus[i];
                var _p = $('<p>' + men.title + '</p>');
                _p.data('callback', men.callback);
                $('.site-menu').append(_p);
            }
            $('.site-menu p').click(function () {
                $('#webedit-con').html('');
                $(this).addClass('bgw').siblings().removeClass('bgw');
                var callback = $(this).data('callback')
                if (callback) callback(item);
            })
            site.reload(0);
        }, 100)
    }
}
site.get_types();



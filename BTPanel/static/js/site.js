var site_table = bt_tools.table({
    el:'#bt_site_table',
    url:'/data?action=getData',
    param:{table:'sites'}, //参数
    minWidth:'1000px',
    autoHeight:true,
    default:"站点列表为空",//数据为空时的默认提示
    beforeRequest:function(param){
        param.type = bt.get_cookie('site_type') || -1;
        return param;
    },
    column:[
        {type:'checkbox',class:'',width:20},
        {fid:'name',title:'网站名',sort:true,sortValue:'asc',type:'link',event:function(row,index,ev){
            site.web_edit(row,true);
        }},
        {fid:'status',title:'状态',sort:true,width:80,config:{icon:true,list:[['1','运行中','bt_success','glyphicon-play'],['0','已停止','bt_danger','glyphicon-pause']]},type:'status',event:function(row,index,ev,key,that){
            var time = row.edate || row.endtime;
            if(time != "0000-00-00"){
                if(new Date(time).getTime() < new Date().getTime()){
                    layer.msg('当前站点已过期，请重新设置站点到期时间',{icon:2});
                    return false;
                }
            }
            bt.site[parseInt(row.status)?'stop':'start'](row.id,row.name,function(res){
                if(res.status) that.$modify_row_data({status:parseInt(row.status)?'0':'1'});
            });
        }},
        {fid:'backup_count',title:'备份',width:80,type:'link',template:function(row,index){
            var backup = lan.site.backup_no,_class = "bt_warning";
            if (row.backup_count > 0) backup = lan.site.backup_yes,_class = "bt_success";
            return '<a href="javascript:;" class="btlink  '+ _class +'">'+ backup + (row.backup_count >0?('('+ row.backup_count +')'):'') +'</a>';
        },event:function(row,index){
            site.backup_site_view({id:row.id,name:row.name});
        }},
        {fid:'path',title:'根目录',tips:'打开目录',type:'link',event:function(row,index,ev){
            openPath(row.path);
        }},
        {fid:'edate',title:'到期时间',width:85,class:'set_site_edate',sort:true,type:'link',template:function(row,index){
            var _endtime = row.edate || row.endtime;
            if(_endtime === "0000-00-00"){
                return lan.site.web_end_time;
            }else{
                if(new Date(_endtime).getTime() < new Date().getTime()){
                    return '<a href="javscript:;" class="bt_danger">已过期</a>';
                }else{
                    return  _endtime;
                }
            }
        },event:function(row){}}, //模拟点击误删
        {fid:'ps',title:'备注',type:'input',blur:function(row,index,ev,key,that){
            bt.pub.set_data_ps({id:row.id,table:'sites',ps:ev.target.value},function(res){
                bt_tools.msg(res,{is_dynamic:true});
            });
        },keyup:function(row,index,ev){
            if(ev.keyCode === 13){
                $(this).blur();
            }
        }},
        {fid:'php_version',title:'PHP',tips:'选择php版本',width:50,type:'link',template:function(row,index){
            if(row.php_version.indexOf('静态') > -1) return  row.php_version;
            return row.php_version;
        },event:function(row,index){
            site.web_edit(row);
            setTimeout(function(){
                $('.site-menu p:eq(9)').click();
            },500);
        }},
        {fid:'ssl',title:'SSL证书',tips:'部署证书',width:100,type:'text',template:function(row,index){
            var _ssl = row.ssl,_info = '',_arry = [['issuer','证书品牌'],['notAfter','到期日期'],['notBefore','申请日期'],['dns','可用域名']];
            try {
                if(typeof row.ssl.endtime != 'undefined'){
                    if(row.ssl.endtime < 0) return '<a class="btlink bt_danger" href="javascript:;">未部署</a>';
                }
            } catch (error){}
            for(var i=0;i<_arry.length;i++){
                var item = _ssl[_arry[i][0]];
                _info += _arry[i][1]+':'+ item + (_arry.length-1 != i?'\n':'');
            }
            return row.ssl === -1?'<a class="btlink bt_warning" href="javascript:;">未部署</a>':'<a class="btlink" href="javascript:;" title="'+ _info +'">剩余'+ row.ssl.endtime +'天</a>';
        },event:function(row,index,ev,key,that){
            site.web_edit(row);
            setTimeout(function(){
                $('.site-menu p:eq(8)').click();
            },500);
        }},
        {title:'操作',type:'group',width:150,align:'right',group:[{
            title:'防火墙',
            event:function(row,index,ev,key,that){
                site.site_waf(row.name);
            }
        },{
            title:'设置',
            event:function(row,index,ev,key,that){
                site.web_edit(row,true);
            }
        },{
            title:'删除',
            event:function(row,index,ev,key,that){
                site.del_site(row.id,row.name,function(){
                    that.$refresh_table_list(true);
                });
            }
        }]}
    ],
    sortParam:function(data){
        return {'order':data.name +' '+ data.sort};
    },
    // 表格渲染完成后
    success:function(that){
        $('.event_edate_'+ that.random).each(function(){
            var $this = $(this);
            laydate.render({
                elem: $this[0] //指定元素
                , min: bt.get_date(1)
                , max: '2099-12-31'
                , vlue: bt.get_date(365)
                , type: 'date'
                , format: 'yyyy-MM-dd'
                , trigger: 'click'
                , btns: ['perpetual', 'confirm']
                , theme: '#20a53a'
                , ready:function(){
                    $this.click();
                }
                , done: function (date) {
                    var item = that.event_rows_model.rows;
                    bt.site.set_endtime(item.id, date,function(res){
                        if(res.status){
                            layer.msg(res.msg);
                            return false;
                        }
                        bt.msg(res);
                    });
                }
            });
        });
    },
    // 渲染完成
    tootls:[{ // 按钮组
        type:'group',
        positon:['left','top'],
        list:[
            {title:'添加站点',active:true, event:function(ev){ site.add_site(function(){ 
                site_table.$refresh_table_list(true) });
                bt.set_cookie('site_type','-1');
            }},
            {title:'修改默认页',event:function(ev){ site.set_default_page() }},
            {title:'默认站点',event:function(ev){ site.set_default_site() }},
            {title:'PHP命令行版本',event:function(ev){ site.get_cli_version()}}
        ]
    },{ // 搜索内容
        type:'search',
        positon:['right','top'],
        placeholder:'请输入域名或备注',
        searchParam:'search', //搜索请求字段，默认为 search
        value:'',// 当前内容,默认为空
    },{ // 批量操作
        type:'batch',//batch_btn
        positon:['left','bottom'],
        placeholder:'请选择批量操作',
        buttonValue:'批量操作',
        disabledSelectValue:'请选择需要批量操作的站点!',
        selectList:[
            {
                group:[{title:'开启站点',param:{status:1}},{title:'停止站点',param:{status:0}}],
                url:'/site?action=set_site_status_multiple',
                confirmVerify:false, //是否提示验证方式
                paramName:'sites_id', //列表参数名,可以为空
                paramId:'id', // 需要传入批量的id
                theadName:'站点名称'
            },{
                title:"备份站点",
                url:'/site?action=ToBackup',
                paramId:'id',
                load:true,
                theadName:'站点名称',
                callback:function(that){ // 手动执行,data参数包含所有选中的站点
                    that.start_batch({},function(list){
                        var html = '';
                        for(var i=0;i<list.length;i++){
                            var item = list[i];
                            html += '<tr><td><span>'+ item.name +'</span></td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ item.request.msg +'</span></div></td></tr>';
                        }
                        site_table.$batch_success_table({title:'批量备份',th:'站点名称',html:html});
                        site_table.$refresh_table_list(true);
                    });
                }
            },{
                title:"设置到期时间",
                url:'/site?action=set_site_etime_multiple',
                paramName:'sites_id', //列表参数名,可以为空
                paramId:'id', // 需要传入批量的id
                theadName:'站点名称',
                confirm:{
                    title:'批量设置到期时间',
                    content:'<div class="line"><span class="tname">到期时间</span><div class="info-r "><input name="edate" id="site_edate" class="bt-input-text mr5" placeholder="yyyy-MM-dd" type="text"></div></div>',
                    success:function(){
                        laydate.render({
                            elem: '#site_edate'
                            ,min: bt.format_data(new Date().getTime(),'yyyy-MM-dd')
                            ,max: '2099-12-31'
                            ,vlue: bt.get_date(365)
                            ,type: 'date'
                            ,format: 'yyyy-MM-dd'
                            ,trigger: 'click'
                            ,btns: ['perpetual','confirm']
                            ,theme: '#20a53a'
                        });
                    },
                    yes:function(index,layers,request){
                        var site_edate = $('#site_edate'),site_edate_val = site_edate.val();
                        if(site_edate_val != ''){
                            if(new Date(site_edate_val).getTime() < new Date().getTime()){
                                layer.tips('设置的到期时间不得小于当前时间','#site_edate',{tips:['1','red']});
                                return false;
                            }
                            request({'edate':site_edate_val==='永久'?'0000-00-00':site_edate_val});
                        }else{
                            layer.tips('请输入到期时间','#site_edate',{tips:['1','red']});
                            $('#site_edate').css('border-color','red');
                            $('#site_edate').click();
                            setTimeout(function(){
                                $('#site_edate').removeAttr('style');
                            },3000);
                            return false;
                        }
                    }
                }
            },{
                title:"设置PHP版本",
                url:'/site?action=set_site_php_version_multiple',
                paramName:'sites_id', //列表参数名,可以为空
                paramId:'id', // 需要传入批量的id
                theadName:'站点名称',
                confirm:{
                    title:'批量设置PHP版本',
                    area:'420px',
                    content:'<div class="line"><span class="tname">PHP版本</span><div class="info-r"><select class="bt-input-text mr5 versions" name="versions" style="width:150px"></select></span></div><ul class="help-info-text c7" style="font-size:11px"><li>请根据您的程序需求选择版本</li><li>若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；</li><li>PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo。</li></ul></div>',
                    success:function(){
                        bt.site.get_all_phpversion(function(res){
                            var html = '';
                            $.each(res,function(index,item){
                                html += '<option value="'+ item.version +'">'+ item.name +'</option>';
                            });
                            $('[name="versions"]').html(html);
                        });
                    },
                    yes:function(index,layers,request){
                        request({version:$('[name="versions"]').val()});
                    }
                }
            },{
                title:"设置分类",
                url:'/site?action=set_site_type',
                paramName:'site_ids', //列表参数名,可以为空
                paramId:'id', // 需要传入批量的id
                beforeRequest:function(list){
                    var arry = [];
                    $.each(list,function(index,item){
                        arry.push(item.id);
                    });
                    return JSON.stringify(arry);
                },
                confirm:{
                    title:'批量设置分类',
                    content:'<div class="line"><span class="tname">站点分类</span><div class="info-r"><select class="bt-input-text mr5 site_types" name="site_types" style="width:150px"></select></span></div></div>',
                    success:function(){
                        bt.site.get_type(function(res){
                            var html = '';
                            $.each(res,function(index,item){
                                html += '<option value="'+ item.id +'">'+ item.name +'</option>';
                            });
                            $('[name="site_types"]').html(html);
                        });
                    },
                    yes:function(index,layers,request){
                        request({id:$('[name="site_types"]').val()});
                    }
                },
                tips:false,
                success:function(res,list,that){
                    var html = '';
                    $.each(list,function(index,item){
                        html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (res.status?'#20a53a':'red') +'">'+ res.msg +'</span></div></td></tr>';
                    });
                    that.$batch_success_table({title:'批量设置分类',th:'站点名称',html:html});
                    that.$refresh_table_list(true);
                }
            },{
                title:"删除站点",
                url:'/site?action=delete_website_multiple',
                paramName:'sites_id', //列表参数名,可以为空
                paramId:'id', //需要传入批量的id
                theadName:'站点名称',
                confirm:function(config,callback){
                    bt.show_confirm("批量删除站点","是否同时删除选中站点同名的FTP、数据库、根目录", function(){
                        var param = {};
                        $('.bacth_options input[type=checkbox]').each(function(){
                            var checked = $(this).is(":checked");
                            if(checked) param[$(this).attr('name')] = checked?1:0;
                        })
                        if(callback) callback(param);
                    },"<div class='options bacth_options'><span class='item'><label><input type='checkbox' name='ftp'><span>FTP</span></label></span><span class='item'><label><input type='checkbox' name='database'><span>" + lan.site.database + "</span></label></span><span class='item'><label><input type='checkbox' name='path'><span>" + lan.site.root_dir + "</span></label></span></div>");
                }
            }
        ],
    },{ //分页显示
        type:'page',
        positon:['right','bottom'], // 默认在右下角
        pageParam:'p', //分页请求字段,默认为 : p
        page:1, //当前分页 默认：1
        numberParam:'limit',　//分页数量请求字段默认为 : limit
        number:20,　//分页数量默认 : 20条
        numberList:[10,20,50,100,200], // 分页显示数量列表
        numberStatus:true, //　是否支持分页数量选择,默认禁用
        jump:true, //是否支持跳转分页,默认禁用
    }]
});
$('.tootls_group.tootls_top .pull-left').append('<div class="bt_select_updown site_class_type"><div class="bt_select_value"><span class="bt_select_content">分类:</span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span></div><ul class="bt_select_list"></ul></div>');

bt.site.get_type(function(res){
    site.reader_site_type(res);
});
var site = {
    reader_site_type:function(res){
        var html = '',active = bt.get_cookie('site_type') || -1,select = $('.site_class_type');
        res.unshift({id:-1, name: "全部分类"});
        $.each(res,function(index,item){
            html += '<li class="item '+ (parseInt(active) == item.id?'active':'') +'" data-id="'+ item.id +'">'+ item.name +'</li>';
        });
        html += '<li role="separator" class="divider"></li><li class="item" data-id="type_sets">分类设置</li>';
        select.find('.bt_select_value').on('click',function(ev){
            var $this = this;
            $(this).next().show();
            $(document).one('click',function(){
                $($this).next().hide();
                
            });
            ev.stopPropagation()
        });

        select.find('.bt_select_list').unbind('click').on('click','li',function(){
            var id = $(this).data('id');
            if(id == 'type_sets'){
                site.set_class_type();
            }else{
                bt.set_cookie('site_type',id);
                site_table.$refresh_table_list(true);
                $(this).addClass('active').siblings().removeClass('active');
                select.find('.bt_select_value .bt_select_content').text('分类: '+$(this).text());
            }
            
        }).empty().html(html);
        if(!select.find('.bt_select_list li.active').length){
            console.log(select.find('.bt_select_list li:eq(0)'));
            select.find('.bt_select_list li:eq(0)').addClass('active');
            select.find('.bt_select_value .bt_select_content').text('分类: 默认分类');
        }else{
            select.find('.bt_select_value .bt_select_content').text('分类: '+select.find('.bt_select_list li.active').text());
        }
    },
    get_list: function (page, search, type) {
        if (page == undefined) page = 1;
        if (type == '-1' || type == undefined) {
            type = bt.get_cookie('site_type');
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
                            field: 'name', title: '网站名', templet: function (item) {
                                return '<a class="btlink webtips" onclick="site.web_edit(this)" href="javascript:;">' + item.name + '</a>';
                            }, sort: function () { site.get_list(); }
                        },
                        {
                            field: 'status', title: '状态', width: 80, templet: function (item) {
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
                            field: 'path', title: '根目录', templet: function (item) {
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
                            field: 'php_version',width:60, title: 'PHP', templet: function (item) {
                                return  '<a class="phpversion_tips btlink">'+item.php_version+'</a>';
                            }
                        },
                        {
                            field: 'ssl', title: 'SSL证书', width: 80, templet: function (item) {
                                var _ssl = '';
                                if (item.ssl == -1)
                                {
                                    _ssl = '<a class="ssl_tips btlink" style="color:orange;">未部署</a>';
                                }else{
                                    var ssl_info = "证书品牌: "+item.ssl.issuer+"<br>到期日期: " + item.ssl.notAfter+"<br>申请日期: " + item.ssl.notBefore +"<br>可用域名: " + item.ssl.dns.join("/");
                                    if(item.ssl.endtime < 0){
                                        _ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="'+ssl_info+'">已过期</a>';
                                    
                                    }else if(item.ssl.endtime < 20){
                                        _ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="'+ssl_info+'">剩余'+(item.ssl.endtime+'天')+'</a>';
                                    }else{
                                        _ssl = '<a class="ssl_tips btlink" style="color:green;" data-tips="'+ssl_info+'">剩余'+item.ssl.endtime+'天</a>';
                                    }
                                }
                                return _ssl;
                            }
                        },
                        {
                            field: 'opt', width: 150, title: '操作', align: 'right', templet: function (item) {
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
                var outTime = '';
                $('.ssl_tips').hover(function(){
                    var that = this,tips = $(that).attr('data-tips');
                    if(!tips) return false;
                    outTime = setTimeout(function(){
                        layer.tips(tips, $(that), {
                          tips: [2, '#20a53a'], //还可配置颜色
                          time:0
                        });
                    },500);
                },function(){
                    outTime != ''?clearTimeout(outTime):'';
                    layer.closeAll('tips');
                })
                $('.ssl_tips').click(function(){
                    site.web_edit(this);
                    var timeVal = setInterval(function(){
                        var content = $('#webedit-con').html();
                        if(content != ''){
                            $('.site-menu p:eq(8)').click();
                            clearInterval(timeVal);
                        }
                    },100);
                });
                $('.phpversion_tips').click(function(){
                    site.web_edit(this);
                    var timeVal = setInterval(function(){
                        var content = $('#webedit-con').html();
                        if(content != ''){
                            $('.site-menu p:eq(9)').click();
                            clearInterval(timeVal);
                        }
                    },100);
                });
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
            var t_val = bt.get_cookie('site_type');
            for (var i = 0; i < rdata.length; i++) {
                optionList += '<button class="btn btn-'+(t_val == rdata[i].id?'success':'default')+' btn-sm" value="' + rdata[i].id + '">' + rdata[i].name + '</button>'
            }
            if($('.dataTables_paginate').next().hasClass('site_type')) $('.site_type').remove();
            $('.dataTables_paginate').after('<div class="site_type"><button class="btn btn-'+(t_val == '-1'?'success':'default')+' btn-sm" value="-1">全部分类</button>' + optionList + '</div>');

            $('.site_type button').click(function () {
                var val = $(this).attr('value');
                bt.set_cookie('site_type', val);
                site.get_list(0,'', val);
                $(".site_type button").removeClass('btn-success').addClass('btn-default');
                $(this).addClass('btn-success');
                
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

    /**
     * @description 备份站点视图
     * @param {object} config  配置参数
     * @param {function} callback  回调函数
    */
    backup_site_view:function(config,callback){
        bt_tools.open({
            title:'备份站点&nbsp;-&nbsp;[&nbsp;'+ config.name +'&nbsp;]',
            area:'720px',
            btn:false,
            skin:'bt_backup_table',
            content:'<div id="bt_backup_table" class="pd20" style="padding-bottom:40px;"></div>',
            success:function(){
                var backup_table = bt_tools.table({
                    el:'#bt_backup_table',
                    url:'/data?action=getData',
                    param:{table:'backup',search:config.id,type:'0'},
                    default:"["+ config.name +"] 站点备份列表为空",//数据为空时的默认提示
                    column:[
                        {type:'checkbox',class:'',width:20},
                        {fid:'name',title:'文件名'},
                        {fid:'size',title:'文件大小',type:'text',template:function(row,index){
                            return bt.format_size(row.size);
                        }},
                        {fid:'addtime',title:'备份时间'},
                        {title:'操作',type:'group',width:150,align:'right',group:[{
                            title:'下载',
                            template:function(row,index,ev,key,that){
                                return '<a target="_blank" class="btlink" href="/download?filename=' + row.filename + '&amp;name=' + row.name +'">下载</a>';
                            }
                        },{
                            title:'删除',
                            event:function(row,index,ev,key,that){
                                that.del_site_backup({name:row.name,id:row.id},function(rdata){
                                    bt_tools.msg(rdata);
                                    if(rdata.status){
                                        site_table.$modify_row_data({backup_count:site_table.event_rows_model.rows.backup_count - 1});
                                        that.$refresh_table_list();
                                    }
                                });
                            }
                        }]}
                    ],
                    methods:{
                        /**
                         * @description 删除站点备份
                         * @param {object} config 
                         * @param {function} callback
                        */
                        del_site_backup:function(config,callback){
                            bt.confirm({title:'删除站点备份',msg:'删除站点备份['+ config.name +'],是否继续？'},function(){
                                bt_tools.send('site/DelBackup',{id:config.id},function(rdata){
                                    if(callback) callback(rdata);
                                },true);
                            });
                        }
                    },
                    success:function(){
                        if(callback) callback();
                        $('.bt_backup_table').css('top',(($(window).height() - $('.bt_backup_table').height())/2) + 'px');
                    },
                    tootls:[{ // 按钮组
                        type:'group',
                        positon:['left','top'],
                        list:[
                            {title:'备份站点',active:true, event:function(ev,that){
                                bt.site.backup_data(config.id,function (rdata){
                                    bt_tools.msg(rdata);
                                    if(rdata.status){
                                        site_table.$modify_row_data({backup_count:site_table.event_rows_model.rows.backup_count + 1});
                                        that.$refresh_table_list();
                                    }
                                });
                            }}
                        ]
                    },{ 
                        type:'batch',
                        positon:['left','bottom'],
                        config:{
                            title:'删除',
                            url:'/site?action=DelBackup',
                            paramId:'id',
                            load:true,
                            callback:function(that){
                                bt.confirm({title:'批量删除站点备份',msg:'是否批量删除选中的站点备份，是否继续？',icon:0},function(index){
                                    layer.close(index);
                                    that.start_batch({},function(list){
                                        var html = '';
                                        for(var i=0;i<list.length;i++){
                                            var item = list[i];
                                            html += '<tr><td><span class="text-overflow" title="'+ item.name +'">'+ item.name +'</span></td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ item.request.msg +'</span></div></td></tr>';
                                        }
                                        backup_table.$batch_success_table({title:'批量删除站点备份',th:'文件名',html:html});
                                        backup_table.$refresh_table_list(true);
                                        site_table.$modify_row_data({backup_count:site_table.event_rows_model.rows.backup_count - list.length});
                                    });
                                });
                            }
                        } //分页显示
                    },{
                        type:'page',
                        positon:['right','bottom'], // 默认在右下角
                        pageParam:'p', //分页请求字段,默认为 : p
                        page:1, //当前分页 默认：1
                        numberParam:'limit',　//分页数量请求字段默认为 : limit
                        number:10,　//分页数量默认 : 20条
                    }]
                });
            }
        });
    },

    /**
     * @description 添加站点
     * @param {object} config  配置参数
     * @param {function} callback  回调函数
    */
    add_site: function (callback) {
        var add_web = bt_tools.form({
            data:{}, //用于存储初始值和编辑时的赋值内容
            class:'',
            form:[{
                    label:'域名',
                    group:{
                        type:'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
                        name:'webname', //当前表单的name
                        style:{'width':'440px','height':'100px','line-height':'22px'},
                        tips:{ //使用hover的方式显示提示
                            text:'如需填写多个域名，请换行填写，每行一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88',
                            style:{top:'15px',left:'15px'},
                        },
                        input:function(value,form,that,config,ev){  //键盘事件
                            var array = value.webname.split("\n"),ress = array[0].split(":")[0],
                            oneVal = bt.strim(ress.replace(new RegExp(/([-.])/g), '_')),defaultPath = $('#defaultPath').text(),is_oneVal = ress.length > 0;
                            that.$set_find_value(is_oneVal?{
                                'ftp_username':'ftp_'+ oneVal,'ftp_password':bt.get_random(16),
                                'datauser':is_oneVal?('sql_'+ oneVal.substr(0, 16)):'','datapassword':bt.get_random(16),
                                'ps':oneVal,
                                'path':bt.rtrim(defaultPath,'/') + '/'+ ress
                            }:{'ftp_username':'','ftp_password':'','datauser':'','datapassword':'','ps':'','path':bt.rtrim(defaultPath,'/')});
                        }
                    }
                },{
                    label:'备注',
                    group:{
                        type:'text',
                        name:'ps',
                        width:'400px',
                        placeholder:'网站备注，可为空' //默认标准备注提示
                    }
                },{
                    label:'根目录',
                    group:{
                        type:'text',
                        width:'400px',
                        name:'path',
                        icon:{
                            type:'glyphicon-folder-open',
                            event:function(ev){
                                console.log(ev)
                            }
                        },
                        value:'/www/wwwroot',
                        placeholder:'请选择文件目录'
                    }
                },{
                    label:'FTP',
                    group:[{
                        type:'select',
                        name:'ftp',
                        width:'120px',
                        disabled:(function(){
                            if(bt.config['pure-ftpd']) return !bt.config['pure-ftpd'].setup;
                            return true;
                        }()),
                        list:[
                            {title:'不创建',value:false},
                            {title:'创建',value:true}
                        ],
                        change:function(value,form,that,config,ev){
                            if(value['ftp'] === 'true'){
                                form['ftp_username'].parents('.line').removeClass('hide');
                            }else{
                                form['ftp_username'].parents('.line').addClass('hide');
                            }
                        }
                    },(function(){
                        if(bt.config['pure-ftpd']['setup']) return {};
                        return {
                            type:'link',
                            title:'未安装FTP，点击安装',
                            event:function(ev){
                                bt.soft.install('pureftpd');
                            }
                        }
                    }())]
                },{
                    label:'FTP账号',
                    hide:true,
                    group:[
                        {type:'text',name:'ftp_username',placeholder:'创建FTP账号',width:'175px',style:{'margin-right':'15px'}},
                        {label:'密码',type:'text',placeholder:'FTP密码',name:'ftp_password',width:'175px'}
                    ],
                    help:{
                        list:['创建站点的同时，为站点创建一个对应FTP帐户，并且FTP目录指向站点所在目录。']
                    }
                },{
                    label:'数据库',
                    group:[{
                        type:'select',
                        name:'sql',
                        width:'120px',
                        disabled:(function(){
                            if(bt.config['mysql']) return !bt.config['mysql'].setup;
                            return true;
                        }()),
                        list:[
                            {title:'不创建',value:false},
                            {title:'MySQL',value:'MySQL'},
                            {title:'SQLServer',value:'SQLServer',disabled:true,tips:'Linux暂不支持SQLServer!'}
                        ],
                        change:function(value,form,that,config,ev){
                            if(value['sql'] === 'MySQL'){
                                form['datauser'].parents('.line').removeClass('hide');
                                form['codeing'].parents('.bt_select_updown').removeClass('hide');
                            }else{
                                form['datauser'].parents('.line').addClass('hide');
                                form['codeing'].parents('.bt_select_updown').addClass('hide');
                            }
                        }
                    },(function(){
                        if(bt.config.mysql.setup) return {};
                        return {
                            type:'link',
                            title:'未安装数据库，点击安装',
                            event:function(){
                                bt.soft.install('mysql');
                            }
                        }
                    }()),{
                        type:'select',
                        name:'codeing',
                        hide:true,
                        width:'120px',
                        list:[
                            {title:'utf8',value:'utf8'},
                            {title:'utf8mb4',value:'utf8mb4'},
                            {title:'gbk',value:'gbk'},
                            {title:'big5',value:'big5'}
                        ]
                    }]
                },{
                    label:'数据库账号',
                    hide:true,
                    group:[
                        {type:'text',name:'datauser',placeholder:'创建数据库账号',width:'175px',style:{'margin-right':'15px'}},
                        {label:'密码',type:'text',placeholder:'数据库密码',name:'datapassword',width:'175px'}
                    ],
                    help:{
                        class:'',
                        style:'',
                        list:['创建站点的同时，为站点创建一个对应的数据库帐户，方便不同站点使用不同数据库。']
                    }
                },{
                    label:'PHP版本',
                    group:[
                        {
                            type:'select',
                            name:'version',
                            width:'120px',
                            list:{
                                url:'/site?action=GetPHPVersion',
                                dataFilter:function(res){
                                    var arry = [];
                                    for(var i = res.length-1; i>=0;i--){
                                        var item = res[i];
                                        arry.push({title:item.name,value:item.version});
                                    }
                                    return arry;
                                }
                            }
                        }
                    ]
                },{
                    label:'网站分类',
                    group:[
                        {
                            type:'select',
                            name:'type_id',
                            width:'120px',
                            list:{
                                url:'/site?action=get_site_types',
                                dataFilter:function(res){
                                    var arry = [];
                                    $.each(res,function(index,item){
                                        arry.push({title:item.name,value:item.id});
                                    });
                                    return arry;
                                }
                            }
                        }
                    ]
                }
            ]
        });
        var bath_web = bt_tools.form({
            class:'plr10',
            form:[{
                line_style:{'position':'relative'},
                group:{
                    type:'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
                    name:'bath_code', //当前表单的name
                    style:{'width':'560px','height':'180px','line-height':'22px','font-size':'13px'},
                    value:'域名|1|0|0|0\n域名|1|0|0|0\n域名|1|0|0|0',
                }
            },{
                group:{
                    type:'help',
                    style:{'margin-top':'0'},
                    class:'none-list-style',
                    list:[
                        '批量格式：域名|根目录|FTP|数据库|PHP版本',
                        '<span style="padding-top:5px;display:inline-block;">域名参数：多个域名用&nbsp;,&nbsp;分割</span>',
                        '根目录参数：填写&nbsp;1&nbsp;为自动创建，或输入具体目录',
                        'FTP参数：填写&nbsp;1&nbsp;为自动创建，填写&nbsp;0&nbsp;为不创建',
                        '数据库参数：填写&nbsp;1&nbsp;为自动创建，填写&nbsp;0&nbsp;为不创建',
                        'PHP版本参数：填写&nbsp;0&nbsp;为静态，或输入PHP具体版本号列如：56、71、74',
                        '<span style="padding-bottom:5px;display:inline-block;">如需添加多个站点，请换行填写</span>',
                        '案例：bt.cn,test.cn:8081|/www/wwwroot/bt.cn|1|1|56'
                    ]
                }
            }]
        });
        var web_tab = bt_tools.tab({
            class:'pd20',
            type:0,
            theme:{nav:'mlr20'},
            active:1, //激活TAB下标
            list:[{
                title:'创建站点',
                name:'createSite',
                content:add_web.$reader_content(),
                success:function(){
                    add_web.$event_bind();
                }
            },{
                title:'批量创建',
                name:'batchCreation',
                content:bath_web.$reader_content(),
                success:function(){
                    bath_web.$event_bind();
                }
            }]
        });
        bt_tools.open({
            title:'添加站点-支持批量建站',
            skin:'custom_layer',
            btn:['提交','取消'],
            content:web_tab.$reader_content(),
            success:function(){
                web_tab.$init();
            },
            yes:function(indexs){
                var formValue = !web_tab.active?add_web.$get_form_value():bath_web.$get_form_value();
                if(!web_tab.active){  // 创建站点
                    var loading = bt.load();
                    add_web.$get_form_element(true);
                    if(formValue.webname === ''){
                        add_web.form_element.webname.focus();
                        bt_tools.msg('域名不能为空！',2);
                        return ;
                    }
                    var webname = bt.replace_all(formValue.webname,'http[s]?:\\/\\/',''),web_list = webname.split('\n'),
                    param = {webname:{domain:'',domainlist:[],count:0},type:'PHP',port:80},arry = ['ps',['path','网站目录'],'type_id','version','ftp','sql','ftp_username','ftp_password','datauser','datapassword','codeing']
                    for(var i=0;i<web_list.length;i++){
                        var temps = web_list[i].replace(/\r\n/,'').split(':');
                        if(i === 0){
                            param['webname']['domain'] = web_list[i];
                            if(typeof temps[1] != 'undefined') param['port'] = temps[1]
                        }else{
                            param['webname']['domainlist'].push(web_list[i]);
                        }
                    }
                    param['webname']['count'] = param['webname']['domainlist'].length;
                    param['webname'] = JSON.stringify(param['webname']);
                    $.each(arry,function(index,item){
                        if(formValue[item] == '' && Array.isArray(item)){
                            bt_tools.msg(item[1] + '不能为空?',2);
                            return false;
                        }
                        Array.isArray(item)? item = item[0]:'';
                        if(formValue['ftp'] === 'false' && (item === 'ftp_username' || item === 'ftp_password')) return true; 
                        if(formValue['sql'] === 'false' && (item === 'datauser' || item === 'datapassword')) return true;
                        param[item] = formValue[item];
                    });
                    if(typeof param.ftp === 'undefined'){
                        param.ftp = false;
                        delete param.ftp_password;
                        delete param.ftp_username;
                    }
                    if(typeof param.sql === 'undefined'){
                        param.sql = false;
                        delete param.datapassword;
                        delete param.datauser;
                    }
                    bt.send('AddSite','site/AddSite',param,function(rdata){
                        loading.close();
                        if (rdata.siteStatus){
                            layer.close(indexs);
                            if(callback) callback(rdata);
                            var html = '',ftpData = '',sqlData = ''
                            if (rdata.ftpStatus) {
                                var list = [];
                                list.push({ title: lan.site.user, val: rdata.ftpUser });
                                list.push({ title: lan.site.password, val: rdata.ftpPass });
                                var item = {};
                                item.title = lan.site.ftp;
                                item.list = list;
                                ftpData = bt.render_ps(item);
                            }
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
                            }else {
                                bt.open({
                                    type: 1,
                                    area: '600px',
                                    title: lan.site.success_txt,
                                    closeBtn: 2,
                                    shadeClose: false,
                                    content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + ftpData + sqlData + "</div></div>"
                                });
            
                                if ($(".success-msg").height() < 150) {
                                    $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                                }
                            }
                        }else {
                            bt.msg(rdata);
                        }
                    });
                }else{ //批量创建
                    var loading = bt.load();
                    if(formValue.bath_code === ''){
                        bt_tools.msg('请输入需要批量创建的站点信息!',2);
                        return false;
                    }else{
                        var arry = formValue.bath_code.split("\n"),config = '',_list = [];
                        for(var i=0; i < arry.length;i++){
                            var item = arry[i],params = item.split("|"),_arry = [];
                            if(item === '') continue;
                            for(var j=0;j<params.length;j++){
                                var line = i+1,items = bt.strim(params[j]);
                                _arry.push(items);
                                switch(j){
                                    case 0: //参数一:域名
                                        var domainList = items.split(",");
                                        for(var z=0;z<domainList.length;z++){
                                            var domain_info = domainList[z],_domain = domain_info.split(":");
                                            if(!bt.check_domain(_domain[0])){
                                                bt_tools.msg('第'+ line +'行,域名格式错误【'+ domain_info +'】',2);
                                                return false;
                                            }
                                            if(typeof _domain[1] !== "undefined"){
                                                if(!bt.check_port(_domain[1])){
                                                    bt_tools.msg('第'+ line +'行,域名端口格式错误【'+ _domain[1] +'】',2);
                                                    return false;
                                                }
                                            }
                                        }
                                    break;
                                    case 1: //参数二:站点目录
                                        if(items !== '1'){
                                            if(items.indexOf('/') < -1){
                                                bt_tools.msg('第'+ line +'行,站点目录格式错误【'+ items +'】',2);
                                                return false;
                                            }
                                        }
                                    break;
                                }
                            }
                            _list.push(_arry.join('|').replace(/\r|\n/,''));
                        }
                    }
                    bt.send('create_type','site/create_website_multiple',{create_type:'txt',websites_content:JSON.stringify(_list)},function(rdata){
                        loading.close();
                        if(rdata.status){
                            var _html = '';
                            layer.close(indexs);
                            if(callback) callback(rdata);
                            $.each(rdata.error,function(key,item){
                                _html += '<tr><td>'+ key +'</td><td>--</td><td>--</td><td style="text-align: right;"><span style="color:red">'+ item +'</td></td></tr>';
                            });
                            $.each(rdata.success,function(key,item){
                                _html += '<tr><td>'+ key +'</td><td>'+ (item.ftp_status?'<span style="color:#20a53a">成功</span>':'<span>未创建</span>') +'</td><td>'+ (item.db_status?'<span style="color:#20a53a">成功</span>':'<span>未创建</span>') +'</td><td  style="text-align: right;"><span style="color:#20a53a">创建成功</span></td></tr>';
                            });
                            bt.open({
                                type:1,
                                title:'站点批量添加',
                                area:['500px','450px'],
                                shadeClose:false,
                                closeBtn:2,
                                content:'<div class="fiexd_thead divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 360px;"><table class="table table-hover"><thead><tr><th>站点名称</th><th>FTP</th><th >数据库</th><th style="text-align:right;width:150px;">操作结果</th></tr></thead><tbody>'+ _html +'</tbody></table></div>',
                                success:function(){
                                    $('.fiexd_thead').scroll(function(){
                                        var scrollTop = this.scrollTop;
                                        this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
                                    });
                                }
                            });
                        }else{
                            bt.msg(rdata);
                        }
                    });
                }
            }
        });
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
            for (var i = rdata.versions.length - 1; i >= 0; i--){
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
    del_site: function (wid, wname,callback) {
        var thtml = "<div class='options'><span class='item'><label><input type='checkbox' id='delftp' name='ftp'><span>FTP</span></label></span><span class='item'><label><input type='checkbox' id='deldata' name='data'><span>" + lan.site.database + "</span></label></span><span class='item'><label><input type='checkbox' id='delpath' name='path'><span>" + lan.site.root_dir + "</span></label></span></div>";
        bt.show_confirm(lan.site.site_del_title + "[" + wname + "]", lan.site.site_del_info, function () {
            var ftp = '', data = '', path = '',data = { id: wid, webname: wname }
            if ($("#delftp").is(":checked")) data.ftp = 1;
            if ($("#deldata").is(":checked")) data.database = 1;
            if ($("#delpath").is(":checked")) data.path = 1;
            bt.site.del_site(data, function (rdata) {
                if(rdata.status) callback?callback(rdata):site.get_list();
                bt.msg(rdata);
            });
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
                bt.site.get_type(function (tdata){
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
        site.reader_site_type(rdata);
        if(callback) callback(rdata);
      });
  	},
    ssl: {
        my_ssl_msg : null,

        //续签订单内
        renew_ssl: function (siteName,auth_type,index) {
            acme.siteName = siteName;
            if(index.length === 32 && index.indexOf('/') === -1){
                acme.renew(index,function(rdata) {
                    site.ssl.ssl_result(rdata,auth_type,siteName)
                });
            }else{
                acme.get_cert_init(index,siteName,function(cert_init){
                    acme.domains = cert_init.dns;
                    var options = '<option value="http">文件验证 - HTTP</option>';
                    for(var i=0;i<cert_init.dnsapi.length;i++){
                        options += '<option value="'+cert_init.dnsapi[i].name+'">DNS验证 - '+cert_init.dnsapi[i].title+'</option>';
                    }
                    acme.select_loadT = layer.open({
                        title: '续签Let\'s Encrypt证书',
                        type:1,
                        closeBtn:2,
                        shade: 0.3,
                        area: "500px",
                        offset: "30%",
                        content: '<div style="margin: 10px;">\
                                    <div class="line ">\
                                        <span class="tname" style="padding-right: 15px;margin-top: 8px;">请选择验证方式</span>\
                                        <div class="info-r label-input-group ptb10">\
                                            <select class="bt-input-text" name="auth_to">'+options+'</select>\
                                            <span class="dnsapi-btn"></span>\
                                            <span class="renew-onkey"><button class="btn btn-success btn-sm mr5" style="margin-left: 10px;" onclick="site.ssl.renew_ssl_other()">一键续签</button></span>\
                                        </div>\
                                    </div>\
                                    <ul class="help-info-text c7">\
                                        <li>通配符证书不能使用【文件验证】，请选择DNS验证</li>\
                                        <li>使用【文件验证】，请确保没有开[启强制HTTPS/301重定向/反向代理]等功能</li>\
                                        <li>使用【阿里云DNS】【DnsPod】等验证方式需要设置正确的密钥</li>\
                                        <li>续签成功后，证书将在下次到期前30天尝试自动续签</li>\
                                        <li>使用【DNS验证 - 手动解析】续签的证书无法实现下次到期前30天自动续签</li>\
                                    </ul>\
                                  </div>',
                        success:function(layers){
                            $("select[name='auth_to']").change(function(){
                                var dnsapi = $(this).val();
                                $(".dnsapi-btn").html('');
                                for(var i=0;i<cert_init.dnsapi.length;i++){
                                    if(cert_init.dnsapi[i].name !== dnsapi) continue;
                                    acme.dnsapi = cert_init.dnsapi[i]
                                    if(!cert_init.dnsapi[i].data) continue;
                                    $(".dnsapi-btn").html('<button class="btn btn-default btn-sm mr5 set_dns_config" onclick="site.ssl.show_dnsapi_setup()">设置</button>');
                                    if(cert_init.dnsapi[i].data[0].value || cert_init.dnsapi[i].data[1].value) break;
                                    site.ssl.show_dnsapi_setup();
                                }
                            });
                        }
                    });
                });
            }
        },
        //续签其它
        renew_ssl_other: function(){
            var auth_to = $("select[name='auth_to']").val()
            var auth_type = 'http'
            if(auth_to === 'http'){
                if(JSON.stringify(acme.domains).indexOf('*.') !== -1){
                    layer.msg("包含通配符的域名不能使用文件验证(HTTP)!",{icon:2});
                    return;
                }
                auth_to = acme.id
            }else{
                if(auth_to !== 'dns'){
                    if(auth_to === "Dns_com"){
                        acme.dnsapi.data = [{value:"None"},{value:"None"}];
                    }
                    if(!acme.dnsapi.data[0].value || !acme.dnsapi.data[1].value){
                        layer.msg("请先设置【"+acme.dnsapi.title+"】接口信息!",{icon:2});
                        return;
                    }
                    auth_to = auth_to + '|' + acme.dnsapi.data[0].value + '|' + acme.dnsapi.data[1].value;
                }
                auth_type = 'dns'
            }
            layer.close(acme.select_loadT);
            acme.apply_cert(acme.domains,auth_type,auth_to,'0',function(rdata){
                site.ssl.ssl_result(rdata,auth_type,acme.siteName);
            });
        },
        show_dnsapi_setup: function(){
            var dnsapi = acme.dnsapi;
            acme.dnsapi_loadT = layer.open({
                title: '设置【'+dnsapi.title+'】接口',
                type:1,
                closeBtn:0,
                shade: 0.3,
                area: "550px",
                offset: "30%",
                content: '<div class="bt-form bt-form pd20 pb70 ">\
                            <div class="line ">\
                                <span class="tname" style="width: 125px;">'+dnsapi.data[0].key+'</span>\
                                <div class="info-r" style="margin-left:120px">\
                                    <input name="'+dnsapi.data[0].name+'" class="bt-input-text mr5 dnsapi-key" type="text" style="width:330px" value="'+dnsapi.data[0].value+'">\
                                </div>\
                            </div>\
                            <div class="line ">\
                                <span class="tname" style="width: 125px;">'+dnsapi.data[1].key+'</span>\
                                <div class="info-r" style="margin-left:120px">\
                                    <input name="'+dnsapi.data[1].name+'" class="bt-input-text mr5 dnsapi-token" type="text" style="width:330px" value="'+dnsapi.data[1].value+'">\
                                </div>\
                            </div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-sm btn-danger" onclick="layer.close(acme.dnsapi_loadT);">关闭</button>\
                                <button type="button" class="btn btn-sm btn-success dnsapi-save">保存</button>\
                            </div>\
                            <ul class="help-info-text c7">\
                                <li>'+dnsapi.help+'</li>\
                            </ul>\
                          </div>',
                success:function(layers){
                    $(".dnsapi-save").click(function(){
                        var dnsapi_key = $(".dnsapi-key");
                        var dnsapi_token = $(".dnsapi-token");
                        pdata = {}
                        pdata[dnsapi_key.attr("name")] = dnsapi_key.val();
                        pdata[dnsapi_token.attr("name")] = dnsapi_token.val();
                        acme.dnsapi.data[0].value = dnsapi_key.val();
                        acme.dnsapi.data[1].value = dnsapi_token.val();
                        bt.site.set_dns_api({ pdata: JSON.stringify(pdata) }, function (ret) {
                            if(ret.status) layer.close(acme.dnsapi_loadT);
                            bt.msg(ret);
                        });
                    });
                }
            });
        },
        set_cert: function(siteName,res){
            var loadT = bt.load(lan.site.saving_txt);
            var pdata = {
                type:1,
                siteName:siteName,
                key:res.private_key,
                csr:res.cert + res.root
            }
            bt.send('SetSSL','site/SetSSL',pdata,function(rdata){
                loadT.close();
                site.reload();
                layer.msg(res.msg,{icon:1});
            })
        },
        show_error:function(res,auth_type){
            var area_size = '500px';
            var err_info = "";
            if(res.msg[1].challenges === undefined){
                err_info += "<p><span>响应状态:</span>" + res.msg[1].status + "</p>"
                err_info += "<p><span>错误类型:</span>" + res.msg[1].type + "</p>"
                err_info += "<p><span>错误代码:</span>" + res.msg[1].detail + "</p>"
            }else{
                if (!res.msg[1].challenges[1]) {
                    if (res.msg[1].challenges[0]) {
                        res.msg[1].challenges[1] = res.msg[1].challenges[0]
                    }
                }
                if (res.msg[1].status === 'invalid') {
                    area_size = '600px';
                    var trs = $("#dns_txt_jx tbody tr");
                    var dns_value = "";

                    for (var imd = 0; imd < trs.length; imd++) {
                        if (trs[imd].outerText.indexOf(res.msg[1].identifier.value) == -1) continue;
                        var s_tmp = trs[imd].outerText.split("\t")
                        if (s_tmp.length > 1) {
                            dns_value = s_tmp[1]
                            break;
                        }
                    }
                    
                    err_info += "<p><span>验证域名:</span>" + res.msg[1].identifier.value + "</p>"
                    if(auth_type === 'dns'){
                        var check_url = "_acme-challenge." + res.msg[1].identifier.value
                        err_info += "<p><span>验证解析:</span>"+check_url+"</p>"
                        err_info += "<p><span>验证内容:</span>" + dns_value + "</p>"
                        err_info += "<p><span>错误代码:</span>" + site.html_encode(res.msg[1].challenges[1].error.detail) + "</p>"
                    }else{
                        var check_url = "http://" + res.msg[1].identifier.value + '/.well-known/acme-challenge/' + res.msg[1].challenges[0].token
                        err_info += "<p><span>验证URL:</span><a class='btlink' href='" + check_url+"' target='_blank'>点击查看</a></p>"
                        err_info += "<p><span>验证内容:</span>" + res.msg[1].challenges[0].token + "</p>"
                        err_info += "<p><span>错误代码:</span>" + site.html_encode(res.msg[1].challenges[0].error.detail) + "</p>"
                    }
                    err_info += "<p><span>验证结果:</span> <a style='color:red;'>验证失败</a></p>"
                }
            }

            layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + res.msg[0]+ '</a>' + err_info + '</div>', {
                icon: 2, time: 0,
                shade:0.3,
                shadeClose: true,
                area: area_size
            });
        },
        ssl_result: function(res,auth_type,siteName){
            layer.close(acme.loadT);
            if(res.status === false && typeof(res.msg) === 'string'){
                bt.msg(res);
                return;
            }
            if(res.status === true || res.status === 'pending' || res.save_path !== undefined){
                if(auth_type == 'dns' && res.status === 'pending'){
                    var b_load = bt.open({
                        type: 1,
                        area: '700px',
                        title: '手动解析TXT记录',
                        closeBtn: 2,
                        shift: 5,
                        shadeClose: false,
                        content: "<div class='divtable pd15 div_txt_jx'>\
                                    <p class='mb15' >请按以下列表做TXT解析:</p>\
                                    <table id='dns_txt_jx' class='table table-hover'></table>\
                                    <div class='text-right mt10'>\
                                        <button class='btn btn-success btn-sm btn_check_txt' >验证</button>\
                                    </div>\
                                    </div>"
                    });

                    //手动验证事件
                    $('.btn_check_txt').click(function () {
                        acme.auth_domain(res.index,function(res1){
                            layer.close(acme.loadT);
                            if(res1.status === true){
                                b_load.close()
                                site.ssl.set_cert(siteName,res1)
                            }else{
                                site.ssl.show_error(res1,auth_type);
                            }
                        })
                        
                    });

                    //显示手动验证信息
                    setTimeout(function () {
                        var data = [];
                        acme_txt = '_acme-challenge.'
                        for (var j = 0; j < res.auths.length; j++) {
                            data.push({ 
                                    name: acme_txt + res.auths[j].domain.replace('*.',''),
                                    type:"TXT",
                                    txt: res.auths[j].auth_value,
                                    force:"是"
                                });
                            data.push({ 
                                name: res.auths[j].domain.replace('*.',''),
                                type:"CAA",
                                txt: '0 issue "letsencrypt.org"',
                                force:"否"
                            });
                        }
                        bt.render({
                            table: '#dns_txt_jx',
                            columns: [
                                { field: 'name', width: '220px', title: '解析域名' },
                                { field: 'txt', title: '记录值' },
                                { field: 'type', title: '类型' },
                                { field: 'force', title: '必需' }
                            ],
                            data: data
                        })
                        $('.div_txt_jx').append(bt.render_help([
                            '解析域名需要一定时间来生效,完成所以上所有解析操作后,请等待1分钟后再点击验证按钮', 
                            '可通过CMD命令来手动验证域名解析是否生效: nslookup -q=txt ' + acme_txt + res.auths[0].domain.replace('*.',''), 
                            '若您使用的是宝塔云解析插件,阿里云DNS,DnsPod作为DNS,可使用DNS接口自动解析'
                        ]));
                    });
                    return;
                }
                site.ssl.set_cert(siteName,res)
                return;
            }
            
            site.ssl.show_error(res,auth_type);
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
        set_ssl_status: function (action, siteName, ssl_id) {
            bt.site.set_ssl_status(action, siteName, function (rdata) {
                bt.msg(rdata);
                if (rdata.status) {
                    site.reload(7);
                    if(ssl_id != undefined){
                        setTimeout(function(){
                            $('#ssl_tabs span:eq('+ ssl_id +')').click();
                        },1000)
                    } 
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
            var list = [
                {
                    class:'mb0',items: [
                        { name: 'newdomain', width: '340px', type: 'textarea', placeholder: '每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88' },
                        {
                            name: 'btn_submit_domain', text: '添加', type: 'button', callback: function (sdata) {
                                var arrs = sdata.newdomain.split("\n");
                                var domins = "";
                                for (var i = 0; i < arrs.length; i++) domins += arrs[i] + ",";
                                bt.site.add_domains(web.id,web.name, bt.rtrim(domins, ','), function (ret) {
                                    if (ret.status) site.reload(0)
                                })
                            }
                        }
                    ]
                }
            ]
            var _form_data = bt.render_form_line(list[0]),loadT = null,placeholder = null;
            $('#webedit-con').html(_form_data.html + "<div class='bt_table' id='domain_table'></div>");
            bt.render_clicks(_form_data.clicks);
            $('.btn_submit_domain').addClass('pull-right').css("margin", "30px 35px 0 0");
            placeholder = $(".placeholder");
            placeholder.click(function () {
                $(this).hide();
                $('.newdomain').focus();
            }).css({ 'width':'340px', 'heigth':'100px','left': '0px', 'top': '0px',  'padding-top': '10px','padding-left': '15px'})
            $('.newdomain').focus(function(){ 
                placeholder.hide();
                console.log(placeholder)
                loadT = layer.tips(placeholder.html(),$(this),{tips:[1,'#20a53a'],time:0,area:$(this).width()});
            }).blur(function(){
                if($(this).val().length == 0) placeholder.show();
                layer.close(loadT);
            });
            bt_tools.table({
                el:'#domain_table',
                url:'/data?action=getData',
                param:{table:'domain',list:'True',search:web.id},
                dataFilter:function(res){
                    return {data:res};
                },
                column:[
                    {type:'checkbox',width:20,keepNumber:1},
                    {fid:'name',title:'域名',template:function(row){
                        return '<a href="http://' + row.name + ':' + row.port + '" target="_blank" class="btlink">'+ row.name +'</a>';
                    }},
                    {fid:'port',title:'端口',width:50,type:'text'},
                    {title:'操作',width:80,type:'group',align:'right',group:[{
                        title:'删除',
                        template:function(row,that){
                            return that.data.length === 1?'<span>不可操作</span>':'删除';
                        },
                        event:function(row,index,ev,key,that){
                            if(that.data.length === 1){
                                bt.msg({status:false,msg:'最后一个域名不能删除!'});
                                return false;
                            }
                            bt.confirm({title:'删除域名【'+ row.name +'】', msg: lan.site.domain_del_confirm }, function () {
                                bt.site.del_domain(web.id,web.name,row.name,row.port,function(res){
                                    if(res.status) that.$delete_table_row(index);
                                    bt.msg(res);
                                });
                            });
                        }
                    }]
                }],
                tootls:[{ // 批量操作
                    type:'batch',
                    positon:['left','bottom'],
                    config:{
                        title:'删除',
                        url:'/site?action=delete_domain_multiple',
                        param:{id:web.id},
                        paramId:'id',
                        paramName:'domains_id',
                        theadName:'域名',
                        confirmVerify:false //是否提示验证方式
                    }
                }]
            });
            $('#domain_table>.divtable').css('max-height','350px');
        },
        set_dirbind: function (web) {
            var _this = this;
            $('#webedit-con').html('<div id="sub_dir_table"></div>');
            bt_tools.table({
                el:'#sub_dir_table',
                url:'/site?action=GetDirBinding',
                param:{id:web.id},
                dataFilter:function(res){
                    if($('#webedit-con').children().length === 2) return {data:res.binding}
                    var dirs = [];
                    for (var n = 0; n < res.dirs.length; n++) dirs.push({ title: res.dirs[n], value: res.dirs[n] });
                    var data = {
                        title: '',class:'mb0',items: [
                            { title: '域名', width: '140px', name: 'domain'},
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
                    $('#webedit-con').prepend(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                    return {data:res.binding};
                },
                column:[
                    {type:'checkbox',width:20,keepNumber:1},
                    {fid:'domain',title:'域名',type:'text'},
                    {fid:'port',title:'端口',width:70,type:'text'},
                    {fid:'path',title:'子目录',width:70,type:'text'},
                    {title:'操作',width:110,type:'group',align:'right',group:[{
                        title:'伪静态',
                        event:function(row,index,ev,key,that){
                            bt.site.get_dir_rewrite({ id: row.id }, function (ret) {
                                if (!ret.status) {
                                    var confirmObj = layer.confirm(lan.site.url_rewrite_alter, { icon: 3, closeBtn: 2 }, function () {
                                        bt.site.get_dir_rewrite({ id: row.id, add: 1 }, function (ret) {
                                            layer.close(confirmObj);
                                            show_dir_rewrite(ret);
                                        });
                                    });
                                    return;
                                }
                                show_dir_rewrite(ret);
                                function get_rewrite_file(name){
                                    var spath = '/www/server/panel/rewrite/' + (bt.get_cookie('serverType') == 'openlitespeed'?'apache':bt.get_cookie('serverType')) + '/' + name + '.conf';
                                    if(bt.get_cookie('serverType') == 'nginx'){
                                        if(name == 'default') spath = '/www/server/panel/vhost/rewrite/'+ web.name +'_'+row['path'] + '.conf';
                                    }else{
                                        if(name == 'default') spath = '/www/wwwroot/'+ web.name +'/'+row['path'] + '.htaccess';
                                    }
                                    bt.files.get_file_body(spath, function(sdata){
                                        $('.dir_config').text(sdata.data);
                                    });
                                }
                                function show_dir_rewrite(ret){
                                    var load_form = bt.open({
                                        type: 1,
                                        area: ['510px','515px'],
                                        title: lan.site.config_url,
                                        closeBtn: 2,
                                        shift: 5,
                                        skin: 'bt-w-con',
                                        shadeClose: true,
                                        content: "<div class='bt-form webedit-dir-box dir-rewrite-man-con'></div>",
                                        success:function(){
                                            var _html = $(".webedit-dir-box"),arrs = [];
                                            for (var i = 0; i < ret.rlist.length; i++){
                                                if(i == 0){
                                                    arrs.push({ title: ret.rlist[i], value: 'default'});
                                                }else{
                                                    arrs.push({ title: ret.rlist[i], value: ret.rlist[i] });
                                                }
                                            } 
                                            var datas = [{
                                                name: 'dir_rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                                                    get_rewrite_file(obj.val());
                                                }
                                            },
                                            { items: [{ name: 'dir_config', type: 'textarea', value: ret.data, width: '470px', height: '260px' }] },
                                            {
                                                items: [{
                                                    name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                                                        console.log(ret)
                                                        bt.files.set_file_body(ret.filename, ldata.dir_config, 'utf-8', function (sdata) {
                                                            if (sdata.status) load_form.close();
                                                            bt.msg(sdata);
                                                        })
                                                    }
                                                }]
                                            }]
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
                                            get_rewrite_file($('.dir_rewrite option:eq(0)').val());
                                        }
                                    });
                                }
                            })
                        }
                    },{
                        title:'删除',
                        event:function(row,index,ev,key,that){
                            bt.confirm({title:'删除子目录绑定【'+ row.path +'】', msg: lan.site.s_bin_del }, function () {
                                bt.site.del_dirbind(row.id, function (res) {
                                    if(res.status) that.$delete_table_row(index);
                                    bt.msg(res);
                                })
                            });
                        }
                    }]
                }],
                tootls:[{ // 批量操作
                    type:'batch',
                    positon:['left','bottom'],
                    config:{
                        title:'删除',
                        url:'/site?action=delete_dir_bind_multiple',
                        param:{id:web.id},
                        paramId:'id',
                        paramName:'bind_ids',
                        theadName:'域名',
                        confirmVerify:false //是否提示验证方式
                    }
                }]
            });
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
                                { name: 'path', title: '网站目录', width: '240px', value: path, event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
                                {
                                    name: 'btn_site_path',class:"ml10",type: 'button', text: '保存', callback: function (pdata) {
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
                                { title: '运行目录', width: '240px', value: rdata.runPath.runPath, name: 'dirName', type: 'select', items: dirs },
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
            $('#webedit-con').html('<div id="set_dirguard"></div>');
            var tab = '<div class="tab-nav mlr20">\
                    <span class="on">加密访问</span><span class="">禁止访问</span>\
                    </div>\
                    <div id="dir_dirguard" class="pd20"></div>\
                    <div id="php_dirguard" class="pd20" style="display:none;"></div>';
            $("#set_dirguard").html(tab)
            bt_tools.table({
                el:'#dir_dirguard',
                url:'/site?action=get_dir_auth',
                param:{id:web.id},
                dataFilter:function(res){
                    return {data:res[web.name]};
                },
                column:[
                    {type:'checkbox',width:20},
                    {fid:'name',title:'名称',type:'text'},
                    {fid:'site_dir',title:'加密访问',type:'text'},
                    {title:'操作',width:110,type:'group',align:'right',group:[{
                        title:'编辑',
                        event:function(row,index,ev,key,that){
                            site.edit.template_Dir(web.id,false,row);
                        }
                    },{
                        title:'删除',
                        event:function(row,index,ev,key,that){
                            bt.site.delete_dir_guard(web.id,row.name,function(res){
                                if(res.status) that.$delete_table_row(index);
                                bt.msg(res);
                            });
                        }
                    }],
                }],
                tootls:[{ // 按钮组
                    type:'group',
                    positon:['left','top'],
                    list:[{title:'添加加密访问',active:true, event:function(ev){ 
                        site.edit.template_Dir(web.id,true);
                    }}]
                },{ // 批量操作
                    type:'batch',
                    positon:['left','bottom'],
                    config:{
                        title:'删除',
                        url:'/site?action=delete_dir_auth_multiple',
                        param:{site_id:web.id},
                        paramId:'name',
                        paramName:'names',
                        theadName:'加密访问名称',
                        confirmVerify:false //是否提示验证方式
                    }
                }]
            });
            bt_tools.table({
                el:'#php_dirguard',
                url:'/config?action=get_file_deny',
                param:{website:web.name},
                dataFilter:function(res){
                    return {data:res};
                },
                column:[
                    {fid:'name',title:'名称',type:'text'},
                    {fid:'dir',title:'保护的目录',type:'text', template:function(row){
                        return '<span title="' + row.dir + '" style="max-width: 250px;text-overflow: ellipsis;overflow: hidden;display: inline-block;">' + row.dir + '</span>';
                    }},
                    {fid: 'suffix', title: '规则', template:function(row){
                        return '<span title="' + row.suffix + '" style="max-width: 85px;text-overflow: ellipsis;overflow: hidden;display: inline-block;">' + row.suffix + '</span>';
                    }},
                    {title:'操作',width:110,type:'group',align:'right',group:[{
                        title:'编辑',
                        event:function(row,index,ev,key,that){
                            site.edit.template_php(web.name,row);
                        }
                    },{
                        title:'删除',
                        event:function(row,index,ev,key,that){
                            bt.site.delete_php_guard(web.name,row.name,function(res){
                                if(res.status) that.$delete_table_row(index);
                                bt.msg(res);
                            });
                        }
                    }],
                }],
                tootls:[{ // 按钮组
                    type:'group',
                    positon:['left','top'],
                    list:[{title:'添加禁止访问',active:true, event:function(ev){ 
                        site.edit.template_php(web.name);
                    }}]
                }]
            });
            $('#dir_dirguard>.divtable,#php_dirguard>.divtable').css('max-height','405px');
            $('#dir_dirguard').append("<ul class='help-info-text c7'>\
                <li>目录设置加密访问后，访问时需要输入账号密码才能访问</li>\
                <li>例如我设置了加密访问 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>\
            </ul>");
            $('#php_dirguard').append("<ul class='help-info-text c7'>\
                <li>后缀：禁止访问的文件后缀</li>\
                <li>目录：规则会在这个目录内生效</li>\
            </ul>");
            $("#set_dirguard").on('click', '.tab-nav span',function () {
                var index = $(this).index();
                $(this).addClass('on').siblings().removeClass('on');
                if (index == 0) {
                    $("#dir_dirguard").show();
                    $("#php_dirguard").hide();
                } else {
                    $("#php_dirguard").show();
                    $("#dir_dirguard").hide();
                }
            });
        },
        ols_cache: function(web) {
            bt.send('get_ols_static_cache', 'config/get_ols_static_cache', { id: web.id }, function(rdata) {
                var clicks = [],
                    newkey = [],
                    newval = [],
                    checked = false;
                Object.keys(rdata).forEach(function(key){
                //for (let key in rdata) {
                    newkey.push(key);
                    newval.push(rdata[key]);
                });
                var datas = [{ title: newkey[0], name: newkey[0], width: '30%', value: newval[0] },
                        { title: newkey[1], name: newkey[1], width: '30%', value: newval[1] },
                        { title: newkey[2], name: newkey[2], width: '30%', value: newval[2] },
                        { title: newkey[3], name: newkey[3], width: '30%', value: newval[3] },
                        {
                            name: 'static_save',
                            text: '保存',
                            type: 'button',
                            callback: function(ldata) {
                                var cdata = {},
                                    loadT = bt.load();
                                Object.assign(cdata, ldata);
                                delete cdata.static_save;
                                delete cdata.maxage;
                                delete cdata.exclude_file;
                                delete cdata.private_save;
                                bt.send('set_ols_static_cache', 'config/set_ols_static_cache', { values: JSON.stringify(cdata), id: web.id }, function(res) {
                                    loadT.close();
                                    bt.msg(res)
                                });
                            }
                        },
                        { title: 'test', name: 'test', width: '30%', value: '11' },
                        { title: '缓存时间', name: 'maxage', width: '30%', value: '43200' },
                        { title: '排除文件', name: 'exclude_file', width: '35%', value: 'fdas.php', },
                        {
                            name: 'private_save',
                            text: '保存',
                            type: 'button',
                            callback: function(ldata) {
                                var edata = {},
                                    loadT = bt.load();
                                if (checked) {
                                    edata.id = web.id;
                                    edata.max_age = parseInt($("input[name='maxage']").val());
                                    edata.exclude_file = $("textarea[name='exclude_file']").val();
                                    bt.send('set_ols_private_cache', 'config/set_ols_private_cache', edata, function(res) {
                                        loadT.close();
                                        bt.msg(res)
                                    });
                                }
                            }
                        }
                    ],
                    _html = $('<div class="ols"></div>');
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    _html.append(_form_data.html);
                    clicks = clicks.concat(_form_data.clicks);
                };
                $('#webedit-con').append(_html);
                $("input[name='exclude_file']").parent().removeAttr('class').html('<textarea name="exclude_file" class="bt-input-text mr5 exclude_file" style="width:35%;height: 130px;"></textarea>');
                $("input[name='test']").parent().parent().html('<div style="padding-left: 29px;border-top: #ccc 1px dashed;margin-top: -7px;"><em style="float: left;color: #555;font-style: normal;line-height: 32px;padding-right: 2px;">私有缓存</em><div style="margin-left: 70px;padding-top: 5px;"><input class="btswitch btswitch-ios" id="ols" type="checkbox"><label class="btswitch-btn" for="ols"></label></div></div>');
                var private = $("input[name='maxage'],textarea[name='exclude_file'],button[name='private_save']").parent().parent();
                $("input.bt-input-text").parent().append('<span>秒</span>');
                $("button[name='static_save']").parent().append(bt.render_help(['默认的静态文件缓存时间是604800秒', '如果要关闭，请将其更改为0秒']));
                $(".ols").append(bt.render_help(['私有缓存只支持PHP页面缓存，默认缓存时间为120秒', '排除文件仅支持以PHP为后缀的文件']));
                private.hide();
                var loadT = bt.load();
                bt.send('get_ols_private_cache_status', 'config/get_ols_private_cache_status', { id: web.id }, function(kdata) {
                    loadT.close();
                    checked = kdata;
                    if (kdata) {
                        bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function(fdata) {
                            $("input[name='maxage']").val(fdata.maxage);
                            var ss = fdata.exclude_file.join("&#13;");
                            $("textarea[name='exclude_file']").html(ss);
                            $("#ols").attr('checked', true);
                            private.show();
                        });
                    }
                });
                $('#ols').on('click', function() {
                    var loadS = bt.load();
                    bt.send('switch_ols_private_cache', 'config/switch_ols_private_cache', { id: web.id }, function(res) {
                        loadS.close();
                        private.toggle();
                        checked = private.is(':hidden') ? false : true;
                        bt.msg(res);
                        if (checked) {
                            bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function(fdata) {
                                private.show();
                                $("input[name='maxage']").val(fdata.maxage);
                                $("textarea[name='exclude_file']").html(fdata.exclude_file.join("&#13;"));
                            });
                        }
                    });
                });
                bt.render_clicks(clicks);
                $("button[name='private_save']").parent().css("margin-bottom", "-13px");
                $('.ss-text').css("margin-left", "66px");
                $('.ols .btn-success').css("margin-left", "100px");
            })
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
                var arrs = [], webserver = bt.get_cookie('serverType');
                if (bt.get_cookie('serverType') == 'apache') filename = rdata.sitePath + '/.htaccess';
                if (webserver == 'apache' || webserver == 'openlitespeed') filename = rdata.sitePath + '/.htaccess';
                if (webserver == 'openlitespeed') webserver = 'apache';
                for (var i = 0; i < rdata.rewrite.length; i++) arrs.push({ title: rdata.rewrite[i], value: rdata.rewrite[i] });

                var datas = [{
                    name: 'rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                        if (bt.os == 'Linux') {
                            var spath = filename;
                            if (obj.val() != lan.site.rewritename) spath = '/www/server/panel/rewrite/' + (webserver == 'openlitespeed'?'apache':webserver) + '/' + obj.val() + '.conf';
                            bt.files.get_file_body(spath, function (ret) {
                                aceEditor.ACE.setValue(ret.data);
                                aceEditor.ACE.moveCursorTo(0, 0); 
                                aceEditor.path = spath;
                            })
                        }
                    }
                },
                { items: [{ name: 'config', type: 'div', value: rdata.data, widht: '340px', height: '200px' }] },
                {
                    items: [{
                        name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                            // bt.files.set_file_body(filename, editor.getValue(), 'utf-8', function (ret) {
                            //     if (ret.status) site.reload(4)
                            //     bt.msg(ret);
                            // })
                            aceEditor.path = filename;
                            bt.saveEditor(aceEditor);
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
                                            bt.site.set_rewrite_tel(rdata.tempname, aceEditor.ACE.getValue(), function (rRet) {
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
                $('div.config').attr('id', 'config_rewrite').css({'height':'360px','width':'540px'})
                var aceEditor = bt.aceEditor({el:'config_rewrite',content:rdata.data});
                $('select.rewrite').trigger('change');
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
        	var con = '<p style="color: #666; margin-bottom: 7px">提示：Ctrl+F 搜索关键字，Ctrl+S 保存，Ctrl+H 查找替换</p><div class="bt-input-text ace_config_editor_scroll" style="height: 400px; line-height:18px;" id="siteConfigBody"></div>\
				<button id="OnlineEditFileBtn" class="btn btn-success btn-sm" style="margin-top:10px;">保存</button>\
				<ul class="c7 ptb15">\
					<li>此处为站点主配置文件,若您不了解配置规则,请勿随意修改.</li>\
				</ul>';
			$("#webedit-con").html(con);
			var webserve = bt.get_cookie('serverType'),
            config = bt.aceEditor({ el: 'siteConfigBody', path: '/www/server/panel/vhost/' + (webserve == 'openlitespeed' ? (webserve + '/detail') : webserve) + '/' + web.name + '.conf' });
    		$("#OnlineEditFileBtn").click(function(e){
				bt.saveEditor(config);
			});
        },
        set_ssl: function (web) {
            $('#webedit-con').html("<div id='ssl_tabs'></div><div class=\"tab-con\" style=\"padding:10px 0px;\"></div>");
            bt.site.get_site_ssl(web.name, function (rdata) {
                var _tabs = [
                                        {
                        title:"商用证书<i class='ssl_recom_icon'></i>",callback:function(robj){
                            var deploy_ssl_info = rdata;
                            var html = '',product_list,userInfo,loadT = bt.load('正在获取商用证书订单列表，请稍候...'),order_list,is_check = true,itemData,activeData,loadY;
                            bt.send('get_order_list','ssl/get_order_list',{},function(rdata){
                                loadT.close();
                                order_list = rdata;
                                $.each(rdata,function(index,item){
                                    if(deploy_ssl_info.type == 3  && deploy_ssl_info.oid === item.oid){
                                        html += '<tr data-index="'+ index +'">'+
                                        '<td><span>'+ item.domainName.join('、') +'</span></td><td>'+ item.title +'</td><td>'+ (function(){
                                                    var dayTime = new Date().getTime() / 1000,color = '',endTiems = '';
                                                    if(item.endDate != ''){
                                                        item.endDate = parseInt(item.endDate);
                                                        endTiems = parseInt((item.endDate - dayTime) / 86400);
                                                        if(endTiems <= 15) color = 'orange';
                                                        if(endTiems <= 7) color = 'red';
                                                        if(endTiems < 0) return '<span style="color:red">已过期</span>';
                                                        return '<span style="'+ color +'">剩余'+ endTiems + '天</span>';
                                                    }else{
                                                        return '--';
                                                    }
                                                }())
                                            +'</td><td>订单完成</td><td style="text-align:right">已部署&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/ssl?action=download_cert&oid='+ item.oid +'" data-type="download_ssl" class="btlink options_ssl">下载</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\''+ web.name +'\',2)">关闭</a></td></td>';
                                    }else if(deploy_ssl_info.type != 3){
                                        html += '<tr data-index="'+ index +'">'+
                                            '<td><span>'+ item.domainName.join('、') +'</span></td><td>'+ item.title +'</td><td>'+ (function(){
                                                    var dayTime = new Date().getTime() / 1000,color = '',endTiems = '';
                                                    if(item.endDate != ''){
                                                        item.endDate = parseInt(item.endDate);
                                                        endTiems = parseInt((item.endDate - dayTime) / 86400);
                                                        if(endTiems <= 15) color = 'orange';
                                                        if(endTiems <= 7) color = 'red';
                                                        if(endTiems < 0) return '<span style="color:red">已过期</span>';
                                                        return '<span style="'+ color +'">剩余'+ endTiems + '天</span>'
                                                    }else{
                                                        return '--';
                                                    }
                                                }())
                                            +'</td><td>'+ (function(){
                                                        if(item.status === 1){
                                                            switch(item.orderStatus){
                                                                case 'COMPLETE':
                                                                    return '<span style="color:#20a53a;">订单完成</span>';
                                                                break;
                                                                case 'PENDING':
                                                                    return '<span style="color: orange;">申请中</span>';
                                                                break;
                                                                case 'CANCELLED':
                                                                    return '<span style="color: #888;">已取消</span>';
                                                                break;
                                                                case 'FAILED':
                                                                    return '<span style="color:red;">申请失败</span>';
                                                                break;
                                                                default:
                                                                    return '<span style="color: orange;">待验证</span>';
                                                                break;
                                                            }
                                                        }else{
                                                            switch(item.status){
                                                                case 0:
                                                                    return '<span style="color: orange;">未支付</span>';
                                                                break;
                                                                case -1:
                                                                    return '<span style="color: #888;">已取消</span>'
                                                                break;
                                                            }
                                                        }
                                                    }())
                                            +'</td><td style="text-align:right;">'+ (function(){
                                                if(item.status === 1){
                                                    switch(item.orderStatus){
                                                        case "COMPLETE": //申请成功
                                                            return '<a href="javascript:;" data-type="deploy_ssl" class="btlink options_ssl">部署</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/ssl?action=download_cert&oid='+ item.oid +'" data-type="download_ssl" class="btlink options_ssl">下载</a>'
                                                        break;
                                                        case "PENDING": //申请中
                                                            return '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">验证</a>';
                                                        break;
                                                        case "CANCELLED": // 已取消
                                                            return '无操作';
                                                        break;
                                                        case "FAILED":
                                                            return '<a href="javascript:;" data-type="info_order" class="btlink options_ssl">详情</a>';
                                                        break;
                                                        default:
                                                            return '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">验证</a>';
                                                        break;
                                                    }
                                                }
                                            }()) +'</td>'+
                                        '</tr>';
                                    }
                                });
                                $('.ssl_order_list tbody').html(html);
                            });
                            robj.append('<div style="margin-bottom: 10px;" class="alert alert-success">此品牌证书适合生产项目使用，宝塔官网BT.CN也是用这款证书，性价比高，推荐使用</div>\
                            <div class= "mtb10" >\
                            <button class="btn btn-success btn-sm btn-title ssl_business_application" type="button">申请证书</button><span class="ml5"><a href="http://q.url.cn/CDfQPS?_type=wpa&amp;qidian=true" target="_blank" class="btlink"><img src="https://pub.idqqimg.com/qconn/wpa/button/button_old_41.gif" style="margin-right:5px;margin-left:3px;vertical-align: -1px;">售前客服: 3007255432</a></span>\
                            <div class="divtable mtb10 ssl_order_list"  style="height: 340px;overflow-y: auto;">\
                                <table class="table table-hover" id="ssl_order_list">\
                                    <thead><tr><th width="120px">域名</th><th  width="220px">证书类型</th><th>到期时间</th><th>状态</th><th style="text-align:right;">操作</th></tr></thead>\
                                    <tbody></tbody>\
                                </table>\
                            </div>\
                        </div><ul class="help-info-text c7">\
                            <li>申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                            <li>有效期1年，不支持续签，到期后需要重新申请</li>\
                            <li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li>\
                            <li><a style="color:red;">如果您的站点有使用CDN、高防IP、反向代理、301重定向等功能，可能导致验证失败</a></li>\
                            <li><a style="color:red;">申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</a></li>\
                            <li><a style="color:red;">商用证书相对于普通证书，具有更高的安全性、赔付保障和支持通配符和多域名等方式。<a class="btlink" target="_blank" href="https://www.racent.com/sectigo-ssl">点击查看</a></a></li>\
                        </ul>');
                            bt.fixed_table('ssl_order_list');
                            /**
                             * @description 对指定表单元素的内容进行效验
                             * @param {Object} el jqdom对象
                             * @param {String} name 表单元素name名称
                             * @param {*} value 表单元素的值
                             * @returns 返回当前元素的值
                             */
                            function check_ssl_user_info(el,name,value){
                                el.css('borderColor','#ccc');
                                var status;
                                switch(name){
                                    case 'domains':
                                        var list = value.split('\n');
                                        if(value == ''){
                                            set_info_tips(el,{msg:'域名不能为空！',color:'red'});
                                            status =  false;
                                        }
                                        if(!Array.isArray(list)) list = [list];
                                        $.each(list,function(index,item){
                                            if(bt.check_domain(item)){
                                                switch(activeData.code){
                                                    case 'comodo-positive-multi-domain':
                                                        if(list.length >3){
                                                            set_info_tips(el,{msg:'多域名证书默认支持3个域名,超出数量请重新申请！',color:'red'});
                                                            status =  false;
                                                        }else if(list.length == 1){
                                                            set_info_tips(el,{msg:'当前为多域名证书，需要2个域名或多个域名！',color:'red'});
                                                            status =  false;
                                                        }
                                                    break;
                                                    case 'comodo-positivessl-wildcard':
                                                        if(item.indexOf('*') != 0){
                                                            set_info_tips(el,{msg:'通配符域名格式错误,正确写法‘*.bt.cn’',color:'red'});
                                                            status = false;
                                                        }
                                                    break;
                                                    case 'comodo-positive-multi-domain-wildcard':
                                                        if(list.length > 2){
                                                            set_info_tips(el,{msg:'多域名通配符证书默认支持2个域名,超出数量请重新申请！',color:'red'});
                                                            status = false;
                                                        }else if(list.length == 1){
                                                            set_info_tips(el,{msg:'当前为多域名通配符，需要2个域名或多个域名！',color:'red'});
                                                            status =  false;
                                                        }
                                                        if(item.indexOf('*') != 0){
                                                            set_info_tips(el,{msg:'通配符域名格式错误,正确写法‘*.bt.cn’',color:'red'});
                                                            status = false;
                                                        }
                                                    break;
                                                }
                                            }else{
                                                set_info_tips(el,{msg:'【 '+ item +' 】'+',域名格式错误',color:'red'});
                                                status = false;
                                            }
                                        });
                                        value = list;
                                    break;
                                    case 'state':
                                        if(value == ''){
                                            set_info_tips(el,{msg:'所在省份不能为空！',color:'red'});
                                            status = false;
                                        }
                                    break;
                                    case 'city':
                                        if(value == ''){
                                            set_info_tips(el,{msg:'所在市/县不能为空！',color:'red'});
                                            status = false;
                                        }
                                    break;
                                    case 'organation':
                                        if(value == ''){
                                            set_info_tips(el,{msg:'公司名称不能为空，如为个人申请请输入个人姓名！',color:'red'});
                                            status = false;
                                        }
                                    break;
                                    case 'name':
                                        if(value == ''){
                                            set_info_tips(el,{msg:'用户姓名不能为空！',color:'red'});
                                            status = false;
                                        }
                                    break;
                                    case 'email':
                                        if(value == ''){
                                            set_info_tips(el,{msg:'用户邮箱地址不能为空！',color:'red'});
                                            status = false;
                                        }
                                        if(!bt.check_email(value)){
                                            set_info_tips(el,{msg:'用户邮箱地址格式错误！',color:'red'});
                                            status = false;
                                        }
                                    break;
                                    case 'mobile':
                                        if(value != ''){
                                            if(!bt.check_phone(value)){
                                                set_info_tips(el,{msg:'用户手机号码格式错误！',color:'red'});
                                                status = false;
                                            }
                                        }
                                    break;
                                    default:
                                        status = value;
                                    break;
                                }
                                if(typeof status == "boolean" && status === false) return false;
                                status = value;
                                return status;
                            }

                            /**
                             * @description 设置元素的提示和边框颜色
                             * @param {Object} el jqdom对象 
                             * @param {Object} config  = {
                             *  @param {String} config.msg 提示内容
                             *  @param {String} config.color 提示颜色
                             * }
                            */
                            function set_info_tips(el,config){
                                $('html').append($('<span id="width_test">'+ config.msg +'</span>'));
                                layer.tips(config.msg,el,{tips:[1,config.color],time:3000,area:($('#width_test').width() + 20) +'px'});
                                el.css('borderColor',config.color);
                                $('#width_test').remove();
                            }
                            /**
                             * @description 更换域名验证方式
                             * @param {Number} oid 域名订单ID
                             * @returns void
                             */
                            function again_verify_veiw(oid, is_success) {
                                var loads = bt.load('正在获取验证方式,请稍候...');
                                bt.send('get_verify_result', 'ssl/get_verify_result', { oid: oid }, function (res) {
                                    loads.close();
                                    var type = res.data.dcvList[0].dcvMethod 

                                    loadT = bt.open({
                                        type: 1,
                                        title: '验证域名-' + (type ? '文件验证' : 'DNS验证'),
                                        area: '500px',
                                        btn:['更改','取消'],
                                        content: '<div class="bt-form pd15">\
		                                        <div class="line"><span class="tname">验证方式</span>\
		                                        <div class="info-r"><select class="bt-input-text mr5" name="file_rule" style="width:250px"></select>\
	                                        	</div>\
	                                        </div>\
	                                    <ul class="help-info-text c7"><li>文件验证（HTTP）：确保网站能够通过http正常访问</li><li>文件验证（HTTPS）：确保网站已开启https，并且网站能够通过https正常访问</li><li>DNS验证：需要手动解析DNS记录值</li></ul></div>',
                                        success: function (layero, index) {
                                            //'HTTP_CSR_HASH','CNAME_CSR_HASH','HTTPS_CSR_HASH'
                                            var _option_list = {'文件验证(HTTP)':'HTTP_CSR_HASH','文件验证(HTTPS)':'HTTPS_CSR_HASH','DNS验证(CNAME解析)':'CNAME_CSR_HASH'},
                                                _option = '';
                                            
                                            $.each(_option_list,function(index,item){                                            	
                                            	_option += '<option value="'+item+'" '+(type == item ? 'selected':'')+'>'+index+'</option>'
                                            })
                                            $('select[name=file_rule]').html(_option)
                                        },
                                        yes:function(index,layero){
                                        	var new_type = $('select[name=file_rule]').val();
                                            if (type == new_type) return layer.msg('重复的验证方式', { icon: 2 })
                                            var loads = bt.load('正在修改验证方式,请稍候...');
                                            bt.send('again_verify', 'ssl/again_verify', { oid: oid, dcvMethod: new_type }, function (res) {
                                                loads.close();
                                                if (res.status) layer.close(index);
												layer.msg(res.msg,{icon:res.status?1:2})
                                            })
                                        }
                                    });
                                })
                            }
                            /**
                             * @description 验证域名
                             * @param {Number} oid 域名订单ID
                             * @returns void
                             */
                            function verify_order_veiw(oid,is_success){
                                var loads = bt.load('正在获取验证结果,请稍候...');
                                bt.send('get_verify_result','ssl/get_verify_result',{oid:oid},function(res){
                                	loads.close();
                                    if(res.status == 'COMPLETE'){
                                        $('#ssl_tabs span:eq(2)').click();
                                        return false;
                                    }
                                    loadT.close();
                                    var rdata = res.data;
                                    var domains = [],type = rdata.dcvList[0].dcvMethod != 'CNAME_CSR_HASH',info = {};
                                    $.each(rdata.dcvList,function(key,item){
                                        domains.push(item['domainName']);
                                    });
                                    if (type) {
                                        info = { fileName: rdata.DCVfileName, fileContent: rdata.DCVfileContent, filePath: '/.well-known/pki-validation/', paths: res.paths,kfqq:res.kfqq };
                                    } else {
                                        info = { dnsHost: rdata.DCVdnsHost, dnsType: rdata.DCVdnsType, dnsValue: rdata.DCVdnsValue, paths: res.paths,kfqq:res.kfqq };
                                    }
                                    if(is_success){
                                    	is_success({type:type,domains:domains,info:info});
                                    	return false;
                                    }
                                    loadT = bt.open({
                                        type:1,
                                        title:'验证域名-'+ ( type?'文件验证':'DNS验证' ),
                                        area:'600px',
                                        content:reader_domains_cname_check({type:type,domains:domains,info:info}),
                                        success:function(){
                                            $('.lib-price-button button').click(function(){
                                                switch($(this).index()){
                                                    case 0:
                                                        loadT.close();
                                                        verify_order_veiw(itemData.oid);
                                                    break;
                                                    case 1:
                                                        loadT.close();
                                                    break;
                                                }
                                            });
                                            var clipboard = new ClipboardJS('.parsing_info .parsing_icon');
                                            clipboard.on('success', function(e){
                                                bt.msg({status:true,msg:'复制成功'});
                                                e.clearSelection();
                                            });
                                            clipboard.on('error', function(e) {
                                                bt.msg({status:true,msg:'复制失败，请手动ctrl+c复制！'});
                                                console.error('Action:', e.action);
                                                console.error('Trigger:', e.trigger);
                                            });
                                            $('.verify_ssl_domain').click(function(){
                                                verify_order_veiw(oid);
                                                loadT.close();
                                            });
                                            
                                            $('.set_verify_type').click(function () {
                                                again_verify_veiw(oid);  
                                                loadT.close();
                                            });
                                            
                                            $('.return_ssl_list').click(function(){
                                                loadT.close();
                                                $('#ssl_tabs span:eq(2)').click();
                                            });
                                            
                                            // 重新验证按钮
                                            $('.domains_table').on('click','.check_url_results',function(){
                                                var _url = $(this).data('url'), _con = $(this).data('content');
                                                check_url_txt(_url, _con, this)
                                             
			                                })
                                        }
                                    });
                                });
                            }

                            /**
                             * @description 重新验证
                             * @param {String} url 验证地址
                             * @param {String} content 验证内容
                             * @returns 返回验证状态
                             */
                            function check_url_txt(url, content,_this) {
                                var loads = bt.load('正在获取验证结果,请稍候...');
                                bt.send('check_url_txt', 'ssl/check_url_txt', { url: url, content: content }, function (res) {
                                    loads.close();
                                    var html = '<span style="color:red">失败[' + res +']</span><a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>'
                                    if (res === '1') {
                                        html =  '<a class="btlink">通过</a>';
                                    }
                                    $(_this).parents('tr').find('td:nth-child(2)').html(html)
                                })
                            }
                            /**
                             * @description 渲染验证模板接口
                             * @param {Object} data 验证数据
                             * @returns void
                             */
                            function reader_domains_cname_check(data) {
                                var html = '';
                                if (data.type) {

                                    var check_html = '<div class="bt-table domains_table" style="margin-bottom:20px"><div class="divtable"><table class="table table-hover"><thead><tr><th>URL</th><th style="width:85px;">验证结果</th><th style="text-align:right;width:135px;">操作</th></thead>'
                                    var paths = data.info.paths
                                    for (var i = 0; i < paths.length; i++) {
                                        check_html += '<tr><td><span title="' + paths[i].url + '" class="lib-ssl-overflow-span-style" style="word-break: break-all;">' + paths[i].url + '</span></td><td>' + (paths[i].status == 1 ? '<a class="btlink">通过</a>' : '<span style="color:red">失败[' + paths[i].status+']</span><a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>') + '</td><td style="text-align:right;"><a href="javascript:bt.pub.copy_pass(\''+paths[i].url+'\');" class="btlink">复制</a> | <a href="'+paths[i].url+'" target="_blank" class="btlink">打开</a> | <a data-url="'+paths[i].url+'" data-content="'+data.info.fileContent+'" class="btlink check_url_results">重新验证</a></td>'
                                    }
                                    check_html += '</table></div></div>'

                                    html = '<div class="lib-ssl-parsing">\
                                        <div class="parsing_tips">请给以下域名【 <span class="highlight">'+ data.domains.join('、') + '</span> 】添加验证文件，验证信息如下：</div>\
                                        <div class="parsing_parem"><div class="parsing_title">文件所在位置：</div><div class="parsing_info"><input type="text" name="filePath"  class="parsing_input border" value="'+ data.info.filePath + '" readonly="readonly" /></div></div>\
                                        <div class="parsing_parem"><div class="parsing_title">文件名：</div><div class="parsing_info"><input type="text" name="fileName" class="parsing_input" value="'+ data.info.fileName + '" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' + data.info.fileName + '">复制</span></div></div>\
                                        <div class="parsing_parem"><div class="parsing_title" style="vertical-align: top;">文件内容：</div><div class="parsing_info"><textarea name="fileValue"  class="parsing_textarea" readonly="readonly">'+ data.info.fileContent + '</textarea><span class="parsing_icon" style="display: block;width: 60px;border-radius: 3px;" data-clipboard-text="' + data.info.fileContent + '">复制</span></div></div>'
                                        + check_html +
                                        '<div class="parsing_tips" >· SSL添加文件验证方式 ->> <a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="btlink" >查看教程</a><span style="padding-left:60px">专属客服QQ：' + data.info.kfqq +'</span></div >\
                                        <div class="parsing_parem" style="padding: 0 55px;"><button type="submit" class="btn btn-success verify_ssl_domain">验证域名</button><button type="submit" class="btn btn-default return_ssl_list">返回列表</button><button type="submit" class="btn btn-success set_verify_type">修改验证方式</button></div>\
                                    </div>';
                                } else {
                                    html = '<div class="lib-ssl-parsing">\
                                        <div class="parsing_tips">请给以下域名【 <span class="highlight">'+ data.domains.join('、') + '</span> 】添加‘‘' + data.info.dnsType + '’’解析，解析参数如下：</div>\
                                        <div class="parsing_parem"><div class="parsing_title">主机记录：</div><div class="parsing_info"><input type="text" name="host" class="parsing_input" value="'+ data.info.dnsHost + '" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' + data.info.dnsHost + '">复制</span></div></div>\
                                        <div class="parsing_parem"><div class="parsing_title">记录值：</div><div class="parsing_info"><input type="text" name="domains"  class="parsing_input" value="'+ data.info.dnsValue + '" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' + data.info.dnsValue + '">复制</span></div></div>\
                                        <div class="parsing_tips">· 关于如何添加域名解析，请自行百度，和咨询服务器运营商。</div>\
                                        <div class="parsing_parem" style="padding: 0 55px;"><button type="submit" class="btn btn-success verify_ssl_domain">验证域名</button><button type="submit" class="btn btn-default return_ssl_list">返回列表</button><button type="submit" class="btn btn-success set_verify_type">修改验证方式</button></div>\
                                    </div>';
                                }
                                return html;
                            }
                            
                            //订单证书操作
                            $('.ssl_order_list').on('click','.options_ssl',function(){
                                var type = $(this).data('type'),tr = $(this).parents('tr');
                                itemData = order_list[tr.data('index')];
                                switch(type){
                                    case 'deploy_ssl': // 部署证书
                                        bt.confirm({
                                            title:'部署证书',
                                            msg:'是否部署该证书,是否继续？<br>证书类型：'+ itemData.title +' <br>证书支持域名：'+ itemData.domainName.join('、') +'<br>部署站点名:'+ web.name +''
                                        },function(){
                                        	var loads = bt.load('正在部署证书，请稍候...');
                                            bt.send('set_cert','ssl/set_cert',{oid:itemData.oid,siteName:web.name},function(rdata){
                                            	loads.close();
                                                $('#webedit-con').empty();
                                                site.edit.set_ssl(web);
                                                site.ssl.reload();
                                                bt.msg(rdata);
                                            });
                                        });
                                    break;
                                    case 'verify_order': // 验证订单
                                        verify_order_veiw(itemData.oid);
                                    break;
                                    case 'clear_order': // 取消订单
                                        bt.confirm({
                                            title:'取消订单',
                                            msg:'是否取消该订单，订单域名【'+ itemData.domainName.join('、') +'】，是否继续？'
                                        },function(){
                                            var loads = bt.load('正在取消订单，请稍候...');
                                            bt.send('cancel_cert_order','ssl/cancel_cert_order',{oid:itemData.oid},function(rdata){
                                            	loads.close();
                                                if(rdata.status){
                                                    $('#ssl_tabs span:eq(2)').click();
                                                    setTimeout(function(){
                                                        bt.msg(rdata);
                                                    },2000);
                                                }
                                                bt.msg(rdata);
                                            });
                                        })
                                    break;
                                }
                            });
                            
                            //申请证书
                            $('.ssl_business_application').click(function(){
                                var loads = bt.load('正在获取商用证书产品列表，请稍候...');
                                bt.send('get_product_list','ssl/get_product_list',{},function(res){
                                    loads.close();
                                    var list = '',userInfo = res.administrator,timeOut,is_pay_view = null;
                                    $.each(res.data,function(index,item){
                                        if(item.state){
                                            list += '<tr data-index="'+index + '"><td><input type="radio" name="ssl_radio" /><span>' + item.title + '</span></td><td style="text-align: right;">'+ (item.discount<1?'<span style="color: #bbbbbb;text-decoration: line-through;margin-right: 15px;" class="mr5">原价:'+ item.src_price.toFixed(2)  +'元/年</span>':'') + '<span style="color: #FF6232;">'+ item.price.toFixed(2) + '元/1年</span></td></tr>'
                                        }
                                    });
                                    if(list == '') list = '<div class="ssl_info_item">无证书信息</div>';
                                    var arry = [['个人使用',true,true],['企业使用',false,true],['多域名/泛域名/IP证书',false,true],['赔付保障',false,true],['技术支持',false,true]],html ='';
                                    $.each(arry,function(index,item){
                                        html+= '<tr><td class="one_title">'+ item[0] +'</td><td class="'+ (item[1]?'yes':'no') +'"></td><td class="'+ (item[2]?'yes':'no') +'"></td></tr>';
                                    });
                                    var cert_info = '<div class="bt-form business_ssl_application">\
                                        <div class="guide_body">\
                                            <div class="guide_path">\
                                                <span class="active"><i>1</i><i>选择产品</i></span>\
                                                <span><i>2</i><i>完善资料</i></span>\
                                                <span><i>3</i><i>支付订单</i></span>\
                                                <span><i>4</i><i>完成订单</i></span>\
                                            </div>\
                                            <div class="guide_path_progress" data-progress="1" style="margin: 0px 80px;"><span style="width: 0px;"></span><span style="width: 430px;"></span></div>\
                                        </div>\
                                        <div class="guide_content" data-guide="1">\
                                            <div class="line">\
                                                <span class="tname">证书品牌</span>\
                                                <div class="info-r" >\
                                                    <a href="javascript:;" class="ssl-brand-info">Sectigo (原Comodo CA)是全球SSL证书市场占有率最高的CA公司，目前将近40%的SSL证书用户选择了Sectigo。由于其产品安全，价格低，受到大量站长的信任和欢迎。</a>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">证书对比</span>\
                                                <div class="info-r" style="min-height: 32px;line-height: 32px;">\
                                                    <table class="compared_ssl_list">\
                                                        <thead><tr><th>证书类型</th><th>免费证书</th><th>商用证书</th></tr></thead>\
                                                        <tbody>'+ html +'</tbody>\
                                                    </table>\
                                                </div>\
                                            </div>\
                                            <div class="alert alert-success" style="margin-left: 90px;margin-bottom:10px;">宝塔官网BT.CN也是用此品牌证书，性价比高，推荐使用</div>\
                                            <div class="line">\
                                                <span class="tname">证书类型</span>\
                                                <div class="info-r">\
                                                    <div class="divtable ssl_class_table" >\
                                                        <table class="table table-hover">\
                                                            <tbody>'+ list + '</tbody>\
                                                        </table>\
                                                    </div>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">总计费用</span>\
                                                <div class="info-r">\
                                                    <div class="guide_price"></div>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname"></span>\
                                                <div class="info-r">\
                                                    <button class="btn btn-success btn-sm next-plan" data-guide="1">下一步</button>\
                                                </div>\
                                            </div>\
                                        </div>\
                                        <div class="guide_content ssl_application_info" style="display:none" data-guide="2">\
                                            <div class="line">\
                                                <span class="tname">证书信息</span>\
                                                <div class="info-r ssl-info-line"></div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">域名</span>\
                                                <div class="info-r domain_list_info" style="margin-bottom:-5px;">\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">验证方式</span>\
                                                <div class="info-r ssl_verification">\
                                                    <label class="mr20"><input type="radio" name="dcvMethod" checked="checked" value="HTTP_CSR_HASH"\><span>文件验证(HTTP)</span></label>\
                                                    <label class="mr20"><input type="radio" name="dcvMethod" value="HTTPS_CSR_HASH"\><span>文件验证(HTTPS)</span></label>\
                                                    <label class="mr20"><input type="radio" name="dcvMethod" value="CNAME_CSR_HASH"\><span>DNS验证(CNAME解析)</span></label>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">所在地区</span>\
                                                <div class="info-r ">\
                                                    <input type="text" class="bt-input-text mr5" name="state" value="'+ (userInfo.state || '') +'"  placeholder="请输入所在省份，必填项" style="width:120px;"/>\
                                                    <input type="text" class="bt-input-text mr5" name="city"  value="'+ (userInfo.city || '') +'" placeholder="请输入所在市/县，必填项" style="width:120px;margin-left:15px" />\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">公司名称</span>\
                                                <div class="info-r ">\
                                                    <input type="text" class="bt-input-text mr5" name="organation" value="'+ (userInfo.organation || '') +'"  placeholder="请输入公司名称，如为个人申请请输入个人姓名，必填项"/>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">姓名</span>\
                                                <div class="info-r ">\
                                                    <input type="text" class="bt-input-text mr5" name="name"  value="'+ ((userInfo.lastName + userInfo.firstName) || '') +'" placeholder="请输入姓名，必填项"/>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">邮箱</span>\
                                                <div class="info-r ">\
                                                    <input type="text" class="bt-input-text mr5" name="email" value="'+ (userInfo.email || '') +'" placeholder="请输入邮箱地址，必填项"/>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">手机</span>\
                                                <div class="info-r ">\
                                                    <input type="text" class="bt-input-text mr5" name="mobile" value="'+ (userInfo.mobile || '') +'" placeholder="请输入手机号码，若为空，则使用当前绑定手机号"/>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname">总计费用</span>\
                                                <div class="info-r">\
                                                    <div class="guide_price"></div>\
                                                </div>\
                                            </div>\
                                            <div class="line">\
                                                <span class="tname"></span>\
                                                <div class="info-r">\
                                                    <button class="btn btn-default btn-sm prev-plan mr10" data-guide="2">上一步</button>\
                                                    <button class="btn btn-success btn-sm play-plan" data-guide="2">支付订单</button>\
                                                </div>\
                                            </div>\
                                        </div>\
                                        <div class="guide_content ssl_applay_info" style="display:none" data-guide="3">\
                                            <div class="payTitle">微信支付</div>\
                                            <div class="paymethod">\
                                                <div class="pay-wx" id="PayQcode"></div>\
                                            </div>\
                                            <div class="lib-price-box text-center">\
                                                <span class="lib-price-name f14"><b>总计</b></span>\
                                                <span class="price-txt"><b class="sale-price">148.00</b>元</span>\
                                            </div>\
                                            <div class="lib-price-detailed">\
                                                <div class="info"><span class="text-left">商品名称</span><span class="text-right"></span></div>\
                                                <div class="info"><span class="text-left">下单时间</span><span class="text-right"></span></div>\
                                            </div>\
                                            <div class="lib-prompt"><span>微信扫一扫支付</span></div>\
                                        </div>\
                                        <div class="guide_content ssl_order_check" style="display:none" data-guide="4">\
                                            <div class="lib-price-icon"><div class="order_paly_success">支付成功</div></div>\
                                            <div class="lib-price-detailed" style="margin-bottom:15px;">\
                                                <div class="info"><span class="text-left">证书类型</span><span class="text-right"></span></div>\
                                            </div>\
                                        </div>\
                                    </div>';
                                    loadY =  bt.open({
                                        type:1,
                                        title:'申请商用证书',
                                        area:'640px',
                                        content:cert_info,
                                        success:function(layers,index){
                                        	
                                            $(layers).css('top',($(window).height() - $(layers).height()) / 2 - 42);
                                            $('.ssl_class_table tbody tr').click(function(){
                                                var index = $(this).data('index');
                                                activeData = res.data[index];
                                                $(this).addClass('active').siblings().removeClass('active');
                                                $(this).find('input').prop('checked','checked');
                                                $('.guide_price').html('<span>'+ activeData.price.toFixed(2) + '</span><span>元/1年</span><span style="color: #bbbbbb;text-decoration: line-through;margin-left: 15px;" class="mr5">原价:'+ activeData.src_price.toFixed(2) +'元/年</span>');
                                            }).eq(0).click();
                                            $('.next-plan').click(function(){
                                                var guide = parseInt($(this).data('guide')),code = activeData.code,placeholder = '';
                                                $(layers).css('top',($(window).height() - $(layers).height()) / 2 - 42);
                                                $('[data-guide='+ (guide + 1) +'].guide_content').show().siblings('.guide_content').hide();
                                                $('.guide_path span:eq('+ guide +')').addClass('active');
                                                $('.guide_path_progress span:eq(0)').width(135);
                                                if(guide == 1) $('.ssl-info-line').html('<span>'+ activeData.title +'</span>');
                                                if(code.indexOf('multi') > -1){
                                                    if(code.indexOf('wildcard') > -1){
                                                        placeholder = '多域名通配符证书，每行一个域名，最高支持2个域名，必填项,例如：\r*.bt.cn\r*.bttest.cn';
                                                    }else{
                                                        placeholder = '多域名证书，每行一个域名，最高支持3个域名，必填项,例如：\rwww.bt.cn\rwww.bttest.cn';
                                                    }
                                                    $('.domain_list_info').html('<textarea class="bt-input-text mr20 key" name="domains" placeholder="'+ placeholder +'" style="line-height:20px;width:400px;height:80px;padding:8px;"></textarea>');
                                                }else {
                                                    if(code.indexOf('wildcard') > -1){
                                                        placeholder = '请输入需要申请证书的域名（单域名通配符证书），必填项，例如：*.bt.cn';
                                                    }else{
                                                        placeholder = '请输入需要申请证书的域名（单域名证书），必填项，例如：www.bt.cn';
                                                    }
                                                    $('.domain_list_info').html('<input type="text" disabled="true" readonly="readonly" id="apply_site_name" class="bt-input-text mr5" name="domains" placeholder="' + placeholder + '"/><button class="btn btn-success btn-xs" onclick="site.select_site_list(\'apply_site_name\',\'' + code +'\')" style="">选择已有域名</button><button class="btn btn-success btn-xs" onclick="site.select_site_txt(\'apply_site_name\')" style="margin: 5px;">自定义域名</button>');
                                                }
                                            });
                                            $('.prev-plan').click(function(){
                                                $(layers).css('top',($(window).height() - $(layers).height()) / 2  - 42);
                                                var guide = parseInt($(this).data('guide'));
                                                $('[data-guide='+ (guide - 1) +'].guide_content').show().siblings('.guide_content').hide();
                                                $('.guide_path span:eq('+ (guide - 1) +')').removeClass('active')
                                                $('.guide_path_progress span:eq(0)').width(0);
                                                
                                            });
                                            $('.ssl_application_info').on('focus','input[type=text],textarea',function(){
                                                var placeholder = $(this).attr('placeholder');
                                                $('html').append($('<span id="width_test">'+ placeholder +'</span>'));
                                                $(this).attr('data-placeholder',placeholder);
                                                layer.tips(placeholder,$(this),{tips:[1,'#20a53a'],time:0,area:($('#width_test').width() + 20) +'px'});
                                                $(this).attr('placeholder','');
                                                $('#width_test').remove();
                                            }).on('blur','input[type=text],textarea',function(){
                                                var name = $(this).attr('name'),val = $(this).val();
                                                layer.closeAll('tips');
                                                $(this).attr('placeholder',$(this).attr('data-placeholder'));
                                                check_ssl_user_info($(this),name,val);
                                            })
                                            $('.play-plan').click(function(){
                                                $(layers).css('top',($(window).height() - $(layers).height()) / 2  - 42);
                                                var form = {},data = {};
                                                is_check = true;
                                                is_pay_view = true;
                                                $('.ssl_application_info').find('input,textarea').each(function(){
                                                    var name =  $(this).attr('name'),value = $(this).val(),
                                                    value = check_ssl_user_info($(this),name,value);
                                                    if(typeof value === "boolean"){
                                                        form = false;
                                                        return false;
                                                    }
                                                    form[name] = value;
                                                });
                                                if(typeof form == "boolean") return false;
                                                data = {
                                                    pid:activeData.pid,
                                                    years:1,
                                                    dcvMethod:$('[name="dcvMethod"]:checked').val(),
                                                    domains:form['domains'],
                                                    Administrator:{
                                                        job: userInfo.job || '总务',
                                                        state: form['state'],
                                                        city: form['city'],
                                                        address: form['state']+ form['city'],
                                                        email:form['email'],
                                                        mobile:form['mobile'],
                                                        country:userInfo.country || 'CN',
                                                        lastName:form['name'],
                                                        organation:form['organation'],
                                                        postCode:userInfo.postCode || '523000'
                                                    }
                                                }
                                                /**
                                                 * @description 支付订单轮询，检测支付状态
                                                 * @param {Number} oid 订单ID
                                                 * @return void 
                                                 */
                                                function pay_order_check(oid,product_info){
                                                    if(!is_check) return false;
                                                    bt.send('get_pay_status','ssl/get_pay_status',{oid:oid},function(rdata){
                                                        if(rdata === 0){
                                                            setTimeout(function(){
                                                                pay_order_check(oid,activeData);
                                                            },1500)
                                                        }else{
                                                            var loadT = bt.load('正在申请证书，请稍候...');
                                                            bt.send('apply_order','ssl/apply_order',{oid:oid},function(res){
                                                                loadT.close();
                                                                $('.guide_path_progress span:eq(0)').width(290);
                                                                $('.ssl_order_check').show().siblings('.guide_content').hide();
                                                                $('.guide_path span:eq(3)').addClass('active');
                                                                $('.ssl_order_check .lib-price-detailed .text-right:eq(0)').text(activeData.title);
                                                                if(res.status){
                                                                    verify_order_veiw(oid,function(data){
                                                                        $('.ssl_order_check').append(reader_domains_cname_check(data));
                                                                        $('.verify_ssl_domain').click(function(){
                                                                        	loadY.close();
                                                                            verify_order_veiw(oid);
                                                                        });
                                                                        $('.return_ssl_list').click(function(){
                                                                            loadY.close();
                                                                            $('#ssl_tabs span:eq(2)').click();
                                                                        });
                                                                    });
                                                                }
                                                            });
                                                        }
                                                        var clipboard = new ClipboardJS('.parsing_info .parsing_icon');
                                                        clipboard.on('success', function(e) {
                                                            bt.msg({status:true,msg:'复制成功'});
                                                            e.clearSelection();
                                                        });
                                                        clipboard.on('error', function(e) {
                                                            bt.msg({status:true,msg:'复制失败，请手动ctrl+c复制！'});
                                                            console.error('Action:', e.action);
                                                            console.error('Trigger:', e.trigger);
                                                        });
                                                    });
                                                }
                                                var loads = bt.load('正在创建支付订单，请稍候...');
                                                bt.send('apply_order_pay','ssl/apply_order_pay',{pdata:JSON.stringify(data)},function(rdata){
                                                    loads.close();
                                                    if(rdata.status === false){
                                                        bt.msg(rdata);
                                                        return false;
                                                    }
                                                    $('.guide_path_progress span:eq(0)').width(290);
                                                    $('.ssl_applay_info').show().siblings('.guide_content').hide();
                                                    $('.sale-price').text(activeData.price.toFixed(2));
                                                    $('.lib-price-detailed .info:eq(0) span:eq(1)').text(activeData.title);
                                                    $('.lib-price-detailed .info:eq(1) span:eq(1)').text(bt.format_data(new Date().getTime()));
                                                    $('.guide_path span:eq(2)').addClass('active');
                                                    $('#PayQcode').qrcode({
                                                        render: "canvas",
                                                        width: 320,
                                                        height: 320,
                                                        text:rdata.msg.wxcode
                                                    });
                                                    pay_order_check(rdata.msg.oid,activeData);
                                                });
                                            });
                                            $('.business_ssl_application ').on('click','.lib-price-button button',function(){
                                                switch($(this).index()){
                                                    case 0:
                                                        loadY.close();
                                                        verify_order_veiw(rdata.msg.oid);
                                                    break;
                                                    case 1:
                                                        loadY.close();
                                                    break;
                                                }
                                            });
                                        },
                                        cancel:function(indexs, layero){
                                        	if(is_pay_view){
                                        		bt.confirm({msg:'当前处于支付状态，支付时请勿强制关闭弹窗，是否关闭弹窗?',title:'提示'},function(index){
                                        			layer.close(index);
                                        			layer.close(indexs);
                                        		});
                                        		return false;
                                        	}
                                        },
                                        end:function(){
                                        	is_pay_view = false;
                                            is_check = false
                                        }
                                    });
                                });
                            });
                            return false;
                        }
                    },
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
                                                        if(tdata.msg.indexOf('<br>') != -1){
                                                            layer.msg(tdata.msg,{time:0,shade:0.3,shadeClose:true,area:'550px',icon:2});
                                                        }else{
                                                            bt.msg(tdata);
                                                        }
                                                        
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
                            acme.get_account_info(function(let_user){
                                if(let_user.status === false){
                                    layer.msg(let_user.msg,{icon:2,time:10000});
                                }
                            });
                            acme.id = web.id;
                            if (rdata.status && rdata.type == 1) {
                                var cert_info = '';
                                if (rdata.cert_data['notBefore']) {
                                    cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;"><b>已部署成功：</b>将在距离到期时间1个月内尝试自动续签</span>\
                                        <span style="margin-left: 15px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 140px;width: 140px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer+'</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 15px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
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
                                                    site.ssl.renew_ssl(web.name,rdata.auth_type,rdata.index);
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
                                robj.append(bt.render_help(['已为您自动生成Let\'s Encrypt免费证书；', '如需使用其他SSL,请切换其他证书后粘贴您的KEY以及PEM内容，然后保存即可。','如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口']));
                                return;
                            }
                            bt.site.get_site_domains(web.id, function (ddata) {
                                var helps = [[
                                    '<span style="color:red;">Let\'s Encrypt因更换根证书，部分老旧设备访问时可能提示不可信，考虑购买<a class="btlink" onclick="$(\'#ssl_tabs span\').eq(0).click();">[商用SSL证书]</a></span>',
                                    '申请之前，请确保域名已解析，如未解析会导致审核失败',
                                    'Let\'s Encrypt免费证书，有效期3个月，支持多域名。默认会自动续签',
                                    '若您的站点使用了CDN或301重定向会导致续签失败',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                    '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
                                ], [
                                    '在DNS验证中，我们提供了多种自动化DNS-API，并提供了手动模式',
                                    '使用DNS接口申请证书可自动续期，手动模式下证书到期后需重新申请',
                                    '使用【DnsPod/阿里云DNS】等接口前您需要先在弹出的窗口中设置对应接口的API',
                                    '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
                                ]]
                                var datas = [
                                    {
                                        title: '验证方式', items: [
                                            {
                                                name: 'check_file', text: '文件验证', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove()
                                                    $(obj).siblings().removeAttr('checked');

                                                    $('.help-info-text').html($(bt.render_help(helps[0])));
                                                    //var _form_data = bt.render_form_line({ title: ' ', class: 'checks_line label-input-group', items: [{ name: 'force', type: 'checkbox', value: true, text: '提前校验域名(提前发现问题,减少失败率)' }] });
                                                    //$(obj).parents('.line').append(_form_data.html);

                                                    $('#ymlist li input[type="checkbox"]').each(function () {
                                                        if ($(this).val().indexOf('*') >= 0) {
                                                            $(this).parents('li').hide();
                                                        }
                                                    })
                                                }
                                            },
                                            {
                                                name: 'check_dns', text: 'DNS验证(支持通配符)', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove();
                                                    $(obj).siblings().removeAttr('checked');
                                                    $('.help-info-text').html($(bt.render_help(helps[1])));
                                                    $('#ymlist li').show();

                                                    var arrs_list = [], arr_obj = {};
                                                    bt.site.get_dns_api(function (api) {
                                                        site.dnsapi = {}
                                                        
                                                        for (var x = 0; x < api.length; x++) {
                                                            site.dnsapi[api[x].name] = {}
                                                            site.dnsapi[api[x].name].s_key = "None"
                                                            site.dnsapi[api[x].name].s_token = "None"
                                                            if(api[x].data){
                                                                site.dnsapi[api[x].name].s_key = api[x].data[0].value
                                                                site.dnsapi[api[x].name].s_token = api[x].data[1].value
                                                            }
                                                            arrs_list.push({ title:  api[x].title, value: api[x].name});
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
                                    }
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

                                        var auth_type = 'http'
                                        var auth_to = web.id
                                        var auto_wildcard = '0'
                                        if(ldata.check_dns){
                                            auth_type = 'dns'
                                            auth_to = 'dns'
                                            auto_wildcard = ldata.app_root?'1':'0'
                                            if(ldata.dns_select !== auth_to){
                                                if(!site.dnsapi[ldata.dns_select].s_key){
                                                    layer.msg("指定dns接口没有设置密钥信息");
                                                    return;
                                                }
                                                auth_to = ldata.dns_select + "|" + site.dnsapi[ldata.dns_select].s_key + "|" + site.dnsapi[ldata.dns_select].s_token;
                                            }
                                        }
                                        acme.apply_cert(ldata['domains'],auth_type,auth_to,auto_wildcard,function(res){
                                            site.ssl.ssl_result(res,auth_type,web.name);
                                        })
                                        
                                    }
                                });
                                robj.append(_btn_data.html);
                                bt.render_clicks(_btn_data.clicks);

                                robj.append(bt.render_help(helps[0]));
                                robj.find('input[type="radio"]:eq(0)').trigger('click');
                            })
                        }
                    },
                    {
                        title: "其他证书", callback: function (robj){
                            var cert_info = '';
                            if (rdata.cert_data['notBefore']){
                                cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;">'+ (rdata.status ? '<b>已部署成功：</b>请在证书到期之前更换新的证书' :'<b style="color:red;">当前未部署：</b>请点击【保存】按钮完成此证书的部署')+'</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 138px;width: 140px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
                            }
                            robj.append('<div>' + cert_info+'<div><span style="width: 45%;display: inline-block;margin-right: 20px;">密钥(KEY)</span><span  style="width: 45%;display: inline-block;margin-right: 20px;">证书(PEM格式)</span></div></div>');
                            var datas = [
                                {
                                    items: [
                                        { name: 'key', width: '45%', height: '260px', type: 'textarea', value: rdata.key },
                                        { name: 'csr', width: '45%', height: '260px', type: 'textarea', value: rdata.csr }
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
                                '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
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
                                case 3:
                                    txt = 'Comodo Positive';
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
                switch(rdata.type) {
                     case 0:
                        $('#ssl_tabs span:eq(3)').trigger('click');
                        break;
                    case 1:
                        $('#ssl_tabs span:eq(1)').trigger('click');
                        break;
                    case 3:
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
                                        if (ret.status){
                                            var versions = $('[name="versions"]').val();
                                            console.log(versions)
                                            versions = versions.slice(0, versions.length - 1) + '.' + versions.slice(-1);
                                            if(versions == '0.0') versions = '静态';
                                            site_table.$refresh_table_list(true);
                                            site.reload()
                                        }
                                        setTimeout(function(){
                                            bt.msg(ret);
                                        },2000);
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
                    	var loading = bt.load('正在获取session状态请稍候');
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
	                    }, 500);
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
        		area: '440px',
        		title: type ? '添加加密访问' : '修改加密访问',
        		closeBtn:  2,
        		shift: 5,
        		shadeClose: false,
        		content: "<form id='form_dir' class='divtable pd15' style='padding-bottom: 60px;'>" +
        			"<div class='line'>" +
                    "<span class='tname'>名称</span>" +
                    "<div class='info-r ml0'><input name='dir_name' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.name + "'>" +
                    "</div></div>" +
        			"<div class='line'>" +
                    "<span class='tname'>加密访问</span>" +
                    "<div class='info-r ml0'><input name='dir_sitedir' placeholder='输入需要加密访问的目录，如：/text/' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.sitedir + "'>" +
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
                        "<li>目录设置加密访问后，访问时需要输入账号密码才能访问</li>"+
                        "<li>例如我设置了加密访问 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>"+
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
        template_php: function(website,obj) {
            var _type = 'add', _name = '', _bggrey = '';
            if (obj == undefined) {
                obj = { "name": "", "suffix": "php|jsp", "dir": "" };
            } else {
                obj = { "name": obj.name, "suffix": obj.suffix, "dir": obj.dir };
                _type = 'edit';
                _name = ' readonly';
                _bggrey = 'background: #eee;'
            }
            var form_directory = bt.open({
                type: 1,
                area: '440px',
                title: '添加禁止访问',
                closeBtn: 2,
                btn: ['保存','取消'],
                content: "<form class='mt10 php_deny'>" +
                    "<div class='line'>" +
                    "<span class='tname' style='width: 100px;'>名称</span>" +
                    "<div class='info-r ml0' style='margin-left: 100px;'><input name='deny_name' placeholder='规则名称' "+_name+" class='bt-input-text mr10' type='text' style='width:270px;" + _bggrey + "' value='" + obj.name + "'>" +
                    "</div></div>" +
                    "<div class='line'>" +
                    "<span class='tname' style='width: 100px;'>后缀</span>" +
                    "<div class='info-r ml0' style='margin-left: 100px;'><input name='suffix' placeholder='禁止访问的后缀' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.suffix + "'>" +
                    "</div></div>" +
                    "<div class='line'>" +
                    "<span class='tname' style='width: 100px;'>目录</span>" +
                    "<div class='info-r ml0' style='margin-left: 100px;'><input name='dir' placeholder='禁止访问的目录' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.dir + "'>" +
                    "</div></div></form>" +
                    "<ul class='help-info-text c7' style='padding-left:40px;margin-bottom: 20px;'>"+
                        "<li>后缀：禁止访问的文件后缀</li>"+
                        "<li>目录：规则会在这个目录内生效</li>"+
                    "</ul>",
                yes: function () {
                    var dent_data = $('.php_deny').serializeObject();
                    dent_data.act = _type;
                    dent_data.website = website;
                    var loading = bt.load();
                    bt.send('set_php_deny', 'config/set_file_deny', dent_data, function(rdata) {
                        loading.close();
                        if (rdata.status) {
                            form_directory.close();
                            site.reload();
                            $("#set_dirguard .tab-nav span:eq(1)").click();
                        }
                        bt.msg(rdata);
                    });
                }
            });
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
        set_301: function (web){
            $('#webedit-con').html('<div id="redirect_list"></div>');
            bt_tools.table({
                el:'#redirect_list',
                url:'/site?action=GetRedirectList',
                param:{sitename:web.name},
                dataFilter:function(res){
                    return {data:res};
                },
                column:[
                    {type:'checkbox',width:20},
                    {fid:'sitename',title:'重定向类型',type:'text',template:function(row){
                        if (row.domainorpath == 'path') {
                            conter = row.redirectpath;
                        } else {
                            conter = row.redirectdomain ? row.redirectdomain.join('、') : '空'
                        }
                        return '<span style="width:100px;" title="' + conter + '">' + conter + '</span>';
                    }},
                    {fid:'redirecttype',title:'重定向方式',type:'text'},
                    {fid:'holdpath',title:'保留URL参数',config:{icon:false,list:[[1,'开启','bt_success'],[0,'关闭','bt_danger']]},type:'status',
                        event:function(row,index,ev,key,that){
                            row.holdpath = !row.holdpath?1:0;
                            row.redirectdomain = JSON.stringify(row['redirectdomain']);
                            bt.site.modify_redirect(row,function (res){
                                row.redirectdomain = JSON.parse(row['redirectdomain']);
                                that.$modify_row_data({holdpath:row.holdpath});
                                bt.msg(res);
                            });
                        }
                    },
                    {fid:'type',title:'状态',config:{icon:true,list:[[1,'运行中','bt_success','glyphicon-play'],[0,'已停止','bt_danger','glyphicon-pause']]},type:'status',
                        event:function(row,index,ev,key,that){
                            row.type = !row.type?1:0;
                            row.redirectdomain = JSON.stringify(row['redirectdomain']);
                            bt.site.modify_redirect(row,function (res){
                                row.redirectdomain = JSON.parse(row['redirectdomain']);
                                that.$modify_row_data({holdpath:row.type});
                                bt.msg(res);
                            });
                        }
                    },{title:'操作',width:150,type:'group',align:'right',group:[{
                        title:'配置文件',
                        event:function(row,index,ev,key,that){
                            bt.site.get_redirect_config({
                                sitename: web.name,
                                redirectname: row.redirectname,
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
                                    title: '编辑配置文件[' + row.redirectname + ']',
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
                        }
                    },{
                        title:'编辑',
                        event:function(row,index,ev,key,that){
                            site.edit.templet_301(web.name,web.id,false,row);
                        }
                    },{
                        title:'删除',
                        event:function(row,index,ev,key,that){
                            bt.site.remove_redirect(web.name,row.redirectname,function(rdata){
                                if(rdata.status) that.$delete_table_row(index);
                            });
                        }
                    }]
                }],
                tootls:[{ //按钮组
                    type:'group',
                    positon:['left','top'],
                    list:[{title:'添加重定向',active:true, event:function(ev){ 
                        site.edit.templet_301(web.name,web.id,true);
                    }}]
                },{ //批量操作
                    type:'batch',
                    positon:['left','bottom'],
                    config:{
                        title:'删除',
                        url:'/site?action=del_redirect_multiple',
                        param:{site_id:web.id},
                        paramId:'redirectname',
                        paramName:'redirectnames',
                        theadName:'重定向名称',
                        confirmVerify:false // 是否提示验证方式
                    }
                }]
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
                val = val.replace(/^http[s]?:\/\//,'');
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
            $('#webedit-con').html('<div id="proxy_list"></div>');
            String.prototype.myReplace = function (f, e) {//吧f替换成e
                var reg = new RegExp(f, "g"); //创建正则RegExp对象   
                return this.replace(reg, e);
            }
            bt_tools.table({
                el:'#proxy_list',
                url:'/site?action=GetProxyList',
                param:{sitename:web.name},
                dataFilter:function(res){
                    return {data:res};
                },
                column:[
                    {type:'checkbox',width:20},
                    {fid:'proxyname',title:'名称',type:'text'},
                    {fid:'proxydir',title:'代理目录',type:'text'},
                    {fid:'proxysite',title:'目标url',type:'link',href:true},
                    bt.get_cookie('serverType') == 'nginx' ? {fid:'cache',title:'缓存',config:{icon:false,list:[[1,'已开启','bt_success'],[0,'已关闭','bt_danger']]},type:'status',event:function(row,index,ev,key,that) {
                        row['cache'] = !row['cache']?1:0;
                        row['subfilter'] = JSON.stringify(row['subfilter']);
                        bt.site.modify_proxy(row, function (rdata) {
                            row['subfilter'] = JSON.parse(row['subfilter']);
                            if (rdata.status) that.$modify_row_data({cache:row['cache']});
                            bt.msg(rdata);
                        });
                    }}:{},
                    {fid:'type',title:'状态',config:{icon:true,list:[[1,'运行中','bt_success','glyphicon-play'],[0,'已暂停','bt_danger','glyphicon-pause']]},type:'status',event:function(row,index,ev,key,that){
                        row['type'] = !row['type']?1:0;
                        row['subfilter'] = JSON.stringify(row['subfilter']);
                        bt.site.modify_proxy(row, function (rdata) {
                            row['subfilter'] = JSON.parse(row['subfilter']);
                            if (rdata.status) that.$modify_row_data({type:row['type']});
                            bt.msg(rdata);
                        });
                    }},
                    {title:'操作',width:150,type:'group',align:'right',group:[{
                        title:'配置文件',
                        event:function(row,index,ev,key,that){
                            bt.site.get_proxy_config({
                                sitename: web.name,
                                proxyname: row.proxyname,
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
                                    title: '编辑配置文件[' + row.proxyname + ']',
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
                        }
                    },{
                        title:'编辑',
                        event:function(row,index,ev,key,that){
                            site.edit.templet_proxy(web.name,false,row);
                        }
                    },{
                        title:'删除',
                        event:function(row,index,ev,key,that){
                            bt.site.remove_proxy(web.name,row.proxyname,function(rdata){
                                if(rdata.status) that.$delete_table_row(index);
                            })
                        }
                    }]
                }],
                tootls:[{ //按钮组
                    type:'group',
                    positon:['left','top'],
                    list:[{title:'添加反向代理',active:true, event:function(ev){ 
                        site.edit.templet_proxy(web.name, true)
                    }}]
                },{ //批量操作
                    type:'batch',
                    positon:['left','bottom'],
                    config:{
                        title:'删除',
                        url:'/site?action=del_proxy_multiple',
                        param:{site_id:web.id},
                        paramId:'proxyname',
                        paramName:'proxynames',
                        theadName:'反向代理名称',
                        confirmVerify:false // 是否提示验证方式
                    }
                }]
            });
        },
        set_security: function (web) {
            bt.site.get_site_security(web.id, web.name, function (rdata) {
                var robj = $('#webedit-con');
                var datas = [
                    { title: 'URL后缀', name: 'sec_fix', value: rdata.fix, disabled: rdata.status, width: '300px' },
                    { title: '许可域名', type:"textarea", name: 'sec_domains', value: rdata.domains.replace(/,/g,"\n"), disabled: rdata.status, width: '300px',height:'210px' },
                    { title: '响应资源', name: 'return_rule', value: rdata.return_rule, disabled: rdata.status, width: '300px' },
                    {
                        title: ' ', class: 'label-input-group', items: [
                            {
                                text: '启用防盗链', name: 'status', value: rdata.status, type: 'checkbox', callback: function (sdata) {
                                    bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split("\n").join(','), sdata.status,sdata.return_rule, function (ret) {
                                        if (ret.status) site.reload(13)
                                        bt.msg(ret);
                                    })
                                }
                            },
                            {
                                text: '允许空HTTP_REFERER请求', name: 'none', value: rdata.none, type: 'checkbox', callback: function (sdata) {
                                    bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split("\n").join(','), '1',sdata.return_rule, function (ret) {
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
                var helps = [
                    '【URL后缀】一般填写文件后缀，每行一个后缀,如: png', 
                    '【许可域名】允许作为来路的域名，每行一个域名,如: www.bt.cn',
                    '【响应资源】可设置404/403等状态码，也可以设置一个有效资源，如：/security.png',
                    '【允许空HTTP_REFERER请求】是否允许浏览器直接访问，若您的网站访问异常，可尝试开启此功能'
                ]
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
                var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '600px', value: rdata.msg, width: '100%', type: 'textarea' }] };
                var _form_data = bt.render_form_line(logs);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
                $('textarea[name="site_logs"]').attr('readonly', true);
                $('textarea[name="site_logs"]').scrollTop(100000000000)

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
    select_site_txt: function (box) {
        layer.open({
            type: 1,
            closeBtn: 2,
            title: '自定义域名',
            area: '600px',
            btn: ['确认', '取消'],
            content: '<div class="pd20"><div class="line "><span class="tname">自定义域名</span><div class="info-r "><input  name="site_name" placeholder="请输入需要申请证书的域名（单域名证书），必填项，例如：www.bt.cn" class="bt-input-text mr5 ssl_site_name_rc" type="text" style="width:400px" value=""></div></div>\
            <ul class="help-info-text c7">\
                    <li> 申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                    <li>申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</li>\
                    <li>SSL证书可选名称赠送规则：</li>\
                    <li>    1、申请根域名(如：bt.cn),赠送下一级为www的域名(如：www.bt.cn)</li>\
                    <li>    2、申请当前host为www的域名（如：www.bt.cn）,赠送上一级域名，(如: bt.cn)</li>\
                    <li>    3、申请其它二级域名，(如：app.bt.cn)，赠送下一级为www的域名 (如：www.app.bt.cn)</li>\
                </ul >\
            </div>',
            success: function () {
          
            }, 
            yes: function (layers, index) {               
                layer.close(layers);
                $('#' + box).val($('.ssl_site_name_rc').val())   
            }
        })
    },
    /**
    * @descripttion: 选择站点
    * @author: Lifu
    * @Date: 2020-08-14
    * @param {String} box 输出时所用ID
    * @return: 无返回值
    */
     select_site_list: function (box,code) {
        var _optArray = [], all_site_list = [];
   
        $.post('/data?action=getData', { tojs: 'site.get_list', table: 'domain', limit: 10000, search: '', p: 1, order: 'id desc', type: -1 }, function (res) {

            var _tbody = '';
            if (res.data.length > 0)
            {
                $.each(res.data, function (index, item) {                    
                    _body = '<tr>'
                        + '<td>'
                        + '<div class="box-group" style="height:16px">'
                        + '<div class="bt_checkbox_groups"></div>'
                        + '</div>'
                        + '</td>'
                        + '<td><span class="overflow_style" style="width:210px">' + item['name'] + '</span></td>'
                 
                        + '</tr>'

                    if (code.indexOf('wildcard') > -1) {
                        if (item['name'].indexOf('*.') > -1) {
                            all_site_list.push(item['name'])
                            _tbody += _body;
                        }
                    }
                    else {
                        all_site_list.push(item['name'])
                        _tbody += _body;
                    }                   
                })
                if (all_site_list.length == 0) {
                    _tbody = '<tr><td colspan="2">暂无数据</td></tr>'
                }
            } else {
                _tbody = '<tr><td colspan="2">暂无数据</td></tr>'
            }
                       
            layer.open({
                type: 1,
                closeBtn: 2,
                title: '选择站点',
                area: '600px',
                btn: ['确认', '取消'],
                content: '<div class="pd20 dynamic_head_box"><div class="line"><input type="text" name="serach_site" class="bt-input-text" style="width: 560px;" placeholder="支持字段模糊搜索"></div>\
                <div class="bt-table dynamic_list_table">\
                    <div class="divtable" style="height:281px">\
                        <table class="table table-hover">\
                            <thead>\
                                <th width="30">\
                                    <div class="box-group" style="height:16px">\
                                        <div class="bt_checkbox_groups" data-key="0"></div>\
                                    </div>\
                                </th>\
                                <th>域名</th>\
                            </thead>\
                            <tbody class="dynamic_list">'+ _tbody +'</tbody>\
                        </table>\
                    </div>\
                </div>\
                <ul class="help-info-text c7">\
                    <li> 申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                    <li>申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</li>\
                    <li>SSL证书可选名称赠送规则：</li>\
                    <li>    1、申请根域名(如：bt.cn),赠送下一级为www的域名(如：www.bt.cn)</li>\
                    <li>    2、申请当前host为www的域名（如：www.bt.cn）,赠送上一级域名，(如: bt.cn)</li>\
                    <li>    3、申请其它二级域名，(如：app.bt.cn)，赠送下一级为www的域名 (如：www.app.bt.cn)</li>\
                </ul >\
                </div> ',
                success: function () {
                        
                    // 固定表格头部
                    if (jQuery.prototype.fixedThead) {
                        $('.dynamic_list_table .divtable').fixedThead({ resize: false });
                    } else {
                        $('.dynamic_list_table .divtable').css({ 'overflow': 'auto' });
                    }
                    //检索输入
                    $('input[name=serach_site]').on('input', function () {
                        var _serach = $(this).val();
                        if (_serach.trim() != '') {
                            $('.dynamic_list tr').each(function () {
                                var _td = $(this).find('td').eq(1).html()
                                if (_td.indexOf(_serach) == -1) {
                                    $(this).hide()
                                } else {
                                    $(this).show()
                                }
                            })
                        } else {
                            $('.dynamic_list tr').show()
                        }
                    })
                  
                    // 单选设置
                    $('.dynamic_list').on('click', '.bt_checkbox_groups', function (e) {
                        var _tr = $(this).parents('tr');
                        if ($(this).hasClass('active')) {
                            $(this).removeClass('active');
                           
                        } else {
                            $('.dynamic_list .bt_checkbox_groups').removeClass('active');
                            $(this).addClass('active');
                            _optArray = [_tr.find('td').eq(1).text()]
                        }
                        e.preventDefault();
                        e.stopPropagation();
                    })
                    // tr点击时
                    $('.dynamic_list').on('click', 'tr', function (e) {
                        $(this).find('.bt_checkbox_groups').click()
                        e.preventDefault();
                        e.stopPropagation();
                    })
                },
                yes: function (layers, index) {
                    var _olist = []                    
                    if (_optArray.length > 0) {
                        $.each(_optArray, function (index, item) {
                            if ($.inArray(item, _olist) == -1) {
                                _olist.push(item)
                            }
                        })
                    }
                    layer.close(layers);
                    $('#' + box).val(_olist.join('\n'))
                    $('textarea[name=lb_site]').focus();
                }
            });        
        });
    },
    web_edit: function (obj) {
        var _this = this,item = obj;
        bt.open({
            type: 1,
            area: ['780px', '722px'],
            title: lan.site.website_change + '[' + item.name + ']  --  ' + lan.site.addtime + '[' + item.addtime + ']',
            closeBtn: 2,
            shift: 0,
            content: "<div class='bt-form'><div class='bt-w-menu site-menu pull-left' style='height: 100%;'></div><div id='webedit-con' class='bt-w-con webedit-con pd15'></div></div>"
        })
        setTimeout(function () {
            var webcache = bt.get_cookie('serverType') == 'openlitespeed' ? { title: 'LS-Cache', callback: site.edit.ols_cache } : '';
            var menus = [
                { title: '域名管理', callback: site.edit.set_domains },
                { title: '子目录绑定', callback: site.edit.set_dirbind },
                { title: '网站目录', callback: site.edit.set_dirpath },
                { title: '访问限制', callback: site.edit.set_dirguard },
                { title: '流量限制', callback: site.edit.limit_network },
                { title: '伪静态', callback: site.edit.get_rewrite_list },
                { title: '默认文档', callback: site.edit.set_default_index },
                { title: '配置文件', callback: site.edit.set_config },
                { title: 'SSL', callback: site.edit.set_ssl },
                { title: 'PHP版本', callback: site.edit.set_php_version },
                { title: 'Tomcat', callback: site.edit.set_tomact },
                // { title: '重定向', callback: site.edit.set_301_old },
                { title: '重定向', callback: site.edit.set_301 },
                { title: '反向代理', callback: site.edit.set_proxy },
                { title: '防盗链', callback: site.edit.set_security },
                { title: '响应日志', callback: site.edit.get_site_logs }
            ]
            if (webcache !== '') menus.splice(3, 0, webcache);
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



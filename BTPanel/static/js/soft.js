var soft = {
    is_install: false,
    get_list: function (page, type, search) {
        if (page == undefined || page == 'null' || page == 'undefined') page = 0;
        if (type == undefined || type == 'null' || type == 'undefined') type = 0;
        if (!search) search = $("#SearchValue").val();
        if (search == undefined || search == 'null' || search == 'undefined' || search == '') search = undefined;
        var _this = this;
        var istype = getCookie('softType');
        if (istype == 'undefined' || istype == 'null' || !istype) {
            istype = 0;
        }
        if (type == 0) type = bt.get_cookie('softType');
        if (page == 0) page = bt.get_cookie('p' + type);
        if (type == '11') {
            soft.get_dep_list(1);
            return;
        }
        soft.is_install = false;
        bt.soft.get_soft_list(page, type, search, function (rdata) {
            soft.set_soft_tips('#updata_pro_info',type);
            var tBody = '';
            rdata.type.unshift({ icon: 'icon', id: 0, ps: '全部', sort: 1, title: '全部' },{ icon: 'icon', id: -1, ps: '已安装', sort: 1, title: '已安装' })
            for (var i = 0; i < rdata.type.length; i++) {
                var c = '';
                if (istype == rdata.type[i].id) {
                    c = 'class="on"';
                }
                tBody += '<span typeid="' + rdata.type[i].id + '" ' + c + '>' + rdata.type[i].title + '</span>';
            }
            if (page) bt.set_cookie('p' + type, page);
            $(".softtype").html(tBody);
            $(".menu-sub span").click(function () {
                var _type = $(this).attr('typeid');
                bt.set_cookie('softType', _type);
                $(this).addClass("on").siblings().removeClass("on");
                if (_type !== '11') {
                    soft.get_list(0, _type);
                } else {
                    soft.get_dep_list(0);
                }
            })
            var data = rdata.list.data;
            $('#softPage').html(rdata.list.page);
            var phps = ['php-5.2', 'php-5.3', 'php-5.4'];
            var _tab = bt.render({
                table: '#softList',
                columns: [
                    {
                        field: 'title', title: '软件名称', width: 165, templet: function (item) {
                            var fName = item.name, version = item.version;
                            if (bt.contains(item.name, 'php-')) {
                                fName = 'php';
                                version = '';
                            }
                            var click_opt = ' ', sStyle = '';
                            if (item.setup) {
                                sStyle = ' style="cursor:pointer"';
                                if (item.admin) {
                                    if (item.endtime >= 0 || item.price == 0) {
                                        click_opt += 'onclick="bt.soft.set_lib_config(\'' + item.name + '\',\'' + item.title + '\')" ';
                                    }

                                }
                                else {
                                    click_opt += ' onclick="soft.set_soft_config(\'' + item.name + '\')" ';
                                }
                            }
                            var is_php = item.name.indexOf('php-') >= 0,
                            is_php5 = item.name.indexOf('php-5') >= 0,
                            webcache = bt.get_cookie('serverType') == 'openlitespeed' ? true : false,
                            distribution = bt.get_cookie('distribution');
                            if (webcache && is_php) {
                                if ((is_php5 || item.name == 'php-7.0')&&distribution=='centos8') {
                                    click_opt = ' title="Apache2.2不兼容此版本，如需使用请切换到Apache2.4或Nginx"';
                                }else if (distribution=='centos7'&&item.name == 'php-5.2') {
                                    click_opt = ' title="Apache2.2不兼容此版本，如需使用请切换到Apache2.4或Nginx"';
                                }else if (is_php5) {
                                    click_opt = ' title="Apache2.2不兼容此版本，如需使用请切换到Apache2.4或Nginx"';
                                }
                            }else if (rdata.apache22 && item.name.indexOf('php-') >= 0 && $.inArray(item.name, phps) == -1) {
                                click_opt = ' title="Apache2.2不兼容此版本，如需使用请切换到Apache2.4或Nginx"';
                            }
                            return '<span ' + click_opt + ' ' + sStyle + ' ><img '+ (item.type === 10?'style="height:20px;width:22px"':'') +' src="/static/img/soft_ico/ico-' + fName + '.png">' + item.title + ' ' + version + '</span>';
                        }
                    },
                    {
                        field: 'price', title: '开发商', width: 92, templet: function (item) {
                            if(!item.author) return '官方'
                            return item.author;
                        }
                    },
                    {
                        field: 'ps', title: '说明', templet: function (item) {
                            var ps = item.ps;
                            var is_php = item.name.indexOf('php-') >= 0;

                            if (is_php && item.setup) {
                                if (rdata.apache22 && $.inArray(item.name, phps) >= 0) {
                                    if (item.fpm) {
                                        ps += " <span style='color:red;'>(" + lan.soft.apache22 + ")</span>";
                                    }
                                }
                                else if (!rdata.apache22) {
                                    if (!item.fpm) {
                                        ps += " <span style='color:red;'>(" + lan.soft.apache24 + ")</span>";
                                    }
                                }
                            }
                            return '<span>' + ps + '</span>';
                        }
                    },
                    {
                        field: 'price', title: '价格', width: 72, templet: function (item) {
                            var price = '免费';
                            if (item.price > 0) {
                                price = '<span style="color:#fc6d26">￥' + item.price + '</span>';
                            }
                            return price;
                        }
                    },
                    (type ==10?{
                        field: 'sort', width: 60, title: '评分', templet: function (item) {
                            return item.sort !== undefined?('<a href="javascript:;" onclick="score.open_score_view('+ item.pid +',\''+ item.title +'\','+ item.count +')" class="btlink open_sort_view">' + (item.sort <= 0 || item.sort >5?'无评分':item.sort.toFixed(1))  +'</a>'):'--';
                        }
                    }:''),
                    {
                        field: 'endtime', width: 120, title: '到期时间', templet: function (item) {
                            var endtime = '--';
                            if (item.pid > 0) {  //判断是否为付费插件
                                if (item.endtime > 0) {
                                    if (item.type != 10) { //判断是否为第三方插件
                                        endtime = bt.format_data(item.endtime, 'yyyy/MM/dd') + '<a class="btlink" onclick=\'bt.soft.product_pay_view('+ JSON.stringify({name:item.title,pid:item.pid,type:item.type,plugin:true,renew:item.endtime}) +')\'> (续费)</a>';
                                    } else {
                                        endtime = bt.format_data(item.endtime, 'yyyy/MM/dd') + '<a class="btlink" onclick="bt.soft.re_plugin_pay_other(\'' + item.title + '\',\'' + item.pid + '\',1,'+item.price+')"> (续费)</a>';
                                    }
                                }
                                else if (item.endtime === 0) {
                                    endtime = '永久';
                                }
                                else if (item.endtime === -1) {
                                    endtime = '未开通';
                                }
                                else if (item.endtime === -2) {
                                    if (item.type != 10) {
                                        endtime = '已到期' + '<a class="btlink" onclick="bt.soft.product_pay_view('+ JSON.stringify({name:item.title,pid:item.pid,type:item.type,plugin:true,renew:item.endtime}) +')"> (续费)</a>';
                                    }else {
                                        endtime = '已到期' + '<a class="btlink" onclick="bt.soft.re_plugin_pay_other(\'' + item.title + '\',\'' + item.pid + '\',1,'+item.price+')"> (续费)</a>';
                                    }
                                }
                            }
                            return endtime;
                        }
                    },
                    {
                        field: 'path', width: 40, title: '位置', templet: function (item) {
                            var path = '';
                            if (item.setup) {
                                path = '<span class="glyphicon glyphicon-folder-open"  onclick="openPath(\'' + item.uninsatll_checks + '\')"></span>';
                            }
                            return path;
                        }
                    },
                    (type !=10?{
                        field: 'status', width: 40, title: '状态', templet: function (item) {
                            var status = '';
                            if (item.setup) {
                                if(item.name == 'phpmyadmin') item.status = 1;
                                if (item.status) {
                                    status = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>';
                                }
                                else {
                                    status = '<span style="color:red" class="glyphicon glyphicon-pause"></span>';
                                }
                            }
                            return status;
                        }
                    }:''),
                    {
                        field: 'index', width: 64, title: '首页显示', templet: function (item) {
                            var to_index = '';
                            if (item.setup) {
                                var checked = '';
                                if (item.index_display) checked = 'checked';
                                var item_id = item.name.replace(/\./, "");
                                to_index = '<div class="index-item"><input class="btswitch btswitch-ios" id="index_' + item_id + '" type="checkbox" ' + checked + '><label class="btswitch-btn" for="index_' + item_id + '" onclick="bt.soft.to_index(\'' + item.name + '\')"></label></div>';
                            }
                            return to_index;
                        }
                    },
                    {
                        field: 'opt', width: 120, title: '操作', align: 'right', templet: function (item) {
                            var option = '';

                            var pay_opt = '';
                            if (item.endtime < 0 && item.pid > 0) {
                                var re_msg = '';
                                var re_status = 0;
                                switch (item.endtime) {
                                    case -1:
                                        re_msg = '立即购买';
                                        break;
                                    case -2:
                                        re_msg = '立即续费';
                                        re_status = 1;
                                        break;
                                }
                                if (item.type != 10) {
                                    pay_opt = '<a class="btlink" onclick=\'bt.soft.product_pay_view('+ JSON.stringify({name:item.title,pid:item.pid,type:item.type,plugin:true,renew:item.endtime}) +')\'>' + re_msg + '</a>';
                                } else {
                                    pay_opt = '<a class="btlink" onclick="bt.soft.re_plugin_pay_other(\'' + item.title + '\',\'' + item.pid + '\',' + re_status + ','+item.price+')">' + re_msg + '</a>';
                                }
                                
                            }
                            var is_php = item.name.indexOf('php-') >= 0,
                            is_php5 = item.name.indexOf('php-5') >= 0,
                            webcache = bt.get_cookie('serverType') == 'openlitespeed' ? true : false,
                            distribution = bt.get_cookie('distribution');
                            if (webcache && is_php) {
                                if ((is_php5 || item.name == 'php-7.0')&&distribution=='centos8') {
                                    option = '<span title="Apache2.4不兼容此版本，如需使用请切换到Apache2.2或Nginx">不兼容</span>';
                                }else if (distribution=='centos7'&&item.name == 'php-5.2') {
                                    option = '<span title="Apache2.4不兼容此版本，如需使用请切换到Apache2.2或Nginx">不兼容</span>';
                                }else{
                                    if (is_php5) {
                                        option = '<span title="Apache2.4不兼容此版本，如需使用请切换到Apache2.2或Nginx">不兼容</span>';
                                    }else {
                                        if (item.setup && item.task == '1') {
                                            if (pay_opt == '') {
                                                if (item.versions.length > 1) {
                                                    for (var i = 0; i < item.versions.length; i++) {
                                                        var min_version = item.versions[i]
                                                        var ret = bt.check_version(item.version, min_version.m_version + '.' + min_version.version);
                                                        if (ret > 0) {
                                                            if (ret == 2) option += '<a class="btlink" onclick="bt.soft.update_soft(\'' + item.name + '\',\'' + item.title + '\',\'' + min_version.m_version + '\',\'' + min_version.version + '\',\'' + min_version.update_msg.replace(/\n/g,"_bt_") + '\',\''+ item.type +'\')" >更新</a> | ';
                                                            break;
                                                        }
                                                    }
                                                }
                                                else {
                                                    var min_version = item.versions[0];
                                                    var cloud_version = min_version.m_version + '.' + min_version.version;
                                                    if (item.version != cloud_version) option += '<a class="btlink" onclick="bt.soft.update_soft(\'' + item.name + '\',\'' + item.title + '\',\'' + min_version.m_version + '\',\'' + min_version.version + '\',\'' + min_version.update_msg.replace(/\n/g, "_bt_") + '\',\''+ item.type +'\')" >更新</a> | ';
                                                }
                                                if (item.admin) {
                                                    option += '<a class="btlink" onclick="bt.soft.set_lib_config(\'' + item.name + '\',\'' + item.title + '\')">' + lan.soft.setup + '</a> | ';
                                                }
                                                else {
                                                    option += '<a class="btlink" onclick="soft.set_soft_config(\'' + item.name + '\')">' + lan.soft.setup + '</a> | ';
                                                }
                                            } else {
                                                option = pay_opt + ' | ' + option;
                                            }
                                            option += '<a class="btlink" onclick="bt.soft.un_install(\'' + item.name + '\')" >' + lan.soft.uninstall + '</a>';
                                        }
                                        else if (item.task == '-1') {
                                            option = '<a class="btlink" onclick="messagebox()"  >正在安装</a>';
                                            soft.is_install = true;
                                        }
                                        else if (item.task == '0') {
                                            option = '<a class="btlink" onclick="messagebox()"  >等待安装</a>';
                                            soft.is_install = true;
                                        }
                                        else if (item.task == '-2') {
                                            option = '<a class="btlink" onclick="messagebox()"  >正在更新</a>';
                                            soft.is_install = true;
                                        }
                                        else {
                                            if (pay_opt) {
                                                option = pay_opt;
                                            }
                                            else {
                                                option = '<a class="btlink" onclick="bt.soft.install(\'' + item.name + '\',this)"  >' + lan.soft.install + '</a>';
                                            }
                                        }
                                    }
                                }
                            }else {
                                if (rdata.apache22 && is_php && $.inArray(item.name, phps) == -1) {
                                    if (item.setup) {
                                        option = '<a class="btlink" onclick="bt.soft.un_install(\'' + item.name + '\')" >' + lan.soft.uninstall + '</a>';
                                    }
                                    else {
                                        option = '<span title="Apache2.2不兼容此版本，如需使用请切换到Apache2.4或Nginx">不兼容</span>';
                                    }
                                }
                                else if (rdata.apache24 && item.name == 'php-5.2') {
                                    if (item.setup) {
                                        option = '<a class="btlink" onclick="bt.soft.un_install(\'' + item.name + '\')" >' + lan.soft.uninstall + '</a>';
                                    }
                                    else {
                                        option = '<span title="Apache2.4不兼容此版本，如需使用请切换到Apache2.2或Nginx">不兼容</span>';
                                    }
                                }else {
                                    if (item.setup && item.task == '1') {
                                        if (pay_opt == '') {
                                            if (item.versions.length > 1) {
                                                for (var i = 0; i < item.versions.length; i++) {
                                                    var min_version = item.versions[i]
                                                    var ret = bt.check_version(item.version, min_version.m_version + '.' + min_version.version);
                                                    if (ret > 0) {
                                                        if (ret == 2) option += '<a class="btlink" onclick="bt.soft.update_soft(\'' + item.name + '\',\'' + item.title + '\',\'' + min_version.m_version + '\',\'' + min_version.version + '\',\'' + min_version.update_msg.replace(/\n/g,"_bt_") + '\',\''+ item.type +'\')" >更新</a> | ';
                                                        break;
                                                    }
                                                }
                                            }
                                            else {
                                                var min_version = item.versions[0];
                                                var cloud_version = min_version.m_version + '.' + min_version.version;
                                                if (item.version != cloud_version) option += '<a class="btlink" onclick="bt.soft.update_soft(\'' + item.name + '\',\'' + item.title + '\',\'' + min_version.m_version + '\',\'' + min_version.version + '\',\'' + min_version.update_msg.replace(/\n/g, "_bt_") + '\',\''+ item.type +'\')" >更新</a> | ';
                                            }
                                            if (item.admin) {
                                                option += '<a class="btlink" onclick="bt.soft.set_lib_config(\'' + item.name + '\',\'' + item.title + '\')">' + lan.soft.setup + '</a> | ';
                                            }
                                            else {
                                                option += '<a class="btlink" onclick="soft.set_soft_config(\'' + item.name + '\')">' + lan.soft.setup + '</a> | ';
                                            }
                                        } else {
                                            option = pay_opt + ' | ' + option;
                                        }
                                        option += '<a class="btlink" onclick="bt.soft.un_install(\'' + item.name + '\')" >' + lan.soft.uninstall + '</a>';
                                    }
                                    else if (item.task == '-1') {
                                        option = '<a class="btlink" onclick="messagebox()"  >正在安装</a>';
                                        soft.is_install = true;
                                    }
                                    else if (item.task == '0') {
                                        option = '<a class="btlink" onclick="messagebox()"  >等待安装</a>';
                                        soft.is_install = true;
                                    }
                                    else if (item.task == '-2') {
                                        option = '<a class="btlink" onclick="messagebox()"  >正在更新</a>';
                                        soft.is_install = true;
                                    }
                                    else {
                                        if (pay_opt) {
                                            option = pay_opt;
                                        }
                                        else {
                                            option = '<a class="btlink" onclick="bt.soft.install(\'' + item.name + '\',this)"  >' + lan.soft.install + '</a>';
                                        }
                                    }
                                }
                            }
                            return option;
                        }
                    }
                ],
                data: data
            })
            bt.set_cookie('load_page', (page+'').split('not_load')[0])
            bt.set_cookie('load_type', type)
            bt.set_cookie('load_search', search)
            if (soft.is_install) {
                setTimeout(function () {
                    soft.get_list(bt.get_cookie('load_page') + 'not_load', bt.get_cookie('load_type'), bt.get_cookie('load_search'));
                }, 3000);
            }
            if(rdata.recommend){
                _this.render_promote_list(rdata.recommend);
            }
        })
    },
    // 渲染列表
    render_promote_list:function(data){
        if($('#soft_recom_list').length > 0) $('#soft_recom_list').remove();
        var html = $('<ul id="soft_recom_list" class="recom_list"></ul>'),that = this;
        for(var i=0;i< data.length;i++){
            var type = '', item = data[i];
            (function(item){
                switch (item.type) {
                    case 'link': // 链接推荐
                        type = $('<a href="'+ item.data +'" target="_blank" title="'+ (item.title || '') +'"><span>'+ (item.title || '') +'</span></a>');
                        break;
                    case 'soft': // 软件推荐
                    case 'other': // 第三方推荐
                    case 'onekey': // 一键部署推荐
                        type = $('<a href="javascript:;" class="btlink" title="'+ (item.title || '') +'"><span>'+ (item.title || '') +'</span></a>').click(function(){
                            that.render_promote_view(item);
                        });
                    break;
                }
                html.append($('<li></li>').append(type));
            }(item))
            // html.append($('<li><img src="'+ item.image +'"></li>').append(type));
        }
        $('#updata_pro_info').before(html);
    },
    // 渲染软件列表
    render_promote_view:function(find){
        var that = this,is_single_product = find.data.length > 1,find_data = find.data;
        if(is_single_product){
            layer.open({
                title:find.title,
                area:'800px',
                btn:false,
                closeBtn:2,
                shadeClose:false,
                content: (function(){
                    var html = '';
                    for(var i=0;i<find_data.length;i++){
                        var item = find_data[i],thtml = '';
                        if(!item.setup){
                            thtml = '<button type="button" class="btn btn-success btn-xs" onclick="bt.soft.install(\''+ item.name +'\',this)">立即安装</button>';
                        }else{
                            if(item.pid != 0){
                                if(item.endtime == 0){ //永久
                                    thtml = '<button type="button" class="btn btn-success btn-xs" onclick="bt.soft.set_lib_config(\''+ item.name +'\',\''+ item.title +'\')">打开软件</button>';
                                }else if(item.endtime > 0){ //已购买
                                    thtml = '<button type="button" class="btn btn-success btn-xs" onclick="bt.soft.set_lib_config(\''+ item.name +'\',\''+ item.title +'\')">打开软件</button>';
                                }else if(item.endtime == -1){  //未购买
                                    thtml = '<button type="button" class="btn btn-success btn-xs" onclick=\'bt.soft.product_pay_view('+ JSON.stringify({name:item.title,pid:item.pid,type:item.type,pulgin:true,renew:item.endtime}) +');\'>立即购买</button>';
                                }else if(item.endtime  == -2){ //已过期
                                    thtml = '<button type="button" class="btn btn-success btn-xs" onclick=\'bt.soft.product_pay_view('+ JSON.stringify({name:item.title,pid:item.pid,type:item.type,pulgin:true,renew:item.endtime}) +');\'>立即续费</button>';
                                }
                            }else{
                                thtml = '<button type="button" class="btn btn-success btn-xs" onclick="bt.soft.set_lib_config(\''+ item.name +'\',\''+ item.title +'\')">打开软件</button>';
                            }
                        }
                        html += '<div class="recom_item_box">' +
                            '<div class="recom_item_left">' +
                                '<div class="recom_item_images"><img src="/static/img/'+(find.type == 'onekey'?'dep_ico':'soft_ico')+'/ico-'+ item.name +'.png" /></div>' +
                                '<div class="recom_item_pay"><a href="javascript:;" class="btlink" style="color:'+(item.setup?'#20a53a':'#666')+'">'+ (item.setup?'已安装':'未安装') +'</a></div>'+
                            '</div>' +
                            '<div class="recom_item_right">' +
                                '<div class="recom_item_title">' +
                                    '<div class="recom_item_text">'+ item.title + '&nbsp;v'+ item.version +'</div>' +
                                    '<div class="recom_item_price">￥<span>'+ item.price +'</span>/月</div>' +
                                '</div>' +
                                '<div class="recom_item_info" title="'+ item.ps +'">'+ item.ps +'</div>'+
                                '<div class="recom_item_btn">'+ thtml +'</div>'+
                            '</div>' +
                        '</div>'
                    }
                    return html;
                })(),
            });
        }
    },
    set_soft_tips:function(el,type){
        var tips_info = $('<div class="alert" style="margin-bottom:15px"><div class="soft_tips_text"></div><div class="btn-ground" style="display:inline-block;"></div></div>'), explain = tips_info.find('.soft_tips_text'), btn_ground = tips_info.find('.btn-ground');
        $(el).empty();
        type = parseInt(type);
        if(type != 11) $(el).next('.onekey-menu-sub').remove();
        if(type == 10){
            explain.text('安全提醒：第三方插件上架前，宝塔官方进行了安全审计，但可能还存在安全风险，在生产环境使用前请自行甄别');
            btn_ground = soft.render_tips_btn(btn_ground,[
                {title:'免费入驻',href:'https://www.bt.cn/developer/',rel:'noreferrer noopener',target:'_blank',btn:'免费入驻',class:'btn btn-success btn-xs va0',style:"margin-left:10px;"},
                {title:'点击获取第三方应用',rel:'noreferrer noopener',href:'https://www.bt.cn/bbs/forum-40-1.html',target:'_blank',btn:'获取第三方应用',class:'btn btn-success btn-xs va0 ml15',style:"margin-left:10px;"},
                {title:'导入插件',href:'javascript:;',btn:'导入插件','class':'btn btn-success btn-xs va0 ml15','style':"margin-left:10px;",click:function(e){
                    var input = $('<input type="file" style="display:none;" accept=".zip,.tar.gz" id="update_zip" multiple="multiple">').change(function (e) {
                        var files =$(this)[0].files;
                        if (files.length == 0) return;
                        soft.update_zip(files[0]);
                    }).click();
                }}
            ]);
            $(el).append(tips_info.addClass('alert-danger'));
        }else if(type == 11){
            explain.text('宝塔一键部署已上线，诚邀全球优秀项目入驻(限项目官方) ');
            btn_ground = soft.render_tips_btn(btn_ground,[
                {title:'免费入驻',href:'https://www.bt.cn/bbs/thread-33063-1-1.html',rel:'noreferrer noopener',target:'_blank',btn:'免费入驻',class:'btn btn-success btn-xs va0',style:"margin-left:10px;"},
                {title:'导入项目',href:'javascript:;',rel:'noreferrer noopener',btn:'导入项目',class:'btn btn-success btn-xs va0',style:"margin-left:10px;",click:soft.input_package}
            ]);
            $(el).append(tips_info.addClass('alert-info'));
        }else{
            var ltd = parseInt(bt.get_cookie('ltd_end')),pro = parseInt(bt.get_cookie('pro_end')),todayDate = parseInt(new Date().getTime()/1000),_ltd = null;
            if((ltd > 0 && (ltd == pro || pro < 0)) || (ltd < 0 && pro >= 0) || (ltd > 0 && pro >= 0)){
                _ltd = ((ltd > 0 && (ltd == pro || pro < 0)) || (ltd > 0 && pro >= 0))?1:0;
                explain.html('当前为'+ (_ltd?'企业版':'专业版') +'，'+ (_ltd?'企业版':'专业版') +'可以免费使用'+ (_ltd?'专业版及企业版插件':'专业版插件') + (!(pro == 0 && ltd < 0)?('，过期时间：'+ (bt.format_data((_ltd?ltd:pro),'yyyy/MM/dd') ) +''+((((_ltd?ltd:pro) - todayDate) <= 15*24*60*60)?('，<span style="color:red">距离过期仅剩'+ Math.round(((_ltd?ltd:pro) - todayDate) / (24*60*60)) +'天</span>'):'')):'，过期时间：<span style="color: #fc6d26;font-weight: bold;">永久授权</span>'));
            }else if(ltd == -1 && pro == -1){
                explain.html('专业版可以免费使用专业版插件，企业版可以免费使用专业版及企业版插件。');
            }else if(pro == 0 && ltd < 0){
                _ltd = 2;
                explain.html('当前为专业版，专业版可以免费使用专业版插件，过期时间：永久授权。'+(type == 12?'&nbsp;&nbsp;<span style="color:#af8e48">升级企业版，企业可以免费试用企业版插件及专业版插件。</span>':''));
                if(type == 12){
                    btn_ground  = soft.render_tips_btn(btn_ground,{title:'立即升级',href:'javascript:;',btn:'立即升级','class':'btn btn-success btn-xs va0 ml15','style':"margin-left:10px;",click:bt.soft.updata_ltd});
                }
            }else if(ltd == -2 || pro == -2){
                _ltd = (ltd == -2)?1:0;
                explain.html('当前为'+ (_ltd?'企业版':'专业版') +'，'+ (_ltd?'企业版':'专业版') +'可以免费使用'+ (_ltd?'专业版及企业版插件':'专业版插件') +'，<span style="color:red">'+ (_ltd?'企业版':'专业版') +'已过期</span>');
            }
            var btn_config = {title:null,href:'javascript:;',btn:null,'class':'btn btn-success btn-xs va0 ml15','style':"margin-left:10px;",click:null};
            var set_btn_style = function(res){
                if(!res.status || !res){
                    $.extend(btn_config,{title:'立即登录',btn:'立即登录',click:function(){
                        bt.pub.bind_btname(function(){
                            window.location.reload();
                        });
                    }});
                }else{
                    if(type == 12 && (ltd < 0 && pro >=0)){
                        explain.html('企业版可以免费使用专业版及企业版插件，了解专业版和企业版的区别，请点击<a href="https://www.bt.cn/download/linux.html" target="_blank" class="btlink ml5">查看详情</a>。<a href="https://www.bt.cn/bbs/forum.php?mod=viewthread&tid=50342&page=1&extra=#pid179211" target="_blank" class="btlink ml5">《专业版升级企业版教程》</a>');
                        $(el).append(tips_info.addClass('alert-ltd-success'));
                        return false;
                    }else{
                        if(_ltd != 2){
                            var fun = '';
                            switch(_ltd){
                                case null:
                                    fun = bt.soft.updata_commercial_view
                                    break;
                                case 1:
                                    fun = bt.soft.updata_ltd
                                    break;
                                case 0:
                                    fun = bt.soft.updata_pro
                                    break;
                            }
                            $.extend(btn_config,{title:_ltd == null?'立即购买':'立即续费',btn:_ltd == null?'立即购买':'立即续费',click:fun})
                        }
                    }
                }
                if(_ltd != 2){
                    if(!(pro == 0 && ltd < 0)){
                        btn_ground  = soft.render_tips_btn(btn_ground,btn_config);
                    }
                }
                $(el).append(tips_info.addClass(_ltd == 1?'alert-ltd-success':'alert-success'));
            }
            var bt_user_info = bt.get_cookie('bt_user_info');
            if(!bt_user_info){
                bt.pub.get_user_info(function(res){
                    if(!res.status){
                         set_btn_style(false);
                        return false;
                    }
                    bt.set_cookie('bt_user_info',JSON.stringify(res),300000);
                    set_btn_style(res);
                });
            }else{
                set_btn_style(JSON.parse(bt.get_cookie('bt_user_info')));
            }
        }
    },
    render_tips_btn:function(node,arry){
        if(!Array.isArray(arry)) arry = [arry]
        for(var i=0;i<arry.length;i++){
            var item = arry[i], btn = '<a ';
            for(var key in item){ if(key != 'click' && key != 'btn') btn += item[key]?(key+'="'+item[key]+'" '):'' }
            btn += '>'+item['btn'] +'</a>';
            if(item.click){
                btn = $(btn).on('click',item.click)
            }
            node.append(btn);
        }
        return node
    },
    get_dep_list: function (p) {
        var loadT = layer.msg('正在获取列表 <img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, '#000'] });
        var pdata = {}
        var search = $("#SearchValue").val();
        if (search != '') {
            pdata['search'] = search
        }
        var type = '';
        var istype = getCookie('depType');
        if (istype == 'undefined' || istype == 'null' || !istype) {
            istype = '0';
        }
        pdata['type'] = istype;

        var force = bt.get_cookie('force');
        if (force === '1') {
            pdata['force'] = force;
        }
        bt.set_cookie('force',0);
        $.post('/deployment?action=GetList', pdata, function (rdata) {
            layer.close(loadT)
            var tBody = '';
            soft.set_soft_tips('#updata_pro_info',11);
            rdata.type.unshift({ icon: 'icon', id: 0, ps: '全部', sort: 1, title: '全部' },{ icon: 'icon', id: -1, ps: '已安装', sort: 1, title: '已安装' });
            for (var i = 0; i < rdata.type.length; i++) {
                var c = '';
                if ('11' == rdata.type[i].id) {
                    c = 'class="on"';
                }
                tBody += '<span typeid="' + rdata.type[i].id + '" ' + c + '>' + rdata.type[i].title + '</span>';
            }
            $(".softtype").html(tBody);
            $(".menu-sub span").click(function () {
                var _type = $(this).attr('typeid');
                bt.set_cookie('softType', _type);
                $(this).addClass("on").siblings().removeClass("on");
                if (_type !== '11') {
                    soft.get_list(0, _type);
                } else {
                    soft.get_dep_list(1);
                }
            });
            if ($(".onekey-type").attr("class") === undefined) {
                tbody = '<div class="onekey-menu-sub onekey-type" style="margin-bottom:15px">';
                rdata.dep_type.unshift({ tid: 0, title: '全部' })
                rdata.dep_type.push({ tid: 100, title: '其它' })
                for (var i = 0; i < rdata.dep_type.length; i++) {
                    var c = '';
                    if (istype == rdata.dep_type[i].tid) {
                        c = 'class="on"';
                    }
                    tbody += '<span typeid="' + rdata.dep_type[i].tid + '" ' + c + '>' + rdata.dep_type[i].title + '</span>';
                }
                tbody += "</div>";
                $("#updata_pro_info").after(tbody);
                $(".onekey-menu-sub span").click(function () {
                    setCookie('depType', $(this).attr('typeid'));
                    $(this).addClass("on").siblings().removeClass("on");
                    soft.get_dep_list(1);
                });
            }
            var zbody = '<thead>\
			                <tr>\
				                <th>名称</th>\
				                <th>版本</th>\
				                <th>简介</th>\
				                <th>支持PHP版本</th>\
                                <th>提供者</th>\
                                <th>评价</th>\
				                <th style="text-align: right;" width="150">操作</th>\
			                </tr>\
		                </thead>';
            var icon_other ='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAYFJREFUeNpi/P//P8NAAhZkzrVr1zyB1FwglqSiHSZAfBZZQEtLC7sDQJZLSUlJcnNzU8Xm27dvg6jVQByqqqp6FpsaJjS+JCcnJ8O/f/+ogkFATk5uJ8gRQMcYE+MAqgN2dvYMeXn5g0DmGmyOYKJHQmNjY0tQUFA4gc0RLLS0mI+PD5YOQCACSp8BYka6OEBUVJRBXFwcW8IkPgQ+r2lk+PPsJnl5XEqdgTeknvhyABsAWS6Ytwyr3PtJUTjlYPKEAEWJEGQ5MZbQzAGEQoDmDhgNAWITGk0dQCkYcAewUJoIh38IgIpTchMai6Qa5Q4gVJYP+SgYcAcwIjfLHxZo0qWNLj/hOp4GCQs7bo0121D4D1u8wGIwGlkcd/3+k/xyANlgdMcgy8McRbM0QIoFVC8J8VkOCxVSHMdCTZ+TEyooDvjPKfCP8ddXJgZGJqISIskW/v8HtIP/H85seGdWYT3L/eN1jN8/0qR8+M8l8PePgkWzSlp/I1YHDAQACDAAtKS/DHmsv9AAAAAASUVORK5CYII='
            for (var i = 0; i < rdata.list.length; i++) {
                var remove_opt = '';
                if (rdata.list[i].id === 0) {
                    remove_opt = ' | <a class="btlink" onclick="soft.update_package(\'' + rdata.list[i].name + '\')">更新</a> | <a class="btlink" onclick="soft.remove_other_dep(\'' + rdata.list[i].name + '\')">删除</a>';
                    rdata.list[i].min_image = icon_other
                } else {
                    rdata.list[i].min_image += '?t=' + new Date().format("yyyyMMdd");
                }
                zbody += '<tr>'
                    + '<td><img style="width:22px;height:20px" src="' + rdata.list[i].min_image +'">' + rdata.list[i].title + '</td>'
                    + '<td>' + rdata.list[i].version + '</td>'
                    + '<td>' + rdata.list[i].ps + '</td>'
                    + '<td>' + rdata.list[i].php + '</td>'
                    + '<td><a class="btlink" target="_blank" rel="noreferrer noopener" href="' + rdata.list[i].official + '">' + (rdata.list[i].author == '宝塔' ? rdata.list[i].title : rdata.list[i].author) + '</a></td>'
                    + '<td>' + (rdata.list[i].sort !== undefined?('<a href="javascript:;" class="btlink open_score_view" onclick="score.open_score_view('+ rdata.list[i].id +',\''+ rdata.list[i].title +'\','+ rdata.list[i].count +')" >' + (rdata.list[i].sort <= 0 || rdata.list[i].sort > 5?'无评分':rdata.list[i].sort.toFixed(1))+'</a>'):'--')
                    + '</td>'
                    + '<td class="text-right"><a href="javascript:onekeyCodeSite(\'' + rdata.list[i].name + '\',\'' + rdata.list[i].php + '\',\'' + rdata.list[i].title + '\',\'' + rdata.list[i].enable_functions + '\');" class="btlink">一键部署</a>' + remove_opt+'</td>'
                    + '</tr>'
            }
            $("#softList").html(zbody);
            $("#softPage").html('');
            $(".searchInput").val('');

        });
    },
    remove_other_dep: function (name) {
        bt.show_confirm('删除自定义项目', '您真的要删除[' + name + ']吗?', function () {
            var loadT = layer.msg('正在删除，请稍候...', { icon: 16, time: 0, shade: 0.3 });
            $.post('/deployment?action=DelPackage', { dname: name }, function (rdata) {
                layer.close(loadT);
                if (rdata.status) soft.get_dep_list();
                setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }); }, 1000);
            });
        });
    },
    input_package: function () {
        var con = '<form class="bt-form pd20 pb70" id="input_package">\
					<div class="line"><span class="tname">英文名</span>\
						<div class="info-r c9"><input class="bt-input-text" type="text" value="" name="name"  placeholder="项目英文名" style="width:190px" />\
							<span>格式: [0-9A-Za-z_-]+，不要带有空格和特殊字符</span>\
						</div>\
					</div>\
					<div class="line"><span class="tname">中文名</span>\
						<div class="info-r c9"><input class="bt-input-text" name="title" placeholder="项目中文名" style="width:190px" type="text">\
                            <span>用于显示到列表的名称</span>\
                        </div>\
					</div>\
                    <div class="line"><span class="tname">PHP版本</span>\
						<input class="bt-input-text mr5 " name="php"  placeholder="如：53,54,55,56,70,71,72" style="width:190px" value="" type="text" />\
						<span class="c9">多个请使用","(逗号)隔开，不要使用PHP5.2</span>\
					</div>\
					<div class="line"><span class="tname">解禁的函数</span>\
						<input class="bt-input-text mr5" name="enable_functions" style="width:190px" placeholder="如：system,exec" type="text" />\
						<span class="c9">多个请使用","(逗号)隔开，只解禁必要函数</span>\
					</div>\
                    <div class="line"><span class="tname">项目版本</span>\
						<input class="bt-input-text mr5" name="version" style="width:190px" placeholder="如：5.2.1" type="text" />\
						<span class="c9">当前导入的项目版本</span>\
					</div>\
                    <div class="line"><span class="tname">简介</span>\
						<div class="info-r c15"><input  class="bt-input-text mr5" name="ps" value="" type="text" style="width:290px" /></div>\
					</div>\
					<div class="line"><span class="tname">上传项目包</span>\
						<input class="bt-input-text mr5" name="dep_zip" type="file" style="width:290px" placeholder="如：system,exec" >\
						<span class="c9">请上传zip格式的项目包,里面必需包含auto_insatll.json配置文件</span>\
					</div>\
					<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm onekeycodeclose" onclick="layer.closeAll()">取消</button>\
						<button type="button" class="btn btn-success btn-sm" onclick="soft.input_package_to()">提交</button>\
					</div>\
				</from>';
        layer.open({
            type: 1,
            title: "导入一键部署项目包",
            area: '600px',
            closeBtn: 2,
            shadeClose: false,
            content: con
        });
    },
    update_package: function (p_name) {
        $.post('/deployment?action=GetPackageOther', { p_name: p_name }, function (rdata) {
            var con = '<form class="bt-form pd20 pb70" id="input_package">\
					<div class="line"><span class="tname">英文名</span>\
						<input class="bt-input-text" type="text" value="'+rdata.name+'" name="name"  placeholder="项目英文名" style="width:190px" />\
					    <span class="c9" style="margin-left: 5px;">格式: [0-9A-Za-z_-]+，不要带有空格和特殊字符</span>\
					</div>\
					<div class="line"><span class="tname">中文名</span>\
						<input class="bt-input-text" name="title" value="'+ rdata.title +'" placeholder="项目中文名" style="width:190px" type="text">\
                        <span class="c9" style="margin-left: 5px;">用于显示到列表的名称</span>\
					</div>\
                    <div class="line"><span class="tname">PHP版本</span>\
						<input class="bt-input-text mr5 " name="php"  placeholder="如：53,54,55,56,70,71,72" style="width:190px" value="'+ rdata.php +'" type="text" />\
						<span class="c9">多个请使用","(逗号)隔开，不要使用PHP5.2</span>\
					</div>\
					<div class="line"><span class="tname">解禁的函数</span>\
						<input class="bt-input-text mr5" name="enable_functions" value="'+ rdata.enable_functions +'" style="width:190px" placeholder="如：system,exec" type="text" />\
						<span class="c9">多个请使用","(逗号)隔开，只解禁必要函数</span>\
					</div>\
                    <div class="line"><span class="tname">项目版本</span>\
						<input class="bt-input-text mr5" name="version" value="'+ rdata.version +'" style="width:190px" placeholder="如：5.2.1" type="text" />\
						<span class="c9">当前导入的项目版本</span>\
					</div>\
                    <div class="line"><span class="tname">简介</span>\
						<div class="info-r c15"><input  class="bt-input-text mr5" name="ps" value="'+ rdata.ps +'" type="text" style="width:290px" /></div>\
					</div>\
					<div class="line"><span class="tname">上传项目包</span>\
						<input class="bt-input-text mr5" name="dep_zip" type="file" style="width:290px" placeholder="如：system,exec" >\
						<span class="c9">请上传zip格式的项目包,里面必需包含auto_insatll.json配置文件</span>\
					</div>\
					<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm onekeycodeclose" onclick="layer.closeAll()">取消</button>\
						<button type="button" class="btn btn-success btn-sm" onclick="soft.input_package_to()">更新</button>\
					</div>\
				</from>';
            layer.open({
                type: 1,
                title: "更新一键部署项目包",
                area: '600px',
                closeBtn: 2,
                shadeClose: false,
                content: con
            });
        });
    },
    input_package_to: function () {
        var pdata = new FormData($("#input_package")[0]);
        if (!pdata.get('name') || !pdata.get('title') || !pdata.get('version') || !pdata.get('php') || !pdata.get('ps')) {
            layer.msg('以下为必填(英文名/中文名/项目版本/PHP版本/简介)', { icon: 2 });
            return;
        }
        var fs = $("input[name='dep_zip']")[0].files;
        if (fs.length < 1) {
            layer.msg('请选择项目包文件', { icon: 2 });
            return;
        }
        var f = fs[0]
        if (f.type.indexOf('zip') == -1) {
            layer.msg('只支持zip格式的文件！');
            return;
        }
        if (!pdata.get('dep_zip')) pdata.append('dep_zip', f);

        var loadT = layer.msg('正在导入...', { icon: 16, time: 0, shade:0.3 });

        $.ajax({
            url: "/deployment?action=AddPackage",
            type: "POST",
            data: pdata,
            processData: false,
            contentType: false,
            success: function (data) {
                layer.close(loadT);
                if (data.status) {
                    layer.closeAll();
                    setCookie('depType',100)
                    soft.get_dep_list();
                    setTimeout(function () { layer.msg('导入成功!'); },1000)
                }
            },
            error: function (responseStr) {
                layer.msg('上传失败2!', { icon: 2 });
            }
        });
    },
    flush_cache: function () {
        bt.set_cookie('force', 1);
        soft.get_list();
    },
    get_config_menu: function (name) //获取设置菜单显示
    {
        var meun = '';
        if (bt.os == 'Linux') {

            var datas = {
                public: [
                    { type: 'config', title: lan.soft.config_edit },
                    { type: 'change_version', title: lan.soft.nginx_version }
                ],
                mysqld: [
                    { type: 'change_data_path', title: lan.soft.save_path },
                    { type: 'change_mysql_port', title: lan.site.port },
                    { type: 'get_mysql_run_status', title: lan.soft.status },
                    { type: 'get_mysql_status', title: lan.soft.php_main7 },
                    { type: 'mysql_log', title: lan.soft.log },
                    { type: 'mysql_slow_log', title: lan.public.slow_log },
                ],
                phpmyadmin: [
                    { type: 'phpmyadmin_php', title: lan.soft.php_version },
                    { type: 'phpmyadmin_safe', title: lan.soft.safe }
                ],
                memcached: [
                    { type: 'memcached_status', title: '负载状态' },
                    { type: 'memcached_set', title: '性能调整' },
                ],
                redis: [
                    { type: 'get_redis_status', title: '负载状态' },
                ],
                tomcat: [
                    { type: 'log', title: '运行日志' }
                ],
                apache: [
                    { type: 'apache_set', title: '性能调整' },
                    { type: 'apache_status', title: lan.soft.nginx_status },
                    { type: 'log', title: '运行日志' }
                ],
                openlitespeed: [{
                    type: 'openliMa_set',
                    title: '参数设置'
                }],
                nginx: [
                    { type: 'nginx_set', title: '性能调整' },
                    { type: 'nginx_status', title: lan.soft.nginx_status },
                    { type: 'log', title: '错误日志' }
                ]
            };
            var arrs = datas.public;
            if (name == 'phpmyadmin') arrs = [];
            if (name == 'openlitespeed') arrs.length = 1;
            arrs = arrs.concat(datas[name]);
            if (arrs) {
                for (var i = 0; i < arrs.length; i++) {
                    var item = arrs[i];
                    if (item) {
                        meun += '<p onclick="soft.get_tab_contents(\'' + item.type + '\',this)">' + item.title + '</p>';
                    }
                }
            }
        }
        return meun;
    },
    set_soft_config: function (name) {
        //软件设置
        var _this = this;
        var loading = bt.load();
        bt.soft.get_soft_find(name, function (rdata) {
            loading.close();

            if (name == 'mysql') name = 'mysqld';
            var menuing = bt.open({
                type: 1,
                area: "650px",
                title: name + lan.soft.admin,
                closeBtn: 2,
                shift: 0,
                content: '<div class="bt-w-main" style="width:640px;"><div class="bt-w-menu bt-soft-menu"></div><div id="webEdit-con" class="bt-w-con pd15" style="height:555px;overflow:auto"><div class="soft-man-con bt-form"></div></div></div>'
            });
            var menu = $('.bt-soft-menu').data("data", rdata);
            setTimeout(function () {
                menu.append($('<p class="bgw bt_server" onclick="soft.get_tab_contents(\'service\',this)">' + lan.soft.service + '</p>'))
                if (rdata.version_coexist) {
                    var ver = name.split('-')[1].replace('.', '');
                    var opt_list = [
                        { type: 'set_php_config', val: ver, title: lan.soft.php_main5 },
                        { type: 'config_edit', val: ver, title: lan.soft.config_edit },
                        { type: 'set_upload_limit', val: ver, title: lan.soft.php_main2 },
                        { type: 'set_timeout_limit', val: ver, title: lan.soft.php_main3, php53: true },
                        { type: 'config', val: ver, title: lan.soft.php_main4 },
                        { type: 'fpm_config', val: ver, title: 'FPM配置文件' },
                        { type: 'set_dis_fun', val: ver, title: lan.soft.php_main6 },
                        { type: 'set_fpm_config', val: ver, title: lan.soft.php_main7, apache24: true, php53: true },
                        { type: 'get_php_status', val: ver, title: lan.soft.php_main8, apache24: true, php53: true },
                        { type: 'get_php_session', val: ver, title: lan.soft.php_main9, apache24: true, php53: true },
                        { type: 'get_fpm_logs', val: ver, title: lan.soft.log, apache24: true, php53: true },
                        { type: 'get_slow_logs', val: ver, title: lan.public.slow_log, apache24: true, php53: true },
                        { type: 'get_phpinfo', val: ver, title: 'phpinfo' }
                    ]

                    var phpSort = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,12],
                    webcache = bt.get_cookie('serverType') == 'openlitespeed' ? true : false;
                    for (var i = 0; i < phpSort.length; i++) {
                        var item = opt_list[i];
                        if (item) {
                            if (item.os == undefined || item['os'] == bt.os) {
                                if (name.indexOf("5.2") >= 0 && item.php53) continue;
                                if (webcache && (item.type == 'set_fpm_config' || item.type == 'fpm_config' || item.type=='get_php_status')) continue;
                                var apache24 = item.apache24 ? 'class="apache24"' : '';
                                menu.append($('<p data-id="' + i + '" ' + apache24 + ' onclick="soft.get_tab_contents(\'' + item.type + '\',this)" >' + item.title + '</p>').data('item', item))
                            }
                        }
                    }
                }
                else {
                    menu.append(soft.get_config_menu(name));
                }
                $(".bt-w-menu p").click(function () {
                    $(this).addClass("bgw").siblings().removeClass("bgw");
                });
                $(".bt-w-menu p:eq(0)").trigger("click");
                bt.soft.get_soft_find('apache', function (rdata) {
                    if (rdata.setup) {
                        if (rdata.version.indexOf('2.2') >= 0) {
                            if (name.indexOf('php-') != -1) {
                                $(".apache24").hide();
                                $(".bt_server").remove();
                                $(".bt-w-menu p:eq(0)").trigger("click");
                            }

                            if (name.indexOf('apache') != -1) {
                                $(".bt-soft-menu p:eq(3)").remove()
                                $(".bt-soft-menu p:eq(3)").remove()
                            }
                        }
                    }
                })
            }, 100)
        })
    },
    get_tab_contents: function (key, obj) //获取设置菜单操作
    {
        var data = $(obj).parents('.bt-soft-menu').data('data');
        var version = data.name;
        if (data.name.indexOf('php-') >= 0) version = data.name.split('-')[1].replace('.', '');
        switch (key) {
            case 'service':
                var tabCon = $(".soft-man-con").empty();
                var status_list = [
                    { opt: data.status ? 'stop' : 'start', title: data.status ? lan.soft.stop : lan.soft.start },
                    { opt: 'restart', title: lan.soft.restart },
                    { opt: 'reload', title: lan.soft.reload }
                ]
                if (data.name == 'phpmyadmin') {
                    status_list = [status_list[0]];
                }else{
                    var btns = $('<div class="sfm-opt"></div>');
                    for (var i = 0; i < status_list.length; i++)  btns.append('<button class="btn btn-default btn-sm" onclick="bt.pub.set_server_status(\'' + data.name + '\',\'' + status_list[i].opt + '\')">' + status_list[i].title + '</button>');
                    tabCon.append('<p class="status">' + lan.soft.status + '：<span>' + (data.status ? lan.soft.on : lan.soft.off) + '</span><span style="color: ' + (data.status ? '#20a53a;' : 'red;') + ' margin-left: 3px;" class="glyphicon ' + (data.status ? 'glyphicon glyphicon-play' : 'glyphicon-pause') + '"></span></p');
                    tabCon.append(btns);
                }
                if (data.name == 'phpmyadmin') {
                    tabCon.append('<div style="margin-top:25px;">\
                    <div class="info-r "><input type="checkbox" class="status" '+(data.status?'checked':'')+' id="pma_status" name="status" onclick="bt.pub.set_server_status(\'' + data.name + '\',\'' + (data.status?'stop':'start') + '\')" style="vertical-align: top;margin-right: 10px;"><label class="mr20" for="pma_status" style="font-weight:normal;vertical-align: sub;">启用公共访问权限</label></div>\
                    <p style="margin-top:5px;"><span>公共访问地址: </span><a class="btlink" href="' + data.ext.url + '" target="_blank">' + data.ext.url + '</a></p>\
                    </div>');
                    tabCon.append('<ul class="help-info-text c7 mtb15" style="padding-top:30px">\
                        <li>phpmyadmin启用公共访问权限可能存在安全风险，建议非必要不启用!</li>\
                        <li>当前版本的phpmyadmin在不需要公共访问权限的情况下不再依赖nginx/apache</li>\
                        <li>phpmyadmin的服务状态不影响通过面板（非公共）访问phpmyadmin</li>\
                        <li>在未开启公共访问权限的情况下，由面板接管访问权限，即需登录面板才能访问</li>\
                    </ul>');
                }
                var help = '<ul class="help-info-text c7 mtb15" style="padding-top:30px"><li>' + lan.soft.mysql_mem_err + '</li></ul>';
                if (name == 'mysqld') tabCon.append(help);

                break;
            case 'config':
                var tabCon = $(".soft-man-con").empty();
                tabCon.append('<p style="color: #666; margin-bottom: 7px">' + lan.bt.edit_ps + '</p>');
                tabCon.append('<div class="bt-input-text ace_config_editor_scroll" style="height: 320px;min-height:350px;line-height:18px;" id="textBody"></div>')
                tabCon.append('<button id="OnlineEditFileBtn" class="btn btn-success btn-sm" style="margin-top:10px;">' + lan.public.save + '</button>')
                var _arry = [lan.get('config_edit_ps', [version])];
				if (data.name.indexOf('php-') >= 0){
					_arry.push(lan.soft.config_php_tips);
				}
				tabCon.append(bt.render_help(_arry))
				$('.return_php_info').click(function(){
					$('.bt-soft-menu p:eq(12)').click();
                });
                var fileName = bt.soft.get_config_path(version),
                loadT = bt.load(lan.soft.get);
                if (data.php_ini) fileName = data.php_ini;
                var config = bt.aceEditor({el:'textBody',path:fileName});
                $("#OnlineEditFileBtn").click(function(){
                    bt.saveEditor(config);
                });
                break;
            case 'fpm_config':
                    var tabCon = $(".soft-man-con").empty();
                    tabCon.append('<p style="color: #666; margin-bottom: 7px">' + lan.bt.edit_ps + '</p>');
                    tabCon.append('<div class="bt-input-text ace_config_editor_scroll" style="height: 320px;min-height:350px;line-height:18px;" id="textBody"></div>')
                    tabCon.append('<button id="OnlineEditFileBtn" class="btn btn-success btn-sm" style="margin-top:10px;">' + lan.public.save + '</button>')
                    var _arry = ['此处为PHP-FPM配置文件,若您不了解配置规则，请勿修改!'];
                    tabCon.append(bt.render_help(_arry))
                    $('.return_php_info').click(function(){
                        $('.bt-soft-menu p:eq(12)').click();
                    });
                    var fileName = bt.soft.get_config_path(version).replace('php.ini','php-fpm.conf');
                    var loadT = bt.load(lan.soft.get);
                    var config = bt.aceEditor({el:'textBody',path:fileName});
                    $("#OnlineEditFileBtn").click(function () {
                        bt.saveEditor(config);
                    });
                    break;
            case 'change_version':
                var _list = [];
                var opt_version = '';
                for (var i = 0; i < data.versions.length; i++) {
                    if (data.versions[i].setup) opt_version = data.name + ' ' + data.versions[i].m_version;
                    _list.push({ value: data.name + ' ' + data.versions[i].m_version, title: data.name + ' ' + data.versions[i].m_version });
                }
                var _form_data = {
                    title: lan.soft.select_version, items: [
                        { name: 'phpVersion', width: '160px', type: 'select', value: opt_version, items: _list },
                        {
                            name: 'btn_change_version', type: 'button', text: lan.soft.version_to, callback: function (ldata) {
                                if (ldata.phpVersion == opt_version) {
                                    bt.msg({ msg: '当前已经是[' + opt_version + ']', icon: 2 })
                                    return;
                                }
                                if (data.name == 'mysql') {
                                    bt.database.get_list(1, '', function (ddata) {
                                        if (ddata.data.length > 0) {
                                            bt.msg({ msg: lan.soft.mysql_d, icon: 5, time: 5000 })
                                            return;
                                        }
                                        bt.soft.install_soft(data, ldata.phpVersion.split(" ")[1], 0);
                                    })
                                }
                                else {
                                    bt.soft.install_soft(data, ldata.phpVersion.split(" ")[1], 0);
                                }
                            }
                        }
                    ]
                }
                bt.render_form_line(_form_data, '', $(".soft-man-con").empty())
                break;
            case 'change_data_path':
                bt.send('GetMySQLInfo', 'database/GetMySQLInfo', {}, function (rdata) {
                    var form_data = {
                        items: [
                            { type: 'text', name: 'datadir', value: rdata.datadir, event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
                            {
                                name: 'btn_change_path', type: 'button', text: lan.soft.mysql_to, callback: function (ldata) {
                                    var loadT = bt.load(lan.soft.mysql_to_msg1);
                                    bt.send('SetDataDir', 'database/SetDataDir', { datadir: ldata.datadir }, function (rdata) {
                                        loadT.close();
                                        bt.msg(rdata);
                                    });
                                }
                            }
                        ]
                    }
                    bt.render_form_line(form_data, '', $(".soft-man-con").empty());
                });
                break;
            case 'change_mysql_port':
                bt.send('GetMySQLInfo', 'database/GetMySQLInfo', {}, function (rdata) {
                    var form_data = {
                        items: [
                            { type: 'text', width: '100px', name: 'port', value: rdata.port },
                            {
                                name: 'btn_change_port', type: 'button', text: lan.public.edit, callback: function (ldata) {
                                    var loadT = bt.load();
                                    bt.send('SetMySQLPort', 'database/SetMySQLPort', { port: ldata.port }, function (rdata) {
                                        loadT.close();
                                        bt.msg(rdata);
                                    });
                                }
                            }
                        ]
                    }
                    bt.render_form_line(form_data, '', $(".soft-man-con").empty());
                });
                break;
            case 'get_mysql_run_status':
                bt.send('GetRunStatus', 'database/GetRunStatus', {}, function (rdata) {
                    var cache_size = ((parseInt(rdata.Qcache_hits) / (parseInt(rdata.Qcache_hits) + parseInt(rdata.Qcache_inserts))) * 100).toFixed(2) + '%';
                    if (cache_size == 'NaN%') cache_size = 'OFF';
					var title10 = ((1 - rdata.Threads_created / rdata.Connections) * 100).toFixed(2);
					var title11 = ((1 - rdata.Key_reads / rdata.Key_read_requests) * 100).toFixed(2);
					var title12 = ((1 - rdata.Innodb_buffer_pool_reads / rdata.Innodb_buffer_pool_read_requests) * 100).toFixed(2);
					var title14 = ((rdata.Created_tmp_disk_tables / rdata.Created_tmp_tables) * 100).toFixed(2);
                    var Con = '<div class="divtable"><table class="table table-hover table-bordered" style="width: 490px;margin-bottom:10px;background-color:#fafafa">\
								<tbody>\
									<tr><th>'+ lan.soft.mysql_status_title1 + '</th><td>' + getLocalTime(rdata.Run) + '</td><th>' + lan.soft.mysql_status_title5 + '</th><td>' + parseInt(rdata.Questions / rdata.Uptime) + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title2 + '</th><td>' + rdata.Connections + '</td><th>' + lan.soft.mysql_status_title6 + '</th><td>' + parseInt((parseInt(rdata.Com_commit) + parseInt(rdata.Com_rollback)) / rdata.Uptime) + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title3 + '</th><td>' + ToSize(rdata.Bytes_sent) + '</td><th>' + lan.soft.mysql_status_title7 + '</th><td>' + rdata.File + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title4 + '</th><td>' + ToSize(rdata.Bytes_received) + '</td><th>' + lan.soft.mysql_status_title8 + '</th><td>' + rdata.Position + '</td></tr>\
								</tbody>\
								</table>\
								<table class="table table-hover table-bordered" style="width: 490px;">\
								<thead style="display:none;"><th></th><th></th><th></th><th></th></thead>\
								<tbody>\
									<tr><th>'+ lan.soft.mysql_status_title9 + '</th><td>' + rdata.Threads_running + '/' + rdata.Max_used_connections + '</td><td colspan="2">' + lan.soft.mysql_status_ps1 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title10 + '</th><td>' + (!isNaN(title10)?title10:'0') + '%</td><td colspan="2">' + lan.soft.mysql_status_ps2 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title11 + '</th><td>' + (!isNaN(title11)?title11:'0') + '%</td><td colspan="2">' + lan.soft.mysql_status_ps3 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title12 + '</th><td>' + (!isNaN(title12)?title12:'0') + '%</td><td colspan="2">' + lan.soft.mysql_status_ps4 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title13 + '</th><td>' + cache_size + '</td><td colspan="2">' + lan.soft.mysql_status_ps5 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title14 + '</th><td>' + (!isNaN(title14)?title14:'0') + '%</td><td colspan="2">' + lan.soft.mysql_status_ps6 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title15 + '</th><td>' + rdata.Open_tables + '</td><td colspan="2">' + lan.soft.mysql_status_ps7 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title16 + '</th><td>' + rdata.Select_full_join + '</td><td colspan="2">' + lan.soft.mysql_status_ps8 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title17 + '</th><td>' + rdata.Select_range_check + '</td><td colspan="2">' + lan.soft.mysql_status_ps9 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title18 + '</th><td>' + rdata.Sort_merge_passes + '</td><td colspan="2">' + lan.soft.mysql_status_ps10 + '</td></tr>\
									<tr><th>'+ lan.soft.mysql_status_title19 + '</th><td>' + rdata.Table_locks_waited + '</td><td colspan="2">' + lan.soft.mysql_status_ps11 + '</td></tr>\
								<tbody>\
						</table></div>'
                    $(".soft-man-con").html(Con);
                })
                break;
            case 'get_mysql_status':
                bt.send('GetDbStatus', 'database/GetDbStatus', {}, function (rdata) {
                    var key_buffer_size = bt.format_size(rdata.mem.key_buffer_size, false, 0, 'MB')
                    var query_cache_size = bt.format_size(rdata.mem.query_cache_size, false, 0, 'MB')
                    var tmp_table_size = bt.format_size(rdata.mem.tmp_table_size, false, 0, 'MB')
                    var innodb_buffer_pool_size = bt.format_size(rdata.mem.innodb_buffer_pool_size, false, 0, 'MB')
                    var innodb_additional_mem_pool_size = bt.format_size(rdata.mem.innodb_additional_mem_pool_size, false, 0, 'MB')
                    var innodb_log_buffer_size = bt.format_size(rdata.mem.innodb_log_buffer_size, false, 0, 'MB')

                    var sort_buffer_size = bt.format_size(rdata.mem.sort_buffer_size, false, 0, 'MB')
                    var read_buffer_size = bt.format_size(rdata.mem.read_buffer_size, false, 0, 'MB')
                    var read_rnd_buffer_size = bt.format_size(rdata.mem.read_rnd_buffer_size, false, 0, 'MB')
                    var join_buffer_size = bt.format_size(rdata.mem.join_buffer_size, false, 0, 'MB')
                    var thread_stack = bt.format_size(rdata.mem.thread_stack, false, 0, 'MB')
                    var binlog_cache_size = bt.format_size(rdata.mem.binlog_cache_size, false, 0, 'MB')
                    var a = key_buffer_size + query_cache_size + tmp_table_size + innodb_buffer_pool_size + innodb_additional_mem_pool_size + innodb_log_buffer_size
                    var b = sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size + thread_stack + binlog_cache_size
                    var memSize = a + rdata.mem.max_connections * b

                    var mysql_select = {
                        '1': {
                            title: '1-2GB', data: {
                                key_buffer_size: 128,
                                query_cache_size: 64,
                                tmp_table_size: 64,
                                innodb_buffer_pool_size: 256,
                                sort_buffer_size: 768,
                                read_buffer_size: 768,
                                read_rnd_buffer_size: 512,
                                join_buffer_size: 1024,
                                thread_stack: 256,
                                binlog_cache_size: 64,
                                thread_cache_size: 64,
                                table_open_cache: 128,
                                max_connections: 100
                            }
                        },
                        '2': {
                            title: '2-4GB', data: {
                                key_buffer_size: 256,
                                query_cache_size: 128,
                                tmp_table_size: 384,
                                innodb_buffer_pool_size: 384,
                                sort_buffer_size: 768,
                                read_buffer_size: 768,
                                read_rnd_buffer_size: 512,
                                join_buffer_size: 2048,
                                thread_stack: 256,
                                binlog_cache_size: 64,
                                thread_cache_size: 96,
                                table_open_cache: 192,
                                max_connections: 200
                            }
                        },
                        '3': {
                            title: '4-8GB', data: {
                                key_buffer_size: 384,
                                query_cache_size: 192,
                                tmp_table_size: 512,
                                innodb_buffer_pool_size: 512,
                                sort_buffer_size: 1024,
                                read_buffer_size: 1024,
                                read_rnd_buffer_size: 768,
                                join_buffer_size: 2048,
                                thread_stack: 256,
                                binlog_cache_size: 128,
                                thread_cache_size: 128,
                                table_open_cache: 384,
                                max_connections: 300
                            }
                        },
                        '4': {
                            title: '8-16GB', data: {
                                key_buffer_size: 512,
                                query_cache_size: 256,
                                tmp_table_size: 1024,
                                innodb_buffer_pool_size: 1024,
                                sort_buffer_size: 2048,
                                read_buffer_size: 2048,
                                read_rnd_buffer_size: 1024,
                                join_buffer_size: 4096,
                                thread_stack: 384,
                                binlog_cache_size: 192,
                                thread_cache_size: 192,
                                table_open_cache: 1024,
                                max_connections: 400
                            }
                        },
                        '5': {
                            title: '16-32GB', data: {
                                key_buffer_size: 1024,
                                query_cache_size: 384,
                                tmp_table_size: 2048,
                                innodb_buffer_pool_size: 4096,
                                sort_buffer_size: 4096,
                                read_buffer_size: 4096,
                                read_rnd_buffer_size: 2048,
                                join_buffer_size: 8192,
                                thread_stack: 512,
                                binlog_cache_size: 256,
                                thread_cache_size: 256,
                                table_open_cache: 2048,
                                max_connections: 500
                            }
                        }

                    }
                    var mysql_arrs = [{ value: 0, title: lan.soft.mysql_set_select }]
                    for (var key in mysql_select) mysql_arrs.push({ value: key, title: mysql_select[key].title })

                    var form_datas = [
                        {
                            items: [
                                {
                                    title: lan.soft.mysql_set_msg, name: 'mysql_set', type: 'select', items: mysql_arrs, callback: function (item) {
                                        if (item.val() > 0) {
                                            var data = mysql_select[item.val()].data;
                                            for (var key in data) $('.' + key).val(data[key]);
                                            if (!data.query_cache_size) data['query_cache_size'] = 0;
                                            $("input[name='max_connections']").trigger('change')

                                        }
                                    }
                                },
                                { title: lan.soft.mysql_set_maxmem, name: 'memSize', width: '70px', disabled: true, value: memSize.toFixed(2), ps: 'MB' }
                            ]
                        },
                        { title: 'key_buffer_size', type: 'number', name: 'key_buffer_size', width: '70px', value: key_buffer_size, ps: 'MB, <font>' + lan.soft.mysql_set_key_buffer_size + '</font>' },
                        { title: 'query_cache_size', type: 'number', name: 'query_cache_size', width: '70px', value: query_cache_size, ps: 'MB, <font>' + lan.soft.mysql_set_query_cache_size + '</font>' },
                        { title: 'tmp_table_size', type: 'number', name: 'tmp_table_size', width: '70px', value: tmp_table_size, ps: 'MB, <font>' + lan.soft.mysql_set_tmp_table_size + '</font>' },
                        { title: 'innodb_buffer_pool_size', type: 'number', name: 'innodb_buffer_pool_size', value: innodb_buffer_pool_size, width: '70px', ps: 'MB, <font>' + lan.soft.mysql_set_innodb_buffer_pool_size + '</font>' },
                        { title: 'innodb_log_buffer_size', type: 'number', name: 'innodb_log_buffer_size', value: innodb_log_buffer_size, width: '70px', ps: 'MB, <font>' + lan.soft.mysql_set_innodb_log_buffer_size + '</font>' },
                        { title: 'sort_buffer_size', type: 'number', name: 'sort_buffer_size', width: '70px', value: (sort_buffer_size * 1024), ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_sort_buffer_size + '</font>' },
                        { title: 'read_buffer_size', type: 'number', name: 'read_buffer_size', width: '70px', value: (read_buffer_size * 1024), ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_read_buffer_size + '</font>' },
                        { title: 'read_rnd_buffer_size', type: 'number', name: 'read_rnd_buffer_size', width: '70px', value: (read_rnd_buffer_size * 1024), ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_read_rnd_buffer_size + '</font>' },
                        { title: 'join_buffer_size', type: 'number', name: 'join_buffer_size', width: '70px', value: (join_buffer_size * 1024), ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_join_buffer_size + '</font>' },
                        { title: 'thread_stack', type: 'number', name: 'thread_stack', width: '70px', value: (thread_stack * 1024), ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_thread_stack + '</font>' },
                        { title: 'binlog_cache_size', type: 'number', name: 'binlog_cache_size', value: (binlog_cache_size * 1024), width: '70px', ps: 'KB * ' + lan.soft.mysql_set_conn + ', <font>' + lan.soft.mysql_set_binlog_cache_size + '</font>' },
                        { title: 'thread_cache_size', type: 'number', name: 'thread_cache_size', value: rdata.mem.thread_cache_size, width: '70px', ps: lan.soft.mysql_set_thread_cache_size },
                        { title: 'table_open_cache', type: 'number', name: 'table_open_cache', value: rdata.mem.table_open_cache, width: '70px', ps: lan.soft.mysql_set_table_open_cache },
                        { title: 'max_connections', type: 'number', name: 'max_connections', value: rdata.mem.max_connections, width: '70px', ps: lan.soft.mysql_set_max_connections },
                        {
                            items: [
                                {
                                    text: lan.soft.mysql_set_restart, type: 'button', name: 'bt_mysql_restart', callback: function (ldata) {
                                        bt.pub.set_server_status('mysqld', 'restart');
                                    }
                                },
                                {
                                    text: lan.public.save, type: 'button', name: 'bt_mysql_save', callback: function (ldata) {
                                        ldata.query_cache_type = 0;
                                        if (ldata.query_cache_size > 0) ldata.query_cache_type = 1;
                                        ldata['max_heap_table_size'] = ldata.tmp_table_size;
                                        bt.send('SetDbConf', 'database/SetDbConf', ldata, function (rdata) {
                                            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                                        });
                                    }
                                }
                            ]
                        }
                    ]
                    var tabCon = $(".soft-man-con").empty().append("<div class='tab-db-status'></div>");
                    for (var i = 0; i < form_datas.length; i++) {
                        bt.render_form_line(form_datas[i], '', $('.tab-db-status'));
                    }

                    $(".tab-db-status input[name*='size'],.tab-db-status input[name='max_connections'],.tab-db-status input[name='thread_stack']").change(function () {

                        var key_buffer_size = parseInt($("input[name='key_buffer_size']").val());
                        var query_cache_size = parseInt($("input[name='query_cache_size']").val());
                        var tmp_table_size = parseInt($("input[name='tmp_table_size']").val());
                        var innodb_buffer_pool_size = parseInt($("input[name='innodb_buffer_pool_size']").val());
                        var innodb_log_buffer_size = parseInt($("input[name='innodb_log_buffer_size']").val());

                        var sort_buffer_size = $("input[name='sort_buffer_size']").val() / 1024;
                        var read_buffer_size = $("input[name='read_buffer_size']").val() / 1024;
                        var read_rnd_buffer_size = $("input[name='read_rnd_buffer_size']").val() / 1024;
                        var join_buffer_size = $("input[name='join_buffer_size']").val() / 1024;
                        var thread_stack = $("input[name='thread_stack']").val() / 1024;
                        var binlog_cache_size = $("input[name='binlog_cache_size']").val() / 1024;
                        var max_connections = $("input[name='max_connections']").val();

                        var a = key_buffer_size + query_cache_size + tmp_table_size + innodb_buffer_pool_size + innodb_additional_mem_pool_size + innodb_log_buffer_size
                        var b = sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size + thread_stack + binlog_cache_size
                        var memSize = a + max_connections * b
                        $("input[name='memSize']").val(memSize.toFixed(2));
                    });
                })
                break;
            case 'mysql_log':
                var loadT = bt.load();
                bt.send('BinLog', 'database/BinLog', { status: 1 }, function (rdata) {
                    loadT.close();
                    var limitCon = '<p class="conf_p">\
										<span class="f14 c6 mr20">'+ lan.soft.mysql_log_bin + ' </span><span class="f14 c6 mr20">' + ToSize(rdata.msg) + '</span>\
										<button class="btn btn-success btn-xs btn-bin va0">'+ (rdata.status ? lan.soft.off : lan.soft.on) + '</button>\
										<p class="f14 c6 mtb10" style="border-top:#ddd 1px solid; padding:10px 0">'+ lan.soft.mysql_log_err + '<button class="btn btn-default btn-clear btn-xs" style="float:right;" >' + lan.soft.mysql_log_close + '</button></p>\
										<textarea readonly style="margin: 0px;width: 515px;height: 440px;background-color: #333;color:#fff; padding:0 5px" id="error_log"></textarea>\
									</p>'
                    $(".soft-man-con").html(limitCon);

                    //设置二进制日志
                    $(".btn-bin").click(function () {
                        var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: 0.3 });
                        $.post('/database?action=BinLog', "", function (rdata) {
                            layer.close(loadT);
                            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                            soft.get_tab_contents('mysql_log')
                        });
                    })

                    //清空日志
                    $(".btn-clear").click(function () {
                        var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: 0.3 });
                        $.post('/database?action=GetErrorLog', "close=1", function (rdata) {
                            layer.close(loadT);
                            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                            soft.get_tab_contents('mysql_log')
                        });
                    })
                    bt.send('GetErrorLog', 'database/GetErrorLog', {}, function (error_body) {
                        if (error_body.status === false) {
                            layer.msg(error_body.msg, { icon: 5 });
                            error_body = lan.soft.mysql_log_ps1;
                        }
                        if (error_body == "") error_body = lan.soft.mysql_log_ps1;
                        $("#error_log").text(error_body);
                        var ob = document.getElementById('error_log');
                        ob.scrollTop = ob.scrollHeight;
                    });
                })
                break;
            case 'mysql_slow_log':
                var loadT = bt.load();
                bt.send('GetSlowLogs', 'database/GetSlowLogs', {}, function (logs) {
                    loadT.close();
                    if (!logs.status) {
                        logs.msg = '';
                    }
                    if (logs.msg == '') logs.msg = '当前没有慢日志.';
                    var phpCon = '<textarea readonly="" style="margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + logs.msg + '</textarea>';
                    $(".soft-man-con").html(phpCon);
                    var ob = document.getElementById('error_log');
                    ob.scrollTop = ob.scrollHeight;
                })
                break;
            case 'log':
                var loadT = bt.load(lan.public.the_get);
                bt.send('GetOpeLogs', 'ajax/GetOpeLogs', { path: '/www/wwwlogs/nginx_error.log' }, function (rdata) {
                    loadT.close();
                    if (rdata.msg == '') rdata.msg = '当前没有日志!';
                    var ebody = '<div class="soft-man-con"><textarea readonly="" style="margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + rdata.msg + '</textarea></div>';
                    $(".soft-man-con").html(ebody);
                    var ob = document.getElementById('error_log');
                    ob.scrollTop = ob.scrollHeight;
                })
                break;
            case 'nginx_status':
                var loadT = bt.load();
                bt.send('GetNginxStatus', 'ajax/GetNginxStatus', {}, function (rdata) {
                    loadT.close();
                    $(".soft-man-con").html("<div><table id='tab-nginx-status' class='table table-hover table-bordered'> </table></div>");
                    var arrs = []
                    arrs[lan.bt.nginx_active] = rdata.active;
                    arrs[lan.bt.nginx_accepts] = rdata.accepts;
                    arrs[lan.bt.nginx_handled] = rdata.handled;
                    arrs[lan.bt.nginx_requests] = rdata.requests;
                    arrs[lan.bt.nginx_reading] = rdata.Reading;
                    arrs[lan.bt.nginx_writing] = rdata.Writing;
                    arrs[lan.bt.nginx_waiting] = rdata.Waiting;
                    arrs[lan.bt.nginx_worker] = rdata.worker;
                    arrs[lan.bt.nginx_workercpu] = rdata.workercpu;
                    arrs[lan.bt.nginx_workermen] = rdata.workermen;
                    bt.render_table("tab-nginx-status", arrs);
                })
            break;
            case 'apache_status':
                var loadT = bt.load();
                bt.send('GetApacheStatus', 'ajax/GetApacheStatus', {}, function (rdata) {
                    loadT.close();
                    $(".soft-man-con").html("<div><table id='tab-Apache-status' class='table table-hover table-bordered'> </table></div>");
                    var arrs = []
                    arrs[lan.bt.apache_uptime] = rdata.UpTime;
                    arrs[lan.bt.apache_idleworkers] = rdata.IdleWorkers;
                    arrs[lan.bt.apache_totalaccesses] = rdata.TotalAccesses;
                    arrs[lan.bt.apache_totalkbytes] = rdata.TotalKBytes;
                    arrs[lan.bt.apache_workermem] = rdata.workermem;
                    arrs[lan.bt.apache_workercpu] = rdata.workercpu;
                    arrs[lan.bt.apache_reqpersec] = rdata.ReqPerSec;
                    arrs[lan.bt.apache_restarttime] = rdata.RestartTime;
                    arrs[lan.bt.apache_busyworkers] = rdata.BusyWorkers;
                    bt.render_table("tab-Apache-status", arrs);
                })
            break;
            case 'nginx_set':
                var loadT = bt.load();
                bt.send('GetNginxValue', 'config/GetNginxValue', {}, function (rdata) {
                    loadT.close();
                    var form_datas = []
                    for(var i = 0; i < rdata.length; i++){
                        if(rdata[i].name == 'worker_processes'){
                            form_datas.push({title: rdata[i].name, name: rdata[i].name,width: '60px',value: rdata[i].value,ps: rdata[i].ps,text:''})
                        }else if(rdata[i].name == 'gzip'){
                            form_datas.push({title: rdata[i].name,type: 'select',items:[{title:'开启',value:'on'},{title:'关闭',value:'off'}],name: rdata[i].name,width: '60px',value: rdata[i].value,ps: rdata[i].ps,text:''})
                        }else{
                            form_datas.push({title: rdata[i].name,type: 'number', name: rdata[i].name,width: '60px',value: rdata[i].value,ps: rdata[i].ps,text:''})
                        }
                            
                    }
                    form_datas.push({
                        items: [{
                            text: lan.public.save, type: 'button', name: 'bt_nginx_save', callback: function (item) {
                                    delete item['bt_nginx_save']
                                    bt.send('SetNginxValue','config/SetNginxValue',item, function (rdata) {
                                        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                                    });
                                }
                            }
                        ]
                    })
                    $(".soft-man-con").empty().append('<div class="set_nginx_config"></div>');
                    for (var i = 0; i < form_datas.length; i++) {
                        bt.render_form_line(form_datas[i], '', $(".soft-man-con .set_nginx_config"));
                    }
                });
            break;
            case 'apache_set':
                var loadT = bt.load();
                bt.send('GetNginxValue', 'config/GetApacheValue', {}, function (rdata) {
                    loadT.close();
                    var form_datas = []
                    for(var i = 0; i < rdata.length; i++){
                        if(rdata[i].name == 'KeepAlive'){
                            form_datas.push({title: rdata[i].name,type: 'select',items:[{title:'开启',value:'on'},{title:'关闭',value:'off'}],name: rdata[i].name,width: '60px',value: rdata[i].value,ps: rdata[i].ps,text:''})
                        }else{
                            form_datas.push({title: rdata[i].name,type: 'number', name: rdata[i].name,width: '60px',value: rdata[i].value,ps: rdata[i].ps,text:''})
                        }
                            
                    }
                    form_datas.push({
                        items: [{
                            text: lan.public.save, type: 'button', name: 'bt_apache_save', callback: function (item) {
                                    delete item['bt_apache_save'];
                                    bt.send('SetApacheValue','config/SetApacheValue',item, function (rdata) {
                                        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                                    });
                                }
                            }
                        ]
                    })
                    $(".soft-man-con").empty().append('<div class="set_Apache_config"></div>');
                    for (var i = 0; i < form_datas.length; i++) {
                        bt.render_form_line(form_datas[i], '', $(".soft-man-con .set_Apache_config"));
                    }
                });
            break;
            case 'memcached_status':
            case 'memcached_set':
                var loadT = bt.load(lan.public.get_the);
                bt.send('GetMemcachedStatus', 'ajax/GetMemcachedStatus', {}, function (rdata) {
                    loadT.close();
                    if (key == 'memcached_set') {
                        var form_data = [
                            { title: 'BindIP', name: 'ip', width: '120px', value: rdata.bind, ps: '监听IP,请勿随意修改' },
                            { title: 'PORT', name: 'port', type: 'number', width: '120px', value: rdata.port, ps: '监听端口,一般无需修改' },
                            { title: 'CACHESIZE', name: 'cachesize', type: 'number', width: '120px', value: rdata.cachesize, ps: 'MB,<font>缓存大小,建议不要大于512M</font>' },
                            { title: 'MAXCONN', name: 'maxconn', type: 'number', width: '120px', value: rdata.maxconn, ps: '最大连接数,建议不要大于40960' },
                            {
                                title: ' ', items: [{
                                    text: lan.public.save, name: 'btn_set_memcached', type: 'button', callback: function (ldata) {
                                        if (ldata.ip.split('.').length < 4) {
                                            layer.msg('IP地址格式不正确!', { icon: 2 });
                                            return;
                                        }
                                        if (ldata.port < 1 || ldata.port > 65535) {
                                            layer.msg('端口范围不正确!', { icon: 2 });
                                            return;
                                        }
                                        if (ldata.cachesize < 8) {
                                            layer.msg('缓存值过小', { icon: 2 });
                                            return;
                                        }
                                        if (ldata.maxconn < 4) {
                                            layer.msg('最大连接数过小', { icon: 2 });
                                            return;
                                        }
                                        var loadT = bt.load(lan.public.the);
                                        bt.send('SetMemcachedCache', 'ajax/SetMemcachedCache', ldata, function (rdata) {
                                            loadT.close();
                                            bt.msg(rdata)
                                        });
                                    }
                                }]
                            }
                        ]
                        var tabCon = $(".soft-man-con").empty();
                        for (var i = 0; i < form_data.length; i++) {
                            bt.render_form_line(form_data[i], '', tabCon);
                        }
                        return;
                    }
                    else {
                        var arr = {};
                        arr['BindIP'] = [rdata.bind, '监听IP'];
                        arr['PORT'] = [rdata.port, '监听端口'];
                        arr['CACHESIZE'] = [rdata.cachesize + ' MB', '最大缓存容量'];
                        arr['MAXCONN'] = [rdata.maxconn, '最大连接数限制'];
                        arr['curr_connections'] = [rdata.curr_connections, '当前打开的连接数'];
                        arr['cmd_get'] = [rdata.cmd_get, 'GET请求数'];
                        arr['get_hits'] = [rdata.get_hits, 'GET命中次数'];
                        arr['get_misses'] = [rdata.get_misses, 'GET失败次数'];
                        arr['hit'] = [rdata.hit.toFixed(2) + ' %', 'GET命中率'];
                        arr['curr_items'] = [rdata.curr_items, '当前被缓存的数据行数'];
                        arr['evictions'] = [rdata.evictions, '因内存不足而被清理的缓存行数'];
                        arr['bytes'] = [ToSize(rdata.bytes), '当前已使用内存'];
                        arr['bytes_read'] = [ToSize(rdata.bytes_read), '请求总大小'];
                        arr['bytes_written'] = [ToSize(rdata.bytes_written), '发送总大小'];

                        var con = "<div class=\"divtable\"><table id='tab_memcached_status' style=\"width: 490px;\" class='table table-hover table-bordered '><thead><th>字段</th><th>当前值</th><th>说明</th></thead></table></div>";
                        $(".soft-man-con").html(con);
                        bt.render_table('tab_memcached_status', arr, true);
                    }
                })
                break;
            case 'phpmyadmin_php':
                bt.send('GetPHPVersion', 'site/GetPHPVersion', {}, function (rdata) {
                    var sdata = $('.bt-soft-menu').data('data');

                    var body = "<div class='ver line'><span class='tname'>" + lan.soft.php_version + "</span><select id='get_phpVersion' class='bt-input-text mr20' name='phpVersion' style='width:110px'>";
                    for (var i = 0; i < rdata.length; i++) {
                        optionSelect = rdata[i].version == sdata.ext.phpversion ? 'selected' : '';
                        body += "<option value='" + rdata[i].version + "' " + optionSelect + ">" + rdata[i].name + "</option>"
                    }
                    body += '</select><button class="btn btn-success btn-sm" >' + lan.public.save + '</button></div>';
                    $(".soft-man-con").html(body);
                    $('.btn-success').click(function () {
                        var loadT = bt.load(lan.public.the);
                        bt.send('setPHPMyAdmin', 'ajax/setPHPMyAdmin', { phpversion: $("#get_phpVersion").val() }, function (rdata) {
                            loadT.close();
                            bt.msg(rdata);
                            if (rdata.status) {
                                setTimeout(function () {
                                    window.location.reload();
                                }, 3000);
                            }
                        })
                    })
                })
                break;
            case 'phpmyadmin_safe':
                var sdata = $('.bt-soft-menu').data('data'),sslPortNum ='';
                var con = '<div class="ver line user_set_info">\
                                    <span class="tit">'+ lan.soft.pma_port + '</span>\
                                    <input class="bt-input-text phpmyadmindk mr20" name="Name" id="pmport" value="'+ sdata.ext.port + '" placeholder="' + lan.soft.pma_port_title + '" maxlength="5" type="number">\
                                    <button class="btn btn-success btn-sm phpmyadmin_port" >'+ lan.public.save + '</button>\
                                </div>\
                                <div class="ver line user_set_info" style="margin-top: 30px;padding-top: 30px;border-top: #ccc 1px dashed;">\
                                	<span class="tit">开启SSL</span>\
                                    <span class="btswitch-p"><input class="btswitch btswitch-ios" id="ssl_safe_checkbox" type="checkbox">\
                                    <label class="btswitch-btn phpmyadmin-btn ssl_safe_label" for="ssl_safe_checkbox" style="margin:0px" ></label>\
                                    </span>\
                                </div>\
                                <div class="ver line user_set_info">\
                                	<span class="tit">SSL端口</span>\
                                	<input class="bt-input-text ssl_port_input mr20" name="Name" id="sslport" value="" maxlength="5" type="number">\
                                    <button class="btn btn-success btn-sm ssl_port_button" >保存</button>\
                                </div>\
                                <div class="user_pw_tit">\
                                    <span class="tit">'+ lan.soft.pma_pass + '</span>\
                                    <span class="btswitch-p"><input class="btswitch btswitch-ios" id="phpmyadminsafe" type="checkbox" '+ (sdata.ext.auth ? 'checked' : '') + '>\
                                    <label class="btswitch-btn phpmyadmin-btn phpmyadmin_safe" for="phpmyadminsafe" ></label>\
                                    </span>\
                                </div>\
                                <div class="user_pw">\
                                    <p><span>'+ lan.soft.pma_user + '</span><input id="username_get" class="bt-input-text" name="username_get" value="" type="text" placeholder="' + lan.soft.edit_empty + '"></p>\
                                    <p><span>'+ lan.soft.pma_pass1 + '</span><input id="password_get_1" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="' + lan.soft.edit_empty + '"></p>\
                                    <p><span>'+ lan.soft.pma_pass2 + '</span><input id="password_get_2" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="' + lan.soft.edit_empty + '"></p>\
                                    <p><button class="btn btn-success btn-sm phpmyadmin_safe_save" >'+ lan.public.save + '</button></p>\
                                </div>\
                                <ul class="help-info-text c7"><li>'+ lan.soft.pma_ps + '</li></ul>';
				
                $(".soft-man-con").html(con);
                if (sdata.ext.port) {
                    $(".user_pw").show();
                }
                
            	function get_phpmyadmin_ssl(){
            		var loading = bt.load('正在获取SSL状态，请稍后...');
					bt.send('get_phpmyadmin_ssl','ajax/get_phpmyadmin_ssl',{},function(tdata){
						loading.close();
						$('#ssl_safe_checkbox').prop("checked",tdata.status);
						$('#sslport').val(tdata.port)
					})
				}
				get_phpmyadmin_ssl()
                $('.phpmyadmin_port').click(function () {
                    var pmport = $("#pmport").val();
                    var loadT = bt.load(lan.public.the);
                    bt.send('setPHPMyAdmin', 'ajax/setPHPMyAdmin', { port: pmport }, function (rdata) {
                        loadT.close();
                        bt.msg(rdata);
                    })
                })
                $('.ssl_safe_label').click(function (){
                	var stat = $('#ssl_safe_checkbox').prop("checked");
                	bt.send('set_phpmyadmin_ssl','ajax/set_phpmyadmin_ssl',{v: !stat? 1:0},function(rdata){
                		bt.msg(rdata)
                	})
                	setTimeout(function () {
                        get_phpmyadmin_ssl();
                    }, 500)
                	
                })
                $('.ssl_port_button').click(function (){
                	var sslPort = $('#sslport').val();
                	if (!bt.check_port(sslPort)) {
                        layer.msg(lan.firewall.port_err, { icon: 2 });
                        return;
                    }
                    var loadTo = bt.load(lan.public.the);
                	if(sslPort > 0){
                		bt.send('change_phpmyadmin_ssl_port','ajax/change_phpmyadmin_ssl_port',{port: sslPort},function(rdata) {
                			loadTo.close();
                        	bt.msg(rdata);
                		})
                	}
                })
                $('.phpmyadmin_safe').click(function () {
                    var stat = $("#phpmyadminsafe").prop("checked");
                    if (stat) {
                        $(".user_pw").hide();
                        set_phpmyadmin('close');
                    } else {
                        $(".user_pw").show();
                    }
                })
                $('.phpmyadmin_safe_save').click(function () {
                    set_phpmyadmin('get');
                })

                function set_phpmyadmin(msg) {
                    var type = 'password';
                    if (msg == 'close') {
                        bt.confirm({ msg: lan.soft.pma_pass_close }, function () {
                            var loading = bt.load(lan.public.the);
                            bt.send('setPHPMyAdmin', 'ajax/setPHPMyAdmin', { password: msg, siteName: 'phpmyadmin' }, function (rdata) {
                                loading.close();
                                bt.msg(rdata);
                            })
                        })
                        return;
                    } else {
                        username = $("#username_get").val()
                        password_1 = $("#password_get_1").val()
                        password_2 = $("#password_get_2").val()
                        if (username.length < 1 || password_1.length < 1) {
                            bt.msg({ msg: lan.soft.pma_pass_empty, icon: 2 })
                            return;
                        }
                        if (password_1 != password_2) {
                            bt.msg({ msg: lan.soft.pass_err_re, icon: 2 })
                            return;
                        }
                    }
                    var loading = bt.load(lan.public.the);
                    bt.send('setPHPMyAdmin', 'ajax/setPHPMyAdmin', { password: password_1, username: username, siteName: 'phpmyadmin' }, function (rdata) {
                        loading.close();
                        bt.msg(rdata);
                    })
                }
                break;
            case 'set_php_config':

                bt.soft.php.get_config(version, function (rdata) {
                    var divObj = document.getElementById('phpextdiv');
                    var scrollTopNum = 0;
                    if (divObj) scrollTopNum = divObj.scrollTop;

                    $(".soft-man-con").empty().append('<div class="divtable" id="phpextdiv" style="margin-right:10px;height: 420px; overflow: auto; margin-right: 0px;"><table id="tab_phpext" class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0"></div></div>');
                    
                    var list = [];
                    for (var i = 0; i < rdata.libs.length; i++) {
                        if (rdata.libs[i].versions.indexOf(version) == -1) continue;
                        list.push(rdata.libs[i]);
                    }
                    var _tab = bt.render({
                        table: '#tab_phpext',
                        data: list,
                        columns: [
                            { field: 'name', title: lan.soft.php_ext_name },
                            { field: 'type', title: lan.soft.php_ext_type, width: 64 },
                            { field: 'msg', title: lan.soft.php_ext_ps },
                            {
                                field: 'status', title: lan.soft.php_ext_status, width: 40, templet: function (item) {
                                    return '<span class="ico-' + (item.status ? 'start' : 'stop') + ' glyphicon glyphicon-' + (item.status ? 'ok' : 'remove') + '"></span>'
                                }
                            },
                            {
                                field: 'opt', title: lan.public.action, width: 50, templet: function (item) {
                                    var opt = '<a class="btlink lib-install" data-name="' + item.name + '" data-title="' + item.title + '"  href="javascript:;">' + lan.soft.install + '</a>'
                                    if (item['task'] == '-1' && item.phpversions.indexOf(version) != -1) {
                                        opt = '<a style="color:green;" href="javascript:messagebox();">' + lan.soft.the_install + '</a>'
                                    } else if (item['task'] == '0' && item.phpversions.indexOf(version) != -1) {
                                        opt = '<a style="color:#C0C0C0;" href="javascript:messagebox();">' + lan.soft.sleep_install + '</a>'
                                    } else if (item.status) {
                                        opt = '<a style="color:red;" data-name="' + item.name + '" data-title="' + item.title + '" class="lib-uninstall" href="javascript:;">' + lan.soft.uninstall + '</a>'
                                    }
                                    return opt;
                                }
                            },
                        ]
                    })
                    var helps = ['Redis扩展仅支持一个PHP版本安装使用，若在其它PHP版本已安装redis扩展，请勿再装', '请按实际需求安装扩展,不要安装不必要的PHP扩展,这会影响PHP执行效率,甚至出现异常', 'opcache/xcache/apc等脚本缓存扩展,请只安装其中1个,否则可能导致您的站点程序异常']
                    $(".soft-man-con").append(bt.render_help(helps));
                    
                    var divObj = document.getElementById('phpextdiv');
                    if (divObj) divObj.scrollTop = scrollTopNum;
                    $('a').click(function () {
                        var _obj = $(this);
                        if (_obj.hasClass('lib-uninstall')) {
                            bt.soft.php.un_install_php_lib(version, _obj.attr('data-name'), _obj.attr('data-title'), function (rdata) {
                                setTimeout(function () {
                                    soft.get_tab_contents('set_php_config', obj);
                                }, 1000)
                            });
                        }
                        else if (_obj.hasClass('lib-install')) {
                            bt.soft.php.install_php_lib(version, _obj.attr('data-name'), _obj.attr('data-title'), function (rdata) {
                                setTimeout(function () {
                                    soft.get_tab_contents('set_php_config', obj);
                                }, 1000)
                            });
                        }
                    })
                    setTimeout(function () {
                        if ($(".bt-soft-menu .bgw").text() === "安装扩展") {
                            soft.get_tab_contents('set_php_config', obj);
                        }
                    }, 3000)
                })
                break;
            case 'get_phpinfo':
                var con = '';
                var p_status = { true: '<span style="color:green;">Yes</span>', false:'<span style="color:red;">No</span>'};
                $.post('/ajax?action=php_info', { php_version: version }, function (php_info) {
                    con += '<button id="btn_phpinfo" class="btn btn-default btn-sm" >' + lan.soft.phpinfo + '</button>'
                    con += '<div class="php_info_group"><p>基本信息 </p>'
                    con += '<table id="tab_php_status" class="table table-hover table-bordered" style="margin:0;padding:0">';
                    con += '<tr><td style="width:70px">PHP版本</td><td>' + php_info.phpinfo.php_version + '</td><td>安装位置</td><td>' + php_info.phpinfo.php_path + '</td></tr>'
                    con += '<tr><td>php.ini</td><td colspan="3">' + php_info.phpinfo.php_ini + '</td></tr>'
                    con += '<tr><td>已加载</td><td colspan="3">' + php_info.phpinfo.modules + '</td></tr>'
                    con += '</table></div>';
                    Object.keys(php_info).sort().forEach(function (k) {
                        if (k !== 'phpinfo') {
                            con += '<div class="php_info_group"><p>' + php_info.phpinfo.keys[k] + '</p>'
                            con += '<table id="tab_php_status" class="table table-hover table-bordered" style="margin:0;padding:0">';
                            var nkey = 0;
                            Object.keys(php_info[k]).forEach(function (key) {
                                if (nkey == 0) con += '<tr>';
                                con += '<td>' + key + '</td><td>' + p_status[php_info[k][key]] + '</td>'
                                nkey++;
                                if (nkey >= 3) {
                                    nkey = 0;
                                    con += '</tr>';
                                }
                            });

                            con += '</table></div>';
                        }
                    })



                    $(".soft-man-con").html(con);

                    $('#btn_phpinfo').click(function () {
                        var loadT = bt.load(lan.soft.get);
                        bt.send('GetPHPInfo', 'ajax/GetPHPInfo', { version: version }, function (rdata) {
                            loadT.close();
                            bt.open({
                                type: 1,
                                title: "PHP-" + version + "-PHPINFO",
                                area: ['70%', '90%'],
                                closeBtn: 2,
                                shadeClose: true,
                                content: rdata.replace('a:link {color: #009; text-decoration: none; background-color: #fff;}', '').replace('a:link {color: #000099; text-decoration: none; background-color: #ffffff;}', '')
                            })
                        })
                    })
                });

                
                break;
            case 'config_edit':
                bt.soft.php.get_php_config(version, function (rdata) {
                    var mlist = '';
                    for (var i = 0; i < rdata.length; i++) {
                        var w = '70'
                        if (rdata[i].name == 'error_reporting') w = '250';
                        var ibody = '<input style="width: ' + w + 'px;" class="bt-input-text mr5" name="' + rdata[i].name + '" value="' + rdata[i].value + '" type="text" >';
                        switch (rdata[i].type) {
                            case 0:
                                var selected_1 = (rdata[i].value == 1) ? 'selected' : '';
                                var selected_0 = (rdata[i].value == 0) ? 'selected' : '';
                                ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;"><option value="1" ' + selected_1 + '>开启</option><option value="0" ' + selected_0 + '>关闭</option></select>'
                                break;
                            case 1:
                                var selected_1 = (rdata[i].value == 'On') ? 'selected' : '';
                                var selected_0 = (rdata[i].value == 'Off') ? 'selected' : '';
                                ibody = '<select class="bt-input-text mr5" name="' + rdata[i].name + '" style="width: ' + w + 'px;"><option value="On" ' + selected_1 + '>开启</option><option value="Off" ' + selected_0 + '>关闭</option></select>'
                                break;
                        }
                        mlist += '<p><span>' + rdata[i].name + '</span>' + ibody + ', <font>' + rdata[i].ps + '</font></p>'
                    }
                    var tabCon = $(".soft-man-con").empty()
                    tabCon.append('<div class="conf_p">' + mlist + '</div></div>')
                    var datas = {
                        title: ' ',
                        items: [{
                            name: 'btn_fresh', text: lan.public.fresh, type: 'button', callback: function (ldata) {
                                soft.get_tab_contents(key, obj);
                            }
                        },
                        {
                            name: 'btn_save', text: lan.public.save, type: 'button', callback: function (ldata) {
                                var loadT = bt.load();
                                ldata['version'] = version;
                                bt.send('SetPHPConf', 'config/SetPHPConf', ldata, function (rdata) {
                                    loadT.close();
                                    soft.get_tab_contents(key, obj);
                                    bt.msg(rdata)
                                });
                            }
                        }]
                    }
                    var _form_data = bt.render_form_line(datas);
                    $('.conf_p').append(_form_data.html)
                    bt.render_clicks(_form_data.clicks);
                });
                break;
            case 'set_upload_limit':
                bt.soft.php.get_limit_config(version, function (ret) {
                    var datas = [
                        {
                            items: [
                                { title: '', type: 'number', width: '100px', value: ret.max, unit: 'MB', name: 'phpUploadLimit' },
                                {
                                    name: 'btn_limit_get', text: lan.public.save, type: 'button', callback: function (ldata) {
                                        var max = ldata.phpUploadLimit;
                                        if (max < 2) {
                                            layer.msg(lan.soft.php_upload_size, { icon: 2 });
                                            return;
                                        }
                                        bt.soft.php.set_upload_max(version, max, function (rdata) {
                                            if (rdata.status) {
                                                soft.get_tab_contents(key, obj);
                                            }
                                            bt.msg(rdata);
                                        })
                                    }
                                }
                            ]
                        }
                    ]
                    var clicks = [];
                    var tabCon = $(".soft-man-con").empty().append("<div class='set_upload_limit'></div>")
                    for (var i = 0; i < datas.length; i++) {
                        var _form_data = bt.render_form_line(datas[i]);
                        $('.set_upload_limit').append(_form_data.html);
                        clicks = clicks.concat(_form_data.clicks);
                    }
                    bt.render_clicks(clicks);
                })
                break;
            case 'set_timeout_limit':
                bt.soft.php.get_limit_config(version, function (ret) {
                    var datas = [
                        {
                            items: [
                                { title: '', type: 'number', width: '100px', value: ret.maxTime, name: 'phpTimeLimit', unit: '秒' },
                                {
                                    name: 'btn_limit_get', text: lan.public.save, type: 'button', callback: function (ldata) {
                                        var max = ldata.phpTimeLimit;
                                        bt.soft.php.set_php_timeout(version, max, function (rdata) {
                                            if (rdata.status) {
                                                soft.get_tab_contents(key, obj);
                                            }
                                            bt.msg(rdata);
                                        })
                                    }
                                }]
                        }
                    ]
                    var clicks = [];
                    var tabCon = $(".soft-man-con").empty().append("<div class='set_timeout_limit bt-form'></div>")
                    for (var i = 0; i < datas.length; i++) {
                        var _form_data = bt.render_form_line(datas[i]);
                        $('.set_timeout_limit').append(_form_data.html);
                        clicks = clicks.concat(_form_data.clicks);
                    }
                    bt.render_clicks(clicks);
                })
                break;
            case 'set_dis_fun':
                bt.soft.php.get_config(version, function (rdata) {
                    var list = [];
                    var disable_functions = rdata.disable_functions.split(',');
                    for (var i = 0; i < disable_functions.length; i++) {
                        if (disable_functions[i] == '') continue;
                        list.push({ name: disable_functions[i] })
                    }
                    var _bt_form = $("<div class='bt-form' style='height:400px;'></div>")
                    var tabCon = $(".soft-man-con").empty().append(_bt_form);
                    var _line = bt.render_form_line({
                        title: '', items: [
                            { name: 'disable_function_val', placeholder: lan.soft.fun_ps1, width: '410px' },
                            {
                                name: 'btn_disable_function_val', text: lan.public.save, type: 'button', callback: function (ldata) {
                                    var disable_functions = rdata.disable_functions.split(',')
                                    if ($.inArray(ldata.disable_function_val, disable_functions) >= 0) {
                                        bt.msg({ msg: lan.soft.fun_msg, icon: 5 });
                                        return;
                                    }
                                    disable_functions.push(ldata.disable_function_val);
                                    set_disable_functions(version, disable_functions.join(','))
                                }
                            }
                        ]
                    }, '', _bt_form)

                    bt.render_clicks(_line.clicks);
                    _bt_form.append("<div class='divtable mtb15' style='height:350px;overflow:auto'><table id=\"blacktable\" class='table table-hover' width='100%' style='margin-bottom:0'></table><div>")
                    var _tab = bt.render({
                        table: '#blacktable',
                        data: list,
                        columns: [
                            { field: 'name', title: lan.soft.php_ext_name },
                            {
                                field: 'opt', title: lan.public.action, width: 50, templet: function (item) {
                                    var new_disable_functions = disable_functions.slice()
                                    new_disable_functions.splice($.inArray(item.name, new_disable_functions), 1)
                                    return '<a class="del_functions" style="float:right;" data-val="shell_exec" onclick="set_disable_functions(\'' + version + '\',\'' + new_disable_functions.join(',') + '\')" href="javascript:;">删除</a>';
                                }
                            }
                        ]
                    })
                    tabCon.append(bt.render_help([lan.soft.fun_ps2, lan.soft.fun_ps3]));

                    
                })
                break;
            case 'set_fpm_config':
                bt.soft.php.get_fpm_config(version, function (rdata) {
                    var datas = {
                        '1GB内存': {
                            max_children: 30,
                            start_servers: 5,
                            min_spare_servers: 5,
                            max_spare_servers: 20
                        },
                        '2GB内存': {
                            max_children: 50,
                            start_servers: 5,
                            min_spare_servers: 5,
                            max_spare_servers: 30
                        },
                        '4GB内存': {
                            max_children: 80,
                            start_servers: 10,
                            min_spare_servers: 10,
                            max_spare_servers: 30
                        },
                        '8GB内存': {
                            max_children: 120,
                            start_servers: 10,
                            min_spare_servers: 10,
                            max_spare_servers: 30
                        },
                        '16GB内存': {
                            max_children: 200,
                            start_servers: 15,
                            min_spare_servers: 15,
                            max_spare_servers: 50
                        },
                        '32GB内存': {
                            max_children: 300,
                            start_servers: 20,
                            min_spare_servers: 20,
                            max_spare_servers: 50
                        }
                    }
                    var limits = [], pmList = [];
                    var my_selected = '';
                    var num_max = Number(rdata.max_children);
                    for (var k in datas) {
                        if(datas[k].max_children === num_max){
                            my_selected = k;
                        }
                        limits.push({ title: k, value: k });
                    }
                    var _form_datas = [
                        {
                            title: lan.soft.concurrency_type, name: 'limit', value: my_selected, type: 'select', items: limits, callback: function (iKey) {
                                var item = datas[iKey.val()]
                                for (var sk in item) $('.' + sk).val(item[sk]);
                            }
                        },
                        {
                            title: '连接方式', name: 'listen', value: rdata.unix, type: 'select', items: [
                                { title: 'Unix套接字', value: 'unix' },
                                { title: 'TCP套接字', value: 'tcp' }
                            ], ps: '* 推荐Unix套接字' 
                        },
                        {
                            title: lan.soft.php_fpm_model, name: 'pm', value: rdata.pm, type: 'select', items: [
                                { title: lan.bt.static, value: 'static' },
                                { title: lan.bt.dynamic, value: 'dynamic' },
                                { title:'按需', value: 'ondemand' },
                            ], ps: '*' + lan.soft.php_fpm_ps1
                        },
                        { title: 'max_children', name: 'max_children', value: rdata.max_children, type: 'number', width: '80px', ps: '*' + lan.soft.php_fpm_ps2 },
                        { title: 'start_servers', name: 'start_servers', value: rdata.start_servers, type: 'number', width: '80px', ps: '*' + lan.soft.php_fpm_ps3 },
                        { title: 'min_spare_servers', name: 'min_spare_servers', value: rdata.min_spare_servers, type: 'number', width: '80px', ps: '*' + lan.soft.php_fpm_ps4 },
                        { title: 'max_spare_servers', name: 'max_spare_servers', value: rdata.max_spare_servers, type: 'number', width: '80px', ps: '*' + lan.soft.php_fpm_ps5 },
                        {
                            title: ' ', text: lan.public.save, name: 'btn_children_submit', css: 'btn-success', type: 'button', callback: function (ldata) {
                                bt.pub.get_menm(function (memInfo) {
                                    var limit_children = parseInt(memInfo['memTotal'] / 8);
                                    if (limit_children < parseInt(ldata.max_children)) {
                                        layer.msg('当前服务器内存不足，最大允许[' + limit_children + ']个子进程!', { icon: 2 });
                                        $("input[name='max_children']").focus();
                                        return;
                                    }
                                    if (parseInt(ldata.max_children) < parseInt(ldata.max_spare_servers)) {
                                        layer.msg(lan.soft.php_fpm_err1, { icon: 2 });
                                        return;
                                    }
                                    if (parseInt(ldata.min_spare_servers) > parseInt(ldata.start_servers)) {
                                        layer.msg(lan.soft.php_fpm_err2, { icon: 2 });
                                        return;
                                    }
                                    if (parseInt(ldata.max_spare_servers) < parseInt(ldata.min_spare_servers)) {
                                        layer.msg(lan.soft.php_fpm_err3, { icon: 2 });
                                        return;
                                    }
                                    if (parseInt(ldata.max_children) < parseInt(ldata.start_servers)) {
                                        layer.msg(lan.soft.php_fpm_err4, { icon: 2 });
                                        return;
                                    }
                                    if (parseInt(ldata.max_children) < 1 || parseInt(ldata.start_servers) < 1 || parseInt(ldata.min_spare_servers) < 1 || parseInt(ldata.max_spare_servers) < 1) {
                                        layer.msg(lan.soft.php_fpm_err5, { icon: 2 });
                                        return;
                                    }
                                    ldata['version'] = version;
                                    bt.soft.php.set_fpm_config(version, ldata, function (rdata) {
                                        soft.get_tab_contents(key, obj);
                                        bt.msg(rdata);
                                    })
                                })
                            }
                        }
                    ]
                    var tabCon = $(".soft-man-con").empty()
                    var _c_form = $('<div class="bt-form php-limit-config"></div >')
                    var clicks = [];
                    for (var i = 0; i < _form_datas.length; i++) {
                        var _form = bt.render_form_line(_form_datas[i]);
                        _c_form.append(_form.html)
                        clicks = clicks.concat(_form.clicks);
                    }
                    _c_form.append('<ul class="help-info-text c7">\
                                        <li>【最大子进程数量】越大，并发能力越强，但max_children最大不要超过5000</li>\
                                        <li>【内存】每个PHP子进程需要20MB左右内存，过大的max_children会导致服务器不稳定</li>\
                                        <li>【静态模式】始终维持设置的子进程数量，对内存开销较大，但并发能力较好</li>\
                                        <li>【动态模式】按设置最大空闲进程数来收回进程，内存开销小，建议小内存机器使用</li>\
                                        <li>【按需模式】根据访问需求自动创建进程，内存开销极小，但并发能力略差</li>\
                                        <li>【注意】以上为建议配置说明，线上项目复杂多样，请根据实际情况酌情调整</li>\
                                    </ul>')
                    tabCon.append(_c_form);

                    
                    bt.render_clicks(clicks);
                });
                break;
            case 'get_php_status':
                bt.soft.php.get_php_status(version, function (rdata) {
                    var arr = {};
                    arr[lan.bt.php_pool] = rdata.pool;
                    arr[lan.bt.php_manager] = ((rdata['process manager'] == 'dynamic') ? lan.bt.dynamic : lan.bt.static);
                    arr[lan.bt.php_start] = rdata['start time'];
                    arr[lan.bt.php_accepted] = rdata['accepted conn'];
                    arr[lan.bt.php_queue] = rdata['listen queue'];
                    arr[lan.bt.php_max_queue] = rdata['max listen queue'];
                    arr[lan.bt.php_len_queue] = rdata['listen queue len'];
                    arr[lan.bt.php_idle] = rdata['idle processes'];
                    arr[lan.bt.php_active] = rdata['active processes'];
                    arr[lan.bt.php_total] = rdata['total processes'];
                    arr[lan.bt.php_max_active] = rdata['max active processes'];
                    arr[lan.bt.php_max_children] = rdata['max children reached'];
                    arr[lan.bt.php_slow] = rdata['slow requests'];

                    var con = "<div style='height:450px;overflow:auto;'><table id='tab_php_status' class='table table-hover table-bordered' style='margin:0;padding:0'></table></div>";
                    $(".soft-man-con").html(con);
                    bt.render_table('tab_php_status', arr);
                })
                break;
              case 'get_php_session':
				bt.soft.php.get_php_session(version,function(res){
                    $(".soft-man-con").html('<div class="conf_p">'+
                        '<div class="line ">'+
                            '<span class="tname">存储模式</span>'+
                            '<div class="info-r ">'+
                                '<select class="bt-input-text mr5 change_select_session" name="save_handler" style="width:160px">'+
                                    '<option value="files" '+ (res.save_handler == 'files'?'selected':'') +'>files</option>'+
                                    (version != '52'?'<option value="redis" '+ (res.save_handler == 'redis'?'selected':'') +'>redis</option>':'') +
                                    (version != '73'?'<option value="memcache" '+ (res.save_handler == 'memcache'?'selected':'') +'>memcache</option>':'')+
                                    '<option value="memcached" '+ (res.save_handler == 'memcached'?'selected':'') +'>memcached</option>'+
                                '</select>'+
                            '</div>'+
                        '</div>'+
                        '<div class="line">'+
                            '<span class="tname">IP地址</span>'+
                            '<div class="info-r ">'+
                                '<input name="ip" class="bt-input-text mr5" type="text" style="width:160px" value="'+ res.save_path +'">'+
                            '</div>'+
                        '</div>'+
                        '<div class="line">'+
                            '<span class="tname">端口</span>'+
                            '<div class="info-r ">'+
                                '<input name="port" class="bt-input-text mr5" type="text" style="width:160px" value="'+ res.port +'">'+
                            '</div>'+
                        '</div>'+
                       '<div class="line">'+
                            '<span class="tname">密码</span>'+
                            '<div class="info-r ">'+
                                '<input name="passwd" class="bt-input-text mr5" placeholder="如果没有密码留空" type="text" style="width:160px" value="'+ res.passwd +'">'+
                            '</div>'+
                        '</div>'+
                        '<div class="line">'+
                            '<button name="btn_save" class="btn btn-success btn-sm mr5 ml5 btn_conf_save" style="margin-left: 110px;">保存</button>'+
                        '</div>'+
                        '<ul class="help-info-text c7">'+
                            '<li>若你的站点并发比较高，使用Redis，Memcache能有效提升PHP并发能力</li>'+
                            '<li>若调整Session模式后，网站访问异常，请切换回原来的模式</li>'+
                            '<li>切换Session模式会使在线的用户会话丢失，请在流量小的时候切换</li>'+
                        '</ul>'+
                        '<div class="session_clear" style="border-top: #ccc 1px dashed;padding-top: 15px;margin-top: 15px;">'+
                        '<div class="clear_title" style="padding-bottom:15px;">清理Session文件</div><div class="clear_conter"></div></div>'+
                    '</div>');
                    if(res.save_handler == 'files'){
                        bt.soft.php.get_session_count(function(res){
                            $('.clear_conter').html('<div class="session_clear_list"><div class="line"><span>总Session文件数量</span><span>'+ res.total +'</span></div><div class="line"><span>可清理的Session文件数量</span><span>'+ res.oldfile +'</span></div></div><button class="btn btn-success btn-sm clear_session_file">清理session文件</button>')
                            $('.clear_session_file').click(function(){
                                bt.soft.php.clear_session_count({
                                    title:'清理php_session文件',
                                    msg:'是否清理php_session文件？'
                                },function(res) {
                                    layer.msg(res.msg,{icon:res.status?1:2});
                                    setTimeout(function(){
                                        $('.bt-soft-menu p:eq(9)').click();
                                    },2000);
                                });
                            })
                        });
                    }else{
                        $('.clear_conter').html('当前只有存储模式为files才需要清理。').attr('style','color:#666')
                    }
                    switch_type(res.save_handler);
                    $('.change_select_session').change(function(){
                        switch_type($(this).val());
                        switch($(this).val()){
                            case 'redis':
                                $('[name="ip"]').val('127.0.0.1');
                                $('[name="port"]').val('6379');
                            break;
                            case 'memcache':
                                $('[name="ip"]').val('127.0.0.1');
                                $('[name="port"]').val('11211');
                            break;
                            case 'memcached':
                                $('[name="ip"]').val('127.0.0.1');
                                $('[name="port"]').val('11211');
                            break;
                        }
                    });
                    $('.btn_conf_save').click(function(){
                        bt.soft.php.set_php_session({
                            version:version,
                            save_handler:$('[name="save_handler"]').val(),
                            ip:$('[name="ip"]').val(),
                            port:$('[name="port"]').val(),
                            passwd:$('[name="passwd"]').val()
                        },function(res){
                            layer.msg(res.msg,{icon:res.status?1:2});
                            setTimeout(function(){
                              $('.bt-soft-menu p:eq(9)').click();
                            },2000);
                        })
                    });
                    function switch_type(type){
                        switch(type){
                            case 'files':
                                $('[name="ip"]').attr('disabled','disabled').val('');
                                $('[name="port"]').attr('disabled','disabled').val('');
                                $('[name="passwd"]').attr('disabled','disabled').val('');
                            break;
                            case 'redis':
                                $('[name="ip"]').attr('disabled',false);
                                $('[name="port"]').attr('disabled',false);
                                $('[name="passwd"]').attr('disabled',false);
                            break;
                            case 'memcache':
                                $('[name="ip"]').attr('disabled',false);
                                $('[name="port"]').attr('disabled',false);
                                $('[name="passwd"]').attr('disabled','disabled').val('');
                            break;
                            case 'memcached':
                                $('[name="ip"]').attr('disabled',false);
                                $('[name="port"]').attr('disabled',false);
                                $('[name="passwd"]').attr('disabled','disabled').val('');
                            break;
                        }
                    }
                });
			break
            case 'get_fpm_logs':
                bt.soft.php.get_fpm_logs(version, function (logs) {
                    var phpCon = '<textarea readonly="" style="margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + logs.msg + '</textarea>';
                    $(".soft-man-con").html(phpCon);
                    var ob = document.getElementById('error_log');
                    ob.scrollTop = ob.scrollHeight;
                })
                break;
            case 'get_slow_logs':
                bt.soft.php.get_slow_logs(version, function (logs) {
                    var phpCon = '<textarea readonly="" style="margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">' + logs.msg + '</textarea>';
                    $(".soft-man-con").html(phpCon);
                    var ob = document.getElementById('error_log');
                    ob.scrollTop = ob.scrollHeight;
                })
                break;
            case 'get_redis_status':
                bt.soft.redis.get_redis_status(function (rdata) {
                    var hit = (parseInt(rdata.keyspace_hits) / (parseInt(rdata.keyspace_hits) + parseInt(rdata.keyspace_misses)) * 100).toFixed(2);
                    var arrs = [];
                    arrs['uptime_in_days'] = [rdata.uptime_in_days, '已运行天数'];
                    arrs['tcp_port'] = [rdata.tcp_port, '当前监听端口'];
                    arrs['connected_clients'] = [rdata.connected_clients, '连接的客户端数量'];
                    arrs['used_memory_rss'] = [bt.format_size(rdata.used_memory_rss), 'Redis当前占用的系统内存总量'];
                    arrs['used_memory'] = [bt.format_size(rdata.used_memory), 'Redis历史分配内存的峰值'];
                    arrs['mem_fragmentation_ratio'] = [rdata.mem_fragmentation_ratio, '内存碎片比率'];
                    arrs['total_connections_received'] = [rdata.total_connections_received, '运行以来连接过的客户端的总数量'];
                    arrs['total_commands_processed'] = [rdata.total_commands_processed, '运行以来执行过的命令的总数量'];
                    arrs['instantaneous_ops_per_sec'] = [rdata.instantaneous_ops_per_sec, '服务器每秒钟执行的命令数量'];
                    arrs['keyspace_hits'] = [rdata.keyspace_hits, '查找数据库键成功的次数'];
                    arrs['keyspace_misses'] = [rdata.keyspace_misses, '查找数据库键失败的次数'];
                    arrs['hit'] = [hit, '查找数据库键命中率'];
                    arrs['latest_fork_usec'] = [rdata.latest_fork_usec, '最近一次 fork() 操作耗费的微秒数'];

                    var con = "<div class=\"divtable\"><table id='tab_get_redis_status' style=\"width: 490px;\" class='table table-hover table-bordered '><thead><th>字段</th><th>当前值</th><th>说明</th></thead></table></div>";
                    $(".soft-man-con").html(con);
                    bt.render_table('tab_get_redis_status', arrs, true);
                })
                break;
            case 'openliMa_set':
                    var loadT = bt.load();
                    $.post('config?action=get_ols_value', function(rdata) {
                        loadT.close();
                        var _mlist_data='',
                        tips_i = 0,
                        help_tips=['#为静态和动态响应启用GZIP/Brotli压缩.',
                        '#指定应用于动态内容的GZIP压缩级别。范围从1（最低）到9（最高）.',
                        '',
                        '#指定服务器可以接受的最大并发连接数.<br>\
                        #这包括纯TCP连接和SSL连接',
                        '#指定服务器将接受的最大并发SSL连接数<br>\
                        #因为总的并发SSL和非SSL连接不能超过“Max connections”指定的限制,<br>\
                        #允许的并发SSL连接的实际数目必须低于此限制.',
                        '#指定在处理一个请求期间允许的最大连接空闲时间（秒）',
                        '#指定可通过保持活动（持久）会话服务的最大请求数'];
                        for (var i in rdata) {
                            var mlist = {title: '',items: []},list = {};
                            list.name = i;
                            list.width = '130px';
                            list.value = rdata[i];
                            list.type = i=='enableGzipCompress'?'switch':'input';
                            list.ps_help = help_tips[tips_i];
                            mlist.items.push(list);
                            mlist.title = i;
                            _mlist_data += bt.render_form_line(mlist).html;
                            tips_i++;
                        }
                        var tabCon = $(".soft-man-con").empty();
                        tabCon.append('<div class="openlite_set">' + _mlist_data + '</div></div>');
                        var datas = {
                            title: ' ',
                            class: 'openlite_button',
                            items: [{
                                    name: 'btn_fresh',
                                    text: lan.public.fresh,
                                    type: 'button',
                                    callback: function(ldata) {
                                        soft.get_tab_contents(key, obj);
                                    }
                                },
                                {
                                    name: 'btn_save',
                                    text: lan.public.save,
                                    type: 'button',
                                    width: '62px',
                                    callback: function(ldata) {
                                        var datal = {},
                                        loadP = bt.load();
                                        delete ldata.btn_fresh;
                                        delete ldata.btn_save;
                                        ldata['enableGzipCompress']=$("#enableGzipCompress").prop('checked')?1:0;
                                        ldata = JSON.stringify(ldata);
                                        datal = { array: ldata };
                                        bt.send('set_ols_value', 'config/set_ols_value', datal, function(res) {
                                            loadP.close();
                                            soft.get_tab_contents(key, obj);
                                            bt.msg(res);
                                        });
                                    }
                                }
                            ]
                        }
                        var _form_data = bt.render_form_line(datas);
                        $('.openlite_set').append(_form_data.html);
                        bt.render_clicks(_form_data.clicks);
                        $(".openlite_set .tname").css('width','150px');
                        $('.enableGzipCompress_help').css('margin-left','104px');
                        $(".openlite_set").on("mouseenter", ".bt-ico-ask", function () {
                            var idd = $(this).attr('class').split(" ")[1], tip = $(this).attr('tip');
                            layer.tips(tip, '.' + idd + '', { tips: [1, '#d4d4d4'], time: 0, area: '300px'});
                        });
                        $(".openlite_set").on("mouseleave", ".bt-ico-ask", function () {
                            layer.closeAll('tips');
                        });
                    });
                    break;
        }
    },
    update_zip: function (file) {
        var formData = new FormData();
        formData.append("plugin_zip", file);
        $.ajax({
            url: "/plugin?action=update_zip",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.status === false) {
                    layer.msg(data.msg, { icon: 2 });
                    return;
                }
                var loadT = layer.open({
                    type: 1,
                    area: "500px",
                    title: "安装第三方插件包",
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: '<style>\
                        .install_three_plugin{padding:25px;padding-bottom:70px}\
                        .plugin_user_info p { font-size: 14px;}\
                        .plugin_user_info {padding: 15px 30px;line-height: 26px;background: #f5f6fa;border-radius: 5px;border: 1px solid #efefef;}\
                        .btn-content{text-align: center;margin-top: 25px;}\
                    </style>\
                    <div class="bt-form c7  install_three_plugin pb70">\
                        <div class="plugin_user_info">\
                            <p><b>名称：</b>'+ data.title + '</p>\
                            <p><b>版本：</b>' + data.versions +'</p>\
                            <p><b>描述：</b>' + data.ps + '</p>\
                            <p><b>大小：</b>' + bt.format_size(data.size, true) + '</p>\
                            <p><b>作者：</b>' + data.author + '</p>\
                            <p><b>来源：</b><a class="btlink" href="'+data.home+'" target="_blank" rel="noreferrer noopener">' + data.home + '</a></p>\
                        </div>\
                        <ul class="help-info-text c7">\
                            <li style="color:red;">此为第三方开发的插件，宝塔无法验证其可靠性!</li>\
                            <li>安装过程可能需要几分钟时间，请耐心等候!</li>\
                            <li>如果已存在此插件，将被替换!</li>\
                        </ul>\
                        <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger mr5" onclick="layer.closeAll()">取消</button><button type="button" class="btn btn-sm btn-success" onclick="soft.input_zip(\''+ data.name + '\',\'' + data.tmp_path +'\')">确定安装</button></div>\
                    </div>'
                });
            },
            error: function (responseStr) {
                layer.msg('上传失败2!', { icon: 2 });
            }
        });
    },

    input_zip: function (plugin_name,tmp_path,data) {
        bt.soft.show_speed_window({title:'正在安装第三方插件，可能需要几分钟时间，请耐心等候!',status:true},function(){
            $.post('/plugin?action=input_zip', { plugin_name: plugin_name, tmp_path: tmp_path }, function (rdata) {
                layer.closeAll()
                if (rdata.status) {
                    soft.get_list();
                }
                setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }) }, 1000);
            });
        });
    }


};

function soft_td_width_auto() {
    var thead_width = '', winWidth = $(window).width();
    if (winWidth <= 1370 && winWidth > 1280) {
        thead_width = winWidth / 4;
    } else if (winWidth <= 1280 && winWidth > 1210) {
        thead_width = winWidth / 5;
    } else if (winWidth <= 1210) {
        thead_width = winWidth / 6;
    } else {
        thead_width = winWidth / 3.5;
    }
    $('#softList thead th:eq(2)').width(thead_width);
    $('#softList tbody tr td:nth-child(8n+2)>span').width(thead_width + 75);
}

function set_disable_functions(version, data) {
    bt.soft.php.disable_functions(version, data, function (rdata) {
        if (rdata.status) {
            soft.get_tab_contents('set_dis_fun', $(".bgw"));
        }
        bt.msg(rdata);
    })
}

var openId = add = null;
function AddDeployment(maction) {
    if (maction == 1) {
        var pdata = 'title=' + $("input[name='title']").val()
            + '&dname=' + $("input[name='name']").val()
            + '&ps=' + $("input[name='ps']").val()
            + '&version=' + $("input[name='version']").val()
            + '&rewrite=' + ($("input[name='rewrite']").attr('checked') ? 1 : 0)
            + '&shell=' + ($("input[name='shell']").attr('checked') ? 1 : 0)
            + '&php=' + $("input[name='php']").val()
            + '&md5=' + $("input[name='md5']").val()
            + '&download=' + $("input[name='download']").val()
        var loadT = layer.msg('正在提交 <img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/deployment?action=AddPackage', pdata, function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            if (rdata.status) {
                GetSrcList();
                layer.close(openId);
            }
        });

        return;
    }
    openId = layer.open({
        type: 1,
        skin: 'demo-class',
        area: '480px',
        title: '添加源码包',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '标题：<input type="text" name="title"><br>\
					标识：<input type="text" name="name"><br>\
					描述：<input type="text" name="ps"><br>\
					版本：<input type="text" name="version"><br>\
					是否写伪静态：<input type="checkbox" name="rewrite"><br>\
					是否执行安装脚本：<input type="checkbox" name="shell"><br>\
					支持的PHP版本：<input type="text" name="php"><br>\
					md5：<input type="text" name="md5">\
					下载地址：<input type="text" name="download"><br>\
					<button class="btn btn-default btn-sm" onclick="AddDeployment(1);">提交</button>'
    });
}


$(".searchInput").keyup(function (e) {
    if (e.keyCode == 13) {
        GetSrcList();
    }
});

function AddSite(codename,title) {
    var array;
    var str = "";
    var domainlist = '';
    var domain = array = $("#mainDomain").val().split("\n");
    var Webport = [];
    var checkDomain = domain[0].split('.');
    if (checkDomain.length < 1) {
        layer.msg('域名格式不正确，请重新输入!', { icon: 2 });
        return;
    }
    for (var i = 1; i < domain.length; i++) {
        domainlist += '"' + domain[i] + '",';
    }
    Webport = domain[0].split(":")[1];//主域名端口
    if (Webport == undefined) {
        Webport = "80";
    }
    domainlist = domainlist.substring(0, domainlist.length - 1);//子域名json
    mainDomain = domain[0].split(':')[0];
    domain = '{"domain":"' + domain[0] + '","domainlist":[' + domainlist + '],"count":' + domain.length + '}';//拼接json
    var php_version = $("select[name='version']").val();
    var loadT = layer.msg('正在创建站点 <img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, "#000"] })
    var data = $("#addweb").serialize() + "&port=" + Webport + "&webname=" + domain + '&ftp=false&sql=true&address=localhost&codeing=utf8&version=' + php_version;
    $.post('/site?action=AddSite', data, function (ret) {
        layer.close(loadT)
        if (!ret.siteStatus) {
            layer.msg(ret.msg, { icon: 5 });
            return;
        }
        layer.close(add)
        var sqlData = '';
        if (ret.databaseStatus) {
            sqlData = "<p class='p1'>数据库账号资料</p>\
					 		<p><span>数据库名：</span><strong>" + ret.databaseUser + "</strong></p>\
					 		<p><span>用户：</span><strong>" + ret.databaseUser + "</strong></p>\
					 		<p><span>密码：</span><strong>" + ret.databasePass + "</strong></p>\
					 		"
        }
        var pdata = 'dname=' + codename + '&site_name=' + mainDomain + '&php_version=' + php_version;
        var loadT = layer.msg('<div class="depSpeed">正在提交 <img src="/static/img/ing.gif"></div>', { icon: 16, time: 0, shade: [0.3, "#000"] });

        setTimeout(function () {
            GetSpeed();
        }, 2000);

        $.post('/deployment?action=SetupPackage', pdata, function (rdata) {
            layer.close(loadT)
            if (!rdata.status) {
                layer.msg(rdata.msg, { icon: 5 ,time:10000});
                return;
            }

            if (rdata.msg.admin_username != '') {
                sqlData = "<p class='p1'>已成功部署，无需安装，请登录修改默认账号密码</p>\
					 		<p><span>用户：</span><strong>" + rdata.msg.admin_username + "</strong></p>\
					 		<p><span>密码：</span><strong>" + rdata.msg.admin_password + "</strong></p>\
					 		"
            }
            sqlData += "<p><span>访问站点：</span><a class='btlink' href='http://" + (mainDomain +'/'+ rdata.msg.success_url).replace('//','/') + "' target='_blank' rel='noreferrer noopener'>http://" + (mainDomain +'/'+ rdata.msg.success_url).replace('//','/') + "</a></p>";

            layer.open({
                type: 1,
                area: '600px',
                title: '已成功部署【' + title+'】',
                closeBtn: 2,
                shadeClose: false,
                content: "<div class='success-msg'>\
						<div class='pic'><img src='/static/img/success-pic.png'></div>\
						<div class='suc-con'>\
							" + sqlData + "\
						</div>\
					 </div>",
            });
            if ($(".success-msg").height() < 150) {
                $(".success-msg").find("img").css({
                    "width": "150px",
                    "margin-top": "30px"
                });
            }
        });


    });

}

function GetSpeed() {
    if (!$('.depSpeed')) return;
    $.get('/deployment?action=GetSpeed', function (speed) {
        if (speed.status === false) return;
        if (speed.name == '下载文件') {
            speed = '<p>正在' + speed.name + ' <img src="/static/img/ing.gif"></p>\
				<div class="bt-progress"><div class="bt-progress-bar" style="width:'+ speed.pre + '%"><span class="bt-progress-text">' + speed.pre + '%</span></div></div>\
				<p class="f12 c9"><span class="pull-left">'+ ToSize(speed.used) + '/' + ToSize(speed.total) + '</span><span class="pull-right">' + ToSize(speed.speed) + '/s</span></p>';
            $('.depSpeed').prev().hide();
            $('.depSpeed').css({ "margin-left": "-37px", "width": "380px" });
            $('.depSpeed').parents(".layui-layer").css({ "margin-left": "-100px" });
        } else {
            speed = '<p>' + speed.name + '</p>';
            $('.depSpeed').prev().show();
            $('.depSpeed').removeAttr("style");
            $('.depSpeed').parents(".layui-layer").css({ "margin-left": "0" });
        }

        $('.depSpeed').html(speed);
        setTimeout(function () {
            GetSpeed();
        }, 1000);
    });
}

function onekeyCodeSite(codename, versions,title,enable_functions) {
    $.post('/site?action=GetPHPVersion', function (rdata) {
        var php_version = "";
        var n = 0;
        for (var i = rdata.length - 1; i >= 0; i--) {
            if (versions.indexOf(rdata[i].version) != -1) {
                php_version += "<option value='" + rdata[i].version + "'>" + rdata[i].name + "</option>";
                n++;
            }
        }

        if (n == 0) {
            layer.msg('缺少被支持的PHP版本，请安装!', { icon: 5 });
            return;
        }
        var default_path = bt.get_cookie('sites_path');
        if (!default_path) default_path = '/www/wwwroot';
        

        var con = '<form class="bt-form pd20 pb70" id="addweb">\
					<div class="line"><span class="tname">域名</span>\
						<div class="info-r c4"><textarea id="mainDomain" class="bt-input-text" name="webname_1" style="width:398px;height:100px;line-height:22px"></textarea>\
							<div class="placeholder c9" style="top:10px;left:10px">每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88</div>\
						</div>\
					</div>\
					<div class="line"><span class="tname">备注</span>\
						<div class="info-r c4"><input id="Wbeizhu" class="bt-input-text" name="ps" placeholder="网站备注" style="width:398px" type="text"> </div>\
					</div>\
					<div class="line"><span class="tname">根目录</span>\
						<div class="info-r c4"><input id="inputPath" class="bt-input-text mr5" name="path" value="'+ default_path+'" placeholder="网站根目录" style="width:398px" type="text"><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'inputPath\')"></span> </div>\
					</div>\
					<div class="line"><span class="tname">数据库</span>\
						<div class="info-r c4">\
							<input id="datauser" class="bt-input-text" name="datauser" placeholder="用户名/数据库名" style="width:190px;margin-right:13px" type="text">\
							<input id="datapassword" class="bt-input-text" name="datapassword" placeholder="密码" style="width:190px" type="text">\
						</div>\
					</div>\
					<div class="line"><span class="tname">源码</span>\
						<input class="bt-input-text mr5 disable" name="code" style="width:190px" value="'+ title + '" disabled>\
						<span class="c9">准备为你部署的源码程序</span>\
					</div>\
					<div class="line"><span class="tname">PHP版本</span>\
						<select class="bt-input-text mr5" name="version" id="c_k3" style="width:100px">\
							'+ php_version + '\
						</select>\
						<span class="c9">请选择源码程序支持的php版本</span>\
					</div>\
					<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm onekeycodeclose">取消</button>\
						<button type="button" class="btn btn-success btn-sm" onclick="AddSite(\''+ codename + '\',\'' + title + '\')">提交</button>\
					</div>\
				</from>';
        add = layer.open({
            type: 1,
            title: "宝塔一键部署【" + title+'】',
            area: '560px',
            closeBtn: 2,
            shadeClose: false,
            content: con
        });

        if (enable_functions.length > 2) {
            layer.msg("<span style='color:red'>注意：部署此项目，以下函数将被解禁:<br> "+ enable_functions +"</span>", {icon:7,time:10000});
        }
        var placeholder = "<div class='placeholder c9' style='top:10px;left:10px'>每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88</div>";
        $(".onekeycodeclose").click(function () {
            layer.close(add);
        });
        $('#mainDomain').after(placeholder);
        $(".placeholder").click(function () {
            $(this).hide();
            $('#mainDomain').focus();
        })
        $('#mainDomain').focus(function () {
            $(".placeholder").hide();
        });

        $('#mainDomain').blur(function () {
            if ($(this).val().length == 0) {
                $(".placeholder").show();
            }
        });
        //FTP账号数据绑定域名
        $('#mainDomain').on('input', function () {
            var defaultPath = bt.get_cookie('sites_path');
            if (!defaultPath) defaultPath = '/www/wwwroot';
            var array;
            var res, ress;
            var str = $(this).val();
            var len = str.replace(/[^\x00-\xff]/g, "**").length;
            array = str.split("\n");
            ress = array[0].split(":")[0];
            res = ress.replace(new RegExp(/([-.])/g), '_');
            if (res.length > 15) res = res.substr(0, 15);
            if ($("#inputPath").val().substr(0, defaultPath.length) == defaultPath) $("#inputPath").val(defaultPath + '/' + ress);
            if (!isNaN(res.substr(0, 1))) res = "sql" + res;
            if (res.length > 15) res = res.substr(0, 15);
            $("#Wbeizhu").val(ress);
            $("#datauser").val(res);
        })
        $('#Wbeizhu').on('input', function () {
            var str = $(this).val();
            var len = str.replace(/[^\x00-\xff]/g, "**").length;
            if (len > 20) {
                str = str.substring(0, 20);
                $(this).val(str);
                layer.msg('不要超出20个字符', {
                    icon: 0
                });
            }
        })
        //获取当前时间时间戳，截取后6位
        var timestamp = new Date().getTime().toString();
        var dtpw = timestamp.substring(7);
        $("#datauser").val("sql" + dtpw);
        $("#datapassword").val(_getRandomString(10));
    });
}

//生成n位随机密码
function _getRandomString(len) {
    len = len || 32;
    var $chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'; // 默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1  
    var maxPos = $chars.length;
    var pwd = '';
    for (i = 0; i < len; i++) {
        pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
    }
    return pwd;
}
var score = {
    total:1,
    type:'',
    data:[],
    // 获取评论信息
    get_score_info:function (obj,callback) {
        var loadT = layer.msg('<div class="depSpeed">正在获取评论信息 <img src="/static/img/ing.gif"></div>', { icon: 16, time: 0, shade: [0.3, "#000"] });
        bt.send('get_score','plugin/get_score',{
            pid:obj.pid,
            p:obj.p,
            limit_num:obj.limit_num
        },function(res){
            layer.close(loadT);
            if(res.status === false){
                layer.msg(res.msg,{icon:2});
                return false;
            }
            if(callback) callback(res);
        });
    },
    render_score_info:function(obj,callback){
        var config = {pid:obj.pid},_this = this;
        obj.p == undefined?config.p = 1:config.p = parseInt(obj.p)
        obj.limit_num == undefined?config.limit_num = '':config.limit_num = obj.limit_num
        score.get_score_info(config,function(res){
            var _split_score = res.split.reverse(),_average_score = (_split_score[4]*1+_split_score[3]*2+_split_score[2]*3+_split_score[1]*4 +_split_score[0]*5)/res.total,_data = res.data,_html ='';
            _this.total = res.total;
            $('.comment_user_count').text(obj.count);
            $('.comment_num').text((res.total!==0?_average_score:0).toFixed(1));
            $('.comment_partake').text(res.total);
            $('.comment_rate').text(res.total!==0?(((((_split_score[0]+_split_score[1])/res.total).toFixed(2)*100).toFixed(0))+'%'):'0%');
            for(var i=0;i<5;i++){
                $('.comment_star_group:eq('+ i +')').find('.comment_progress .comment_progress_bgw').css('width',(((_split_score[i] / res.total).toFixed(2)*100).toFixed(0))+'%')
            }
            $('.comment_tab span:eq(1)').find('i').text(_split_score[0]+_split_score[1]);
            $('.comment_tab span:eq(2)').find('i').text(_split_score[2]+_split_score[3]);
            $('.comment_tab span:eq(3)').find('i').text(_split_score[4]);
            
            for (var j = 0; j < _data.length; j++){
                _html += '<div class="comment_box" data-index="'+ ((config.p == 1?'':config.p-1)+(j+'')) +'">\
                    <div class="comment_box_title">\
                        <span class="nice_star">\
                            <span class="glyphicon '+ (_data[j].num >=1?'star_active':'') +' glyphicon-star" aria-hidden="true"></span>\
                            <span class="glyphicon '+ (_data[j].num >=2?'star_active':'') +' glyphicon-star" aria-hidden="true"></span>\
                            <span class="glyphicon '+ (_data[j].num >=3?'star_active':'') +' glyphicon-star" aria-hidden="true"></span>\
                            <span class="glyphicon '+ (_data[j].num >=4?'star_active':'') +' glyphicon-star" aria-hidden="true"></span>\
                            <span class="glyphicon '+ (_data[j].num >=5?'star_active':'') +' glyphicon-star" aria-hidden="true"></span>\
                        </span>\
                        <span class="nice_name" title="'+ _data[j].nickname +'">'+ _data[j].nickname +'</span>\
                        <span class="nice_time" title="'+ bt.format_data(_data[j].addtime ) +'">'+ timeago(_data[j].addtime * 1000) +'</span>\
                    </div>\
                    <div class="comment_box_content">'+ (getLength(_data[j].ps)>65?reBytesStr(_data[j].ps,65)+'...&nbsp;<a href="javascript:;" class="btlink">详情</a>':_data[j].ps) +'</div>\
                </div>'
                // console.log(getLength(_data[j].ps)>70?reBytesStr(_data[j].ps,70)+'&nbsp;<a href="javascript:;" class="btlink">详情</a>':_data[j].ps);
            }
            _this.data = _this.data.concat(_data);
            if(res.total > 10 && _data.length === 10){
                _html += '<div class="comment_box get_next_page"><span class="glyphicon glyphicon-chevron-down" aria-hidden="true"></span>点击获取更多评论</div>'
            }
            $('.comment_content').find('.get_next_page').remove();
            $('.comment_content').append(_html);
            if($('.comment_content .comment_box').length > 6){
                $('.comment_content').addClass('box-shadow');
            }else{
                $('.comment_content').removeClass('box-shadow');
            }
            if(callback) callback(res);
        });
    },
    // 设置评论信息
    set_score_info:function (obj,callback){
        var loadT = layer.msg('<div class="depSpeed">正在提交评论信息 <img src="/static/img/ing.gif"></div>', { icon: 16, time: 0, shade: [0.3, "#000"] });
        bt.send('set_score','plugin/set_score',{
            pid:obj.pid,
            num:obj.num,
            ps:obj.ps
        },function(res){
            layer.close(loadT);
            if(res.status === false){
                layer.msg(res.msg,{icon:2});
                return false;
            }
            if(callback) callback(res);
        });
    },
    open_score_view:function(_pid,_name,_count){
        layer.open({
            type: 1,
            title:'【'+ _name + '】评分',
            area:['550px','350px'],
            closeBtn: 2,
            shadeClose: false,
            content:'<div class="pd20 score_info_view"><div class="comment_title">\
                    <div class="comment_left">\
                        <div class="comment_num">--</div>\
                        <ul class="comment_num_tips">\
                            <li>使用人数&nbsp;<span class="comment_user_count">--</span></li>\
                            <li>共&nbsp;<span class="comment_partake">--</span>&nbsp;人参与评分</li>\
                            <li><span class="comment_rate">--</span>&nbsp;好评率</li>\
                        </ul>\
                    </div>\
                    <div class="comment_right">\
                        <div class="comment_star_group">\
                            <div class="comment_star">\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                            </div>\
                            <div class="comment_progress">\
                                <div class="comment_progress_bgw"></div>\
                                <div class="comment_progress_speed"></div>\
                            </div>\
                        </div>\
                        <div class="comment_star_group">\
                            <div class="comment_star">\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                            </div>\
                            <div class="comment_progress">\
                                <div class="comment_progress_bgw"></div>\
                                <div class="comment_progress_speed"></div>\
                            </div>\
                        </div>\
                        <div class="comment_star_group">\
                            <div class="comment_star">\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                            </div>\
                            <div class="comment_progress">\
                                <div class="comment_progress_bgw"></div>\
                                <div class="comment_progress_speed"></div>\
                            </div>\
                        </div>\
                        <div class="comment_star_group">\
                            <div class="comment_star">\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                            </div>\
                            <div class="comment_progress">\
                                <div class="comment_progress_bgw"></div>\
                                <div class="comment_progress_speed"></div>\
                            </div>\
                        </div>\
                        <div class="comment_star_group">\
                            <div class="comment_star">\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_none glyphicon-star" aria-hidden="true"></span>\
                                <span class="glyphicon star_active glyphicon-star" aria-hidden="true"></span>\
                            </div>\
                            <div class="comment_progress">\
                                <div class="comment_progress_bgw"></div>\
                                <div class="comment_progress_speed"></div>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
                <div class="comment_tab">\
                    <span class="active" data-num="">全部评价</span>\
                    <span data-num="5">好评&nbsp;<i>--</i>&nbsp;</span>\
                    <span data-num="3">中评&nbsp;<i>--</i>&nbsp;</span>\
                    <span data-num="1">差评&nbsp;<i>--</i>&nbsp;</span>\
                </div>\
                <div class="comment_content">\
                </div>\
                <div class="add_score_view">\
                    <div class="score_icon_group" data-icon="5">\
                        <span class="glyphicon glyphicon-star active" aria-hidden="true" title="非常差：1分"></span>\
                        <span class="glyphicon glyphicon-star active" aria-hidden="true" title="差：2分"></span>\
                        <span class="glyphicon glyphicon-star active" aria-hidden="true" title="一般：3分"></span>\
                        <span class="glyphicon glyphicon-star active" aria-hidden="true" title="好：4分"></span>\
                        <span class="glyphicon glyphicon-star active" aria-hidden="true" title="非常好：5分" ></span>\
                    </div>\
                    <div class="score_icon_group_tips">力荐：5分</div>\
                    <textarea class="score_input bt-input-text" placeholder="请输入评价内容，字数少于60字，可为空。" name="score_val"></textarea>\
                    <span class="score_input_tips pull-right">还可输入&nbsp;<i>60</i>&nbsp;个字</span>\
                </div>\
                <div class="edit_view ">\
                    <span>参与评分</span>\
                </div>\
            </div>'
            ,success:function(index,layero){
                score.data = [];
                score.render_score_info({pid:_pid,count:_count},function(){
                    $('.score_info_view').show();
                });
                score.score_icon_time = null;
                $('.score_icon_group span').hover(function(){
                    var _active = $(this).hasClass('active');
                    // if($(this).prevAll().length == 0 && $(this).nextAll('.active').length == 0 && _active){
                    //     $(this).removeClass('active').nextAll().removeClass('active')
                    //     $('.score_icon_group_tips').html('选择以上图标选择评分等级1-5');
                    //     $('.score_icon_group').attr('data-icon',0)
                    // }else{
                        // $(this).addClass('active').nextAll().removeClass('active');
                        // $(this).prevAll().addClass('active');
                        // $('.score_icon_group').attr('data-icon',$(this).prevAll().length +1)
                        // var _title =  $(this).attr('title');
                        // $('.score_icon_group_tips').text(_title);
                    // }
                });
                $('.score_icon_group span').click(function(){
                    var _active = $(this).hasClass('active');
                    if($(this).prevAll().length == 0 && $(this).nextAll('.active').length == 0 && _active){
                        $('.edit_view').addClass('active');
                        $(this).removeClass('active').nextAll().removeClass('active')
                        $('.score_icon_group_tips').html('点击选择图标评分等级1-5星');
                        $('.score_icon_group').attr('data-icon',0)
                    }else{
                        $('.edit_view').removeClass('active');
                        $(this).addClass('active').nextAll().removeClass('active');
                        $(this).prevAll().addClass('active');
                        $('.score_icon_group').attr('data-icon',$(this).prevAll().length +1)
                        var _title =  $(this).attr('title');
                        $('.score_icon_group_tips').text(_title);
                    }
                });
                $('.comment_tab span').click(function(e){
                    var _num = $(this).attr('data-num');
                    $('.comment_content').removeClass('box-shadow');
                    $(this).addClass('active').siblings().removeClass('active');
                    $('.comment_content').html('');
                    score.data = []
                    score.type = _num;
                    score.render_score_info({pid:_pid,limit_num:_num,count:_count});

                });
                $('.comment_content').on('click','.get_next_page',function () {
                    var _next_page = ($('.comment_content .comment_box').length / 10)+1;
                    score.render_score_info({pid:_pid,limit_num:score.type,p:_next_page,count:_count});
                });
                $('.comment_content').on('click','.comment_box',function(){
                    if(!$(this).hasClass('get_next_page')){
                        var _index = $(this).attr('data-index');
                        layer.open({
                            type: 1,
                            title:false,
                            area:['350px','200px'],
                            closeBtn: 2,
                            shadeClose: false,
                            content: '<div class="score_details" >'+ $(this).html() +'</div>',
                            success:function(index,layers) {
                                $('.score_details .comment_box_content').html(score.data[_index]['ps']);
                            }
                        });
                    }
                });
                $('.edit_view').click(function(){
                    if($('.edit_view').hasClass('active')){
                        // layer.msg('请选择评分等级',{icon:2});
                        $('.score_icon_group_tips').css('color','red');
                        setTimeout(function(){
                            $('.score_icon_group_tips').removeAttr('style')
                        },1000);
                        return false
                    }
                    var _num = parseInt($('.score_icon_group').attr('data-icon')),_ps = $('.score_input').val();
                    if(_num == 0){
                        layer.msg('评分等级不能为空',{icon:2});
                        return false;
                    }
                    if(120 - getLength(_ps)<0){
                        layer.msg('评价信息不能超过60个字',{icon:2});
                        return false;
                    }
                    score.set_score_info({pid:_pid,num:_num,ps:_ps == ''?'用户未做任何评价': _ps},function(res){
                        layer.msg(res.msg,{icon:1});
                        score.render_score_info({pid:_pid,limit_num:score.type,count:_count});
                        soft.flush_cache();
                        layer.close(index);
                    });
                    return false
                    layer.open({
                        type: 1,
                        title:'添加评论',
                        area:['400px','350px'],
                        closeBtn: 2,
                        shadeClose: false,
                        btn:['确认','取消'],
                        content:'<div class="add_score_view">\
                            <div class="score_icon_group" data-icon="0">\
                                <span class="glyphicon glyphicon-star" aria-hidden="true" title="很差：1分"></span>\
                                <span class="glyphicon glyphicon-star" aria-hidden="true" title="较差：2分"></span>\
                                <span class="glyphicon glyphicon-star" aria-hidden="true" title="还行：3分"></span>\
                                <span class="glyphicon glyphicon-star" aria-hidden="true" title="推荐：4分"></span>\
                                <span class="glyphicon glyphicon-star" aria-hidden="true" title="力荐：5分" ></span>\
                            </div>\
                            <div class="score_icon_group_tips">(点击以上图标选择评分等级1-5)</div>\
                            <textarea class="score_input bt-input-text" placeholder="请输入评价内容，字数少于60字，可为空。" name="score_val"></textarea>\
                            <span class="score_input_tips pull-right">还可输入&nbsp;<i>60</i>&nbsp;个字</span>\
                        </div>',
                        success:function(){
                            $('.score_icon_group span').click(function(){
                                var _active = $(this).hasClass('active');
                                if($(this).prevAll().length == 0 && $(this).nextAll('.active').length == 0 && _active){
                                    $(this).removeClass('active').nextAll().removeClass('active')
                                    $('.score_icon_group_tips').html('(点击以上图标选择评分等级1-5)');
                                    $('.score_icon_group').attr('data-icon',0)
                                }else{
                                    $(this).addClass('active').nextAll().removeClass('active');
                                    $(this).prevAll().addClass('active');
                                    $('.score_icon_group').attr('data-icon',$(this).prevAll().length +1)
                                    var _title =  $(this).attr('title');
                                    $('.score_icon_group_tips').text(_title);
                                }
                            });
                            $('.score_input').on('keydown keyup focus click',function(){
                                var _val = $('.score_input').val(),_size = 120 - getLength(_val);
                                if(_size > 0){
                                    $('.score_input_tips i').css('color',_size > 20?'#666':'red').text(parseInt(_size/2));
                                    $('.score_input').attr('style','');
                                }else{
                                    $('.score_input_tips i').text(0)
                                    $('.score_input').css({'outline-color':'red','border':'1px solid red'});
                                }
                            });
                        },
                        yes:function(index,layero){
                            var _num = parseInt($('.score_icon_group').attr('data-icon')),_ps = $('.score_input').val();
                            if(_num == 0){
                                layer.msg('评分等级不能为空',{icon:2});
                                return false;
                            }
                            if(120 - getLength(_ps)<0){
                                layer.msg('评价信息不能超过60个字',{icon:2});
                                return false;
                            }
                            score.set_score_info({pid:_pid,num:_num,ps:_ps == ''?'用户未做任何评价': _ps},function(res){
                                layer.msg(res.msg,{icon:1});
                                score.render_score_info({pid:_pid,limit_num:score.type,count:_count});
                                soft.flush_cache();
                                layer.close(index);
                            });
                        }
                    });
                });
            }
        })
    }
}

function timeago(dateTimeStamp){   //dateTimeStamp是一个时间毫秒，注意时间戳是秒的形式，在这个毫秒的基础上除以1000，就是十位数的时间戳。13位数的都是时间毫秒。
    if(dateTimeStamp.toString().length < 10) dateTimeStamp = dateTimeStamp * 1000
    var minute = 1000 * 60,
        hour = minute * 60,
        day = hour * 24,
        week = day * 7,
        halfamonth = day * 15,
        month = day * 30,
        now = new Date().getTime(),   //获取当前时间毫秒
        diffValue = now - dateTimeStamp;//时间差
    if(diffValue <= 0){return '刚刚';}
    var minC = diffValue/minute,  //计算时间差的分，时，天，周，月
        hourC = diffValue/hour,
        dayC = diffValue/day,
        weekC = diffValue/week,
        monthC = diffValue/month,
        result ='刚刚';
    if(monthC >= 1 && monthC <= 3){
        result = " " + parseInt(monthC) + "月前"
    }else if(weekC >= 1 && weekC <= 3){
        result = " " + parseInt(weekC) + "周前"
    }else if(dayC >= 1 && dayC <= 6){
        result = " " + parseInt(dayC) + "天前"
    }else if(hourC >= 1 && hourC <= 23){
        result = " " + parseInt(hourC) + "小时前"
    }else if(minC >= 1 && minC <= 59){
        result =" " + parseInt(minC) + "分钟前"
    }else if(diffValue >= 0 && diffValue <= minute){
        result = "刚刚"
    }else {
        var datetime = new Date();
        datetime.setTime(dateTimeStamp);
        var Nyear = datetime.getFullYear(),
            Nmonth = datetime.getMonth() + 1 < 10 ? "0" + (datetime.getMonth() + 1) : datetime.getMonth() + 1,
            Ndate = datetime.getDate() < 10 ? "0" + datetime.getDate() : datetime.getDate(),
            Nhour = datetime.getHours() < 10 ? "0" + datetime.getHours() : datetime.getHours(),
            Nminute = datetime.getMinutes() < 10 ? "0" + datetime.getMinutes() : datetime.getMinutes(),
            Nsecond = datetime.getSeconds() < 10 ? "0" + datetime.getSeconds() : datetime.getSeconds(),
            result =  Nmonth + "-" + Ndate
    }
    if (!result) result = '刚刚'
    return ((result == undefined || result == 'undefined')?'刚刚':result);
}
// 规则转码
function escapeHTML(val) {
    val = "" + val;
    return val.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, '&quot;').replace(/'/g, "‘").replace(/\(/g, "&#40;").replace(/\&#60;/g, "&lt;").replace(/\&#62;/g, "&gt;").replace(/`/g, "&#96;").replace(/=/g, "＝");
}
function getLength(val) {  
    var str = new String(val);  
    var bytesCount = 0;  
    for (var i = 0 ,n = str.length; i < n; i++) {  
        var c = str.charCodeAt(i);  
        if ((c >= 0x0001 && c <= 0x007e) || (0xff60<=c && c<=0xff9f)) {  
            bytesCount += 1;  
        } else {  
            bytesCount += 2;  
        }  
    }  
    return bytesCount;  
} 
function reBytesStr(str, len) {
    if ((!str && typeof(str) != 'undefined')) {return '';}
    var num = 0;
    var str1 = str;
    var str = '';
    for (var i = 0,lens = str1.length; i < lens; i++) {
        num += ((str1.charCodeAt(i) > 255) ? 2 : 1);
        if (num > len) {
            break;
        } else {
            str = str1.substring(0, i + 1);
        }
    }
    return str;
}
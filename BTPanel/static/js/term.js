function Terms(el,config){
    if(typeof config == "undefined") config = {};
    this.el = el;
    this.id = config.ssh_info.id || '';
    this.bws = null; //websocket对象
    this.route ='/webssh'; // 访问的方法
    this.term =null; //term对象
    this.info =null; // 请求数据
    this.last_body =null;
    this.fontSize =15; //终端字体大小
    this.ssh_info = config.ssh_info;
    this.run();
}
Terms.prototype = {
    // websocket持久化连接
    connect:function(callback){
        var that = this;
        // 判断当前websocket连接是否存在
        if(!this.bws || this.bws.readyState == 3 || this.bws.readyState == 2){
            this.bws = new WebSocket((window.location.protocol === 'http:' ? 'ws://' : 'wss://') + window.location.host + this.route);
            this.bws.addEventListener('message',function(ev){that.on_message(ev)});
            this.bws.addEventListener('close',function(ev){that.on_close(ev)});
            this.bws.addEventListener('error',function(ev){that.on_error(ev)});
            this.bws.addEventListener('open',function(ev){that.on_open(ev)});
            if(callback) callback(this.bws)
        }
    },

    //连接服务器成功
    on_open:function(ws_event){
        this.send(JSON.stringify(this.ssh_info || {}))
        this.term.FitAddon.fit();
        this.resize({cols:this.term.cols, rows:this.term.rows});
    },
    //服务器消息事件
    on_message: function (ws_event){
        result = ws_event.data;
        if(!result) return;
        if ((result.indexOf("@127.0.0.1:") != -1 || result.indexOf("@localhost:") != -1) && result.indexOf('Authentication failed') != -1) {
            this.term.write(result);
            host_trem.localhost_login_form(result);
            this.close();
            return;
        }
        if(result.length > 1 && this.last_body === false){
            this.last_body = true;
        }
        this.term.write(result);
        this.set_term_icon(1);
        if (result == '\r\n登出\r\n' || result == '登出\r\n' || result == '\r\nlogout\r\n' || result == 'logout\r\n') {
            // setTimeout(function () {
                // layer.close(Term.term_box);
            // }, 500);
            this.close();
            this.bws = null;
            
        }
    },
    //websocket关闭事件
    on_close: function (ws_event) {
        this.set_term_icon(0);
        this.bws = null;
    },

    /**
     * @name 设置终端标题状态
     * @author chudong<2020-08-10>
     * @param {number} status 终端状态
     * @return void 
    */
    set_term_icon:function(status){
        var icon_list = ['icon-warning','icon-sucess','icon-info'];
        if(status == 1){
            if($("[data-id='"+ this.id +"']").attr("class").indexOf('active') == -1){
                status = 2;
            }
        }
        $("[data-id='"+ this.id +"']").find('.icon').removeAttr('class').addClass(icon_list[status]+' icon');
        if(status == 2){
            that = this;
            setTimeout(function(){
                $("[data-id='"+ that.id +"']").find('.icon').removeAttr('class').addClass(icon_list[1]+' icon');
            },200);
        }
    },
    //websocket错误事件
    on_error: function (ws_event) {
        if(ws_event.target.readyState === 3){
            // var msg = '错误: 无法创建WebSocket连接，请在面板设置页面关闭【开发者模式】';
            // layer.msg(msg,{time:5000})
            // if(Term.state === 3) return
            // Term.term.write(msg)
            // Term.state = 3;
        }else{
            console.log(ws_event)
        }
    },
    //发送数据
    //@param event 唯一事件名称
    //@param data 发送的数据
    //@param callback 服务器返回结果时回调的函数,运行完后将被回收
    send: function (data, num) {
        var that = this;
        //如果没有连接，则尝试连接服务器
        if (!this.bws || this.bws.readyState == 3 || this.bws.readyState == 2) {
            this.connect();
        }

        //判断当前连接状态,如果!=1，则100ms后尝试重新发送
        if (this.bws.readyState === 1) {
            this.bws.send(data);
        } else {
			if(this.state === 3) return;
            if (!num) num = 0;
            if (num < 5) {
                num++;
                setTimeout(function () { that.send(data, num++); }, 100)
            }
        }
    },
    //关闭连接
    close: function () {
        this.bws.close();
        this.set_term_icon(0);
    },
    resize: function (size){
        if(this.bws){
            size['resize'] = 1;
            this.send(JSON.stringify(size));
            this.term
        }
        
    },
    run: function (ssh_info) {
        var that = this;
        this.term = new Terminal({fontSize:this.fontSize, screenKeys: true, useStyle: true });
        this.term.setOption('cursorBlink', true);
        this.last_body = false;
        this.term.open($(this.el)[0]);

        this.term.FitAddon = new FitAddon.FitAddon();
        this.term.loadAddon(this.term.FitAddon);
        this.term.WebLinksAddon = new WebLinksAddon.WebLinksAddon()
        this.term.loadAddon(this.term.WebLinksAddon)
        if (ssh_info) this.ssh_info = ssh_info
        this.connect();
        that.term.onData(function (data) {
            try {
                that.bws.send(data)
            } catch (e) {
                that.term.write('\r\n连接丢失,正在尝试重新连接!\r\n')
                that.connect()
            }
        });
        this.term.focus();
    }
}
var host_trem = {
    host_term:{},
    host_list:[],
    command_list:[],
    sort_time:null,
    is_full:false,
    command_form:{
        title:'',
        shell:'',
    },
    host_form:{
        host:'',
        port:'22', //默认端口22
        username:'root',
        password:'',
        pkey: '',
        ps: ''  
    },
    init:function(){
        var that = this;
        Object.defineProperty(host_trem,'is_full',{
            get:function(val){
                return val;
            },
            set:function(newValue) {
                if(newValue){
                    $('body').addClass('full_term_view');
                    var win = $(window)[0],win_width = win.innerHeight,win_height = win.innerHeight;
                    $('.main-content .safe').height(win_height);
                    $('#term_box_view,.term_tootls').height(win_height);
                    $('.tootls_host_list').height((win_height - 80) * .75);
                    $('.tootls_commonly_list').height((win_height - 80) * .25);
                    $('.tab_tootls .glyphicon').removeClass('glyphicon-resize-full').addClass('glyphicon-resize-small').attr('title','退出全屏');
                }else{
                    $('body').removeClass('full_term_view');
                    $('.tab_tootls .glyphicon').removeClass('glyphicon-resize-small').addClass('glyphicon-resize-full').attr('title','全屏显示');
                }
            }
        });
        document.onkeydown = function(e){
            e = e || window.event;
            if ((e.metaKey && e.keyCode == 82) || e.keyCode == 116){
                return false;
            }
            if(that.is_full && e.keyCode == 27){
                return false;
            }
        }
        $(window).resize(function(ev){
            var win = $(window)[0],win_width = win.innerHeight,win_height = win.innerHeight,host_commonly = win_height - 185;
            if(that.isFullScreen()){
                $('.main-content .safe').height(win_height);
                $('#term_box_view,.term_tootls').height(win_height);
                $('.tootls_host_list').height((win_height - 80) * .75);
                $('.tootls_commonly_list').height((win_height - 80) * .25);
            }else{
                $('.main-content .safe').height(win_height - 105);
                $('#term_box_view,.term_tootls').height(win_height - 105);
                $('.tootls_host_list').height(host_commonly * .75);
                $('.tootls_commonly_list').height(host_commonly * .25);
            }
            var id = $('.term_item_tab .active').data('id');
            var item_term = that.host_term[id].term;
            item_term.FitAddon.fit();
            that.host_term[id].resize({cols:item_term.cols, rows:item_term.rows});
        });
        $('.tab_tootls').on('click','.glyphicon-resize-full',function(){
            $(this).removeClass('glyphicon-resize-full').addClass('glyphicon-resize-small').attr('title','退出全屏');
            $('body').addClass('full_term_view');
            that.requestFullScreen();
        });
        $('.tab_tootls').on('click','.glyphicon-resize-small',function(){
            $(this).removeClass('glyphicon-resize-small').addClass('glyphicon-resize-full').attr('title','全屏显示');
            $('body').removeClass('full_term_view');
            that.exitFullscreen();
        });


        $(document).ready(function (e) {
            var win = $(window)[0],win_width = win.innerHeight,win_height = win.innerHeight,host_commonly = win_height - 185;
            $('.main-content .safe').height(win_height - 105);
            $('#term_box_view,.term_tootls').height(win_height - 105);
            $('.tootls_host_list').height(host_commonly * .75);
            $('.tootls_commonly_list').height(host_commonly * .25);
            that.open_term_view();
        });

        // 添加服务器信息
        $('.addServer').on('click',function(){
            that.editor_host_view();
        });

        // 切换服务器终端视图
        $('.term_item_tab .list').on('click','span.item',function(ev){
            var index = $(this).index(),data = $(this).data();
            if($(this).hasClass('addServer')){

            }else if($(this).hasClass('tab_tootls')){

            }else{
                $(this).addClass('active').siblings().removeClass('active');
                $('.term_content_tab .term_item:eq('+ index +')').addClass('active').siblings().removeClass('active');
                that.host_term[data.id];
                var item = that.host_term[data.id];
                item.term.focus();
                item.term.FitAddon.fit();
                item.resize({cols:item.term.cols, rows:item.term.rows});
            }
            
        });
        
        $('.term_item_tab').on('click','.icon-trem-close',function(){
            var id = $(this).parent().data('id');
            that.remove_term_view(id);
        })

        // 服务器列表工具箱
        $('.tootls_host_list').on('click','li .tootls span',function(ev){
            var item = $(this).parent().parent(),host = item.data('host'),index = item.data('index');
            if(!$(this).index()){
                that.get_host_find(host,function(rdata){
                    if(rdata.status === false){
                        bt.msg(rdata);
                        return false;
                    }
                    that.editor_host_view({
                        form:rdata,
                        config: {btn: '保存', title: '编辑服务器信息【'+ host +'】'}
                    });
                });
            }else{
                bt.confirm({title:'删除信息',msg:'是否删除服务信息【'+ host +'】，是否继续?',icon:0},function(index){
                    that.remove_host(host,function(rdata){
                        layer.close(index);
                        that.reader_host_list(function(){
                            bt.msg(rdata);
                        });
                    });
                });
            }
            ev.stopPropagation();
        });
        // 服务器列表工具箱
        $('.tootls_commonly_list').on('click','li .tootls span',function(ev){
            var item = $(this).parent().parent(),title = item.data('title'),index = item.data('index');
            if(!$(this).index()){
                that.get_command_find(title,function(rdata){
                    if(rdata.status === false){
                        bt.msg(rdata);
                        return false;
                    }
                    that.editor_command_view({
                        form:rdata,
                        config: {btn: '保存', title: '编辑常用命令信息【'+ title +'】'}
                    });
                });
            }else{
                bt.confirm({title:'删除常用命令',msg:'是否删除常用命令信息【'+ title +'】，是否继续?',icon:0},function(index){
                    that.remove_command(title,function(rdata){
                        layer.close(index);
                        that.reader_command_list(function(){
                            bt.msg(rdata);
                        });
                    });
                });
            }
            ev.stopPropagation();
        });
        // 右键菜单
        $('.term_item_tab .list').on('mousedown','.item',function(ev){
            if(ev.which == 3){
                that.reader_right_menu({
                    el:$(this),
                    position:[ev.clientX,ev.clientY],
                    list:[
                        [{title:'复制会话',event:function(el,data){
                            that.open_term_view(that.host_term[data.id].ssh_info);
                        }}],
                        [{title:'关闭会话',event:function(el,data){
                            that.remove_term_view(data.id);
                        }},
                        {title:'关闭到右侧',event:function(el,data){
                            bt.confirm({msg:'关闭SSH会话后，当前命令行会话正在执行的命令可能被中止，确定关闭吗？',title: "确定要关闭SSH会话吗？"},function(index){
                                that.remove_term_right_view(data.id);
                                layer.close(index);
                            });
                        }},
                        {title:'关闭其他',event:function(el,data){
                            bt.confirm({msg:'关闭SSH会话后，当前命令行会话正在执行的命令可能被中止，确定关闭吗？',title: "确定要关闭SSH会话吗？"},function(index){
                                that.remove_term_other_view(data.id);
                                layer.close(index);
                            });
                        }}]
                    ]
                },function(){
                    $(document).unbind('contextmenu');
                });
                ev.preventDefault();
                $(document).contextmenu(function(e){
                    e.preventDefault();
                });
            }
        });

        // 添加服务器和常用秘钥
        $('.term_tootls .tootls_tab a').click(function(){
            var type = $(this).data('type');
            if(type == 'host'){
                that.editor_host_view();
            }else{
                that.editor_command_view();
            }
        });
        // var clientX = null,clientY = null;
        // $('.tootls_host_list').on('mousedown','li',function(e){
        //     clientX = e.clientX,clientY = e.clientY;
        // })
        // 模拟触发服务器列表点击事件
        // $('.tootls_host_list').on('mouseup','li',function(e){
        //     if(e.button == 0){
        //         if(clientX == e.clientX && clientY == e.clientY){
                    
        //         }
        //     }
        // });

        $('.tootls_host_list').on('click','li',function(e){
            var index = $(this).index(),host = $(this).data('host');
            $(this).find('i').addClass('active');
            if($('.item[data-host="'+ host +'"]').length > 0){
                layer.msg('如需多会话窗口，请右键终端标题复制会话!',{icon:0,time:3000})
            }else{
                that.open_term_view(that.host_list[index]);
            }
        });
        // 服务器列表拖动
        $('.tootls_host_list').dragsort({
            dragSelector:'li i',
            dragEnd:function(){
                clearTimeout(that.sort_time);
                that.sort_time = setTimeout(function(){
                    var sort_list = {};
                    $('.tootls_host_list li').each(function(index,el){
                        sort_list[$(this).data('host')] = index;
                    });
                    that.set_sort(sort_list,function(rdata){
                        if(!rdata.status){
                            bt.msg(rdata);
                        }
                    });
                },500);
            },
            dragBetween:false,
        });
        
        this.reader_host_list();
        this.reader_command_list();
    },
    // 判断全屏状态
    isFullScreen:function() {
        var is_full = document.isFullScreen || document.mozIsFullScreen || document.webkitIsFullScreen;
        this.is_full = is_full
        return is_full;
    },

    // 进入全屏
    requestFullScreen:function(element){
        if(element == undefined) element = document.documentElement;
        // 判断各种浏览器，找到正确的方法
        var requestMethod = element.requestFullScreen || //W3C
            element.webkitRequestFullScreen || //FireFox
            element.mozRequestFullScreen || //Chrome等
            element.msRequestFullScreen; //IE11
        if (requestMethod) {
            requestMethod.call(element);
        } else if (typeof window.ActiveXObject !== "undefined") { //for Internet Explorer
            var wscript = new ActiveXObject("WScript.Shell");
            if (wscript !== null) {
                wscript.SendKeys("{F11}");
            }
        }
        this.is_full = true;
    },
    // 退出全屏
    exitFullscreen:function(element) {
        if(element == undefined) element = document.documentElement;
        // 判断各种浏览器，找到正确的方法
        var exitMethod = document.exitFullscreen || //W3C
            document.mozCancelFullScreen || //FireFox
            document.webkitExitFullscreen || //Chrome等
            document.webkitExitFullscreen; //IE11
        if (exitMethod) {
            exitMethod.call(document);
        } else if (typeof window.ActiveXObject !== "undefined") { //for Internet Explorer
            var wscript = new ActiveXObject("WScript.Shell");
            if (wscript !== null) {
                wscript.SendKeys("{F11}");
            }
        }
        this.is_full = false;
    },
    
    /**
     * @name 本地服务器登录表单 
     * @author chudong<2020-08-10>
     * @return void
    */
    localhost_login_form:function(result){

        var that = this,form = $(this.render_template({html:host_form_view.innerHTML,data:{form:$.extend(that.host_form,{host:'127.0.0.1'})}})),id = $('.localhost_item').data('id')
        form.find('.ssh_ps_tips').remove();
        form.prepend('<div class="localhost-form-title"><i class="localhost-form_tip"></i><span style="vertical-align: middle;">无法自动认证，请填写本地服务器的登录信息!</span></div>');
        form.append('<button type="submit" class="btn btn-sm btn-success">登录</button>');
        $('#'+id).append('<div class="localhost-form-shade"><div class="localhost-form-view bt-form-2x">'+ form[0].innerHTML +'</div></div>');
        if(result){
            if(result.indexOf('@127.0.0.1') != -1){
                var user = result.split('@')[0].split(',')[1];
                var port = result.split('1:')[1]
                $("input[name='username']").val(user);
                $("input[name='port']").val(port);
                
            }
            
        }
        $('.auth_type_checkbox').click(function(){
            var index = $(this).index();
            $(this).addClass('btn-success').removeClass('btn-default').siblings().removeClass('btn-success').addClass('btn-default')
            switch(index){
                case 0:
                    $('.c_password_view').addClass('show').removeClass('hidden');
                    $('.c_pkey_view').addClass('hidden').removeClass('show').find('input').val('');
                break;
                case 1:
                    $('.c_password_view').addClass('hidden').removeClass('show').find('input').val('');
                    $('.c_pkey_view').addClass('show').removeClass('hidden');
                break;
            }
        });
        $('.localhost-form-view > button').click(function(){
            var form = {};
            $('.localhost-form-view input,.localhost-form-view textarea').each(function(index,el){
                var name = $(this).attr('name'),value = $(this).val();
                form[name] = value;
                switch(name){
                    case 'port':
                        if(!bt.check_port(value)){
                            bt.msg({status:false,msg:'服务器端口格式错误！'});
                            return false;
                        }
                    break;
                    case 'username':
                        if(value == ''){
                            bt.msg({status:false,msg:'服务器用户名不能为空!'});
                            return false;
                        }
                    break;
                    case 'password':
                        if(value == '' && $('.c_password_view').hasClass('show')){
                            bt.msg({status:false,msg:'服务器密码不能为空!'});
                            return false;
                        }
                    break;   
                    case 'pkey':
                        if(value == '' && $('.c_pkey_view').hasClass('show')){
                            bt.msg({status:false,msg:'服务器秘钥不能为空!'});
                            return false;
                        }
                    break;
                }
            });
            delete form.sort
            form.ps = '本地服务器';
            that.create_host(form,function(res){
                bt.msg(res);
                if(res.status){
                    bt.msg({status:true,msg:'登录成功！'});
                    $('.localhost_item .icon-trem-close').click();
                    that.open_term_view();
                }
            });
        });
        $('.localhost-form-view [name="password"]').keyup(function(e){
            if(e.keyCode == 13){
                $('.localhost-form-view > button').click();
            }
        }).focus();
    },
    
    reader_right_menu:function(config,callback){
        var menu = $('<ul class="menu_right_list" id="term_title_menu"></ul>').css({'top':config.position[1],'left':config.position[0]}),html = '';
        bt.each(config.list,function(index,item){
            bt.each(item,function(indexs,items){
                (function(items){
                    menu.append($('<li></li>').append($('<a href="javascript:;" title="'+ items.title +'">'+ items.title +'</a>').click(function(e){
                        if(items.event) items.event(config.el,$(config.el).data())
                        menu.remove();
                        if(callback) callback();
                    })));
                }(items));
            });
            if(index != config.list.length - 1){
                menu.append('<li class="split_line"></li>');
            }
        });
        if(!$('#term_title_menu').length){
            $('body').append(menu);
        }else{
            $('#term_title_menu').replaceWith(menu);
        }
        $(document).click(function(e){
            menu.remove();
            $(this).unbind('click');
            if(callback) callback();
        })
    },
    /**
     * @name 主机信息添加或编辑
     * @author chudong<2020-08-10>
     * @param {Objeact} obj 需要编辑的form数据,可以为空，为空则添加
     * @return void 
    */
    editor_host_view:function(obj){
        var that = this;
        if (!obj) obj = {form: this.host_form, config: {btn: '提交', title: '添加主机信息'}}
        this.render_template({
            html: host_form_view.innerHTML,
            data: obj
        }, function (html) {
            layer.open({
                type: 1 //Page层类型
                ,area: '510px'
                ,closeBtn: 2
                ,title: obj.config.title
                ,btn: [obj.config.btn, '取消']
                ,content: html
                ,success: function (layers, index){
                    $('.auth_type_checkbox').click(function(){
                        var index = $(this).index();
                        $(this).addClass('btn-success').removeClass('btn-default').siblings().removeClass('btn-success').addClass('btn-default')
                        switch(index){
                            case 0:
                                $('.c_password_view').addClass('show').removeClass('hidden');
                                $('.c_pkey_view').addClass('hidden').removeClass('show').find('input').val('');
                            break;
                            case 1:
                                $('.c_password_view').addClass('hidden').removeClass('show').find('input').val('');
                                $('.c_pkey_view').addClass('show').removeClass('hidden');
                            break;
                        }
                    });

                    $('[name="host"]').on('change',function(){
                        var host_val = $(this).val();
                        if(!host_val) return;

                        var s_host,s_port,s_username,s_password;
                        s_host = host_val;
                        if(host_val.indexOf('@') != -1){
                            var tmp = host_val.split('@')
                            s_host = tmp[1]
                            s_username = tmp[0]

                            if (s_username.indexOf(':') != -1){
                                var tmp = s_username.split(':')
                                s_username = tmp[0]
                                s_password = tmp[1]
                            }
                        }
                        if(s_host.indexOf(':')!=-1){
                            var tmp = s_host.split(':')
                            s_host = tmp[0]
                            s_port = tmp[1]
                        }

                        if(s_host) {
                            $(this).val(s_host);
                            $('[name="ps"]').val(s_host);
                        }
                        if(s_port) $('[name="port"]').val(s_port);
                        if(s_username) $('[name="username"]').val(s_username);
                        if(s_password) $('[name="password"]').val(s_password);
                    });

                    $('[name="host"]').on('input',function(){
                        $('[name="ps"]').val($(this).val());
                    });
                    $('[name="password"],[name="ps"]').keyup(function(e){
                        if(e.keyCode === 13){
                            $('#layui-layer'+ index +' .layui-layer-btn0').click();
                        }
                    });
                },
                yes:function(indexs,layero){
                    var form = {};
                    $('.bt-form input,.bt-form textarea').each(function(index,el){
                        var name = $(this).attr('name'),value = $(this).val();
                        form[name] = value;
                        switch(name){
                            case 'port':
                                if(!bt.check_port(value)){
                                    bt.msg({status:false,msg:'服务器端口格式错误！'});
                                    return false;
                                }
                            break;
                            case 'username':
                                if(value == ''){
                                    bt.msg({status:false,msg:'服务器用户名不能为空!'});
                                    return false;
                                }
                            break;
                            case 'password':
                                if(value == '' && $('.c_password_view').hasClass('show')){
                                    bt.msg({status:false,msg:'服务器密码不能为空!'});
                                    return false;
                                }
                            break;   
                            case 'pkey':
                                if(value == '' && $('.c_pkey_view').hasClass('show')){
                                    bt.msg({status:false,msg:'服务器秘钥不能为空!'});
                                    return false;
                                }
                            break;
                        }
                    });
                    if(!obj.form.sort){
                        delete form.sort;
                        that.create_host(form,function(res){
                            if(res.status){
                                that.open_term_view(form);
                                layer.close(indexs)
                                that.reader_host_list(function(){
                                    bt.msg(res);
                                })
                            }
                        });
                    }else{
                        form.new_host = form.host;
                        form.host = obj.form.host;
                        that.modify_host(form,function(res){
                            if(res.status){
                                layer.close(indexs)
                                that.reader_host_list(function(){
                                    bt.msg(res);
                                })
                            }
                        })
                    }
                }
            });
        });
    },

    /**
     * @name 常用信息添加或编辑
     * @author chudong<2020-08-10>
     * @param {Objeact} obj 需要编辑的form数据,可以为空，为空则添加
     * @return void 
    */
    editor_command_view:function(obj){
        var that = this;
        if (!obj) obj = {form: this.command_form, config: {btn: '提交', title: '添加常用命令信息'}};
        this.render_template({
            html: shell_form_view.innerHTML,
            data: obj
        }, function (html) {
            layer.open({
                type: 1 //Page层类型
                ,area: '510px'
                ,closeBtn: 2
                ,title: obj.config.title
                ,btn: [obj.config.btn, '取消']
                ,content: html
                ,yes: function (indexs,layero){
                    var shell = $('[name="shell"]').val(),title = $('[name="title"]').val();
                    if(title == ''){
                        bt.msg({status:false,msg:'常用命令描述不能为空！'});
                        return false;
                    }
                    if(shell == ''){
                        bt.msg({status:false,msg:'常用命令不能为空！'});
                        return false;
                    }

                    if(!obj.form.title){
                        that.create_command({shell:shell,title:title},function(res){
                            if(res.status){
                                layer.close(indexs);
                                that.reader_command_list(function(){
                                    bt.msg(res);
                                });
                            }
                        });
                    }else{
                        that.modify_command({new_title:title,title:obj.form.title,shell:shell},function(res){
                            if(res.status){
                                layer.close(indexs);
                                that.reader_command_list(function(){
                                    bt.msg(res);
                                });
                            }
                        });
                    }
                },

            });
        });
    },
    /**
     * @name 设置终端标题状态
     * @author chudong<2020-08-10>
     * @param {String} id 终端ID
     * @param {number} status 终端状态
     * @return void 
    */
    set_term_icon:function(id,status){
        var icon_list = ['icon-warning','icon-sucess','icon-info'];
        $("[data-id='"+ id +"']").find('.icon').removeAttr('class').addClass(icon_list[status]+' icon');
    },
    /**
     * @name 打开终端显示视图
     * @author chudong<2020-08-10>
     * @param {Objeact} info 终端数据 {
     *  ps:已添加的备注,
     *  host:已添加的服务器ip
     * }
     * @return void 
    */
    open_term_view:function(info){
        if(typeof info  === "undefined") info = {host:'127.0.0.1',ps:'本地服务器'}
        var random = bt.get_random(9),tab_content = $('.term_content_tab'),item_list = $('.term_item_tab .list');
        tab_content.find('.term_item').removeClass('active').siblings().removeClass('active');
        tab_content.append('<div class="term_item active" id="'+ random +'" data-host="'+ info.host +'"></div>');
        item_list.find('.item').removeClass('active');
        item_list.append('<span class="active item '+ (info.host =='127.0.0.1'?'localhost_item':'') +'" data-host="'+ info.host +'" data-id="'+ random +'"><i class="icon icon-sucess"></i><div class="content"><span>'+ info.ps +'</span></div><span class="icon-trem-close"></span></span>');
        this.host_term[random] = new Terms('#'+random,{ssh_info:{host:info.host,ps:info.ps,id:random}});
    },
    /**
     * @name 关闭终端显示视图
     * @author chudong<2020-08-10>
     * @param {String} id  终端id
     * @return void 
    */
    remove_term_view:function(id){
        var item  = $('[data-id="'+ id +'"]'),next = item.next(),prev = item.prev();
        $('#'+id).remove();
        item.remove();
        try {
            this.host_term[id].bws.close();
        } catch (error) {
        }
        delete this.host_term[id];
        if(item.hasClass('active')){
            if(next.length > 0){
                next.click();
            }else{
                prev.click();
            }
        }
    },
        /**
     * @name 关闭选中右侧终端显示视图
     * @author chudong<2020-08-10>
     * @param {String} id  终端id
     * @return void 
    */
    remove_term_right_view:function(id){
        var arry = [],item  = $('[data-id="'+ id +'"]'),nextAll = item.nextAll(),that = this;
        if(!nextAll.length){
            return false;
        }
        nextAll.each(function(index,el){
            var data = $(this).data();
            try {
                that.host_term[data.id].bws.close();
            } catch (error) {
            }
            delete that.host_term[data.id];
        });
        nextAll.remove();
        item.addClass('active');
        $('#'+id).addClass('active').nextAll().remove();
    },
    /**
     * @name 关闭其他终端显示视图
     * @author chudong<2020-08-10>
     * @param {String} id  终端id
     * @return void 
    */
    remove_term_other_view:function(id){
        var arry = [],item  = $('[data-id="'+ id +'"]'),siblings = item.siblings(),that = this;
        if(!siblings.length){
            return false;
        }
        siblings.each(function(index,el){
            var data = $(this).data();
            try {
                that.host_term[data.id].bws.close();
            } catch (error) {
            }
            delete that.host_term[data.id];
        });
        siblings.remove();
        item.addClass('active');
        $('#'+id).addClass('active').siblings().remove();
    },
        /**
     * @name 渲染常用命令列表
     * @author chudong<2020-08-10>
     * @param {Objeact} callback 回调函数，回调参数1:当前请求内容
     * @return void 
    */
    reader_command_list:function(callback){
        var that = this,html = '';
        this.get_command_list(function(rdata){
            bt.each(rdata,function(index,item){
                html += '<li data-title="'+ item.title +'" data-index="'+ index +'" data-clipboard-text="'+ item.shell +'"><i></i><span>'+ item.title +'</span><span class="tootls">'+
                    '<span class="glyphicon glyphicon-edit" aria-hidden="true" title="编辑常用命令信息"></span>'+
                    '<span class="glyphicon glyphicon-trash" aria-hidden="true" title="删除常用命令信息"></span>'+
                '</span></li>';
            });
            $('.tootls_commonly_list').html(html);
            var clipboard = new ClipboardJS('.tootls_commonly_list li');
            clipboard.on('success', function(e) {
                layer.msg('复制成功！',{icon:1});
                e.clearSelection();
            });

            clipboard.on('error', function(e) {
                console.error('Action:', e.action);
                console.error('Trigger:', e.trigger);
            });
            that.command_list = rdata;
            if(callback) callback(rdata)
        });
    },



    /**
     * @name 渲染主机视图列表
     * @author chudong<2020-08-10>
     * @param {Objeact} callback 回调函数，回调参数1:当前请求内容
     * @return void 
    */
    reader_host_list:function(callback){
        var that = this,html = '';
        this.get_host_list(function(rdata){
            bt.each(rdata,function(index,item){
                html += '<li data-host="'+ item.host +'" data-index="'+ index +'"><i></i><span>'+ (item.ps == item.host?item.ps:(item.ps +'【'+ item.host +'】')) +'</span><span class="tootls">'+
                    '<span class="glyphicon glyphicon-edit" aria-hidden="true" title="编辑服务器信息"></span>'+
                    '<span class="glyphicon glyphicon-trash" aria-hidden="true" title="删除服务器信息"></span>'+
                '</span></li>';
            });
            $('.tootls_host_list').html(html);
            that.host_list = rdata;
            if(callback) callback()
        });
    },
    /**
     * @name 获取host列表
     * @author chudong<2020-08-010>
     * @param {Objeact} callback 回调函数，回调参数1:当前请求内容
     * @return void 
     */
    get_host_list:function(callback){
        var loadT = bt.load('正在获取服务器列表，请稍后...');
        this.post('get_host_list',{},function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },

    /**
     * @name 获取指定host信息
     * @author hwliang<2020-08-07>
     * @param host string host地址 
     * @return void
     */
    get_host_find:function(host,callback){
        var loadT = bt.load('正在获取指定服务器信息，请稍后...');
        this.post('get_host_find',{host:host},function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },


    /**
     * @name 创建新的host信息
     * @author hwliang<2020-08-07>
     * @param ssh_info array ssh信息对象 {
     *      host: 主机地址,
            port: 端口
            ps: 备注
            username: 用户名
            password: 密码
            pkey: 密钥(如果不为空，将使用密钥连接)
     * }
     * @return void
     */
     create_host:function(ssh_info,callback){
        var loadT = bt.load('正在添加服务器信息，请稍后...');
        this.post('create_host',ssh_info,function(rdata){
            loadT.close();
            if(!rdata.status){
                bt.msg(rdata);
                return false;
            }
            if(callback) callback(rdata);
        });
    },

    /**
     * @name 修改host信息
     * @author hwliang<2020-08-07>
     * @param ssh_info array ssh信息对象 {
     *      host: 主机地址,
            port: 端口
            ps: 备注
            sort: 排序(可选，默认0)
            username: 用户名
            password: 密码
            pkey: 密钥(如果不为空，将使用密钥连接)
     * }
     * @return void
     */
     modify_host:function(ssh_info,callback){
        var loadT = bt.load('正在修改指定服务器信息，请稍后...');
        this.post('modify_host',ssh_info,function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },


    /**
     * @name 删除host信息
     * @author hwliang<2020-08-07>
     * @param host string host地址 
     * @return void
     */
     remove_host:function(host,callback){
        var loadT = bt.load('正在删除指定服务器信息，请稍后...');
        this.post('remove_host',{host:host},function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },


    /**
     * @name 设置host排序(使用降序)
     * @author hwliang<2020-08-07>
     * @param sort_list array 排序对象{
     *      "127.0.0.1":3,
     *      "192.168.1.254":2
     * } 
     * @return void
     */
     set_sort:function(sort_list,callabck){
        this.post('set_sort',{sort_list:JSON.stringify(sort_list)},function(rdata){
            if(callabck) callabck(rdata);
        });
    },

    
    /**
     * @name 获取常用命令列表
     * @author hwliang<2020-08-08>
     * @return void
     */
    get_command_list: function(callback){
        var loadT = bt.load('正在获取常用命令列表，请稍后...');
        this.post('get_command_list',{},function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },

    /**
     * @name 创建常用命令
     * @author hwliang<2020-08-08>
     * @param {title} string 命令标题
     * @parma {shell} string 命令文本
     * @return void
     */
    create_command: function(obj,callback){
        var loadT = bt.load('正在创建常用命令，请稍后...');
        this.post('create_command',obj,function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },


    /**
     * @name 获取指定常用命令
     * @author hwliang<2020-08-08>
     * @param {title} string 命令标题
     * @return void
     */
    get_command_find: function(title,callback){
        var loadT = bt.load('正在获取指定常用命令数据，请稍后...');
        this.post('get_command_find',{title:title},function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },

    /**
     * @name 修改常用命令
     * @author hwliang<2020-08-08>
     * @param {title} string 命令标题
     * @param {new_title} string 新的命令标题
     * @parma {shell} string 命令文本
     * @return void
     */
    modify_command: function(obj,callback){
        var loadT = bt.load('正在修改指定常用命令，请稍后...');
        this.post('modify_command',obj,function(rdata){
            loadT.close();
            if(callback) callback(rdata);
        });
    },

    /**
     * @name 删除指定常用命令
     * @author hwliang<2020-08-08>
     * @param {title} string 命令标题
     * @return void
     */
    remove_command: function(title,callback){
        var loadT = bt.load('正在删除指定常用命令，请稍后...');
        this.post('remove_command',{title:title},function(rdata){
            loadT.close();
            // console.log(rdata)
            if(callback) callback(rdata);
        });
    },


    /**
     * @name 请求到后端
     * @author hwliang<2020-08-07>
     * @param fun_name string 要访问的方法名称
     * @param pdata array POST数据
     * @param callback function 回调函数 
     * @return void
     */
    post:function(fun_name,pdata,callback){
        bt.send(fun_name,'xterm/'+fun_name,pdata,callback);
    },

    /**
     * @author chudong<2020-08-08>
     * @param {Object} obj  需要渲染的配置对象
     * @param {*} callback  渲染完成的回调方法
     */
    render_template:function(obj, callback) {
        if (!obj.html) return '缺少模板HTML';
        var re = /<%([^%>]+)?%>/g, reExp = /(^( )?(if|for|else|switch|case|break|{|}))(.*)?/g, code = 'var r=[];\n',
            cursor = 0;
        var add = function (line, js) {
            js ? (code += line.match(reExp) ? line + '\n' : 'r.push(' + line + ');\n') :
                (code += line != '' ? 'r.push("' + line.replace(/"/g, '\\"') + '");\n' : '');
            return add;
        }
        while (match = re.exec(obj.html)) {
            add(obj.html.slice(cursor, match.index))(match[1], true);
            cursor = match.index + match[0].length;
        }
        add(obj.html.substr(cursor, obj.html.length - cursor));
        code += 'return r.join("");';
        if (callback) {
            callback(new Function(code.replace(/[\r\t\n]/g, '')).apply(obj.data));
        } else {
            return new Function(code.replace(/[\r\t\n]/g, '')).apply(obj.data);
        }
    }
}
host_trem.init();
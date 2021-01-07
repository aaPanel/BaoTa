function show_force_bind(){
    layer.open({
        type: 1,
        title: '绑定宝塔官网账号',
        area: ['420px', '400px'],
        closeBtn: 2,
        shadeClose: false,
        content: '<div class="libLogin pd20">\
                <div class="bt-form text-center">\
                    <div class="line mb15">\
                        <p>恭喜您，宝塔面板已经安装成功。 </p>\
                        <h3 class="c2 f16 text-center mtb20">绑定宝塔官网账号，即可开始使用<a href="javascript:;" class="bind_ps bt-ico-ask">?</a></h3>\
                    </div>\
                    <div class="line"><input class="bt-input-text" name="username2" type="text" placeholder="手机" id="p1"></div>\
                    <div class="line"><input autocomplete="new-password" class="bt-input-text" type="password" name="password2"  placeholder="密码" id="p2"></div>\
                    <div class="line" style="margin-top: 15px;"><input class="login-button" value="登录" type="button" ></div>\
                    <p class="text-right"><a class="btlink" href="https://www.bt.cn/register.html" target="_blank">未有账号，免费注册</a></p>\
                </div>\
            </div>',
        success: function () {
            $('.login-button').click(function () {
                p1 = $("#p1").val();
                p2 = $("#p2").val();
                var loadT = bt.load(lan.config.token_get);
                bt.send('GetToken', 'ssl/GetToken', "username=" + p1 + "&password=" + p2, function (rdata) {
                    loadT.close();
                    bt.msg(rdata);
                    if (rdata.status) {
                        window.location.reload();
                    }
                })
            });

            $('.libLogin input[type=password]').keyup(function (e) {
                if (e.keyCode == 13) {
                    $('.login-button').click();
                }
            });

            var time = '';
            $('.bind_ps').hover(function () {    
                var _that = $(this);
                time = setTimeout(function () {
                    layer.tips('宝塔面板许多功能都依赖于官网，绑定仅限于为您提供更好的面板服务体验，不涉及您服务器任何敏感信息，请放心使用。', _that, { tips: [1, '#20a53a'], time: 0 })
                }, 500)
            }, function () {
                clearTimeout(time)
                layer.closeAll('tips');
            })
        },
        cancel: function () {
            layer.alert('<ul class="help-info-text" style="margin-top:0px;">\
            <li>为了您能更好的体验面板功能，请先绑定宝塔账号；</li>\
            <li>绑定帐号没有接管服务器的功能权限，请放心使用；</li>\
            <li>帐号绑定过程中遇到问题请联系客服处理；</li>\
            <li>客服QQ：800176556，客服电话：0769-23030556</li>\
            </ul>', {btn:'我已了解', title:'绑定提醒',area:'500px'}, function(index){
			  layer.close(index);
			});
			return false; 
        }
    });
}

if (bind_user == 'True') {
    show_force_bind();
}


$("select[name='network-io']").change(function(){
    var net_key = $(this).val();
    if(net_key == 'all') net_key = '';
    bt.set_cookie('network_io_key',net_key);
});



var interval_stop = false;
var index = {
    warning_list:[],
    warning_num:0,
    interval: {
        limit: 10,
        count: 0,
        task_id: 0,
        start: function () {
            var _this = this;
            _this.count = 0;
            _this.task_id = setInterval(function () {
                if (_this.count >= _this.limit) {
                    _this.reload();
                    return;
                }
                _this.count++;
                if (!interval_stop) index.get_data_info();
            }, 3000)
        },
        reload: function () {
            var _this = this;
            if (_this) clearInterval(_this.task_id);
            _this.start();
        }
    },
    net: {
        table: null,
        data: {
            uData: [],
            dData: [],
            aData: []
        },
        init: function () {
            //流量图表
            index.net.table = echarts.init(document.getElementById('NetImg'));
            var obj = {};
            obj.dataZoom = [];
            obj.unit = lan.index.unit + ':Kb/s';
            obj.tData = index.net.data.aData;

            obj.list = [];
            obj.list.push({ name: lan.index.net_up, data: index.net.data.uData, circle: 'circle', itemStyle: { normal: { color: '#f7b851' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(255, 140, 0,0.5)' }, { offset: 1, color: 'rgba(255, 140, 0,0.8)' }], false) } }, lineStyle: { normal: { width: 1, color: '#aaa' } } });
            obj.list.push({ name: lan.index.net_down, data: index.net.data.dData, circle: 'circle', itemStyle: { normal: { color: '#52a9ff' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30, 144, 255,0.5)' }, { offset: 1, color: 'rgba(30, 144, 255,0.8)' }], false) } }, lineStyle: { normal: { width: 1, color: '#aaa' } } });
            option = bt.control.format_option(obj)

            index.net.table.setOption(option);
            window.addEventListener("resize", function () {
                index.net.table.resize();
            });
        },
        add: function (up, down) {
            var _net = this;
            var limit = 8;
            var d = new Date()

            if (_net.data.uData.length >= limit) _net.data.uData.splice(0, 1);
            if (_net.data.dData.length >= limit) _net.data.dData.splice(0, 1);
            if (_net.data.aData.length >= limit) _net.data.aData.splice(0, 1);

            _net.data.uData.push(up);
            _net.data.dData.push(down);
            _net.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
        }
    },
    mem: {
        status: 1,
        set_status: function (obj, status, val) {
            var _this = this;
            _this.status = status;
            var _div = $('<div><span style="display:none">1</span></div>')
            if (status == 2) {
                obj.find(".mem-re-con").animate({ "top": "-400px", opacity: 0 }); //动画
                var btlen = parseInt(obj.find('.occupy span').html());
                for (var i = 0; i < btlen; i++) {
                    setTimeout(index.set_val(obj.parents('li'), { usage: btlen - i }), i * 30);
                };
                obj.addClass("mem-action");
                obj.find('.occupy').html(_div.append(lan.index.memre_ok_0 + ' <img src="/static/img/ings.gif">').html());
            }
            else if (status == 1) { //完成
                obj.removeClass('mem-action');
                obj.find('.occupy').removeClass('line').html("<span>" + val + "</span>%");
            }
            else {
                obj.find('.occupy').html(_div.append(status).html());
                if (bt.contains(status, '<br>')) obj.find('.occupy').addClass('line')
            }
        }
    },
    get_init: function () {
        var _this = this;
        // setTimeout(function () { _this.get_disk_list(); }, 10);


        // bt.pub.get_user_info(function (rdata) {
            
        // })

        _this.get_data_info(function (loadbox, rdata) {
            loadbox.find('.cicle').hover(function () {
                var _this = $(this);
                var d = _this.parents('ul').data('data').load;
                layer.tips('最近1分钟平均负载：' + d.one + '</br>最近5分钟平均负载：' + d.five + '</br>最近15分钟平均负载：' + d.fifteen + '', _this, { time: 0, tips: [1, '#999'] });
            }, function () {
                layer.closeAll('tips');
            })
            $('.cpubox').find('.cicle').hover(function () {
                var _this = $(this);
                var d = _this.parents('ul').data('data').cpu;
                var crs = '';
                var n1 = 0;
                for (var i = 0; i < d[2].length; i++) {
                    n1++;
                    crs += 'CPU-' + i + ": " + d[2][i] + '%' + (n1 % 2 == 0?'</br>':' | ');
                    
                }
                layer.tips(d[3] + "</br>" + d[5] + "个物理CPU，" + (d[5] * d[4]) + "个物理核心，" + d[1]+"线程</br>"+ crs, _this, { time: 0, tips: [1, '#999'] });
            }, function () {
                layer.closeAll('tips');
            });

            $(".mem-release").hover(function () {
                $(this).addClass("shine_green");
                if (!($(this).hasClass("mem-action"))) {
                    $(this).find(".mem-re-min").hide();
                    $(this).find(".occupy").css({ "color": "#d2edd8" });
                    $(this).find(".mem-re-con").css({ "display": "block" });
                    $(this).find(".mem-re-con").animate({ "top": "0", opacity: 1 });
                }
				$(this).next().hide();
            }, function () {
                if (!($(this).hasClass("mem-action"))) {
                    $(this).find(".mem-re-min").show();
                }
                else {
                    $(this).find(".mem-re-min").hide();
                }
                $(this).removeClass("shine_green");
                $(this).find(".occupy").css({ "color": "#20a53a" });
                $(this).find(".mem-re-con").css({ "top": "15px", opacity: 1, "display": "none" });
				$(this).next().show();
                //$(this).next().html(bt.get_cookie("mem-before"));
            }).click(function () {
                var _this = $(this);
                bt.show_confirm('真的要释放内存吗？', '<font style="color:red;">若您的站点处于有大量访问的状态，释放内存可能带来无法预测的后果，您确定现在就释放内存吗？</font>', function () {
                    if (!(_this.hasClass("mem-action"))) {
						_this.next().hide();
						_this.find('.mem-re-min').hide();
                        var data = _this.parents('ul').data('data').mem;
                        index.mem.set_status(_this, 2); //释放中
                        bt.system.re_memory(function (nData) {
                            index.mem.set_status(_this, '释放完成');
							
							_this.next().show();
                            setTimeout(function () {
                                var t = nData.memFree - data.memFree;
                                var m = lan.index.memre_ok_2;
                                if (t > 0) m = lan.index.memre_ok_1 + "<br>" + t + "MB";
                                index.mem.set_status(_this, m);
                            }, 200);
                            setTimeout(function () { 
								index.mem.set_status(_this, 1, (nData.memRealUsed * 100 / nData.memTotal).toFixed(1)); 
								_this.find('.mem-re-min').show();
							}, 1200);
                        })
                    }
                })
            })
            _this.get_server_info(rdata);
            _this.get_disk_list(rdata.disk);
            if(rdata.installed === false) bt.index.rec_install();
            if (rdata.user_info.status) {
                var rdata_data = rdata.user_info.data;
                bt.set_cookie('bt_user_info',JSON.stringify(rdata.user_info));
                $(".bind-user").html(rdata_data.username);
            }
            else {
                $(".bind-weixin a").attr("href", "javascript:;");
                $(".bind-weixin a").click(function () {
                    bt.msg({ msg: '请先绑定宝塔账号!', icon: 2 });
                })
            }
        });
        setTimeout(function () { _this.interval.start(); }, 400)
        setTimeout(function () { _this.get_index_list(); }, 500)
        setTimeout(function () { _this.net.init() }, 600);
        setTimeout(function () { _this.get_warning_list(); }, 700);


        setTimeout(function () {
            bt.system.check_update(function (rdata) {
                //console.log(rdata);
                if (rdata.status !== false) {
                    $('#toUpdate a').html('更新<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
                    $('#toUpdate a').css("position", "relative");

                }
                if (rdata.msg.is_beta === 1) {
                    $('#btversion').prepend('<span style="margin-right:5px;">Beta</span>');
                    $('#btversion').append('<a class="btlink" href="https://www.bt.cn/bbs/forum-39-1.html" target="_blank">  [找Bug奖宝塔币]</a>');
                }

            }, false)
        }, 700)
    },
    get_data_info: function (callback) {
        bt.system.get_net(function (net) {
            var pub_arr = [{ val: 100, color: '#dd2f00' }, { val: 90, color: '#ff9900' }, { val: 70, color: '#20a53a' }, { val: 30, color: '#20a53a' }];
            var load_arr = [{ title: '运行堵塞', val: 100, color: '#dd2f00' }, { title: '运行缓慢', val: 90, color: '#ff9900' }, { title: '运行正常', val: 70, color: '#20a53a' }, { title: '运行流畅', val: 30, color: '#20a53a' }];
            var _cpubox = $('.cpubox'), _membox = $('.membox'), _loadbox = $('.loadbox')

            index.set_val(_cpubox, { usage: net.cpu[0], title: net.cpu[1]+' 核心', items: pub_arr })
            index.set_val(_membox, { usage: (net.mem.memRealUsed * 100 / net.mem.memTotal).toFixed(1), items: pub_arr, title: net.mem.memRealUsed + '/' + net.mem.memTotal + '(MB)' })
            bt.set_cookie('memSize', net.mem.memTotal)

            var _lval = Math.round((net.load.one / net.load.max) * 100);
            if (_lval > 100) _lval = 100;
            index.set_val(_loadbox, { usage: _lval, items: load_arr })
            
            var net_key = bt.get_cookie('network_io_key');
            if(net_key){
                console.log(net_key,net.network[net_key])
                net.up = net.network[net_key].up;
                net.down = net.network[net_key].down;
                net.downTotal = net.network[net_key].downTotal;
                net.upTotal = net.network[net_key].upTotal;
                net.downPackets = net.network[net_key].downPackets;
                net.upPackets = net.network[net_key].upPackets;
                net.downAll = net.network[net_key].downTotal;
                net.upAll = net.network[net_key].upTotal;
            }

            var net_option = '<option value="all">全部</option>';
            $.each(net.network,function(k,v){
                var act = (k == net_key)?'selected':'';
                net_option += '<option value="'+k+'" '+act+'>'+k+'</option>';
            });

            $('select[name="network-io"]').html(net_option);

            _loadbox.parents('ul').data('data', net);
            
            

            //刷新流量
            $("#upSpeed").html(net.up.toFixed(2) + ' KB');
            $("#downSpeed").html(net.down.toFixed(2) + ' KB');
            $("#downAll").html(bt.format_size(net.downTotal));
            $("#upAll").html(bt.format_size(net.upTotal));
            index.net.add(net.up, net.down);
            if (index.net.table) index.net.table.setOption({ xAxis: { data: index.net.data.aData }, series: [{ name: lan.index.net_up, data: index.net.data.uData }, { name: lan.index.net_down, data: index.net.data.dData }] });
            if (callback) callback(_loadbox, net);
        })
    },
    get_server_info: function(info) {
        // bt.system.get_total(function (info) {
        var memFree = info.memTotal - info.memRealUsed;
        if (memFree < 64) {
            $("#messageError").show();
            $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;">' + lan.index.mem_warning + '</span> </p>')
        }

        if (info.isuser > 0) {
            $("#messageError").show();
            $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>' + lan.index.user_warning + '<span class="c7 mr5" title="此安全问题不可忽略，请尽快处理" style="cursor:no-drop"> [不可忽略]</span><a class="btlink" href="javascript:setUserName();"> [立即修改]</a></p>')
        }

        if (info.isport === true) {
            $("#messageError").show();
            $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>当前面板使用的是默认端口[8888]，有安全隐患，请到面板设置中修改面板端口!<span class="c7 mr5" title="此安全问题不可忽略，请尽快处理" style="cursor:no-drop"> [不可忽略]</span><a class="btlink" href="/config"> [立即修改]</a></p>')
        }
        var _system = info.system;
        $("#info").html(_system);
        $("#running").html(info.time);
        if (_system.indexOf("Windows") != -1) {
            $(".ico-system").addClass("ico-windows");
        }
        else if (_system.indexOf("CentOS") != -1) {
            $(".ico-system").addClass("ico-centos");
        }
        else if (_system.indexOf("Ubuntu") != -1) {
            $(".ico-system").addClass("ico-ubuntu");
        }
        else if (_system.indexOf("Debian") != -1) {
            $(".ico-system").addClass("ico-debian");
        }
        else if (_system.indexOf("Fedora") != -1) {
            $(".ico-system").addClass("ico-fedora");
        }
        else {
            $(".ico-system").addClass("ico-linux");
        }
        // })
    },
    get_disk_list:function(rdata) {
        // bt.system.get_disk_list(function (rdata) {
            if (rdata) {
                var data = { table: '#systemInfoList', items: [] };
                for (var i = 0; i < rdata.length; i++) {
                    var item = rdata[i];
                    var obj = {};
                    obj.name = item.path;
                    obj.title = item.size[1] + '/' + item.size[0];
                    obj.rate = item.size[3].replace('%', '');
                    obj.free = item.size[2];
                    var arr = [];
                    arr.push({ title: '<b>基础信息</b>', value: '' })
                    arr.push({ title: '文件系统', value: item.filesystem })
                    arr.push({ title: '类型', value: item.type })
                    arr.push({ title: '挂载点', value: item.path })
                    arr.push({ title: '<b>Inode信息</b>', value: '' })
                    arr.push({ title: '总数', value: item.inodes[0] })
                    arr.push({ title: '已用', value: item.inodes[1] })
                    arr.push({ title: '可用', value: item.inodes[2] })
                    arr.push({ title: 'Inode使用率', value: item.inodes[3] })
                    arr.push({ title: '<b>容量信息</b>', value: '' })
                    arr.push({ title: '容量', value: item.size[0] })
                    arr.push({ title: '已用', value: item.size[1] })
                    arr.push({ title: '可用', value: item.size[2] })
                    arr.push({ title: '使用率', value: item.size[3] })
                    obj.masks = arr;
                    data.items.push(obj)
                }
                index.render_disk(data);
            }
        // })
    },
    render_disk: function (data) {
        if (data.items.length > 0) {
            var _tab = $(data.table);
            for (var i = 0; i < data.items.length; i++) {
                var item = data.items[i];
                var html = '';
                html += '<li class="col-xs-6 col-sm-3 col-md-3 col-lg-2 mtb20 circle-box text-center diskbox">';
                html += '<h3 class="c9 f15">' + item.name + '</h3>';
                html += '<div class="cicle">';
                html += '<div class="bar bar-left"><div class="bar-left-an bar-an"></div></div>';
                html += '<div class="bar bar-right"><div  class="bar-right-an bar-an"></div></div>';
                html += '<div class="occupy"><span>0</span>%</div>';
                html += '</div>';
                html += '<h4 class="c9 f15">' + item.title + '</h4>';
                html += '</li>';
                var _li = $(html);
                if (item.masks) {
                    var mask = '';
                    for (var j = 0; j < item.masks.length; j++) mask += item.masks[j].title + ': ' + item.masks[j].value + "<br>";
                    _li.data('mask', mask);
                    _li.find('.cicle').hover(function () {
                        var _this = $(this);
                        layer.tips(_this.parent().data('mask'), _this, { time: 0, tips: [1, '#999'] });
                    }, function () {
                        layer.closeAll('tips');
                    })
                }
                var color = '#20a53a';
                if (parseFloat(item.rate) >= 80) color = '#ff9900';
                var size = parseFloat(item.free.substr(0, item.free.length - 1));
                var unit = item.free.substr(item.free.length - 1, 1);
                switch (unit) {
                    case 'G':
                        if (size < 1) color = '#dd2f00';
                        break;
                    case 'T':
                        if (size < 0.1) color = '#dd2f00';
                        break;
                    default:
                        color = '#dd2f00'
                        break;
                }
                index.set_val(_li, { usage: item.rate, color: color })
                _tab.append(_li);
            }
        }
    },
    set_val: function (_li, obj) {
        //obj.usage = parseInt(obj.usage)
        if (obj.usage > 50) {
            setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(45deg)", "transition": "transform 750ms linear" }); }, 10)
            setTimeout(function () { _li.find('.bar-left-an').css({ "transform": "rotate(" + (((obj.usage - 50) / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }); }, 760);
        } else {
            if (parseInt(_li.find('.occupy span').html()) > 50) {
                setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(" + ((obj.usage / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }) }, 760);
                setTimeout(function () { _li.find('.bar-left-an').css({ "transform": "rotate(-135deg)", "transition": "transform 750ms linear" }) }, 10)
            } else {
                setTimeout(function () { _li.find('.bar-right-an').css({ "transform": "rotate(" + ((obj.usage / 100 * 360) - 135) + "deg)", "transition": "transform 750ms linear" }); }, 10)
            }
        }
        if (obj.items) {
            var item = {};
            for (var i = 0; i < obj.items.length; i++) {
                if (obj.usage <= obj.items[i].val) {
                    item = obj.items[i];
                    continue;
                }
                break;
            }
            if (item.title) obj.title = item.title;
            if (item.color) obj.color = item.color;
        }
        if (obj.color) {
            _li.find('.cicle .bar-left-an').css('border-color', 'transparent transparent ' + obj.color + ' ' + obj.color);
            _li.find('.cicle .bar-right-an').css('border-color', obj.color + ' ' + obj.color + ' transparent transparent');
            _li.find('.occupy').css('color', obj.color);
        }
        if (obj.title) _li.find('h4').text(obj.title);
        _li.find('.occupy span').html(obj.usage);
    },
    get_index_list: function () {
        bt.soft.get_index_list(function (rdata) {
            var con = '';
            var icon = '';
            var rlen = rdata.length;
            var clickName = '';
            var setup_length = 0;
            for (var i = 0; i < rlen; i++) {
                if (rdata[i].setup) {
                    setup_length++;
                    if (rdata[i].admin) {
                        clickName = ' onclick="bt.soft.set_lib_config(\'' + rdata[i].name + '\',\'' + rdata[i].title + '\')"';
                    }
                    else {
                        clickName = 'onclick="soft.set_soft_config(\'' + rdata[i].name + '\')"';
                    }
                    var icon = rdata[i].name;
                    if (bt.contains(rdata[i].name, 'php-')) {
                        icon = 'php';
                        rdata[i].version = '';
                    }
                    var status = '';
                    if (rdata[i].status) {
                        status = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>';
                    } else {
                        status = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
                    }
                    con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + rdata[i].name + '">\
							<span class="spanmove"></span>\
							<div '+ clickName + '>\
							<div class="image"><img width="48" src="/static/img/soft_ico/ico-'+ icon + '.png"></div>\
							<div class="sname">'+ rdata[i].title + ' ' + rdata[i].version + status + '</div>\
							</div>\
						</div>'
                }
            }
            $("#indexsoft").html(con);
            //软件位置移动
            var softboxsum = 12;
            var softboxcon = '';
            if (setup_length <= softboxsum) {
                for (var i = 0; i < softboxsum - setup_length; i++) {
                    softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg"></div>'
                }
                $("#indexsoft").append(softboxcon);
            }
            $("#indexsoft").dragsort({ dragSelector: ".spanmove", dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });

            function saveOrder() {
                var data = $("#indexsoft > div").map(function () { return $(this).attr("data-id"); }).get();
                data = data.join('|');
                bt.soft.set_sort_index(data)
            };
        })
    },
    check_update: function () {
    	var _load = bt.load('正在获取更新内容，请稍后...');
        bt.system.check_update(function (rdata) {
        	_load.close();
            if (rdata.status === false) {
                if (!rdata.msg.beta) {
                    bt.msg(rdata);
                    return;
                }
                var loading = bt.open({
                    type: 1,
                    title: '[Linux' + (rdata.msg.is_beta == 1 ? '测试版' : '正式版') + ']-更新版本',
                    area: '520px',
                    shadeClose: false,
                    skin: 'layui-layer-dialog',
                    closeBtn: 2,
                    content: '<div class="setchmod bt-form">\
                                <div class="update_title"><i class="layui-layer-ico layui-layer-ico1"></i><span>恭喜您，当前已经是最新版本</span></div>\
                                <div class="update_version">当前版本：<a href="http://www.bt.cn/bbs/forum.php?mod=viewthread&tid=19376" target="_blank" class="btlink" title="查看当前版本日志">宝塔Linux'+ (rdata.msg.is_beta == 1 ? '测试版 ' + rdata.msg.beta.version : '正式版 ' + rdata.msg.version) + '</a>&nbsp;&nbsp;发布时间：' + (rdata.msg.is_beta == 1 ? rdata.msg.beta.uptime : rdata.msg.uptime) + '</div>\
                                <div class="update_conter">\
                                    <div class="update_tips">'+ (rdata.msg.is_beta != 1 ? '测试版' : '正式版') + '最新版本为&nbsp;' + (rdata.msg.is_beta != 1 ? rdata.msg.beta.version : rdata.msg.version) + '&nbsp;&nbsp;&nbsp;更新时间&nbsp;&nbsp;' + (rdata.msg.is_beta != 1 ? rdata.msg.beta.uptime : rdata.msg.uptime) + '&nbsp;&nbsp;&nbsp;\
                                    '+ (rdata.msg.is_beta !== 1 ? '<span>如需更新测试版请点击<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">查看详情</a></span>' : '<span>如需切换回正式版请点击<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">切换到正式版</a></span>') + '\
                                    '+ (rdata.msg.is_beta !== 1 ? rdata.msg.btb : '') + '\
                                    </div>\
                                </div>\
                                <div class="bt-form-submit-btn">\
                                    <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                    <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="layer.closeAll()">'+ lan.public.know + '</button>\
                                </div>\
                            </div>\
                            <style>\
                                .setchmod{padding-bottom:50px;}\
                                .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}\
                                .update_title .layui-layer-ico{display: block;left: 60px !important;top: 1px !important;}\
                                .update_title span{display: inline-block;color: #333;height: 30px;margin-left: 105px;margin-top: 3px;font-size: 20px;}\
                                .update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}\
                                .update_version{font-size: 12px;margin:15px 0 10px 85px}\
                                .update_logs{margin-bottom:10px;border-bottom:1px solid #ececec;padding-bottom:10px;}\
                                .update_tips{font-size: 13px;color: #666;font-weight: 600;}\
                                .update_tips span{padding-top: 5px;display: block;font-weight: 500;}\
                            </style>'
                });
                return;
            }
            if (rdata.status === true) {
                var result = rdata
                var is_beta = rdata.msg.is_beta
                if (is_beta) {
                    rdata = result.msg.beta
                } else {
                    rdata = result.msg
                }
                var loading = bt.open({
                    type: 1,
                    title: '[Linux' + (is_beta === 1 ? '测试版' : '正式版') + ']-版本更新',
                    area: '520px',
                    shadeClose: false,
                    skin: 'layui-layer-dialog',
                    closeBtn: 2,
                    content: '<div class="setchmod bt-form" style="padding-bottom:50px;">\
                                    <div class="update_title"><i class="layui-layer-ico layui-layer-ico0"></i><span>有新的面板版本更新，是否更新？</span></div>\
                                    <div class="update_conter">\
                                        <div class="update_version">最新版本：<a href="https://www.bt.cn/bbs/forum.php?mod=forumdisplay&fid=36" target="_blank" class="btlink" title="查看版本更新日志">宝塔Linux'+ (is_beta === 1 ? '测试版' : '正式版') + rdata.version + '</a>&nbsp;&nbsp;更新日期：' + (result.msg.is_beta == 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        <div class="update_logs">'+ rdata.updateMsg + '</div>\
                                    </div>\
                                    <div class="update_conter">\
                                        <div class="update_tips">'+ (is_beta !== 1 ? '测试版' : '正式版') + '最新版本为&nbsp;' + (result.msg.is_beta != 1 ? result.msg.beta.version : result.msg.version) + '&nbsp;&nbsp;&nbsp;更新时间&nbsp;&nbsp;' + (is_beta != 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        '+ (is_beta !== 1 ? '<span>如需更新测试版请点击<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">查看详情</a></span>' : '<span>如需切换回正式版请点击<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">切换到正式版</a></span>') + '\
                                    </div>\
                                    <div class="bt-form-submit-btn">\
                                        <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                        <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="index.to_update()" >'+ lan.index.update_go + '</button>\
                                    </div>\
                                </div>\
                                <style>\
                                    .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}.update_title .layui-layer-ico{display: block;left: 60px !important;top: 1px !important;}.update_title span{display: inline-block;color: #333;height: 30px;margin-left: 105px;margin-top: 3px;font-size: 20px;}.update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}.update_version{font-size: 13.5px; margin-bottom: 10px;font-weight: 600;}.update_logs{margin-bottom:10px;}.update_tips{font-size: 13px;color:#666;}.update_conter span{display: block;font-size:13px;color:#666}\
                                </style>'
                });
            }
        })
    },
    to_update: function () {
        layer.closeAll();
        bt.system.to_update(function (rdata) {
            if (rdata.status) {
                bt.msg({ msg: lan.index.update_ok, icon: 1 })
                $("#btversion").html(rdata.version);
                $("#toUpdate").html('');
                bt.system.reload_panel();
                setTimeout(function () { window.location.reload(); }, 3000);
            }
            else {
                bt.msg({ msg: rdata.msg, icon: 5, time: 5000 });
            }
        });
    },
    to_not_beta: function () {
        bt.show_confirm('切换到正式版', '是否从测试版切换到正式版？', function () {

            bt.send('apple_beta', 'ajax/to_not_beta', {}, function (rdata) {
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return;
                }
                bt.system.check_update(function (rdata) {
                    index.to_update();
                });

            });
        });
    },
    beta_msg: function () {
        bt.send('get_beta_logs', 'ajax/get_beta_logs', {}, function (data) {
            var my_list = '';
            for (var i = 0; i < data.list.length; i++) {
                my_list += '<div class="item_list">\
                                            <span class="index_acive"></span>\
                                            <div class="index_date">'+ bt.format_data(data.list[i].uptime).split(' ')[0] + '</div>\
                                            <div class="index_title">'+ data.list[i].version + '</div>\
                                            <div class="index_conter">'+ data.list[i].upmsg + '</div>\
                                        </div>'
            }
            layer.open({
                type: 1,
                title: '申请Linux测试版',
                area: '650px',
                shadeClose: false,
                skin: 'layui-layer-dialog',
                closeBtn: 2,
                content: '<div class="bt-form pd20" style="padding-bottom:50px;padding-top:0">\
                            <div class="bt-form-conter">\
                                <span style="font-weight: 600;">申请内测须知</span>\
                                <div class="form-body">'+ data.beta_ps + '</div>\
                            </div>\
                            <div class="bt-form-conter">\
                                <span style="font-size:16px;">Linux测试版更新日志</span>\
                                <div class="item_box"  style="height:180px;overflow: auto;">'+ my_list + '</div>\
                            </div>\
                            <div class="bt-form-line"> <label for="notice" style="cursor: pointer;"><input id="notice" disabled="disabled" type="checkbox" style="vertical-align: text-top;margin-right:5px"></input><span style="font-weight:500">我已查看“<b>《申请内测须知》</b>”<i id="update_time"></i></span></label>\</div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel_beta" disabled>'+ lan.index.update_go + '</button>\
                            </div>\
                            <style>\
                                .bt-form-conter{padding: 20px 25px;line-height: 29px;background: #f7f7f7;border-radius: 5px;padding-bottom:30px;margin-bottom:20px;}\
                                .bt-form-conter span{margin-bottom: 10px;display: block;font-size: 19px;text-align: center;color: #333;}\
                                .form-body{color: #333;}\
                                #notice span{cursor: pointer;}\
                                #update_time{font-style:normal;color:red;}\
                                .item_list{margin-left:95px;border-left:5px solid #e1e1e1;position:relative;padding:5px 0 0 2px}.index_title{border-bottom:1px solid #ececec;margin-bottom:5px;font-size:15px;color:#20a53a;padding-left:15px;margin-top:7px;margin-left:5px}.index_conter{line-height:25px;font-size:12px;min-height:40px;padding-left:20px;color:#888}.index_date{position:absolute;left:-90px;top:13px;font-size:13px;color:#333}.index_acive{width:15px;height:15px;background-color:#20a53a;display:block;border-radius:50%;position:absolute;left:-10px;top:21px}.index_acive::after{position:relative;display:block;content:"";height:5px;width:5px;display:block;border-radius:50%;background-color:#fff;top:5px;left:5px}\
                            </style>\
                        </div>'
            });
            var countdown = 5;
            function settime(val) {
                if (countdown == 0) {
                    val.removeAttr("disabled");
                    $('#update_time').text('');
                    return false;
                } else {
                    $('#update_time').text('还剩' + countdown + '秒，可点击。');
                    countdown--;
                    setTimeout(function () {
                        settime(val)
                    }, 1000)
                }
            }
            settime($('#notice'));
            $('#notice').click(function () {
                console.log($(this).prop('checked'))
                if ($(this).prop('checked')) {
                    $('.btn_update_panel_beta').removeAttr('disabled');
                } else {
                    $('.btn_update_panel_beta').attr('disabled', 'disabled');
                }
            });
            $('.btn_update_panel_beta').click(function () {
                bt.show_confirm('升级Linux内测版', '请仔细阅读内测升级须知，是否升级Linux内测版？', function () {

                    bt.send('apple_beta', 'ajax/apple_beta', {}, function (rdata) {
                        if (rdata.status === false) {
                            bt.msg(rdata);
                            return;
                        }
                        bt.system.check_update(function (rdata) {
                            index.to_update();
                        });
                    });
                });
            })
        });
    },
    re_panel: function () {
        layer.confirm(lan.index.rep_panel_msg, { title: lan.index.rep_panel_title, closeBtn: 2, icon: 3 }, function () {
            bt.system.rep_panel(function (rdata) {
                if (rdata.status) {
                    bt.msg({ msg: lan.index.rep_panel_ok, icon: 1 });
                    return;
                }
                bt.msg(rdata);
            })
        });
    },
    re_server: function () {
        bt.open({
            type: 1,
            title: '重启服务器或者面板',
            area: '330px',
            closeBtn: 2,
            shadeClose: false,
            content: '<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">重启服务器</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">重启面板</a></div></div>'
        })
        setTimeout(function () {
            $('.rebt-con a').click(function () {
                var type = $(this).attr('data-id');
                switch (type) {
                    case 'panel':
                        layer.confirm(lan.index.panel_reboot_msg, { title: lan.index.panel_reboot_title, closeBtn: 2, icon: 3 }, function () {
                            var loading = bt.load();
                            interval_stop = true;
                            bt.system.reload_panel(function (rdata) {
                                loading.close();
                                bt.msg(rdata);
                            });
                            setTimeout(function () { window.location.reload(); }, 3000);
                        });
                        break;
                    case 'server':
                        var rebootbox = bt.open({
                            type: 1,
                            title: lan.index.reboot_title,
                            area: ['500px', '280px'],
                            closeBtn: 2,
                            shadeClose: false,
                            content: "<div class='bt-form bt-window-restart'>\
									<div class='pd15'>\
									<p style='color:red; margin-bottom:10px; font-size:15px;'>"+ lan.index.reboot_warning + "</p>\
									<div class='SafeRestart' style='line-height:26px'>\
										<p>"+ lan.index.reboot_ps + "</p>\
										<p>"+ lan.index.reboot_ps_1 + "</p>\
										<p>"+ lan.index.reboot_ps_2 + "</p>\
										<p>"+ lan.index.reboot_ps_3 + "</p>\
										<p>"+ lan.index.reboot_ps_4 + "</p>\
									</div>\
									</div>\
									<div class='bt-form-submit-btn'>\
										<button type='button' class='btn btn-danger btn-sm btn-reboot'>"+ lan.public.cancel + "</button>\
										<button type='button' class='btn btn-success btn-sm WSafeRestart' >"+ lan.public.ok + "</button>\
									</div>\
								</div>"
                        });
                        setTimeout(function () {
                            $(".btn-reboot").click(function () {
                                rebootbox.close();
                            })
                            $(".WSafeRestart").click(function () {
                                var body = '<div class="SafeRestartCode pd15" style="line-height:26px"></div>';
                                $(".bt-window-restart").html(body);
                                $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_1 + "</p>");
                                bt.pub.set_server_status_by("name="+bt.get_cookie('serverType')+"&type=stop", function (r1) {
                                    $(".SafeRestartCode p").addClass('c9');
                                    $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_2 + "...</p>");
                                    bt.pub.set_server_status_by("name=mysqld&type=stop", function (r2) {
                                        $(".SafeRestartCode p").addClass('c9');
                                        $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_3 + "...</p>");
                                        bt.system.root_reload(function (rdata) {
                                            $(".SafeRestartCode p").addClass('c9');
                                            $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_4 + "...</p>");
                                            var sEver = setInterval(function () {
                                                bt.system.get_total(function () {
                                                    clearInterval(sEver);
                                                    $(".SafeRestartCode p").addClass('c9');
                                                    $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_5 + "...</p>");
                                                    setTimeout(function () {
                                                        layer.closeAll();
                                                    }, 3000);
                                                })
                                            }, 3000);
                                        })
                                    })
                                })
                            })
                        }, 100)
                        break;
                }
            })
        }, 100)
    },
    open_log: function () {
        bt.open({
            type: 1,
            area: '640px',
            title: lan.index.update_log,
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            content: '<div class="DrawRecordCon"></div>'
        });
        $.get('https://www.bt.cn/Api/getUpdateLogs?type=' + bt.os, function (rdata) {
            var body = '';
            for (var i = 0; i < rdata.length; i++) {
                body += '<div class="DrawRecord DrawRecordlist">\
							<div class="DrawRecordL">'+ rdata[i].addtime + '<i></i></div>\
							<div class="DrawRecordR">\
								<h3>'+ rdata[i].title + '</h3>\
								<p>'+ rdata[i].body + '</p>\
							</div>\
						</div>'
            }
            $(".DrawRecordCon").html(body);
        }, 'jsonp');
    },
    get_cloud_list: function () {
        $.post('/plugin?action=get_soft_list', { type: 8, p: 1, force: 1, cache: 1 }, function (rdata) {
            console.log("已成功从云端获取软件列表");
        });
    },
    // 获取安全风险列表
    get_warning_list:function(active,callback){
        var that = this,obj = {};
        if(active == true) obj = {force:1}
        bt.send('get_list','warning/get_list',obj,function(res){
            if(res.status !== false){
                that.warning_list = res;
                that.warning_num = res.risk.length;
                $('.warning_num').css('color',(that.warning_num > 0?'red':'#20a53a')).html(that.warning_num);
                $('.warning_scan_ps').html(that.warning_num>0?('本次扫描共检测到风险项<i>'+ that.warning_num +'</i>个,请及时修复！'):'本次扫描检测无风险项，请继续保持！');
                if(callback) callback(res);
            }
        });
    },
    /**
     * @description 获取时间简化缩写
     * @param {Numbre} dateTimeStamp 需要转换的时间戳
     * @return {String} 简化后的时间格式
    */
    get_simplify_time:function(dateTimeStamp){
        if(dateTimeStamp === 0) return '刚刚';
        if(dateTimeStamp.toString().length == 10)  dateTimeStamp = dateTimeStamp * 1000
        var minute = 1000 * 60,hour = minute * 60,day = hour * 24,halfamonth = day * 15,month = day * 30,now = new Date().getTime(),diffValue = now - dateTimeStamp;  
        if(diffValue < 0) return  '刚刚';
        var monthC = diffValue / month,weekC = diffValue / (7 * day),dayC = diffValue / day,hourC = diffValue / hour,minC = diffValue / minute;  
        if(monthC >= 1) {  
            result = "" + parseInt(monthC) + "月前";  
        } else if(weekC >= 1) {  
            result = "" + parseInt(weekC) + "周前";  
        } else if(dayC >= 1) {  
            result = "" + parseInt(dayC) + "天前";  
        } else if(hourC >= 1) {  
            result = "" + parseInt(hourC) + "小时前";  
        } else if(minC >= 1) {  
            result = "" + parseInt(minC) + "分钟前";  
        } else{  
            result = "刚刚";  
        }     
        return result;
    },
    /**
     * @description 渲染安全模块视图
     * @return 无返回值
    */
    reader_warning_view:function(){
        var that = this;
        function reader_warning_list(data){
            var html = '',scan_time = '',arry =  [['risk','风险项'],['security','无风险项'],['ignore','已忽略项']],level = [['低危','#e8d544'],['中危','#E6A23C'],['高危','red']]
            bt.each(arry,function(index,item){
                var data_item = data[item[0]],data_title = item[1];
                html += '<li class="module_item '+ item[0] +'">'+
                        '<div class="module_head">'+
                            '<span class="module_title">'+ data_title +'</span>'+
                            '<span class="module_num">'+ data_item.length +'</span>'+
                            '<span class="module_cut_show">'+ (item[index] == 'risk' && that.warning_num > 0?'<i>点击折叠</i><span class="glyphicon glyphicon-menu-up" aria-hidden="false"></span>':'<i>查看详情</i><span class="glyphicon glyphicon-menu-down" aria-hidden="false"></span>') +'</span>'+
                        '</div>'+
                        (function(index,item){
                            var htmls = '<ul class="module_details_list '+ (item[0] == 'risk' && that.warning_num > 0?'active':'') +'">';
                            bt.each(data_item,function(indexs,items){
                                scan_time = items.check_time;
                                htmls += '<li class="module_details_item">'+
                                    '<div class="module_details_head">'+
                                        '<span class="module_details_title">'+ items.ps +'<i>（&nbsp;检测时间：'+ (that.get_simplify_time(items.check_time) || '刚刚') +'，耗时：'+ ( items.taking>1?( items.taking +'秒'):((items.taking * 1000).toFixed(2) +'毫秒')) +'&nbsp;）</i></span>'+
                                        '<span class="operate_tools">'+ (item[0] != 'security'?('<a href="javascript:;" class="btlink cut_details">详情</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" data-model="'+ items.m_name +'" data-title="'+ items.title +'" '+ (item[0]=='ignore'?'class=\"btlink\"':'') +' data-type="'+item[0]+'">'+ (item[0] != 'ignore'?'忽略':'移除忽略') +'</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" data-model="'+ items.m_name +'" data-title="'+ items.title +'">检测</a>'):'<a href="javascript:;" class="btlink cut_details">详情</a>') +'</span>' +
                                    '</div>'+
                                    '<div class="module_details_body">'+
                                        '<div class="module_details_line">'+
                                            '<div class="module_details_block"><span class="line_title">检测类型：</span><span class="line_content">'+ items.title +'</span></div>'+
                                            '<div class="module_details_block"><span class="line_title">风险等级：</span><span class="line_content" style="color:'+ level[items.level-1][1] +'">'+ level[items.level-1][0] +'</span></div>'+
                                        '</div>'+
                                        '<div class="module_details_line"><span class="line_title">风险描述：</span><span class="line_content">'+ items.msg +'</span></div>'+
                                        '<div class="module_details_line"><span class="line_title">'+ (item[0] != 'security'?'解决方案：':'配置建议') +'</span><span class="line_content">'+ 
                                        (function(){
                                            var htmlss = '';
                                            bt.each(items.tips,function(indexss,itemss){
                                                htmlss +='<i>'+ (indexss+1) +'、'+ itemss  +'</i></br>';
                                            });
                                            return htmlss;
                                        }()) +'</span></div>'+
                                        (items.help != ''?('<div class="module_details_line"><span class="line_title">帮助文档：</span><span class="line_content"><a href="'+ items.help +'" target="_blank" class="btlink">'+items.help +'</span></div>'):'') +
                                    '</div>'+
                                '</li>';
                            });
                            htmls += '</ul>';
                            return htmls;
                        }(index,item))
                    +'</li>'
            });
            $('.warning_scan_body').html(html);
            $('.warning_scan_time').html('检测时间：&nbsp;'+ bt.format_data(scan_time));
        }
        bt.open({
            type:'1',
            title:'安全风险',
            area:['750px','700px'],
            skin:'warning_scan_view',
            content:'<div class="warning_scan_view">'+
                '<div class="warning_scan_head">'+
                    '<span class="warning_scan_ps">'+ (that.warning_num>0?('本次扫描共检测到风险项<i>'+ that.warning_num +'</i>个,请及时修复！'):'本次扫描检测无风险项，请继续保持！') +'</span>'+
                    '<span class="warning_scan_time"></span>'+
                    '<button class="warning_again_scan">重新检测</button>'+
                '</div>'+
                '<ol class="warning_scan_body"></ol>'+
            '</div>',
            success:function(){
                $('.warning_again_scan').click(function(){
                     var loadT = layer.msg('正在重新检测安全风险，请稍后...',{icon:16});
                    that.get_warning_list(true,function(){
                        layer.msg('扫描成功',{icon:1});
                        reader_warning_list(that.warning_list);
                    });
                });
                $('.warning_scan_body').on('click','.module_item .module_head',function(){
                    var _parent = $(this).parent(),_parent_index = _parent.index(),_list = $(this).next();
                    if(parseInt($(this).find('.module_num').text()) > 0){
                        if(_list.hasClass('active')){
                            _list.css('height',0);
                            $(this).find('.module_cut_show i').text('查看详情').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
                            setTimeout(function(){  
                                _list.removeClass('active').removeAttr('style');
                            },500);
                        }else{
                            $(this).find('.module_cut_show i').text('点击折叠').next().removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
                            _list.addClass('active');
                            var details_list = _list.parent().siblings().find('.module_details_list');
                            details_list.removeClass('active');
                            details_list.prev().find('.module_cut_show i').text('查看详情').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down')
                        }
                    }
                });
                $('.warning_scan_body').on('click','.operate_tools a',function(){
                    var index = $(this).index(),data = $(this).data();
                    switch(index){
                        case 0:
                            if($(this).hasClass('active')){
                                $(this).parents('.module_details_head').next().hide();
                                $(this).removeClass('active').text('详情');
                            }else{
                                var item = $(this).parents('.module_details_item'),indexs = item.index();
                                $(this).addClass('active').text('折叠');
                                item.siblings().find('.module_details_body').hide();
                                item.siblings().find('.operate_tools a:eq(0)').removeClass('active').text('详情');
                                $(this).parents('.module_details_head').next().show();
                                $('.module_details_list').scrollTop(indexs * 41);
                            }
                        break;
                        case 1:
                            if(data.type != 'ignore'){
                                bt.confirm({title:'忽略风险',msg:'是否忽略【'+ data.title +'】风险,是否继续?'},function(){
                                    that.warning_set_ignore(data.model,function(res){
                                        that.get_warning_list(false,function(){
                                            bt.msg(res)
                                            reader_warning_list(that.warning_list);
                                        });
                                    });
                                }); 
                            }else{
                                that.warning_set_ignore(data.model,function(res){
                                    that.get_warning_list(false,function(){
                                        bt.msg(res)
                                        reader_warning_list(that.warning_list);
                                        setTimeout(function(){
                                            $('.module_item.ignore').click();
                                        },100)
                                    });
                                });  
                            }
                        break;
                        case 2:
                            that.waring_check_find(data.model,function(res){
                                that.get_warning_list(false,function(){
                                    bt.msg(res)
                                    reader_warning_list(that.warning_list);
                                });
                            });
                        break;
                    }
                });
                reader_warning_list(that.warning_list);
            }
        })
    },
    /**
     * @description 安全风险指定模块检查
     * @param {String} model_name 模块名称
     * @param {Function} callback 成功后的回调
     * @return 无返回值
    */
    waring_check_find:function(model_name,callback){
        var loadT = layer.msg('正在检测指定模块，请稍后...',{icon:16,time:0});
        bt.send('check_find','warning/check_find',{m_name:model_name},function(res){
            bt.msg(res);
            if(res.status !== false){
                if(callback) callback(res);
            }
        });
        
    },

    /**
     * @description 安全风险指定模块是否忽略
     * @param {String} model_name 模块名称
     * @param {Function} callback 成功后的回调
     * @return 无返回值
    */
    warning_set_ignore:function(model_name,callback){
        var loadT = layer.msg('正在设置模块状态，请稍后...',{icon:16,time:0});
        bt.send('set_ignore','warning/set_ignore',{m_name:model_name},function(res){
            bt.msg(res);
            if(res.status !== false){
                if(callback) callback(res);
            }
        });
    }
}
index.get_init();
//setTimeout(function () { index.get_cloud_list() }, 800);
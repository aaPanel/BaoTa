function modify_port_val(port){
	layer.open({
		type: 1,
		area: '400px',
		title: '修改端口',
		closeBtn:2,
		shadeClose: false,
		btn:['确认','取消'],
		content: '<div class="bt-form pd20 pd70" style="padding:20px 35px;">\
				<ul style="margin-bottom:10px;color:red;width: 100%;background: #f7f7f7;padding: 10px;border-radius: 5px;font-size: 12px;">\
					<li style="color:red;font-size:13px;">1、有安全组的服务器请提前在安全组放行新端口</li>\
					<li style="color:red;font-size:13px;">2、如果修改端口导致面板无法访问，请在SSH命令行通过bt命令改回原来的端口</li>\
				</ul>\
				<div class="line">\
	                <span class="tname" style="width: 70px;">面板端口</span>\
	                <div class="info-r" style="margin-left:70px">\
	                    <input name="portss" class="bt-input-text mr5" type="text" style="width:200px" value="'+ port +'">\
	                </div>\
                </div>\
                <div class="details" style="margin-top:5px;padding-left: 3px;">\
					<input type="checkbox" id="check_port">\
					<label style="font-weight: 400;margin: 3px 5px 0px;" for="check_port">我已了解</label>,<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-40037-1-1.html">如何放行端口？</a>\
				</div>\
			</div>',
		yes:function(index,layero){
			var check_port = $('#check_port').prop('checked'),_tips = '';
			if(!check_port){
				_tips = layer.tips('请勾选我已了解', '#check_port', {tips:[1,'#ff0000'],time:5000});
				return false;
			}
			layer.close(_tips);
			$('#banport').val($('[name="portss"]').val());
			var _data = $("#set-Config").serializeObject();
			_data['port'] = $('[name="portss"]').val();
			var loadT = layer.msg(lan.config.config_save,{icon:16,time:0,shade: [0.3, '#000']});
			$.post('/config?action=setPanel',_data,function(rdata){
				layer.close(loadT);
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				if(rdata.status){
					layer.close(index);
					setTimeout(function(){
						window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.host + window.location.pathname;
					},4000);
				}
			});
		},
		success:function(){
			$('#check_port').click(function(){
				layer.closeAll('tips');
			});
		}
	});
}
$.fn.serializeObject = function(){   
   var o = {};   
   var a = this.serializeArray();   
   $.each(a, function() {   
       if (o[this.name]) {   
           if (!o[this.name].push) {   
               o[this.name] = [o[this.name]];   
           }   
           o[this.name].push(this.value || '');   
       } else {   
           o[this.name] = this.value || '';   
       }   
   });   
   return o;   
};


//关闭面板
function ClosePanel(){
	layer.confirm(lan.config.close_panel_msg,{title:lan.config.close_panel_title,closeBtn:2,icon:13,cancel:function(){
		$("#closePl").prop("checked",false);
	}}, function() {
		$.post('/config?action=ClosePanel','',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setTimeout(function(){window.location.reload();},1000);
		});
	},function(){
		$("#closePl").prop("checked",false);
	});
}

//设置自动更新
function SetPanelAutoUpload(){
	loadT = layer.msg(lan.public.config,{icon:16,time:0});
	$.post('/config?action=AutoUpdatePanel','',function(rdata){ 
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

$('#show_recommend').click(function(){
	var status = !$(this).prop("checked"),that = $(this);
	layer.confirm(status?'关闭活动推荐，将无法接受到宝塔官方推荐的活动内容？':'开启活动推荐，定期获取宝塔官方推荐的的活动内容！',{title:status?'关闭活动推荐':'开启活动推荐',closeBtn:2,icon:13,cancel:function(){
		that.prop("checked",status);
	}}, function() {
		$.post('/config?action=show_recommend',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	},function(){
		that.prop("checked",status);
	});
});

$('#show_workorder').click(function(){
	var status = !$(this).prop("checked"),that = $(this);
	layer.confirm(status?'关闭在线客服，将无法实时向宝塔技术人员反馈问题？':'开启BUG反馈，实时向宝塔技术人员反馈问题？',{title:status?'关闭在线客服':'开启在线客服',closeBtn:2,icon:13,cancel:function(){
		that.prop("checked",status);
	}}, function() {
		$.post('/config?action=show_workorder',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			window.location.reload();
		});
	},function(){
		that.prop("checked",status);
	});
});

$('#panel_verification').click(function(){
	var _checked = $(this).prop('checked');
	if(_checked){
		layer.open({
			type: 1,
			area: ['500px','530px'],
			title: '动态口令设置',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '<div class="bt-form pd20 pd70 ssl_cert_from" style="padding:20px 35px;">\
				<div class="">\
					<i class="layui-layer-ico layui-layer-ico3"></i>\
					<h3>危险！此功能不懂别开启!</h3>\
					<ul style="width:91%;margin-bottom:10px;margin-top:10px;">\
						<li style="color:red;">必须要用到且了解此功能才决定自己是否要开启!</li>\
						<li style="color:red;">如果无法验证，命令行输入"bt 24" 取消动态口令认证</li>\
						<li>开启服务后，请立即绑定，以免出现面板不能访问。</li>\
						<li>请先下载宝塔APP或(谷歌认证器)，并完成安装和初始化</li>\
						<li>基于google Authenticator 开发,如遇到问题请点击<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/forum.php?mod=viewthread&tid=37437">了解详情</a></li>\
					</ul>\
				</div>\
				<div class="download_Qcode">\
					<div class="item_down">\
						<div class="qcode_title">Android/IOS应用 扫码下载</div>\
						<div class="qcode_conter"><img src="/static/img/bt_app.png" /></div>\
					</div>\
				</div>\
				<div class="details" style="width: 90%;margin-bottom:10px;">\
					<input type="checkbox" id="check_verification">\
					<label style="font-weight: 400;margin: 3px 5px 0px;" for="check_verification">我已安装APP和了解详情,并愿意承担风险！</label>\
				</div>\
				<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-sm btn-danger close_verify">关闭</button>\
					<button type="button" class="btn btn-sm btn-success submit_verify">确认</button>\
				</div>\
			</div>',
			success:function(layers,index){
				$('.submit_verify').click(function(e){
					var check_verification = $('#check_verification').prop('checked');
					if(!check_verification){
						layer.msg('请先勾选同意风险',{icon:0});
						return false;
					}
					var loadT = layer.msg('正在开启动态口令认证，请稍后...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					set_two_step_auth({act:_checked},function(rdata){
						layer.close(loadT);
						if (rdata.status) layer.closeAll();
						layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
						if(rdata.status && _checked){
							$('.open_two_verify_view').click();
						}
					});
				});
				$('.close_verify').click(function(){
					layer.closeAll();
					$('#panel_verification').prop('checked',!_checked);
				});
			},cancel:function () {
				layer.closeAll();
				$('#panel_verification').prop('checked',!_checked);
			}
		});
	}else{
		bt.confirm({
			title: '动态口令认证',
			msg: '是否关闭动态口令认证，是否继续？',
			cancel: function () {
				$('#panel_verification').prop('checked',!_checked);
			}}, function () {
				var loadT = layer.msg('正在关闭动态口令认证，请稍后...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				set_two_step_auth({act:_checked},function(rdata){
					layer.close(loadT);
					if (rdata.status) layer.closeAll();
					layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
					if(rdata.status && _checked){
						$('.open_two_verify_view').click();
					}
				});
			},function () {
				$('#panel_verification').prop('checked',!_checked);
		   });
	}
	
	// console.log(_data);
	
});

$('.open_two_verify_view').click(function(){
	var _checked = $('#panel_verification').prop('checked');
	if(!_checked){
		layer.msg('请先开启动态口令认证',{icon:0});
		return false;
	}
	layer.open({
        type: 1,
        area: '560px',
        title: '动态口令认证绑定',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form" style="padding:40px 25px; 20px 25px">\
					<div class="verify_item">\
						<div class="verify_vice_title" style="font-weight: 500;font-size:16px;">扫码绑定（使用宝塔面板APP或Google身份验证器APP扫码）</div>\
						<div class="verify_conter" style="text-align:center;padding-top:10px;">\
							<div id="verify_qrcode"></div>\
						</div>\
					</div>\
					<div class="verify_tips">\
						<p>提示：请使用“ 宝塔面板APP或Google身份验证器APP ”绑定,各大软件商店均可下载该APP，支持安卓、IOS系统。<a href="https://www.bt.cn/bbs/forum.php?mod=viewthread&tid=37437" class="btlink" target="_blank">使用教程</a></p>\
						<p style="color:red;">开启服务后，请立即使用“宝塔面板APP或Google身份验证器APP”绑定，以免出现无法登录的情况。</p>\
					</div>\
				</div>',
		success:function(e){
			get_two_verify(function(res){
				$('.verify_box_line .username').html(res.username);
				$('.verify_box_line .userkey').html(res.key);
			});
			get_qrcode_data(function(res){
				jQuery('#verify_qrcode').qrcode({
					render: "canvas",
					text: res,
					height:150,
					width:150
				});
			});
		}
    });
});

(function(){
	check_two_step(function(res){
		$('#panel_verification').prop('checked',res.status);
	});
	get_three_channel(function(res){
		$('#channel_auth').val(!res.user_mail.user_name && !res.dingding.dingding ? '邮箱未设置 | 钉钉未设置':(res.user_mail.user_name? '邮箱已设置':(res.dingding.dingding? '钉钉已设置': '')))
	});
})()

function get_three_channel(callback){
	$.post('/config?action=get_settings',function(res){
		if(callback) callback(res);
	});
}

function check_two_step(callback){
	$.post('/config?action=check_two_step',function(res){
		if(callback) callback(res);
	});
}
function get_qrcode_data(callback){
	$.post('/config?action=get_qrcode_data',function(res){
		if(callback) callback(res);
	});
}
function get_two_verify(callback){
	$.post('/config?action=get_key',function(res){
		if(callback) callback(res);
	});
}
function set_two_step_auth(obj,callback){
	$.post('/config?action=set_two_step_auth',{act:obj.act?1:0},function(res){
		if(callback) callback(res);
	});
}

$(".set-submit").click(function(){
	var data = $("#set-Config").serialize();
	layer.msg(lan.config.config_save,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=setPanel',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status){
			setTimeout(function(){
				window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.host + window.location.pathname;
			},1500);
		}
	});
	
});


function modify_auth_path() {
    var auth_path = $("#admin_path").val();
    btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">确定</button>";
    layer.open({
        type: 1,
        area: "500px",
        title: "修改安全入口",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20 pb70">\
                    <div class="line ">\
                        <span class="tname">入口地址</span>\
                        <div class="info-r">\
                            <input name="auth_path_set" class="bt-input-text mr5" type="text" style="width: 311px" value="'+ auth_path+'">\
                        </div></div>\
                        <div class="bt-form-submit-btn">\
                            <button type="button" class= "btn btn-sm btn-danger" onclick="layer.closeAll()"> 关闭</button>\
                            <button type="button" class="btn btn-sm btn-success" onclick="set_auth_path()">提交</button>\
                    </div></div>'
    })


    
    

}

function set_auth_path() {
    var auth_path = $("input[name='auth_path_set']").val();
    var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_admin_path', { admin_path: auth_path }, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            $("#admin_path").val(auth_path);
        }

        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }); }, 200);
    });
}


function syncDate() {
	var loadT = layer.msg(lan.config.config_sync,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=syncDate','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:1});
		setTimeout(function(){
				window.location.reload();
			},1500);
	});
}

//PHP守护程序
function Set502(){
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=Set502','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//绑定修改宝塔账号
function bindBTName(a,type){
	var titleName = lan.config.config_user_binding;
	if(type == "b"){
		btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">"+lan.config.binding+"</button>";
	}
	else{
		titleName = lan.config.config_user_edit;
		btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'c')\">"+lan.public.edit+"</button>";
	}
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		var loadT = layer.msg(lan.config.token_get,{icon:16,time:0,shade: [0.3, '#000']});
		$.post(" /ssl?action=GetToken", "username=" + p1 + "&password=" + p2, function(b){
			layer.close(loadT);
			layer.msg(b.msg, {icon: b.status?1:2});
			if(b.status) {
				window.location.reload();
				$("input[name='btusername']").val(p1);
			}
		});
		return
	}
	layer.open({
		type: 1,
		area: "290px",
		title: titleName,
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>"+lan.public.user+"</span><div class='info-r'><input class='bt-input-text' type='text' name='username' id='p1' value='' placeholder='"+lan.config.user_bt+"' style='width:100%'/></div></div><div class='line'><span class='tname'>"+lan.public.pass+"</span><div class='info-r'><input class='bt-input-text' type='password' name='password' id='p2' value='' placeholder='"+lan.config.pass_bt+"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.cancel+"</button> "+btn+"</div></div>"
	})
}
//解除绑定宝塔账号
function UnboundBt(){
	var name = $("input[name='btusername']").val();
	layer.confirm(lan.config.binding_un_msg,{closeBtn:2,icon:3,title:lan.config.binding_un},function(){
		$.get("/ssl?action=DelToken",function(b){
			layer.msg(b.msg,{icon:b.status? 1:2})
			$("input[name='btusername']").val('');
            bt.clear_cookie('bt_user_info');
		})
	})
}

//设置API
function apiSetup(){
	var loadT = layer.msg(lan.config.token_get,{icon:16,time:0,shade: [0.3, '#000']});
	$.get('/api?action=GetToken',function(rdata){
		layer.close(loadT);
		
	});
}


//设置模板
function setTemplate(){
	var template = $("select[name='template']").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=SetTemplates','templates='+template,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
		if(rdata.status === true){
			$.get('/system?action=ReWeb',function(){});
			setTimeout(function(){
				window.location.reload();
			},3000);
		}
	});
}

//设置面板SSL
function setPanelSSL(){
	var status = $("#panelSSL").prop("checked");
	var loadT = layer.msg(lan.config.ssl_msg,{icon:16,time:0,shade: [0.3, '#000']});
	if(status){
		var confirm = layer.confirm('是否关闭面板SSL证书', {title:'提示',btn: ['确定','取消'],icon:0,closeBtn:2}, function() {
            bt.send('SetPanelSSL', 'config/SetPanelSSL', {}, function (rdata) {
                layer.close(loadT);
                if (rdata.status) {
                	layer.msg(rdata.msg,{icon:1});
                    $.get('/system?action=ReWeb', function () {
                    });
                    setTimeout(function () {
                        window.location.href = ((window.location.protocol.indexOf('https') != -1) ? 'http://' : 'https://') + window.location.host + window.location.pathname;
                    }, 1500);
                }
                else {
                    layer.msg(res.rdata,{icon:2});
                }
            });
            return;
        })
	}
	else {
        bt.send('get_cert_source', 'config/get_cert_source', {}, function (rdata) {
            layer.close(loadT);
            var sdata = rdata;
            var _data = {
                title: '面板SSL',
                area: '530px',
				class:'ssl_cert_from',
                list: [
                  {
                  		html:'<div><i class="layui-layer-ico layui-layer-ico3"></i><h3>'+lan.config.ssl_open_ps+'</h3><ul><li style="color:red;">'+lan.config.ssl_open_ps_1+'</li><li>'+lan.config.ssl_open_ps_2+'</li><li>'+lan.config.ssl_open_ps_3+'</li></ul></div>'
                  },
                    {
                        title: '类型',
                        name: 'cert_type',
                        type: 'select',
                        width: '200px',
                        value: sdata.cert_type,
                        items: [{value: '1', title: '自签证书'}, {value: '2', title: 'Let\'s Encrypt'}],
                        callback: function (obj) {
                            var subid = obj.attr('name') + '_subid';
                            $('#' + subid).remove();
                            if (obj.val() == '2') {
                                var _tr = bt.render_form_line({
                                    title: '管理员邮箱',
                                    name: 'email',
									width: '250px',
                                    placeholder: '管理员邮箱',
                                    value: sdata.email
                                });
                                obj.parents('div.line').append('<div class="line" id=' + subid + '>' + _tr.html + '</div>');
                            }
                        }
                    },
                  {
                  	html:'<div class="details"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">'+lan.config.ssl_open_ps_4+'</label><a target="_blank" class="btlink" href="https://www.bt.cn/bbs">'+lan.config.ssl_open_ps_5+'</a></p></div>'
                  }
                  
                ],
                btns: [
                    {
                        title: '关闭', name: 'close', callback: function (rdata, load, callback) {
                            load.close();
                            $("#panelSSL").prop("checked", false);
                        }
                    },
                    {
                        title: '提交', name: 'submit', css: 'btn-success', callback: function (rdata, load, callback) {                                                    	
                          	if(!$('#checkSSL').is(':checked')){
                            	bt.msg({status:false,msg:'请先确认风险！'})
                              	return;
                            }                          
                        	var confirm = layer.confirm('是否开启面板SSL证书', {title:'提示',btn: ['确定','取消'],icon:0,closeBtn:2}, function() {
                            var loading = bt.load();
                            bt.send('SetPanelSSL', 'config/SetPanelSSL', rdata, function (rdata) {
                                loading.close()
                                if (rdata.status) {
                                	layer.msg(rdata.msg,{icon:1});
                                    $.get('/system?action=ReWeb', function () {
                                    });
                                    setTimeout(function () {
                                        window.location.href = ((window.location.protocol.indexOf('https') != -1) ? 'http://' : 'https://') + window.location.host + window.location.pathname;
                                    }, 1500);
                                }
                                else {
                                    layer.msg(rdata.msg,{icon:2});
                                }
                            })
							});
                        }

                    }
                ],
                end: function () {
                    $("#panelSSL").prop("checked", false);
                }
            };

            var _bs = bt.render_form(_data);
            setTimeout(function () {
                $('.cert_type' + _bs).trigger('change')
            }, 200);
        });
    }
}

function GetPanelSSL(){
	var loadT = layer.msg('正在获取证书信息...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=GetPanelSSL',{},function(cert){
		layer.close(loadT);
		var certBody = '<div class="tab-con">\
			<div class="myKeyCon ptb15">\
				<div class="ssl-con-key pull-left mr20">密钥(KEY)<br>\
					<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
				</div>\
				<div class="ssl-con-key pull-left">证书(PEM格式)<br>\
					<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
				</div>\
				<div class="ssl-btn pull-left mtb15" style="width:100%">\
					<button class="btn btn-success btn-sm" onclick="SavePanelSSL()">保存</button>\
				</div>\
			</div>\
			<ul class="help-info-text c7 pull-left">\
				<li>粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。</li>\
				<li>如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书</li><li>PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt</li>\
			</ul>\
		</div>'
		layer.open({
			type: 1,
			area: "600px",
			title: '自定义面板证书',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:certBody
		});
	});
}

function SavePanelSSL(){
	var data = {
		privateKey:$("#key").val(),
		certPem:$("#csr").val()
	}
	var loadT = layer.msg(lan.config.ssl_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config?action=SavePanelSSL',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.closeAll();
		}
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}


function SetDebug() {
    var status_s = {false:'开启',true:'关闭'};
    var debug_stat = $("#panelDebug").prop('checked');
    if(debug_stat){
    	bt.confirm({
			title: status_s[debug_stat] + "开发者模式",
			msg: "您确定要"+ status_s[debug_stat] + "开发者模式吗 ?",
	    cancel: function () {
			$("#panelDebug").prop('checked',debug_stat);
    	}},function () {
    		var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/config?action=set_debug', {}, function (rdata) {
				layer.close(loadT);
				if (rdata.status) layer.closeAll()
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			});
    	},function () {
			$("#panelDebug").prop('checked',debug_stat);
    	});
    	return;
    }
    bt.open({
    	type:'1',
    	title:status_s[debug_stat] + "开发者模式",
    	area:'450px',
    	btn:['确认','取消'],
    	content:'<div style="padding:20px 30px;">\
    		<div style="padding-bottom: 10px;">\
	    		<i class="layui-layer-ico layui-layer-ico3" style="width: 30px;height: 30px;display: inline-block;"></i>\
	    		<h3 style="display:inline-block;vertical-align:super;margin-left:15px;">警告！此功能普通用户别开启!</h3>\
    		</div>\
    		<ul style="font-size: 14px;padding: 15px;line-height:21px;background: #f5f5f5;border-radius: 8px;"><li style="color:red;">仅第三方开发者开发使用，普通用户请勿开启；</li>\
    			<li>请不要在生产环境开启，这可能增加服务器安全风险；</li>\
    			<li>开启开发者模式可能会占用大量内存；</li>\
    		</ul>\
    		<div class="details" style="margin-top: 11px;font-size: 13px;padding-left: 5px;">\
    			<input type="checkbox" id="checkDebug" style="width: 16px;height: 16px;">\
    			<label style="font-weight: 400;margin: 3px 5px 0px;" for="checkDebug">我已了经解详情,并愿意承担风险</label><p></p></div>\
    	</div>',
    	yes:function(){
    		if($('#checkDebug').prop('checked')){
    			var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
				$.post('/config?action=set_debug', {}, function (rdata) {
					layer.close(loadT);
					if (rdata.status) layer.closeAll()
					layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
				});
    		}else{
    			layer.tips('请勾选我已了解', '#checkDebug', {tips: [1,'#FF5722']});
    		}

    	},
    	btn2:function(){
    		$("#panelDebug").prop('checked',debug_stat);
    	},
    	cancel: function () {
			$("#panelDebug").prop('checked',debug_stat);
    	}
    });
 //   bt.confirm({
	// 	title: status_s[debug_stat] + "开发者模式",
	// 	msg: "开启开发者模式后面板可能会占用大量内存开销，您真的要"+ status_s[debug_stat]+"开发者模式?",
	// 	cancel: function () {
	// 		$("#panelDebug").prop('checked',debug_stat);
 //   	}}, function () {
	// 		var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
	// 		$.post('/config?action=set_debug', {}, function (rdata) {
	// 			layer.close(loadT);
	// 			if (rdata.status) layer.closeAll()
	// 			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
	// 		});
	// 	},function () {
	// 	$("#panelDebug").prop('checked',debug_stat);
	// });
}

function set_local() {
    var status_s = { false: '开启', true: '关闭' }
    var debug_stat = $("#panelLocal").prop('checked');
    bt.confirm({
		title: status_s[debug_stat] + "离线模式",
		msg: "您真的要"+ status_s[debug_stat] + "离线模式 ?",
	    cancel: function () {
			$("#panelLocal").prop('checked',debug_stat);
    	}}, function () {
        	var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/config?action=set_local', {}, function (rdata) {
				layer.close(loadT);
				if (rdata.status) layer.closeAll();
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			});
        },function () {
		$("#panelLocal").prop('checked',debug_stat);
    });
}


if(window.location.protocol.indexOf('https') != -1){
	$("#panelSSL").attr('checked',true);
}

var weChat = {
		settiming:'',
		relHeight:500,
		relWidth:500,
		userLength:'',
		init:function(){
			var _this = this;
			$('.layui-layer-page').css('display', 'none');
			$('.layui-layer-page').width(_this.relWidth);
			$('.layui-layer-page').height(_this.relHeight);
			$('.bt-w-menu').height((_this.relWidth - 1) - $('.layui-layer-title').height());
			var width = $(document).width();
			var height = $(document).height();
			var boxwidth =  (width / 2) - (_this.relWidth / 2);
			var boxheight =  (height / 2) - (_this.relHeight / 2);
			$('.layui-layer-page').css({
				'left':boxwidth +'px',
				'top':boxheight+'px'
			});
			$('.boxConter,.layui-layer-page').css('display', 'block');
			$('.layui-layer-close').click(function(event) {
				window.clearInterval(_this.settiming);
			});
			this.getUserDetails();
			$('.iconCode').hide();
			$('.personalDetails').show();
		},
		// 获取二维码
		getQRCode:function(){
			var _this = this;
			var qrLoading = layer.msg('正在获取二维码,请稍后...',{time:0,shade: [0.4,'#fff'],icon:16});
			$.get('/wxapp?action=blind_qrcode', function(res) {
				layer.close(qrLoading);
				if (res.status){
                	$('#QRcode').empty();
					$('#QRcode').qrcode({
					    render: "canvas", //也可以替换为table
					    width: 200,
					    height: 200,
					    text:res.msg
					});
					// $('.QRcode img').attr('src', res.msg);
					_this.settiming =  setInterval(function(){
						_this.verifyBdinding();
					},2000);
				}else{
					layer.msg('无法获取二维码，请稍后重试',{icon:2});
				}
			});
		},
		// 获取用户信息
		getUserDetails:function(type){
			var _this = this;
			var conter = '';
			$.get('/wxapp?action=get_user_info',function(res){
				clearInterval(_this.settiming);
				if (!res.status){
					layer.msg(res.msg,{icon:2,time:3000});
					$('.iconCode').hide();
					return false;
				}
				if (JSON.stringify(res.msg) =='{}'){
					if (type){
						layer.msg('当前绑定列表为空,请先绑定然后重试',{icon:2});
					}else{
						_this.getQRCode();
					}
					$('.iconCode').show();
					$('.personalDetails').hide();
					return false;
				}
				$('.iconCode').hide();
				$('.personalDetails').show();
				var datas = res.msg;
				for(var item in datas){
					conter += '<li class="item">\
								<div class="head_img"><img src="'+datas[item].avatarUrl+'" title="用户头像" /></div>\
								<div class="nick_name"><span>昵称:</span><span class="nick"></span>'+datas[item].nickName+'</div>\
								<div class="cancelBind">\
									<a href="javascript:;" class="btlink" title="取消当前微信小程序的绑定" onclick="weChat.cancelBdinding('+ item +')">取消绑定</a>\
								</div>\
							</li>'
				}
				conter += '<li class="item addweChat" style="height:45px;"><a href="javascript:;" class="btlink" onclick="weChat.addweChatView()"><span class="glyphicon glyphicon-plus"></span>添加绑定账号</a></li>'
				$('.userList').empty().append(conter);
			});
		},
		// 添加绑定视图
		addweChatView:function(){
			$('.iconCode').show();
			$('.personalDetails').hide();
			this.getQRCode();
		},
		// 取消当前绑定
		cancelBdinding:function(uid){
			var _this = this;
			var bdinding = layer.confirm('您确定要取消当前绑定吗？',{
				btn:['确认','取消'],
				icon:3,
				title:'取消绑定'
			},function(){
				$.get('/wxapp?action=blind_del',{uid:uid}, function(res) {
					layer.msg(res.msg,{icon:res.status?1:2});
					_this.getUserDetails();
				});
			},function(){
				layer.close(bdinding);
			});
		},
		// 监听是否绑定
		verifyBdinding:function(){
			var _this = this;
			$.get('/wxapp?action=blind_result',function(res){
				if(res){
					layer.msg('绑定成功',{icon:1});
					clearInterval(_this.settiming);
					_this.getUserDetails();
				}
			});
		},
	}
	
function open_wxapp(){
	var rhtml = '<div class="boxConter" style="display: none">\
					<div class="iconCode" >\
						<div class="box-conter">\
							<div id="QRcode"></div>\
							<div class="codeTip">\
								<ul>\
									<li>1、打开宝塔面板小程序<span class="btlink weChat">小程序二维码<div class="weChatSamll"><img src="https://app.bt.cn/static/app.png"></div></span></li>\
									<li>2、使用宝塔小程序扫描当前二维码，绑定该面板</li>\
								</ul>\
								<span><a href="javascript:;" title="返回面板绑定列表" class="btlink" style="margin: 0 auto" onclick="weChat.getUserDetails(true)">查看绑定列表</a></span>\
							</div>\
						</div>\
					</div>\
					<div class="personalDetails" style="display: none">\
						<ul class="userList"></ul>\
					</div>\
				</div>'
	
	layer.open({
		type: 1,
		title: "绑定微信",
		area: '500px',
		closeBtn: 2,
		shadeClose: false,
		content:rhtml
	});
	
	weChat.init();
}

$(function () {

    $.get("/ssl?action=GetUserInfo", function (b) {
        if (b.status) {
            $("input[name='btusername']").val(b.data.username);
            $("input[name='btusername']").next().text(lan.public.edit).attr("onclick", "bindBTName(2,'c')").css({ "margin-left": "-82px" });
            $("input[name='btusername']").next().after('<span class="btn btn-xs btn-success" onclick="UnboundBt()" style="vertical-align: 0px;">' + lan.config.binding_un + '</span>');
        }
        else {
            $("input[name='btusername']").next().text(lan.config.binding).attr("onclick", "bindBTName(2,'b')").removeAttr("style");

        }
        bt_init();
    });
})

function bt_init() {
    var btName = $("input[name='btusername']").val();
    if (!btName) {
        $('.wxapp_p .inputtxt').val("未绑定宝塔账号");
        $('.wxapp_p .modify').attr("onclick", "");
    }
}



function GetPanelApi() {
    var loadT = layer.msg('正在获取API接口信息...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=get_token', {}, function (rdata) {
        layer.close(loadT);
        isOpen = rdata.open ? 'checked' : '';
        layer.open({
            type: 1,
            area: "500px",
            title: "配置面板API",
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
			content: ' <div class="bt-form bt-form" style="padding:15px 25px">\
						<div class="line">\
							<span class="tname">API接口</span>\
							<div class="info-r" style="height:28px;">\
								<input class="btswitch btswitch-ios" id="panelApi_s" type="checkbox" '+ isOpen+'>\
								<label style="position: relative;top: 5px;" class="btswitch-btn" for="panelApi_s" onclick="SetPanelApi(2,0)"></label>\
							</div>\
						</div>\
                        <div class="line">\
                            <span class="tname">接口密钥</span>\
                            <div class="info-r">\
                                <input readonly="readonly" name="panel_token_value" class="bt-input-text mr5 disable" type="text" style="width: 310px" value="'+rdata.token+'" disable>\
								<button class="btn btn-xs btn-success btn-sm" style="margin-left: -48px;" onclick="SetPanelApi(1)">重置</button>\
                            </div>\
                        </div>\
                        <div class="line ">\
                            <span class="tname" style="overflow: initial;height:20px;line-height:20px;">IP白名单</br>(每行1个)</span>\
                            <div class="info-r">\
                                <textarea name="api_limit_addr" class="bt-input-text mr5" type="text" style="width: 310px;height:80px;line-height: 20px;padding: 5px 8px;margin-bottom:10px;">'+ rdata.limit_addr +'</textarea>\
                                <button class="btn btn-success btn-sm" onclick="SetPanelApi(3)">保存</button>\
                            </div>\
						</div>\
                        <ul class="help-info-text c7">\
                            <li>开启API后，必需在IP白名单列表中的IP才能访问面板API接口</li>\
                            <li style="color:red;">如需本机调用面板API密钥，请添加" 127.0.0.1 "和本机IP至IP白名单</li>\
                            <li>API接口文档在这里：<a class="btlink" href="https://www.bt.cn/bbs/thread-20376-1-1.html" target="_blank">https://www.bt.cn/bbs/thread-20376-1-1.html</a></li>\
                        </ul>\
					</div>'
		})
    });
}

function showPawApi(){
	layer.msg('面板API密钥仅支持一次性显示,请妥善保管。<br>如需显示面板API密钥,请点击重置按钮，重新获取新的API密钥。<br><span style="color:red;">注意事项：重置密钥后，已关联密钥产品，将失效，请重新添加新密钥至产品。</span>',{icon:0,time:0,shadeClose:true,shade:0.1});
}


function SetPanelApi(t_type,index) {
    var pdata = {}
    pdata['t_type'] = t_type
    if (t_type == 3) {
        pdata['limit_addr'] = $("textarea[name='api_limit_addr']").val()
    }
    if(t_type == 1){
    	var bdinding = layer.confirm('您确定要重置当前密钥吗？<br><span style="color:red;">重置密钥后，已关联密钥产品，将失效，请重新添加新密钥至产品。</span>',{
			btn:['确认','取消'],
			icon:3,
			closeBtn: 2,
			title:'重置密钥'
		},function(){
		    var loadT = layer.msg('正在提交...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		    set_token_req(pdata,function(rdata){
	    		if (rdata.status) {
	                $("input[name='panel_token_value']").val(rdata.msg);
	                layer.msg('接口密钥已生成，重置密钥后，已关联密钥产品，将失效，请重新添加新密钥至产品。', { icon: 1, time: 0, shade: 0.3, shadeClose:true,closeBtn:2});
	            }else{
	            	layer.msg(rdata.msg, { icon: 2});
	            }
	            return false;
		    });
		});
		return false
    }
    set_token_req(pdata,function(rdata){
    	layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        if (rdata.msg == '开启成功!') {
            if(t_type == 2 && index != '0') GetPanelApi();
        }
    });
}

function set_token_req(pdata,callback){
	$.post('/config?action=set_token', pdata, function (rdata) {
		if(callback) callback(rdata);
	});
}



function SetIPv6() {
    var loadT = layer.msg('正在配置,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_ipv6_status', {}, function (rdata) {
        layer.close(loadT);
        bt.msg(rdata);
    });
}


function modify_basic_auth_to() {
    var pdata = {
        open: $("select[name='open']").val(),
        basic_user: $("input[name='basic_user']").val(),
        basic_pwd: $("input[name='basic_pwd']").val()
    }
    var loadT = layer.msg('正在配置BasicAuth服务，请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=set_basic_auth', pdata, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            setTimeout(function () { window.location.reload(); }, 3000);
        }
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });

}

function modify_basic_auth() {
    var loadT = layer.msg('正在获取配置,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config?action=get_basic_auth_stat', {}, function (rdata) {
        layer.closeAll();
        if (rdata.open) {
            show_basic_auth(rdata);
        } else {
            m_html = '<div><i class="layui-layer-ico layui-layer-ico3"></i>'
                + '<h3 style="margin-left: 40px;margin - bottom:10px;"> 危险！此功能不懂别开启!</h3>'
                + '<ul style="border: 1px solid #ececec;border-radius: 10px; margin: 0px auto;margin-top: 20px;margin-bottom: 20px;background: #f7f7f7; width: 100 %;padding: 33px;list-style-type: inherit;">'
                + '<li style="color:red;">必须要用到且了解此功能才决定自己是否要开启!</li>'
                + '<li>开启后，以任何方式访问面板，将先要求输入BasicAuth用户名和密码</li>'
                + '<li>开启后，能有效防止面板被扫描发现，但并不能代替面板本身的帐号密码</li>'
                + '<li>请牢记BasicAuth密码，一但忘记将无法访问面板</li>'
                + '<li>如忘记密码，可在SSH通过bt命令来关闭BasicAuth验证</li>'
                + '</ul></div>'
                + '<div class="details">'
                + '<input type="checkbox" id="check_basic"><label style="font-weight: 400;margin: 3px 5px 0px;" for="check_basic">我已经了解详情,并愿意承担风险</label>'
                + '<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-34374-1-1.html">什么是BasicAuth认证？</a><p></p></div>'
            var loadT = layer.confirm(m_html, { title: "风险提醒", area: "600px" }, function () {
                if (!$("#check_basic").prop("checked")) {
                    layer.msg("请仔细阅读注意事项，并勾选同意承担风险!");
                    setTimeout(function () { modify_basic_auth();},3000)
                    return;
                }
                layer.close(loadT)
                show_basic_auth(rdata);
            });
            
        }
    });
}
function open_three_channel_auth(){
	get_channel_settings(function(rdata){
		var isOpen = rdata.dingding.info.msg.isAtAll == 'True' ? 'checked': '';
		var isDing = rdata.dingding.info.msg == '无信息'? '': rdata.dingding.info.msg.dingding_url;
		layer.open({
			type: 1,
	        area: "600px",
	        title: "设置消息通道",
	        closeBtn: 2,
	        shift: 5,
	        shadeClose: false,
	        content: '<div class="bt-form">\
	        			<div class="bt-w-main">\
					        <div class="bt-w-menu">\
					            <p class="bgw">邮箱</p>\
					            <p>钉钉</p>\
					        </div>\
					        <div class="bt-w-con pd15">\
					            <div class="plugin_body">\
	                				<div class="conter_box active" >\
	                					<div class="bt-form">\
	                						<div class="line">\
	                							<button class="btn btn-success btn-sm" onclick="add_receive_info()">添加收件者</button>\
	                							<button class="btn btn-default btn-sm" onclick="sender_info_edit()">发送者设置</button>\
	                						</div>\
					                        <div class="line">\
						                        <div class="divtable">\
						                        	<table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0"><thead><tr><th>邮箱</th><th width="80px">操作</th></tr></thead></table>\
						                        	<table class="table table-hover"><tbody id="receive_table"></tbody></table>\
						                        </div>\
					                        </div>\
				                        </div>\
	                				</div>\
	                				<div class="conter_box" style="display:none">\
		                				<div class="bt-form">\
		                					<div class="line">\
												<span class="tname">通知全体</span>\
												<div class="info-r" style="height:28px; margin-left:100px">\
													<input class="btswitch btswitch-ios" id="panel_alert_all" type="checkbox" '+ isOpen+'>\
													<label style="position: relative;top: 5px;" class="btswitch-btn" for="panel_alert_all"></label>\
												</div>\
											</div>\
						        			<div class="line">\
					                            <span class="tname">钉钉URL</span>\
					                            <div class="info-r">\
					                                <textarea name="channel_dingding_value" class="bt-input-text mr5" type="text" style="width: 300px; height:90px; line-height:20px">'+isDing+'</textarea>\
					                            </div>\
					                            <button class="btn btn-success btn-sm" onclick="SetChannelDing()" style="margin: 10px 0 0 100px;">保存</button>\
					                        </div>\
				                        </div>\
		            				</div>\
	                			</div>\
	                		</div>\
                		</div>\
                	  </div>'
		})
		$(".bt-w-menu p").click(function () {
            var index = $(this).index();
            $(this).addClass('bgw').siblings().removeClass('bgw');
            $('.conter_box').eq(index).show().siblings().hide();
        });
		get_receive_list();
	})
}
function sender_info_edit(){
	var loadT = layer.msg('正在获取配置,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/config?action=get_settings',function(rdata){
		layer.close(loadT);
		var qq_mail = rdata.user_mail.info.msg.qq_mail == undefined ? '' : rdata.user_mail.info.msg.qq_mail,
			qq_stmp_pwd = rdata.user_mail.info.msg.qq_stmp_pwd == undefined? '' : rdata.user_mail.info.msg.qq_stmp_pwd,
			hosts = rdata.user_mail.info.msg.hosts == undefined? '' : rdata.user_mail.info.msg.hosts,
			port = rdata.user_mail.info.msg.port == undefined? '' : rdata.user_mail.info.msg.port
		layer.open({
		type: 1,
        area: "460px",
        title: "设置发送者邮箱信息",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20 pb70">\
        	<div class="line">\
                <span class="tname">发送人邮箱</span>\
                <div class="info-r">\
                    <input name="channel_email_value" class="bt-input-text mr5" type="text" style="width: 300px" value="'+qq_mail+'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">smtp密码</span>\
                <div class="info-r">\
                    <input name="channel_email_password" class="bt-input-text mr5" type="password" style="width: 300px" value="'+qq_stmp_pwd+'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">smtp服务器</span>\
                <div class="info-r">\
                    <input name="channel_email_server" class="bt-input-text mr5" type="text" style="width: 300px" value="'+hosts+'">\
                </div>\
            </div>\
            <div class="line">\
                <span class="tname">端口</span>\
                <div class="info-r">\
                    <select class="bt-input-text mr5" id="port_select" style="width:'+(select_port(port)?'300px':'100px')+'"></select>\
                    <input name="channel_email_port" class="bt-input-text mr5" type="Number" style="display:'+(select_port(port)? 'none':'inline-block')+'; width: 190px" value="'+port+'">\
                </div>\
            </div>\
            <ul class="help-info-text c7">\
            	<li>推荐使用465端口，协议为SSL/TLS</li>\
            	<li>25端口为SMTP协议，587端口为STARTTLS协议</li>\
            </ul>\
            <div class="bt-form-submit-btn">\
	            <button type="button" class="btn btn-danger btn-sm smtp_closeBtn">关闭</button>\
	            <button class="btn btn-success btn-sm SetChannelEmail">保存</button></div>\
        	</div>',
        success:function(layers,index){
        	var _option = '';
        	if(select_port(port)){
        		if(port == '465' || port == ''){
        			_option = '<option value="465" selected="selected">465</option><option value="25">25</option><option value="587">587</option><option value="other">自定义</option>'
        		}else if(port == '25'){
        			_option = '<option value="465">465</option><option value="25" selected="selected">25</option><option value="587">587</option><option value="other">自定义</option>'
        		}else{
        			_option = '<option value="465">465</option><option value="25">25</option><option value="587" selected="selected">587</option><option value="other">自定义</option>'
        		}
        	}else{
        		_option = '<option value="465">465</option><option value="25">25</option><option value="587" >587</option><option value="other" selected="selected">自定义</option>'
        	}
        	console.log(port)
        	$("#port_select").html(_option)
        	$("#port_select").change(function(e){
        		if(e.target.value == 'other'){
        			$("#port_select").css("width","100px");
					$('input[name=channel_email_port]').css("display","inline-block");
        		}else{
        			$("#port_select").css("width","300px");
					$('input[name=channel_email_port]').css("display","none");
        		}
        	})
			$(".SetChannelEmail").click(function(){
				var _email = $('input[name=channel_email_value]').val();
				var _passW = $('input[name=channel_email_password]').val();
				var _server = $('input[name=channel_email_server]').val(),_port
				if($('#port_select').val() == 'other'){
					_port = $('input[name=channel_email_port]').val();
				}else{
					_port = $('#port_select').val()
				}
				if(_email == ''){
					return layer.msg('邮箱地址不能为空！',{icon:2});
				}else if(_passW == ''){
					return layer.msg('STMP密码不能为空！',{icon:2});
				}else if(_server == ''){
					return layer.msg('STMP服务器地址不能为空！',{icon:2})
				}else if(_port == ''){
					return layer.msg('请输入有效的端口号',{icon:2})
				}
				var loadT = layer.msg('正在生成邮箱通道中,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
				$.post('/config?action=user_mail_send',{email:_email,stmp_pwd:_passW,hosts:_server,port:_port},function(rdata){
					layer.close(loadT);
					layer.msg(rdata.msg,{icon:rdata.status?1:2})
					if(rdata.status){
						layer.close(index)
						get_channel_settings();
					}
				})
			})
			$(".smtp_closeBtn").click(function(){
				layer.close(index)
			})
		}
	})
	})
}
function select_port(port){
	switch(port){
		case '25':
			return true;
		case '465':
			return true;
		case '587':
			return true;
		case '':
			return true;
		default:
			return false
	}
}
function get_channel_settings(callback){
	var loadT = layer.msg('正在获取配置,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/config?action=get_settings',function(rdata){
		layer.close(loadT);
        if (callback) callback(rdata);
	})
}
function add_receive_info(){
	layer.open({
		type: 1,
        area: "400px",
        title: "添加收件者邮箱",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20 pb70">\
	        <div class="line">\
	            <span class="tname">收件人邮箱</span>\
	            <div class="info-r">\
	                <input name="creater_email_value" class="bt-input-text mr5" type="text" style="width: 240px" value="">\
	            </div>\
	        </div>\
	        <div class="bt-form-submit-btn">\
	            <button type="button" class="btn btn-danger btn-sm smtp_closeBtn">关闭</button>\
	            <button class="btn btn-success btn-sm CreaterReceive">创建</button>\
	        </div>\
	        </div>',
        success:function(layers,index){
        	$(".CreaterReceive").click(function(){
        		var _receive = $('input[name=creater_email_value]').val(),_that = this;
				if(_receive != ''){
					var loadT = layer.msg('正在创建收件人列表中,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
					layer.close(index)
					$.post('/config?action=add_mail_address',{email:_receive},function(rdata){
						layer.close(loadT);
						// 刷新收件列表
						get_receive_list();
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					})
				}else{
					layer.msg('收件人邮箱不能为空！',{icon:2});
				}
        	})
        	
			$(".smtp_closeBtn").click(function(){
				layer.close(index)
			})
		}
	})
}
function get_receive_list(){
	$.post('/config?action=get_settings',function(rdata){
		var _html = '',_list = rdata.user_mail.mail_list;
		if(_list.length > 0){
			for(var i= 0; i<_list.length;i++){
				_html += '<tr>\
					<td>'+ _list[i] +'</td>\
					<td width="80px"><a onclick="del_email(\''+ _list[i] + '\')" href="javascript:;" style="color:#20a53a">删除</a></td>\
					</tr>'
			}
		}else{
			_html = '<tr>没有数据</tr>'
		}
		$('#receive_table').html(_html);
	})
	
}

function del_email(mail){
	var loadT = layer.msg('正在删除【'+mail+'】中,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] }),_this = this;
	$.post('/config?action=del_mail_list',{email:mail},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2})
		_this.get_receive_list()
	})
}
// 设置钉钉
function SetChannelDing(){
	var _url = $('textarea[name=channel_dingding_value]').val();
	var _all = $('#panel_alert_all').prop("checked");
	if(_url != ''){
		var loadT = layer.msg('正在生成钉钉通道中,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
		$.post('/config?action=set_dingding',{url:_url,atall:_all == true? 'True':'False'},function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2})
		})
	}else{
		layer.msg('请输入钉钉url',{icon:2})
	}
}

function show_basic_auth(rdata) {
    layer.open({
        type: 1,
        area: "500px",
        title: "配置BasicAuth认证",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: ' <div class="bt-form bt-form" style="padding:15px 25px">\
						<div class="line">\
							<span class="tname">服务状态</span>\
							<div class="info-r" style="height:28px;">\
								<select class="bt-input-text" name="open">\
                                    <option value="True" '+ (rdata.open ? 'selected' : '') + '>开启</option>\
                                    <option value="False" '+ (rdata.open ? '' : 'selected') + '>关闭</option>\
                                </select>\
							</div>\
						</div>\
                        <div class="line">\
                            <span class="tname">用户名</span>\
                            <div class="info-r">\
                                <input name="basic_user" class="bt-input-text mr5" type="text" style="width: 310px" value="" placeholder="'+ (rdata.basic_user ? '不修改请留空' : '请设置用户名') + '">\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">密码</span>\
                            <div class="info-r">\
                                <input name="basic_pwd" class="bt-input-text mr5" type="text" style="width: 310px" value="" placeholder="'+ (rdata.basic_pwd ? '不修改请留空' : '请设置密码') + '">\
                            </div>\
                        </div>\
                        <span><button class="btn btn-success btn-sm" style="    margin-left: 340px;" onclick="modify_basic_auth_to()">保存配置</button></span>\
                        <ul class="help-info-text c7">\
                            <li style="color:red;">注意：请不要在这里使用您的常用密码，这可能导致密码泄漏！</li>\
                            <li>开启后，以任何方式访问面板，将先要求输入BasicAuth用户名和密码</li>\
                            <li>开启后，能有效防止面板被扫描发现，但并不能代替面板本身的帐号密码</li>\
                        </ul>\
                    </div>'
    })
}

function get_panel_hide_list(){
	var loadT = bt.load('正在获取面板菜单栏目，请稍后..'),arry = [];
	$.post('/config?action=get_menu_list',function(rdata){
		loadT.close();
		$.each(rdata,function(index,item){
			if(!item.show) arry.push(item.title)
		});
		$('#panel_menu_hide').val(arry.length > 0?arry.join('、'):'无隐藏栏目');
	});

}

get_panel_hide_list();

// 设置面板菜单显示功能
function set_panel_ground(){
	var loadT = bt.load('正在获取面板菜单栏目，请稍后..');
	$.post('/config?action=get_menu_list',function(rdata){
		var html = '',arry = ["dologin","memuAconfig","memuAsoft","memuA"],is_option = '';
		loadT.close();
		$.each(rdata,function(index,item){
			is_option = '<div class="index-item" style="float:right;"><input class="btswitch btswitch-ios" id="'+ item.id +'0000" name="'+ item.id +'" type="checkbox" '+ (item.show?'checked':'') +'><label class="btswitch-btn" for="'+ item.id +'0000"></label></div>'
			
			if(item.id == 'dologin' || item.id == 'memuAconfig' || item.id == 'memuAsoft' || item.id == 'memuA') is_option = '不可操作';
			html += '<tr><td>'+ item.title +'</td><td><div style="float:right;">'+ is_option +'</div></td></tr>';
		});
		layer.open({
			type:1,
			title:'设置面板菜单栏目管理',
			area:['350px','530px'],
			shadeClose:false,
			closeBtn:2,
			content:'<div class="divtable softlist" id="panel_menu_tab" style="padding: 20px 15px;"><table class="table table-hover"><thead><tr><th>菜单栏目</th><th style="text-align:right;width:120px;">是否显示</th></tr></thead><tbody>'+ html +'</tbody></table></div>',
			success:function(){
				$('#panel_menu_tab input').click(function(){
					var arry = [];
					$(this).parents('tr').siblings().each(function(index,el){
						if($(this).find('input').length >0 && !$(this).find('input').prop('checked')){
							arry.push($(this).find('input').attr('name'));
						}
					});
					if(!$(this).prop('checked')){
						arry.push($(this).attr('name'));
					}
					var loadT = bt.load('正在设置面板菜单栏目显示状态，请稍后..');
					$.post('/config?action=set_hide_menu_list',{hide_list:JSON.stringify(arry)},function(rdata){
						loadT.close();
						if(!rdata.status) bt.msg(rdata);
					});
				});
			}
		});
	});
}


/**
 * @description 获取临时授权列表
 * @param {Function} callback 回调函数列表
 * @returns void
 */
function get_temp_login(data,callback){
	var loadT = bt.load('获取临时授权列表，请稍后...');
	bt.send('get_temp_login','config/get_temp_login',data,function(res){
		if(res.status === false){
			layer.closeAll();
			bt.msg(res);
			return false;
		}
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 设置临时链接
 * @param {Function} callback 回调函数列表
 * @returns void
 */
function set_temp_login(callback){
	var loadT = bt.load('正在设置临时链接，请稍后...');
	bt.send('set_temp_login','config/set_temp_login',{},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 设置临时链接
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function remove_temp_login(data,callback){
	var loadT = bt.load('正在删除临时授权记录，请稍后...');
	bt.send('remove_temp_login','config/remove_temp_login',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}
/**
 * @description 强制用户登出
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function clear_temp_login(data,callback){
	var loadT = bt.load('正在强制用户登出，请稍后...');
	bt.send('clear_temp_login','config/clear_temp_login',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 渲染授权管理列表
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function reader_temp_list(data,callback){
	if(typeof data == 'function') callback = data,data = {p:1};
	get_temp_login(data,function(rdata){
		var html = '';
		$.each(rdata.data,function(index,item){
			html += '<tr><td>'+ (item.login_addr || '未登录') +'</td><td>'+ (function(){
				switch(item.state){
					case 0:
						return '<a style="color:green;">待使用</a>';
					break;
					case 1:
						return '<a style="color:brown;">已使用</a>';
					break;
					case -1:
						return '<a>已过期</a>';
					break;
				}
			}()) +'</td><td >'+ (item.login_time == 0?'未登录':bt.format_data(item.login_time)) +'</td><td>'+ bt.format_data(item.expire) +'</td><td style="text-align:right;">'+ (function(){
				if(item.state != 1){
					return '<a href="javascript:;" class="btlink remove_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">删除</a>';
				}
				if(item.online_state){
					return '<a href="javascript:;" class="btlink clear_temp_login" style="color:red" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">强制登出</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink logs_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">操作日志</a>';
				}
				return '<a href="javascript:;" class="btlink logs_temp_login" data-ip="'+ item.login_addr +'" data-id="'+ item.id +'">操作日志</a>';
			}()) +'</td></tr>';
		});
		$('#temp_login_view_tbody').html(html);
		$('.temp_login_view_page').html(rdata.page);
		if(callback) callback()
	});
}




/**
 * @description 获取操作日志
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function get_temp_login_logs(data,callback){
	var loadT = bt.load('正在获取操作日志，请稍后...');
	bt.send('clear_temp_login','config/get_temp_login_logs',{id:data.id},function(res){
		loadT.close();
		if(callback) callback(res)
	});
}

/**
 * @description 渲染操作日志
 * @param {Object} data 传入参数，id
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function reader_temp_login_logs(data,callback){
	get_temp_login_logs(data,function(res){
		var html = '';
		$.each(res,function(index,item){
			html += '<tr><td>'+ item.type +'</td><td>'+ item.addtime +'</td><td><span title="'+ item.log +'" style="white-space: pre;">'+ item.log +'</span></td></tr>';
		});
		if(callback) callback({tbody:html,data:res});
	})
}




/**
 * @description 设置临时链接
 * @param {Function} callback 回调函数列表
 * @returns void
*/
function get_temp_login_view(){
	layer.open({
		type: 1,
        area:["700px",'600px'],
        title: "临时授权管理",
        closeBtn: 2,
        shift: 5,
		shadeClose: false,
		content:'<div class="login_view_table pd15">'+
			'<button class="btn btn-success btn-sm va0 create_temp_login" >创建临时授权</button>'+
			'<div class="divtable mt10">'+
				'<table class="table table-hover">'+
					'<thead><tr><th>登录IP</th><th>状态</th><th>登录时间</th><th>过期时间</th><th style="text-align:right;">操作</th></tr></thead>'+
					'<tbody id="temp_login_view_tbody"></tbody>'+
				'</table>'+
				'<div class="temp_login_view_page page"></div>'+
			'</div>'+
		'</div>',
		success:function(){
			reader_temp_list();
			// 创建临时授权
			$('.create_temp_login').click(function(){
				bt.confirm({title:'风险提示',msg:'<span style="color:red">注意1：滥用临时授权可能导致安全风险。</br>注意2：请勿在公共场合发布临时授权连接</span></br>即将创建临时授权连接，继续吗？'},function(){
					layer.open({
						type: 1,
						area:'570px',
						title: "创建临时授权",
						closeBtn: 2,
						shift: 5,
						shadeClose: false,
						content:'<div class="bt-form create_temp_view">'+
							'<div class="line"><span class="tname">临时授权地址</span><div class="info-r ml0"><textarea id="temp_link" class="bt-input-text mr20" style="margin: 0px;width: 500px;height: 50px;line-height: 19px;"></textarea></div></div>'+
							'<div class="line"><button type="submit" class="btn btn-success btn-sm btn-copy-temp-link" data-clipboard-text="">复制地址</button></div>'+
							'<ul class="help-info-text c7"><li>临时授权生成后1小时内使用有效，为一次性授权，使用后立即失效</li><li>使用临时授权登录面板后1小时内拥有面板所有权限，请勿在公共场合发布临时授权连接</li><li>授权连接信息仅在此处显示一次，若在使用前忘记，请重新生成</li></ul>'+
						'</div>',
						success:function(){
							set_temp_login(function(res){
								if(res.status){
									var temp_link = location.origin+ '/login?tmp_token=' + res.token;
									$('#temp_link').val(temp_link);
									$('.btn-copy-temp-link').attr('data-clipboard-text',temp_link);
								}
							});
							var clipboard = new ClipboardJS('.btn');
							clipboard.on('success', function(e) {
								bt.msg({status:true,msg:'复制成功！'});
								e.clearSelection();
							});
							clipboard.on('error', function(e) {
								bt.msg({status:false,msg:'复制失败，请手动复制地址'});
							});
						},
						end:function(){
							reader_temp_list();
						}
					});
				});
			});
			// 操作日志
			$('#temp_login_view_tbody').on('click','.logs_temp_login',function(){
				var id = $(this).data('id'),ip = $(this).data('ip');
				layer.open({
					type: 1,
					area:['700px','550px'],
					title:'查看操作日志['+ ip +']',
					closeBtn: 2,
					shift: 5,
					shadeClose: false,
					content:'<div class="pd15">'+
						'<button class="btn btn-default btn-sm va0 refresh_login_logs">刷新日志</button>'+
						'<div class="divtable mt10 tablescroll" style="max-height: 420px;overflow-y: auto;border:none">'+
							'<table class="table table-hover" id="logs_login_view_table">'+
								'<thead><tr><th width="90px">操作类型</th><th width="140px">操作时间</th><th>日志</th></tr></thead>'+
								'<tbody ></tbody>'+
							'</table>'+
						'</div>'+
					'</div>',
					success:function(){
						reader_temp_login_logs({id:id},function(data){
							$('#logs_login_view_table tbody').html(data.tbody);
						});
						$('.refresh_login_logs').click(function(){
							reader_temp_login_logs({id:id},function(data){
								$('#logs_login_view_table tbody').html(data.tbody);
							});
						});
						bt.fixed_table('logs_login_view_table');
					}
				});
			});

			

			//删除授权记录，仅未使用的授权记录
			$('#temp_login_view_tbody').on('click','.remove_temp_login',function(){
				var id = $(this).data('id');
				bt.confirm({
					title:'删除未使用授权',
					msg:'是否删除未使用授权记录，是否继续？'
				},function(){
					remove_temp_login({id:id},function(res){
						reader_temp_list(function(){
							bt.msg(res);
						})
					})
				})
			});
			//强制下线，强制登录的用户下线
			$('#temp_login_view_tbody').on('click','.clear_temp_login',function(){
				var id = $(this).data('id'),ip= $(this).data('ip');
				bt.confirm({
					title:'强制登出[ '+ ip +' ]',
					msg:'是否强制登出[ '+ ip +' ]，是否继续？'
				},function(){
					clear_temp_login({id:id},function(res){
						reader_temp_list(function(){
							bt.msg(res);
						});
					});
				})
			});
			// 分页操作
			$('.temp_login_view_page').on('click','a',function(ev){
				var href = $(this).attr('href'),reg = /([0-9]*)$/,page = reg.exec(href)[0];
				reader_temp_list({p:page});
				ev.stopPropagation();
				ev.preventDefault();
			});
		}
	});

}







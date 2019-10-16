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




$('#panel_verification').click(function(){
	var _checked = $(this).prop('checked');
	if(_checked){
		layer.open({
			type: 1,
			area: ['500px','530px'],
			title: 'Google身份认证绑定',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: '<div class="bt-form pd20 pd70 ssl_cert_from" style="padding:20px 35px;">\
				<div class="">\
					<i class="layui-layer-ico layui-layer-ico3"></i>\
					<h3>危险！此功能不懂别开启!</h3>\
					<ul style="width:91%;margin-bottom:10px;margin-top:10px;">\
						<li style="color:red;">必须要用到且了解此功能才决定自己是否要开启!</li>\
						<li style="color:red;">如果无法验证，命令行输入"bt 24" 取消谷歌登录认证</li>\
						<li>请先下载APP，并完成安装和初始化</li>\
						<li>开启服务后，请立即绑定，以免出现面板不能访问。</li>\
						<li>开启后导致面板不能访问，可以点击下面链接了解解决方法。</li>\
					</ul>\
				</div>\
				<div class="download_Qcode">\
					<div class="item_down">\
						<div class="qcode_title">Android 应用下载</div>\
						<div class="qcode_conter"><img src="/static/img/icon_qcode_android.png" /></div>\
					</div>\
					<div class="item_down">\
						<div class="qcode_title">IOS 应用下载</div>\
						<div class="qcode_conter"><img src="/static/img/icon_qcode_ios.png" /></div>\
					</div>\
				</div>\
				<div class="details" style="width: 90%;margin-bottom:10px;">\
					<input type="checkbox" id="check_verification">\
					<label style="font-weight: 400;margin: 3px 5px 0px;" for="check_verification">我已安装APP和了解详情,并愿意承担风险</label>\
					<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/forum.php?mod=viewthread&tid=37437">了解详情</a>\
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
					var loadT = layer.msg('正在开启Google身份认证，请稍后...', { icon: 16, time: 0, shade: [0.3, '#000'] });
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
			title: 'Google身份认证',
			msg: '是否关闭Google身份认证，是否继续？',
			cancel: function () {
				$('#panel_verification').prop('checked',!_checked);
			}}, function () {
				var loadT = layer.msg('正在关闭Google身份认证，请稍后...', { icon: 16, time: 0, shade: [0.3, '#000'] });
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
		layer.msg('请先开启Google身份认证服务',{icon:0});
		return false;
	}
	layer.open({
        type: 1,
        area: ['600px','670px'],
        title: 'Google身份认证绑定',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form pd20" style="padding:20px 35px;">\
					<div class="verify_title">基于Google Authenticator用户进行登录认证</div>\
					<div class="verify_item">\
						<div class="verify_vice_title">1. 密钥绑定</div>\
						<div class="verify_conter">\
							<div class="verify_box">\
								<div class="verify_box_line">账号：<span class="username"></sapn></div>\
								<div class="verify_box_line">密钥：<span class="userkey"></sapn></div>\
								<div class="verify_box_line">类型：<span class="usertype">基于时间</sapn></div>\
							</div>\
						</div>\
					</div>\
					<div class="verify_item">\
						<div class="verify_vice_title">2. 扫码绑定 （ 使用Google 身份验证器APP扫码 ）</div>\
						<div class="verify_conter" style="text-align:center;padding-top:10px;">\
							<div id="verify_qrcode"></div>\
						</div>\
					</div>\
					<div class="verify_tips">\
						<p>提示：请使用“ Google 身份验证器APP ”绑定,各大软件商店均可下载该APP，支持安卓、IOS系统。<a href="https://www.bt.cn/bbs/forum.php?mod=viewthread&tid=37437" class="btlink" target="_blank">使用教程</a></p>\
						<p style="color:red;">开启服务后，请立即使用“Google 身份验证器APP”绑定，以免出现无法登录的情况。</p>\
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
})()


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
    var status_s = {false:'开启',true:'关闭'}
    var debug_stat = $("#panelDebug").prop('checked');
    bt.confirm({
		title: status_s[debug_stat] + "开发者模式",
		msg: "您真的要"+ status_s[debug_stat]+"开发者模式?",
		cancel: function () {
			$("#panelDebug").prop('checked',debug_stat);
    	}}, function () {
			var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
			$.post('/config?action=set_debug', {}, function (rdata) {
				layer.close(loadT);
				if (rdata.status) layer.closeAll()
				layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			});
		},function () {
		$("#panelDebug").prop('checked',debug_stat);
	});
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
    console.log(btName);
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
        layer.close(loadT);
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

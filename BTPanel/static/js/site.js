/**
 * 取回网站数据列表
 * @param {Number} page   当前页
 * @param {String} search 搜索条件
 */


Plugin_firewall();
function getWeb(page, search) {
	search = $("#SearchValue").prop("value");
	page = page == undefined ? '1':page;
	order = getCookie('order');
	if(order){
		order = '&order=' + order;
	}else{
		order = '';
	}
	var sUrl = '/data?action=getData'
	var pdata = 'tojs=getWeb&table=sites&limit=15&p=' + page + '&search=' + search + order;
	var loadT = layer.load();
	//取回数据
	$.post(sUrl,pdata, function(data) {
		layer.close(loadT);
		//构造数据列表
		var Body = '';
		$("#webBody").html(Body);
		for (var i = 0; i < data.data.length; i++) {
			//当前站点状态
			if (data.data[i].status == lan.site.running || data.data[i].status == '1') {
				var status = "<a href='javascript:;' title='"+lan.site.running_title+"' onclick=\"webStop(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:rgb(92, 184, 92)'>"+lan.site.running_text+"    </span><span style='color:rgb(92, 184, 92)' class='glyphicon glyphicon-play'></span></a>";
			} else {
				var status = "<a href='javascript:;' title='"+lan.site.stopped_title+"' onclick=\"webStart(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:red'>"+lan.site.stopped+"    </span><span style='color:rgb(255, 0, 0);' class='glyphicon glyphicon-pause'></span></a>";
			}

			//是否有备份
			if (data.data[i].backup_count > 0) {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ",'" + data.data[i].name + "')\">"+lan.site.backup_yes+"</a>";
			} else {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ",'" + data.data[i].name + "')\">"+lan.site.backup_no+"</a>";
			}
			//是否设置有效期
			var web_end_time = (data.data[i].edate == "0000-00-00") ? lan.site.web_end_time : data.data[i].edate;
			//表格主体
			var shortwebname = data.data[i].name;
			var shortpath = data.data[i].path;
			if(data.data[i].name.length > 30) shortwebname = data.data[i].name.substring(0, 30) + "...";
			if(data.data[i].path.length > 30) shortpath = data.data[i].path.substring(0, 30) + "...";
			
			var idname = data.data[i].name.replace(/\./g,'_');
			
			Body = "<tr><td><input type='checkbox' name='id' title='"+data.data[i].name+"' onclick='checkSelect();' value='" + data.data[i].id + "'></td>\
					<td><a class='btlink webtips' href='javascript:;' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\" title='"+data.data[i].name+"'>" + shortwebname + "</td>\
					<td>" + status + "</td>\
					<td>" + backup + "</td>\
					<td><a class='btlink' title='"+lan.site.open_path_txt+data.data[i].path+"' href=\"javascript:openPath('"+data.data[i].path+"');\">" + shortpath + "</a></td>\
					<td><a class='btlink setTimes' id='site_"+data.data[i].id+"' data-ids='"+data.data[i].id+"'>" + web_end_time + "</a></td>\
					<td><a class='btlinkbed' href='javascript:;' data-id='"+data.data[i].id+"'>" + data.data[i].ps + "</a></td>\
					<td><input class='btswitch btswitch-ios' id='closewaf_"+idname+"' type='checkbox'><label class='btswitch-btn' for='closewaf_"+idname+"' onclick=\"set_site_obj_state('" + data.data[i].name + "','open')\" style='width:2.4em;height:1.4em;margin-bottom: 0'></label></td>\
					<td style='text-align:right; color:#bbb'>\
					<a href='javascript:;' class='btlink' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\">"+lan.site.set+" </a>\
                        | <a href='javascript:;' class='btlink' onclick=\"webDelete('" + data.data[i].id + "','" + data.data[i].name + "')\" title='"+lan.site.site_del_title+"'>"+lan.public.del+"</a>\
					</td></tr>"
			
			$("#webBody").append(Body);
			
			//setEdate(data.data[i].id,data.data[i].edate);
         	//设置到期日期
            function getDate(a) {
              var dd = new Date();
              dd.setTime(dd.getTime() + (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000);
              var y = dd.getFullYear();
              var m = dd.getMonth() + 1;
              var d = dd.getDate();
              return y + "-" + (m < 10 ? ('0' + m) : m) + "-" + (d < 10 ? ('0' + d) : d);
            }
            $('#webBody').on('click','#site_'+ data.data[i].id,function(){
              var _this = $(this);
              var id = $(this).attr('data-ids');
              laydate.render({
                elem: '#site_'+ id //指定元素
                ,min:getDate(1)
                ,max:'2099-12-31'
                ,vlue:getDate(365)
                ,type:'date'
                ,format :'yyyy-MM-dd'
                ,trigger:'click'
                ,btns:['perpetual', 'confirm']
                ,theme:'#20a53a'
                ,done:function(dates){
					if(_this.html() == '永久'){
                      dates = '0000-00-00';
                    }
                    var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 0, shade: [0.3, "#000"]}); 
                    $.post('/site?action=SetEdate','id='+id+'&edate='+dates,function(rdata){
                      layer.close(loadT);
                      layer.msg(rdata.msg,{icon:rdata.status?1:5});
                    });
				}
              });
             this.click();
            });
		}
		if(Body.length < 10){
			Body = "<tr><td colspan='8'>"+lan.site.site_no_data+"</td></tr>";
			$(".dataTables_paginate").hide();
			$("#webBody").html(Body);
		}
		//输出数据列表
		$(".btn-more").hover(function(){
			$(this).addClass("open");
		},function(){
			$(this).removeClass("open");
		});
		//输出分页
		$("#webPage").html(data.page);
		get_firewall_state();
		$(".btlinkbed").click(function(){
			var dataid = $(this).attr("data-id");
			var databak = $(this).text();
			if(databak==lan.site.site_null){
				databak='';
			}
			$(this).hide().after("<input class='baktext' type='text' data-id='"+dataid+"' name='bak' value='" + databak + "' placeholder='"+lan.site.site_bak+"' onblur='GetBakPost(\"sites\")' />");
			$(".baktext").focus();
		});
	});
}

//获取防火墙状态
function get_firewall_state(){
	var typename = getCookie('serverType');
	if(typename == "nginx"){
		name='btwaf'
	}
	else {
		name='btwaf_httpd'
	}
	$.get('/plugin?action=a&name='+name+'&s=get_site_config',function(rdata){
		if(rdata.status === false){
			$(".btswitch-btn").parent().next().prepend("<a href=\"javascript:no_firewall();\" class='btlink'>防火墙</a> | ");
			$(".btswitch-btn").attr("title",typename+"防火墙开关");
			$(".btswitch-btn").click(function(){
				var that = $(this);
				layer.confirm(typename+'防火墙暂未开通，<br>请到&quot;<a href="/soft" class="btlink">软件管理>付费插件>'+typename+'防火墙</a>&quot;<br>开通安装使用。',{title:typename+'防火墙未开通',icon:7,closeBtn:2,cancel:function(){that.prev().prop('checked',false)}},function(){
					window.location.href='/soft';
				},function(){
					that.prev().prop('checked',false)
					}
				)
			})
		}
		else{
			for(var i=0;i<rdata.length;i++){
				var mid = '#closewaf_' + rdata[i].siteName.replace(/\./g,'_');
				var objs = $(mid);
				var titletips ='';
				if(!objs) continue;
				objs.prop('checked',rdata[i].open);
				for(var j=0,l=rdata[i].total.length;j<l;j++){
					if(rdata[i].total[j].value>0){
						titletips += rdata[i].total[j].name+":"+rdata[i].total[j].value+"\n";
					}
					else{
						titletips +='';
					}
				}
				objs.next().attr("title",typename+"防火墙开关");
				objs.parent().next().prepend("<a href=\"javascript:site_waf_config('" + rdata[i].siteName + "');\" class='btlink' title='"+titletips+"'>防火墙</a> | ");
			}
		}
	});
}
//未开通防火墙提示
function no_firewall(){
	var typename = getCookie('serverType');
	layer.confirm(typename+'防火墙暂未开通，<br>请到&quot;<a href="/soft" class="btlink">软件管理>付费插件>'+typename+'防火墙</a>&quot;<br>开通安装使用。',{title:typename+'防火墙未开通',icon:7,closeBtn:2},function(){
		window.location.href='/soft';
	})
}

//网站防火墙
function Plugin_firewall(){
	var typename = getCookie('serverType');
	if(typename == "nginx"){
		name='btwaf'
	}
	else {
		name='btwaf_httpd'
	}
	$.get('/plugin?action=getConfigHtml&name=' + name,function(rhtml){
		if(rhtml.status === false){
			return;
		}
		rcode = rhtml.split('<script type="javascript/text">')[1].replace('</script>','');
		rcss = rhtml.split('<style>')[1].split('</style>')[0];
		$("body").append('<div style="display:none"><style>'+rcss+'</style><script type="javascript/text">'+rcode+'</script></div>');
		setTimeout(function(){
			if(!!(window.attachEvent && !window.opera)){ 
				execScript(rcode); 
			}else{
				window.eval(rcode);
			}
		},200)
	});
}

//添加站点
function webAdd(type) {
	if (type == 1) {
		var array;
		var str="";
		var domainlist='';
		var domain = array = $("#mainDomain").val().replace('http://','').replace('https://','').split("\n");
		var Webport=[];
		var checkDomain = domain[0].split('.');
		if(checkDomain.length < 1){
			layer.msg(lan.site.domain_err_txt,{icon:2});
			return;
		}
		for(var i=1; i<domain.length; i++){
			domainlist += '"'+domain[i]+'",';
		}
		Webport = domain[0].split(":")[1];//主域名端口
		if(Webport==undefined){
			Webport="80";
		}
		domainlist = domainlist.substring(0,domainlist.length-1);//子域名json
		domain ='{"domain":"'+domain[0]+'","domainlist":['+domainlist+'],"count":'+domain.length+'}';//拼接joson
		var loadT = layer.msg(lan.public.the_get,{icon:16,time:0,shade: [0.3, "#000"]})
		var data = $("#addweb").serialize()+"&port="+Webport+"&webname="+domain;
		$.post('/site?action=AddSite', data, function(ret) {
			if(ret.status === false){
				layer.msg(ret.msg,{icon:ret.status?1:2})
				return
			}
			
			var ftpData = '';
			if (ret.ftpStatus) {
				ftpData = "<p class='p1'>"+lan.site.ftp+"</p>\
					 		<p><span>"+lan.site.user+"：</span><strong>" + ret.ftpUser + "</strong></p>\
					 		<p><span>"+lan.site.password+"：</span><strong>" + ret.ftpPass + "</strong></p>\
					 		<p style='margin-bottom: 19px; margin-top: 11px; color: #666'>"+lan.site.ftp_tips+"</p>"
			}
			var sqlData = '';
			if (ret.databaseStatus) {
				sqlData = "<p class='p1'>"+lan.site.database_txt+"</p>\
					 		<p><span>"+lan.site.database_name+"：</span><strong>" + ret.databaseUser + "</strong></p>\
					 		<p><span>"+lan.site.user+"：</span><strong>" + ret.databaseUser + "</strong></p>\
					 		<p><span>"+lan.site.password+"：</span><strong>" + ret.databasePass + "</strong></p>"
			}
			if (ret.siteStatus == true) {
				getWeb(1);
				layer.closeAll();
				if(ftpData == '' && sqlData == ''){
					layer.msg(lan.site.success_txt,{icon:1})
				}
				else{
					layer.open({
						type: 1,
						area: '600px',
						title: lan.site.success_txt,
						closeBtn:2,
						shadeClose: false,
						content: "<div class='success-msg'>\
							<div class='pic'><img src='/static/img/success-pic.png'></div>\
							<div class='suc-con'>\
								" + ftpData + sqlData + "\
							</div>\
						 </div>",
					});
					if ($(".success-msg").height() < 150) {
						$(".success-msg").find("img").css({
							"width": "150px",
							"margin-top": "30px"
						});
					}
				}

			} else {
				layer.msg(ret.msg, {
					icon: 2
				});
			}
			layer.close(loadT);
		});
		return;
	}
	
	$.post('/site?action=GetPHPVersion',function(rdata){
		var defaultPath = $("#defaultPath").html();
		var php_version = "<div class='line'><span class='tname'>"+lan.site.php_ver+"</span><select class='bt-input-text' name='version' id='c_k3' style='width:100px'>";
		for(var i=rdata.length-1;i>=0;i--){
            php_version += "<option value='"+rdata[i].version+"'>"+rdata[i].name+"</option>";
        }
		php_version += "</select><span id='php_w' style='color:red;margin-left: 10px;'></span></div>";
		layer.open({
			type: 1,
			skin: 'demo-class',
			area: '640px',
			title: lan.site.site_add,
			closeBtn: 2,
			shift: 0,
			shadeClose: false,
			content: "<form class='bt-form pd20 pb70' id='addweb'>\
						<div class='line'>\
		                    <span class='tname'>"+lan.site.domain+"</span>\
		                    <div class='info-r c4'>\
								<textarea id='mainDomain' class='bt-input-text' name='webname' style='width:458px;height:100px;line-height:22px' /></textarea>\
							</div>\
						</div>\
	                    <div class='line'>\
	                    <span class='tname'>"+lan.site.note+"</span>\
	                    <div class='info-r c4'>\
	                    	<input id='Wbeizhu' class='bt-input-text' type='text' name='ps' placeholder='"+lan.site.note_ph+"' style='width:458px' />\
	                    </div>\
	                    </div>\
	                    <div class='line'>\
	                    <span class='tname'>"+lan.site.root_dir+"</span>\
	                    <div class='info-r c4'>\
	                    	<input id='inputPath' class='bt-input-text mr5' type='text' name='path' value='"+defaultPath+"/' placeholder='"+lan.site.web_root_dir+"' style='width:458px' /><span class='glyphicon glyphicon-folder-open cursor' onclick='ChangePath(\"inputPath\")'></span>\
	                    </div>\
	                    </div>\
	                    <div class='line'>\
	                    	<span class='tname'>FTP</span>\
	                    	<div class='info-r'>\
	                    	<select class='bt-input-text' name='ftp' id='c_k1' style='width:100px'>\
		                    	<option value='true'>"+lan.site.yes+"</option>\
		                    	<option value='false' selected>"+lan.site.no+"</option>\
		                    </select>\
		                    </div>\
	                    </div>\
	                    <div class='line' id='ftpss'>\
	                    <span class='tname'>"+lan.site.ftp_set+"</span>\
	                    <div class='info-r c4'>\
		                    <div class='userpassword'><span class='mr5'>"+lan.site.user+"：<input id='ftp-user' class='bt-input-text' type='text' name='ftp_username' value='' style='width:173px' /></span>\
		                    <span class='last'>"+lan.site.password+"：<input id='ftp-password' class='bt-input-text' type='text' name='ftp_password' value=''  style='width:173px' /></span></div>\
		                    <p class='c9 mt10'>"+lan.site.ftp_help+"</p>\
	                    </div>\
	                    </div>\
	                    <div class='line'>\
	                    <span class='tname'>"+lan.site.database+"</span>\
							<div class='info-r c4'>\
								<select class='bt-input-text mr5' name='sql' id='c_k2' style='width:100px'>\
									<option value='true'>MySQL</option>\
									<option value='false' selected>"+lan.site.no+"</option>\
								</select>\
								<select class='bt-input-text' name='codeing' id='c_codeing' style='width:100px'>\
									<option value='utf8'>utf-8</option>\
									<option value='utf8mb4'>utf8mb4</option>\
									<option value='gbk'>gbk</option>\
									<option value='big5'>big5</option>\
								</select>\
							</div>\
	                    </div>\
	                    <div class='line' id='datass'>\
	                    <span class='tname'>"+lan.site.database_set+"</span>\
	                    <div class='info-r c4'>\
		                    <div class='userpassword'><span class='mr5'>"+lan.site.user+"：<input id='data-user' class='bt-input-text' type='text' name='datauser' value=''  style='width:173px' /></span>\
		                    <span class='last'>"+lan.site.password+"：<input id='data-password' class='bt-input-text' type='text' name='datapassword' value=''  style='width:173px' /></span></div>\
		                    <p class='c9 mt10'>"+lan.site.database_help+"</p>\
	                    </div>\
	                    </div>\
						"+php_version+"\
	                    <div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>"+lan.public.cancel+"</button>\
							<button type='button' class='btn btn-success btn-sm btn-title' onclick=\"webAdd(1)\">"+lan.public.submit+"</button>\
						</div>\
	                  </form>",
		});
		$(function() {
			var placeholder = "<div class='placeholder c9' style='top:10px;left:10px'>"+lan.site.domain_help+"</div>";
			$('#mainDomain').after(placeholder);
			$(".placeholder").click(function(){
				$(this).hide();
				$('#mainDomain').focus();
			})
			$('#mainDomain').focus(function() {
			    $(".placeholder").hide();
			});
			
			$('#mainDomain').blur(function() {
				if($(this).val().length==0){
					$(".placeholder").show();
				}  
			});
			
			//验证PHP版本
			$("select[name='version']").change(function(){
				if($(this).val() == '52'){
					var msgerr = 'PHP5.2在您的站点有漏洞时有跨站风险，请尽量使用PHP5.3以上版本!';
					$('#php_w').text(msgerr);
				}else{
					$('#php_w').text('');
				}
			})
			
			
			//FTP账号数据绑定域名
			$('#mainDomain').on('input', function() {
				var array;
				var res,ress;
				var str = $(this).val().replace('http://','').replace('https://','');
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				array = str.split("\n");
				ress =array[0].split(":")[0];
				res = ress.replace(new RegExp(/([-.])/g), '_');
				if(res.length > 15) res = res.substr(0,15);
				if($("#inputPath").val().substr(0,defaultPath.length) == defaultPath) $("#inputPath").val(defaultPath+'/'+ress);
				if(!isNaN(res.substr(0,1))) res = "sql"+res;
				if(res.length > 15) res = res.substr(0,15);
				$("#Wbeizhu").val(ress);
				$("#ftp-user").val(res);
				$("#data-user").val(res);
				if(isChineseChar(str)) $('.btn-zhm').show();
				else $('.btn-zhm').hide();
			})
			$('#Wbeizhu').on('input', function() {
				var str = $(this).val();
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				if (len > 20) {
					str = str.substring(0, 20);
					$(this).val(str);
					layer.msg(lan.site.domain_len_msg, {
						icon: 0
					});
				}
			})
			//获取当前时间时间戳，截取后6位
			var timestamp = new Date().getTime().toString();
			var dtpw = timestamp.substring(7);
			$("#data-user").val("sql" + dtpw);
	
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
			$("#ftp-password").val(_getRandomString(16));
			$("#data-password").val(_getRandomString(16));
	
	
			$("#ftpss,#datass").hide();
			//不创建
			$("#c_k1").change(function() {
					var val = $("#c_k1").val();
					if (val == 'false') {
						$("#ftp-user").attr("disabled", true);
						$("#ftp-password").attr("disabled", true);
						$("#ftpss").hide();
					} else {
						$("#ftp-user").attr("disabled", false);
						$("#ftp-password").attr("disabled", false);
						$("#ftpss").show();
					}
				})
				//不创建
			$("#c_k2").change(function() {
				var val = $("#c_k2").val();
				if (val == 'false') {
					$("#data-user").attr("disabled", true);
					$("#data-password").attr("disabled", true);
					$("#datass").hide();
				} else {
					$("#data-user").attr("disabled", false);
					$("#data-password").attr("disabled", false);
					$("#datass").show();
				}
			});
		});
	});
}

//修改网站目录
function webPathEdit(id){
	$.post("/data?action=getKey","table=sites&key=path&id="+id,function(rdata){
		$.post('/site?action=GetDirUserINI','path='+rdata+'&id='+id,function(userini){
			var userinicheckeds = userini.userini?'checked':'';
			var logscheckeds = userini.logs?'checked':'';
			var opt = ''
			var selected = '';
			for(var i=0;i<userini.runPath.dirs.length;i++){
				selected = '';
				if(userini.runPath.dirs[i] == userini.runPath.runPath) selected = 'selected';
				opt += '<option value="'+ userini.runPath.dirs[i] +'" '+selected+'>'+ userini.runPath.dirs[i] +'</option>'
			}
			var webPathHtml = "<div class='webedit-box soft-man-con'>\
						<div class='label-input-group ptb10'>\
							<input type='checkbox' name='userini' id='userini'"+userinicheckeds+" /><label class='mr20' for='userini' style='font-weight:normal'>"+lan.site.anti_XSS_attack+"(open_basedir)</label>\
							<input type='checkbox' name='logs' id='logs'"+logscheckeds+" /><label for='logs' style='font-weight:normal'>"+lan.site.write_access_log+"</label>\
						</div>\
						<div class='line mt10'>\
							<span class='mr5'>"+lan.site.web_dir+"</span>\
							<input class='bt-input-text mr5' type='text' style='width:50%' placeholder='"+lan.site.web_root_dir+"' value='"+rdata+"' name='webdir' id='inputPath'>\
							<span onclick='ChangePath(&quot;inputPath&quot;)' class='glyphicon glyphicon-folder-open cursor mr20'></span>\
							<button class='btn btn-success btn-sm' onclick='SetSitePath("+id+")'>"+lan.public.save+"</button>\
						</div>\
						<div class='line mtb15'>\
							<span class='mr5'>"+lan.site.run_dir+"</span>\
							<select class='bt-input-text' type='text' style='width:50%; margin-right:41px' name='runPath' id='runPath'>"+opt+"</select>\
							<button class='btn btn-success btn-sm' onclick='SetSiteRunPath("+id+")' style='margin-top: -1px;'>"+lan.public.save+"</button>\
						</div>\
						<ul class='help-info-text c7 ptb10'>\
							<li>"+lan.site.site_help_1+"</li>\
							<li>"+lan.site.site_help_2+"</li>\
						</ul>"
						+'<div class="user_pw_tit" style="margin-top: -8px;padding-top: 11px;">'
							+'<span class="tit">'+lan.soft.pma_pass+'</span>'
							+'<span class="btswitch-p"><input '+(userini.pass?'checked':'')+' class="btswitch btswitch-ios" id="pathSafe" type="checkbox">'
								+'<label class="btswitch-btn phpmyadmin-btn" for="pathSafe" onclick="PathSafe('+id+')"></label>'
							+'</span>'
						+'</div>'
						+'<div class="user_pw" style="margin-top: 10px;display:'+(userini.pass?'block;':'none;')+'">'
							+'<p><span>'+lan.soft.pma_user+'</span><input id="username_get" class="bt-input-text" name="username_get" value="" type="text" placeholder="'+lan.soft.edit_empty+'"></p>'
							+'<p><span>'+lan.soft.pma_pass1+'</span><input id="password_get_1" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="'+lan.soft.edit_empty+'"></p>'
							+'<p><span>'+lan.soft.pma_pass2+'</span><input id="password_get_2" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="'+lan.soft.edit_empty+'"></p>'
							+'<p><button class="btn btn-success btn-sm" onclick="SetPathSafe('+id+')">'+lan.public.save+'</button></p>'
						+'</div>'
					+'</div>';
			$("#webedit-con").html(webPathHtml);
			
			$("#userini").change(function(){
				$.post('/site?action=SetDirUserINI','path='+rdata,function(userini){
					layer.msg(userini.msg+'<p style="color:red;">注意：设置防跨站需要重启PHP才能生效!</p>',{icon:userini.status?1:2});
				});
			});
			
			$("#logs").change(function(){
				$.post('/site?action=logsOpen','id='+id,function(userini){
					layer.msg(userini.msg,{icon:userini.status?1:2});
				});
			});
			
		});
	});
}

//是否设置访问密码
function PathSafe(id){
	var isPass = $('#pathSafe').prop('checked');
	if(!isPass){
		$(".user_pw").show();
	}else{
		var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
		$.post('/site?action=CloseHasPwd',{id:id},function(rdata){
			layer.close(loadT);
			var ico = rdata.status?1:2;
			layer.msg(rdata.msg,{icon:ico});
			$(".user_pw").hide();
		});
	}
}

//设置访问密码
function SetPathSafe(id){
	var username = $("#username_get").val();
	var pass1 = $("#password_get_1").val();
	var pass2 = $("#password_get_2").val();
	if(pass1 != pass2){
		layer.msg(lan.bt.pass_err_re,{icon:2});
		return;
	}
	var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site?action=SetHasPwd',{id:id,username:username,password:pass1},function(rdata){
		layer.close(loadT);
		var ico = rdata.status?1:2;
		layer.msg(rdata.msg,{icon:ico});
	});
}

//提交运行目录
function SetSiteRunPath(id){
	var NewPath = $("#runPath").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site?action=SetSiteRunPath','id='+id+'&runPath='+NewPath,function(rdata){
		layer.close(loadT);
		var ico = rdata.status?1:2;
		layer.msg(rdata.msg,{icon:ico});
	});
}

//提交网站目录
function SetSitePath(id){
	var NewPath = $("#inputPath").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site?action=SetPath','id='+id+'&path='+NewPath,function(rdata){
		layer.close(loadT);
		var ico = rdata.status?1:2;
		layer.msg(rdata.msg,{icon:ico});
	});
}

//修改网站备注
function webBakEdit(id){
	$.post("/data?action=getKey','table=sites&key=ps&id="+id,function(rdata){
		var webBakHtml = "<div class='webEdit-box padding-10'>\
					<div class='line'>\
					<label><span>"+lan.site.note_ph+"</span></label>\
					<div class='info-r'>\
					<textarea name='beizhu' id='webbeizhu' col='5' style='width:96%'>"+rdata+"</textarea>\
					<br><br><button class='btn btn-success btn-sm' onclick='SetSitePs("+id+")'>"+lan.public.save+"</button>\
					</div>\
					</div>";
		$("#webedit-con").html(webBakHtml)
	});
}

//提交网站备注
function SetSitePs(id){
	var myPs = $("#webbeizhu").val();
	$.post('/data?action=setPs','table=sites&id='+id+'&ps='+myPs,function(rdata){
		layer.msg(rdata?lan.public.edit_ok:lan.public.edit_err,{icon:rdata?1:2});
	});
}


//设置默认文档
function SetIndexEdit(id){
	$.post('/site?action=GetIndex','id='+id,function(rdata){
		rdata= rdata.replace(new RegExp(/(,)/g), "\n");
		var setIndexHtml = "<div id='SetIndex'><div class='SetIndex'>\
				<div class='line'>\
						<textarea class='bt-input-text' id='Dindex' name='files' style='height: 180px; width:50%; line-height:20px'>"+rdata+"</textarea>\
						<button type='button' class='btn btn-success btn-sm pull-right' onclick='SetIndexList("+id+")' style='margin: 70px 130px 0px 0px;'>"+lan.public.save+"</button>\
				</div>\
				<ul class='help-info-text c7 ptb10'>\
					<li>"+lan.site.default_doc_help+"</li>\
				</ul>\
				</div></div>";
		$("#webedit-con").html(setIndexHtml);
	});
	
}


/**
 * 停止一个站点
 * @param {Int} wid  网站ID
 * @param {String} wname 网站名称
 */
function webStop(wid, wname) {
	layer.confirm(lan.site.site_stop_txt, {icon:3,closeBtn:2},function(index) {
		if (index > 0) {
			var loadT = layer.load()
			$.post("/site?action=SiteStop","id=" + wid + "&name=" + wname, function(ret) {
				layer.msg(ret.msg,{icon:ret.status?1:2})
				layer.close(loadT);
				getWeb(1);
				
			});
		}
	});
}

/**
 * 启动一个网站
 * @param {Number} wid 网站ID
 * @param {String} wname 网站名称
 */
function webStart(wid, wname) {
	layer.confirm(lan.site.site_start_txt,{icon:3,closeBtn:2}, function(index) {
		if (index > 0) {
			var loadT = layer.load()
			$.post("/site?action=SiteStart","id=" + wid + "&name=" + wname, function(ret) {
				layer.msg(ret.msg,{icon:ret.status?1:2})
				layer.close(loadT);
				getWeb(1);
			});
		}
	});
}

/**
 * 删除一个网站
 * @param {Number} wid 网站ID
 * @param {String} wname 网站名称
 */
function webDelete(wid, wname){
	var thtml = "<div class='options'>\
	    	<label><input type='checkbox' id='delftp' name='ftp'><span>FTP</span></label>\
	    	<label><input type='checkbox' id='deldata' name='data'><span>"+lan.site.database+"</span></label>\
	    	<label><input type='checkbox' id='delpath' name='path'><span>"+lan.site.root_dir+"</span></label>\
	    	</div>";
	SafeMessage(lan.site.site_del_title+"["+wname+"]",lan.site.site_del_info,function(){
		var ftp='',data='',path='';
		if($("#delftp").is(":checked")){
			ftp='&ftp=1';
		}
		if($("#deldata").is(":checked")){
			data='&database=1';
		}
		if($("#delpath").is(":checked")){
			path='&path=1';
		}
		var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
		$.post("/site?action=DeleteSite","id=" + wid + "&webname=" + wname+ftp+data+path, function(ret){
			layer.closeAll();
			layer.msg(ret.msg,{icon:ret.status?1:2})
			getWeb(1);
		});
	},thtml);
}


//批量删除
function allDeleteSite(){
	var checkList = $("input[name=id]");
	var dataList = new Array();
	for(var i=0;i<checkList.length;i++){
		if(!checkList[i].checked) continue;
		var tmp = new Object();
		tmp.name = checkList[i].title;
		tmp.id = checkList[i].value;
		dataList.push(tmp);
	}
	
	var thtml = "<div class='options'>\
	    	<label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>"+lan.site.all_del_info+"</span></label>\
	    	</div>";
	SafeMessage(lan.site.all_del_site,"<a style='color:red;'>"+lan.get('del_all_site',[dataList.length])+"</a>",function(){
		layer.closeAll();
		var path = '';
		if($("#delpath").is(":checked")){
			path='&path=1';
		}
		syncDeleteSite(dataList,0,'',path);
	},thtml);
}

//模拟同步开始批量删除
function syncDeleteSite(dataList,successCount,errorMsg,path){
	if(dataList.length < 1) {
		layer.msg(lan.get('del_all_site_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('del_all_task_the',[dataList[0].name]),{icon:16,time:0,shade: [0.3, '#000']});
	$.ajax({
			type:'POST',
			url:'/site?action=DeleteSite',
			data:'id='+dataList[0].id+'&webname='+dataList[0].name+path,
			async: true,
			success:function(frdata){
				layer.close(loadT);
				if(frdata.status){
					successCount++;
					$("input[title='"+dataList[0].name+"']").parents("tr").remove();
				}else{
					if(!errorMsg){
						errorMsg = '<br><p>'+lan.site.del_err+':</p>';
					}
					errorMsg += '<li>'+dataList[0].name+' -> '+frdata.msg+'</li>'
				}
				
				dataList.splice(0,1);
				syncDeleteSite(dataList,successCount,errorMsg,path);
			}
	});
}


/**
 * 域名管理
 * @param {Int} id 网站ID
 */
function DomainEdit(id, name,msg,status) {
	$.get('/data?action=getData&table=domain&list=True&search=' + id, function(domain) {
		var echoHtml = "";
		for (var i = 0; i < domain.length; i++) {
			echoHtml += "<tr><td><a title='"+lan.site.click_access+"' target='_blank' href='http://" + domain[i].name + ":" + domain[i].port + "' class='btlinkbed'>" + domain[i].name + "</a></td><td><a class='btlinkbed'>" + domain[i].port + "</a></td><td class='text-center'><a class='table-btn-del' href='javascript:;' onclick=\"delDomain(" + id + ",'" + name + "','" + domain[i].name + "','" + domain[i].port + "',1)\"><span class='glyphicon glyphicon-trash'></span></a></td></tr>";
		}
		var bodyHtml = "<textarea id='newdomain' class='bt-input-text' style='height: 100px; width: 340px;padding:5px 10px;line-height:20px'></textarea>\
								<input type='hidden' id='newport' value='80' />\
								<button type='button' class='btn btn-success btn-sm pull-right' style='margin:30px 35px 0 0' onclick=\"DomainAdd(" + id + ",'" + name + "',1)\">"+lan.public.add+"</button>\
							<div class='divtable mtb15' style='height:350px;overflow:auto'>\
								<table class='table table-hover' width='100%'>\
								<thead><tr><th>"+lan.site.domain+"</th><th width='70px'>"+lan.site.port+"</th><th width='50px' class='text-center'>"+lan.site.operate+"</th></tr></thead>\
								<tbody id='checkDomain'>" + echoHtml + "</tbody>\
								</table>\
							</div>";
		$("#webedit-con").html(bodyHtml);
		if(msg != undefined){
			layer.msg(msg,{icon:status?1:5});
		}
		var placeholder = "<div class='placeholder c9' style='left:28px;width:330px;top:16px;'>"+lan.site.domain_help+"</div>";
		$('#newdomain').after(placeholder);
		$(".placeholder").click(function(){
			$(this).hide();
			$('#newdomain').focus();
		})
		$('#newdomain').focus(function() {
		    $(".placeholder").hide();
		});
		
		$('#newdomain').blur(function() {
			if($(this).val().length==0){
				$(".placeholder").show();
			}  
		});
		$("#newdomain").on("input",function(){
			var str = $(this).val();
			if(isChineseChar(str)) $('.btn-zhm').show();
			else $('.btn-zhm').hide();
		})
		//checkDomain();
	});
}

function DomainRoot(id, name,msg) {
	$.get('/data?action=getData&table=domain&list=True&search=' + id, function(domain) {
		var echoHtml = "";
		for (var i = 0; i < domain.length; i++) {
			echoHtml += "<tr><td><a title='"+lan.site.click_access+"' target='_blank' href='http://" + domain[i].name + ":" + domain[i].port + "' class='btlinkbed'>" + domain[i].name + "</a></td><td><a class='btlinkbed'>" + domain[i].port + "</a></td><td class='text-center'><a class='table-btn-del' href='javascript:;' onclick=\"delDomain(" + id + ",'" + name + "','" + domain[i].name + "','" + domain[i].port + "',1)\"><span class='glyphicon glyphicon-trash'></span></a></td></tr>";
		}
		var index = layer.open({
			type: 1,
			skin: 'demo-class',
			area: '450px',
			title: lan.site.domain_man,
			closeBtn: 2,
			shift: 0,
			shadeClose: true,
			content: "<div class='divtable padding-10'>\
						<textarea id='newdomain'></textarea>\
						<input type='hidden' id='newport' value='80' />\
						<button type='button' class='btn btn-success btn-sm pull-right' style='margin:30px 35px 0 0' onclick=\"DomainAdd(" + id + ",'" + name + "')\">添加</button>\
						<table class='table table-hover' width='100%' style='margin-bottom:0'>\
						<thead><tr><th>"+lan.site.domain+"</th><th width='70px'>"+lan.site.port+"</th><th width='50px' class='text-center'>"+lan.site.operate+"</th></tr></thead>\
						<tbody id='checkDomain'>" + echoHtml + "</tbody>\
						</table></div>"
		});
		if(msg != undefined){
			layer.msg(msg,{icon:1});
		}
		var placeholder = "<div class='placeholder'>"+lan.site.domain_help+"</div>";
		$('#newdomain').after(placeholder);
		$(".placeholder").click(function(){
			$(this).hide();
			$('#newdomain').focus();
		})
		$('#newdomain').focus(function() {
		    $(".placeholder").hide();
		});
		
		$('#newdomain').blur(function() {
			if($(this).val().length==0){
				$(".placeholder").show();
			}  
		});
		$("#newdomain").on("input",function(){
			var str = $(this).val();
			if(isChineseChar(str)) $('.btn-zhm').show();
			else $('.btn-zhm').hide();
		})
		//checkDomain();
	});
}
//编辑域名/端口
function cancelSend(){
	$(".changeDomain,.changePort").hide().prev().show();
	$(".changeDomain,.changePort").remove();
}
//遍历域名
function checkDomain() {
	$("#checkDomain tr").each(function() {
		var $this = $(this);
		var domain = $(this).find("td:first-child").text();
		$(this).find("td:first-child").append("<i class='lading'></i>");
		checkDomainWebsize($this,domain);
	})
}
//检查域名是否解析备案
function checkDomainWebsize(obj,domain){
	var gurl = "http://api.bt.cn/ipaddess";
	var ip = getCookie('iplist');
	var data = "domain=" + domain+"&ip="+ip;
	$.ajax({ url: gurl,data:data,type:"get",dataType:"jsonp",async:true ,success: function(rdata){
		obj.find("td:first-child").find(".lading").remove();
		if (rdata.code == -1) {
			obj.find("td:first-child").append("<i class='yf' data-title='"+lan.site.this_domain_un+"'>"+lan.site.unresolved+"</i>");
		} else {
			obj.find("td:first-child").append("<i class='f' data-title='"+lan.site.analytic_ip+"：" + rdata.data.ip + "<br>"+lan.site.current_server_ip+"：" + rdata.data.main_ip + "("+lan.site.parsed_info+")'>"+lan.site.parsed+"</i>");
		}

		obj.find("i").mouseover(function() {
			var tipsTitle = $(this).attr("data-title");
			layer.tips(tipsTitle, this, {
				tips: [1, '#3c8dbc'],
				time: 0
			})
		})
		obj.find("i").mouseout(function() {
			$(".layui-layer-tips").remove();
		})
	}})
}

/**
 * 添加域名
 * @param {Int} id  网站ID
 * @param {String} webname 主域名
 */
function DomainAdd(id, webname,type) {
	var Domain = $("#newdomain").val().split("\n");
	
	var domainlist="";
	for(var i=0; i<Domain.length; i++){
		domainlist += Domain[i]+",";
	}
	
	if(domainlist.length < 3){
		layer.msg(lan.site.domain_empty,{icon:5});
		return;
	}
	domainlist = domainlist.substring(0,domainlist.length-1);
	var loadT = layer.load();
	var data = "domain=" + domainlist + "&webname=" + webname + "&id=" + id;
	$.post('/site?action=AddDomain', data, function(retuls) {
		layer.close(loadT);
		DomainEdit(id,webname,retuls.msg,retuls.status);
	});
}

/**
 * 删除域名
 * @param {Number} wid 网站ID
 * @param {String} wname 主域名
 * @param {String} domain 欲删除的域名
 * @param {Number} port 对应的端口
 */
function delDomain(wid, wname, domain, port,type) {
	var num = $("#checkDomain").find("tr").length;
	if(num==1){
		layer.msg(lan.site.domain_last_cannot);
	}
	layer.confirm(lan.site.domain_del_confirm,{icon:3,closeBtn:2}, function(index) {
			var url = "/site?action=DelDomain"
			var data = "id=" + wid + "&webname=" + wname + "&domain=" + domain + "&port=" + port;
			var loadT = layer.msg(lan.public.the_del,{time:0,icon:16});
			$.post(url,data, function(ret) {
				layer.close(loadT);
				layer.msg(ret.msg,{icon:ret.status?1:2})
				if(type == 1){
					layer.close(loadT);
					DomainEdit(wid,wname)
				}else{
					layer.closeAll();
					DomainRoot(wid, wname);
				}
			});
	});
}

/**
 * 判断IP/域名格式
 * @param {String} domain  源文本
 * @return bool
 */
function IsDomain(domain) {
		//domain = 'http://'+domain;
		var re = new RegExp();
		re.compile("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_%&\?\/.=]+$");
		if (re.test(domain)) {
			return (true);
		} else {
			return (false);
		}
	}



/**
 *设置数据库备份
 * @param {Number} sign	操作标识
 * @param {Number} id	编号
 * @param {String} name	主域名
 */
function WebBackup(id, name) {
		var loadT =layer.msg(lan.database.backup_the, {icon:16,time:0,shade: [0.3, '#000']});
		var data = "id="+id;
		$.post('/site?action=ToBackup', data, function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg,{icon:rdata.status?1:2})
			getBackup(id);
		});
}

/**
 *删除网站备份
 * @param {Number} webid	网站编号
 * @param {Number} id	文件编号
 * @param {String} name	主域名
 */
function WebBackupDelete(id,pid){
	layer.confirm(lan.site.webback_del_confirm,{title:lan.site.del_bak_file,icon:3,closeBtn:2},function(index){
		var loadT =layer.msg(lan.public.the_del, {icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=DelBackup','id='+id, function(rdata){
			layer.closeAll();
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			getBackup(pid);
		});
	})
}

function getBackup(id,name,page) {
	if(page == undefined){
		page = '1';
	} 
	$.post('/data?action=getFind','table=sites&id=' + id, function(rdata) {
		$.post('/data?action=getData','table=backup&search=' + id + '&limit=5&p='+page+'&type=0&tojs=getBackup',function(frdata){
			
			var body = '';
				for (var i = 0; i < frdata.data.length; i++) {
					if(frdata.data[i].type == '1') continue;
					if(frdata.data[i].filename.length < 15){
						var ftpdown = "<a class='btlink' href='/cloud?filename="+frdata.data[i].filename+"&name="+ frdata.data[i].name+"' target='_blank'>下载</a> | ";
					}else{
						var ftpdown = "<a class='btlink' href='/download?filename="+frdata.data[i].filename+"&name="+frdata.data[i].name+"' target='_blank'>下载</a> | ";
					}
					body += "<tr><td><span class='glyphicon glyphicon-file'></span>"+frdata.data[i].name+"</td>\
							<td>" + (ToSize(frdata.data[i].size)) + "</td>\
							<td>" + frdata.data[i].addtime + "</td>\
							<td class='text-right' style='color:#ccc'>"+ ftpdown + "<a class='btlink' href='javascript:;' onclick=\"WebBackupDelete('" + frdata.data[i].id + "',"+id+")\">"+lan.public.del+"</a></td>\
						</tr>"
				}
			var ftpdown = '';
			frdata.page = frdata.page.replace(/'/g,'"').replace(/getBackup\(/g,"getBackup(" + id + ",0,");
			
			if(name == 0){
				var sBody = "<table width='100%' id='WebBackupList' class='table table-hover'>\
							<thead><tr><th>"+lan.site.filename+"</th><th>"+lan.site.filesize+"</th><th>"+lan.site.backuptime+"</th><th width='140px' class='text-right'>"+lan.site.operate+"</th></tr></thead>\
							<tbody id='WebBackupBody' class='list-list'>"+body+"</tbody>\
							</table>"
				$("#WebBackupList").html(sBody);
				$(".page").html(frdata.page);
				return;
			}
			layer.closeAll();
			layer.open({
				type: 1,
				skin: 'demo-class',
				area: '700px',
				title: lan.site.backup_title,
				closeBtn: 2,
				shift: 0,
				shadeClose: false,
				content: "<div class='bt-form ptb15 mlr15' id='WebBackup'>\
							<button class='btn btn-default btn-sm' style='margin-right:10px' type='button' onclick=\"WebBackup('" + rdata.id + "','" + rdata.name + "')\">"+lan.site.backup_title+"</button>\
							<div class='divtable mtb15' style='margin-bottom:0'><table width='100%' id='WebBackupList' class='table table-hover'>\
							<thead><tr><th>"+lan.site.filename+"</th><th>"+lan.site.filesize+"</th><th>"+lan.site.backuptime+"</th><th width='140px' class='text-right'>"+lan.site.operate+"</th></tr></thead>\
							<tbody id='WebBackupBody' class='list-list'>"+body+"</tbody>\
							</table><div class='page'>"+frdata.page+"</div></div></div>"
			});
		});
		
	});

}

function goSet(num) {
	//取选中对象
	var el = document.getElementsByTagName('input');
	var len = el.length;
	var data = '';
	var a = '';
	var count = 0;
	//构造POST数据
	for (var i = 0; i < len; i++) {
		if (el[i].checked == true && el[i].value != 'on') {
			data += a + count + '=' + el[i].value;
			a = '&';
			count++;
		}
	}
	//判断操作类别
	if(num==1){
		reAdd(data);
	}
	else if(num==2){
		shift(data);
	}
}


//设置默认文档
function SetIndex(id){
	var quanju = (id==undefined)?lan.site.public_set:lan.site.local_site;
	var data=id==undefined?"":"id="+id;
	$.post('/site?action=GetIndex',data,function(rdata){
		rdata= rdata.replace(new RegExp(/(,)/g), "\n");
		layer.open({
				type: 1,
				area: '500px',
				title: lan.site.setindex,
				closeBtn: 2,
				shift: 5,
				shadeClose: true,
				content:"<form class='bt-form' id='SetIndex'><div class='SetIndex'>"
				+"<div class='line'>"
				+"	<span class='tname' style='padding-right:2px'>"+lan.site.default_doc+"</span>"
				+"	<div class='info-r'>"
				+"		<textarea id='Dindex' name='files' style='line-height:20px'>"+rdata+"</textarea>"
				+"		<p>"+quanju+lan.site.default_doc_help+"</p>"
				+"	</div>"
				+"</div>"
				+"<div class='bt-form-submit-btn'>"
				+"	<button type='button' id='web_end_time' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>"+lan.public.cancel+"</button>"
			    +"    <button type='button' class='btn btn-success btn-sm btn-title' onclick='SetIndexList("+id+")'>"+lan.public.ok+"</button>"
		        +"</div>"
				+"</div></form>"
		});
	});
}

//设置默认站点
function SetDefaultSite(){
	var name = $("#defaultSite").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=SetDefaultSite','name='+name,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	});
}


//默认站点
function GetDefaultSite(){
	$.post('/site?action=GetDefaultSite','',function(rdata){
		var opt = '<option value="off">'+lan.site.default_site_no+'</option>';
		var selected = '';
		for(var i=0;i<rdata.sites.length;i++){
			selected = '';
			if(rdata.defaultSite == rdata.sites[i].name) selected = 'selected';
			opt += '<option value="' + rdata.sites[i].name + '" ' + selected + '>' + rdata.sites[i].name + '</option>';
		}
		
		layer.open({
				type: 1,
				area: '430px',
				title: lan.site.default_site_yes,
				closeBtn: 2,
				shift: 5,
				shadeClose: true,
				content:'<div class="bt-form ptb15 pb70">\
							<p class="line">\
								<span class="tname text-right">'+lan.site.default_site+'</span>\
								<select id="defaultSite" class="bt-input-text" style="width: 300px;">'+opt+'</select>\
							</p>\
							<ul class="help-info-text c6 plr20">\
							    <li>'+lan.site.default_site_help_1+'</li>\
							    <li>'+lan.site.default_site_help_2+'</li>\
						    </ul>\
							<div class="bt-form-submit-btn">\
								<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.cancel+'</button>\
								<button class="btn btn-success btn-sm btn-title" onclick="SetDefaultSite()">'+lan.public.ok+'</button>\
							</div>\
						</div>'
		});
	});
}

function SetIndexList(id){
	var Dindex = $("#Dindex").val().replace(new RegExp(/(\n)/g), ",");
	if(id==undefined){
		var data="id=&Index="+Dindex;
	}
	else{
		var data="id="+id+"&Index="+Dindex;
	}
	var loadT= layer.load(2);
	$.post('/site?action=SetIndex',data,function(rdata){
		layer.close(loadT);
		var ico = rdata.status? 1:5;
		layer.msg(rdata.msg,{icon:ico});
	});
}



/*站点修改*/
function webEdit(id,website,endTime,addtime){
	var system = "{$Think.session.system}";
	var eMenu = '';
	eMenu = "<p onclick='DirBinding("+id+")' title='"+lan.site.site_menu_1+"'>"+lan.site.site_menu_1+"</p>"
	+"<p onclick='webPathEdit("+id+")' title='"+lan.site.site_menu_2+"'>"+lan.site.site_menu_2+"</p>"
	+"<p onclick='limitNet("+id+")' title='"+lan.site.site_menu_3+"'>"+lan.site.site_menu_3+"</p>"
	+"<p onclick=\"Rewrite('"+website+"')\" title='"+lan.site.site_menu_4+"'>"+lan.site.site_menu_4+"</p>"
	+"<p onclick='SetIndexEdit("+id+")' title='"+lan.site.site_menu_5+"'>"+lan.site.site_menu_5+"</p>"
	+"<p onclick=\"ConfigFile('"+website+"')\" title='"+lan.site.site_menu_6+"'>"+lan.site.site_menu_6+"</p>"
	+"<p onclick=\"SetSSL("+id+",'"+website+"')\" title='"+lan.site.site_menu_7+"'>"+lan.site.site_menu_7+"</p>"
	+"<p onclick=\"PHPVersion('"+website+"')\" title='"+lan.site.site_menu_8+"'>"+lan.site.site_menu_8+"</p>"
	+"<p onclick=\"toTomcat('"+website+"')\" title='"+lan.site.site_menu_9+"'>"+lan.site.site_menu_9+"</p>"
	+"<p onclick=\"To301('"+website+"')\" title='"+lan.site.site_menu_10+"'>"+lan.site.site_menu_10+"</p>"
	+"<p onclick=\"Proxy('"+website+"')\" title='"+lan.site.site_menu_12+"'>"+lan.site.site_menu_11+"</p>"
	+"<p id='site_"+id+"' onclick=\"Security('"+id+"','"+website+"')\" title='"+lan.site.site_menu_12+"'>"+lan.site.site_menu_12+"</p>"
	+"<p id='site_"+id+"' onclick=\"GetSiteLogs('"+website+"')\" title='查看站点请求日志'>响应日志</p>";
	layer.open({
		type: 1,
		area: '640px',
		title: lan.site.website_change+'['+website+']  --  '+lan.site.addtime+'['+addtime+']',
		closeBtn: 2,
		shift: 0,
		content: "<div class='bt-form'>"
			+"<div class='bt-w-menu pull-left' style='height: 565px;'>"
			+"	<p class='bgw'  onclick=\"DomainEdit(" + id + ",'" + website + "')\">"+lan.site.domain_man+"</p>"
			+"	"+eMenu+""
			+"</div>"
			+"<div id='webedit-con' class='bt-w-con webedit-con pd15'></div>"
			+"</div>"
	});
	DomainEdit(id,website);
	//域名输入提示
	var placeholder = "<div class='placeholder'>"+lan.site.domain_help+"</div>";
	$('#newdomain').after(placeholder);
	$(".placeholder").click(function(){
		$(this).hide();
		$('#newdomain').focus();
	});
	$('#newdomain').focus(function() {
	    $(".placeholder").hide();
	});
	
	$('#newdomain').blur(function() {
		if($(this).val().length==0){
			$(".placeholder").show();
		}  
	});
	//切换
	var $p = $(".bt-w-menu p");
	$p.click(function(){
		$(this).addClass("bgw").siblings().removeClass("bgw");
	});
}

//取网站日志
function GetSiteLogs(siteName){
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=GetSiteLogs',{siteName:siteName},function(logs){
		layer.close(loadT);
		if(logs.status !== true){
			logs.msg = '';
		}
		if (logs.msg == '') logs.msg = '当前没有日志.';
		var phpCon = '<textarea wrap="off" readonly="" style="white-space: pre;margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">'+logs.msg+'</textarea>';
		$("#webedit-con").html(phpCon);
		var ob = document.getElementById('error_log');
		ob.scrollTop = ob.scrollHeight;		
	});
}


//防盗链
function Security(id,name){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=GetSecurity',{id:id,name:name},function(rdata){
		layer.close(loadT);
		var mbody = '<div>'
					+'<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">URL后缀</span><input class="bt-input-text" type="text" name="sec_fix" value="'+rdata.fix+'" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;'+(rdata.status?'background-color: #eee;':'')+'" placeholder="多个请用逗号隔开,例：png,jpeg,jpg,gif,zip" '+(rdata.status?'readonly':'')+'></p>'
					+'<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">许可域名</span><input class="bt-input-text" type="text" name="sec_domains" value="'+rdata.domains+'" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;'+(rdata.status?'background-color: #eee;':'')+'" placeholder="支持通配符,多个域名请用逗号隔开,例：*.test.com,test.com" '+(rdata.status?'readonly':'')+'></p>'
					+'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="sec_status" onclick="SetSecurity(\''+name+'\','+id+')" '+(rdata.status?'checked':'')+'>启用防盗链</label></div>'
					+'<ul class="help-info-text c7 ptb10">'
						+'<li>默认允许资源被直接访问,即不限制HTTP_REFERER为空的请求</li>'
						+'<li>多个URL后缀与域名请使用逗号(,)隔开,如: png,jpeg,zip,js</li>'
						+'<li>当触发防盗链时,将直接返回404状态</li>'
					+'</ul>'
				+'</div>'
		$("#webedit-con").html(mbody);
	});
}

//设置防盗链
function SetSecurity(name,id){
	var data = {
		fix:$("input[name='sec_fix']").val(),
		domains:$("input[name='sec_domains']").val(),
		status:$("input[name='sec_status']").val(),
		name:name,
		id:id
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=SetSecurity',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status) setTimeout(function(){Security(id,name);},1000);
	});
}


//木马扫描
function CheckSafe(id,act){
	if(act != undefined){
		var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=CheckSafe','id='+id,function(rdata){
			$(".btnStart").hide()
			setTimeout(function(){
				CheckSafe(id);
			},3000);
			GetTaskCount();
			layer.close(loadT)
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
		});
		
		return;
	}
	
   $.post('/site?action=GetCheckSafe','id='+id,function(rdata){
   		var done = "<button type='button' class='btn btn-success btn-sm btnStart mr5'  onclick=\"CheckSafe("+id+",1)\">"+lan.site.start_scan+"</button>\
   					<button type='button' class='btn btn-default btn-sm btnStart mr20'  onclick=\"UpdateRulelist()\">"+lan.site.update_lib+"</button>\
   					<a class='f14 mr20' style='color:green;'>"+lan.site.scanned+"："+rdata.count+"</a><a class='f14' style='color:red;'>"+lan.site.risk_quantity+"："+rdata.error+"</a>";
   		
   		if(rdata['scan']) done = "<a class='f14 mr20' style='color:green;'>"+lan.site.scanned+"："+rdata.count+"</a><a class='f14' style='color:red;'>"+lan.site.risk_quantity+"："+rdata.error+"</a>";
		var echoHtml = "<div class='mtb15'>"
					   + done
					   +"</div>"
		for(var i=0;i<rdata.phpini.length;i++){
			echoHtml += "<tr><td>"+lan.site.danger_fun+"</td><td>"+lan.site.danger+"</td><td>"+lan.site.danger_fun_no+"："+rdata.phpini[i].function+"<br>"+lan.site.file+"：<a style='color: red;' href='javascript:;' onclick=\"OnlineEditFile(0,'/www/server/php/"+rdata.phpini[i].version+"/etc/php.ini')\">/www/server/php/"+rdata.phpini[i].version+"/etc/php.ini</a></td></tr>";
		}
		
		if(!rdata.sshd){
			echoHtml += "<tr><td>"+lan.site.ssh_port+"</td><td>"+lan.site.high_risk+"</td><td>"+lan.site.sshd_tampering+"</td></tr>";
		}
		
		if(!rdata.userini){
			echoHtml += "<tr><td>"+lan.site.xss_attack+"</td><td>"+lan.site.danger+"</td><td>"+lan.site.site_xss_attack+"</td></tr>";
		}
		
		for(var i=0;i<rdata.data.length;i++){
			echoHtml += "<tr><td>"+rdata.data[i].msg+"</td><td>"+rdata.data[i].level+"</td><td>文件：<a style='color: red;' href='javascript:;' onclick=\"OnlineEditFile(0,'"+rdata.data[i].filename+"')\">"+rdata.data[i].filename+"</a><br>"+lan.site.mod_time+"："+rdata.data[i].etime+"<br>"+lan.site.code+"："+rdata.data[i].code+"</td></tr>";
		}

		var body = "<div>"
					+"<div class='divtable mtb15'><table class='table table-hover' width='100%' style='margin-bottom:0'>"
				  	+"<thead><tr><th width='100px'>"+lan.site.behavior+"</th><th width='70px'>"+lan.site.risk+"</th><th>"+lan.site.details+"</th></tr></thead>"
				   	+"<tbody id='checkDomain'>" + echoHtml + "</tbody>"
				   	+"</table></div>"
		
		$("#webedit-con").html(body);
		$(".btnStart").click(function(){
			fly('btnStart');	
		});
		if(rdata['scan']){
			c = $("#site_"+id).attr('class');
			if(c != 'active') return;
			setTimeout(function(){
				CheckSafe(id);
			},1000);
		}
	});
}

function UpdateRulelist(){
	var loadT = layer.msg(lan.site.to_update,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=UpdateRulelist','',function(rdata){
		layer.close(loadT)
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	});
	
}


//流量限制
function limitNet(id){
	$.post('site?action=GetLimitNet&id='+id,function(rdata){
		var status_selected = rdata.perserver != 0?'checked':'';
		if(rdata.perserver == 0){
			rdata.perserver = 300;
			rdata.perip = 25;
			rdata.limit_rate = 512;
		}
		var limitList = "<option value='1' "+((rdata.perserver == 0 || rdata.perserver == 300)?'selected':'')+">"+lan.site.limit_net_1+"</option>"
						+"<option value='2' "+((rdata.perserver == 200)?'selected':'')+">"+lan.site.limit_net_2+"</option>"
						+"<option value='3' "+((rdata.perserver == 50)?'selected':'')+">"+lan.site.limit_net_3+"</option>"
						+"<option value='4' "+((rdata.perserver == 500)?'selected':'')+">"+lan.site.limit_net_4+"</option>"
						+"<option value='5'  "+((rdata.perserver == 400)?'selected':'')+">"+lan.site.limit_net_5+"</option>"
						+"<option value='6' "+((rdata.perserver == 60)?'selected':'')+">"+lan.site.limit_net_6+"</option>"
						+"<option value='7' "+((rdata.perserver == 150)?'selected':'')+">"+lan.site.limit_net_7+"</option>"
		var body = "<div class='dirBinding flow c4'>"
				+'<p class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="SaveLimitNet('+id+')" style="width:15px;height:15px;margin-right:5px" />'+lan.site.limit_net_8+'</label></p>'
				+"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_9+"：</span><select class='bt-input-text mr20' name='limit' style='width:90px'>"+limitList+"</select></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_10+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perserver' value='"+rdata.perserver+"' /></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_12+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perip' value='"+rdata.perip+"' /></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_14+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='limit_rate' value='"+rdata.limit_rate+"' /></p>"
			    +"<button class='btn btn-success btn-sm mt10' onclick='SaveLimitNet("+id+",1)'>"+lan.public.save+"</button>"
			    +"</div>"
				+"<ul class='help-info-text c7 mtb15'><li>"+lan.site.limit_net_11+"</li><li>"+lan.site.limit_net_13+"</li><li>"+lan.site.limit_net_15+"</li></ul>"
			$("#webedit-con").html(body);
			
			$("select[name='limit']").change(function(){
				var type = $(this).val();
				perserver = 300;
				perip = 25;
				limit_rate = 512;
				switch(type){
					case '1':
						perserver = 300;
						perip = 25;
						limit_rate = 512;
						break;
					case '2':
						perserver = 200;
						perip = 10;
						limit_rate = 1024;
						break;
					case '3':
						perserver = 50;
						perip = 3;
						limit_rate = 2048;
						break;
					case '4':
						perserver = 500;
						perip = 10;
						limit_rate = 2048;
						break;
					case '5':
						perserver = 400;
						perip = 15;
						limit_rate = 1024;
						break;
					case '6':
						perserver = 60;
						perip = 10;
						limit_rate = 512;
						break;
					case '7':
						perserver = 150;
						perip = 4;
						limit_rate = 1024;
						break;
				}
				
				
				$("input[name='perserver']").val(perserver);
				$("input[name='perip']").val(perip);
				$("input[name='limit_rate']").val(limit_rate);
			});
	});
}


//保存流量限制配置
function SaveLimitNet(id,type){
	var isChecked = $("input[name='status']").attr('checked');
	if(isChecked == undefined || type == 1){
		var data = 'id='+id+'&perserver='+$("input[name='perserver']").val()+'&perip='+$("input[name='perip']").val()+'&limit_rate='+$("input[name='limit_rate']").val();
		var loadT = layer.msg(lan.public.config,{icon:16,time:10000})
		$.post('site?action=SetLimitNet',data,function(rdata){
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	}else{
		var loadT = layer.msg(lan.public.config,{icon:16,time:10000})
		$.post('site?action=CloseLimitNet&id='+id,function(rdata){
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	}
}


//子目录绑定
function DirBinding(id){
	$.post('/site?action=GetDirBinding&id='+id,function(rdata){
		var echoHtml = '';
		for(var i=0;i<rdata.binding.length;i++){
			echoHtml += "<tr><td>"+rdata.binding[i].domain+"</td><td>"+rdata.binding[i].port+"</td><td>"+rdata.binding[i].path+"</td><td class='text-right'><a class='btlink' href='javascript:SetDirRewrite("+rdata.binding[i].id+");'>"+lan.site.site_menu_4+"</a> | <a class='btlink' href='javascript:DelBinding("+rdata.binding[i].id+","+id+");'>"+lan.public.del+"</a></td></tr>";
		}
		
		var dirList = '';
		for(var n=0;n<rdata.dirs.length;n++){
			dirList += "<option value='"+rdata.dirs[n]+"'>"+rdata.dirs[n]+"</option>";
		}
		
		var body = "<div class='dirBinding c5'>"
			   +lan.site.domain+"：<input class='bt-input-text mr20' type='text' name='domain' />"
			   +lan.site.subdirectories+"：<select class='bt-input-text mr20' name='dirName'>"+dirList+"</select>"
			   +"<button class='btn btn-success btn-sm' onclick='AddDirBinding("+id+")'>"+lan.public.add+"</button>"
			   +"</div>"
			   +"<div class='divtable mtb15' style='height:470px;overflow:auto'><table class='table table-hover' width='100%' style='margin-bottom:0'>"
			   +"<thead><tr><th>"+lan.site.domain+"</th><th width='70'>"+lan.site.port+"</th><th width='100'>"+lan.site.subdirectories+"</th><th width='100' class='text-right'>"+lan.site.operate+"</th></tr></thead>"
			   +"<tbody id='checkDomain'>" + echoHtml + "</tbody>"
			   +"</table></div>"
		
		$("#webedit-con").html(body);
	})
	
}

//子目录伪静态
function SetDirRewrite(id){
	$.post('/site?action=GetDirRewrite&id='+id,function(rdata){
		if(!rdata.status){
			var confirmObj = layer.confirm(lan.site.url_rewrite_alter,{icon:3,closeBtn:2},function(){
				$.post('/site?action=GetDirRewrite&id='+id+'&add=1',function(rdata){
					layer.close(confirmObj);
					ShowRewrite(rdata);
				});
			});
			return;
		}
		ShowRewrite(rdata);
	});
}

//显示伪静态
function ShowRewrite(rdata){
	var rList = ''; 
	for(var i=0;i<rdata.rlist.length;i++){
		rList += "<option value='"+rdata.rlist[i]+"'>"+rdata.rlist[i]+"</option>";
	}
	var webBakHtml = "<div class='c5 plr15'>\
						<div class='line'>\
						<select class='bt-input-text mr20' id='myRewrite' name='rewrite' style='width:30%;'>"+rList+"</select>\
						<span>"+lan.site.rule_cov_tool+"：<a class='btlink' href='https://www.bt.cn/Tools' target='_blank'>"+lan.site.a_c_n+"</a>\</span>\
						<textarea class='bt-input-text mtb15' style='height: 260px; width: 470px; line-height:18px;padding:5px;' id='rewriteBody'>"+rdata.data+"</textarea></div>\
						<button id='SetRewriteBtn' class='btn btn-success btn-sm' onclick=\"SetRewrite('"+rdata.filename+"')\">"+lan.public.save+"</button>\
						<ul class='help-info-text c7 ptb10'>\
							<li>"+lan.site.url_rw_help_1+"</li>\
							<li>"+lan.site.url_rw_help_2+"</li>\
						</ul>\
						</div>";
	layer.open({
		type: 1,
		area: '500px',
		title: lan.site.config_url,
		closeBtn: 2,
		shift: 5,
		shadeClose: true,
		content:webBakHtml
	});
	
	$("#myRewrite").change(function(){
		var rewriteName = $(this).val();
		$.post('/files?action=GetFileBody','path=/www/server/panel/rewrite/'+getCookie('serverType')+'/'+rewriteName+'.conf',function(fileBody){
			 $("#rewriteBody").val(fileBody.data);
		});
	});
}

//添加子目录绑定
function AddDirBinding(id){
	var domain = $("input[name='domain']").val();
	var dirName = $("select[name='dirName']").val();
	if(domain == '' || dirName == '' || dirName == null){
		layer.msg(lan.site.d_s_empty,{icon:2});
		return;
	}
	
	var data = 'id='+id+'&domain='+domain+'&dirName='+dirName
	$.post('site?action=AddDirBinding',data,function(rdata){
		DirBinding(id);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
	
}

//删除子目录绑定
function DelBinding(id,siteId){
	layer.confirm(lan.site.s_bin_del,{icon:3,closeBtn:2},function(){
		$.post('site?action=DelDirBinding','id='+id,function(rdata){
			DirBinding(siteId);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	});
}


//反向代理
function Proxy(siteName,type){
	if(type == 1){
		type = $("input[name='status']").attr('checked')?'0':'1';
		toUrl = encodeURIComponent($("input[name='toUrl']").val());
		toDomain = encodeURIComponent($("input[name='toDomain']").val());
		var sub1 = encodeURIComponent($("input[name='sub1']").val());
		var sub2 = encodeURIComponent($("input[name='sub2']").val());
		var data = 'name='+siteName+'&type='+type+'&proxyUrl='+toUrl+'&toDomain=' + toDomain + '&sub1=' + sub1 + '&sub2=' + sub2;
		var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=SetProxy',data,function(rdata){
			layer.close(loadT);
			if(rdata.status) {
				Proxy(siteName);
			}else{
				$("input[name='status']").attr('checked',false)
			}
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
		return;
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=GetProxy','name='+siteName,function(rdata){
		layer.close(loadT);
		if(rdata.proxyUrl == null) rdata.proxyUrl = '';
		var status_selected = rdata.status?'checked':'';
		var disabled = rdata.status?'disabled':'';
		var body = "<div>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.proxy_url+"</span><input "+disabled+" class='bt-input-text' type='text' name='toUrl' value='"+rdata.proxyUrl+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;' placeholder='"+lan.site.proxy_url_info+"' /></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.proxy_domain+"</span><input "+disabled+" class='bt-input-text' type='text' name='toDomain' value='"+rdata.toDomain+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;' placeholder='"+lan.site.proxy_domian_info+"' /></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.con_rep+"</span><input "+disabled+" class='bt-input-text' type='text' name='sub1' value='"+rdata.sub1+"' style='margin-left: 5px;width: 182px;height: 30px;margin-right:10px;' placeholder='"+lan.site.con_rep_info+"' />"
			   +"<input class='bt-input-text' type='text' name='sub2' "+disabled+" value='"+rdata.sub2+"' style='margin-left: 5px;width: 183px;height: 30px;margin-right:10px;' placeholder='"+lan.site.to_con+"' /></p>"
			   +'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="Proxy(\''+siteName+'\',1)" />'+lan.site.proxy_enable+'</label><label style="margin-left: 18px;"><input '+(rdata.cache?'checked':'')+' type="checkbox" name="status" onclick="OpenCache(\''+siteName+'\',1)" />'+lan.site.proxy_cache+'</label></div>'
			   +'<ul class="help-info-text c7 ptb10">'
			   +'<li>'+lan.site.proxy_help_1+'</li>'
			   +'<li>'+lan.site.proxy_help_2+'</li>'
			   +'<li>'+lan.site.proxy_help_3+'</li>'
			   +'<li>'+lan.site.proxy_help_4+'</li>'
			   +'<li>'+lan.site.proxy_help_5+'</li>'
			   +'</ul>'
			   +"</div>";
			$("#webedit-con").html(body);
	});
}

//开启缓存
function OpenCache(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=ProxyCache',{siteName:siteName},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}
		
//301重定向
function To301(siteName,type){
	if(type == 1){
		type = $("input[name='status']").attr('checked')?'0':'1';
		toUrl = encodeURIComponent($("input[name='toUrl']").val());
		srcDomain = encodeURIComponent($("select[name='srcDomain']").val());
		var data = 'siteName='+siteName+'&type='+type+'&toDomain='+toUrl+'&srcDomain='+srcDomain;
		$.post('site?action=Set301Status',data,function(rdata){
			To301(siteName);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
		return;
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=Get301Status','siteName='+siteName,function(rdata){
		layer.close(loadT);
		var domain_tmp = rdata.domain.split(',');
		var domains = '';
		var selected = '';
		for(var i=0;i<domain_tmp.length;i++){
			selected = '';
			if(domain_tmp[i] == rdata.src) selected = 'selected';
			domains += "<option value='"+domain_tmp[i]+"' "+selected+">"+domain_tmp[i]+"</option>";
		}
		
		if(rdata.url == null) rdata.url = '';
		var status_selected = rdata.status?'checked':'';
		var isRead = rdata.status?'readonly':'';
		var body = "<div>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 90px;'>"+lan.site.access_domain+"</span><select class='bt-input-text' name='srcDomain' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;"+(rdata.status?'background-color: #eee;':'')+"' "+(rdata.status?'disabled':'')+"><option value='all'>"+lan.site.all_site+"</option>"+domains+"</select></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 90px;'>"+lan.site.target_url+"</span><input class='bt-input-text' type='text' name='toUrl' value='"+rdata.url+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;"+(rdata.status?'background-color: #eee;':'')+"' placeholder='"+lan.site.eg_url+"' "+isRead+" /></p>"
			   +'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="To301(\''+siteName+'\',1)" />'+lan.site.enable_301+'</label></div>'
			   +'<ul class="help-info-text c7 ptb10">'
			   +'<li>'+lan.site.to301_help_1+'</li>'
			   +'<li>'+lan.site.to301_help_2+'</li>'
			   +'</ul>'
			   +"</div>";
			$("#webedit-con").html(body);
	});
}

//验证IP地址
function isValidIP(ip) {
    var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/
    return reg.test(ip);
}
function isContains(str, substr) {
    return str.indexOf(substr) >= 0;
}
//证书夹
function ssl_admin(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.get('/ssl?action=GetCertList',function(rdata){
		layer.close(loadT);
		var tbody = '';
		for(var i=0;i<rdata.length;i++){
			tbody += '<tr><td>'+rdata[i].subject+'</td><td>'+rdata[i].dns.join('<br>')+'</td><td>'+rdata[i].notAfter+'</td><td>'+rdata[i].issuer+'</td><td style="text-align: right;"><a onclick="set_cert_ssl(\''+rdata[i].subject+'\',\''+siteName+'\')" class="btlink">部署</a> | <a onclick="remove_ssl(\''+rdata[i].subject+'\')" class="btlink">删除</a></td></tr>'
		}
		var txt = '<div class="mtb15" style="line-height:30px">\
		<button style="margin-bottom: 7px;display:none;" class="btn btn-success btn-sm">添加</button>\
		<div class="divtable"><div id="ssl-fold-list" style="max-height:470px;overflow:auto;border:#ddd 1px solid"><table class="table table-hover" style="border:none"><thead><tr><th>域名</th><th>信任名称</th><th>到期时间</th><th>品牌</th><th class="text-right" width="120">操作</th></tr></thead>\
		<tbody>'+tbody+'</tbody>\
		</table></div></div></div>';
		$(".tab-con").html(txt);
	});
}

//删除证书
function remove_ssl(certName){
	SafeMessage('删除证书','您真的要从证书夹删除证书吗?',function(){
		var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/ssl?action=RemoveCert',{certName:certName},function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			$("#ssl_admin").click();
		});
	});
}

//从证书夹部署
function set_cert_ssl(certName,siteName){
	var loadT = layer.msg('正在部署证书...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/ssl?action=SetCertToSite',{certName:certName,siteName:siteName},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//宝塔ssl
function SetSSL(id,siteName){
	var mBody = '<div class="tab-nav">\
					<span class="on" onclick="BTssl(\'a\','+id+',\''+siteName+'\')">'+lan.site.bt_ssl+'</span>\
					<span onclick="BTssl(\'lets\','+id+',\''+siteName+'\')">Let\'s Encrypt</span>\
					<span onclick="BTssl(\'other\','+id+',\''+siteName+'\')">'+lan.site.other_ssl+'</span>\
					<span class="sslclose" onclick="closeSSL(\''+siteName+'\')">'+lan.public.close+'</span>\
					<span id="ssl_admin" onclick="ssl_admin(\''+siteName+'\')">证书夹</span>'
					+ '<div class="ss-text pull-right mr30" style="position: relative;top:-4px">\
	                    <em>强制HTTPS</em>\
	                    <div class="ssh-item">\
	                    	<input class="btswitch btswitch-ios" id="toHttps" type="checkbox">\
	                    	<label class="btswitch-btn" for="toHttps" onclick="httpToHttps(\''+siteName+'\')"></label>\
	                    </div>\
	                </div></div>'
			  + '<div class="tab-con" style="padding: 0px;"></div>'
			  
	$("#webedit-con").html(mBody);
	//BTssl('a',id,siteName);
	$(".tab-nav span").click(function(){
		$(this).addClass("on").siblings().removeClass("on");
	});
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('site?action=GetSSL','siteName='+siteName,function(rdata){
		layer.close(loadT);
		$("#toHttps").attr('checked',rdata.httpTohttps);
		switch(rdata.type){
			case -1:
				$(".tab-nav span").eq(3).addClass("on").siblings().removeClass("on");
				var txt = "<div class='mtb15'  style='line-height:30px'>"+lan.site.ssl_help_1+"</div>";
				$(".tab-con").html(txt);
				break;
			case 1:
				$(".tab-nav span").eq(1).addClass("on").siblings().removeClass("on");
				setCookie('letssl',1);
				var lets = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.csr+'</textarea></div>'
					+ '</div>'
					+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.ssl_help_2+'</li><li>'+lan.site.ssl_help_3+'</li></ul>'
				$(".tab-con").html(lets);
				$(".help-info-text").after("<div class='line mtb15'><button class='btn btn-default btn-sm' onclick=\"OcSSL('CloseSSLConf','"+siteName+"')\" style='margin-left:10px'>"+lan.site.ssl_close+"</button></div>");
				break;
			case 0:
				$(".tab-nav span").eq(2).addClass("on").siblings().removeClass("on");
				BTssl('other',id,siteName);
				break;
			case 2:
				$(".tab-nav span").eq(0).addClass("on").siblings().removeClass("on");
				BTssl('a',id,siteName);
				break;
		}
	})
}
//关闭SSL
function closeSSL(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('site?action=GetSSL','siteName='+siteName,function(rdata){
		layer.close(loadT);
		switch(rdata.type){
			case -1:
				var txt = "<div class='mtb15' style='line-height:30px'>"+lan.site.ssl_help_1+"</div>";
				setCookie('letssl',0);
				$(".tab-con").html(txt);
				break;
			case 1:
				var txt = "Let's Encrypt";
				closeSSLHTML(txt,siteName);
				break;
			case 0:
				var txt = lan.site.other;
				closeSSLHTML(txt,siteName);
				break;
			case 2:
				var txt = lan.site.bt_ssl;
				closeSSLHTML(txt,siteName);
				break;
		}
	})
}

//设置httpToHttps
function httpToHttps(siteName){
	var isHttps = $("#toHttps").attr('checked');
	if(isHttps){
		layer.confirm('关闭强制HTTPS后需要清空浏览器缓存才能看到效果,继续吗?',{icon:3,title:"关闭强制HTTPS"},function(){
			$.post('site?action=CloseToHttps','siteName='+siteName,function(rdata){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
			});
		});
	}else{
		$.post('site?action=HttpToHttps','siteName='+siteName,function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	}
}

//关闭SSL内容
function closeSSLHTML(txt,siteName){
	$(".tab-con").html("<div class='line mtb15'>"+lan.get('ssl_enable',[txt])+"</div><div class='line mtb15'><button class='btn btn-success btn-sm' onclick=\"OcSSL('CloseSSLConf','"+siteName+"')\">"+lan.site.ssl_close+"</button></div>");
}

//宝塔SSL
function BTssl(type,id,siteName){
	var a = '<div class="btssl"><div class="alert alert-warning" style="padding:10px">'+lan.site.bt_bind_no+'</div>'
			+ '<div class="line mtb10"><span class="tname text-right mr20">'+lan.site.bt_user+'</span><input id="btusername" class="bt-input-text" type="text" name="bt_panel_username" maxlength="11" style="width:200px" ><i style="font-style:normal;margin-left:10px;color:#999"></i></div>'
			+ '<div class="line mtb10"><span class="tname text-right mr20">'+lan.site.password+'</span><input id="btpassword" class="bt-input-text" type="password" name="bt_panel_password" style="width:200px" ></div>'
			+ '<div class="line mtb15" style="margin-left:100px"><button class="btn btn-success btn-sm mr20 btlogin">'+lan.site.login+'</button><button class="btn btn-success btn-sm" onclick="javascript:window.open(\'https://www.bt.cn/register.html\')">'+lan.site.bt_reg+'</button></div>'
			+ '<ul class="help-info-text c7 ptb15"><li style="color:red">'+lan.site.bt_ssl_help_1+'</li><li>'+lan.site.bt_ssl_help_2+'</li><li>'+lan.site.bt_ssl_help_3+'</li><li>'+lan.site.bt_ssl_help_4+'</li></ul>'
			+ '</div>';
	var b = '<div class="btssl"><div class="line mtb15"><span class="tname text-center">'+lan.site.domain+'</span><select id="domainlist" class="bt-input-text" style="width:220px"></select></div>'
		  + '<div class="line mtb15" style="margin-left:100px"><button class="btn btn-success btn-sm btsslApply">'+lan.site.btapply+'</button></div>'
		  + '<div class="btssllist mtb15"><div class="divtable"><div id="btssl_table_list" style="max-height:205px;border:#ddd 1px solid;overflow:auto"><table class="table table-hover" style="border:none"><thead><tr><th>'+lan.site.domain+'</th><th>'+lan.site.endtime+'</th><th>'+lan.site.status+'<a href="https://www.bt.cn/bbs/thread-7860-1-1.html" class="bt-ico-ask" title="查看说明" target="_blank">?</a></th><th class="text-right" width="120">'+lan.site.operate+'</th></tr></thead><tbody id="ssllist"></tbody></table></div></div></div>'
		  + '<ul class="help-info-text c7"><li>'+lan.site.bt_ssl_help_5+'(包括根域名)</li><li>'+lan.site.bt_ssl_help_6+'</li><li>'+lan.site.bt_ssl_help_7+'</li><li>建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称</li><li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li><li>99%的用户都可以轻易自助部署，如果您不懂，<a class="btlink" href="https://www.bt.cn/yunwei" target="_blank">宝塔提供证书部署服务50元一次</a></li></ul>'
		  + '</div>';
	
	var lets =  '<div class="btssl"><div class="label-input-group">'
			  + '<div class="line mtb10"><form><span class="tname text-center">验证方式</span><div style="margin-top:7px;display:inline-block"><input type="radio" name="c_type" onclick="file_check()" id="check_file" checked="checked" /><label class="mr20" for="check_file" style="font-weight:normal">文件验证</label><input type="radio" onclick="dns_check()" name="c_type" id="check_dns" /><label class="mr20" for="check_dns" style="font-weight:normal">DNS验证</label></div></form></div>'
			  + '<div class="check_message line"><div style="margin-left:100px"><input type="checkbox" name="checkDomain" id="checkDomain" checked=""><label class="mr20" for="checkDomain" style="font-weight:normal">提前校验域名(提前发现问题,减少失败率)</label></div></div>'
			  + '</div><div class="line mtb10"><span class="tname text-center">管理员邮箱</span><input class="bt-input-text" style="width:240px;" type="text" name="admin_email" /></div>'
			  + '<div class="line mtb10"><span class="tname text-center">'+lan.site.domain+'</span><ul id="ymlist" style="padding: 5px 10px;max-height:180px;overflow:auto; width:240px;border:#ccc 1px solid;border-radius:3px"></ul></div>'
			  + '<div class="line mtb10" style="margin-left:100px"><button class="btn btn-success btn-sm letsApply">'+lan.site.btapply+'</button></div>'
			  + '<ul class="help-info-text c7" id="lets_help"><li>'+lan.site.bt_ssl_help_5+'</li><li>'+lan.site.bt_ssl_help_8+'</li><li>'+lan.site.bt_ssl_help_9+'</li><li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li></ul>'
			  + '</div>';
	
	var other = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text"></textarea></div>'
					+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text"></textarea></div>'
					+ '<div class="ssl-btn pull-left mtb15" style="width:100%"><button class="btn btn-success btn-sm" onclick="SaveSSL(\''+siteName+'\')">'+lan.public.save+'</button></div></div>'
					+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.bt_ssl_help_10+'</li><li>如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书</li><li>PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt</li><li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li></ul>';
					
	switch(type){
		case 'a':
			$.get("/ssl?action=GetUserInfo",function(rdata){
				if(rdata.status){
					BTssl('b',id,siteName);
				}
				else{
					$(".tab-con").html(a);
					$("#btusername").blur(function(){
						if(!(/^1(3|4|5|7|8)\d{9}$/.test($(this).val()))){ 
							$("#btusername").css("border","1px solid #e53451");
							$("#btusername").next("i").html(lan.site.phone_input);
						}
						else{
							$("#btusername").removeAttr("style").css("width","200px");
							$("#btusername").next("i").empty();
						}
					});
					$(".btlogin").click(function(){
						var data = "username="+$("#btusername").val()+"&password="+$("#btpassword").val();
						$.post("/ssl?action=GetToken",data,function(tdata){
							if(tdata.status){
								layer.msg(tdata.msg,{icon:1});
								BTssl('b',id,siteName);
							}
							else{
								layer.msg(tdata.msg,{icon:2})
							}
						})
					})
				}
			});
			break;
		case 'b':
			$(".tab-con").html(b);
			var opt = '';
			$.get('/data?action=getData&table=domain&list=True&search=' + id, function(rdata) {
				for(var i=0;i<rdata.length;i++){
					var isIP = isValidIP(rdata[i].name);
					var x = isContains(rdata[i].name, '*');
					if(!isIP && !x){
						opt+='<option>'+rdata[i].name+'</option>'
					}
				}
				$("#domainlist").html(opt);
			})
			getSSLlist(siteName);
			$(".btsslApply").click(function(){
				var ym = $("#domainlist").val();
				if(ym.indexOf('www.') != -1){
					var len = $("#domainlist")[0].length;
					var rootDomain = ym.split(/www\./)[1];
					var mn = 0;
					for(var i=0;i<len;i++){
						if($("#domainlist")[0][i].innerText == rootDomain) mn++;
					}
					if(mn < 1){
						layer.msg('您为域名['+ym+']申请证书，但程序检测到您没有将其根域名['+rootDomain+']绑定并解析到站点，这会导致证书签发失败!',{icon:2,time:5000});
						return;
					}
				}
				
				$.post("/data?action=getKey","table=sites&key=path&id="+id,function(rdata){
					//第一步
					var loadT = layer.msg(lan.site.ssl_apply_1,{icon:16,time:0,shade:0.3});
					$.post("/ssl?action=GetDVSSL","domain="+ym+"&path="+rdata,function(tdata){
						layer.close(loadT);
						if(tdata.status){
							layer.msg(tdata.msg,{icon:1});
							var partnerOrderId = tdata.data.partnerOrderId;
							//第二步
							var loadT = layer.msg(lan.site.ssl_apply_2,{icon:16,time:0,shade:0.3});
							$.post("/ssl?action=Completed","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(ydata){
								layer.close(loadT);
								if(!ydata.status){
									layer.msg(ydata.msg,{icon:2});
									getSSLlist(siteName);
									return;
								}
								//第三步
								var loadT = layer.msg(lan.site.ssl_apply_3,{icon:16,time:0,shade:0.3});
								$.post("/ssl?action=GetSSLInfo","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(zdata){
									layer.close(loadT);
									layer.msg(zdata.msg,{icon:zdata.status?1:2});
									getSSLlist(siteName);
								});
							});
							
						}
						else{
							layer.msg(tdata.msg,{icon:2})
						}
					})
				})
			});
			break;
		case 'lets':
			/*
			$.get("/ssl?action=GetUserInfo",function(sdata){
				if(!sdata.status){
					$(".tab-con").html(a);
					$(".help-info-text").html("<li>"+lan.site.+"</li><li>let's Encrypt证书有效期为3个月</li><li>3个月有效期后自动续签</li>");
					$("#btusername").blur(function(){
						if(!(/^1(3|4|5|7|8)\d{9}$/.test($(this).val()))){ 
							$("#btusername").css("border","1px solid #e53451");
							$("#btusername").next("i").html(lan.site.phone_input);
						}
						else{
							$("#btusername").removeAttr("style").css("width","200px");
							$("#btusername").next("i").empty();
						}
					});
					$(".btlogin").click(function(){
						var data = "username="+$("#btusername").val()+"&password="+$("#btpassword").val();
						$.post("/ssl?action=GetToken",data,function(tdata){
							if(tdata.status){
								layer.msg(tdata.msg,{icon:1});
								BTssl('lets',id,siteName);
							}
							else{
								layer.msg(tdata.msg,{icon:2})
							}
						})
					})
				}
				else{}
			});*/
			if(getCookie('letssl') == 1){
				$.post('site?action=GetSSL','siteName='+siteName,function(rdata){
					if(rdata.csr === false){
						setCookie('letssl',0);
						BTssl(type,id,siteName);
						return;
					}
					var lets = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.key+'</textarea></div>'
						+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.csr+'</textarea></div>'
						+ '</div>'
						+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.ssl_help_2+'</li><li>'+lan.site.ssl_help_3+'</li></ul>';
					$(".tab-con").html(lets);
					$(".help-info-text").after("<div class='line mtb15'><button class='btn btn-default btn-sm' onclick=\"OcSSL('CloseSSLConf','"+siteName+"')\" style='margin-left:10px'>"+lan.site.ssl_close+"</button></div>");
				});
				return;
			}
			$(".tab-con").html(lets);
			var opt='';
			$.post('/site?action=GetSiteDomains',{id:id}, function(rdata) {
				for(var i=0;i<rdata.domains.length;i++){
					var isIP = isValidIP(rdata.domains[i].name);
					//var x = isContains(rdata.domains[i].name, '*');
					if(!isIP){
						opt+='<li style="line-height:26px"><input type="checkbox" style="margin-right:5px; vertical-align:-2px" value="'+rdata.domains[i].name+'">'+rdata.domains[i].name+'</li>'
					}
				}
				$("input[name='admin_email']").val(rdata.email);
				$("#ymlist").html(opt);
				$("#ymlist li input").click(function(e){
					e.stopPropagation();
				})
				$("#ymlist li").click(function(){
					var o = $(this).find("input");
					if(o.prop("checked")){
						o.prop("checked",false)
					}
					else{
						o.prop("checked",true);
					}
				})
				$(".letsApply").click(function(){
					var c = $("#ymlist input[type='checkbox']");
					var str = [];
					var domains = '';
					for(var i=0; i<c.length; i++){
						if(c[i].checked){
							str.push(c[i].value);
						}
					}
					domains = JSON.stringify(str);
					newSSL(siteName,domains);
					
				})
			});
			break;
		case 'other':
			$(".tab-con").html(other);
			var key = '';
			var csr = '';
			var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
			$.post('site?action=GetSSL','siteName='+siteName,function(rdata){
				layer.close(loadT);
				if(rdata.status){
					$(".ssl-btn").append("<button class='btn btn-default btn-sm' onclick=\"OcSSL('CloseSSLConf','"+siteName+"')\" style='margin-left:10px'>"+lan.site.ssl_close+"</button>");
				}
				if(rdata.key == false) rdata.key = '';
				if(rdata.csr == false) rdata.csr = '';
				$("#key").val(rdata.key);
				$("#csr").val(rdata.csr);
			});
			break;
	}
	table_fixed("btssl_table_list")
}

//文件验证
function file_check(){
	$(".check_message").html('<div style="margin-left:100px"><input type="checkbox" name="checkDomain" id="checkDomain" checked=""><label class="mr20" for="checkDomain" style="font-weight:normal">提前校验域名(提前发现问题,减少失败率)</label></div>');
	$("#lets_help").html('<li>'+lan.site.bt_ssl_help_5+'</li><li>'+lan.site.bt_ssl_help_8+'</li><li>'+lan.site.bt_ssl_help_9+'</li><li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li>');
}

dnsapis = {};

//DNS验证
function dns_check(){
	var loadT = layer.msg('正在安装DNS组件,请稍候...',{icon:16,time:0,shade:0.3});
	$.post('/site?action=GetDnsApi',{},function(rdata){
		layer.close(loadT)
		var obody = '<span class="tname">选择DNS接口</span><select onchange="dns_select(this)" class="bt-input-text" style="width:120px" name="dns_select" id="dns_selects">';
		for(var i=0;i<rdata.length;i++){
			dnsapis[rdata[i]['name']] = rdata[i];
			obody += '<option value="'+rdata[i]['name']+'" title="'+rdata[i]['ps']+'">'+rdata[i]['title']+'</option>';
		}
		obody += '</select><span id="dnsapi_edit"></span> 等待 <input type="number" class="bt-input-text" name="dnssleep" value="20" style="width:50px;vertical-align:-1px" min="10" max="120" />秒'
		$(".check_message").html(obody);
		$("#lets_help").html("<li>在DNS验证中，我们提供了3个自动化DNS-API，并提供了手动模式</li><li>使用DNS接口申请证书可自动续期，手动模式下证书到期后手需重新申请</li><li>使用【宝塔DNS云解析】接口前您需要确认当前要申请SSL证书的域名DNS为【云解析】</li><li>使用【DnsPod/阿里云DNS】接口前您需要先在弹出的窗口中设置对应接口的API</li>")
	});
}

//DNSAPI选择事件
function dns_select(obj,force){
	if(!obj) obj = $("#dns_selects")[0];
	if(obj.value == 'dns_bt'){
		layer.msg('请注意：被申请SSL证书的域名必需使用【云解析】插件作为DNS服务器才能使用此选项',{icon:3,time:5000});
	}
	
	if(dnsapis[obj.value]['data'] == false){
		$("#dnsapi_edit").html('');
		return true;
	}
	
	if(dnsapis[obj.value]['data'][0]['value'] == '' || force == true){
		var input_body = '';
		for(var i=0;i<dnsapis[obj.value].data.length;i++){
			input_body += '<div class="line">\
								<span class="tname">'+dnsapis[obj.value]['data'][i]['name']+':</span>\
								<div class="info-r">\
									<input class="bt-input-text" type="text" name="'+dnsapis[obj.value]['data'][i]['key']+'" placeholder="" value="'+dnsapis[obj.value]['data'][i]['value']+'" style="width:100%">\
								</div>\
							</div>'
		}
		
		var tbody = '<form class="bt-form pd20 pb70" id="dnsapi_form">'+input_body+'\
			<ul class="help-info-text c7"><li>'+dnsapis[obj.value].help+'</li></ul>\
			<div class="bt-form-submit-btn">\
				<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.close(loadT2)">关闭</button>\
				<button type="button" class="btn btn-success btn-sm btn-title" onclick="set_dnsapi()">确定</button>\
			</div>\
		</form>'
		
		loadT2 = layer.open({
				type: 1,
				shift: 5,
				closeBtn: 2,
				area: '500px', 
				title: "设置["+dnsapis[obj.value]['title']+"]接口",
				content: tbody
			});
	}
	
	tbody = '<button onclick="dns_select(false,true)" class="btn btn-default btn-sm" style="margin-left: 5px;margin-right: 5px;margin-top: -4px;">设置</button>'
	$("#dnsapi_edit").html(tbody)
	
}


//设置DNS-API
function set_dnsapi(){
	var arr = $("#dnsapi_form").serializeArray();
	pdata = {}
	for(var i=0;i<arr.length;i++){
		pdata[arr[i].name] = arr[i].value;
	}
	$.post('/site?action=SetDnsApi',{pdata:JSON.stringify(pdata)},function(rdata){
		layer.close(loadT2);
		layer.msg('设置成功!',{icon:1});
		dns_check()
	});
}

//取证书列表
function getSSLlist(siteName){
	var tr='';
	var loadT = layer.msg(lan.site.get_ssl_list,{icon:16,time:0,shade:0.3});
	$.get("/ssl?action=GetOrderList&siteName="+siteName,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			for(var i=0;i<rdata.data.length;i++){
				var txt = '';
				var tips = '';
				var icoask = '';
				txt = (rdata.data[i].stateName == lan.site.order_success) ? '<a href="javascript:onekeySSl(\''+rdata.data[i].partnerOrderId+'\',\''+siteName+'\');" class="btlink">'+lan.site.deploy+'</a>' : '';
				if(rdata.data[i].stateName == lan.site.domain_wait) {
					txt = '<a href="javascript:VerifyDomain(\''+rdata.data[i].partnerOrderId+'\',\''+siteName+'\');" class="btlink">'+lan.site.domain_validate+'</a>';
					//tips = lan.site.domain_check;
					//icoask = '<i class="ico-font-ask" title="'+tips+'">?</i>';
				}
				if(rdata.data[i].setup){
					txt = lan.site.deployed+' | <a class="btlink" href="javascript:OcSSL(\'CloseSSLConf\',\''+siteName+'\')">'+lan.public.close+'</a></div>';
				}
				
				tr += '<tr><td>'+rdata.data[i].commonName+'</td><td>'+getLocalTime(rdata.data[i].endtime).split(" ")[0]+'</td><td title='+tips+'>'+rdata.data[i].stateName+icoask+'</td><td class="text-right">'+txt+'</td></tr>'
			}
			$("#ssllist").html(tr);
		}
	});
}

//一键部署证书
function onekeySSl(partnerOrderId,siteName){
	var loadT = layer.msg(lan.site.ssl_apply_3,{icon:16,time:0,shade:0.3});
	$.post("/ssl?action=GetSSLInfo","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(zdata){
		layer.close(loadT);
		layer.msg(zdata.msg,{icon:zdata.status?1:2});
		getSSLlist(siteName);
	})
}

//验证域名
function VerifyDomain(partnerOrderId,siteName){
	var loadT = layer.msg(lan.site.ssl_apply_2,{icon:16,time:0,shade:0.3});
	$.post("/ssl?action=Completed","partnerOrderId="+partnerOrderId+'&siteName='+siteName,function(ydata){
		layer.close(loadT);
		if(!ydata.status){
			layer.msg(ydata.msg,{icon:2});
			return;
		}
		//第三步
		var loadT = layer.msg(lan.site.ssl_apply_3,{icon:16,time:0,shade:0.3});
		$.post("/ssl?action=GetSSLInfo","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(zdata){
			layer.close(loadT);
			if(zdata.status) getSSLlist();
			layer.msg(zdata.msg,{icon:zdata.status?1:2});
		});
	});
}

//旧的设置SSL
function SetSSL_old(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('site?action=GetSSL','siteName='+siteName,function(rdata){
		layer.close(loadT);
		var status_selecteda ="";
		var status_selectedb ="";
		var status_selectedc ="";
		if(rdata.key == false) rdata.key = '';
		if(rdata.csr == false) rdata.csr = '';
		switch(rdata.type){
			case -1:
				status_selecteda = "checked='checked'";
				break;
			case 1:
				status_selectedb = "checked='checked'";
				break
			case 0:
				status_selectedc = "checked='checked'";
			default:
				status_selecteda = "checked='checked'";
		}

		var mBody = '<div class="ssl-con c4">'
				  + '<div class="ssl-type label-input-group ptb10"><label class="mr20"><input type="radio" name="type" value="0" '+status_selecteda+'/>'+lan.site.ssl_close+'</label><label class="mr20"><input type="radio" name="type" value="1" '+status_selectedb+'/>'+lan.site.lets_ssl+'</label><label><input class="otherssl" name="type" type="radio" value="2" '+status_selectedc+'>'+lan.site.use_other_ssl+'</label></div>'
				  + '<div class="ssl-type-con"></div>'
				  + '</div>';
		var mykeyhtml = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.csr+'</textarea></div>'
					+ '<div class="ssl-btn pull-left mtb15" style="width:100%"><button class="btn btn-success btn-sm" onclick="ChangeSaveSSL(\''+siteName+'\')">'+lan.site.update_ssl+'</button></div></div>'
					+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.ssl_help_2+'</li><li>'+lan.site.ssl_help_3+'</li></ul>';
		
		var othersslhtml = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text">'+rdata.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text">'+rdata.csr+'</textarea></div>'
					+ '<div class="ssl-btn pull-left mtb15" style="width:100%"><button class="btn btn-success btn-sm" onclick="SaveSSL(\''+siteName+'\')">'+lan.public.save+'</button></div></div>'
					+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.bt_ssl_help_10+'</li></ul>';
		$("#webedit-con").html(mBody);
		if(rdata.type == 1){
			$(".ssl-type-con").html(mykeyhtml);
		}
		if(rdata.type == 0){
			$(".ssl-type-con").html(othersslhtml);
		}
		$("input[type='radio']").click(function(){
			var val = $(this).val();
			if(val == 0){
				OcSSL('CloseSSLConf',siteName)
			}
			if(val == 1){
				OcSSL("CreateLet",siteName);
			}
			if(val == 2){
				//OcSSL("CreateLet",siteName);
				$(".ssl-type-con").html(othersslhtml);
			}
		});
	});

}
//开启与关闭SSL
function OcSSL(action,siteName){
	var loadT = layer.msg(lan.site.get_ssl_list,{icon:16,time:0,shade: [0.3, '#000']});
	$.post("site?action="+action,'siteName='+siteName+'&updateOf=1',function(rdata){
		layer.close(loadT)
		
		if(!rdata.status){
			if(!rdata.out){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				//SetSSL(siteName);
				return;
			}
			
			data = "<p>"+lan.site.get_ssl_err+"：</p><hr />"
			for(var i=0;i<rdata.out.length;i++){
				data += "<p>"+lan.site.domain+": "+rdata.out[i].Domain+"</p>"
					  + "<p>"+lan.site.err_type+": "+rdata.out[i].Type+"</p>"
					  + "<p>"+lan.site.details+": "+rdata.out[i].Detail+"</p>"
					  + "<hr />"
			}
			
			layer.msg(data,{icon:2,time:0,shade:0.3,shadeClose:true});
			return;
		}
		
		setCookie('letssl',0);
		$.post('/system?action=ServiceAdmin','name='+getCookie('serverType')+'&type=reload',function(result){
			//SetSSL(siteName);
			if(!result.status) layer.msg(result.msg,{icon:2});
		});
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(action == 'CloseSSLConf'){
			layer.msg(lan.site.ssl_close_info,{icon:1,time:5000});
		}
		$(".bt-w-menu .bgw").click();
	})
}
var loadT2 = null;
//生成SSL
function newSSL(siteName,domains,renew){
	var loadT = layer.msg('正在验证，这可能需要几分钟时间...',{icon:16,time:0,shade: [0.3, '#000']});
	var force = '';
	var dns = '';
	var dnsapi = '';
	if(renew == undefined){
		if($("#checkDomain").prop("checked")) force = '&force=true';
		if($("#check_dns").prop('checked')){
			dnsapi = $("select[name='dns_select']").val();
			dns = '&dnsapi=' + dnsapi + '&dnssleep=' + $("input[name='dnssleep']").val();
		}
	}else{
		dns = '&renew=True';
	}
	var email = $("input[name='admin_email']").val();
	
	if(domains === false){
		var c = $("#ymlist input[type='checkbox']");
		var str = [];
		var domains = '';
		for(var i=0; i<c.length; i++){
			if(c[i].checked){
				str.push(c[i].value);
			}
		}
		domains = JSON.stringify(str);
	}
	$.post('site?action=CreateLet','siteName='+siteName+'&domains='+domains+'&updateOf=1&email='+email + force + dns,function(rdata){
		layer.close(loadT)
		if(dnsapi == 'dns' && renew == undefined && rdata.status == true){
			var tbody = '<div class="bt-form pd15"><div class="divtable" style="margin:10px;">';
			tbody += '<p style="margin-bottom:10px">请按以下列表做TXT解析:</p>';
			tbody += '<table class="table table-hover" width="100%" style="margin-bottom:10px"><thead><tr><th>解析域名</th><th>TXT记录值</th></tr></thead><tbody>';
			for(var i=0;i<rdata.fullDomain.length;i++){
				tbody += '<tr><td>'+rdata.fullDomain[i]+'</td><td>'+rdata.txtValue[i]+'</td></tr>'
			}
			tbody += '</tbody></table><div class="text-right"><button class="btn btn-success btn-sm" onclick="newSSL(\''+siteName+'\',false,\'renew\')">验证</button></div></div>';	
			tbody += '<ul class="help-info-text c7">'
			tbody += '<li>解析域名需要一定时间来生效,完成所以上所有解析操作手,请至少等待3分钟后再点击验证按钮</li>'
			tbody += '<li>可通过CMD命令来手动验证域名解析是否生效: nslookup -q=txt _acme-challenge.bt.cn</li>'
			tbody += '<li>若您使用的是宝塔云解析插件,阿里云DNS,DnsPod作为DNS,可使用DNS接口自动解析</li>'
			tbody += '</ul></div>'
			loadT2 = layer.open({
				type: 1,
				shift: 5,
				closeBtn: 2,
				area: '700px', 
				title: "手动解析TXT记录",
				content: tbody
			});
			
			return;
		}
		
		if(rdata.status){
			if(loadT2) layer.close(loadT2);
			var mykeyhtml = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">'+lan.site.ssl_key+'<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">'+lan.site.ssl_crt+'<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.csr+'</textarea></div>'
					+ '</div>'
					+ '<ul class="help-info-text c7 pull-left"><li>'+lan.site.ssl_help_2+'</li><li>'+lan.site.ssl_help_3+'</li></ul>';
			$(".btssl").html(mykeyhtml);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setCookie('letssl',1);
			return;
		}
		
		if(!rdata.out){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			//SetSSL(siteName);
			return;
		}
		
		data = "<p>"+rdata.msg+"</p><hr />"
		if(rdata.err[0].length > 10) data += '<p style="color:red;">' + rdata.err[0].replace(/\n/g,'<br>') + '</p>';
		if(rdata.err[1].length > 10) data += '<p style="color:red;">' + rdata.err[1].replace(/\n/g,'<br>') + '</p>';
		setCookie('letssl',0);
		layer.msg(data,{icon:2,area:'500px',time:0,shade:0.3,shadeClose:true});
		
	});
}

//保存SSL
function SaveSSL(siteName){
	var data = 'type=1&siteName='+siteName+'&key='+encodeURIComponent($("#key").val())+'&csr='+encodeURIComponent($("#csr").val());
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:20000,shade: [0.3, '#000']})
	$.post('site?action=SetSSL',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
			$(".ssl-btn").find(".btn-default").remove();
			$(".ssl-btn").append("<button class='btn btn-default btn-sm' onclick=\"OcSSL('CloseSSLConf','"+siteName+"')\" style='margin-left:10px'>"+lan.site.ssl_close+"</button>");
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	});
}

//更新SSL
function ChangeSaveSSL(siteName){
	var loadT = layer.msg(lan.site.ssl_apply_4,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('site?action=CreateLet','siteName='+siteName+'&updateOf=2',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//PHP版本
function PHPVersion(siteName){
	$.post('/site?action=GetSitePHPVersion','siteName='+siteName,function(version){
		if(version.status === false){
			layer.msg(version.msg,{icon:5});
			return;
		}
		$.post('/site?action=GetPHPVersion',function(rdata){
			var versionSelect = "<div class='webEdit-box'>\
									<div class='line'>\
										<span class='tname' style='width:100px'>"+lan.site.php_ver+"</span>\
										<div class='info-r'>\
											<select id='phpVersion' class='bt-input-text mr5' name='phpVersion' style='width:110px'>";
			var optionSelect = '';
			for(var i=0;i<rdata.length;i++){
				optionSelect = version.phpversion == rdata[i].version?'selected':'';
				versionSelect += "<option value='"+ rdata[i].version +"' "+ optionSelect +">"+ rdata[i].name +"</option>"
			}
			versionSelect += "</select>\
							<button class='btn btn-success btn-sm' onclick=\"SetPHPVersion('"+siteName+"')\">"+lan.site.switch+"</button>\
							</div>\
							<span id='php_w' style='color:red;margin-left: 32px;'></span>\
						</div>\
							<ul class='help-info-text c7 ptb10'>\
								<li>"+lan.site.switch_php_help1+"</li>\
								<li>"+lan.site.switch_php_help2+"</li>\
								<li>"+lan.site.switch_php_help3+"</li>\
							</ul>\
						</div>\
					</div>";
			if(version.nodejsversion){
				var nodejs_checked = '';
				if(version.nodejs != -1) nodejs_checked = 'checked';
				versionSelect += '<div class="webEdit-box padding-10">\
									<div class="linex">\
										<label style="font-weight:normal">\
											<input type="checkbox" name="status"  onclick="Nodejs(\''+siteName+'\')" style="width:15px;height:15px;" '+nodejs_checked+' />'+lan.site.enable_nodejs+'\
										</label>\
									</div>\
									<ul class="help-info-text c7 ptb10">\
									<li>'+lan.site.nodejs_help1+' '+version.nodejsversion+'；</li>\
									<li>'+lan.site.nodejs_help2+'</li>\
									<li>'+lan.site.nodejs_help3+'</li>\
								</ul>\
								</div>'
			}
			$("#webedit-con").html(versionSelect);
			//验证PHP版本
			$("select[name='phpVersion']").change(function(){
				if($(this).val() == '52'){
					var msgerr = 'PHP5.2在您的站点有漏洞时有跨站风险，请尽量使用PHP5.3以上版本!';
					$('#php_w').text(msgerr);
				}else{
					$('#php_w').text('');
				}
			})
		});
	});
}

//tomcat
function toTomcat(siteName){
	$.post('/site?action=GetSitePHPVersion','siteName='+siteName,function(version){
		if(version.status === false){
			layer.msg(lan.site.a_n_n,{icon:5});
			return;
		}
		$.post('/site?action=GetPHPVersion',function(rdata){
			var versionSelect ='';
			if(version.tomcatversion){
				var tomcat_checked = '';
				if(version.tomcat != -1) tomcat_checked = 'checked';
				versionSelect += '<div class="webEdit-box padding-10">\
									<div class="linex">\
										<label style="font-weight:normal">\
											<input type="checkbox" name="status"  onclick="Tomcat(\''+siteName+'\')" style="width: 15px; height: 15px; vertical-align: -2px; margin: 0px 3px 0px 0px;" '+tomcat_checked+' />'+lan.site.enable_tomcat+'\
										</label>\
									</div>\
									<ul class="help-info-text c7 ptb10">\
									<li>'+lan.site.tomcat_help1+' '+version.tomcatversion+','+lan.site.tomcat_help2+'</li>\
									<li>'+lan.site.tomcat_help3+'</li>\
									<li>'+lan.site.tomcat_help4+'</li>\
									<li>'+lan.site.tomcat_help5+'</li>\
								</ul>\
								</div>'
			}else{
				layer.msg(lan.site.tomcat_err_msg,{icon:2});
				versionSelect = '<font>'+lan.site.tomcat_err_msg1+'</font>'
			}
			
			$("#webedit-con").html(versionSelect);
		});
	});
}
//设置Tomcat
function Tomcat(siteName){
	var data = 'siteName='+siteName;
	var loadT = layer.msg(lan.public.config,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=SetTomcat',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}


//设置PHP版本
function SetPHPVersion(siteName){
	var data = 'version='+$("#phpVersion").val()+'&siteName='+siteName;
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=SetPHPVersion',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//配置文件
function ConfigFile(webSite){
	$.post('/files?action=GetFileBody','path=/www/server/panel/vhost/'+getCookie('serverType')+'/'+webSite+'.conf',function(rdata){
		var mBody = "<div class='webEdit-box padding-10'>\
		<textarea style='height: 320px; width: 445px; margin-left: 20px;line-height:18px' id='configBody'>"+rdata.data+"</textarea>\
			<div class='info-r'>\
				<button id='SaveConfigFileBtn' class='btn btn-success btn-sm' style='margin-top:15px;'>"+lan.public.save+"</button>\
				<ul class='help-info-text c7 ptb10'>\
					<li>"+lan.site.web_config_help+"</li>\
				</ul>\
			</div>\
		</div>";
		$("#webedit-con").html(mBody);
		var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
			extraKeys: {"Ctrl-Space": "autocomplete"},
			lineNumbers: true,
			matchBrackets:true,
		});
		$(".CodeMirror-scroll").css({"height":"300px","margin":0,"padding":0});
		$("#SaveConfigFileBtn").click(function(){
			$("#configBody").empty();
			$("#configBody").text(editor.getValue());
			SaveConfigFile(webSite,rdata.encoding);
		})
	});
}

//保存配置文件
function SaveConfigFile(webSite,encoding){
	var data = 'encoding='+encoding+'&data='+encodeURIComponent($("#configBody").val())+'&path=/www/server/panel/vhost/'+getCookie('serverType')+'/'+webSite+'.conf';
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/files?action=SaveFileBody',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	});
}

//伪静态
function Rewrite(siteName){
	$.post("/site?action=GetRewriteList&siteName="+siteName,function(rdata){
		var filename = '/www/server/panel/vhost/rewrite/'+siteName+'.conf';
		if(getCookie('serverType') == 'apache')	filename = rdata.sitePath+'/.htaccess';
		$.post('/files?action=GetFileBody','path='+filename,function(fileBody){
			var rList = ''; 
			for(var i=0;i<rdata.rewrite.length;i++){
				rList += "<option value='"+rdata.rewrite[i]+"'>"+rdata.rewrite[i]+"</option>";
			}
			var webBakHtml = "<div class='bt-form'>\
						<div class='line'>\
						<select id='myRewrite' class='bt-input-text mr20' name='rewrite' style='width:30%;'>"+rList+"</select>\
						<span>"+lan.site.rule_cov_tool+"：<a href='https://www.bt.cn/Tools' target='_blank' style='color:#20a53a'>"+lan.site.a_c_n+"</a>\</span></div><div class='line'>\
						<textarea class='bt-input-text' style='height: 260px; width: 480px; line-height:18px;margin-top:10px;padding:5px;' id='rewriteBody'>"+fileBody.data+"</textarea></div>\
						<button id='SetRewriteBtn' class='btn btn-success btn-sm'>"+lan.public.save+"</button>\
						<button id='SetRewriteBtnTel' class='btn btn-success btn-sm'>"+lan.site.save_as_template+"</button>\
						<ul class='help-info-text c7 ptb15'>\
							<li>"+lan.site.url_rw_help_1+"</li>\
							<li>"+lan.site.url_rw_help_2+"</li>\
						</ul>\
						</div>";
			$("#webedit-con").html(webBakHtml);
			
			var editor = CodeMirror.fromTextArea(document.getElementById("rewriteBody"), {
	            extraKeys: {"Ctrl-Space": "autocomplete"},
				lineNumbers: true,
				matchBrackets:true,
			});
			
			$(".CodeMirror-scroll").css({"height":"300px","margin":0,"padding":0});
			$("#SetRewriteBtn").click(function(){
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				SetRewrite(filename);
			});
			$("#SetRewriteBtnTel").click(function(){
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				SetRewriteTel();
			});
			
			$("#myRewrite").change(function(){
				var rewriteName = $(this).val();
				if(rewriteName == lan.site.rewritename){
					rpath = '/www/server/panel/vhost/rewrite/'+siteName+'.conf';
					if(getCookie('serverType') == 'apache')	filename = rdata.sitePath+'/.htaccess';
				}else{
					rpath = '/www/server/panel/rewrite/' + getCookie('serverType')+'/' + rewriteName + '.conf';
				}
				
				$.post('/files?action=GetFileBody','path='+rpath,function(fileBody){
					 $("#rewriteBody").val(fileBody.data);
					 editor.setValue(fileBody.data);
				});
			});
		});
	});
}


//设置伪静态
function SetRewrite(filename){
	var data = 'data='+encodeURIComponent($("#rewriteBody").val())+'&path='+filename+'&encoding=utf-8';
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/files?action=SaveFileBody',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	});
}
var aindex = null;
//保存为模板
function SetRewriteTel(act){
	if(act != undefined){
		name = $("#rewriteName").val();
		if(name == ''){
			layer.msg(lan.site.template_empty,{icon:5});
			return;
		}
		var data = 'data='+encodeURIComponent($("#rewriteBody").val())+'&name='+name;
		var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=SetRewriteTel',data,function(rdata){
			layer.close(loadT);
			layer.close(aindex);
			
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
		});
		return;
	}
	
	aindex = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '320px', //宽高
		title: lan.site.save_rewrite_temp,
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
						<input type="text" class="bt-input-text" name="rewriteName" id="rewriteName" value="" placeholder="'+lan.site.template_name+'" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm">'+lan.public.cancel+'</button>\
					<button type="button" id="rewriteNameBtn" class="btn btn-success btn-sm" onclick="SetRewriteTel(1)">'+lan.public.ok+'</button>\
					</div>\
				</div>'
	});
	$(".btn-danger").click(function(){
		layer.close(aindex);
	});
	$("#rewriteName").focus().keyup(function(e){
		if(e.keyCode == 13) $("#rewriteNameBtn").click();
	});
}
//修改默认页
function SiteDefaultPage(){
	stype = getCookie('serverType');
	layer.open({
		type: 1,
		area: '460px',
		title: lan.site.change_defalut_page,
		closeBtn: 2,
		shift: 0,
		content: '<div class="changeDefault pd20">\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(1)">'+lan.site.default_doc+'</button>\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(2)">'+lan.site.err_404+'</button>\
							<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault('+(stype=='nginx'?3:4)+')">'+(stype=='nginx'?'Nginx':'Apache')+lan.site.empty_page+'</button>\
						<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(5)">'+lan.site.default_page_stop+'</button>\
				</div>'
	});
}
function changeDefault(type){
	var vhref='';
	switch(type){
		case 1:
			vhref = '/www/server/panel/data/defaultDoc.html';
			break;
		case 2:
			vhref = '/www/server/panel/data/404.html';
			break;
		case 3:
			vhref = '/www/server/nginx/html/index.html';
			break;
		case 4:
			vhref = '/www/server/apache/htdocs/index.html';
			break;
		case 5:
			vhref = '/www/server/stop/index.html';
			break;
	}
	OnlineEditFile(0,vhref);
}
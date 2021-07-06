var num = 0
//查看任务日志
function GetLogs(id){
	layer.msg(lan.public.the_get,{icon:16,time:0,shade: [0.3, '#000']});
	var data='&id='+id
	$.post('/crontab?action=GetLogs',data,function(rdata){
		layer.closeAll();
		if(!rdata.status) {
			layer.msg(rdata.msg,{icon:2});
			return;
		};
		layer.open({
			type:1,
			title:lan.crontab.task_log_title,
			area: ['700px','490px'], 
			shadeClose:false,
			closeBtn:2,
			content:'<div class="setchmod bt-form  pb70">'
					+'<pre class="crontab-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0px;font-family: \"微软雅黑\""></pre>'
					+'<div class="bt-form-submit-btn" style="margin-top: 0px;">'
					+'<button type="button" class="btn btn-danger btn-sm btn-title" style="margin-right:15px;" onclick="CloseLogs('+id+')">'+lan.public.empty+'</button>'
					+'<button type="button" class="btn btn-success btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>'
					+'</div>'
					+'</div>',
			success:function(){
				var log_body = rdata.msg == '' ? '当前日志为空':rdata.msg;
				$(".setchmod pre").text(log_body);
			}
		});
		setTimeout(function(){
			$("#crontab-log").text(rdata.msg);
			var div = document.getElementsByClassName('crontab-log')[0]
			div.scrollTop  = div.scrollHeight;
		},200)
	});
}

function getCronData(){
	var laid=layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/crontab?action=GetCrontab',"",function(rdata){
		layer.close(laid);
		var cbody="";
		if(rdata == []){
			layer.close(laid);
			cbody="<tr><td colspan='6'>"+lan.crontab.task_empty+"</td></tr>"
		}
		else{
			$.post('/crontab?action=GetDataList',{type:'sites'},function(res){
				layer.close(laid);
                for (var i = 0; i < rdata.length; i++){                  
					var s_status = '<span class="btOpen" onclick="set_task_status('+rdata[i].id+',0)" style="color:rgb(92, 184, 92);cursor:pointer" title="停用该计划任务">正常<span  class="glyphicon glyphicon-play"></span></span> ';
					var optName = '';
					if(rdata[i].status!=1) s_status = '<span onclick="set_task_status('+rdata[i].id+',1)"  class="btClose" style="color:red;cursor:pointer" title="启用该计划任务">停用<span style="color:rgb(255, 0, 0);" class="glyphicon glyphicon-pause"></span></span> ';
					
					for(var j = 0; j < res.orderOpt.length;j++){
						if(rdata[i].backupTo == res.orderOpt[j].value){
							optName = res.orderOpt[j].name;
						}else if(rdata[i].backupTo == ''){
							optName = ''
						}
					}
					
					if(rdata[i].backupTo == 'localhost'){
						optName = '本地磁盘';
					}
					
					var arrs = ['site','database','path'];
                    if ($.inArray(rdata[i].sType, arrs) == -1) optName = "--";
					cbody += "<tr>\
						<td><input type='checkbox' onclick='checkSelect();' title='"+rdata[i].name+"' name='id' value='"+rdata[i].id+"'></td>\
						<td>"+rdata[i].name+"</td>\
						<td>"+s_status+"</td>\
						<td>"+rdata[i].type+"</td>\
						<td>"+rdata[i].cycle+"</td>\
						<td>"+(rdata[i].save?rdata[i].save+'份':'-')+"</td>\
						<td>"+optName+"</td>\
						<td>"+rdata[i].addtime+"</td>\
						<td>\
							<a href=\"javascript:StartTask("+rdata[i].id+");\" class='btlink'>"+lan.public.exec+"</a> | \
							<a href=\"javascript:edit_task_info('"+rdata[i].id +"');\" class='btlink'>"+lan.files.file_menu_edit+"</a> | \
							<a href=\"javascript:GetLogs("+rdata[i].id+");\" class='btlink'>"+lan.public.log+"</a> | \
							<a href=\"javascript:planDel("+rdata[i].id+" ,'"+rdata[i].name.replace('\\','\\\\').replace("'","\\'").replace('"','')+"');\" class='btlink'>"+lan.public.del+"</a>\
						</td>\
					</tr>"
				}
				$('#cronbody').html(cbody);
			});
		}
	});
}
// 编辑计划任务
function edit_task_info(id){
	// var obj = {};
	layer.msg(lan.public.the_get,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/crontab?action=get_crond_find',{id:id},function(rdata){
		layer.closeAll();
		var sTypeName = '',sTypeDom = '',cycleName = '',cycleDom = '',weekName = '',weekDom = '',sNameName ='',sNameDom = '',backupsName = '',backupsDom ='';
		obj = {
			sBody: {
				messageChannelBtnText: '',
				channelInitVal: '',
				messageChannelDom: ''
			},
			from:{
				id:rdata.id,
				name: rdata.name,
				type: rdata.type,
				where1: rdata.where1,
				hour: rdata.where_hour,
				minute: rdata.where_minute,
				week: rdata.where1,
				sType: rdata.sType,
                sBody: rdata.sBody == 'undefined' ? '' : rdata.sBody,
				sName: rdata.sName,
				backupTo: rdata.backupTo,
				save: rdata.save,
				urladdress: rdata.urladdress,
				save_local: rdata.save_local,
				notice: rdata.notice,
				notice_channel: rdata.notice_channel
			},
			sTypeArray:[['toShell','Shell脚本'],['site','备份网站'],['database','备份数据库'],['logs','日志切割'],['path','备份目录'],['rememory','释放内存'],['toUrl','访问URL'],['webshell','木马查杀']],
			cycleArray:[['day','每天'],['day-n','N天'],['hour','每小时'],['hour-n','N小时'],['minute-n','N分钟'],['week','每星期'],['month','每月']],
			weekArray:[[1,'周一'],[2,'周二'],[3,'周三'],[4,'周四'],[5,'周五'],[6,'周六'],[0,'周日']],
			sNameArray:[],
			backupsArray:[],
			create:function(callback){
				for(var i = 0; i <obj['sTypeArray'].length; i++){
					if(obj.from['sType'] == obj['sTypeArray'][i][0])  sTypeName  = obj['sTypeArray'][i][1];
					sTypeDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['sTypeArray'][i][0] +'">'+ obj['sTypeArray'][i][1] +'</a></li>';
				}
				for(var i = 0; i <obj['cycleArray'].length; i++){
					if(obj.from['type'] == obj['cycleArray'][i][0])  cycleName  = obj['cycleArray'][i][1];
					cycleDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['cycleArray'][i][0] +'">'+ obj['cycleArray'][i][1] +'</a></li>';
				}
				for(var i = 0; i <obj['weekArray'].length; i++){
					if(obj.from['week'] == obj['weekArray'][i][0])  weekName  = obj['weekArray'][i][1];
					weekDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['weekArray'][i][0] +'">'+ obj['weekArray'][i][1] +'</a></li>';
				}
				if(obj.from.notice_channel == 'dingding') {
				    obj.sBody.title = '钉钉'
				}else if(obj.from.notice_channel == 'mail') {
				    obj.sBody.title = '邮箱'
				}else if(obj.from.notice_channel == 'dingding,mail') {
				    obj.sBody.title = '全部通道'
				} else {
				    obj.sBody.title = '无'
				}
				setTimeout(function() {
					callback();
				},200)
			}
		};
		obj.create(function(){
			layer.open({
				type:1,
				title:'编辑计划任务-['+rdata.name+']',
				area: '850px', 
				skin:'layer-create-content',
				shadeClose:false,
				closeBtn:2,
				content:'<div class="setting-con ptb20">\
								<div class="clearfix plan ptb10">\
									<span class="typename c4 pull-left f14 text-right mr20">任务类型</span>\
									<div class="dropdown stype_list pull-left mr20">\
										<button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto" disabled="disabled">\
											<b val="'+ obj.from.sType +'">'+ sTypeName +'</b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="sType">'+ sTypeDom +'</ul>\
									</div>\
								</div>\
								<div class="clearfix plan ptb10">\
									<span class="typename c4 pull-left f14 text-right mr20">任务名称</span>\
									<div class="planname pull-left"><input type="text" name="name" class="bt-input-text sName_create" value="'+ obj.from.name +'"></div>\
								</div>\
								<div class="clearfix plan ptb10">\
									<span class="typename c4 pull-left f14 text-right mr20">执行周期</span>\
									<div class="dropdown  pull-left mr20">\
										<button class="btn btn-default dropdown-toggle cycle_btn" type="button" data-toggle="dropdown" style="width:94px">\
											<b val="'+ obj.from.type +'">'+ cycleName +'</b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="cycle">'+ cycleDom +'</ul>\
									</div>\
									<div class="pull-left optional_week">\
										<div class="dropdown week_btn pull-left mr20" style="display:'+ (obj.from.type == "week"  ?'block;':'none') +'">\
											<button class="btn btn-default dropdown-toggle" type="button" data-toggle="dropdown" >\
												<b val="'+ obj.from.week +'">'+ weekName +'</b> \
												<span class="caret"></span>\
											</button>\
											<ul class="dropdown-menu" role="menu" aria-labelledby="week">'+ weekDom +'</ul>\
										</div>\
										<div class="plan_hms pull-left mr20 bt-input-text where1_input" style="display:'+ (obj.from.type == "day-n" || obj.from.type == 'month' ?'block;':'none') +'"><span><input type="number" name="where1" class="where1_create" value="'+obj.from.where1 +'" maxlength="2" max="23" min="0"></span> <span class="name">日</span> </div>\
										<div class="plan_hms pull-left mr20 bt-input-text hour_input" style="display:'+ (obj.from.type == "day" || obj.from.type == 'day-n' || obj.from.type == 'hour-n' || obj.from.type == 'week' || obj.from.type == 'month'?'block;':'none') +'"><span><input type="number" name="hour" class="hour_create" value="'+ ( obj.from.type == 'hour-n' ? obj.from.where1 : obj.from.hour ) +'" maxlength="2" max="23" min="0"></span> <span class="name">时</span> </div>\
										<div class="plan_hms pull-left mr20 bt-input-text minute_input"><span><input type="number" name="minute" class="minute_create" value="'+ (obj.from.type == 'minute-n' ? obj.from.where1 : obj.from.minute)+'" maxlength="2" max="59" min="0"></span> <span class="name">分</span> </div>\
									</div>\
								</div>\
								<div class="clearfix plan ptb10 site_list">\
									<span class="typename controls c4 pull-left f14 text-right mr20">'+ sTypeName  +'</span>\
									<div style="line-height:34px"><div class="dropdown pull-left mr20 sName_btn" style="display:'+ (obj.from.sType != "path"?'block;':'none') +'">\
										<button class="btn btn-default dropdown-toggle" type="button"  data-toggle="dropdown" style="width:auto" disabled="disabled">\
											<b id="sNameEdit1" val="'+ obj.from.sName +'"></b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="sNameEdit1">'+ sNameDom +'</ul>\
									</div>\
									<div style="line-height:34px">\
    									<div class="pull-left" style="margin-right:20px;display:'+ (obj.from.sType == "path"?'block;':'none') +'"><input type="text" name="name" class="bt-input-text sName_create" value="'+ obj.from.sName +'" disabled="disabled"></div>\
    								</div>\
									<div class="textname pull-left mr20" style="display:'+ (obj.from.sType == "logs"?'none':'block') +';">备份到</div>\
										<div class="dropdown  pull-left mr20" style="display:'+ (obj.from.sType == "logs"?'none':'block') +';">\
											<button class="btn btn-default dropdown-toggle backup_btn"  type="button"  data-toggle="dropdown" style="width:auto;">\
												<b val="'+ obj.from.backupTo +'">'+ backupsName +'</b>\
												<span class="caret"></span>\
											</button>\
											<ul class="dropdown-menu" role="menu" aria-labelledby="backupTo">'+ backupsDom +'</ul>\
										</div>\
										<div class="textname pull-left mr20">保留最新</div>\
										<div class="plan_hms pull-left mr20 bt-input-text">\
											<span><input type="number" name="save" class="save_create" value="'+ obj.from.save +'" maxlength="4" max="100" min="1"></span><span class="name">份</span>\
										</div>\
									</div>\
								</div>\
								<div class="clearfix plan ptb10 site_list">\
									<span class="typename controls c4 pull-left f14 text-right mr20" style="display:'+ (obj.from.sType == "logs"?'none':'block') +';">备份提醒</span>\
									<div style="line-height:34px" ><div class="dropdown pull-left mr20 sName_btn" id="modNotice" style="display:'+ (obj.from.sType == "logs"?'none':'block') +';">\
										<button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:180px;">\
											<b val="'+obj.from.notice+'">'+ (obj.from.notice == 1 ? '任务执行失败接收通知' : '不接收任何消息通知') +'</b> <span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
											<li><a role="menuitem" tabindex="-1" href="javascript:;" value="0">不接收任何消息通知</a></li>\
											<li><a role="menuitem" tabindex="-1" href="javascript:;" value="1">任务执行失败接收通知</a></li>\
										</ul>\
									</div>\
									<div class="pull-left mr20"  style="display:'+ (obj.from.notice == 1 && obj.from.sType != 'logs' ?'block':'none') +';" >消息通道</div>\
										<div class="dropdown  pull-left mr20"  style="display:'+ (obj.from.notice == 1 ?'block':'none') +';" id="messageChannel">\
											<button class="btn btn-default dropdown-toggle"  type="button"  data-toggle="dropdown" style="width:auto;" id="modNotice_channel">\
												<b val="'+ obj.from.notice_channel +'" id="modNotice_channelValue">'+ obj.sBody.title +'</b> <span class="caret"></span>\
											</button>\
											<ul class="dropdown-menu" role="menu"></ul>\
										</div>\
										<div class="textname pull-left mr20" id="selmodnoticeBox" onclick="modSelSave_local()" style="display:'+ (obj.from.backupTo == 'localhost' ? 'none' : 'block') +';">\
											<span style="display:'+ (obj.from.sType == "logs"?'none':'block') +';"><input type="checkbox" value="'+obj.from.save_local+'" '+ (obj.from.save_local == 1 ? 'checked': '') +' style="margin-left: 20px;margin-right: 10px;" id="modSave_local">同时保留本地备份（和云存储保留份数一致）</span>\
										</div>\
									</div>\
								</div>\
								<div class="clearfix plan ptb10"  style="display:'+ ((obj.from.sType == "toShell" || obj.from.sType == 'site' || obj.from.sType == 'path')?'block;':'none') +'">\
									<span class="typename controls c4 pull-left f14 text-right mr20">'+ (obj.from.sType == "toShell" ?'脚本内容':'排除规则')+'</span>\
									<div style="line-height:22px"><textarea style="line-height:22px" class="txtsjs bt-input-text sBody_create" name="sBody">'+ obj.from.sBody +'</textarea></div>\
								</div>\
								<div class="clearfix plan ptb10" style="display:'+ (obj.from.sType == "rememory"?'block;':'none') +'">\
									<span class="typename controls c4 pull-left f14 text-right mr20">提示</span>\
									<div style="line-height:34px">释放PHP、MYSQL、PURE-FTPD、APACHE、NGINX的内存占用,建议在每天半夜执行!</div>\
								</div>\
								<div class="clearfix plan ptb10" style="display:'+ (obj.from.sType == "toUrl"?'block;':'none') +'">\
									<span class="typename controls c4 pull-left f14 text-right mr20">URL地址</span>\
									<div style="line-height:34px"><input type="text" style="width:400px; height:34px" class="bt-input-text url_create" name="urladdress"  placeholder="URL地址" value="'+ obj.from.urladdress +'"></div>\
								</div>\
								<div class="clearfix plan ptb10" style="display:'+ (obj.from.sType == "webshell"?'block;':'none') +'">\
									<span class="typename controls c4 pull-left f14 text-right mr20">查杀站点</span>\
									<div class="dropdown pull-left mr20 sName_btn">\
										<button class="btn btn-default dropdown-toggle" type="button"  data-toggle="dropdown" style="width:auto" disabled="disabled">\
											<b id="sNameEdit2" val="'+ obj.from.sName +'"></b>\
											<span class="caret"></span>\
										</button>\
										<ul class="dropdown-menu" role="menu" aria-labelledby="sNameEdit2">'+ sNameDom +'</ul>\
									</div>\
									<p class="clearfix plan">\
										<div class="textname pull-left mr20" style="margin-left: 63px; font-size: 14px;">消息通道</div>\
										<div class="dropdown planBackupTo pull-left mr20 edit_message_start" style="line-height: 34px;"></div>\
									</p>\
								</div>\
								<div class="clearfix plan ptb10">\
									<div class="bt-submit plan-submits " style="margin-left: 141px;">保存编辑</div>\
								</div>\
							</div>',
        success:function(){
          if(obj.from.sType == 'site' || obj.from.sType == 'database' || obj.from.sType == 'path' || obj.from.sType == 'logs' || obj.from.sType == 'webshell'){
            $.post('/crontab?action=GetDataList',{type:obj.from.sType  == 'database'?'databases':'sites'},function(rdata){
              obj.sNameArray = rdata.data;
              obj.sNameArray.unshift({name:'ALL',ps:'所有'});
              obj.backupsArray = rdata.orderOpt;
              obj.backupsArray.unshift({name:'服务器磁盘',value:'localhost'});
              for(var i = 0; i <obj['sNameArray'].length; i++){
                if(obj.from['sName'] == obj['sNameArray'][i]['name'])  sNameName  = obj['sNameArray'][i]['ps'];
                sNameDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['sNameArray'][i]['name'] +'">'+ obj['sNameArray'][i]['ps'] +'</a></li>';
              }
              for(var i = 0; i <obj['backupsArray'].length; i++){
                if(obj.from['backupTo'] == obj['backupsArray'][i]['value'])  backupsName  = obj['backupsArray'][i]['name'];
                backupsDom += '<li><a role="menuitem"  href="javascript:;" value="'+ obj['backupsArray'][i]['value'] +'">'+ obj['backupsArray'][i]['name'] +'</a></li>';
              }
              console.log(sNameName)
              $('#sNameEdit1,#sNameEdit2').html(sNameName)
              $('.backup_btn b').html(backupsName)
              $('.backup_btn+.dropdown-menu').html(backupsDom)
              if(obj.from.sType == 'webshell'){
                edit_message_channel(obj.from.urladdress)
              }
            });
          }
          if(obj.from.sType == 'site' || obj.from.sType == 'database' || obj.from.sType == 'path') {
            $.post('/config?action=get_settings',{type: 'sites'},function(rdata){
              var messageChannelDom = ''
              if(rdata.user_mail.user_name && rdata.dingding.dingding) {
                messageChannelDom = '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding,mail">全部通道</a></li><li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding">钉钉</a></li><li><a role="menuitem" tabindex="-1" href="javascript:;" value="mail">邮箱</a></li>'
              } else if(!rdata.user_mail.user_name && !rdata.dingding.dingding){
                messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="">无</a></li>'
              } else if(rdata.dingding.dingding) {
                messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding">钉钉</a></li>'
              } else if(rdata.user_mail.user_name) {
                messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="mail">邮箱</a></li>'
              }
              $('#messageChannel .dropdown-menu').html(messageChannelDom)
              
            })
            $('#messageChannel .dropdown-menu').on('click','li',function(){
              $('#modNotice_channelValue').attr('val',$(this).find('a').attr('value'))
              $('#modNotice_channelValue').html($(this).find('a').text())
            })
          }
        }
			});
			getselectnoticename();
			setTimeout(function(){
				if(obj.from.sType == 'toShell'){
					$('.site_list').hide();
				}else if(obj.from.sType == 'rememory'){
					$('.site_list').hide();
				}else if( obj.from.sType == 'toUrl'){
					$('.site_list').hide();
				}else if( obj.from.sType == 'webshell'){
					$('.site_list').hide();
				}else{
					$('.site_list').show();
				}

				$('.sName_create').blur(function () {
					obj.from.name = $(this).val();
				});
				$('.where1_create').blur(function () {
					obj.from.where1 = $(this).val();
				});
	
				$('.hour_create').blur(function () {
					obj.from.hour = $(this).val();
				});
	
				$('.minute_create').blur(function () {
					obj.from.minute = $(this).val();
				});
	
				$('.save_create').blur(function () {
					obj.from.save = $(this).val();
				});
	
				$('.sBody_create').blur(function () {
					obj.from.sBody = $(this).val();
				});
				$('.url_create').blur(function () {
					obj.from.urladdress = $(this).val();
				});
				$('.layer-create-content [aria-labelledby="cycle"] a').unbind().click(function () {
					$('.cycle_btn').find('b').attr('val',$(this).attr('value')).html($(this).html());
					var type = $(this).attr('value');
					switch(type){
						case 'day':
							$('.week_btn').hide();
							$('.where1_input').hide();
							$('.hour_input').show().find('input').val('1');
							$('.minute_input').show().find('input').val('30');
							obj.from.week = '';
							obj.from.type = '';
							obj.from.hour = 1;
							obj.from.minute = 30;
						break;
						case 'day-n':
							$('.week_btn').hide();
							$('.where1_input').show().find('input').val('1');
							$('.hour_input').show().find('input').val('1');
							$('.minute_input').show().find('input').val('30');
							obj.from.week = '';
							obj.from.where1 = 1;
							obj.from.hour = 1;
							obj.from.minute = 30;
						break;
						case 'hour':
							$('.week_btn').hide();
							$('.where1_input').hide();
							$('.hour_input').hide();
							$('.minute_input').show().find('input').val('30');
							obj.from.week = '';
							obj.from.where1 = '';
							obj.from.hour = '';
							obj.from.minute = 30;
						break;
						case 'hour-n':
							$('.week_btn').hide();
							$('.where1_input').hide();
							$('.hour_input').show().find('input').val('1');
							$('.minute_input').show().find('input').val('30');
							obj.from.week = '';
							obj.from.where1 = '';
							obj.from.hour = 1;
							obj.from.minute = 30;
						break;
						case 'minute-n':
							$('.week_btn').hide();
							$('.where1_input').hide();
							$('.hour_input').hide();
							$('.minute_input').show();
							obj.from.week = '';
							obj.from.where1 = '';
							obj.from.hour = '';
							obj.from.minute = 30;
						break;
						case 'week':
							$('.week_btn').show();
							$('.where1_input').hide();
							$('.hour_input').show();
							$('.minute_input').show();
							obj.from.week = 1;
							obj.from.where1 = '';
							obj.from.hour = 1;
							obj.from.minute = 30;
						break;
						case 'month':
							$('.week_btn').hide();
							$('.where1_input').show();
							$('.hour_input').show();
							$('.minute_input').show();
							obj.from.week = '';
							obj.from.where1 = 1;
							obj.from.hour = 1;
							obj.from.minute = 30;
						break;
					}
					obj.from.type = $(this).attr('value');
				});
	
				$('.layer-create-content [aria-labelledby="week"] a').unbind().click(function () {
					$('.week_btn').find('b').attr('val',$(this).attr('value')).html($(this).html());
					obj.from.week = $(this).attr('value');
				});
	
				$('.layer-create-content [aria-labelledby="backupTo"] a').unbind().click(function () {
					$('.backup_btn').find('b').attr('val', $(this).attr('value')).html($(this).html());
					obj.from.backupTo = $(this).attr('value');
					if(obj.from.backupTo == 'localhost') {
						$('#selmodnoticeBox').hide()
					} else {
						$('#selmodnoticeBox').show()
					}
				});
				$('.plan-submits').unbind().click(function(){
					if(obj.from.type == 'hour-n'){
						obj.from.where1 = obj.from.hour;
						obj.from.hour = '';
					}else if(obj.from.type == 'minute-n'){
						obj.from.where1 = obj.from.minute;
						obj.from.minute = '';
					}else if(obj.from.sType == 'webshell'){
						obj.from.urladdress = $(".edit_message_start input:checked").val()
					}
					obj.from.save_local = $('#modSave_local').val()
					obj.from.notice = $("#modNotice").find("button b").attr("val")
					obj.from.notice_channel = $("#modNotice_channelValue").attr("val")
					layer.msg('正在保存编辑内容，请稍后...',{icon:16,time:0,shade: [0.3, '#000']});
					$.post('/crontab?action=modify_crond',obj.from,function(rdata){
						layer.closeAll();
						getCronData();
						layer.msg(rdata.msg,{icon:rdata.status?1:2});
					});
				});
			},100);
		});
	});

}
// 修改木马查杀  消息通道
function edit_message_channel(type){
	$.post('/config?action=get_settings',function(res){
		var tMess = "";
		if(res.user_mail.user_name){
		    tMess = '<div class="check_alert" style="margin-right:20px;display: inline-block;">\
				<input id="mail_edit" type="radio" name="alert_edit" title="邮箱" value="mail" '+ (type == 'mail'? 'checked' : '') +'>\
				<label for="mail_edit" style="font-weight: normal;font-size: 14px;margin-left: 6px;display: inline;">邮箱</label>\
			</div>'
		}
		if(res.dingding.dingding){
		    tMess += '<div class="check_alert" style="display: inline-block;">\
				<input id="dingding_edit" type="radio" name="alert_edit" title="钉钉" value="dingding" '+ (type == 'dingding'? 'checked' : '') +'>\
				<label for="dingding_edit" style="font-weight: normal;font-size: 14px;margin-left: 6px;display: inline;">钉钉</label>\
			</div>'
		}
		$(".edit_message_start").html(tMess);
	})
	
}

// 设置计划任务状态
function set_task_status(id,status){
	var confirm = layer.confirm(status == '0'?'计划任务暂停后将无法继续运行，您真的要停用这个计划任务吗？':'该计划任务已停用，是否要启用这个计划任务', {title:'提示',icon:3,closeBtn:2},function(index) {
		if (index > 0) {
			var loadT = layer.msg('正在设置状态，请稍后...',{icon:16,time:0,shade: [0.3, '#000']});
			$.post('/crontab?action=set_cron_status',{id:id},function(rdata){
				layer.closeAll();
				layer.close(confirm);
				layer.msg(rdata.data,{icon:rdata.status?1:2});
				if(rdata.status) getCronData();
			});
		}
	});
}

//执行任务脚本
function StartTask(id){
	layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab?action=StartTask',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}


//清空日志
function CloseLogs(id){
	layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	var data='id='+id;
	$.post('/crontab?action=DelLogs',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}


//删除
function planDel(id,name){
	SafeMessage(lan.get('del',[name]),lan.crontab.del_task,function(){
			layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
			var data='id='+id;
			$.post('/crontab?action=DelCrontab',data,function(rdata){
				layer.closeAll();
                getCronData();
                setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });},1000)
			});
	});
}


//批量删除
function allDeleteCron(){
	var checkList = $("input[name=id]");
	var dataList = new Array();
	for(var i=0;i<checkList.length;i++){
		if(!checkList[i].checked) continue;
		var tmp = new Object();
		tmp.name = checkList[i].title;
		tmp.id = checkList[i].value;
		dataList.push(tmp);
	}
	SafeMessage(lan.crontab.del_task_all_title,"<a style='color:red;'>"+lan.get('del_all_task',[dataList.length])+"</a>",function(){
		layer.closeAll();
		syncDeleteCron(dataList,0,'');
	});
}

//模拟同步开始批量删除数据库
function syncDeleteCron(dataList,successCount,errorMsg){
	if(dataList.length < 1) {
		layer.msg(lan.get('del_all_task_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('del_all_task_the',[dataList[0].name]),{icon:16,time:0,shade: [0.3, '#000']});
	$.ajax({
			type:'POST',
			url:'/crontab?action=DelCrontab',
			data:'id='+dataList[0].id+'&name='+dataList[0].name,
			async: true,
			success:function(frdata){
				layer.close(loadT);
				if(frdata.status){
					successCount++;
					$("input[title='"+dataList[0].name+"']").parents("tr").remove();
				}else{
					if(!errorMsg){
						errorMsg = '<br><p>'+lan.crontab.del_task_err+'</p>';
					}
					errorMsg += '<li>'+dataList[0].name+' -> '+frdata.msg+'</li>'
				}
				
				dataList.splice(0,1);
				syncDeleteCron(dataList,successCount,errorMsg);
			}
	});
}

	
function IsURL(str_url){
	var strRegex = '^(https|http|ftp|rtsp|mms)?://.+';
	var re=new RegExp(strRegex);
	if (re.test(str_url)){
		return (true);
	}else{
		return (false);
	}
}


//提交
function planAdd(){
	var name = $(".planname input[name='name']").val();
	if(name == ''){
		$(".planname input[name='name']").focus();
		layer.msg(lan.crontab.add_task_empty,{icon:2});
		return;
	}
	$("#set-Config input[name='name']").val(name);
	
	var type = $(".plancycle").find("b").attr("val");
	$("#set-Config input[name='type']").val(type);
	
	var where1 = $("#ptime input[name='where1']").val();
	var is1;
	var is2 = 1;
	switch(type){
		case 'day-n':
			is1=31;
			break;
		case 'hour-n':
			is1=23;
			break;
		case 'minute-n':
			is1=59;
			break;
		case 'month':
			is1=31;
			break;
		
	}
	
	if(where1 > is1 || where1 < is2){
		$("#ptime input[name='where1']").focus();
		layer.msg(lan.public.input_err,{icon:2});
		return;
	}
	
	$("#set-Config input[name='where1']").val(where1);
	
	var hour = $("#ptime input[name='hour']").val();
	if(hour > 23 || hour < 0){
		$("#ptime input[name='hour']").focus();
		layer.msg(lan.crontab.input_hour_err,{icon:2});
		return;
	}
	$("#set-Config input[name='hour']").val(hour);
	var minute = $("#ptime input[name='minute']").val();
	if(minute > 59 || minute < 0){
		$("#ptime input[name='minute']").focus();
		layer.msg(lan.crontab.input_minute_err,{icon:2});
		return;
	}
	$("#set-Config input[name='minute']").val(minute);
	
	var save = $("#save").val();
	
	if(save < 0){
		layer.msg(lan.crontab.input_number_err,{icon:2});
		return;
	}
	
	$("#set-Config input[name='save']").val(save);
	
	
	$("#set-Config input[name='week']").val($(".planweek").find("b").attr("val"));
	var sType = $(".planjs").find("b").attr("val");
	var sBody = encodeURIComponent($("#implement textarea[name='sBody']").val());
	
	if(sType == 'toFile'){
		if($("#viewfile").val() == ''){
			layer.msg(lan.crontab.input_file_err,{icon:2});
			return;
		}
	}else{
        if (sBody == '' && sType == 'toShell'){
			$("#implement textarea[name='sBody']").focus();
			layer.msg(lan.crontab.input_script_err,{icon:2});
			return;
		}
	}
	var urladdress_1 = $("#urladdress_1").val();
	if(sType == 'toUrl'){
		if(!IsURL(urladdress_1)){
			layer.msg(lan.crontab.input_url_err,{icon:2});
			$("implement textarea[name='urladdress_1']").focus();
			return;
		}
	}
	urladdress_1 = encodeURIComponent(urladdress_1);
	$("#set-Config input[name='sType']").val(sType);
	$("#set-Config textarea[name='sBody']").val(decodeURIComponent(sBody));
	
	if(sType == 'site' || sType == 'database' || sType == 'path'){
		var backupTo = $(".planBackupTo").find("b").attr("val");
		$("#backupTo").val(backupTo);
	}

	var sName = $("#sName").attr("val");
	
	/*if(sName == 'backupAll'){
		var alist = $("ul[aria-labelledby='backdata'] li a");
		var dataList = new Array();
		for(var i=1;i<alist.length;i++){
			var tmp = alist[i].getAttribute('value');
			dataList.push(tmp);
		}
		if(dataList.length < 1){
			layer.msg(lan.crontab.input_empty_err,{icon:5});
			return;
		}
		
		allAddCrontab(dataList,0,'');
		return;
	}*/
	$("#set-Config input[name='sName']").val(sName);
	layer.msg(lan.public.the_add,{icon:16,time:0,shade: [0.3, '#000']});
	var data= $("#set-Config").serialize() + '&sBody='+sBody + '&urladdress=' + urladdress_1;
	if(data.indexOf('sType=path') > -1){
		data = data.replace('&sName=&','&sName='+ encodeURIComponent($('#inputPath').val()) +'&')
	}else if(data.indexOf('sType=webshell') > -1){
		data = $("#set-Config").serialize() + '&urladdress=' + $(".message_start input:checked").val()
		data = data.replace('&sName=&','&sName='+ encodeURIComponent($('#filePath').val()) +'&')
	}
	if(data.indexOf('&save_local=') == -1) {
		data = data + '&save_local='+ $('#save_local').val() +'&notice='+ $("#notice").find("b").attr("val") +'&notice_channel='+ $("#notice_channel").find("b").attr("val") +''
	}
	$.post('/crontab?action=AddCrontab',data,function(rdata){
		layer.closeAll();
        getCronData();
        $(".dropdown ul li:first a").click();
        setTimeout(function () {
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        }, 1000)
	});
}

//批量添加任务
function allAddCrontab(dataList,successCount,errorMsg){
	if(dataList.length < 1) {
		layer.msg(lan.get('add_all_task_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('add',[dataList[0]]),{icon:16,time:0,shade: [0.3, '#000']});
	var sType = $(".planjs").find("b").attr("val");
	var minute = parseInt($("#set-Config input[name='minute']").val());
	var hour = parseInt($("#set-Config input[name='hour']").val());
	var sTitle = (sType == 'site')?lan.crontab.backup_site:lan.crontab.backup_database;
	if(sType == 'logs') sTitle = lan.crontab.backup_log;
	minute += 5;
	if(hour !== '' && minute > 59){
		if(hour >= 23) hour = 0;
		$("#set-Config input[name='hour']").val(hour+1);
		minute = 5;
	}
	$("#set-Config input[name='minute']").val(minute);
	$("#set-Config input[name='name']").val(sTitle + '['+dataList[0]+']');
	$("#set-Config input[name='sName']").val(dataList[0]);
	var pdata = $("#set-Config").serialize() + '&sBody=&urladdress_1=';
	$.ajax({
			type:'POST',
			url:'/crontab?action=AddCrontab',
			data:pdata,
			async: true,
			success:function(frdata){
				layer.close(loadT);
				if(frdata.status){
					successCount++;
					getCronData();
				}else{
					if(!errorMsg){
						errorMsg = '<br><p>'+lan.crontab.backup_all_err+'</p>';
					}
					errorMsg += '<li>'+dataList[0]+' -> '+frdata.msg+'</li>'
				}
				
				dataList.splice(0,1);
				allAddCrontab(dataList,successCount,errorMsg);
			}
	});
}

$(".dropdown ul li a").click(function(){
	var txt = $(this).text();
	var type = $(this).attr("value");
	$(this).parents(".dropdown").find("button b").text(txt).attr("val",type);
	$('#logs_tips').remove();
	$(".plan-submit").css({"pointer-events":"auto","background-color":"#20a53a","color":"#fff"});
	switch(type){
		case 'day':
			closeOpt();
			toHour();
			toMinute();
			break;
		case 'day-n':
			closeOpt();
			toWhere1(lan.crontab.day);
			toHour();
			toMinute();
			break;
		case 'hour':
			closeOpt();
			toMinute();
			break;
		case 'hour-n':
			closeOpt();
			toWhere1(lan.crontab.hour);
			toMinute();
			break;
		case 'minute-n':
			closeOpt();
			toWhere1(lan.crontab.minute);
			break;
		case 'week':
			closeOpt();
			toWeek();
			toHour();
			toMinute();
			break;
		case 'month':
			closeOpt();
			toWhere1(lan.crontab.sun);
			toHour();
			toMinute();
			break;
		case 'toFile':
			toFile();
			break;
		case 'toShell':
			toShell();
			$(".controls").html(lan.crontab.sbody);
			break;
		case 'path':
			toBackup('path');
			$(".controls").html('备份目录');
			break;
		case 'rememory':
			rememory();
			$(".controls").html(lan.public.msg);
			break;
		case 'site':
			toBackup('sites');
			$(".controls").html(lan.crontab.backup_site);
			break;
		case 'database':
			toBackup('databases');
			$(".controls").html(lan.crontab.backup_database);
			break;
		case 'logs':
			toBackup('logs');
			$(".controls").html(lan.crontab.log_site);
			break;
		case 'toUrl':
			toUrl();
			$(".controls").html(lan.crontab.url_address);
			break;
		case 'webshell':
			webShell();
			break;
	}
})


//备份
function toBackup(type){
	var sMsg = "";
	switch(type){
		case 'sites':
			sMsg = lan.crontab.backup_site;
			sType = "sites";
			break;
		case 'databases':
			sMsg = lan.crontab.backup_database;
			sType = "databases";
			break;
		case 'logs':
			sMsg = lan.crontab.backup_log;
			sType = "sites";
			break;
		case 'path':
			sMsg = '备份目录';
			sType = "sites";
			break;
	}
	var data='type='+sType
	$.post('/crontab?action=GetDataList',data,function(rdata){
		$(".planname input[name='name']").attr('readonly','true').css({"background-color":"#f6f6f6","color":"#666"});
		if(type != 'path'){
			var sOpt = "",sOptBody = '';
			if(rdata.data.length == 0){
				layer.msg(lan.public.list_empty,{icon:2})
				return
			}
			for(var i=0;i<rdata.data.length;i++){
				if(type === 'logs'){
					$(".planname input[name='name']").val(sMsg+'[ALL]');
				}else{
					if(i ==0){
						$(".planname input[name='name']").val(sMsg+'['+rdata.data[i].name+']');
					}
				}
				sOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.data[i].name+'">'+rdata.data[i].name+'['+rdata.data[i].ps+']</a></li>';			
			}	
			sOptBody ='<div class="dropdown pull-left mr20">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="backdata" data-toggle="dropdown" style="width:auto">\
						<b id="sName" val="'+ (type === 'logs'?'ALL':rdata.data[0].name) +'">'+ (type === 'logs'?'所有':(rdata.data[0].name +'['+rdata.data[0].ps+']')) +'</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="backdata">\
					 	<li><a role="menuitem" tabindex="-1" href="javascript:;" value="ALL">'+lan.public.all+'</a></li>\
					  	'+sOpt+'\
					  </ul>\
            </div>'
		}else{
			$(".planname input[name='name']").val(sMsg+'[/www/wwwroot/]');
			sOptBody = '<div class="info-r" style="display: inline-block;float: left;margin-right: 25px;"><input id="inputPath" class="bt-input-text mr5" type="text" name="path" value="/www/wwwroot/" placeholder="备份目录" style="width:208px;height:33px;"><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(&quot;inputPath&quot;)"></span></div>'
			setCookie('default_dir_path','/www/wwwroot/');
			setCookie('path_dir_change','/www/wwwroot/');
			setInterval(function(){
				if(getCookie('path_dir_change') != getCookie('default_dir_path')){
					var  path_dir_change = getCookie('path_dir_change')
					$(".planname input").val('备份目录['+getCookie('path_dir_change')+']');
					setCookie('default_dir_path',path_dir_change);
				}
			},500);
		}		
		var orderOpt = ''
		for (var i=0;i<rdata.orderOpt.length;i++){
			orderOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.orderOpt[i].value+'">'+rdata.orderOpt[i].name+'</a></li>'
		}
		var save_num = 3;
		if(type === 'logs'){
			$('#cycle b').attr('val','day').text('每天');
			$('.planweek').hide();
			$('[name="hour"]').val(0);
			$('[name="minute"]').val(1);
			$('#implement').parent().after('<div class="clearfix plan" id="logs_tips"><span class="typename controls c4 pull-left f14 text-right mr20">提示</span><div style="line-height:34px">根据网络安全法第二十一条规定，网络日志应留存不少于六个月。</div></div>')
			save_num = 180;
		}else{
			$('#logs_tips').remove();
		}
		var sBody = sOptBody + '<div class="textname pull-left mr20" style="display:'+ (type === 'logs'?'none':'inline-block') +'">'+lan.crontab.backup_to+'</div>\
					<div class="dropdown planBackupTo pull-left mr20" style="display:'+ (type === 'logs'?'none':'inline-block') +'" id="saveAddServerDiskToLocal">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto;">\
						<b val="localhost">'+lan.crontab.disk+'</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="localhost">'+lan.crontab.disk+'</a></li>\
						'+ orderOpt +'\
					  </ul>\
					</div>\
					<div class="textname pull-left mr20">'+lan.crontab.save_new+'</div><div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="save" id="save" value="'+save_num+'" maxlength="4" max="100" min="1"></span>\
					<span class="name">'+lan.crontab.save_num+'</span>\
					</div>';
        if (type == 'sites' || type == 'path' || type == 'databases') {
          $.post('/config?action=get_settings',data,function(rdata){
            var messageChannelDom = '', messageChannelBtnText = '', channelInitVal = ''
            if(rdata.user_mail.user_name && rdata.dingding.dingding) {
              messageChannelBtnText = '全部通道'
			  channelInitVal= 'user_name,dingding'
              messageChannelDom = '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding,mail">全部通道</a></li><li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding">钉钉</a></li><li><a role="menuitem" tabindex="-1" href="javascript:;" value="mail">邮箱</a></li>'
            } else if(!rdata.user_mail.user_name && !rdata.dingding.dingding){
              messageChannelBtnText = '无'
			  channelInitVal= ''
              messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="">无</a></li>'
            } else if(rdata.dingding.dingding) {
              messageChannelBtnText = '钉钉'
			  channelInitVal= 'dingding'
              messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="dingding">钉钉</a></li>'
            } else if(rdata.user_mail.user_name) {
              messageChannelBtnText = '邮箱'
			  channelInitVal= 'mail'
              messageChannelDom += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="mail">邮箱</a></li>'
            }
            sBody += '<p class="clearfix plan">\
                <div class="textname pull-left mr20" style="margin-left: 63px; font-size: 14px;">备份提醒</div>\
                  <div class="dropdown planBackupTo pull-left mr20" style="display:'+ (type === 'logs'?'none':'inline-block') +'"  id="notice">\
                    <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:180px;">\
                      <b val="0">不接收任何消息通知</b> <span class="caret"></span>\
                    </button>\
                    <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
                      <li><a role="menuitem" tabindex="-1" href="javascript:;" value="0">不接收任何消息通知</a></li>\
                      <li><a role="menuitem" tabindex="-1" href="javascript:;" value="1">任务执行失败接收通知</a></li>\
                    </ul>\
                  </div>\
                </div>\
                <div class="textname pull-left mr20" style="font-size: 14px;display:none;" id="messageChannelBox">消息通道</div>\
                  <div class="dropdown planBackupTo pull-left mr20" style="display:none;" id="notice_channel">\
                    <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown" style="width:auto;">\
                      <b val="'+channelInitVal+'">'+ messageChannelBtnText +'</b> <span class="caret"></span>\
                    </button>\
                    <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
                      '+messageChannelDom+'\
                    </ul>\
                  </div>\
                </div>\
                <a role="menuitem" tabindex="-1" href="javascript:;" onclick="open_three_channel_auth()" value="0" style="color: #20a53a;">设置消息通道</a>\
				<span  id="selnoticeBox"  onclick="selSave_local()" style="display:none;"><input type="checkbox" value="0" style="margin-left: 20px;margin-right: 10px;" id="save_local">同时保留本地备份（和云存储保留份数一致）</span>\
            </p>';
            if(type == 'sites' || type == "path") {
				sBody += '<p class="clearfix plan">\
              <div class="textname pull-left mr20" style="margin-left: 63px; font-size: 14px;">排除规则</div>\
              <div class="dropdown planBackupTo pull-left mr20">\
                  <span><textarea style=" height: 100px;width:300px;line-height:22px;" class="bt-input-text" type="text" name="sBody" id="exclude" placeholder="每行一条规则,目录不能以/结尾，示例：\ndata/config.php\nstatic/upload\n *.log\n"></textarea></span>\
              </div>\
            </p>';
			}
            $("#implement").html(sBody);
			getselectnoticename();
          })
        } else {
            $("#implement").html('<div></div>');
            sBody += '<p class="clearfix plan">\
              <div class="textname pull-left mr20" style="margin-left: 63px; font-size: 14px;">排除规则</div>\
              <div class="dropdown planBackupTo pull-left mr20">\
                  <span><textarea style=" height: 100px;width:300px;line-height:22px;" class="bt-input-text" type="text" name="sBody" id="exclude" placeholder="每行一条规则,目录不能以/结尾，示例：\ndata/config.php\nstatic/upload\n *.log\n"></textarea></span>\
              </div>\
            </p>';
            $("#implement").html(sBody);
            getselectname();
		}
		$("#implement").on('click','.dropdown ul li a',function(ev){
			var sName = $("#sName").attr("val");
			if(!sName) return;
			$(".planname input[name='name']").val(sMsg+'['+sName+']');
		});
		if(type == "path"){
			$('.planname input').attr('readonly',false).removeAttr('style');
		}
	});
}

//下拉菜单名称
function getselectname(){
	$(".dropdown ul li a").click(function(){
		var txt = $(this).text();
		var type = $(this).attr("value");
		$(this).parents(".dropdown").find("button b").text(txt).attr("val",type);
	});
}
//清理
function closeOpt(){
	$("#ptime").html('');
}
//星期
function toWeek(){
	var mBody = '<div class="dropdown planweek pull-left mr20">\
					  <button class="btn btn-default dropdown-toggle" type="button" id="excode" data-toggle="dropdown">\
						<b val="1">'+lan.crontab.TZZ1+'</b> <span class="caret"></span>\
					  </button>\
					  <ul class="dropdown-menu" role="menu" aria-labelledby="excode">\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="1">'+lan.crontab.TZZ1+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="2">'+lan.crontab.TZZ2+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="3">'+lan.crontab.TZZ3+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="4">'+lan.crontab.TZZ4+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="5">'+lan.crontab.TZZ5+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="6">'+lan.crontab.TZZ6+'</a></li>\
						<li><a role="menuitem" tabindex="-1" href="javascript:;" value="0">'+lan.crontab.TZZ7+'</a></li>\
					  </ul>\
					</div>';
	$("#ptime").html(mBody);
	getselectname()
}
//指定1
function toWhere1(ix){
	var mBody ='<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="where1" value="3" maxlength="2" max="31" min="0"></span>\
					<span class="name">'+ix+'</span>\
					</div>';
	$("#ptime").append(mBody);
}
//小时
function toHour(){
	var mBody = '<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="hour" value="1" maxlength="2" max="23" min="0"></span>\
					<span class="name">'+lan.crontab.hour+'</span>\
					</div>';
	$("#ptime").append(mBody);
}

//分钟
function toMinute(){
	var mBody = '<div class="plan_hms pull-left mr20 bt-input-text">\
					<span><input type="number" name="minute" value="30" maxlength="2" max="59" min="0"></span>\
					<span class="name">'+lan.crontab.minute+'</span>\
					</div>';
	$("#ptime").append(mBody);
	
}

//从文件
function toFile(){
	var tBody = '<input type="text" value="" name="file" id="viewfile" onclick="fileupload()" readonly="true">\
				<button class="btn btn-default" onclick="fileupload()">'+lan.public.upload+'</button>';
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val("");
}

//从脚本
function toShell(){
	var shell_body = '';
	var shell_name = '';
	if($("b[val='toShell']").text() === '同步时间'){
		shell_name = '定期同步服务器时间';
		shell_body = 'echo "|-正在尝试从0.pool.bt.cn同步时间..";\n\
ntpdate -u 0.pool.bt.cn\n\
if [ $? = 1 ];then\n\
	echo "|-正在尝试从1.pool.bt.cn同步时间..";\n\
	ntpdate -u 1.pool.bt.cn\n\
fi\n\
if [ $? = 1 ];then\n\
	echo "|-正在尝试从0.asia.pool.ntp.org同步时间..";\n\
	ntpdate -u 0.asia.pool.ntp.org\n\
fi\n\
if [ $? = 1 ];then\n\
	echo "|-正在尝试从www.bt.cn同步时间..";\n\
	getBtTime=$(curl -sS --connect-timeout 3 -m 60 http://www.bt.cn/api/index/get_time)\n\
	if [ "${getBtTime}" ];then	\n\
		date -s "$(date -d @$getBtTime +"%Y-%m-%d %H:%M:%S")"\n\
	fi\n\
fi\n\
echo "|-正在尝试将当前系统时间写入硬件..";\n\
hwclock -w\n\
date\n\
echo "|-时间同步完成!";'
	}
	var tBody = "<textarea class='txtsjs bt-input-text' name='sBody' style='margin: 0px; width: 445px; height: 90px;line-height: 16px;'>"+shell_body+"</textarea>";
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val(shell_name);
}

function toPath() {

}
//木马查杀
function webShell(){
	var sOpt = '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="ALL">所有</a></li>',sOptBody = '';
	$.post('/crontab?action=GetDataList&type=sites',function(rdata){
		$(".planname input[name='name']").attr('readonly','true').css({"background-color":"#f6f6f6","color":"#666"});
		$("#implement").siblings(".controls").html("查杀站点");
		if(rdata.data.length == 0){
			layer.msg(lan.public.list_empty,{icon:2});
			$("#implement").html("<input type='text' class='bt-input-text' style='width:260px;background-color: rgb(246, 246, 246);height:34px'>");
			return
		}
		for(var i=0;i<rdata.data.length;i++){
			if(i==0){// 默认获取第一个值
				$(".planname input[name='name']").val("木马查杀"+'['+rdata.data[i].name+']');
			}
			sOpt += '<li><a role="menuitem" tabindex="-1" href="javascript:;" value="'+rdata.data[i].name+'">'+rdata.data[i].name+'['+rdata.data[i].ps+']</a></li>';			
		}	
		sOptBody ='<div class="dropdown pull-left mr20">\
				  <button class="btn btn-default dropdown-toggle" type="button" id="backdata" data-toggle="dropdown" style="width:auto">\
					<b id="sName" val="'+rdata.data[0].name+'">'+rdata.data[0].name+'['+rdata.data[0].ps+']</b> <span class="caret"></span>\
				  </button>\
				  <ul class="dropdown-menu" role="menu" aria-labelledby="backdata">'+sOpt+'</ul>\
				  <span class="planSign"><i>*</i>本次查杀由长亭牧云强力驱动</span>\
                </div>'
// 		setCookie('default_dir_path','/www/wwwroot/');
// 		setCookie('path_dir_change','/www/wwwroot/');
// 		setInterval(function(){
// 			if(getCookie('path_dir_change') != getCookie('default_dir_path')){
// 				var  path_dir_change = getCookie('path_dir_change')
// 				$(".planname input").val('木马查杀['+getCookie('path_dir_change')+']');
// 				setCookie('default_dir_path',path_dir_change);
// 			}
// 		},500);
		sOptBody += '<p class="clearfix plan">\
            <div class="textname pull-left mr20" style="margin-left: 63px; font-size: 14px;">消息通道</div>\
            <div class="dropdown planBackupTo pull-left mr20 message_start"></div>\
        </p>';
		$("#implement").html(sOptBody);
		message_channel_start();
		getselectname();
		$(".dropdown ul li a").click(function(){
			var sName = $("#sName").attr("val");
			if(!sName) return;
			$(".planname input[name='name']").val("木马查杀"+'['+sName+']');
		});	
	})
}
function message_channel_start(){
	$.post('/config?action=get_settings',function(res){
		var wBody = "",s_mail = res.user_mail.user_name,s_ding =res.dingding.dingding
		if(!s_mail && !s_ding){
			$(".plan-submit").css({"pointer-events":"none","background-color":"#e6e6e6","color":"#333"});
			return $(".message_start").html('<span style="color:red;">未设置消息通道，请前往面板设置添加消息通道配置<a href="https://www.bt.cn/bbs/thread-42312-1-1.html" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a></span>');
		}
		if(s_mail){
		    wBody = '<div class="check_alert" style="margin-right:20px;display: inline-block;">\
				<input id="mail" type="radio" name="alert" title="邮箱" value="mail" '+(s_ding?'checked':(s_mail ?'checked':''))+'>\
				<label for="mail" style="font-weight: normal;font-size: 14px;margin-left: 6px;display: inline;">邮箱</label>\
			</div>'
		}
		if(s_ding){
		    wBody += '<div class="check_alert" style="display: inline-block;">\
				<input id="dingding" type="radio" name="alert" title="钉钉" value="dingding" '+(s_mail?'':'checked')+'>\
				<label for="dingding" style="font-weight: normal;font-size: 14px;margin-left: 6px;display: inline;">钉钉</label>\
			</div>'
		}
		$(".message_start").html(wBody);
	})
}
//从url
function toUrl(){
	var tBody = "<input type='text' style='width:400px; height:34px' class='bt-input-text' name='urladdress_1' id='urladdress_1' placeholder='"+lan.crontab.url_address+"' value='http://' />";
	$("#implement").html(tBody);
	$(".planname input[name='name']").removeAttr('readonly style').val("");
}

//释放内存
function rememory(){
	$(".planname input[name='name']").removeAttr('readonly style').val("");
	$(".planname input[name='name']").val(lan.crontab.mem);
	$("#implement").html(lan.crontab.mem_ps);
	return;
}
//上传
function fileupload(){
	$("#sFile").change(function(){
		$("#viewfile").val($("#sFile").val());
	});
	$("#sFile").click();
}

// 计划任务2021/3/24新增任务通知新增
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

function get_channel_settings(callback){
	var loadT = layer.msg('正在获取配置,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/config?action=get_settings',function(rdata){
		layer.close(loadT);
        if (callback) callback(rdata);
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

function selSave_local() {
	if($('#save_local').val() == '0') {
		$('#save_local').val(1)
		$('#save_local').prop('checked', true)	
	} else {
		$('#save_local').val(0)
		$('#save_local').removeAttr('checked')
	}
}
function modSelSave_local() {
	if($('#modSave_local').val() == '0') {
		$('#modSave_local').val(1)
		$('#modSave_local').prop('checked', true)	
	} else {
		$('#modSave_local').val(0)
		$('#modSave_local').removeAttr('checked')
	}
}

//下拉菜单名称
function getselectnoticename(){
	$(".dropdown ul li a").click(function(){
		var txt = $(this).text();
		var type = $(this).attr("value");
		$(this).parents(".dropdown").find("button b").text(txt).attr("val",type);
		if($("#modNotice").find("button b").attr("val") == '0') {
			$('#modNotice').nextAll().hide()
			$('#selmodnoticeBox').show()
		} else {
			$('#modNotice').nextAll().show()
		}
		if($("#notice").find("button b").attr("val") == '0') {
			$('#messageChannelBox').hide()
			$('#notice_channel').hide()
		}else {
			$('#messageChannelBox').show()
			$('#notice_channel').show()
		}
	});
	$("#saveAddServerDiskToLocal ul li a").click(function(){
		var txt = $(this).text();
		if(txt == '服务器磁盘') {
			$('#selnoticeBox').hide()
		} else {
			$('#selnoticeBox').show()
		}
	});
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

// --计划任务2021/4/21新增任务通知新增结束
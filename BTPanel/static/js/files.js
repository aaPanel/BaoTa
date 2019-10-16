function IsDiskWidth(){
	var comlistWidth = $("#comlist").width();
	var bodyWidth = $(".file-box").width();
	if(comlistWidth + 530 > bodyWidth){
		$("#comlist").css({"width":bodyWidth-530+"px","height":"34px","overflow":"auto"});
	}
	else{
		$("#comlist").removeAttr("style");
	}
}
function Recycle_bin(type){
	$.post('/files?action=Get_Recycle_bin','',function(rdata){
		var body = ''
		switch(type){
			case 1:
				for(var i=0;i<rdata.dirs.length;i++){
					var shortwebname = rdata.dirs[i].name.replace(/'/,"\\'");
					var shortpath = rdata.dirs[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+rdata.dirs[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.dirs[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.dirs[i].size)+'</td>\
								<td>'+getLocalTime(rdata.dirs[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>';
				}
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname.replace('BTDB_','')+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">mysql://'+shortpath.replace('BTDB_','')+'</span></td>\
								<td>-</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
							
						continue;
					}
					var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
					var shortpath = rdata.files[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 2:
				for(var i=0;i<rdata.dirs.length;i++){
					var shortwebname = rdata.dirs[i].name.replace(/'/,"\\'");
					var shortpath = rdata.dirs[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+rdata.dirs[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.dirs[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.dirs[i].size)+'</td>\
								<td>'+getLocalTime(rdata.dirs[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 3:
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1) continue;
					var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
					var shortpath = rdata.files[i].dname;
					if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
					if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
					body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 4:
				for(var i=0;i<rdata.files.length;i++){
					if(ReisImage(getFileName(rdata.files[i].name))){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
					}
				}
				$("#RecycleBody").html(body);
				return;
				break;
			case 5:
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1) continue;
					if(!(ReisImage(getFileName(rdata.files[i].name)))){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">'+shortpath+'</span></td>\
								<td>'+ToSize(rdata.files[i].size)+'</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
					}
				}
				$("#RecycleBody").html(body);
				return;
			case 6:
				for(var i=0;i<rdata.files.length;i++){
					if(rdata.files[i].name.indexOf('BTDB_') != -1){
						var shortwebname = rdata.files[i].name.replace(/'/,"\\'");
						var shortpath = rdata.files[i].dname;
						if(shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
						if(shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
						body += '<tr>\
								<td><span class="ico ico-'+(GetExtName(rdata.files[i].name))+'"></span><span class="tname" title="'+rdata.files[i].name+'">'+shortwebname.replace('BTDB_','')+'</span></td>\
								<td><span title="'+rdata.files[i].dname+'">mysql://'+shortpath.replace('BTDB_','')+'</span></td>\
								<td>-</td>\
								<td>'+getLocalTime(rdata.files[i].time)+'</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_re+'</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/,"\\'") + '\',this)">'+lan.files.recycle_bin_del+'</a>\
								</td>\
							</tr>'
					}
				}
				$("#RecycleBody").html(body);
				return;
				break;
		}
				
		
		var tablehtml = '<div class="re-head">\
				<div style="margin-left: 3px;" class="ss-text">\
                        <em>'+lan.files.recycle_bin_on+'</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox" '+(rdata.status?'checked':'')+'>\
                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="Set_Recycle_bin()"></label>\
                        </div>\
                        <em style="margin-left: 20px;">'+lan.files.recycle_bin_on_db+'</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox" '+(rdata.status_db?'checked':'')+'>\
                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="Set_Recycle_bin(1)"></label>\
                        </div>\
                </div>\
				<span style="line-height: 32px; margin-left: 30px;">'+lan.files.recycle_bin_ps+'</span>\
                <button style="float: right" class="btn btn-default btn-sm" onclick="CloseRecycleBin();">'+lan.files.recycle_bin_close+'</button>\
				</div>\
				<div class="re-con">\
					<div class="re-con-menu">\
						<p class="on" onclick="Recycle_bin(1)">'+lan.files.recycle_bin_type1+'</p>\
						<p onclick="Recycle_bin(2)">'+lan.files.recycle_bin_type2+'</p>\
						<p onclick="Recycle_bin(3)">'+lan.files.recycle_bin_type3+'</p>\
						<p onclick="Recycle_bin(4)">'+lan.files.recycle_bin_type4+'</p>\
						<p onclick="Recycle_bin(5)">'+lan.files.recycle_bin_type5+'</p>\
						<p onclick="Recycle_bin(6)">'+lan.files.recycle_bin_type6+'</p>\
					</div>\
					<div class="re-con-con">\
					<div style="margin: 15px;" class="divtable">\
					<table width="100%" class="table table-hover">\
						<thead>\
							<tr>\
								<th>'+lan.files.recycle_bin_th1+'</th>\
								<th>'+lan.files.recycle_bin_th2+'</th>\
								<th>'+lan.files.recycle_bin_th3+'</th>\
								<th width="150">'+lan.files.recycle_bin_th4+'</th>\
								<th style="text-align: right;" width="110">'+lan.files.recycle_bin_th5+'</th>\
							</tr>\
						</thead>\
					<tbody id="RecycleBody" class="list-list">'+body+'</tbody>\
			</table></div></div></div>';
		if(type == "open"){
			layer.open({
				type: 1,
				shift: 5,
				closeBtn: 2,
				area: ['80%','606px'],
				title: lan.files.recycle_bin_title,
				content: tablehtml
			});
			
			if(window.location.href.indexOf("database") != -1){
				Recycle_bin(6);
				$(".re-con-menu p:last-child").addClass("on").siblings().removeClass("on");
			}else{
				Recycle_bin(1);
			}
		}
		$(".re-con-menu p").click(function(){
			$(this).addClass("on").siblings().removeClass("on");
		})
	});
}
function getFileName(name){
	var text = name.split(".");
	var n = text.length-1;
	text = text[n];
	return text;
}
function ReisImage(fileName){
	var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
	for(var i=0; i<exts.length; i++){
		if(fileName == exts[i]) return true
	}
	return false;
}
function ReRecycleBin(path,obj){
	layer.confirm(lan.files.recycle_bin_re_msg,{title:lan.files.recycle_bin_re_title,closeBtn:2,icon:3},function(){
		var loadT = layer.msg(lan.files.recycle_bin_re_the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files?action=Re_Recycle_bin','path='+encodeURIComponent(path),function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$(obj).parents('tr').remove();
		});
	});
}
function DelRecycleBin(path,obj){
	layer.confirm(lan.files.recycle_bin_del_msg,{title:lan.files.recycle_bin_del_title,closeBtn:2,icon:3},function(){
		var loadT = layer.msg(lan.files.recycle_bin_del_the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files?action=Del_Recycle_bin','path='+encodeURIComponent(path),function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$(obj).parents('tr').remove();
		});
	});
}
function CloseRecycleBin(){
	layer.confirm(lan.files.recycle_bin_close_msg,{title:lan.files.recycle_bin_close,closeBtn:2,icon:3},function(){
		var loadT = layer.msg("<div class='myspeed'>"+lan.files.recycle_bin_close_the+"</div>",{icon:16,time:0,shade: [0.3, '#000']});
		setTimeout(function(){
			getSpeed('.myspeed');
		},1000);
		$.post('/files?action=Close_Recycle_bin','',function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			$("#RecycleBody").html('');
		});
	});
}
function Set_Recycle_bin(db){
	var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
	var data = {}
	if(db == 1){
		data = {db:db};
	}
	$.post('/files?action=Recycle_bin',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	});
}

function get_path_size(path) {
    var loadT = layer.msg('正在计算目录大小,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/files?action=get_path_size', { path: path }, function (rdata) {
        layer.close(loadT);
        var myclass = '.' + rdata.path.replace(/[^\w]/g, '-');
        console.log(myclass)
        console.log($(myclass).text())
        $(myclass).text(ToSize(rdata.size));
    });
}


function path_check(path) {
    if (path == '/') return path;
    path = path.replace(/[\/]{2,}/g, '/');
    path = path.replace(/[\/]+$/g, '');
    return path;
}

function GetFiles(Path,sort) {
    var searchtype = Path;
    var p = '1';
	if(!isNaN(Path)){
		p = Path;
		Path = getCookie('Path');
    }

    Path = path_check(Path);

    var data = {};
	var search = '';
	var searchV = $("#SearchValue").val();
    if (searchV.length > 0 && searchtype == "1") {
        data['search'] = searchV;
        if ($("#search_all")[0].checked) {
            data['all'] = 'True'
        }
    }

    var sorted = '';
    var reverse = '';
    if (!sort) {
        sort = getCookie('files_sort');
        reverse = getCookie(sort + '_reverse');
    } else {
        reverse = getCookie(sort + '_reverse');
        if (reverse === 'True') {
            reverse = 'False';
        } else {
            reverse = 'True';
        }
    }
    if (sort) {
        data['sort'] = sort;
        data['reverse'] = reverse;
        setCookie(sort + '_reverse', reverse);
        setCookie('files_sort', sort);
    }


	var showRow = getCookie('showRow');
	if(!showRow) showRow = '200';
	var Body = '';
    data['path'] = Path;


    if (searchV) {
        var loadT = layer.msg('正在搜索,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000']});
    }
	var totalSize = 0;
	$.post('/files?action=GetDir&tojs=GetFiles&p=' + p + '&showRow=' + showRow + search, data, function(rdata) {
        if (searchV) layer.close(loadT);
        if (rdata.status === false) {
            layer.msg(rdata.msg, { icon: 2 });
            return;
        }
		
		var rows = ['10','50','100','200','500','1000','2000'];
		var rowOption = '';
		for(var i=0;i<rows.length;i++){
			var rowSelected = '';
			if(showRow == rows[i]) rowSelected = 'selected';
			rowOption += '<option value="'+rows[i]+'" '+rowSelected+'>'+rows[i]+'</option>';
		}
		
		$("#filePage").html(rdata.PAGE);
		$("#filePage div").append("<span class='Pcount-item'>每页<select style='margin-left: 3px;margin-right: 3px;border:#ddd 1px solid' class='showRow'>"+rowOption+"</select>条</span>");
		$("#filePage .Pcount").css("left","16px");
		if(rdata.DIR == null) rdata.DIR = [];
		for (var i = 0; i < rdata.DIR.length; i++) {
			var fmp = rdata.DIR[i].split(";");
			var cnametext =fmp[0] + fmp[5];
			fmp[0] = fmp[0].replace(/'/,"\\'");
			if(cnametext.length>20){
				cnametext = cnametext.substring(0,20)+'...'
			}
			if(isChineseChar(cnametext)){
				if(cnametext.length>10){
					cnametext = cnametext.substring(0,10)+'...'
				}
			}
			var timetext ='--';
			if(getCookie("rank") == "a"){
					$("#set_list").addClass("active");
					$("#set_icon").removeClass("active");
					Body += "<tr class='folderBoxTr' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir'>\
						<td><input type='checkbox' name='id' value='"+fmp[0]+"'></td>\
						<td class='column-name'><span class='cursor' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='ico ico-folder'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + "</a></span></td>\
						<td><a class='btlink "+ (rdata.PATH + '/' + fmp[0]).replace(/[^\w]/g,'-') + "' onclick=\"get_path_size('" + rdata.PATH + "/" + fmp[0]+"')\">点击计算</a></td>\
						<td>"+getLocalTime(fmp[2])+"</td>\
						<td>"+fmp[3]+"</td>\
						<td>"+fmp[4]+"</td>\
						<td class='editmenu'><span>\
						<a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_copy+"</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH +"/"+ fmp[0]+ "')\">"+lan.files.file_menu_mv+"</a> | \
						<a class='btlink' href=\"javascript:ReName(0,'" + fmp[0] + "');\">"+lan.files.file_menu_rename+"</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH + "/"+fmp[0] + "');\">"+lan.files.file_menu_auth+"</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH +"/" +fmp[0] + "');\">"+lan.files.file_menu_zip+"</a> | \
						<a class='btlink' href='javascript:;' onclick=\"DeleteDir('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_del+"</a></span>\
					</td></tr>";
			}
			else{
				$("#set_icon").addClass("active");
				$("#set_list").removeClass("active");
				Body += "<div class='file folderBox menufolder' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir' title='"+lan.files.file_name+"：" + fmp[0]+"&#13;"+lan.files.file_size+"：" + ToSize(fmp[1])+"&#13;"+lan.files.file_etime+"："+getLocalTime(fmp[2])+"&#13;"+lan.files.file_auth+"："+fmp[3]+"&#13;"+lan.files.file_own+"："+fmp[4]+"'>\
						<input type='checkbox' name='id' value='"+fmp[0]+"'>\
						<div class='ico ico-folder' ondblclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"></div>\
						<div class='titleBox' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
			}
		}
		for (var i = 0; i < rdata.FILES.length; i++) {
			if(rdata.FILES[i] == null) continue;
			var fmp = rdata.FILES[i].split(";");
			var displayZip = isZip(fmp[0]);
			var bodyZip = '';
			var download = '';
			var cnametext =fmp[0] + fmp[5];
			fmp[0] = fmp[0].replace(/'/,"\\'");
			if(cnametext.length>48){
				cnametext = cnametext.substring(0,48)+'...'
			}
			if(isChineseChar(cnametext)){
				if(cnametext.length>16){
					cnametext = cnametext.substring(0,16)+'...'
				}
			}
			if(displayZip != -1){
				bodyZip = "<a class='btlink' href='javascript:;' onclick=\"UnZip('" + rdata.PATH +"/" +fmp[0] + "'," + displayZip + ")\">"+lan.files.file_menu_unzip+"</a> | ";
			}
			if(isText(fmp[0])){
				bodyZip = "<a class='btlink' href='javascript:;' onclick=\"openEditorView(0,'" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_edit+"</a> | ";
			}
			if(isImage(fmp[0])){
				download = "<a class='btlink' href='javascript:;' onclick=\"GetImage('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_img+"</a> | ";
			}else{
				download = "<a class='btlink' href='javascript:;' onclick=\"GetFileBytes('" + rdata.PATH +"/"+ fmp[0] + "',"+fmp[1]+")\">"+lan.files.file_menu_down+"</a> | ";
			}
			
			totalSize +=  parseInt(fmp[1]);
            if (getCookie("rank") == "a") {
                var fileMsg = '';
                switch (fmp[0]) {
                    case '.user.ini':
                        fileMsg = 'PS: PHP用户配置文件(防跨站)!';
                        break;
                    case '.htaccess':
                        fileMsg = 'PS: Apache用户配置文件(伪静态)';
                        break;
                    case 'swap':
                        fileMsg = 'PS: 宝塔默认设置的SWAP交换分区文件';
                        break;
                }

                if (fmp[0].indexOf('.upload.tmp') != -1) {
                    fileMsg = 'PS: 宝塔文件上传临时文件,重新上传从断点续传,可删除';
                }

                if (fileMsg != '') {
                    fileMsg = '<span style="margin-left: 30px; color: #999;">' + fileMsg + '</span>';
                }
				Body += "<tr class='folderBoxTr' data-path='" + rdata.PATH +"/"+ fmp[0] + "' filetype='" + fmp[0] + "'><td><input type='checkbox' name='id' value='"+fmp[0]+"'></td>\
						<td class='column-name'><span class='ico ico-"+ (GetExtName(fmp[0])) + "'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + fileMsg+"</a></td>\
						<td>" + (ToSize(fmp[1])) + "</td>\
						<td>" + ((fmp[2].length > 11)?fmp[2]:getLocalTime(fmp[2])) + "</td>\
						<td>"+fmp[3]+"</td>\
						<td>"+fmp[4]+"</td>\
						<td class='editmenu'>\
						<span><a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_copy+"</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_mv+"</a> | \
						<a class='btlink' href='javascript:;' onclick=\"ReName(0,'" + fmp[0] + "')\">"+lan.files.file_menu_rename+"</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH +"/"+ fmp[0] + "');\">"+lan.files.file_menu_auth+"</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH +"/" +fmp[0] + "');\">"+lan.files.file_menu_zip+"</a> | \
						"+bodyZip+download+"\
						<a class='btlink' href='javascript:;' onclick=\"DeleteFile('" + rdata.PATH +"/"+ fmp[0] + "')\">"+lan.files.file_menu_del+"</a>\
						</span></td></tr>";
			}
			else{
				Body += "<div class='file folderBox menufile' data-path='" + rdata.PATH +"/"+ fmp[0] + "' filetype='"+fmp[0]+"' title='"+lan.files.file_name+"：" + fmp[0]+"&#13;"+lan.files.file_size+"：" + ToSize(fmp[1])+"&#13;"+lan.files.file_etime+"："+getLocalTime(fmp[2])+"&#13;"+lan.files.file_auth+"："+fmp[3]+"&#13;"+lan.files.file_own+"："+fmp[4]+"'>\
						<input type='checkbox' name='id' value='"+fmp[0]+"'>\
						<div class='ico ico-"+(GetExtName(fmp[0]))+"'></div>\
						<div class='titleBox'><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
			}
        }
        var dirInfo = '(' + lan.files.get_size.replace('{1}', rdata.DIR.length + '').replace('{2}', rdata.FILES.length + '') + '<font id="pathSize">' + (ToSize(totalSize)) + '<a class="btlink ml5" onClick="GetPathSize()">' + lan.files.get + '</a></font>)';
		$("#DirInfo").html(dirInfo);
        if (getCookie("rank") === "a") {
            var sort_icon = '<span data-id="status" class="glyphicon glyphicon-triangle-' + ((data['reverse'] !== 'False') ? 'bottom' :'top')+'" style="margin-left:5px;color:#bbb"></span>';
            var tablehtml = '<div class="newTable"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
                              <thead>\
                                  <tr>\
                                      <th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon:'') +'</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') +'</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') +'</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') +'</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') +'</a></th>\
                                      <th style="text-align: right;" width="330">'+lan.files.file_act+'</th>\
									  <th></th>\
                                  </tr>\
                              </thead>\
                              </table>\
							</div>\
							<div class="newTableShadow"></div>\
            				<div class="oldTable" style="overflow: auto;height: 500px;margin-top: -8px;"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
							<thead>\
								<tr>\
									<th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon:'') +'</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') +'</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') +'</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') +'</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') +'</a></th>\
									<th style="text-align: right;" width="330">'+lan.files.file_act+'</th>\
								</tr>\
							</thead>\
							<tbody id="filesBody" class="list-list">'+Body+'</tbody>\
						</table></div><div class="oldTableShadow"></div>';
			$("#fileCon").removeClass("fileList").html(tablehtml);
			$("#tipTools").width($("#fileCon").width());
		}
		else{
			$("#fileCon").addClass("fileList").html(Body);
			$("#tipTools").width($("#fileCon").width());
		}
		$("#DirPathPlace input").val(rdata.PATH);
		var BarTools = '<div class="btn-group">\
						<button class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\
						'+lan.files.new+' <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">\
						<li><a href="javascript:CreateFile(0,\'' + Path + '\');">'+lan.files.new_empty_file+'</a></li>\
						<li><a href="javascript:CreateDir(0,\'' + Path + '\');">'+lan.files.new_dir+'</a></li>\
						</ul>\
						</div>';
		if (rdata.PATH != '/') {
			BarTools += ' <button onclick="javascript:BackDir();" class="btn btn-default btn-sm glyphicon glyphicon-arrow-left" title="'+lan.files.return+'"></button>';
		}
		setCookie('Path',rdata.PATH);
		BarTools += ' <button onclick="javascript:GetFiles(\'' + rdata.PATH + '\');" class="btn btn-default btn-sm glyphicon glyphicon-refresh" title="'+lan.public.fresh+'"></button> <button onclick="web_shell()" title="'+lan.files.shell+'" type="button" class="btn btn-default btn-sm"><em class="ico-cmd"></em></button>';
		

        //收藏夹
        var shtml = '<div class="btn-group">\
						<button style="margin-left: 5px;" class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">收藏夹 <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">'

        for (var i = 0; i < rdata.STORE.length; i++) {
            shtml += '<li class="file-types"><div style=" padding: 3px 0;"><span class="ico ico-folder"></span><a href="javascript:;">' + rdata.STORE[i].name + '</a><span class="glyphicon glyphicon-triangle-right file-type-span" aria-hidden="true"></span></div><ul data-file-type="' + rdata.STORE[i].name + '" class="dropdown-menu-li">'
            if (rdata.STORE[i].data.length > 0) {
                for (var j = 0; j < rdata.STORE[i].data.length; j++) {
                    if (rdata.STORE[i].data[j].type == "dir") {
                        shtml += '<li title="' + rdata.STORE[i].data[j].path + '" class = "file-type-li"><div style=" padding: 3px 0;"><span class="ico ico-folder"></span><a  href="javascript:;" onclick="GetFiles(\'' + rdata.STORE[i].data[j].path + '\');">' + rdata.STORE[i].data[j].path + '</a></div></li>';
                    }
                    else {
                        shtml += '<li title="' + rdata.STORE[i].data[j].path + '" class = "file-type-li"><div  style=" padding: 3px 0;"><span class="ico ico-file"></span><a href="javascript:;" onclick="openEditorView(0,\'' + rdata.STORE[i].data[j].path + '\')" >' + rdata.STORE[i].data[j].path + '</a></div></li>';
                    }
                }
            }
            else {
                shtml += '<li><a style="padding-left: 15px;" href="javascript:;">暂无数据</a></li>';
            }
            shtml += '</ul>';
        }
        shtml += '<li style="text-align: center;"><a href="javascript: ;" onclick="set_file_store(\'' + rdata.PATH + '\')">+ 管理</a></li></ul></div>'

        BarTools += shtml;

        var copyName = getCookie('copyFileName');
        var cutName = getCookie('cutFileName');
        var isPaste = (copyName == 'null') ? cutName : copyName;
        if (isPaste != 'null' && isPaste != undefined) {
            BarTools += ' <button onclick="javascript:PasteFile(\'' + (GetFileName(isPaste)) + '\');" class="btn btn-Warning btn-sm">' + lan.files.paste + '</button>';
        }

		$("#Batch").html('');
		var BatchTools = '';
		var isBatch = getCookie('BatchSelected');
		if (isBatch == 1 || isBatch == '1'){
			BatchTools += ' <button onclick="javascript:BatchPaste();" class="btn btn-default btn-sm">'+lan.files.paste_all+'</button>';
		}
		$("#Batch").html(BatchTools);
		$("#setBox").prop("checked", false);
		
		$("#BarTools").html(BarTools);
		
		$("input[name=id]").click(function(){
			if($(this).prop("checked")) {
				$(this).prop("checked", true);
				$(this).parents("tr").addClass("ui-selected");
			}
			else{
				$(this).prop("checked", false);
				$(this).parents("tr").removeClass("ui-selected");
			}
			showSeclect()
        });

        // 鼠标移入移出事件
        $('.file-types').hover(function () {
            // 鼠标移入时添加hover类            
            $('.dropdown-menu-li').hide();
            $(this).find('.dropdown-menu-li').show();

        }, function () {
            $('.dropdown-menu-li').hide();
            // 鼠标移出时移出hover类

        });

		$("#setBox").click(function() {
			if ($(this).prop("checked")) {
				$("input[name=id]").prop("checked", true);
				$("#filesBody > tr").addClass("ui-selected");
				
			} else {
				$("input[name=id]").prop("checked", false);
				$("#filesBody > tr").removeClass("ui-selected");
			}
			showSeclect();
        });

		$("#filesBody .btlink").click(function(e){
			e.stopPropagation();
		});
		$("input[name=id]").dblclick(function(e){
			e.stopPropagation();
		});
        $("#filesBody").bind("contextmenu",function(e){
			return false;
		});
		bindselect();
        $("#filesBody").mousedown(function(e){
			var count = totalFile();
			if(e.which == 3) {
				if(count>1){
					RClickAll(e);
				}
				else{
					return
				}
			}
		});
		$(".folderBox,.folderBoxTr").mousedown(function(e){
			var count = totalFile();
			if(e.which == 3) {
				if(count <= 1){
					var a = $(this);
					a.contextify(RClick(a.attr("filetype"),a.attr("data-path"),a.find("input").val(),rdata));
				}
				else{
					RClickAll(e);
				}
			}
		});
		$(".showRow").change(function(){
			setCookie('showRow',$(this).val());
			GetFiles(p);
		});
		PathPlaceBtn(rdata.PATH);
      	auto_table_width();
	});
}
function auto_table_width(){
	var oldTable = $(window).height() - $('#tipTools')[0].getBoundingClientRect().height - $('#filePage')[0].getBoundingClientRect().height - $('.footer')[0].getBoundingClientRect().height - 111;
	var oldTable_heigth =  $('.oldTable table').height();
    $('.oldTable thead th').each(function(index,el){
        var table_th = $('.oldTable thead th').length;
        $('.newTable thead th').eq(index).attr('width',el.offsetWidth);
        if(index == (table_th - 1)) $('.newTable thead th').eq(table_th).attr('width','10').css('padding','0');
    });
	if(oldTable_heigth > oldTable){
		$('.oldTableShadow,.newTableShadow').show();
		$('.oldTable').css('marginTop','0')
	}else{
    	$('.oldTableShadow,.newTableShadow').hide();
		$('.oldTable').css('marginTop','0')
	}
  	$('.oldTable').height(oldTable);
	$('.oldTable table').css({'marginTop':'-47px'})

}


function totalFile(){
	var el = $("input[name='id']");
	var len = el.length;
	var count = 0;
	for(var i=0;i<len;i++){
		if(el[i].checked == true){
			count++;
		}
	}
	return count;
}
function bindselect(){
	$("#filesBody").selectable({
		autoRefresh: false,
		filter:"tr,.folderBox",
		cancel: "a,span,input,.ico-folder",
		selecting:function(e){
			$(".ui-selecting").find("input").prop("checked", true);
			showSeclect();
		},
		selected:function(e){
			$(".ui-selectee").find("input").prop("checked", false);
			$(".ui-selected", this).each(function() {
				$(this).find("input").prop("checked", true);
				showSeclect();
			});
		},
		unselecting:function(e){
			$(".ui-selectee").find("input").prop("checked", false);
			$(".ui-selecting").find("input").prop("checked", true);
			showSeclect();
			$("#rmenu").hide()
		}
	});
	$("#filesBody").selectable("refresh");
	$(".ico-folder").click(function(){
		$(this).parent().addClass("ui-selected").siblings().removeClass("ui-selected");
		$(".ui-selectee").find("input").prop("checked", false);
		$(this).prev("input").prop("checked", true);
		showSeclect();
	})
}
function showSeclect(){
	var count = totalFile();
	var BatchTools = '';
	if(count > 1){
		BatchTools = '<button onclick="javascript:Batch(1);" class="btn btn-default btn-sm">'+lan.files.file_menu_copy+'</button>\
						  <button onclick="javascript:Batch(2);" class="btn btn-default btn-sm">'+lan.files.file_menu_mv+'</button>\
						  <button onclick="javascript:Batch(3);" class="btn btn-default btn-sm">'+lan.files.file_menu_auth+'</button>\
						  <button onclick="javascript:Batch(5);" class="btn btn-default btn-sm">'+lan.files.file_menu_zip+'</button>\
						  <button onclick="javascript:Batch(4);" class="btn btn-default btn-sm">'+lan.files.file_menu_del+'</button>'
		$("#Batch").html(BatchTools);
	}else{
		$("#Batch").html(BatchTools);
	}
}
$("#tipTools").width($(".file-box").width());
$("#PathPlaceBtn").width($(".file-box").width()-700);
$("#DirPathPlace input").width($(".file-box").width()-700);
if($(window).width()<1160){
	$("#PathPlaceBtn").width(290);
}
window.onresize = function(){
	$("#tipTools").width($(".file-box").width()-30);
	$("#PathPlaceBtn").width($(".file-box").width()-700);
	$("#DirPathPlace input").width($(".file-box").width()-700);
	if($(window).width()<1160){
		$("#PathPlaceBtn,#DirPathPlace input").width(290);
	}
	PathLeft();
	IsDiskWidth()
  	auto_table_width();
}
function Batch(type,access){
	var path = $("#DirPathPlace input").val();
	var el = document.getElementsByTagName('input');
	var len = el.length;
	var data='path='+path+'&type='+type;
    var name = 'data';
    var datas = []
	
	var oldType = getCookie('BatchPaste');
	
	for(var i=0;i<len;i++){
        if (el[i].checked == true && el[i].value != 'on') {
            datas.push(el[i].value)
		}
    }

    data += "&data=" + encodeURIComponent(JSON.stringify(datas))
	
	if(type == 3 && access == undefined){
		SetChmod(0,lan.files.all);
		return;
	}
	
	if(type < 3) setCookie('BatchSelected', '1');
	setCookie('BatchPaste',type);
	
	if(access == 1){
		var access = $("#access").val();
		var chown = $("#chown").val();
		data += '&access='+access+'&user='+chown;
		layer.closeAll();
	}
	if(type == 4){
		AllDeleteFileSub(data,path);
		setCookie('BatchPaste',oldType);
		return;
	}
	
	if(type == 5){
		var names = '';
		for(var i=0;i<len;i++){
			if(el[i].checked == true && el[i].value != 'on'){
				names += el[i].value + ',';
			}
		}
		Zip(names);
		return;
	}
		
	myloadT = layer.msg("<div class='myspeed'>"+lan.public.the+"</div>",{icon:16,time:0,shade: [0.3, '#000']});
	setTimeout(function(){getSpeed('.myspeed');},1000);
	$.post('/files?action=SetBatchData',data,function(rdata){
		layer.close(myloadT);
		GetFiles(path);
		layer.msg(rdata.msg,{icon:1});
	});
}
function BatchPaste(){
	var path = $("#DirPathPlace input").val();
	var type = getCookie('BatchPaste');
	var data = 'type='+type+'&path='+path;
	
	$.post('/files?action=CheckExistsFiles',{dfile:path},function(result){
		if(result.length > 0){
			var tbody = '';
			for(var i=0;i<result.length;i++){
				tbody += '<tr><td>'+result[i].filename+'</td><td>'+ToSize(result[i].size)+'</td><td>'+getLocalTime(result[i].mtime)+'</td></tr>';
			}
            var mbody = '<div class="divtable" style="height: 395px;overflow: auto;border: #ddd 1px solid;position: relative;"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
						<tbody>'+tbody+'</tbody>\
						</table></div>';
			SafeMessage('即将覆盖以下文件',mbody,function(){
				BatchPasteTo(data,path);
			});
			$(".layui-layer-page").css("width","500px");
		}else{
			BatchPasteTo(data,path);
		}
	});
}
	
function BatchPasteTo(data,path){
	myloadT = layer.msg("<div class='myspeed'>"+lan.public.the+"</div>",{icon:16,time:0,shade: [0.3, '#000']});
	setTimeout(function(){getSpeed('.myspeed');},1000);
	$.post('files?action=BatchPaste',data,function(rdata){
		layer.close(myloadT);
		setCookie('BatchSelected', null);
		GetFiles(path);
		layer.msg(rdata.msg,{icon:1});
	});
}
function GetExtName(fileName){
	var extArr = fileName.split(".");	
	var exts = ['folder','folder-unempty','sql','c','cpp','cs','flv','css','js','htm','html','java','log','mht','php','url','xml','ai','bmp','cdr','gif','ico','jpeg','jpg','JPG','png','psd','webp','ape','avi','flv','mkv','mov','mp3','mp4','mpeg','mpg','rm','rmvb','swf','wav','webm','wma','wmv','rtf','docx','fdf','potm','pptx','txt','xlsb','xlsx','7z','cab','iso','bz2','rar','zip','gz','bt','file','apk','bookfolder','folder','folder-empty','folder-unempty','fromchromefolder','documentfolder','fromphonefolder','mix','musicfolder','picturefolder','videofolder','sefolder','access','mdb','accdb','sql','c','cpp','cs','js','fla','flv','htm','html','java','log','mht','php','url','xml','ai','bmp','cdr','gif','ico','jpeg','jpg','JPG','png','psd','webp','ape','avi','flv','mkv','mov','mp3','mp4','mpeg','mpg','rm','rmvb','swf','wav','webm','wma','wmv','doc','docm','dotx','dotm','dot','rtf','docx','pdf','fdf','ppt','pptm','pot','potm','pptx','txt','xls','csv','xlsm','xlsb','xlsx','7z','gz','cab','iso','rar','zip','bt','file','apk','css'];
	var extLastName = extArr[extArr.length - 1];
	for(var i=0; i<exts.length; i++){
		if(exts[i]==extLastName){
			return exts[i];
		}
	}
	return 'file';
}
function ShowEditMenu(){
	$("#filesBody > tr").hover(function(){
		$(this).addClass("hover");
	},function(){
		$(this).removeClass("hover");
	}).click(function(){
		$(this).addClass("on").siblings().removeClass("on");
	})
}
function GetFileName(fileNameFull) {
	var pName = fileNameFull.split('/');
	return pName[pName.length - 1];
}
function GetDisk() {
	var LBody = '';
	$.get('/system?action=GetDiskInfo', function(rdata) {
		for (var i = 0; i < rdata.length; i++) {
			LBody += "<span onclick=\"GetFiles('" + rdata[i].path + "')\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" + (rdata[i].path=='/'?lan.files.path_root:rdata[i].path) + "(" + rdata[i].size[2] + ")</span>";
		}
		var trash = '<span id="recycle_bin" onclick="Recycle_bin(\'open\')" title="'+lan.files.recycle_bin_title+'" style="position: absolute; border-color: #ccc; right: 77px;"><span class="glyphicon glyphicon-trash"></span>&nbsp;'+lan.files.recycle_bin_title+'</span>';
		$("#comlist").html(LBody+trash);
		IsDiskWidth();
	});
}
function BackDir() {
	var str = $("#DirPathPlace input").val().replace('//','/');
	if(str.substr(str.length-1,1) == '/'){
			str = str.substr(0,str.length-1);
	}
	var Path = str.split("/");
	var back = '/';
	if (Path.length > 2) {
		var count = Path.length - 1;
		for (var i = 0; i < count; i++) {
			back += Path[i] + '/';
		}
		if(back.substr(back.length-1,1) == '/'){
			back = back.substr(0,back.length-1);
		}
		GetFiles(back);
	} else {
		back += Path[0];
		GetFiles(back);
	}
	setTimeout('PathPlaceBtn(getCookie("Path"));',200);
}
function CreateFile(type, path) {
	if (type == 1) {
		var fileName = $("#newFileName").val();
		layer.msg(lan.public.the, { icon: 16, time: 10000 });
		$.post('/files?action=CreateFile', 'path=' + encodeURIComponent(path + '/' + fileName), function(rdata) {
			layer.close(getCookie('layers'));
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2});
			if(rdata.status){
				GetFiles($("#DirPathPlace input").val());
				openEditorView(0,path + '/' + fileName);
			}
		});
		return;
	}
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '320px', 
		title: lan.files.new_empty_file,
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newFileName" value="" placeholder="'+lan.files.file_name+'" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm layer_close">'+lan.public.close+'</button>\
					<button id="CreateFileBtn" type="button" class="btn btn-success btn-sm" onclick="CreateFile(1,\'' + path + '\')">'+lan.files.new+'</button>\
					</div>\
				</div>',
		success:function(layers,index){
			$('.layer_close').click(function(){
				layer.close(index);
			});
		}
	});
	setCookie('layers',layers);
	$("#newFileName").focus().keyup(function(e){
		if(e.keyCode == 13) $("#CreateFileBtn").click();
	});
}
function CreateDir(type, path) {
	if (type == 1) {
		var dirName = $("#newDirName").val();
		layer.msg(lan.public.the, {
			icon: 16,
			time: 10000
		});
		$.post('/files?action=CreateDir', 'path=' + encodeURIComponent(path + '/' + dirName), function(rdata) {
			layer.close(getCookie('layers'));
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			GetFiles($("#DirPathPlace input").val());
		});
		return;
	}
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '320px',
		title: lan.files.new_dir,
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
					<input type="text" class="bt-input-text" name="Name" id="newDirName" value="" placeholder="'+lan.files.dir_name+'" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+lan.public.close+'</button>\
					<button type="button" id="CreateDirBtn" class="btn btn-success btn-sm btn-title" onclick="CreateDir(1,\'' + path + '\')">'+lan.files.new+'</button>\
					</div>\
				</div>',
		success:function(layers,index){
			$('.layer_close').click(function(){
				layer.close(index);
			});
		}
	});
	setCookie('layers',layers);
	$("#newDirName").focus().keyup(function(e){
		if(e.keyCode == 13) $("#CreateDirBtn").click();
	});
}
// 删除文件
function DeleteFile(fileName){
	layer.confirm(lan.get('recycle_bin_confirm',[fileName]),{title:lan.files.del_file,closeBtn:2,icon:3},function(index){
		layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files?action=DeleteFile', 'path=' + encodeURIComponent(fileName), function(rdata) {
			layer.close(index);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			GetFiles($("#DirPathPlace input").val());
		});
	});
}
function DeleteDir(dirName){
	layer.confirm(lan.get('recycle_bin_confirm_dir',[dirName]),{title:lan.files.del_dir,closeBtn:2,icon:3},function(index){
		layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/files?action=DeleteDir', 'path=' + encodeURIComponent(dirName), function(rdata) {
			layer.close(index);
			layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
			GetFiles($("#DirPathPlace input").val());
		});
	});
}
function AllDeleteFileSub(data,path){
	layer.confirm(lan.files.del_all_msg,{title:lan.files.del_all_file,closeBtn:2,icon:3},function(index){
		layer.msg("<div class='myspeed'>"+lan.public.the+"</div>",{icon:16,time:0,shade: [0.3, '#000']});
		setTimeout(function(){getSpeed('.myspeed');},1000);
		$.post('files?action=SetBatchData',data,function(rdata){
			layer.close(index);
			GetFiles(path);
			layer.msg(rdata.msg,{icon:1});
		});
	});
}
function ReloadFiles(){
	setInterval(function(){
		var path = $("#DirPathPlace input").val();
		GetFiles(path);
	},3000);
}
function DownloadFile(action){
	if(action == 1){
		var fUrl = $("#mUrl").val();
		fUrl = encodeURIComponent(fUrl);
		fpath = $("#dpath").val();
        fname = encodeURIComponent($("#dfilename").val());
        if (!fname) {
            durl = $("#mUrl").val()
            tmp = durl.split('/')
            $("#dfilename").val(tmp[tmp.length - 1])
            fname = encodeURIComponent($("#dfilename").val());
            if (!fname) {
                layer.msg('文件名不能为空!');
                return;
            }
        }
		layer.close(getCookie('layers'))
		layer.msg(lan.files.down_task,{time:0,icon:16,shade: [0.3, '#000']});
		$.post('/files?action=DownloadFile','path='+fpath+'&url='+fUrl+'&filename='+fname,function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			GetFiles(fpath);
            GetTaskCount();
            task_stat();
		});
		return;
	}
	var path = $("#DirPathPlace input").val();
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '500px',
		title: lan.files.down_title,
		content: '<form class="bt-form pd20 pb70">\
					<div class="line">\
					<span class="tname">'+lan.files.down_url+':</span><input type="text" class="bt-input-text" name="url" id="mUrl" value="" placeholder="'+lan.files.down_url+'" style="width:330px" />\
					</div>\
					<div class="line">\
					<span class="tname ">'+lan.files.down_to+':</span><input type="text" class="bt-input-text" name="path" id="dpath" value="'+path+'" placeholder="'+lan.files.down_to+'" style="width:330px" />\
					</div>\
					<div class="line">\
					<span class="tname">'+lan.files.file_name+':</span><input type="text" class="bt-input-text" name="filename" id="dfilename" value="" placeholder="'+lan.files.down_save+'" style="width:330px" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm layer_close">'+lan.public.close+'</button>\
					<button type="button" id="dlok" class="btn btn-success btn-sm dlok" onclick="DownloadFile(1)">'+lan.public.ok+'</button>\
					</div>\
				</form>',
		success:function(layers,index){
			$('.layer_close').click(function(){
				layer.close(index)
			});
		}
	});
	setCookie('layers',layers);
    //fly("dlok");
    $("#mUrl").change(function () {
		durl = $(this).val()
		tmp = durl.split('/')
		$("#dfilename").val(tmp[tmp.length-1])
    });
}
function ExecShell(action){
	if(action == 1){
		var path = $("#DirPathPlace input").val();
		var exec = encodeURIComponent($("#mExec").val());
		$.post('/files?action=ExecShell','path='+path+'&shell='+exec,function(rdata){
			if(rdata.status){
				$("#mExec").val('');
				GetShellEcho();
			}
			else{
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
			}
			
		});
		return;
	}
	layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: ['70%','600px'], 
		title: lan.files.shell_title,
		content: '<div class="bt-form pd15">\
					<div class="shellcode"><pre id="Result"></pre></div>\
					<div class="line">\
					<input type="text" class="bt-input-text" name="exec" id="mExec" value="" placeholder="'+lan.files.shell_ps+'" onkeydown="if(event.keyCode==13)ExecShell(1);" /><span class="shellbutton btn btn-default btn-sm pull-right" onclick="ExecShell(1)" style="width:10%">'+lan.files.shell_go+'</span>\
					</div>\
				</div>'
	});
	setTimeout(function(){
		outTimeGet();
	},1000);
	
}

var outTime = null;
function outTimeGet(){
	outTime = setInterval(function(){
		if(!$("#mExec").attr('name')){
			clearInterval(outTime);
			return;
		}
		GetShellEcho();
	},1000);
}

function GetShellEcho(){
	$.post('/files?action=GetExecShellMsg','',function(rdata){
		$("#Result").html(rdata);
		$(".shellcode").scrollTop($(".shellcode")[0].scrollHeight);
	});
}
function ReName(type, fileName) {
	if (type == 1) {
		var path = $("#DirPathPlace input").val();
		var newFileName = encodeURIComponent(path + '/' + $("#newFileName").val());
		var oldFileName = encodeURIComponent(path + '/' + fileName);
		layer.msg(lan.public.the, {icon: 16,time: 10000});
		$.post('/files?action=MvFile', 'sfile=' + oldFileName + '&dfile=' + newFileName + '&rename=true', function(rdata) {
			layer.close(getCookie('layers'));
			layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
			GetFiles(path);
		});
		return;
	}
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '320px', 
		title: lan.files.file_menu_rename,
		content: '<div class="bt-form pd20 pb70">\
				<div class="line">\
				<input type="text" class="bt-input-text" name="Name" id="newFileName" value="' + fileName + '" placeholder="'+lan.files.file_name+'" style="width:100%" />\
				</div>\
				<div class="bt-form-submit-btn">\
				<button type="button" class="btn btn-danger btn-sm btn-title layers_close">'+lan.public.close+'</button>\
				<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="ReName(1,\'' + fileName.replace(/'/,"\\'") + '\')">'+lan.public.save+'</button>\
				</div>\
			</div>',
		success:function (layers,index){
			$('.layers_close').click(function(){
				layer.close(index);
			});
		}
	});
	setCookie('layers',layers);
	$("#newFileName").focus().keyup(function(e){
		if(e.keyCode == 13) $("#ReNameBtn").click();
	});
}
function CutFile(fileName) {
	var path = $("#DirPathPlace input").val();
	setCookie('cutFileName', fileName);
	setCookie('copyFileName', null);
	layer.msg(lan.files.mv_ok, {icon: 1,time: 1000});
	GetFiles(path);
}
function CopyFile(fileName) {
	var path = $("#DirPathPlace input").val();
	setCookie('copyFileName', fileName);
	setCookie('cutFileName', null);
	layer.msg(lan.files.copy_ok, {icon: 1,time: 1000});
	GetFiles(path);
}
function PasteFile(fileName) {
	var path = $("#DirPathPlace input").val();
	var copyName = getCookie('copyFileName');
	var cutName = getCookie('cutFileName');
	var filename = copyName;
	if(cutName != 'null' && cutName != undefined) filename=cutName;
	filename = filename.split('/').pop();
	$.post('/files?action=CheckExistsFiles',{dfile:path,filename:filename},function(result){
		if(result.length > 0){
			var tbody = '';
			for(var i=0;i<result.length;i++){
				tbody += '<tr><td>'+result[i].filename+'</td><td>'+ToSize(result[i].size)+'</td><td>'+getLocalTime(result[i].mtime)+'</td></tr>';
			}
			var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
						<tbody>'+tbody+'</tbody>\
						</table></div>';
			SafeMessage('即将覆盖以下文件',mbody,function(){
				PasteTo(path,copyName,cutName,fileName);
			});
		}else{
			PasteTo(path,copyName,cutName,fileName);
		}
	});
}


function PasteTo(path,copyName,cutName,fileName){
	if (copyName != 'null' && copyName != undefined) {
		layer.msg(lan.files.copy_the, {
			icon: 16,
			time: 0,shade: [0.3, '#000']
		});
		$.post('/files?action=CopyFile', 'sfile=' + encodeURIComponent(copyName) + '&dfile=' + encodeURIComponent(path +'/'+ fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			GetFiles(path);
		});
		setCookie('copyFileName', null);
		setCookie('cutFileName', null);
		return;
	}
	
	if (cutName != 'null' && cutName != undefined) {
		layer.msg(lan.files.mv_the, {
			icon: 16,
			time: 0,shade: [0.3, '#000']
		});
		$.post('/files?action=MvFile', 'sfile=' + encodeURIComponent(cutName) + '&dfile=' + encodeURIComponent(path + '/'+fileName), function(rdata) {
			layer.closeAll();
			layer.msg(rdata.msg, {
				icon: rdata.status ? 1 : 2
			});
			GetFiles(path);
		});
		setCookie('copyFileName', null);
		setCookie('cutFileName', null);
	}
}
// 压缩文件
function Zip(dirName,submits) {
	var path = $("#DirPathPlace input").val();
	if(submits != undefined){
		if(dirName.indexOf(',') == -1){
			tmp = $("#sfile").val().split('/');
			sfile = encodeURIComponent(tmp[tmp.length-1]);
		}else{
			sfile = encodeURIComponent(dirName);
		}
        dfile = encodeURIComponent($("#dfile").val());
        var z_type = $("select[name='z_type']").val();
        if (!z_type) z_type = 'tar.gz';
		layer.close(getCookie('layers'));
		var layers = layer.msg(lan.files.zip_the, {icon: 16,time: 0,shade: [0.3, '#000']});
		$.post('/files?action=Zip', 'sfile=' + sfile + '&dfile=' + dfile + '&z_type='+z_type+'&path='+encodeURIComponent(path), function(rdata) {
			layer.close(layers);
			if(rdata == null || rdata == undefined){
				layer.msg(lan.files.zip_ok,{icon:1});
				GetFiles(path)
				ReloadFiles();
				return;
			}
			layer.msg(rdata.msg, {icon: rdata.status ? 1 : 2});
            if (rdata.status) {
                task_stat()
                GetFiles(path);
            }
		});
		return
	}
	
	param = dirName;
	if(dirName.indexOf(',') != -1){
		tmp = path.split('/')
		dirName = path + '/' + tmp[tmp.length-1]
	}
	
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '650px',
		title: lan.files.zip_title,
		content: '<div class="bt-form pd20 pb70">'
					+'<div class="line noborder">'
                    + '<input type="text" class="form-control" id="sfile" value="' + param + '" placeholder="" style="display:none" />'
                    + '<p style="margin-bottom: 10px;"><span>压缩类型</span><select style="margin-left: 8px;" class="bt-input-text" name="z_type"><option value="tar.gz">tar.gz (推荐)</option><option value="zip">zip (通用格式)</option><option value="rar">rar (WinRAR对中文兼容较好)</option></select></p>'
					+'<span>'+lan.files.zip_to+'</span><input type="text" class="bt-input-text" id="dfile" value="'+dirName + '.tar.gz" placeholder="'+lan.files.zip_to+'" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" /><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'dfile\')"></span>'
                    + '</div>'
					+'<div class="bt-form-submit-btn">'
					+'<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+lan.public.close+'</button>'
					+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="Zip(\'' + param + '\',1)">'+lan.files.file_menu_zip+'</button>'
					+'</div>'
				+'</div>',
		success:function(layers,index){
			$('.layer_close').click(function(){
				layer.close(index);
			});
		}
	});
	setCookie('layers',layers);
    setTimeout(function (){
		$("select[name='z_type']").change(function(){
            var z_type = $(this).val();
            dirName = dirName.replace("tar.gz", z_type)
            $("#dfile").val(dirName + '.' + z_type);
		});
	},100);
	
}
function UnZip(fileName,type) {
	var path = $("#DirPathPlace input").val();
	if(type.length ==3){
		var sfile = encodeURIComponent($("#sfile").val());
		var dfile = encodeURIComponent($("#dfile").val());
		var password = encodeURIComponent($("#unpass").val());
		coding = $("select[name='coding']").val();
		layer.close(getCookie('layers'));
		layer.msg(lan.files.unzip_the, {icon: 16,time: 0,shade: [0.3, '#000']});
		$.post('/files?action=UnZip', 'sfile=' + sfile + '&dfile=' + dfile +'&type=' + type + '&coding=' + coding + '&password=' + password, function(rdata) {
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            task_stat();
			GetFiles(path);
		});
		return
	}
	
	type = (type == 1) ? 'tar':'zip'
	var umpass = '';
	if(type == 'zip'){
		umpass = '<div class="line"><span class="tname">'+lan.files.zip_pass_title+'</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="'+lan.files.zip_pass_msg+'" style="width:330px" /></div>'
	}
	var layers = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '490px',
		title: lan.files.unzip_title,
		content: '<div class="bt-form pd20 pb70">'
					+'<div class="line unzipdiv">'
					+'<span class="tname">'+lan.files.unzip_name+'</span><input type="text" class="bt-input-text" id="sfile" value="' +fileName + '" placeholder="'+lan.files.unzip_name_title+'" style="width:330px" /></div>'
					+'<div class="line"><span class="tname">'+lan.files.unzip_to+'</span><input type="text" class="bt-input-text" id="dfile" value="'+path + '" placeholder="'+lan.files.unzip_to+'" style="width:330px" /></div>' + umpass
					+'<div class="line"><span class="tname">'+lan.files.unzip_coding+'</span><select class="bt-input-text" name="coding">'
						+'<option value="UTF-8">UTF-8</option>'
						+'<option value="gb18030">GBK</option>'
					+'</select>'
					+'</div>'
					+'<div class="bt-form-submit-btn">'
					+'<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+lan.public.close+'</button>'
					+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="UnZip(\'' + fileName + '\',\''+type+'\')">'+lan.files.file_menu_unzip+'</button>'
					+'</div>'
				+'</div>',
		success:function(layers,index){
			$('.layer_close').click(function(){
				layer.close(index);
			});
		}
	});
	setCookie('layers',layers);
}
function isZip(fileName){
	var ext = fileName.split('.');
	var extName = ext[ext.length-1].toLowerCase();
    if (extName == 'zip' || extName == 'war' || extName == 'rar') return 0;
	if( extName == 'gz' || extName == 'tgz' || extName == 'bz2') return 1;
	return -1;
}
function isText(fileName){
	var exts = ['rar','war','zip','tar.gz','gz','iso','xsl','doc','xdoc','jpeg','jpg','png','gif','bmp','tiff','exe','so','7z','bz','bz2'];
	return isExts(fileName,exts)?false:true;
}
function isImage(fileName){
	var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
	return isExts(fileName,exts);
}
function isVideo(fileName) {
    var exts = ['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'webm', 'mkv'];
    return isExts(fileName, exts);
}
function isExts(fileName,exts){
	var ext = fileName.split('.');
	if(ext.length < 2) return false;
	var extName = ext[ext.length-1].toLowerCase();
	for(var i=0;i<exts.length;i++){
		if(extName == exts[i]) return true;
	}
	return false;
}
function GetImage(fileName){
	var imgUrl = '/download?filename='+fileName;
	layer.open({
		type:1,
		closeBtn: 2,
		title:false,
		area: '500px',
		shadeClose: true,
		content: '<div class="showpicdiv"><img width="100%" src="'+imgUrl+'"></div>'
	});
	$(".layui-layer").css("top", "30%");
}

function GetPlay(fileName) {
    var imgUrl = '/download?filename=' + fileName;
    layer.open({
        type: 1,
        closeBtn: 2,
        title: '播放[' + fileName+']',
        area: '500px',
        shadeClose: false,
        content: '<div class="showpicdiv"><video src="' + imgUrl +'" controls="controls" autoplay="autoplay" width="100%" type="video/mp4">\
                    您的浏览器不支持 video 标签。\
                    </video></div>'
    });
    $(".layui-layer").css("top", "30%");
}
function GetFileBytes(fileName, fileSize){
	window.open('/download?filename='+encodeURIComponent(fileName));
}
function UploadFiles() {

    var path = $("#DirPathPlace input").val() + "/";
    bt_upload_file.open(path, null, null, function (path) {
        GetFiles(path);
    });
    return;

    /*
	layer.open({
		type:1,
		closeBtn: 2,
		title:lan.files.up_title,
		area: ['500px','500px'], 
		shadeClose:false,
		content:'<div class="fileUploadDiv"><input type="hidden" id="input-val" value="'+path+'" />\
				<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
				<button type="button"  id="opt" autocomplete="off">'+lan.files.up_add+'</button>\
				<button type="button" id="up" autocomplete="off" >'+lan.files.up_start+'</button>\
				<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
				<span style="float:right;margin-top: 9px;">\
				<font>'+lan.files.up_coding+':</font>\
				<select id="fileCodeing" >\
					<option value="byte">'+lan.files.up_bin+'</option>\
					<option value="utf-8">UTF-8</option>\
					<option value="gb18030">GB2312</option>\
				</select>\
				</span>\
				<button type="button" id="filesClose" autocomplete="off" onClick="layer.closeAll()" >'+lan.public.close+'</button>\
				<ul id="up_box"></ul></div>'
	});
	UploadStart();*/
}

// 设置权限
function SetChmod(action,fileName){
	if(action == 1){
		var chmod = $("#access").val();
        var chown = $("#chown").val();
        var all = $("#accept_all").prop("checked") ? 'True' : 'False';
		var data = 'filename='+ encodeURIComponent(fileName)+'&user='+chown+'&access='+chmod+'&all=' + all;
		var loadT = layer.msg(lan.public.config,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('files?action=SetFileAccess',data,function(rdata){
			layer.close(loadT);
			if(rdata.status) layer.close(getCookie('layers'));
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			var path = $("#DirPathPlace input").val();
			GetFiles(path)
		});
		return;
	}
	
	var toExec = fileName == lan.files.all?'Batch(3,1)':'SetChmod(1,\''+fileName+'\')';
	
	$.post('/files?action=GetFileAccess','filename='+encodeURIComponent(fileName),function(rdata){
		var layers = layer.open({
			type:1,
			closeBtn: 2,
			title: lan.files.set_auth + '['+fileName+']',
			area: '400px', 
			shadeClose:false,
			content:'<div class="setchmod bt-form ptb15 pb70">\
						<fieldset>\
							<legend>'+lan.files.file_own+'</legend>\
							<p><input type="checkbox" id="owner_r" />'+lan.files.file_read+'</p>\
							<p><input type="checkbox" id="owner_w" />'+lan.files.file_write+'</p>\
							<p><input type="checkbox" id="owner_x" />'+lan.files.file_exec+'</p>\
						</fieldset>\
						<fieldset>\
							<legend>'+lan.files.file_group+'</legend>\
							<p><input type="checkbox" id="group_r" />'+lan.files.file_read+'</p>\
							<p><input type="checkbox" id="group_w" />'+lan.files.file_write+'</p>\
							<p><input type="checkbox" id="group_x" />'+lan.files.file_exec+'</p>\
						</fieldset>\
						<fieldset>\
							<legend>'+lan.files.file_public+'</legend>\
							<p><input type="checkbox" id="public_r" />'+lan.files.file_read+'</p>\
							<p><input type="checkbox" id="public_w" />'+lan.files.file_write+'</p>\
							<p><input type="checkbox" id="public_x" />'+lan.files.file_exec+'</p>\
						</fieldset>\
						<div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="'+rdata.chmod+'">'+lan.files.file_menu_auth+'，\
						<span>'+lan.files.file_own+'\
						<select id="chown" class="bt-input-text">\
							<option value="www" '+(rdata.chown=='www'?'selected="selected"':'')+'>www</option>\
							<option value="mysql" '+(rdata.chown=='mysql'?'selected="selected"':'')+'>mysql</option>\
							<option value="root" '+(rdata.chown=='root'?'selected="selected"':'')+'>root</option>\
						</select></span>\
                        <span><input type="checkbox" id="accept_all" checked /><label for="accept_all" style="position: absolute;margin-top: 4px; margin-left: 5px;font-weight: 400;">应用到子目录</label></span>\
                        </div>\
						<div class="bt-form-submit-btn">\
							<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+lan.public.close+'</button>\
					        <button type="button" class="btn btn-success btn-sm btn-title" onclick="'+toExec+'" >'+lan.public.ok+'</button>\
				        </div>\
					</div>',
			success:function(layers,index){
				$('.layer_close').click(function(){
					layer.close(index);
				})
			}
		});
		setCookie('layers',layers);
		
		onAccess();
		$("#access").keyup(function(){
			onAccess();
		});
		
		$("input[type=checkbox]").change(function(){
			var idName = ['owner','group','public'];
			var onacc = '';
			for(var n=0;n<idName.length;n++){
				var access = 0;
				access += $("#"+idName[n]+"_x").prop('checked')?1:0;
				access += $("#"+idName[n]+"_w").prop('checked')?2:0;
				access += $("#"+idName[n]+"_r").prop('checked')?4:0;
				onacc += access;
			}
			$("#access").val(onacc);
			
		});
	})
	
}

function onAccess(){
	var access = $("#access").val();
	var idName = ['owner','group','public'];				
	for(var n=0;n<idName.length;n++){
		$("#"+idName[n]+"_x").prop('checked',false);
		$("#"+idName[n]+"_w").prop('checked',false);
		$("#"+idName[n]+"_r").prop('checked',false);
	}
	for(var i=0;i<access.length;i++){
		var onacc = access.substr(i,1);
		if(i > idName.length) continue;
		if(onacc > 7) $("#access").val(access.substr(0,access.length-1));
		switch(onacc){
			case '1':
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
			case '2':
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '3':
				$("#"+idName[i]+"_x").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '4':
				$("#"+idName[i]+"_r").prop('checked',true);
				break;
			case '5':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
			case '6':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				break;
			case '7':
				$("#"+idName[i]+"_r").prop('checked',true);
				$("#"+idName[i]+"_w").prop('checked',true);
				$("#"+idName[i]+"_x").prop('checked',true);
				break;
		}
	}
}
function RClick(type, path, name, file_store){
	var displayZip = isZip(type);
	var options = {items:[
	  {text: lan.files.file_menu_copy, 	onclick: function() {CopyFile(path)}},
	  {text: lan.files.file_menu_mv, 	onclick: function() {CutFile(path)}},
	  {text: lan.files.file_menu_rename, 	onclick: function() {ReName(0,name)}},
	  {text: lan.files.file_menu_auth, 	onclick: function() {SetChmod(0,path)}},
	  {text: lan.files.file_menu_zip, onclick: function() {Zip(path)}}
	  
    ]
    };  
    
	if(type == "dir"){
		options.items.push({text: lan.files.file_menu_del, onclick: function() {DeleteDir(path)}});
    }
    //else if (isVideo(type)) {
    //    options.items.push({ text: '播放', onclick: function () { GetPlay(path) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    //}
	else if(isText(type)){
		options.items.push({text: lan.files.file_menu_edit, onclick: function() {openEditorView(0,path)}},{text: lan.files.file_menu_down, onclick: function() {GetFileBytes(path)}},{text: lan.files.file_menu_del, onclick: function() {DeleteFile(path)}});
	}
	else if(displayZip != -1){
		options.items.push({text: lan.files.file_menu_unzip, onclick: function() {UnZip(path,displayZip)}},{text: lan.files.file_menu_down, onclick: function() {GetFileBytes(path)}},{text: lan.files.file_menu_del, onclick: function() {DeleteFile(path)}});
	}
	else if(isImage(type)){
		options.items.push({text: lan.files.file_menu_img, onclick: function() {GetImage(path)}},{text: lan.files.file_menu_down, onclick: function() {GetFileBytes(path)}},{text: lan.files.file_menu_del, onclick: function() {DeleteFile(path)}});
    }
	else{
		options.items.push({text: lan.files.file_menu_down, onclick: function() {GetFileBytes(path)}},{text: lan.files.file_menu_del, onclick: function() {DeleteFile(path)}});
    }

    options.items.push({
        text: "收藏夹", onclick: function () {

            var datas = []
            for (var i = 0; i < file_store.STORE.length; i++) {
                datas.push({ title: file_store.STORE[i].name, value: file_store.STORE[i].name })
            }
            var file_data = {
                title: '加入收藏夹',
                area: '500px',
                list: [
                    { name: 'path', disabled: true, width: '300px', value: path },
                    { name: 'file_type', type: 'select', width: '300px', items: datas }
                ],
                btns: [
                    bt.form.btn.close(),
                    {
                        title: '添加', name: 'submit', css: 'btn-success', callback: function (rdata, load) {
                            var loading = bt.load();
                            bt.send('add_files_store', 'files/add_files_store', rdata, function (rRet) {
                                loading.close();
                                bt.msg(rRet);
                                if (rRet.status) {
                                    load.close();
                                    GetFiles(file_store.PATH)
                                }
                            })
                        }
                    }
                ]
            }
            var bs = bt.render_form(file_data);
            $(".bt-form" + bs).find(".info-r").css("margin-left", "15px")
        }
    })
	return options;
}


function RClickAll(e){
	var menu = $("#rmenu");
	var windowWidth = $(window).width(),
		windowHeight = $(window).height(),
		menuWidth = menu.outerWidth(),
		menuHeight = menu.outerHeight(),
		x = (menuWidth + e.clientX < windowWidth) ? e.clientX : windowWidth - menuWidth,
		y = (menuHeight + e.clientY < windowHeight) ? e.clientY : windowHeight - menuHeight;

	menu.css('top', y)
		.css('left', x)
		.css('position', 'fixed')
		.css("z-index","1")
		.show();
}
function GetPathSize(){
	var path = encodeURIComponent($("#DirPathPlace input").val());
	layer.msg("正在计算，请稍候",{icon:16,time:0,shade: [0.3, '#000']})
	$.post("/files?action=GetDirSize","path="+path,function(rdata){
		layer.closeAll();
		$("#pathSize").text(rdata)
	})
}
$("body").not(".def-log").click(function(){
	$("#rmenu").hide()
});
$("#DirPathPlace input").keyup(function(e){
	if(e.keyCode == 13) {
		GetFiles($(this).val());
	}
});
function PathPlaceBtn(path){
	var html = '';
    var title = '';
    path = path.replace('//', '/');
	var	Dpath = path;
	if(path == '/'){
		html ='<li><a title="/">'+lan.files.path_root+'</a></li>';
	}
	else{
		Dpath = path.split("/");
		for(var i = 0; i<Dpath.length; i++ ){
			title += Dpath[i]+'/';
			Dpath[0] = lan.files.path_root;
			html +='<li><a title="'+title+'">'+Dpath[i]+'</a></li>';
		}
	}
	html = '<div style="width:1200px;height:26px"><ul>'+html+'</ul></div>';
	$("#PathPlaceBtn").html(html);
	$("#PathPlaceBtn ul li a").click(function(e){
		var Gopath = $(this).attr("title");
		if(Gopath.length>1){
			if(Gopath.substr(Gopath.length-1,Gopath.length) =='/'){
				Gopath = Gopath.substr(0,Gopath.length-1);
			}
		}
		GetFiles(Gopath);
		e.stopPropagation();
	});
	PathLeft();
}
function PathLeft(){
	var UlWidth = $("#PathPlaceBtn ul").width();
	var SpanPathWidth = $("#PathPlaceBtn").width() - 50;
	var Ml = UlWidth - SpanPathWidth;
	if(UlWidth > SpanPathWidth ){
		$("#PathPlaceBtn ul").css("left",-Ml)
	}
	else{
		$("#PathPlaceBtn ul").css("left",0)
	}
}

var store_type_index = 0
//删除分类或者文件
function del_files_store(path, obj, parent_name) {
    var _item = $(obj).parents('tr').data('item')
    var action = '', msg = '';
    var data = {}
    if (parent_name != undefined) {
        action = 'del_files_store';
        data['file_type'] = parent_name
        data['path'] = _item.path;
        msg = "是否确定删除路径【" + _item.path + "】?"
    }
    else {
        action = 'del_files_store_types';
        data['file_type'] = _item.name;
        msg = "是否确定删除分类【" + _item.name + "】?"
    }
    bt.confirm({ msg: msg, title: '提示' }, function () {
        var loading = bt.load();
        bt.send(action, 'files/' + action, data, function (rRet) {
            loading.close();
            if (parent_name) {
                store_type_index.close();
            }

            if (rRet.status) {
                set_file_store(path)
                GetFiles(getCookie('Path'))
            }
            bt.msg(rRet);
        })
    })
}

function set_file_store(path) {

    var loading = bt.load();
    bt.send('get_files_store', 'files/get_files_store', {}, function (rRet) {
        loading.close();
        if ($('#stroe_tab_list').length <= 0) {
            bt.open({
                type: 1,
                skin: 'demo-class',
                area: '510px',
                title: "管理收藏夹",
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: "<div class='divtable pd15 style='padding-bottom: 0'><input name='type_name' class='bt-input-text mr5 type_name' placeholder='请填写分类名称' type='text' style='width:420px'/><button id='btn_data_store_add' class='btn btn-success btn-sm' type='button' style='margin-bottom:10px'>添加</button><table width='100%' id='stroe_tab_list' class='table table-hover'></table><div class='page sitebackup_page'></div></div>",
                success: function () {
                    $('#btn_data_store_add').click(function () {
                        bt.send('add_files_store_types', 'files/add_files_store_types', { file_type: $(".type_name").val() }, function (rRet) {
                            loading.close();

                            if (rRet.status) {
                                set_file_store(path)
                                GetFiles(path)
                            }
                            bt.msg(rRet);
                        })
                    })
                    reload_sort_data(path)
                }
            });
        }
        else {
            reload_sort_data(path)
        }

        function reload_sort_data(path) {
            var _tab = bt.render({
                table: '#stroe_tab_list',
                columns: [
                    { field: 'name', title: '分类名称' },
                    {
                        field: 'opt', align: 'right', title: '操作', templet: function (item) {
                            var opt = ' <a class="btlink show_file_store_detail" >查看</a>'
                            if (item.name != '默认分类') {
                                opt += ' | <a class="btlink del_file_store" onclick="del_files_store(\'' + path + '\',this)" >删除</a>';
                            }
                            return opt;
                        }
                    },
                ],
                data: rRet
            });

            $(".show_file_store_detail").click(function () {
                var _item = $(this).parents('tr').data('item')
                store_type_index = bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '710px',
                    title: "管理[" + _item['name'] + ']',
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: "<div class='divtable pd15 style='padding-bottom: 0'><table width='100%' id='stroe_tab_list_detail' class='table table-hover'></table><div class='page sitebackup_page'></div></div>",
                    success: function () {
                        var _tab = bt.render({
                            table: '#stroe_tab_list_detail',
                            columns: [
                                { field: 'path', title: '路径名称' },
                                {
                                    field: 'opt', align: 'right', title: '操作', templet: function (item) {
                                        var opt = ' <a class="btlink del_file_store" onclick="del_files_store(\'' + path + '\',this,\'' + _item['name'] + '\')" >删除</a>'
                                        return opt;
                                    }
                                },
                            ],
                            data: _item.data
                        });
                    }
                });
            })
        }
    })
}



$("#PathPlaceBtn").on("click", function(e){
	if($("#DirPathPlace").is(":hidden")){
		$("#DirPathPlace").css("display","inline");
		$("#DirPathPlace input").focus();
		$(this).hide();
	}else{
		$("#DirPathPlace").hide();
		$(this).css("display","inline");
	}
	$(document).one("click", function(){
		$("#DirPathPlace").hide();
		$("#PathPlaceBtn").css("display","inline");
	});
	e.stopPropagation(); 
}); 
$("#DirPathPlace").on("click", function(e){
	e.stopPropagation();
});

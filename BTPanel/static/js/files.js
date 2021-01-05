var fileDrop = {
    startTime: 0,
    endTime:0,
    uploadLength:0, //上传数量
    splitSize: 1024 * 1024 * 2, //文件上传分片大小
    splitEndTime: 0,
    splitStartTime:0,
    fileSize:0,
    speedLastTime:0,
    filesList:[], // 文件列表数组
    errorLength:0, //上传失败文件数量
    isUpload:true, //上传状态，是否可以上传
    uploadSuspend:[],  //上传暂停参数
    isUploadNumber:800,//限制单次上传数量
    uploadAllSize:0, // 上传文件总大小
    uploadedSize:0, // 已上传文件大小
    updateedSizeLast:0,
    topUploadedSize:0, // 上一次文件上传大小
    uploadExpectTime:0, // 预计上传时间
    initTimer:0, // 初始化计时
    speedInterval:null, //平局速度定时器
    timerSpeed:0, //速度
    isLayuiDrop:false, //是否是小窗口拖拽
    uploading:false,
    is_webkit:(function(){
        if(navigator.userAgent.indexOf('WebKit')>-1) return true;
        return false;
    })(),
    init:function(){
        if($('#mask_layer').length == 0) {
            window.UploadFiles = function(){ fileDrop.dialog_view()};
            $("body").append($('<div class="mask_layer" id="mask_layer" style="position:fixed;top:0;left:0;right:0;bottom:0; background:rgba(255,255,255,0.6);border:3px #ccc dashed;z-index:99999999;display:none;color:#999;font-size:40px;text-align:center;overflow:hidden;"><span style="position: absolute;top: 50%;left: 50%;margin-left: -300px;margin-top: -40px;">上传文件到当前目录下'+ (!this.is_webkit?'<i style="font-size:20px;font-style:normal;display:block;margin-top:15px;color:red;">当前浏览器暂不支持拖动上传，推荐使用Chrome浏览器或WebKit内核的浏览。</i>':'') +'</span></div>'));
            this.event_relation(document.querySelector('#container'),document,document.querySelector('#mask_layer'));
        }
    },
    // 事件关联 (进入，离开，放下)
    event_relation:function(enter,leave,drop){
        var that = this,obj = Object.keys(arguments);
        for(var item in arguments){
            if(typeof arguments[item] == "object" && typeof arguments[item].nodeType != 'undefined'){
                arguments[item] = {
                    el:arguments[item],
                    callback:null
                }
            }
        }
        leave.el.addEventListener("dragleave",(leave.callback != null)?leave.callback:function(e){
            if(e.x == 0 && e.y == 0) $('#mask_layer').hide();
            e.preventDefault();
        },false);
        enter.el.addEventListener("dragenter", (enter.callback != null)?enter.callback:function(e){
            if(e.dataTransfer.items[0].kind == 'string') return false
            $('#mask_layer').show();
            that.isLayuiDrop = false;
            e.preventDefault();
        },false);
        drop.el.addEventListener("dragover",function(e){ e.preventDefault() }, false);
        drop.el.addEventListener("drop",(enter.callback != null)?drop.callback:that.ev_drop, false);
    },
    // 事件触发
    ev_drop:function(e){
        if(!fileDrop.is_webkit){
            $('#mask_layer').hide();
            return false;
        }
        e.preventDefault();
        if(fileDrop.uploading){
        	layer.msg('正在上传文件中，请稍后...');
        	return false;
        }
        var items = e.dataTransfer.items,time,num = 0;
            loadT = layer.msg('正在获取上传文件信息，请稍后...',{icon:16,time:0,shade:.3});
        fileDrop.isUpload = true;
        if(items && items.length && items[0].webkitGetAsEntry != null) {
            if(items[0].kind != 'file') return false;
        }
        if(fileDrop.filesList == null) fileDrop.filesList = []
        for(var i = fileDrop.filesList.length -1; i >= 0 ; i--){
            if(fileDrop.filesList[i].is_upload) fileDrop.filesList.splice(-i,1)
        }
        $('#mask_layer').hide();
        function update_sync(s){
            s.getFilesAndDirectories().then(function(subFilesAndDirs) {
                return iterateFilesAndDirs(subFilesAndDirs, s.path);
            });
        }

        var iterateFilesAndDirs = function(filesAndDirs, path) {
            if(!fileDrop.isUpload) return false
			for (var i = 0; i < filesAndDirs.length; i++) {
				if (typeof(filesAndDirs[i].getFilesAndDirectories) == 'function') {
                    update_sync(filesAndDirs[i])
				} else {
				    if(num > fileDrop.isUploadNumber){
				        fileDrop.isUpload = false;
                        layer.msg(' '+ fileDrop.isUploadNumber +'份，无法上传,请压缩后上传!。',{icon:2,area:'405px'});
                        clearTimeout(time);
                        return false;
                    }
                    fileDrop.filesList.push({
                        file:filesAndDirs[i],
                        path:bt.get_file_path(path +'/'+ filesAndDirs[i].name).replace('//','/'),
                        name:filesAndDirs[i].name.replace('//','/'),
                        icon:GetExtName(filesAndDirs[i].name),
                        size:fileDrop.to_size(filesAndDirs[i].size),
                        upload:0, //上传状态,未上传：0、上传中：1，已上传：2，上传失败：-1
                        is_upload:false
                    });
                    fileDrop.uploadAllSize += filesAndDirs[i].size
                    clearTimeout(time);
                    time = setTimeout(function(){
                        layer.close(loadT);
                        fileDrop.dialog_view();
                    },100);
                    num ++;
				}
			}
		}
		if('getFilesAndDirectories' in e.dataTransfer){
			e.dataTransfer.getFilesAndDirectories().then(function(filesAndDirs) {
			 	return iterateFilesAndDirs(filesAndDirs, '/');
			});
		}
        
    },
    // 上传视图
    dialog_view:function(config){
        var that = this,html = '';
        if(!$('.file_dir_uploads').length > 0){
        	if(that.filesList == null) that.filesList = []
            for(var i =0; i<that.filesList.length; i++){
                var item = that.filesList[i];
               html +='<li><div class="fileItem"><span class="filename" title="文件路径:'+ (item.path + '/' + item.name).replace('//','/') +'&#10;文件类型:'+ item.file.type +'&#10;文件大小:'+ item.size +'"><i class="ico ico-'+ item.icon + '"></i>'+ (item.path + '/' + item.name).replace('//','/') +'</span><span class="filesize">'+ item.size +'</span><span class="fileStatus">'+ that.is_upload_status(item.upload) +'</span></div><div class="fileLoading"></div></li>';
            }
            var is_show = that.filesList.length > 11;
            layer.open({
                type: 1,
                closeBtn: 1,
                maxmin:true,
                area: ['540px','505px'],
                btn:['开始上传','取消上传'],
                title: '上传文件到【'+ bt.get_cookie('Path')  +'】--- 支持断点续传',
                skin:'file_dir_uploads',
                content:'<div style="padding:15px 15px 10px 15px;"><div class="upload_btn_groud"><div class="btn-group"><button type="button" class="btn btn-primary btn-sm upload_file_btn">上传文件</button><button type="button" class="btn btn-primary  btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span class="caret"></span><span class="sr-only">Toggle Dropdown</span></button><ul class="dropdown-menu"><li><a href="#" data-type="file">上传文件</a></li><li><a href="#" data-type="dir">上传目录</a></li></ul></div><div class="file_upload_info" style="display:none;"><span>总进度&nbsp;<i class="uploadProgress"></i>，正在上传&nbsp;<i class="uploadNumber"></i>，</span><span style="display:none">上传失败&nbsp;<i class="uploadError"></i></span><span>上传速度&nbsp;<i class="uploadSpeed">获取中</i>，</span><span>预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span><i></i></div></div><div class="upload_file_body '+ (html==''?'active':'') +'">'+ (html!=''?('<ul class="dropUpLoadFileHead" style="padding-right:'+ (is_show?'15':'0') +'px"><li class="fileTitle"><span class="filename">文件名</span><span class="filesize">文件大小</span><span class="fileStatus">上传状态</span></li></ul><ul class="dropUpLoadFile list-list">'+ html +'</ul>'):'<span>请将需要上传的文件拖到此处'+ (!that.is_webkit?'<i style="display: block;font-style: normal;margin-top: 10px;color: red;font-size: 17px;">当前浏览器暂不支持拖动上传，推荐使用Chrome浏览器或WebKit内核的浏览。</i>':'') +'</span>') +'</div></div>',
                success:function(){
                    $('#mask_layer').hide();
                    $('.file_dir_uploads .layui-layer-max').hide();
                    $('.upload_btn_groud .upload_file_btn').click(function(){$('.upload_btn_groud .dropdown-menu [data-type=file]').click()});
                    $('.upload_btn_groud .dropdown-menu a').click(function(){
                        var type = $(this).attr('data-type');
                        $('<input type="file" multiple="true" autocomplete="off" '+ (type == 'dir'?'webkitdirectory=""':'') +' />').change(function(e){
                            var files = e.target.files,arry = [];
                            for(var i=0;i<files.length;i++){
                                var config = {
                                    file:files[i],
                                    path: bt.get_file_path('/' + files[i].webkitRelativePath).replace('//','/') ,
                                    icon:GetExtName(files[i].name),
                                    name:files[i].name.replace('//','/'),
                                    size:that.to_size(files[i].size),
                                    upload:0, //上传状态,未上传：0、上传中：1，已上传：2，上传失败：-1
                                    is_upload:true
                                }
                                that.filesList.push(config);
                                fileDrop.uploadAllSize += files[i].size
                            }
                            that.dialog_view(that.filesList);
                        }).click();
                    });
                    var el = '';
                    that.event_relation({
                        el:$('.upload_file_body')[0],
                        callback:function(e){
                            if($(this).hasClass('active')){
                                $(this).css('borderColor','#4592f0').find('span').css('color','#4592f0');
                            }
                        }
                    },{
                        el:$('.upload_file_body')[0],
                        callback:function(e){
                            if($(this).hasClass('active')){
                                $(this).removeAttr('style').find('span').removeAttr('style');
                            }
                        }
                    },{
                        el:$('.upload_file_body')[0],
                        callback:function (e) {
                            var active = $('.upload_file_body');
                            if(active.hasClass('active')){
                                active.removeAttr('style').find('span').removeAttr('style');
                            }
                            that.ev_drop(e);
                            that.isLayuiDrop = true;
                        }
                    });
                },
                yes:function(index, layero){
                    if(!that.uploading){
                        if(that.filesList.length == 0){
                            layer.msg('请选择上传文件',{icon:0});
                            return false;
                        }
                        $('.layui-layer-btn0').css({'cursor':'no-drop','background':'#5c9e69'}).attr('data-upload','true').text('上传中');
                        that.upload_file();
                        that.initTimer = new Date();
                        that.uploading = true;
                        //that.get_timer_speed();
                    }
                },
                btn2:function (index, layero){
                    if(that.uploading){
                        layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？',{title:'取消上传文件',icon:0},function(indexs){
                            layer.close(index);
                            layer.close(indexs);
                        });
                        return false;
                    }else{
                        layer.close(index);
                    }
                },
                cancel:function(index, layero){
                    if(that.uploading){
                        layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？',{title:'取消上传文件',icon:0},function(indexs){
                            layer.close(index);
                            layer.close(indexs);
                        });
                        return false;
                    }else{
                        layer.close(index);
                    }
                },
                end:function (){
                    GetFiles(bt.get_cookie('Path'));
                    that.clear_drop_stauts(true);
                },
                min:function(){
                    $('.file_dir_uploads .layui-layer-max').show();
                    $('#layui-layer-shade'+$('.file_dir_uploads').attr('times')).fadeOut();
                },
                restore:function(){
                    $('.file_dir_uploads .layui-layer-max').hide();
                    $('#layui-layer-shade'+$('.file_dir_uploads').attr('times')).fadeIn();
                }
            });
        }else{
            if(config == undefined && !that.isLayuiDrop) return false;
            if(that.isLayuiDrop) config = that.filesList;
            $('.upload_file_body').html('<ul class="dropUpLoadFileHead" style="padding-right:'+ (config.length>11?'15':'0') +'px"><li class="fileTitle"><span class="filename">文件名</span><span class="filesize">文件大小</span><span class="fileStatus">上传状态</span></li></ul><ul class="dropUpLoadFile list-list"></ul>').removeClass('active');
            if(Array.isArray(config)){
                for(var i =0; i<config.length; i++){
                    var item = config[i];
                    html +='<li><div class="fileItem"><span class="filename" title="文件路径:'+ item.path + '/' + item.name +'&#10;文件类型:'+ item.file.type +'&#10;文件大小:'+ item.size +'"><i class="ico ico-'+ item.icon + '"></i>'+ (item.path + '/' + item.name).replace('//','/')  +'</span><span class="filesize">'+ item.size +'</span><span class="fileStatus">'+ that.is_upload_status(item.upload) +'</span></div><div class="fileLoading"></div></li>';
                }
                $('.dropUpLoadFile').append(html);
            }else{
                $('.dropUpLoadFile').append('<li><div class="fileItem"><span class="filename" title="文件路径:'+ (config.path + '/' + config.name).replace('//','/') +'&#10;文件类型:'+ config.type +'&#10;文件大小:'+ config.size +'"><i class="ico ico-'+ config.icon + '"></i>'+ (config.path + '/' + config.name).replace('//','/') +'</span><span class="filesize">'+ config.size +'</span><span class="fileStatus">'+ that.is_upload_status(config.upload) +'</span></div><div class="fileLoading"></div></li>');
            }

        }
    },
    // 上传单文件状态
    is_upload_status:function(status,val){
        if(val === undefined) val = ''
        switch(status){
            case -1:
                return '<span class="upload_info upload_error" title="上传失败'+ (val != ''?','+val:'') +'">上传失败'+ (val != ''?','+val:'') +'</span>';
            break;                    
            case 0:
                return '<span class="upload_info upload_primary">等待上传</span>';
            break;   
            case 1:
                return '<span class="upload_info upload_success">上传成功</span>';
            break;
            case 2:
                return '<span class="upload_info upload_warning">上传中'+ val+'</span>';
            break;
            case 3:
                return '<span class="upload_info upload_success">已暂停</span>';
            break;
        }
    },
    // 设置上传实时反馈视图
    set_upload_view:function(index,config){
        var item = $('.dropUpLoadFile li:eq('+ index +')'),that = this;
        var file_info = $('.file_upload_info');
        if($('.file_upload_info .uploadProgress').length == 0){
        	$('.file_upload_info').html('<span>总进度&nbsp;<i class="uploadProgress"></i>，正在上传&nbsp;<i class="uploadNumber"></i>，</span><span style="display:none">上传失败&nbsp;<i class="uploadError"></i></span><span>上传速度&nbsp;<i class="uploadSpeed">获取中</i>，</span><span>预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span><i></i>');
        }
        file_info.show().prev().hide().parent().css('paddingRight',0);
        if(that.errorLength > 0) file_info.find('.uploadError').text('('+ that.errorLength +'份)').parent().show();
        file_info.find('.uploadNumber').html('('+ that.uploadLength +'/'+ that.filesList.length +')');
        file_info.find('.uploadProgress').html( ((that.uploadedSize / that.uploadAllSize) * 100).toFixed(2) +'%');
        if(config.upload === 1 || config.upload === -1){
            that.filesList[index].is_upload = true;
            that.uploadLength += 1;
            item.find('.fileLoading').css({'width':'100%','opacity':'.5','background': config.upload == -1?'#ffadad':'#20a53a21'});
            item.find('.filesize').text(config.size);
            item.find('.fileStatus').html(that.is_upload_status(config.upload,(config.upload === 1?('(耗时:'+ that.diff_time(that.startTime,that.endTime) +')'):config.errorMsg)));
            item.find('.fileLoading').fadeOut(500,function(){
                $(this).remove();
                var uploadHeight = $('.dropUpLoadFile');
                if(uploadHeight.length == 0) return false;
                if(uploadHeight[0].scrollHeight > uploadHeight.height()){
                    uploadHeight.scrollTop(uploadHeight.scrollTop()+40);
                }
            });
        }else{
            item.find('.fileLoading').css('width',config.percent);
            item.find('.filesize').text(config.upload_size +'/'+ config.size);
            item.find('.fileStatus').html(that.is_upload_status(config.upload,'('+ config.percent +')'));
        }
    },
    // 清除上传状态
    clear_drop_stauts:function(status){
        var time = new Date(),that = this;
        if(!status){
        	try {
                var s_peed  = fileDrop.to_size(fileDrop.uploadedSize / ((time.getTime() - fileDrop.initTimer.getTime()) / 1000))
	        	$('.file_upload_info').html('<span>上传成功 '+ this.uploadLength +'个文件，'+ (this.errorLength>0?('上传失败 '+ this.errorLength +'个文件，'):'') +'耗时'+ this.diff_time(this.initTimer,time) + '，平均速度 '+ s_peed +'/s</span>').append($('<i class="ico-tips-close"></i>').click(function(){
	                $('.file_upload_info').hide().prev().show();
	            }));
        	} catch (e) {
        		
        	}
        }
        $('.layui-layer-btn0').removeAttr('style data-upload').text('开始上传');
        $.extend(fileDrop,{
            startTime: 0,
            endTime:0,
            uploadLength:0, //上传数量
            splitSize: 1024 * 1024 * 2, //文件上传分片大小
            filesList:[], // 文件列表数组
            errorLength:0, //上传失败文件数量
            isUpload:false, //上传状态，是否可以上传
            isUploadNumber:800,//限制单次上传数量
            uploadAllSize:0, // 上传文件总大小
            uploadedSize:0, // 已上传文件大小
            topUploadedSize:0, // 上一次文件上传大小
            uploadExpectTime:0, // 预计上传时间
            initTimer:0, // 初始化计时
            speedInterval:null, //平局速度定时器
            timerSpeed:0, //速度
            uploading:false
        });
        clearInterval(that.speedInterval);
    },
    // 上传文件,文件开始字段，文件编号
    upload_file:function(fileStart,index){
        
        if(fileStart == undefined && this.uploadSuspend.length == 0) fileStart = 0,index = 0;
        if(this.filesList.length === index){
            clearInterval(this.speedInterval);
            this.clear_drop_stauts();
            GetFiles(bt.get_cookie('Path'));
            return false;
        }
        var that = this;
        that.splitEndTime = new Date().getTime()
        that.get_timer_speed()

        that.splitStartTime = new Date().getTime()
        var item = this.filesList[index],fileEnd = '';
        if(item == undefined) return false;
        fileEnd = Math.min(item.file.size, fileStart + this.splitSize),
        that.fileSize = fileEnd - fileStart
        form = new FormData();
        if(fileStart == 0){
            that.startTime = new Date();
            item = $.extend(item,{percent:'0%',upload:2,upload_size:'0B'});
        }
        form.append("f_path", bt.get_cookie('Path') + item.path);
        form.append("f_name", item.name);
        form.append("f_size", item.file.size);
        form.append("f_start", fileStart);
        form.append("blob", item.file.slice(fileStart, fileEnd));
        that.set_upload_view(index,item);
        $.ajax({
            url:'/files?action=upload',
            type: "POST",
            data: form,
            async: true,
            processData: false,
            contentType: false,
            success:function(data){
                if(typeof(data) === "number"){
                    that.set_upload_view(index,$.extend(item,{percent:(((data / item.file.size)* 100).toFixed(2)  +'%'),upload:2,upload_size:that.to_size(data)}));
                    if(fileEnd != data){
                        that.uploadedSize += data;
                    }else{
                        that.uploadedSize += parseInt(fileEnd - fileStart);  
                    }

                    that.upload_file(data,index);
                }else{
                    if(data.status){
                        that.endTime = new Date();
                        that.uploadedSize += parseInt(fileEnd - fileStart);
                        that.set_upload_view(index,$.extend(item,{upload:1,upload_size:item.size}));
                        that.upload_file(0,index += 1);
                    }else{
                        that.set_upload_view(index,$.extend(item,{upload:-1,errorMsg:data.msg}));
                        that.errorLength ++;
                    }
                }
                
            },
            error:function(e){
                if(that.filesList[index].req_error === undefined) that.filesList[index].req_error = 1
                if(that.filesList[index].req_error > 2){
                    that.set_upload_view(index,$.extend(that.filesList[index],{upload:-1,errorMsg:e.statusText == 'error'?'网络中断':e.statusText }));
                    that.errorLength ++;
                    that.upload_file(fileStart,index += 1)
                    return false;
                }
                that.filesList[index].req_error += 1;
                that.upload_file(fileStart,index)

                
            }
        });
    }, 
    // 获取上传速度
    get_timer_speed:function(speed){
        var done_time = new Date().getTime()
        if(done_time - this.speedLastTime > 1000){
            var that = this,num = 0;
            if(speed == undefined) speed = 200
            var s_time = (that.splitEndTime - that.splitStartTime) / 1000;
            that.timerSpeed = (that.fileSize / s_time).toFixed(2)
            that.updateedSizeLast = that.uploadedSize
            if(that.timerSpeed < 2) return;

            $('.file_upload_info .uploadSpeed').text(that.to_size(isNaN(that.timerSpeed)?0:that.timerSpeed)+'/s');
            var estimateTime = that.time(parseInt(((that.uploadAllSize - that.uploadedSize) / that.timerSpeed) * 1000))
            if(!isNaN(that.timerSpeed)) $('.file_upload_info .uploadEstimate').text(estimateTime.indexOf('NaN') == -1?estimateTime:'0秒');
            this.speedLastTime = done_time;
        }
    },
    time:function(date){
        var hours = Math.floor(date / (60 * 60 * 1000));
        var minutes = Math.floor(date / (60 * 1000));
        var seconds = parseInt((date % (60 * 1000)) / 1000);
        var result = seconds + '秒';
        if(minutes > 0) {
            result = minutes + "分钟" + seconds  + '秒';
        }
        if(hours > 0){
            result = hours + '小时' + Math.floor((date - (hours * (60 * 60 * 1000))) / (60 * 1000))  + "分钟";
        }
        return result
    },
    diff_time: function (start_date, end_date) {
        var diff = end_date.getTime() - start_date.getTime();
        var minutes = Math.floor(diff / (60 * 1000));
        var leave3 = diff % (60 * 1000);
        var seconds = leave3 / 1000
        var result = seconds.toFixed(minutes > 0?0:2) + '秒';
        if (minutes > 0) {
            result = minutes + "分" + seconds.toFixed(0) + '秒'
        }
        return result
    },
    
    to_size: function (a) {
        var d = [" B", " KB", " MB", " GB", " TB", " PB"];
        var e = 1024;
        for (var b = 0; b < d.length; b += 1) {
            if (a < e) {
                var num = (b === 0 ? a : a.toFixed(2)) + d[b];
                return (!isNaN((b === 0 ? a : a.toFixed(2))) && typeof num != 'undefined')?num:'0B';
            }
            a /= e
        }
    }
}
function IsDiskWidth() {
    var comlistWidth = $("#comlist").width();
    var bodyWidth = $(".file-box").width();
    if (comlistWidth + 530 > bodyWidth) {
        $("#comlist").css({ "width": bodyWidth - 530 + "px", "height": "34px", "overflow": "auto" });
    }
    else {
        $("#comlist").removeAttr("style"); 
    } 
}
function Recycle_bin(type) {
    $.post('/files?action=Get_Recycle_bin','',function (rdata) {
        var body = '';
        switch (type) {
            case 1:
                for (var i = 0; i < rdata.dirs.length; i++) {
                    var shortwebname = rdata.dirs[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.dirs[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+ rdata.dirs[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.dirs[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.dirs[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.dirs[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>';
                }
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname.replace('BTDB_', '') + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">mysql://' + shortpath.replace('BTDB_', '') + '</span></td>\
								<td>-</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'

                        continue;
                    }
                    var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.files[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.files[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 2:
                for (var i = 0; i < rdata.dirs.length; i++) {
                    var shortwebname = rdata.dirs[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.dirs[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class=\'ico ico-folder\'></span><span class="tname" title="'+ rdata.dirs[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.dirs[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.dirs[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.dirs[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.dirs[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 3:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) continue;
                    var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                    var shortpath = rdata.files[i].dname;
                    if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                    if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                    body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.files[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 4:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (ReisImage(getFileName(rdata.files[i].name))) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.files[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                    }
                }
                $("#RecycleBody").html(body);
                return;
                break;
            case 5:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) continue;
                    if (!(ReisImage(getFileName(rdata.files[i].name)))) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">' + shortpath + '</span></td>\
								<td>'+ ToSize(rdata.files[i].size) + '</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
								</td>\
							</tr>'
                    }
                }
                $("#RecycleBody").html(body);
                return;
            case 6:
                for (var i = 0; i < rdata.files.length; i++) {
                    if (rdata.files[i].name.indexOf('BTDB_') != -1) {
                        var shortwebname = rdata.files[i].name.replace(/'/, "\\'");
                        var shortpath = rdata.files[i].dname;
                        if (shortwebname.length > 20) shortwebname = shortwebname.substring(0, 20) + "...";
                        if (shortpath.length > 20) shortpath = shortpath.substring(0, 20) + "...";
                        body += '<tr>\
								<td><span class="ico ico-'+ (GetExtName(rdata.files[i].name)) + '"></span><span class="tname" title="' + rdata.files[i].name + '">' + shortwebname.replace('BTDB_', '') + '</span></td>\
								<td><span title="'+ rdata.files[i].dname + '">mysql://' + shortpath.replace('BTDB_', '') + '</span></td>\
								<td>-</td>\
								<td>'+ getLocalTime(rdata.files[i].time) + '</td>\
								<td style="text-align: right;">\
									<a class="btlink" href="javascript:;" onclick="ReRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_re + '</a>\
									 | <a class="btlink" href="javascript:;" onclick="DelRecycleBin(\'' + rdata.files[i].rname.replace(/'/, "\\'") + '\',this)">' + lan.files.recycle_bin_del + '</a>\
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
                        <em>'+ lan.files.recycle_bin_on + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox" '+ (rdata.status ? 'checked' : '') + '>\
                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="Set_Recycle_bin()"></label>\
                        </div>\
                        <em style="margin-left: 20px;">'+ lan.files.recycle_bin_on_db + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox" '+ (rdata.status_db ? 'checked' : '') + '>\
                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="Set_Recycle_bin(1)"></label>\
                        </div>\
                </div>\
				<span style="line-height: 32px; margin-left: 30px;">'+ lan.files.recycle_bin_ps + '</span>\
                <button style="float: right" class="btn btn-default btn-sm" onclick="CloseRecycleBin();">'+ lan.files.recycle_bin_close + '</button>\
				</div>\
				<div class="re-con">\
					<div class="re-con-menu">\
						<p class="on" onclick="Recycle_bin(1)">'+ lan.files.recycle_bin_type1 + '</p>\
						<p onclick="Recycle_bin(2)">'+ lan.files.recycle_bin_type2 + '</p>\
						<p onclick="Recycle_bin(3)">'+ lan.files.recycle_bin_type3 + '</p>\
						<p onclick="Recycle_bin(4)">'+ lan.files.recycle_bin_type4 + '</p>\
						<p onclick="Recycle_bin(5)">'+ lan.files.recycle_bin_type5 + '</p>\
						<p onclick="Recycle_bin(6)">'+ lan.files.recycle_bin_type6 + '</p>\
					</div>\
					<div class="re-con-con">\
					<div style="margin: 15px;" class="divtable">\
					<table width="100%" class="table table-hover">\
						<thead>\
							<tr>\
								<th>'+ lan.files.recycle_bin_th1 + '</th>\
								<th>'+ lan.files.recycle_bin_th2 + '</th>\
								<th>'+ lan.files.recycle_bin_th3 + '</th>\
								<th width="150">'+ lan.files.recycle_bin_th4 + '</th>\
								<th style="text-align: right;" width="110">'+ lan.files.recycle_bin_th5 + '</th>\
							</tr>\
						</thead>\
					<tbody id="RecycleBody" class="list-list">'+ body + '</tbody>\
			</table></div></div></div>';
        if (type == "open") {
            layer.open({
                type: 1,
                shift: 5,
                closeBtn: 2,
                area: ['80%', '606px'],
                title: lan.files.recycle_bin_title,
                content: tablehtml
            });

            if (window.location.href.indexOf("database") != -1) {
                Recycle_bin(6);
                $(".re-con-menu p:last-child").addClass("on").siblings().removeClass("on");
            } else {
                Recycle_bin(1);
            }
        }
        $(".re-con-menu p").click(function () {
            $(this).addClass("on").siblings().removeClass("on");
        })
    });
}
function getFileName(name) {
    var text = name.split(".");
    var n = text.length - 1;
    text = text[n];
    return text;
}
function ReisImage(fileName) {
    var exts = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico'];
    for (var i = 0; i < exts.length; i++) {
        if (fileName == exts[i]) return true
    }
    return false;
}
function ReRecycleBin(path, obj) {
    layer.confirm(lan.files.recycle_bin_re_msg, { title: lan.files.recycle_bin_re_title, closeBtn: 2, icon: 3 }, function () {
        var loadT = layer.msg(lan.files.recycle_bin_re_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=Re_Recycle_bin', 'path=' + encodeURIComponent(path), function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            $(obj).parents('tr').remove();
        });
    });
}
function DelRecycleBin(path, obj) {
    layer.confirm(lan.files.recycle_bin_del_msg, { title: lan.files.recycle_bin_del_title, closeBtn: 2, icon: 3 }, function () {
        var loadT = layer.msg(lan.files.recycle_bin_del_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=Del_Recycle_bin', 'path=' + encodeURIComponent(path), function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            $(obj).parents('tr').remove();
        });
    });
}
function CloseRecycleBin() {
    layer.confirm(lan.files.recycle_bin_close_msg, { title: lan.files.recycle_bin_close, closeBtn: 2, icon: 3 }, function () {
        var loadT = layer.msg("<div class='myspeed'>" + lan.files.recycle_bin_close_the + "</div>", { icon: 16, time: 0, shade: [0.3, '#000'] });
        setTimeout(function () {
            getSpeed('.myspeed');
        }, 1000);
        $.post('/files?action=Close_Recycle_bin', '', function (rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            $("#RecycleBody").html('');
        });
    });
}
function Set_Recycle_bin(db) {
    var loadT = layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
    var data = {}
    if (db == 1) {
        data = { db: db };
    }
    $.post('/files?action=Recycle_bin', data, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
    });
}
function get_path_size(path) {
    var loadT = layer.msg('正在计算目录大小,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/files?action=get_path_size', { path: path }, function (rdata) {
        layer.close(loadT);
        var myclass = '.' + rdata.path.replace(/[^\w]/g, '-');
        $(myclass).text(ToSize(rdata.size));
    });
}
function path_check(path) {
    if (path == '/') return path;
    path = path.replace(/[\/]{2,}/g, '/');
    path = path.replace(/[\/]+$/g, '');
    return path;
}

function GetFiles(Path, sort) {
    var searchtype = Path;
    var p = '1';
    if (!isNaN(Path)) {
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

    var old_scroll_top = 0;
    if (getCookie('Path') === Path) {
        old_scroll_top = $(".oldTable").scrollTop();
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
    if (!showRow) showRow = '200';
    var Body = '';
    data['path'] = Path;


    if (searchV) {
        var loadT = layer.msg('正在搜索,请稍候...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    }
    var totalSize = 0;
    $.post('/files?action=GetDir&tojs=GetFiles&p=' + p + '&showRow=' + showRow + search, data, function (rdata) {
        if (searchV) layer.close(loadT);
        if (rdata.status === false) {
            layer.msg(rdata.msg, { icon: 2 });
            return;
        }

        var rows = ['10', '50', '100', '200', '500', '1000', '2000'];
        var rowOption = '';
        for (var i = 0; i < rows.length; i++) {
            var rowSelected = '';
            if (showRow == rows[i]) rowSelected = 'selected';
            rowOption += '<option value="' + rows[i] + '" ' + rowSelected + '>' + rows[i] + '</option>';
        }

        $("#filePage").html(rdata.PAGE);
        $("#filePage div").append("<span class='Pcount-item'>每页<select style='margin-left: 3px;margin-right: 3px;border:#ddd 1px solid' class='showRow'>" + rowOption + "</select>条</span>");
        $("#filePage .Pcount").css("left", "16px");
        if (rdata.DIR == null) rdata.DIR = [];
        for (var i = 0; i < rdata.DIR.length; i++) {
            var fmp = rdata.DIR[i].split(";");
            var cnametext = fmp[0] + fmp[5];
            fmp[0] = fmp[0].replace(/'/, "\\'");
            if (cnametext.length > 20) {
                cnametext = cnametext.substring(0, 20) + '...'
            }
            if (isChineseChar(cnametext)) {
                if (cnametext.length > 10) {
                    cnametext = cnametext.substring(0, 10) + '...'
                }
            }
            var fileMsg = '';
            if (fmp[0].indexOf('Recycle_bin') != -1) {
                fileMsg = 'PS: 回收站目录,勿动!';
            }
            if (fileMsg == ''){
                fileMsg = fmp[8];
            }
            if (fileMsg != '') {
                fileMsg = '<span style="margin-left: 30px; color: #999;">' + fileMsg + '</span>';
            }
            var timetext = '--';
            if (getCookie("rank") == "a") {
                $("#set_list").addClass("active");
                $("#set_icon").removeClass("active");
                Body += "<tr class='folderBoxTr' fileshare='"+ fmp[6] +"' data-composer='"+fmp[7]+"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir' data-ps='"+fmp[8]+"'>\
						<td><input type='checkbox' name='id' value='"+ fmp[0] + "'></td>\
						<td class='column-name'><span class='cursor' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='ico ico-folder'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + fileMsg + "</a></span></td>\
						<td><a class='btlink "+ (rdata.PATH + '/' + fmp[0]).replace(/[^\w]/g, '-') + "' onclick=\"get_path_size('" + rdata.PATH + "/" + fmp[0] + "')\">点击计算</a></td>\
						<td>"+ getLocalTime(fmp[2]) + "</td>\
						<td>"+ fmp[3] + "</td>\
						<td>"+ fmp[4] + "</td>\
						<td class='editmenu'><span>\
						<a class='btlink' href='javascript:;' onclick=\"webshell_dir('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.dir_menu_webshell + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_copy + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_mv + "</a> | \
						<a class='btlink' href=\"javascript:ReName(0,'" + fmp[0] + "');\">" + lan.files.file_menu_rename + "</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_auth + "</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_zip + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"DeleteDir('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_del + "</a></span>\
					</td></tr>";
            }
            else {
                $("#set_icon").addClass("active");
                $("#set_list").removeClass("active");
                Body += "<div class='file folderBox menufolder' fileshare='"+ fmp[6] +"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='dir' title='" + lan.files.file_name + "：" + fmp[0] + "&#13;" + lan.files.file_size + "：" + ToSize(fmp[1]) + "&#13;" + lan.files.file_etime + "：" + getLocalTime(fmp[2]) + "&#13;" + lan.files.file_auth + "：" + fmp[3] + "&#13;" + lan.files.file_own + "：" + fmp[4] + "'>\
						<input type='checkbox' name='id' value='"+ fmp[0] + "'>\
						<div class='ico ico-folder' ondblclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"></div>\
						<div class='titleBox' onclick=\"GetFiles('" + rdata.PATH + "/" + fmp[0] + "')\"><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
            }
        }
        for (var i = 0; i < rdata.FILES.length; i++) {
            if (rdata.FILES[i] == null) continue;
            var fmp = rdata.FILES[i].split(";");
            var displayZip = isZip(fmp[0]),bodyZip = '',download = '',image_view = '',file_webshell = '';
            var cnametext = fmp[0] + fmp[5];
            fmp[0] = fmp[0].replace(/'/, "\\'");
            if (cnametext.length > 48) {
                cnametext = cnametext.substring(0, 48) + '...'
            }
            if (isChineseChar(cnametext)) {
                if (cnametext.length > 16) {
                    cnametext = cnametext.substring(0, 16) + '...'
                }
            }
            if(isPhp(fmp[0])){
            	file_webshell = "<a class='btlink' href='javascript:;' onclick=\"php_file_webshell('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_webshell + "</a> | ";
            }
            if (displayZip != -1) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"UnZip('" + rdata.PATH + "/" + fmp[0] + "'," + displayZip + ")\">" + lan.files.file_menu_unzip + "</a> | ";
            }
            if (isText(fmp[0])) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"openEditorView(0,'" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_edit + "</a> | ";
            }

            if (isVideo(fmp[0])) {
                bodyZip = "<a class='btlink' href='javascript:;' onclick=\"GetPlay('" + rdata.PATH + "/" + fmp[0] + "')\">播放</a> | ";
            }

            if (isImage(fmp[0])) {
                image_view = "<a class='btlink' href='javascript:;' onclick=\"GetImage({path:'" + rdata.PATH + "/" + fmp[0] + "',filename:'"+ fmp[0] +"'})\">" + lan.files.file_menu_img + "</a> | ";
            }
            download = "<a class='btlink' href='javascript:;' onclick=\"GetFileBytes('" + rdata.PATH + "/" + fmp[0] + "'," + fmp[1] + ")\">" + lan.files.file_menu_down + "</a> | ";
            

            totalSize += parseInt(fmp[1]);
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

                if (fileMsg == ''){
                    fileMsg = fmp[8];
                }

                if (fileMsg != '') {
                    fileMsg = '<span style="margin-left: 30px; color: #999;">' + fileMsg + '</span>';
                }
                Body += "<tr class='folderBoxTr' fileshare='"+ fmp[6] +"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='" + fmp[0] + "' data-ps='"+fmp[8]+"'><td><input type='checkbox' name='id' value='" + fmp[0] + "'></td>\
						<td class='column-name'><span class='ico ico-"+ (GetExtName(fmp[0])) + "'></span><a class='text' title='" + fmp[0] + fmp[5] + "'>" + cnametext + fileMsg + "</a></td>\
						<td>" + (ToSize(fmp[1])) + "</td>\
						<td>" + ((fmp[2].length > 11) ? fmp[2] : getLocalTime(fmp[2])) + "</td>\
						<td>"+ fmp[3] + "</td>\
						<td>"+ fmp[4] + "</td>\
						<td class='editmenu'>\
						<span>"+file_webshell+"<a class='btlink' href='javascript:;' onclick=\"CopyFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_copy + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"CutFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_mv + "</a> | \
						<a class='btlink' href='javascript:;' onclick=\"ReName(0,'" + fmp[0] + "')\">" + lan.files.file_menu_rename + "</a> | \
						<a class='btlink' href=\"javascript:SetChmod(0,'" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_auth + "</a> | \
						<a class='btlink' href=\"javascript:Zip('" + rdata.PATH + "/" + fmp[0] + "');\">" + lan.files.file_menu_zip + "</a> | \
						"+ bodyZip + image_view + download + "\
						<a class='btlink' href='javascript:;' onclick=\"DeleteFile('" + rdata.PATH + "/" + fmp[0] + "')\">" + lan.files.file_menu_del + "</a>\
						</span></td></tr>";
            }
            else {
                Body += "<div class='file folderBox menufile' fileshare='"+ fmp[6] +"' data-path='" + rdata.PATH + "/" + fmp[0] + "' filetype='" + fmp[0] + "' title='" + lan.files.file_name + "：" + fmp[0] + "&#13;" + lan.files.file_size + "：" + ToSize(fmp[1]) + "&#13;" + lan.files.file_etime + "：" + getLocalTime(fmp[2]) + "&#13;" + lan.files.file_auth + "：" + fmp[3] + "&#13;" + lan.files.file_own + "：" + fmp[4] + "'>\
						<input type='checkbox' name='id' value='"+ fmp[0] + "'>\
						<div class='ico ico-"+ (GetExtName(fmp[0])) + "'></div>\
						<div class='titleBox'><span class='tname'>" + fmp[0] + "</span></div>\
						</div>";
            }
        }
        var dirInfo = '(' + lan.files.get_size.replace('{1}', rdata.DIR.length + '').replace('{2}', rdata.FILES.length + '') + '<font id="pathSize"><a class="btlink ml5" onClick="GetPathSize()">' + lan.files.get + '</a></font>)';
        $("#DirInfo").html(dirInfo);
        if (getCookie("rank") === "a") {
            var sort_icon = '<span data-id="status" class="glyphicon glyphicon-triangle-' + ((data['reverse'] !== 'False') ? 'bottom' : 'top') + '" style="margin-left:5px;color:#bbb"></span>';
            var tablehtml = '<div class="newTable"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="table table-hover">\
                              <thead>\
                                  <tr>\
                                      <th width="30"><input type="checkbox" id="setBox" placeholder=""></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') + '</a></th>\
                                      <th><a style="cursor: pointer;" onclick="GetFiles('+ p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') + '</a></th>\
                                      <th style="text-align: right;" width="330">'+ lan.files.file_act + '</th>\
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
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'name\')">' + lan.files.file_name + ((data['sort'] === 'name' || !data['sort']) ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'size\')">' + lan.files.file_size + ((data['sort'] === 'size') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'mtime\')">' + lan.files.file_etime + ((data['sort'] === 'mtime') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'accept\')">' + lan.files.file_auth + ((data['sort'] === 'accept') ? sort_icon : '') + '</a></th>\
									<th><a style="cursor: pointer;" class="btlink" onclick="GetFiles('+ p + ',\'user\')">' + lan.files.file_own + ((data['sort'] === 'user') ? sort_icon : '') + '</a></th>\
									<th style="text-align: right;" width="330">'+ lan.files.file_act + '</th>\
								</tr>\
							</thead>\
							<tbody id="filesBody" class="list-list">'+ Body + '</tbody>\
						</table></div><div class="oldTableShadow"></div>';
            $("#fileCon").removeClass("fileList").html(tablehtml);
            $("#tipTools").width($("#fileCon")[0].clientWidth - 30);
        }
        else {
            $("#fileCon").addClass("fileList").html(Body);
            $("#tipTools").width($("#fileCon")[0].clientWidth - 30);
        }
        $("#DirPathPlace input").val(rdata.PATH);
        fileDrop.init();
        var BarTools = '<div class="btn-group">\
						<button class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\
						'+ lan.files.new + ' <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">\
						<li><a href="javascript:CreateFile(0,\'' + Path + '\');">' + lan.files.new_empty_file + '</a></li>\
						<li><a href="javascript:CreateDir(0,\'' + Path + '\');">' + lan.files.new_dir + '</a></li>\
						</ul>\
						</div>';
        if (rdata.PATH != '/') {
            BarTools += ' <button onclick="javascript:BackDir();" class="btn btn-default btn-sm glyphicon glyphicon-arrow-left" title="' + lan.files.return + '"></button>';
        }
        setCookie('Path', rdata.PATH);
        BarTools += ' <button onclick="javascript:GetFiles(\'' + rdata.PATH + '\');" class="btn btn-default btn-sm glyphicon glyphicon-refresh" title="' + lan.public.fresh + '"></button> <button onclick="web_shell()" title="' + lan.files.shell + '" type="button" class="btn btn-default btn-sm"><em class="ico-cmd"></em></button><button onclick="get_download_url_list()" type="button" class="btn btn-default btn-sm ml5">分享列表</button>';

        // 收藏夹
        var shtml = '<div class="btn-group">\
						<button style="margin-left: 5px;" class="btn btn-default btn-sm dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">收藏夹 <span class="caret"></span>\
						</button>\
						<ul class="dropdown-menu">'

        for (var i = 0; i < rdata.STORE.length; i++) {
            shtml += '<li class="file-types" title="'+ rdata.STORE[i].path +'"><div style="width:200px"><span class="ico '+ (rdata.STORE[i].type ==='file'?'ico-file':'ico-folder') +'"></span><a href="javascript:;"  style="display: inline-block;width:150px;overflow: hidden;text-overflow: ellipsis;vertical-align: top;" onclick="'+ (rdata.STORE[i].type ==='file'?'openEditorView(0,\''+ rdata.STORE[i].path +'\')':'GetFiles(\''+ rdata.STORE[i].path +'\')') +'">' + rdata.STORE[i].name + '</a></div>';
        }
        shtml += '<li style="text-align: center;"><a href="javascript: ;" onclick="set_file_store(\'' + rdata.PATH + '\')">管理收藏夹</a></li></ul></div>'

        BarTools += shtml;
        
        var copyName = getCookie('copyFileName');
        var cutName = getCookie('cutFileName');
        var isPaste = (copyName == 'null') ? cutName : copyName;
        if (isPaste != 'null' && isPaste != undefined) {
            BarTools += ' <button onclick="javascript:PasteFile(\'' + (GetFileName(isPaste)) + '\');" class="btn btn-default btn-Warning btn-sm">' + lan.files.paste + '</button>';
        }

        $("#Batch").html('');
        var BatchTools = '';
        var isBatch = getCookie('BatchSelected');
        if (isBatch == 1 || isBatch == '1') {
            BatchTools += ' <button onclick="javascript:BatchPaste();" class="btn btn-default btn-sm">' + lan.files.paste_all + '</button>';
        }

        
        $("#Batch").html(BatchTools);
        $("#setBox").prop("checked", false);

        $("#BarTools").html(BarTools);
        $(".oldTable").scrollTop(old_scroll_top);
        $("input[name=id]").click(function () {
            if ($(this).prop("checked")) {
                $(this).prop("checked", true);
                $(this).parents("tr").addClass("ui-selected");
            }
            else {
                $(this).prop("checked", false);
                $(this).parents("tr").removeClass("ui-selected");
            }
            showSeclect()
        });

        $("#setBox").click(function () {
            if ($(this).prop("checked")) {
                $("input[name=id]").prop("checked", true);
                $("#filesBody > tr").addClass("ui-selected");

            } else {
                $("input[name=id]").prop("checked", false);
                $("#filesBody > tr").removeClass("ui-selected");
            }
            showSeclect();
        });

        $("#filesBody .btlink").click(function (e) {
            e.stopPropagation();
        });
        $("input[name=id]").dblclick(function (e) {
            e.stopPropagation();
        });
        $("#filesBody").bind("contextmenu", function (e) {
            return false;
        });
        bindselect();
        $("#filesBody").mousedown(function (e) {
            var count = totalFile();
            if (e.which == 3) {
                if (count > 1) {
                    RClickAll(e);
                }
                else {
                    return
                }
            }
        });
        $(".folderBox,.folderBoxTr").mousedown(function (e) {
            var count = totalFile();
            if (e.which == 3) {
                if (count <= 1) {
                    var a = $(this);
                    a.contextify(RClick(a.attr("filetype"), a.attr("data-path"), a.find("input").val(), rdata,a.attr('fileshare'),a.attr('data-composer'),a.attr('data-ps')));
                    $(this).find('input').prop("checked", true);
                    $(this).addClass('ui-selected');
                    $(this).siblings().removeClass('ui-selected').find('input').prop("checked", false);
                }
                else {
                    RClickAll(e);
                }
            }
        });
        $(".showRow").change(function () {
            setCookie('showRow', $(this).val());
            GetFiles(p);
        });
        PathPlaceBtn(rdata.PATH);
        auto_table_width();
    });
}
function webshell_dir(path){
    layer.confirm('目录查杀将包含子目录中的php文件，是否操作？', { title: lan.files.dir_menu_webshell, closeBtn: 2, icon: 3 }, function (index) {
        layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=dir_webshell_check', 'path=' + path, function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        });
    });
}
function php_file_webshell(file){
	var loadT = layer.msg('正在查杀文件中，请稍后...', { icon: 16, time: 0, shade: [0.3, '#000'] });
	$.post('/files?action=file_webshell_check','filename='+ file,function(rdata){
		layer.close(loadT);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 0,time: 0,shade: 0.3,shadeClose:true });
	})
}
function auto_table_width() {
    var oldTable = $(window).height() - $('#tipTools')[0].getBoundingClientRect().height - $('#filePage')[0].getBoundingClientRect().height - $('.footer')[0].getBoundingClientRect().height - 115;
    var oldTable_heigth = $('.oldTable table').height();
    $('.oldTable thead th').each(function (index, el) {
        var table_th = $('.oldTable thead th').length;
        $('.newTable thead th').eq(index).attr('width', el.offsetWidth);
        if (index == (table_th - 1)) $('.newTable thead th').eq(table_th).attr('width', '10').css('padding', '0');
    });
    if (oldTable_heigth > oldTable) {
        $('.oldTableShadow,.newTableShadow').show();
        $('.oldTable').css('marginTop', '0')
    } else {
        $('.oldTableShadow,.newTableShadow').hide();
        $('.oldTable').css('marginTop', '0')
    }
    $('.oldTable').height(oldTable);
    $('.oldTable table').css({ 'marginTop': '-40px' })

}


function totalFile() {
    var el = $("input[name='id']");
    var len = el.length;
    var count = 0;
    for (var i = 0; i < len; i++) {
        if (el[i].checked == true) {
            count++;
        }
    }
    return count;
}
function bindselect() {
    $("#filesBody").selectable({
        autoRefresh: false,
        filter: "tr,.folderBox",
        cancel: "a,span,input,.ico-folder",
        selecting: function (e) {
            $(".ui-selecting").find("input").prop("checked", true);
            showSeclect();
        },
        selected: function (e) {
            $(".ui-selectee").find("input").prop("checked", false);
            $(".ui-selected", this).each(function () {
                $(this).find("input").prop("checked", true);
                showSeclect();
            });
            $("#contextify-menu").hide();
        },
        unselecting: function (e) {
            $(".ui-selectee").find("input").prop("checked", false);
            $(".ui-selecting").find("input").prop("checked", true);
            showSeclect();
            $("#rmenu").hide()
        }
    });
    $("#filesBody").selectable("refresh");
    $(".ico-folder").click(function () {
        $(this).parent().addClass("ui-selected").siblings().removeClass("ui-selected");
        $(".ui-selectee").find("input").prop("checked", false);
        $(this).prev("input").prop("checked", true);
        showSeclect();
    })
}
function showSeclect() {
    var count = totalFile();
    var BatchTools = '';
    if (count > 1) {
        BatchTools = '<button onclick="javascript:Batch(1);" class="btn btn-default btn-sm">' + lan.files.file_menu_copy + '</button>\
						  <button onclick="javascript:Batch(2);" class="btn btn-default btn-sm">'+ lan.files.file_menu_mv + '</button>\
						  <button onclick="javascript:Batch(3);" class="btn btn-default btn-sm">'+ lan.files.file_menu_auth + '</button>\
						  <button onclick="javascript:Batch(5);" class="btn btn-default btn-sm">'+ lan.files.file_menu_zip + '</button>\
						  <button onclick="javascript:Batch(4);" class="btn btn-default btn-sm">'+ lan.files.file_menu_del + '</button>'
        $("#Batch").html(BatchTools);
    } else {
        $("#Batch").html(BatchTools);
    }
}
$(window).keyup(function(e){
    var tagName = e.target.tagName.toLowerCase();
    if(e.keyCode === 8 && tagName !== 'input' && tagName !== 'textarea'){ //判断当前键值码为space
        if($('.aceEditors')[0] == undefined || $('.aceEditors .layui-layer-content').height() === 0){
            BackDir();
        }
    }
    e.stopPropagation();
});

$("#tipTools").width($(".file-box")[0].clientWidth-30);
$("#PathPlaceBtn").width($(".file-box").width() - 700);
$("#DirPathPlace input").width($(".file-box").width() - 700);
if ($(window).width() < 1160) {
    $("#PathPlaceBtn").width(290);
}
window.onresize = function () {
    $("#tipTools").width($(".file-box")[0].clientWidth-30);
    $("#PathPlaceBtn").width($(".file-box").width() - 700);
    $("#DirPathPlace input").width($(".file-box").width() - 700);
    if ($(window).width() < 1160) {
        $("#PathPlaceBtn,#DirPathPlace input").width(290);
    }
    PathLeft();
    IsDiskWidth()
    auto_table_width();
}
function Batch(type, access) {
    var path = $("#DirPathPlace input").val();
    var el = document.getElementsByTagName('input');
    var len = el.length;
    var data = 'path=' + path + '&type=' + type;
    var name = 'data';
    var datas = []

    var oldType = getCookie('BatchPaste');

    for (var i = 0; i < len; i++) {
        if (el[i].checked == true && el[i].value != 'on') {
            datas.push(el[i].value)
        }
    }

    data += "&data=" + encodeURIComponent(JSON.stringify(datas))

    if (type == 3 && access == undefined) {
        SetChmod(0, lan.files.all);
        return;
    }

    if (type < 3) setCookie('BatchSelected', '1');
    setCookie('BatchPaste', type);

    if (access == 1) {
        var access = $("#access").val();
        var chown = $("#chown").val();
        var all = $("#accept_all").prop("checked") ? 'True' : 'False';
        data += '&access=' + access + '&user=' + chown + "&all=" + all;
        layer.closeAll();
    }
    if (type == 4) {
        AllDeleteFileSub(data, path);
        setCookie('BatchPaste', oldType);
        return;
    }

    if (type == 5) {
        var names = '';
        for (var i = 0; i < len; i++) {
            if (el[i].checked == true && el[i].value != 'on') {
                names += el[i].value + ',';
            }
        }
        Zip(names);
        return;
    }
    if(type == 6){
    	webshell_dir()
    }

    myloadT = layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", { icon: 16, time: 0, shade: [0.3, '#000'] });
    setTimeout(function () { getSpeed('.myspeed'); }, 1000);
    $.post('/files?action=SetBatchData', data, function (rdata) {
        layer.close(myloadT);
        GetFiles(path);
        layer.msg(rdata.msg, { icon: 1 });
    });
}
function BatchPaste() {
    var path = $("#DirPathPlace input").val();
    var type = getCookie('BatchPaste');
    var data = 'type=' + type + '&path=' + path;

    $.post('/files?action=CheckExistsFiles', { dfile: path }, function (result) {
        if (result.length > 0) {
            var tbody = '';
            for (var i = 0; i < result.length; i++) {
                tbody += '<tr><td>' + result[i].filename + '</td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
            }
            var mbody = '<div class="divtable" style="height: 395px;overflow: auto;border: #ddd 1px solid;position: relative;"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
						<tbody>'+ tbody + '</tbody>\
						</table></div>';
            SafeMessage('即将覆盖以下文件', mbody, function () {
                BatchPasteTo(data, path);
            });
            $(".layui-layer-page").css("width", "500px");
        } else {
            BatchPasteTo(data, path);
        }
    });
}

function BatchPasteTo(data, path) {
    myloadT = layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", { icon: 16, time: 0, shade: [0.3, '#000'] });
    setTimeout(function () { getSpeed('.myspeed'); }, 1000);
    $.post('files?action=BatchPaste', data, function (rdata) {
        layer.close(myloadT);
        setCookie('BatchSelected', null);
        GetFiles(path);
        layer.msg(rdata.msg, { icon: 1 });
    });
}
function GetExtName(fileName) {
    var extArr = fileName.split(".");
    var exts = ['folder', 'folder-unempty', 'sql', 'c', 'cpp', 'cs', 'flv', 'css', 'js', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'rtf', 'docx', 'fdf', 'potm', 'pptx', 'txt', 'xlsb', 'xlsx', '7z', 'cab', 'iso', 'bz2', 'rar', 'zip', 'gz', 'bt', 'file', 'apk', 'bookfolder', 'folder', 'folder-empty', 'folder-unempty', 'fromchromefolder', 'documentfolder', 'fromphonefolder', 'mix', 'musicfolder', 'picturefolder', 'videofolder', 'sefolder', 'access', 'mdb', 'accdb', 'sql', 'c', 'cpp', 'cs', 'js', 'fla', 'flv', 'htm', 'html', 'java', 'log', 'mht', 'php', 'url', 'xml', 'ai', 'bmp', 'cdr', 'gif', 'ico', 'jpeg', 'jpg', 'JPG', 'png', 'psd', 'webp', 'ape', 'avi', 'flv', 'mkv', 'mov', 'mp3', 'mp4', 'mpeg', 'mpg', 'rm', 'rmvb', 'swf', 'wav', 'webm', 'wma', 'wmv', 'doc', 'docm', 'dotx', 'dotm', 'dot', 'rtf', 'docx', 'pdf', 'fdf', 'ppt', 'pptm', 'pot', 'potm', 'pptx', 'txt', 'xls', 'csv', 'xlsm', 'xlsb', 'xlsx', '7z', 'gz', 'cab', 'iso', 'rar', 'zip', 'bt', 'file', 'apk', 'css'];
    var extLastName = extArr[extArr.length - 1];
    for (var i = 0; i < exts.length; i++) {
        if (exts[i] == extLastName) {
            return exts[i];
        }
    }
    return 'file';
}
function ShowEditMenu() {
    $("#filesBody > tr").hover(function () {
        $(this).addClass("hover");
    }, function () {
        $(this).removeClass("hover");
    }).click(function () {
        $(this).addClass("on").siblings().removeClass("on");
    })
}
function GetFileName(fileNameFull) {
    var pName = fileNameFull.split('/');
    return pName[pName.length - 1];
}
function GetDisk() {
    var LBody = '';
    $.get('/system?action=GetDiskInfo', function (rdata) {
        for (var i = 0; i < rdata.length; i++) {
            LBody += "<span onclick=\"GetFiles('" + rdata[i].path + "')\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" + (rdata[i].path == '/' ? lan.files.path_root : rdata[i].path) + "(" + rdata[i].size[2] + ")</span>";
        }
        var trash = '<span id="recycle_bin" onclick="Recycle_bin(\'open\')" title="' + lan.files.recycle_bin_title + '" style="position: absolute; border-color: #ccc; right: 77px;"><span class="glyphicon glyphicon-trash"></span>&nbsp;' + lan.files.recycle_bin_title + '</span>';
        $("#comlist").html(LBody + trash);
        IsDiskWidth();
    });
}
function BackDir() {
    var str = $("#DirPathPlace input").val().replace('//', '/');
    if (str.substr(str.length - 1, 1) == '/') {
        str = str.substr(0, str.length - 1);
    }
    var Path = str.split("/");
    var back = '/';
    if (Path.length > 2) {
        var count = Path.length - 1;
        for (var i = 0; i < count; i++) {
            back += Path[i] + '/';
        }
        if (back.substr(back.length - 1, 1) == '/') {
            back = back.substr(0, back.length - 1);
        }
        GetFiles(back);
    } else {
        back += Path[0];
        GetFiles(back);
    }
    setTimeout('PathPlaceBtn(getCookie("Path"));', 200);
}
function CreateFile(type, path) {
    if (type == 1) {
        var fileName = $("#newFileName").val();
        layer.msg(lan.public.the, { icon: 16, time: 10000 });
        $.post('/files?action=CreateFile', 'path=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
            layer.close(getCookie('layers'));
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            if (rdata.status) {
                GetFiles($("#DirPathPlace input").val());
                openEditorView(0, path + '/' + fileName);
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
					<input type="text" class="bt-input-text" name="Name" id="newFileName" value="" placeholder="'+ lan.files.file_name + '" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm layer_close">'+ lan.public.close + '</button>\
					<button id="CreateFileBtn" type="button" class="btn btn-success btn-sm" onclick="CreateFile(1,\'' + path + '\')">' + lan.files.new + '</button>\
					</div>\
				</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newFileName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#CreateFileBtn").click();
    });
}
function CreateDir(type, path) {
    if (type == 1) {
        var dirName = $("#newDirName").val();
        layer.msg(lan.public.the, {
            icon: 16,
            time: 10000
        });
        $.post('/files?action=CreateDir', 'path=' + encodeURIComponent(path + '/' + dirName), function (rdata) {
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
					<input type="text" class="bt-input-text" name="Name" id="newDirName" value="" placeholder="'+ lan.files.dir_name + '" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+ lan.public.close + '</button>\
					<button type="button" id="CreateDirBtn" class="btn btn-success btn-sm btn-title" onclick="CreateDir(1,\'' + path + '\')">' + lan.files.new + '</button>\
					</div>\
				</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newDirName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#CreateDirBtn").click();
    });
}
// 删除文件
function DeleteFile(fileName) {
    layer.confirm(lan.get('recycle_bin_confirm', [fileName]), { title: lan.files.del_file, closeBtn: 2, icon: 3 }, function (index) {
        layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=DeleteFile', 'path=' + encodeURIComponent(fileName), function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            GetFiles($("#DirPathPlace input").val());
        });
    });
}
function DeleteDir(dirName) {
    layer.confirm(lan.get('recycle_bin_confirm_dir', [dirName]), { title: lan.files.del_dir, closeBtn: 2, icon: 3 }, function (index) {
        layer.msg(lan.public.the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=DeleteDir', 'path=' + encodeURIComponent(dirName), function (rdata) {
            layer.close(index);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            GetFiles($("#DirPathPlace input").val());
        });
    });
}
function AllDeleteFileSub(data, path) {
    layer.confirm(lan.files.del_all_msg, { title: lan.files.del_all_file, closeBtn: 2, icon: 3 }, function (index) {
        layer.msg("<div class='myspeed'>" + lan.public.the + "</div>", { icon: 16, time: 0, shade: [0.3, '#000'] });
        setTimeout(function () { getSpeed('.myspeed'); }, 1000);
        $.post('files?action=SetBatchData', data, function (rdata) {
            layer.close(index);
            GetFiles(path);
            layer.msg(rdata.msg, { icon: 1 });
        });
    });
}
function ReloadFiles() {
    setInterval(function () {
        var path = $("#DirPathPlace input").val();
        GetFiles(path);
    }, 3000);
}
function DownloadFile(action) {
    if (action == 1) {
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
        layer.msg(lan.files.down_task, { time: 0, icon: 16, shade: [0.3, '#000'] });
        $.post('/files?action=DownloadFile', 'path=' + fpath + '&url=' + fUrl + '&filename=' + fname, function (rdata) {
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
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
					<span class="tname">'+ lan.files.down_url + ':</span><input type="text" class="bt-input-text" name="url" id="mUrl" value="" placeholder="' + lan.files.down_url + '" style="width:330px" />\
					</div>\
					<div class="line">\
					<span class="tname ">'+ lan.files.down_to + ':</span><input type="text" class="bt-input-text" name="path" id="dpath" value="' + path + '" placeholder="' + lan.files.down_to + '" style="width:330px" />\
					</div>\
					<div class="line">\
					<span class="tname">'+ lan.files.file_name + ':</span><input type="text" class="bt-input-text" name="filename" id="dfilename" value="" placeholder="' + lan.files.down_save + '" style="width:330px" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm layer_close">'+ lan.public.close + '</button>\
					<button type="button" id="dlok" class="btn btn-success btn-sm dlok" onclick="DownloadFile(1)">'+ lan.public.ok + '</button>\
					</div>\
				</form>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index)
            });
        }
    });
    setCookie('layers', layers);
    //fly("dlok");
    $("#mUrl").change(function () {
        durl = $(this).val()
        tmp = durl.split('/')
        $("#dfilename").val(tmp[tmp.length - 1])
    });
}
function ExecShell(action) {
    if (action == 1) {
        var path = $("#DirPathPlace input").val();
        var exec = encodeURIComponent($("#mExec").val());
        $.post('/files?action=ExecShell', 'path=' + path + '&shell=' + exec, function (rdata) {
            if (rdata.status) {
                $("#mExec").val('');
                GetShellEcho();
            }
            else {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            }

        });
        return;
    }
    layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: ['70%', '600px'],
        title: lan.files.shell_title,
        content: '<div class="bt-form pd15">\
					<div class="shellcode"><pre id="Result"></pre></div>\
					<div class="line">\
					<input type="text" class="bt-input-text" name="exec" id="mExec" value="" placeholder="'+ lan.files.shell_ps + '" onkeydown="if(event.keyCode==13)ExecShell(1);" /><span class="shellbutton btn btn-default btn-sm pull-right" onclick="ExecShell(1)" style="width:10%">' + lan.files.shell_go + '</span>\
					</div>\
				</div>'
    });
    setTimeout(function () {
        outTimeGet();
    }, 1000);

}

var outTime = null;
function outTimeGet() {
    outTime = setInterval(function () {
        if (!$("#mExec").attr('name')) {
            clearInterval(outTime);
            return;
        }
        GetShellEcho();
    }, 1000);
}

function GetShellEcho() {
    $.post('/files?action=GetExecShellMsg', '', function (rdata) {
        $("#Result").html(rdata);
        $(".shellcode").scrollTop($(".shellcode")[0].scrollHeight);
    });
}
function ReName(type, fileName) {
    if (type == 1) {
        var path = $("#DirPathPlace input").val();
        var newFileName = encodeURIComponent(path + '/' + $("#newFileName").val());
        var oldFileName = encodeURIComponent(path + '/' + fileName);
        layer.msg(lan.public.the, { icon: 16, time: 10000 });
        $.post('/files?action=MvFile', 'sfile=' + oldFileName + '&dfile=' + newFileName + '&rename=true', function (rdata) {
            layer.close(getCookie('layers'));
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
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
				<input type="text" class="bt-input-text" name="Name" id="newFileName" value="' + fileName + '" placeholder="' + lan.files.file_name + '" style="width:100%" />\
				</div>\
				<div class="bt-form-submit-btn">\
				<button type="button" class="btn btn-danger btn-sm btn-title layers_close">'+ lan.public.close + '</button>\
				<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="ReName(1,\'' + fileName.replace(/'/, "\\'") + '\')">' + lan.public.save + '</button>\
				</div>\
			</div>',
        success: function (layers, index) {
            $('.layers_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    $("#newFileName").focus().keyup(function (e) {
        if (e.keyCode == 13) $("#ReNameBtn").click();
    });
}
function CutFile(fileName) {
    var path = $("#DirPathPlace input").val();
    setCookie('cutFileName', fileName);
    setCookie('copyFileName', null);
    layer.msg(lan.files.mv_ok, { icon: 1, time: 1000 });
    GetFiles(path);
}
function CopyFile(fileName) {
    var path = $("#DirPathPlace input").val();
    setCookie('copyFileName', fileName);
    setCookie('cutFileName', null);
    layer.msg(lan.files.copy_ok, { icon: 1, time: 1000 });
    GetFiles(path);
}
function PasteFile(fileName) {
    var path = $("#DirPathPlace input").val();
    var copyName = getCookie('copyFileName');
    var cutName = getCookie('cutFileName');
    var filename = copyName;
    if (cutName != 'null' && cutName != undefined) filename = cutName;
    filename = filename.split('/').pop();
    $.post('/files?action=CheckExistsFiles', { dfile: path, filename: filename }, function (result) {
        if (result.length > 0) {
            var tbody = '';
            for (var i = 0; i < result.length; i++) {
                tbody += '<tr><td>' + result[i].filename + '</td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
            }
            var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
						<tbody>'+ tbody + '</tbody>\
						</table></div>';
            SafeMessage('即将覆盖以下文件', mbody, function () {
                PasteTo(path, copyName, cutName, fileName);
            });
        } else {
            PasteTo(path, copyName, cutName, fileName);
        }
    });
}


function PasteTo(path, copyName, cutName, fileName) {
    if (copyName != 'null' && copyName != undefined) {
        layer.msg(lan.files.copy_the, {
            icon: 16,
            time: 0, shade: [0.3, '#000']
        });
        $.post('/files?action=CopyFile', 'sfile=' + encodeURIComponent(copyName) + '&dfile=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
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
            time: 0, shade: [0.3, '#000']
        });
        $.post('/files?action=MvFile', 'sfile=' + encodeURIComponent(cutName) + '&dfile=' + encodeURIComponent(path + '/' + fileName), function (rdata) {
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
function Zip(dirName, submits) {
    var path = $("#DirPathPlace input").val();
    if (submits != undefined) {
        if (dirName.indexOf(',') == -1) {
            tmp = $("#sfile").val().split('/');
            sfile = encodeURIComponent(tmp[tmp.length - 1]);
        } else {
            sfile = encodeURIComponent(dirName);
        }
        dfile = encodeURIComponent($("#dfile").val());
        var z_type = $("select[name='z_type']").val();
        if (!z_type) z_type = 'tar.gz';
        layer.close(getCookie('layers'));
        var layers = layer.msg(lan.files.zip_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=Zip', 'sfile=' + sfile + '&dfile=' + dfile + '&z_type=' + z_type + '&path=' + encodeURIComponent(path), function (rdata) {
            layer.close(layers);
            if (rdata == null || rdata == undefined) {
                layer.msg(lan.files.zip_ok, { icon: 1 });
                GetFiles(path)
                ReloadFiles();
                return;
            }
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            if (rdata.status) {
                task_stat()
                GetFiles(path);
            }
        });
        return
    }

    param = dirName;
    if (dirName.indexOf(',') != -1) {
        tmp = path.split('/')
        dirName = path + '/' + tmp[tmp.length - 1]
    }
    
    var arrs = dirName.split('/');
    var root_path = '';
    for (var i = 0; i < arrs.length - 1; i++) {
        root_path += arrs[i] + '/'
    }
    
    var zipname = root_path + bt.get_random(10) + '.tar.gz';
    
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '650px',
        title: lan.files.zip_title,
        content: '<div class="bt-form pd20 pb70">'
            + '<div class="line noborder">'
            + '<input type="text" class="form-control" id="sfile" value="' + param + '" placeholder="" style="display:none" />'
            + '<p style="margin-bottom: 10px;"><span>压缩类型</span><select style="margin-left: 8px;" class="bt-input-text" name="z_type"><option value="tar.gz">tar.gz (推荐)</option><option value="zip">zip (通用格式)</option><option value="rar">rar (WinRAR对中文兼容较好)</option></select></p>'
            + '<span>' + lan.files.zip_to + '</span><input type="text" class="bt-input-text" id="dfile" value="' + zipname + '" placeholder="' + lan.files.zip_to + '" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" /><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'dfile\')"></span>'
            + '</div>'
            + '<div class="line"><div class="info-r  ml0 label-input-group ptb10" style="margin-left: 55px;"> <input type="checkbox" checked="checked" class="random_zip_name" id="random_zip_name" name="random_zip_name"><label class="mr20" for="random_zip_name" style="font-weight:normal">随机生成压缩包名</label></div></div>'
            + '<div class="bt-form-submit-btn">'
            + '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>'
            + '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="Zip(\'' + param + '\',1)">' + lan.files.file_menu_zip + '</button>'
            + '</div>'
            + '</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
    setTimeout(function () {
        $("select[name='z_type']").change(function () {
            var z_type = $(this).val();
            
            var _checked = $(this).prop('checked')         
            if(_checked){
                zipname = zipname.replace("tar.gz", z_type)
                $("#dfile").val(zipname);
            }
            else{
                dirName = dirName.replace("tar.gz", z_type)
                $("#dfile").val(dirName + '.' + z_type); 
            }
        });
        
         $("#random_zip_name").change(function () {
            var _checked = $(this).prop('checked')               
            if (_checked){                
                $("#dfile").val(zipname);
            }
            else {
                var z_type =  $("select[name='z_type']").val();
                $("#dfile").val(dirName + '.' + z_type); 
            }
        })
    }, 100);

}
function UnZip(fileName, type) {
    var path = $("#DirPathPlace input").val();
    if (type.length == 3) {
        var sfile = encodeURIComponent($("#sfile").val());
        var dfile = encodeURIComponent($("#dfile").val());
        var password = encodeURIComponent($("#unpass").val());
        coding = $("select[name='coding']").val();
        layer.close(getCookie('layers'));
        layer.msg(lan.files.unzip_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/files?action=UnZip', 'sfile=' + sfile + '&dfile=' + dfile + '&type=' + type + '&coding=' + coding + '&password=' + password, function (rdata) {
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            task_stat();
            GetFiles(path);
        });
        return
    }

    type = (type == 1) ? 'tar' : 'zip'
    var umpass = '';
    if (type == 'zip') {
        umpass = '<div class="line"><span class="tname">' + lan.files.zip_pass_title + '</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="' + lan.files.zip_pass_msg + '" style="width:330px" /></div>'
    }
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '490px',
        title: lan.files.unzip_title,
        content: '<div class="bt-form pd20 pb70">'
            + '<div class="line unzipdiv">'
            + '<span class="tname">' + lan.files.unzip_name + '</span><input type="text" class="bt-input-text" id="sfile" value="' + fileName + '" placeholder="' + lan.files.unzip_name_title + '" style="width:330px" /></div>'
            + '<div class="line"><span class="tname">' + lan.files.unzip_to + '</span><input type="text" class="bt-input-text" id="dfile" value="' + path + '" placeholder="' + lan.files.unzip_to + '" style="width:330px" /></div>' + umpass
            + '<div class="line"><span class="tname">' + lan.files.unzip_coding + '</span><select class="bt-input-text" name="coding">'
            + '<option value="UTF-8">UTF-8</option>'
            + '<option value="gb18030">GBK</option>'
            + '</select>'
            + '</div>'
            + '<div class="bt-form-submit-btn">'
            + '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>'
            + '<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" onclick="UnZip(\'' + fileName + '\',\'' + type + '\')">' + lan.files.file_menu_unzip + '</button>'
            + '</div>'
            + '</div>',
        success: function (layers, index) {
            $('.layer_close').click(function () {
                layer.close(index);
            });
        }
    });
    setCookie('layers', layers);
}
function isZip(fileName) {
    var ext = fileName.split('.');
    var extName = ext[ext.length - 1].toLowerCase();
    if (extName == 'zip' || extName == 'war' || extName == 'rar') return 0;
    if (extName == 'gz' || extName == 'tgz' || extName == 'bz2') return 1;
    return -1;
}
function isText(fileName) {
    var exts = ['rar', 'war', 'zip', 'tar.gz', 'gz', 'iso', 'xsl', 'doc', 'xdoc', 'jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'exe', 'so', '7z', 'bz', 'bz2','ico'];
    return isExts(fileName, exts) ? false : true;
}
function isImage(fileName) {
    var exts = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico'];
    return isExts(fileName, exts);
}
function isVideo(fileName) {
    var exts = ['mp4', 'mpeg', 'mpg', 'mov', 'avi', 'webm', 'mkv'];
    return isExts(fileName, exts);
}
function isPhp(fileName){
	var exts = ['php'];
	return isExts(fileName,exts);
}
function isExts(fileName, exts) {
    var ext = fileName.split('.');
    if (ext.length < 2) return false;
    var extName = ext[ext.length - 1].toLowerCase();
    for (var i = 0; i < exts.length; i++) {
        if (extName == exts[i]) return true;
    }
    return false;
}
function GetImage(data) {
    console.log(data);
    var that = this,mask = $('<div class="preview_images_mask">'+
        '<div class="preview_head">'+
            '<span class="preview_title">'+ data.filename +'</span>'+
            '<span class="preview_small hidden" title="缩小显示"><span class="glyphicon glyphicon-resize-small" aria-hidden="true"></span></span>'+
            '<span class="preview_full" title="最大化显示"><span class="glyphicon glyphicon-resize-full" aria-hidden="true"></span></span>'+
            '<span class="preview_close" title="关闭图片预览视图"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></span>'+
        '</div>'+
        '<div class="preview_body"><img id="preview_images" src="/download?filename='+ data.path +'"></div>'+
        '<div class="preview_toolbar">'+
            '<a href="javascript:;" title="左旋转"><span class="glyphicon glyphicon-repeat reverse-repeat" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="右旋转"><span class="glyphicon glyphicon-repeat" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="放大视图"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="缩小视图"><span class="glyphicon glyphicon-zoom-out" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="重置视图"><span class="glyphicon glyphicon-refresh" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="图片列表"><span class="glyphicon glyphicon-list" aria-hidden="true"></span></a>'+
        '</div>'+
        '<div class="preview_cut_view" style="display:none;">'+
            '<a href="javascript:;" title="上一张"><span class="glyphicon glyphicon-menu-left" aria-hidden="true"></span></a>'+
            '<a href="javascript:;" title="下一张"><span class="glyphicon glyphicon-menu-right" aria-hidden="true"></span></a>'+
        '</div>'+
    '</div>'),
    images_config = {natural_width:0,natural_height:0,init_width:0,init_height:0,preview_width:0,preview_height:0,current_width:0,current_height:0,current_left:0,current_top:0,rotate:0,scale:1,images_mouse:false};
    if($('.preview_images_mask').length > 0){
        $('#preview_images').attr('src','/download?filename=' + data.path);
        return false;
    }
    $('body').css('overflow','hidden').append(mask);
    images_config.preview_width = mask[0].clientWidth;
    images_config.preview_height = mask[0].clientHeight;
    // 图片预览
    $('.preview_body img').load(function(){
        var img = $(this)[0];
        if(!$(this).attr('data-index')) $(this).attr('data-index',data.images_id);
        images_config.natural_width = img.naturalWidth;
        images_config.natural_height = img.naturalHeight;
        auto_images_size(false);
    });
    //图片头部拖动
    $('.preview_images_mask .preview_head').on('mousedown',function(e){
        e = e || window.event; //兼容ie浏览器
        var drag = $(this).parent();
        $('body').addClass('select'); //webkit内核和火狐禁止文字被选中
        document.body.onselectstart = document.body.ondrag = function () { //ie浏览器禁止文字选中
            return false;
        }
        if ($(e.target).hasClass('preview_close')) { //点关闭按钮不能拖拽模态框
            return;
        }
        var diffX = e.clientX - drag.offset().left;
        var diffY = e.clientY - drag.offset().top;
        $(document).on('mousemove',function(e){
            e = e || window.event; //兼容ie浏览器
            var left = e.clientX - diffX;
            var top = e.clientY - diffY;
            if (left < 0) {
                left = 0;
            } else if (left > window.innerWidth - drag.width()) {
                left = window.innerWidth - drag.width();
            }
            if (top < 0) {
                top = 0;
            } else if (top > window.innerHeight - drag.height()) {
                top = window.innerHeight - drag.height();
            }
            drag.css({
                left:left,
                top:top,
                margin:0
            });
        }).on('mouseup',function(){
            $(this).unbind('mousemove mouseup');
        });
    });
    //图片拖动
    $('.preview_images_mask #preview_images').on('mousedown',function(e){
        e = e || window.event;
        document.body.onselectstart = document.body.ondrag = function(){
            return false;
        }
        var images = $(this);
        var preview =  $('.preview_images_mask').offset();
        var diffX = e.clientX - preview.left;
        var diffY = e.clientY - preview.top;
        $('.preview_images_mask').on('mousemove',function(e){
            e = e || window.event
            var offsetX = e.clientX - preview.left - diffX,
                offsetY = e.clientY - preview.top - diffY,
                rotate = Math.abs(images_config.rotate / 90),
                preview_width = (rotate % 2 == 0?images_config.preview_width:images_config.preview_height),
                preview_height = (rotate % 2 == 0?images_config.preview_height:images_config.preview_width),
                left,top;
            if(images_config.current_width > preview_width){
                var max_left = preview_width - images_config.current_width;
                left = images_config.current_left + offsetX;
                if(left > 0){
                    left = 0
                }else if(left < max_left){
                    left = max_left
                }
                images_config.current_left = left;
            }
            if(images_config.current_height > preview_height){
                var max_top = preview_height - images_config.current_height;
                top = images_config.current_top + offsetY;
                if(top > 0){
                    top = 0
                }else if(top < max_top){
                    top = max_top
                }
                images_config.current_top = top;
            }
            if(images_config.current_height > preview_height && images_config.current_top <= 0){
                if((images_config.current_height - preview_height) <= images_config.current_top){
                    images_config.current_top -= offsetY
                }
            }
            images.css({'left':images_config.current_left,'top':images_config.current_top});
        }).on('mouseup',function(){
            $(this).unbind('mousemove mouseup');
        }).on('dragstart',function(){
            e.preventDefault();
        });
    }).on('dragstart',function(){
        return false;
    });
    //关闭预览图片
    $('.preview_close').click(function(e){
        $('.preview_images_mask').remove();
    });
    //图片工具条预览
    $('.preview_toolbar a').click(function(){
        var index = $(this).index(),images = $('#preview_images');
        switch(index){
            case 0: //左旋转,一次旋转90度
            case 1: //右旋转,一次旋转90度
                images_config.rotate = index?(images_config.rotate + 90):(images_config.rotate - 90);
                auto_images_size();
            break;
            case 2:
            case 3:
                if(images_config.scale == 3 && index == 2|| images_config.scale == 0.2 && index == 3){
                    layer.msg((images_config.scale >= 1?'图像放大，已达到最大尺寸。':'图像缩小，已达到最小尺寸。'));
                    return false;
                }
                images_config.scale = (index == 2?Math.round((images_config.scale + 0.4)*10):Math.round((images_config.scale - 0.4)*10))/10;
                auto_images_size();
            break;
            case 4:
                var scale_offset =  images_config.rotate % 360;
                if(scale_offset >= 180){
                    images_config.rotate += (360 - scale_offset);
                }else{
                    images_config.rotate -= scale_offset;
                }
                images_config.scale = 1;
                auto_images_size();
            break;
        }
    });
    // 最大最小化图片
    $('.preview_full,.preview_small').click(function(){
        if($(this).hasClass('preview_full')){
            $(this).addClass('hidden').prev().removeClass('hidden');
            images_config.preview_width = $(window)[0].innerWidth;
            images_config.preview_height = $(window)[0].innerHeight;
            mask.css({width:images_config.preview_width,height:images_config.preview_height ,top:0,left:0,margin:0}).data('type','full');
            auto_images_size();
        }else{
            $(this).addClass('hidden').next().removeClass('hidden');
            $('.preview_images_mask').removeAttr('style');
            images_config.preview_width = 750;
            images_config.preview_height = 650;
            auto_images_size();
        }
    });
    // 自动图片大小
    function auto_images_size(transition){
        var rotate = Math.abs(images_config.rotate / 90),preview_width = (rotate % 2 == 0?images_config.preview_width:images_config.preview_height),preview_height = (rotate % 2 == 0?images_config.preview_height:images_config.preview_width),preview_images = $('#preview_images'),css_config = {};
        images_config.init_width = images_config.natural_width;
        images_config.init_height = images_config.natural_height;
        if(images_config.init_width > preview_width){
            images_config.init_width = preview_width;
            images_config.init_height = parseFloat(((preview_width / images_config.natural_width) * images_config.init_height).toFixed(2));
        }
        if(images_config.init_height > preview_height){
            images_config.init_width = parseFloat(((preview_height / images_config.natural_height) * images_config.init_width).toFixed(2));
            images_config.init_height= preview_height;
        }
        images_config.current_width = parseFloat(images_config.init_width * images_config.scale);
        images_config.current_height  = parseFloat(images_config.init_height * images_config.scale);
        images_config.current_left = parseFloat(((images_config.preview_width - images_config.current_width) / 2).toFixed(2));
        images_config.current_top = parseFloat(((images_config.preview_height - images_config.current_height) / 2).toFixed(2));
        css_config = {
            'width':images_config.current_width ,
            'height':images_config.current_height,
            'top':images_config.current_top,
            'left':images_config.current_left,
            'display':'inline',
            'transform':'rotate('+ images_config.rotate +'deg)',
            'opacity':1,
            'transition':'all 400ms',
        }
        if(transition === false) delete css_config.transition;
        preview_images.css(css_config);
    }

}

function play_file(obj,filename) {
    if($('#btvideo video').attr('data-filename')== filename) return false;
    var imgUrl = '/download?filename=' + filename + '&play=true';
    var v = '<video src="' + imgUrl +'" controls="controls" data-fileName="'+ filename +'" autoplay="autoplay" width="640" height="360">\
                    您的浏览器不支持 video 标签。\
                    </video>'
    $("#btvideo").html(v);
    var p_tmp = filename.split('/')
    $(".btvideo-title").html(p_tmp[p_tmp.length-1]);
    $(".video-avt").removeClass('video-avt');
    $(obj).parents('tr').addClass('video-avt');
}
function GetPlay(fileName) {
    var old_filename = fileName;
    var imgUrl = '/download?filename=' + fileName;
    var p_tmp = fileName.split('/')
    var path = p_tmp.slice(0, p_tmp.length - 1).join('/')
    layer.open({
        type: 1,
        closeBtn: 2,
        // maxmin:true,
        title: '正在播放[<a class="btvideo-title">' + p_tmp[p_tmp.length-1] + '</a>]',
        area: ["890px","402px"],
        shadeClose: false,
        skin:'movie_pay',
        content: '<div id="btvideo"><video type="" src="' + imgUrl + '&play=true" data-filename="'+ fileName +'" controls="controls" autoplay="autoplay" width="640" height="360">\
                    您的浏览器不支持 video 标签。\
                    </video></div><div class="video-list"></div>',
        success: function () {
            $.post('/files?action=get_videos', { path: path }, function (rdata) {
                var video_list = '<table class="table table-hover" style=""><thead style="display: none;"><tr><th style="word-break: break-all;word-wrap:break-word;width:165px;">文件名</th><th style="width:65px" style="text-align:right;">大小</th></tr></thead>';
                for (var i = 0; i < rdata.length; i++) {
                    var filename = path + '/' + rdata[i].name
                    video_list += '<tr class="' + ((filename === old_filename) ? 'video-avt' :'') + '"><td style="word-break: break-all;word-wrap:break-word;width:150px" onclick="play_file(this,\'' + filename + '\')" title="文件: ' + filename + '\n类型: ' + rdata[i].type + '"><a>'
                        + rdata[i].name + '</a></td><td style="font-size: 8px;text-align:right;width:65px;">' + ToSize(rdata[i].size) + '</td></tr>';
                }
                video_list += '</table>';
                $('.video-list').html(video_list);
            });
        }
    });
}
function GetFileBytes(fileName, fileSize) {
    window.open('/download?filename=' + encodeURIComponent(fileName));
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
function SetChmod(action, fileName) {
    if (action == 1) {
        var chmod = $("#access").val();
        var chown = $("#chown").val();
        var all = $("#accept_all").prop("checked") ? 'True' : 'False';
        var data = 'filename=' + encodeURIComponent(fileName) + '&user=' + chown + '&access=' + chmod + '&all=' + all;
        var loadT = layer.msg(lan.public.config, { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('files?action=SetFileAccess', data, function (rdata) {
            layer.close(loadT);
            if (rdata.status) layer.close(getCookie('layers'));
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            var path = $("#DirPathPlace input").val();
            GetFiles(path)
        });
        return;
    }

    var toExec = fileName == lan.files.all ? 'Batch(3,1)' : 'SetChmod(1,\'' + fileName + '\')';

    $.post('/files?action=GetFileAccess', 'filename=' + encodeURIComponent(fileName), function (rdata) {
        var layers = layer.open({
            type: 1,
            closeBtn: 2,
            title: lan.files.set_auth + '[' + fileName + ']',
            area: '400px',
            shadeClose: false,
            content: '<div class="setchmod bt-form ptb15 pb70">\
						<fieldset>\
							<legend>'+ lan.files.file_own + '</legend>\
							<p><input type="checkbox" id="owner_r" />'+ lan.files.file_read + '</p>\
							<p><input type="checkbox" id="owner_w" />'+ lan.files.file_write + '</p>\
							<p><input type="checkbox" id="owner_x" />'+ lan.files.file_exec + '</p>\
						</fieldset>\
						<fieldset>\
							<legend>'+ lan.files.file_group + '</legend>\
							<p><input type="checkbox" id="group_r" />'+ lan.files.file_read + '</p>\
							<p><input type="checkbox" id="group_w" />'+ lan.files.file_write + '</p>\
							<p><input type="checkbox" id="group_x" />'+ lan.files.file_exec + '</p>\
						</fieldset>\
						<fieldset>\
							<legend>'+ lan.files.file_public + '</legend>\
							<p><input type="checkbox" id="public_r" />'+ lan.files.file_read + '</p>\
							<p><input type="checkbox" id="public_w" />'+ lan.files.file_write + '</p>\
							<p><input type="checkbox" id="public_x" />'+ lan.files.file_exec + '</p>\
						</fieldset>\
						<div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="'+ rdata.chmod + '">' + lan.files.file_menu_auth + '，\
						<span>'+ lan.files.file_own + '\
						<select id="chown" class="bt-input-text">\
							<option value="www" '+ (rdata.chown == 'www' ? 'selected="selected"' : '') + '>www</option>\
							<option value="mysql" '+ (rdata.chown == 'mysql' ? 'selected="selected"' : '') + '>mysql</option>\
							<option value="root" '+ (rdata.chown == 'root' ? 'selected="selected"' : '') + '>root</option>\
						</select></span>\
                        <span><input type="checkbox" id="accept_all" checked /><label for="accept_all" style="position: absolute;margin-top: 4px; margin-left: 5px;font-weight: 400;">应用到子目录</label></span>\
                        </div>\
						<div class="bt-form-submit-btn">\
							<button type="button" class="btn btn-danger btn-sm btn-title layer_close">'+ lan.public.close + '</button>\
					        <button type="button" class="btn btn-success btn-sm btn-title" onclick="'+ toExec + '" >' + lan.public.ok + '</button>\
				        </div>\
					</div>',
            success: function (layers, index) {
                $('.layer_close').click(function () {
                    layer.close(index);
                })
            }
        });
        setCookie('layers', layers);

        onAccess();
        $("#access").keyup(function () {
            onAccess();
        });

        $("input[type=checkbox]").change(function () {
            var idName = ['owner', 'group', 'public'];
            var onacc = '';
            for (var n = 0; n < idName.length; n++) {
                var access = 0;
                access += $("#" + idName[n] + "_x").prop('checked') ? 1 : 0;
                access += $("#" + idName[n] + "_w").prop('checked') ? 2 : 0;
                access += $("#" + idName[n] + "_r").prop('checked') ? 4 : 0;
                onacc += access;
            }
            $("#access").val(onacc);

        });
    })

}

function onAccess() {
    var access = $("#access").val();
    var idName = ['owner', 'group', 'public'];
    for (var n = 0; n < idName.length; n++) {
        $("#" + idName[n] + "_x").prop('checked', false);
        $("#" + idName[n] + "_w").prop('checked', false);
        $("#" + idName[n] + "_r").prop('checked', false);
    }
    for (var i = 0; i < access.length; i++) {
        var onacc = access.substr(i, 1);
        if (i > idName.length) continue;
        if (onacc > 7) $("#access").val(access.substr(0, access.length - 1));
        switch (onacc) {
            case '1':
                $("#" + idName[i] + "_x").prop('checked', true);
                break;
            case '2':
                $("#" + idName[i] + "_w").prop('checked', true);
                break;
            case '3':
                $("#" + idName[i] + "_x").prop('checked', true);
                $("#" + idName[i] + "_w").prop('checked', true);
                break;
            case '4':
                $("#" + idName[i] + "_r").prop('checked', true);
                break;
            case '5':
                $("#" + idName[i] + "_r").prop('checked', true);
                $("#" + idName[i] + "_x").prop('checked', true);
                break;
            case '6':
                $("#" + idName[i] + "_r").prop('checked', true);
                $("#" + idName[i] + "_w").prop('checked', true);
                break;
            case '7':
                $("#" + idName[i] + "_r").prop('checked', true);
                $("#" + idName[i] + "_w").prop('checked', true);
                $("#" + idName[i] + "_x").prop('checked', true);
                break;
        }
    }
}
function RClick(type, path, name, file_store,file_share,data_composer,data_ps) {
    var displayZip = isZip(type);
    var options = {
        items: [
            { text: lan.files.file_menu_copy, onclick: function () { CopyFile(path) } },
            { text: lan.files.file_menu_mv, onclick: function () { CutFile(path) } },
            { text: lan.files.file_menu_rename, onclick: function () { ReName(0, name) } },
            { text: lan.files.file_menu_auth, onclick: function () { SetChmod(0, path) } },
            { text: lan.files.file_menu_zip, onclick: function () { Zip(path) } }

        ]
    };

    if (type == "dir") {
        options.items.push(
        	{ text: lan.files.file_menu_del, onclick: function () { DeleteDir(path) } },
        	{ text: lan.files.dir_menu_webshell, onclick: function () { webshell_dir(path) } }
        );
    }
    
    else if(isPhp(type)){
    	options.items.push({text: lan.files.file_menu_webshell, onclick: function() {php_file_webshell(path)}},{ text: lan.files.file_menu_edit, onclick: function () { openEditorView(0, path) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } })
    }
    else if (isVideo(type)) {
        options.items.push({ text: '播放', onclick: function () { GetPlay(path) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }
    else if (isText(type)) {
        options.items.push({ text: lan.files.file_menu_edit, onclick: function () { openEditorView(0, path) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }
    else if (displayZip != -1) {
        options.items.push({ text: lan.files.file_menu_unzip, onclick: function () { UnZip(path, displayZip) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }
    else if (isImage(type)) {
        options.items.push({ text: lan.files.file_menu_img, onclick: function () { GetImage({path:path,filename:name}) } }, { text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }
    else {
        options.items.push({ text: lan.files.file_menu_down, onclick: function () { GetFileBytes(path) } }, { text: lan.files.file_menu_del, onclick: function () { DeleteFile(path) } });
    }

    //if(type !== 'dir'){
        options.items.push({ text: '外链分享', onclick: function () { create_download_url(name,path,file_share) } });
    //}
    
    options.items.push({ text: '备注', onclick: function () { set_files_ps(0,path,data_ps) } });
    if( type === 'dir' && data_composer === '1'){
        options.items.push({ text: 'Composer', onclick: function () { exec_composer(path) } });
    }

    options.items.push({
        text: "收藏夹", onclick: function () {
			var loading = bt.load();
            bt.send('add_files_store', 'files/add_files_store',{path:path}, function (rRet) {
                loading.close();
                bt.msg(rRet);
                if (rRet.status) {
                    GetFiles(file_store.PATH)
                }
            });
        }
    })


    return options;
}

/**
 * 设置文件或目录备注
 * @param {string} path 全路径
 */
function set_files_ps(act,path,ps){

    if(act === 1){
        ps = $('#ps_body').val();
        // ps_type = $('#ps_type').val();
        $.post('/files?action=set_file_ps',{filename:path,ps_body:ps,ps_type:0},function(rdata){
            if(rdata.status){
                layer.closeAll();
                GetFiles(getCookie('Path'));
            }
            bt.msg(rdata);
            return;
        })
    }
    var arry = path.split('/');
    // <select id="ps_type" class="bt-input-text"><option value="0">全路径</option><option value="1">文件名</option></select>\
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '320px',
        title: '设置[ '+ arry[arry.length-1] +' ]文件备注',
        content: '<div class="bt-form pd20 pb70">\
                <div class="line">\
				    <input type="text" class="bt-input-text" name="ps_body" id="ps_body" value="' + ps + '" placeholder="请填写文件备注" style="width:100%" />\
				</div>\
				<div class="bt-form-submit-btn">\
				<button type="button" class="btn btn-danger btn-sm btn-title layers_close">'+ lan.public.close + '</button>\
				<button type="button" id="set-files-ps" class="btn btn-success btn-sm btn-title" onclick="set_files_ps(1,\'' + path + '\')">' + lan.public.save + '</button>\
				</div>\
			</div>',
        success: function (layers, index) {
            $('.layers_close').click(function () {
                layer.close(index);
            });
            setCookie('layers', layers);
            $("#ps_body").focus().keyup(function (e) {
                if (e.keyCode == 13) $("#set-files-ps").click();
            });
        }
    });
}

function update_composer(){
    loadT = bt.load()
    $.post('/files?action=update_composer',{},function(v_data){
        loadT.close();
        bt.msg(v_data);
    });
}


function exec_composer(fileName,path){
    $.post('/files?action=get_composer_version',{},function(v_data){
        if(v_data.status === false){
            bt.msg(v_data);
            return;
        }

        var php_versions = '';
        for(var i=0;i<v_data.php_versions.length;i++){
            if(v_data.php_versions[i].version == '00') continue;
            php_versions += '<option value="'+v_data.php_versions[i].version+'">'+v_data.php_versions[i].name+'</option>';
        }

        var layers = layer.open({
            type: 1,
            shift: 5,
            closeBtn: 2,
            area: '450px',
            title: '在['+path+']目录执行Composer',
            btn:['执行Composer','取消'],
            content: '<from class="bt-form" style="padding:30px 15px;display:inline-block">'
                + '<div class="line"><span class="tname">版本</span><div class="info-r"><input readonly="readonly" style="background-color: #eee;" name="composer_version" class="bt-input-text" value="'+v_data.msg +'" /><a onclick="update_composer();" style="margin-left: 5px;" class="btn btn-default btn-sm">升级Composer<a></div></div>'
                + '<div class="line"><span class="tname">PHP版本</span><div class="info-r">'
                    +'<select class="bt-input-text" name="php_version">'
                        +'<option value="auto">自动选择</option>'
                        +php_versions
                    +'</select>'
                +'</div></div>'
                + '<div class="line"><span class="tname">执行参数</span><div class="info-r">'
                    +'<select class="bt-input-text" name="composer_args">'
                        +'<option value="install">安装：install</option>'
                        +'<option value="update">更新：update</option>'
                    +'</select>'
                +'</div></div>'
                + '<div class="line"><span class="tname">镜像源</span><div class="info-r">'
                    +'<select class="bt-input-text" name="repo">'
                        +'<option value="https://mirrors.aliyun.com/composer/">阿里源：mirrors.aliyun.com</option>'
                        +'<option value="repos.packagist">官方源：packagist.org</option>'
                    +'</select>'
                +'</div></div>'
                + '</from>',
            yes:function(indexs,layers){
                layer.confirm('执行Composer的影响范围取决于该目录下的composer.json配置文件，继续吗？', { title: '确认执行Composer', closeBtn: 2, icon: 3 }, function (index) {
                    var pdata = {
                        php_version:$("select[name='php_version']").val(),
                        composer_args:$("select[name='composer_args']").val(),
                        repo:$("select[name='repo']").val(),
                        path:path
                    }
                    $.post('/files?action=exec_composer',pdata,function(rdatas){
                        if(!rdatas.status){
                            layer.msg(rdatas.msg,{icon:2});
                            return false;
                        }
                        layer.closeAll();
                        if(rdatas.status === true){
                            layer.open({
                                area:"600px",
                                type: 1,
                                shift: 5,
                                closeBtn: 2,
                                title: '在['+path+']目录执行Composer，执行完后请关闭此窗口',
                                content:"<pre id='composer-log' style='height: 300px;background-color: #333;color: #fff;margin: 0 0 0;'></pre>"
                            });
                            setTimeout(function(){show_composer_log();},200);
                        }
                    });
                });
            }
        });
    });
}


function show_composer_log(){
    $.post('/ajax?action=get_lines',{filename:'/tmp/panelExec.pl',num:30},function(v_body){
        var log_obj = $("#composer-log")
        if(log_obj.length < 1) return;
        log_obj.html(v_body.msg);
        var div = document.getElementById('composer-log')
        div.scrollTop = div.scrollHeight;
        setTimeout(function(){show_composer_log()},1000)
    });
}


function create_download_url(fileName,path,fileShare) {
	fileShare = parseInt(fileShare);
	if(fileShare != 0){
		$.post('/files?action=get_download_url_find',{id:fileShare},function(rdata){
    		set_download_url(rdata);
    	});
		return false
	}
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '450px',
        title: '外链分享',
        btn:['生成外链','取消'],
        content: '<from class="bt-form" id="outer_url_form" style="padding:30px 15px;display:inline-block">'
        	+ '<div class="line"><span class="tname">分享名称</span><div class="info-r"><input name="ps" class="bt-input-text mr5" type="text" placeholder="分享名称不能为空" style="width:270px" value="'+ fileName +'"></div></div>'
            + '<div class="line"><span class="tname">有效期</span><div class="info-r">'
                +'<label class="checkbox_grourd"><input type="radio" name="expire" value="24" checked><span>&nbsp;1天</span></label>'
                +'<label class="checkbox_grourd"><input type="radio" name="expire" value="168"><span>&nbsp;7天</span></label>'
                +'<label class="checkbox_grourd"><input type="radio" name="expire" value="1130800"><span>&nbsp;永久</span></label>'
            +'</div></div>'
        	+ '<div class="line"><span class="tname">提取码</span><div class="info-r"><input name="password" class="bt-input-text mr5" placeholder="为空则不设置提取码" type="text" style="width:170px" value=""><button type="button" id="random_paw" class="btn btn-success btn-sm btn-title">随机</button></div></div>'
            + '</from>',
        yes:function(indexs,layers){
        	layer.confirm('是否分享该文件，是否继续？', { title: '确认分享', closeBtn: 2, icon: 3 }, function (index) {
	        	var ps = $('[name=ps]').val(),expire = $('[name=expire]:checked').val(),password = $('[name=password]').val();
	        	if(ps === ''){
	        		layer.msg('分享名称不能为空',{icon:2});
	        		return false;
	        	}
	        	$.post('/files?action=create_download_url',{
	        		filename:path,
	        		ps:ps,
	        		password:password,
	        		expire:expire
	        	},function(rdatas){
        			if(!rdatas.status){
				    	layer.msg(rdatas.msg,{icon:2});
				    	return false;
				    }
				    layer.close(index);
				    layer.close(indexs)
	        		set_download_url(rdatas.msg);
	        	});
        	});
        },
        success: function (layers, index) {
            $('#random_paw').click(function(){
            	$(this).prev().val(bt.get_random(6));
            });
        }
    });
}


function set_download_url(rdata){
    var download_url = window.location.protocol + '//'+window.location.host + '/down/' + rdata.token;
    var layers = layer.open({
        type: 1,
        shift: 5,
        closeBtn: 2,
        area: '550px',
        title: '外链分享',
        content: '<div class="bt-form pd20 pb70">'
	            + '<div class="line"><span class="tname">分享名称</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:365px" value="'+ rdata.ps +'"></div></div>'
	        	+ '<div class="line external_link"><span class="tname">分享外链</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:280px" value="'+ download_url +'"><button type="button" id="copy_url" data-clipboard-text="'+ download_url +'" class="btn btn-success btn-sm btn-title copy_url" style="margin-right:5px" data-clipboard-target="#copy_url"><img style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABIUlEQVQ4T6XTsSuFURjH8d+3/AFm0x0MyqBEUQaUIqUU3YwWyqgMptud/BlMSt1SBiklg0K3bhmUQTFZDZTxpyOvznt7z3sG7/T2vOf5vM85z3nQPx+KfNuHkhoZ7xXYjNfEwIukXUnvNcg2sJECnoHhugpsnwBN21PAXVgbV/AEjNhuVSFA23YHWLNt4Cc3Bh6BUdtLcbzAgHPbp8BqCngAxjJbOANWUkAPGA8fE8icpD1gOQV0gclMBRfAYgq4BaZtz/YhA5IGgY7tS2AhBdwAM7b3JX1I+iz1G45sXwHzKeAa6P97qZgcEA6v/ZsR3v9aHCmt0P9UBVuShjKz8CYpXPkDYKJ0kaKhWpe0UwOFxDATx5VACFZ0Ivbuga8i8A3NFqQRZ5pz7wAAAABJRU5ErkJggg=="></button><button type="button" class="btn btn-success QR_code btn-sm btn-title"><img  style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABUklEQVQ4T6WSIU9DQRCEvwlYLIoEgwEECs3rDyCpobbtL6AKRyggMQ9TJBjUMzgMCeUnIEAREoICFAoEZMk2dy/Xo4KGNZu7nZ2bnT3xz1DsN7MFYCnhe5V0n/Kb2QowL2kY70cEoXAHVEnDG/ABXAJXmVDHVZKqSFAA58AqsAY8AW3A68/AQ7hbBG6BbeDGlaQEh8AucA3suzDgC5gFXHID2At5YxJBNwA6ocFBM8B3OL8DTaCcpMDN2QojxHHdk9Qrx9SeAyf1CMFIJ3DjYqxLOgo192gs4ibSNfrMOaj2yBvMrCnpImYHR4C/vizpIPkX/mpbUtfMepJKMxtKKsyslNTLCZxkBzgFjoE5oCVp08yKvyhwgkGyRl9nX1LDzDz3kzxS8kuBpFYygq8xJ4gjjBMEpz+BF+AxcXLg39XMOpLOciW1gtz9ac71GqdpSrE/8U20EQ3XLHEAAAAASUVORK5CYII="></button></div></div>'
	        	+ '<div class="line external_link" style="'+ (rdata.password == ""?"display:none;":"display:block") +'"><span class="tname">提取码</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:243px" value="'+ rdata.password +'"><button type="button" data-clipboard-text="链接:'+ download_url +' 提取码:'+ rdata.password +'"  class="btn btn-success copy_paw btn-sm btn-title">复制链接及提取码</button></div></div>'
	        	+ '<div class="line"><span class="tname">过期时间</span><div class="info-r"><span style="line-height:32px; display: block;font-size:14px">'+((rdata.expire > (new Date('2099-01-01 00:00:00').getTime())/1000)?'<span calss="btlink">永久有效</span>':bt.format_data(rdata.expire))+'</span></div></div>'
	        	+ '<div class="bt-form-submit-btn">'
	            + '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan.public.close + '</button>'
	            + '<button type="button" id="down_del" class="btn btn-danger btn-sm btn-title close_down" style="color:#fff;background-color:#c9302c;border-color:#ac2925;" onclick="">关闭分享外链</button>'
	            + '</div>'
            + '</div>',
        success: function (layers, index) {
        	var copy_url = new ClipboardJS('.copy_url');
        	var copy_paw = new ClipboardJS('.copy_paw');
        	copy_url.on('success', function(e) {
				layer.msg('复制链接成功!',{icon:1});
			    e.clearSelection();
			});
			copy_paw.on('success', function(e) {
				layer.msg('复制链接及提取码成功!',{icon:1});
			    e.clearSelection();
			});
            $('.layer_close').click(function () {
                layer.close(index);
            });
            $('.QR_code').click(function(){
            	layer.closeAll('tips');
            	layer.tips('<div style="height:140px;width:140px;padding:8px 0" id="QR_code"></div>','.QR_code',{
	            	area:['150px','150px'],
	            	tips: [1, '#ececec'],
	            	time:0,
	            	shade:[0.05, '#000'],
	            	shadeClose:true,
	            	success:function(){
	            		jQuery('#QR_code').qrcode({
							render: "canvas",
							text: download_url,
							height:130,
							width:130
						});
	            	}
	            });
            });
            $('.close_down').click(function(){
            	del_download_url(rdata.id,false,index,rdata.ps)
            });
        }
    });
}
function del_download_url(id,is_list,index,filename){
	layer.confirm('是否取消分享该文件【'+ filename +'】，是否继续？', { title: '取消分享', closeBtn: 2, icon: 3 }, function (indexs) {
		$.post('/files?action=remove_download_url',{id:id},function(res){
		    if(index) layer.close(index);
		    layer.close(indexs)
		    if(is_list === false) get_download_url_list({},true,function(){
		    	layer.msg(res.msg,{icon:res.status?1:2});
		    });
		});
	});
}

function get_download_url_list(data,is_refresh,callback){
	if(data == undefined) data = {p:1}
    var loadT = layer.msg('正在加载分享列表，请稍后...', {
        icon: 16,
        time: 0,
        shade: 0.3
    });
	$.post('/files?action=get_download_url_list',{p:data.p},function(res){
		layer.close(loadT);
		var _html = '',rdata = res.data;
		for(var i=0;i<rdata.length;i++){
			_html += '<tr><td ><span style="width:230px;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;display: inline-block;" title="'+ rdata[i].ps +'">'+ rdata[i].ps +'</span></td><td ><span style="width:300px;white-space: nowrap;overflow:hidden;text-overflow: ellipsis;display: inline-block;" title="'+ rdata[i].filename +'">'+ rdata[i].filename +'</span></td><td><span >'+ bt.format_data(rdata[i].expire) +'</span></td><td style="text-align:right;"><a href="javascript:;" class="btlink info_down" data-index="'+i +'" data-id="'+ rdata[i].id +'">详情</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink del_down" data-id="'+ rdata[i].id +'" data-index="'+i +'" data-ps="'+ rdata[i].ps +'">关闭</a></td></tr>';
		}
		if(callback) callback();
		if(is_refresh){
			$('.download_url_list').html(_html);
			$('.download_url_page').html(res.page);
			
			return false;
		}
	   var layers = layer.open({
		    type: 1,
		    shift: 5,
		    closeBtn: 2,
		    area: ['850px','580px'],
		    title: '分享列表',
		    content:'<div class="divtable mtb10 download_table" style="padding:5px 10px;">\
		    			<table class="table table-hover" id="download_url">\
		    				<thead><tr><th width="230px">分享名称</th><th width="300px">文件地址</th><th>过期时间</th><th style="text-align:right;width:120px;">操作</th></tr></thead>\
		    				<tbody class="download_url_list">'+ _html +'</tbody>\
		    			</table>\
		    			<div class="page download_url_page">'+ res.page +'</div>\
		    	</div>', 
		    success:function(layers,index){
		    	$('.download_table').on('click','.info_down',function(){
		    		var indexs = $(this).attr('data-index');
		    		set_download_url(rdata[indexs]);
		    	});
				$('.download_table').on('click','.del_down',function(){
		    		var id = $(this).attr('data-id'),_ps = $(this).attr('data-ps');
		    		del_download_url(id,false,false,_ps);
		    	});
		    	$('.download_table .download_url_page').on('click','a',function(e){
		    		var _href =  $(this).attr('href');
		    		var page = _href.replace(/\/files\?action=get_download_url_list\?p=/,'')
		    		get_download_url_list({p:page},true);
		    		return false;
		    	});
		    }
	   });
	});
}



function RClickAll(e) {
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
        .css("z-index", "1")
        .show();
}
function GetPathSize() {
    var path = encodeURIComponent($("#DirPathPlace input").val());
    layer.msg("正在计算，请稍候", { icon: 16, time: 0, shade: [0.3, '#000'] })
    $.post("/files?action=GetDirSize", "path=" + path, function (rdata) {
        layer.closeAll();
        $("#pathSize").text(rdata)
    })
}
$("body").not(".def-log").click(function () {
    $("#rmenu").hide()
});
$("#DirPathPlace input").keyup(function (e) {
    if (e.keyCode == 13) {
        GetFiles($(this).val());
    }
});
function PathPlaceBtn(path) {
    var html = '';
    var title = '';
    path = path.replace('//', '/');
    var Dpath = path;
    if (path == '/') {
        html = '<li><a title="/">' + lan.files.path_root + '</a></li>';
    }
    else {
        Dpath = path.split("/");
        for (var i = 0; i < Dpath.length; i++) {
            title += Dpath[i] + '/';
            Dpath[0] = lan.files.path_root;
            html += '<li><a title="' + title + '">' + Dpath[i] + '</a></li>';
        }
    }
    html = '<div style="width:1200px;height:26px"><ul>' + html + '</ul></div>';
    $("#PathPlaceBtn").html(html);
    $("#PathPlaceBtn ul li a").click(function (e) {
        var Gopath = $(this).attr("title");
        if (Gopath.length > 1) {
            if (Gopath.substr(Gopath.length - 1, Gopath.length) == '/') {
                Gopath = Gopath.substr(0, Gopath.length - 1);
            }
        }
        GetFiles(Gopath);
        e.stopPropagation();
    });
    PathLeft();
}
function PathLeft() {
    var UlWidth = $("#PathPlaceBtn ul").width();
    var SpanPathWidth = $("#PathPlaceBtn").width() - 50;
    var Ml = UlWidth - SpanPathWidth;
    if (UlWidth > SpanPathWidth) {
        $("#PathPlaceBtn ul").css("left", -Ml)
    }
    else {
        $("#PathPlaceBtn ul").css("left", 0)
    }
}

var store_type_index = 0
//删除分类或者文件
function del_files_store(path, obj) {
    var _item = $(obj).parents('tr').data('item')
    var action = '', msg = '';
    var data = {}
    action = 'del_files_store';
    data['path'] = _item.path;
    msg = "是否确定删除路径【" + _item.path + "】?"
    bt.confirm({ msg: msg, title: '提示' }, function () {
        var loading = bt.load();
        bt.send(action, 'files/' + action, data, function (rRet) {
            loading.close();
            if (rRet.status) {
                set_file_store(path)
                GetFiles(getCookie('Path'))
            }
            bt.msg(rRet);
        })
    })
}

function set_file_store(path){
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
                content: "<div class='divtable pd15 style='padding-bottom: 0'><table width='100%' id='stroe_tab_list' class='table table-hover'></table><div class='page sitebackup_page'></div></div>",
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
                    { field: 'path', title: '路径' },
                    {
                        field: 'opt', align: 'right', title: '操作', templet: function (item) {
                            return '<a class="btlink del_file_store" onclick="del_files_store(\'' + path + '\',this)" >删除</a>';
                        }
                    },
                ],
                data: rRet
            });
        }
    })
}



$("#PathPlaceBtn").on("click", function (e) {
    if ($("#DirPathPlace").is(":hidden")) {
        $("#DirPathPlace").css("display", "inline");
        $("#DirPathPlace input").focus();
        $(this).hide();
    } else {
        $("#DirPathPlace").hide();
        $(this).css("display", "inline");
    }
    $(document).one("click", function () {
        $("#DirPathPlace").hide();
        $("#PathPlaceBtn").css("display", "inline");
    });
    e.stopPropagation();
});
$("#DirPathPlace").on("click", function (e) {
    e.stopPropagation();
});
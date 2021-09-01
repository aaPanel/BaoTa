var bt_file = {
    area: [], // Win视图大小
    loadT: null, // 加载load对象
    loadY: null, // 弹窗layer对象，仅二级弹窗
    vscode: null,
    file_table_arry: [], // 选中的文件列表
    timerM: null, // 定时器
    is_update_down_list: true,
    is_recycle: bt.get_cookie('file_recycle_status') || false, // 是否开启回收站
    is_editor: false, // 是否处于重命名、新建编辑状态
    file_header: { 'file_checkbox': 40, 'file_name': 'auto', 'file_accept': 120, 'file_size': 90, 'file_mtime': 145, 'file_ps': 'auto', 'file_operation': 350, 'file_tr': 0, 'file_list_header': 0 },
    file_operating: [], // 文件操作记录，用于前进或后退
    file_pointer: -1, // 文件操作指针，用于指定前进和后退的路径，的指针位数
    file_path: 'C:/', // 文件目录
    file_page_num: bt.get_storage('local', 'showRow') || 100, //每页个数
    file_list: [], // 文件列表
    file_store_list: [], // 文件收藏列表
    file_store_current: 0, //文件收藏当前分类索引
    file_images_list: [], // 文件图片列表
    file_drop: null, // 拖拽上传
    file_present_task: null,
    file_selection_operating: {},
    file_share_list: [],
    scroll_width: (function() {
        
        // 创建一个div元素
        var noScroll, scroll, oDiv = document.createElement('DIV');
        oDiv.style.cssText = 'position:absolute; top:-1000px; width:100px; height:100px; overflow:hidden;';
        noScroll = document.body.appendChild(oDiv).clientWidth;
        oDiv.style.overflowY = 'scroll';
        scroll = oDiv.clientWidth;
        document.body.removeChild(oDiv);
        return noScroll - scroll;
    }()),
    is_mobile: function() {
        if (navigator.userAgent.match(/mobile/i) || /(iPhone|iPad|iPod|iOS|Android)/i.test(navigator.userAgent)) {
            layer.msg(navigator.userAgent.match(/mobile/i), { icon: 2, time: 0 })
            return true;
        }
        return false;
    },
    method_list: {
        GetFileBody: '获取文件内容', // 获取文件内容
        DeleteDir: '删除文件目录',
        DeleteFile: '删除文件',
        GetDiskInfo: ['system', '获取磁盘列表'],
        CheckExistsFiles: '检测同名文件是否存在',
        GetFileAccess: '获取文件权限信息',
        SetFileAccess: lan['public'].config,
        DelFileAccess: '正在删除用户',
        get_path_size: '获取文件目录大小',
        add_files_store_types: '创建收藏夹分类',
        get_files_store: '获取收藏夹列表',
        del_files_store: '取消文件收藏',
        dir_webshell_check: '目录查杀',
        file_webshell_check: '查杀文件',
        get_download_url_list: '获取外链分享列表',
        get_download_url_find: '获取指定外链分享信息',
        create_download_url: '创建外链分享',
        remove_download_url: '取消外链分享',
        add_files_store: '添加文件收藏',
        CopyFile: '复制文件',
        MvFile: '剪切文件',
        SetBatchData: '执行批量操作',
        BatchPaste: '粘贴中'
    },
    file_drop: {
        f_path: null,
        startTime: 0,
        endTime: 0,
        uploadLength: 0, //上传数量
        splitSize: 1024 * 1024 * 2, //文件上传分片大小
        splitEndTime: 0,
        splitStartTime: 0,
        fileSize: 0,
        speedLastTime: 0,
        filesList: [], // 文件列表数组
        errorLength: 0, //上传失败文件数量
        isUpload: true, //上传状态，是否可以上传
        uploadSuspend: [], //上传暂停参数
        isUploadNumber: 800, //限制单次上传数量
        uploadAllSize: 0, // 上传文件总大小
        uploadedSize: 0, // 已上传文件大小
        updateedSizeLast: 0,
        topUploadedSize: 0, // 上一次文件上传大小
        uploadExpectTime: 0, // 预计上传时间
        initTimer: 0, // 初始化计时
        speedInterval: null, //平局速度定时器
        timerSpeed: 0, //速度
        isLayuiDrop: false, //是否是小窗口拖拽
        uploading: false,
        is_webkit: (function() {
            if (navigator.userAgent.indexOf('WebKit') > -1) return true;
            return false;
        })(),
        init: function() {
            if ($('#mask_layer').length == 0) {
                window.UploadFiles = function() { bt_file.file_drop.dialog_view() };
                $("body").append($('<div class="mask_layer" id="mask_layer" style="position:fixed;top:0;left:0;right:0;bottom:0; background:rgba(255,255,255,0.6);border:3px #ccc dashed;z-index:99999999;display:none;color:#999;font-size:40px;text-align:center;overflow:hidden;"><span style="position: absolute;top: 50%;left: 50%;margin-left: -300px;margin-top: -40px;">' + (!this.is_webkit ? '<i style="font-size:20px;font-style:normal;display:block;margin-top:15px;color:red;">当前浏览器暂不支持拖动上传，推荐使用Chrome浏览器或WebKit内核的浏览器。</i>' : '上传文件到当前目录下') + '</span></div>'));
                this.event_relation(document.querySelector('#container'), document, document.querySelector('#mask_layer'));
            }
        },
        // 事件关联 (进入，离开，放下)
        event_relation: function(enter, leave, drop) {
            var that = this,
                obj = Object.keys(arguments);
            for (var item in arguments) {
                if (typeof arguments[item] == "object" && typeof arguments[item].nodeType != 'undefined') {
                    arguments[item] = {
                        el: arguments[item],
                        callback: null
                    }
                }
            }
            leave.el.addEventListener("dragleave", (leave.callback != null) ? leave.callback : function(e) {
                if (e.x == 0 && e.y == 0) $('#mask_layer').hide();
                e.preventDefault();
            }, false);
            enter.el.addEventListener("dragenter", (enter.callback != null) ? enter.callback : function(e) {
                if (e.dataTransfer.items[0].kind == 'string') return false
                $('#mask_layer').show();
                that.isLayuiDrop = false;
                e.preventDefault();
            }, false);
            drop.el.addEventListener("dragover", function(e) { e.preventDefault() }, false);
            drop.el.addEventListener("drop", (enter.callback != null) ? drop.callback : that.ev_drop, false);
        },


        // 事件触发
        ev_drop: function(e) {
            if (e.dataTransfer.items[0].kind == 'string') return false;
            if (!bt_file.file_drop.is_webkit) {
                $('#mask_layer').hide();
                return false;
            }
            e.preventDefault();
            if (bt_file.file_drop.uploading) {
                layer.msg('正在上传文件中，请稍候...');
                return false;
            }
            var items = e.dataTransfer.items,
                time, num = 0;
            loadT = layer.msg('正在获取上传文件信息，请稍候...', { icon: 16, time: 0, shade: .3 });
            bt_file.file_drop.isUpload = true;
            if (items && items.length && items[0].webkitGetAsEntry != null) {
                if (items[0].kind != 'file') return false;
            }
            if (bt_file.file_drop.filesList == null) bt_file.file_drop.filesList = []
            for (var i = bt_file.file_drop.filesList.length - 1; i >= 0; i--) {
                if (bt_file.file_drop.filesList[i].is_upload) bt_file.file_drop.filesList.splice(-i, 1)
            }
            $('#mask_layer').hide();

            function update_sync(s) {
                s.getFilesAndDirectories().then(function(subFilesAndDirs) {
                    return iterateFilesAndDirs(subFilesAndDirs, s.path);
                });
            }
            var iterateFilesAndDirs = function(filesAndDirs, path) {
                if (!bt_file.file_drop.isUpload) return false
                for (var i = 0; i < filesAndDirs.length; i++) {
                    if (typeof(filesAndDirs[i].getFilesAndDirectories) == 'function') {
                        update_sync(filesAndDirs[i])
                    } else {
                        if (num > bt_file.file_drop.isUploadNumber) {
                            bt_file.file_drop.isUpload = false;
                            layer.msg(' ' + bt_file.file_drop.isUploadNumber + '份，无法上传,请压缩后上传!。', { icon: 2, area: '405px' });
                            bt_file.file_drop.filesList = [];
                            clearTimeout(time);
                            return false;
                        }
                        bt_file.file_drop.filesList.push({
                            file: filesAndDirs[i],
                            path: bt.get_file_path(path + '/' + filesAndDirs[i].name).replace('//', '/'),
                            name: filesAndDirs[i].name.replace('//', '/'),
                            icon: bt_file.get_ext_name(filesAndDirs[i].name),
                            size: bt_file.file_drop.to_size(filesAndDirs[i].size),
                            upload: 0, //上传状态,未上传：0、上传中：1，已上传：2，上传失败：-1
                            is_upload: false
                        });
                        bt_file.file_drop.uploadAllSize += filesAndDirs[i].size
                        clearTimeout(time);
                        time = setTimeout(function() {
                            layer.close(loadT);
                            bt_file.file_drop.dialog_view();
                        }, 100);
                        num++;
                    }
                }
            }
            if ('getFilesAndDirectories' in e.dataTransfer) {
                e.dataTransfer.getFilesAndDirectories().then(function(filesAndDirs) {
                    return iterateFilesAndDirs(filesAndDirs, '/');
                });
            }

        },
        // 上传视图
        dialog_view: function(config) {
            var that = this,
                html = '';
            this.f_path = bt_file.file_path;
            if (!$('.file_dir_uploads').length > 0) {
                if (that.filesList == null) that.filesList = []
                for (var i = 0; i < that.filesList.length; i++) {
                    var item = that.filesList[i];
                    html += '<li><div class="fileItem"><span class="filename" title="文件路径:' + (item.path + '/' + item.name).replace('//', '/') + '&#10;文件类型:' + item.file.type + '&#10;文件大小:' + item.size + '"><i class="ico ico-' + item.icon + '"></i>' + (item.path + '/' + item.name).replace('//', '/') + '</span><span class="filesize">' + item.size + '</span><span class="fileStatus">' + that.is_upload_status(item.upload) + '</span></div><div class="fileLoading"></div></li>';
                }
                var is_show = that.filesList.length > 11;
                layer.open({
                    type: 1,
                    closeBtn: 1,
                    maxmin: true,
                    area: ['650px', '605px'],
                    btn: ['开始上传', '取消上传'],
                    title: '上传文件到【' + bt.get_cookie('Path') + '】--- 支持断点续传',
                    skin: 'file_dir_uploads',
                    content: '<div style="padding:15px 15px 10px 15px;"><div class="upload_btn_groud"><div class="btn-group"><button type="button" class="btn btn-primary btn-sm upload_file_btn">上传文件</button><button type="button" class="btn btn-primary  btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span class="caret"></span><span class="sr-only">Toggle Dropdown</span></button><ul class="dropdown-menu"><li><a href="#" data-type="file">上传文件</a></li><li><a href="#" data-type="dir">上传目录</a></li></ul></div><div class="file_upload_info" style="display:none;"><span>总进度&nbsp;<i class="uploadProgress"></i>,正在上传&nbsp;<i class="uploadNumber"></i>,</span><span style="display:none">上传失败&nbsp;<i class="uploadError"></i></span><span>上传速度&nbsp;<i class="uploadSpeed">获取中</i>,</span><span>预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span><i></i></div></div><div class="upload_file_body ' + (html == '' ? 'active' : '') + '">' + (html != '' ? ('<ul class="dropUpLoadFileHead" style="padding-right:' + (is_show ? '15' : '0') + 'px"><li class="fileTitle"><span class="filename">文件名</span><span class="filesize">文件大小</span><span class="fileStatus">上传状态</span></li></ul><ul class="dropUpLoadFile list-list">' + html + '</ul>') : '<span>' + (!that.is_webkit ? '<i style="display: block;font-style: normal;margin-top: 10px;color: red;font-size: 17px;">当前浏览器暂不支持拖动上传，推荐使用Chrome浏览器或WebKit内核的浏览器。</i>' : '请将需要上传的文件拖到此处') + '</span>') + '</div></div>',
                    success: function() {
                        $('#mask_layer').hide();
                        $('.file_dir_uploads .layui-layer-max').hide();
                        $('.upload_btn_groud .upload_file_btn').click(function() { $('.upload_btn_groud .dropdown-menu [data-type=file]').click() });
                        $('.upload_btn_groud .dropdown-menu a').click(function() {
                            var type = $(this).attr('data-type');
                            $('<input type="file" multiple="true" autocomplete="off" ' + (type == 'dir' ? 'webkitdirectory=""' : '') + ' />').change(function(e) {
                                var files = e.target.files,
                                    arry = [];
                                for (var i = 0; i < files.length; i++) {
                                    var config = {
                                        file: files[i],
                                        path: bt.get_file_path('/' + files[i].webkitRelativePath).replace('//', '/'),
                                        icon: bt_file.get_ext_name(files[i].name),
                                        name: files[i].name.replace('//', '/'),
                                        size: that.to_size(files[i].size),
                                        upload: 0, //上传状态,未上传：0、上传中：1，已上传：2，上传失败：-1
                                        is_upload: true
                                    }
                                    that.filesList.push(config);
                                    bt_file.file_drop.uploadAllSize += files[i].size
                                }
                                that.dialog_view(that.filesList);
                            }).click();
                        });
                        var el = '';
                        that.event_relation({
                            el: $('.upload_file_body')[0],
                            callback: function(e) {
                                if ($(this).hasClass('active')) {
                                    $(this).css('borderColor', '#4592f0').find('span').css('color', '#4592f0');
                                }
                            }
                        }, {
                            el: $('.upload_file_body')[0],
                            callback: function(e) {
                                if ($(this).hasClass('active')) {
                                    $(this).removeAttr('style').find('span').removeAttr('style');
                                }
                            }
                        }, {
                            el: $('.upload_file_body')[0],
                            callback: function(e) {
                                var active = $('.upload_file_body');
                                if (active.hasClass('active')) {
                                    active.removeAttr('style').find('span').removeAttr('style');
                                }
                                that.ev_drop(e);
                                that.isLayuiDrop = true;
                            }
                        });
                    },
                    yes: function(index, layero) {
                        if (!that.uploading) {
                            if (that.filesList.length == 0) {
                                layer.msg('请选择上传文件', { icon: 0 });
                                return false;
                            }
                            $('.layui-layer-btn0').css({ 'cursor': 'no-drop', 'background': '#5c9e69' }).attr('data-upload', 'true').text('上传中');
                            that.upload_file();
                            that.initTimer = new Date();
                            that.uploading = true;
                            //that.get_timer_speed();
                        }
                    },
                    btn2: function(index, layero) {
                        if (that.uploading) {
                            layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？', { title: '取消上传文件', icon: 0 }, function(indexs) {
                                layer.close(index);
                                layer.close(indexs);
                            });
                            return false;
                        } else {
                            layer.close(index);
                        }
                    },
                    cancel: function(index, layero) {
                        if (that.uploading) {
                            layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？', { title: '取消上传文件', icon: 0 }, function(indexs) {
                                layer.close(index);
                                layer.close(indexs);
                            });
                            return false;
                        } else {
                            layer.close(index);
                        }
                    },
                    end: function() {
                        // GetFiles(bt.get_cookie('Path'));
                        that.clear_drop_stauts(true);
                    },
                    min: function() {
                        $('.file_dir_uploads .layui-layer-max').show();
                        $('#layui-layer-shade' + $('.file_dir_uploads').attr('times')).fadeOut();
                    },
                    restore: function() {
                        $('.file_dir_uploads .layui-layer-max').hide();
                        $('#layui-layer-shade' + $('.file_dir_uploads').attr('times')).fadeIn();
                    }
                });
            } else {
                if (config == undefined && !that.isLayuiDrop) return false;
                if (that.isLayuiDrop) config = that.filesList;
                $('.upload_file_body').html('<ul class="dropUpLoadFileHead" style="padding-right:' + (config.length > 11 ? '15' : '0') + 'px"><li class="fileTitle"><span class="filename">文件名</span><span class="filesize">文件大小</span><span class="fileStatus">上传状态</span></li></ul><ul class="dropUpLoadFile list-list"></ul>').removeClass('active');
                if (Array.isArray(config)) {
                    for (var i = 0; i < config.length; i++) {
                        var item = config[i];
                        html += '<li><div class="fileItem"><span class="filename" title="文件路径:' + item.path + '/' + item.name + '&#10;文件类型:' + item.file.type + '&#10;文件大小:' + item.size + '"><i class="ico ico-' + item.icon + '"></i>' + (item.path + '/' + item.name).replace('//', '/') + '</span><span class="filesize">' + item.size + '</span><span class="fileStatus">' + that.is_upload_status(item.upload) + '</span></div><div class="fileLoading"></div></li>';
                    }
                    $('.dropUpLoadFile').append(html);
                } else {
                    $('.dropUpLoadFile').append('<li><div class="fileItem"><span class="filename" title="文件路径:' + (config.path + '/' + config.name).replace('//', '/') + '&#10;文件类型:' + config.type + '&#10;文件大小:' + config.size + '"><i class="ico ico-' + config.icon + '"></i>' + (config.path + '/' + config.name).replace('//', '/') + '</span><span class="filesize">' + config.size + '</span><span class="fileStatus">' + that.is_upload_status(config.upload) + '</span></div><div class="fileLoading"></div></li>');
                }

            }
        },
        // 上传单文件状态
        is_upload_status: function(status, val) {
            if (val === undefined) val = ''
            switch (status) {
                case -1:
                    return '<span class="upload_info upload_error" title="上传失败' + (val != '' ? ',' + val : '') + '">上传失败' + (val != '' ? ',' + val : '') + '</span>';
                    break;
                case 0:
                    return '<span class="upload_info upload_primary">等待上传</span>';
                    break;
                case 1:
                    return '<span class="upload_info upload_success">上传成功</span>';
                    break;
                case 2:
                    return '<span class="upload_info upload_warning">上传中' + val + '</span>';
                    break;
                case 3:
                    return '<span class="upload_info upload_success">已暂停</span>';
                    break;
            }
        },
        // 设置上传实时反馈视图
        set_upload_view: function(index, config) {
            var item = $('.dropUpLoadFile li:eq(' + index + ')'),
                that = this;
            var file_info = $('.file_upload_info');
            if ($('.file_upload_info .uploadProgress').length == 0) {
                $('.file_upload_info').html('<span>总进度&nbsp;<i class="uploadProgress"></i>,正在上传&nbsp;<i class="uploadNumber"></i>,</span><span style="display:none">上传失败&nbsp;<i class="uploadError"></i></span><span>上传速度&nbsp;<i class="uploadSpeed">获取中</i>,</span><span>预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span><i></i>');
            }
            file_info.show().prev().hide().parent().css('paddingRight', 0);
            if (that.errorLength > 0) file_info.find('.uploadError').text('(' + that.errorLength + '份)').parent().show();
            file_info.find('.uploadNumber').html('(' + that.uploadLength + '/' + that.filesList.length + ')');
            file_info.find('.uploadProgress').html(((that.uploadedSize / that.uploadAllSize) * 100).toFixed(2) + '%');
            if (config.upload === 1 || config.upload === -1) {
                that.filesList[index].is_upload = true;
                that.uploadLength += 1;
                item.find('.fileLoading').css({ 'width': '100%', 'opacity': '.5', 'background': config.upload == -1 ? '#ffadad' : '#20a53a21' });
                item.find('.filesize').text(config.size);
                item.find('.fileStatus').html(that.is_upload_status(config.upload, (config.upload === 1 ? ('(耗时:' + that.diff_time(that.startTime, that.endTime) + ')') : config.errorMsg)));
                item.find('.fileLoading').fadeOut(500, function() {
                    $(this).remove();
                    var uploadHeight = $('.dropUpLoadFile');
                    if (uploadHeight.length == 0) return false;
                    if (uploadHeight[0].scrollHeight > uploadHeight.height()) {
                        uploadHeight.scrollTop(uploadHeight.scrollTop() + 40);
                    }
                });
            } else {
                item.find('.fileLoading').css('width', config.percent);
                item.find('.filesize').text(config.upload_size + '/' + config.size);
                item.find('.fileStatus').html(that.is_upload_status(config.upload, '(' + config.percent + ')'));
            }
        },
        // 清除上传状态
        clear_drop_stauts: function(status) {
            var time = new Date(),
                that = this;
            if (!status) {
                try {
                    var s_peed = bt_file.file_drop.to_size(bt_file.file_drop.uploadedSize / ((time.getTime() - bt_file.file_drop.initTimer.getTime()) / 1000))
                    $('.file_upload_info').html('<span>上传成功 ' + this.uploadLength + '个文件,' + (this.errorLength > 0 ? ('上传失败 ' + this.errorLength + '个文件，') : '') + '耗时' + this.diff_time(this.initTimer, time) + ',平均速度 ' + s_peed + '/s</span>').append($('<i class="ico-tips-close"></i>').click(function() {
                        $('.file_upload_info').hide().prev().show();
                    }));
                } catch (e) {

                }
            }
            $('.layui-layer-btn0').removeAttr('style data-upload').text('开始上传');
            $.extend(bt_file.file_drop, {
                startTime: 0,
                endTime: 0,
                uploadLength: 0, //上传数量
                splitSize: 1024 * 1024 * 2, //文件上传分片大小
                filesList: [], // 文件列表数组
                errorLength: 0, //上传失败文件数量
                isUpload: false, //上传状态，是否可以上传
                isUploadNumber: 800, //限制单次上传数量
                uploadAllSize: 0, // 上传文件总大小
                uploadedSize: 0, // 已上传文件大小
                topUploadedSize: 0, // 上一次文件上传大小
                uploadExpectTime: 0, // 预计上传时间
                initTimer: 0, // 初始化计时
                speedInterval: null, //平局速度定时器
                timerSpeed: 0, //速度
                uploading: false
            });
            clearInterval(that.speedInterval);
        },
        // 上传文件,文件开始字段，文件编号
        upload_file: function(fileStart, index) {
            if (fileStart == undefined && this.uploadSuspend.length == 0) fileStart = 0, index = 0;
            if (this.filesList.length === index) {
                clearInterval(this.speedInterval);
                this.clear_drop_stauts();
                bt_file.reader_file_list({ path: bt_file.file_path, is_operating: false });
                return false;
            }
            var that = this;
            that.splitEndTime = new Date().getTime()
            that.get_timer_speed()

            that.splitStartTime = new Date().getTime()
            var item = this.filesList[index],
                fileEnd = '';
            if (item == undefined) return false;
            fileEnd = Math.min(item.file.size, fileStart + this.splitSize),
                that.fileSize = fileEnd - fileStart
            form = new FormData();
            if (fileStart == 0) {
                that.startTime = new Date();
                item = $.extend(item, { percent: '0%', upload: 2, upload_size: '0B' });
            }
            form.append("f_path", this.f_path + item.path);
            form.append("f_name", item.name);
            form.append("f_size", item.file.size);
            form.append("f_start", fileStart);
            form.append("blob", item.file.slice(fileStart, fileEnd));
            that.set_upload_view(index, item);
            $.ajax({
                url: '/files?action=upload',
                type: "POST",
                data: form,
                async: true,
                processData: false,
                contentType: false,
                success: function(data) {
                    if (typeof(data) === "number") {
                        that.set_upload_view(index, $.extend(item, { percent: (((data / item.file.size) * 100).toFixed(2) + '%'), upload: 2, upload_size: that.to_size(data) }));
                        if (fileEnd != data) {
                            that.uploadedSize += data;
                        } else {
                            that.uploadedSize += parseInt(fileEnd - fileStart);
                        }

                        that.upload_file(data, index);
                    } else {
                        if (data.status) {
                            that.endTime = new Date();
                            that.uploadedSize += parseInt(fileEnd - fileStart);
                            that.set_upload_view(index, $.extend(item, { upload: 1, upload_size: item.size }));
                            that.upload_file(0, index += 1);
                        } else {
                            that.set_upload_view(index, $.extend(item, { upload: -1, errorMsg: data.msg }));
                            that.errorLength++;
                        }
                    }

                },
                error: function(e) {
                    if (that.filesList[index].req_error === undefined) that.filesList[index].req_error = 1
                    if (that.filesList[index].req_error > 2) {
                        that.set_upload_view(index, $.extend(that.filesList[index], { upload: -1, errorMsg: e.statusText == 'error' ? '网络中断' : e.statusText }));
                        that.errorLength++;
                        that.upload_file(fileStart, index += 1)
                        return false;
                    }
                    that.filesList[index].req_error += 1;
                    that.upload_file(fileStart, index)


                }
            });
        },
        // 获取上传速度
        get_timer_speed: function(speed) {
            var done_time = new Date().getTime()
            if (done_time - this.speedLastTime > 1000) {
                var that = this,
                    num = 0;
                if (speed == undefined) speed = 200
                var s_time = (that.splitEndTime - that.splitStartTime) / 1000;
                that.timerSpeed = (that.fileSize / s_time).toFixed(2)
                that.updateedSizeLast = that.uploadedSize
                if (that.timerSpeed < 2) return;

                $('.file_upload_info .uploadSpeed').text(that.to_size(isNaN(that.timerSpeed) ? 0 : that.timerSpeed) + '/s');
                var estimateTime = that.time(parseInt(((that.uploadAllSize - that.uploadedSize) / that.timerSpeed) * 1000))
                if (!isNaN(that.timerSpeed)) $('.file_upload_info .uploadEstimate').text(estimateTime.indexOf('NaN') == -1 ? estimateTime : '0秒');
                this.speedLastTime = done_time;
            }
        },
        time: function(date) {
            var hours = Math.floor(date / (60 * 60 * 1000));
            var minutes = Math.floor(date / (60 * 1000));
            var seconds = parseInt((date % (60 * 1000)) / 1000);
            var result = seconds + '秒';
            if (minutes > 0) {
                result = minutes + "分钟" + seconds + '秒';
            }
            if (hours > 0) {
                result = hours + '小时' + Math.floor((date - (hours * (60 * 60 * 1000))) / (60 * 1000)) + "分钟";
            }
            return result
        },
        diff_time: function(start_date, end_date) {
            var diff = end_date.getTime() - start_date.getTime();
            var minutes = Math.floor(diff / (60 * 1000));
            var leave3 = diff % (60 * 1000);
            var seconds = leave3 / 1000
            var result = seconds.toFixed(minutes > 0 ? 0 : 2) + '秒';
            if (minutes > 0) {
                result = minutes + "分" + seconds.toFixed(0) + '秒'
            }
            return result
        },
        to_size: function(a) {
            var d = [" B", " KB", " MB", " GB", " TB", " PB"];
            var e = 1024;
            for (var b = 0; b < d.length; b += 1) {
                if (a < e) {
                    var num = (b === 0 ? a : a.toFixed(2)) + d[b];
                    return (!isNaN((b === 0 ? a : a.toFixed(2))) && typeof num != 'undefined') ? num : '0B';
                }
                a /= e
            }
        }
    },
    init: function() {
        if (bt.get_cookie('rank') == undefined || bt.get_cookie('rank') == null || bt.get_cookie('rank') == 'a' || bt.get_cookie('rank') == 'b') {
            bt.set_cookie('rank', 'list');
        }
        this.area = [window.innerWidth, window.innerHeight];
        this.file_path = bt.get_cookie('Path');
        this.event_bind(); // 事件绑定
        this.reader_file_list({ is_operating: true }); // 渲染文件列表
        this.render_file_disk_list(); // 渲染文件磁盘列表
        this.file_drop.init(); // 初始化文件上传
        this.set_file_table_width(); // 设置表格宽度
    },
    // 事件绑定
    event_bind: function() {
        var that = this;
        // 窗口大小限制
        $(window).resize(function(ev) {
            if ($(this)[0].innerHeight != that.area[1]) {
                that.area[1] = $(this)[0].innerHeight;
                that.set_file_view();
            }
            if ($(this)[0].innerWidth != that.area[0]) {
                that.area[0] = $(this)[0].innerWidth;
                that.set_dir_view_resize(); //目录视图
                that.set_menu_line_view_resize(); //菜单栏视图
                that.set_file_table_width(); //设置表头宽度
            }
        }).keydown(function(e) { // 全局按键事件
            e = window.event || e;
            var keyCode = e.keyCode,
                tagName = e.target.tagName.toLowerCase();
            if (!that.is_editor) { //非编辑模式
                // Ctrl + v   粘贴事件
                if (e.ctrlKey && keyCode == 86 && tagName != 'input' && tagName != 'textarea') {
                    that.paste_file_or_dir();
                }
                // 退格键
                if (keyCode == 8 && tagName !== 'input' && tagName !== 'textarea' && typeof $(e.target).attr('data-backspace') === "undefined") {
                    $('.file_path_upper').click()
                }
            }
        });
        $('.search_path_views').find('.file_search_checked').unbind('click').click(function() {
                if ($(this).hasClass('active')) {
                    $(this).removeClass('active')
                } else {
                    $(this).addClass('active');
                }
            })
            // 搜索按钮
        $('.search_path_views').on('click', '.path_btn', function(e) {
            var _obj = { path: that.file_path, search: $('.file_search_input').val() };
            if ($('#search_all').hasClass('active')) _obj['all'] = 'True'
            that.loadT = bt.load('正在搜索文件中,请稍候...');
            that.reader_file_list(_obj, function(res) {
                if (!res.msg) {
                    that.loadT.close();
                }
            })
            e.stopPropagation();
        })
        $('.search_path_views').on('click', '.file_search_config label', function(e) {
            $(this).prev().click();
        });
        // 搜索框（获取焦点、回车提交）
        $('.search_path_views .file_search_input').on('focus keyup', function(e) {
                e = e || window.event;
                var _obj = { path: that.file_path, search: $(this).val() };
                switch (e.type) {
                    case 'keyup':
                        var isCheck = $('.file_search_checked').hasClass('active')
                        if (isCheck) _obj['all'] = 'True'
                        if (e.keyCode != 13 && e.type == 'keyup') return false;
                        that.loadT = bt.load('正在搜索文件中,请稍候...');
                        that.reader_file_list(_obj, function(res) {
                            if (!res.msg) {
                                that.loadT.close();
                            }
                        })
                        break;
                }
                e.stopPropagation();
                e.preventDefault();
            })
            // 文件路径事件（获取焦点、失去焦点、回车提交）
        $('.file_path_input .path_input').on('focus blur keyup', function(e) {
            e = e || window.event;
            var path = $(this).attr('data-path'),
                _this = $(this);
            switch (e.type) {
                case 'focus':
                    $(this).addClass('focus').val(path).prev().hide();
                    break;
                case 'blur':
                    $(this).removeClass('focus').val('').prev().show();
                    break;
                case 'keyup':
                    if (e.keyCode != 13 && e.type == 'keyup') return false;
                    if ($(this).data('path') != $(this).val()) {
                        that.reader_file_list({ path: that.path_check($(this).val()), is_operating: true }, function(res) {
                            if (res.status === false) {
                                _this.val(path);
                            } else {
                                _this.val(that.path_check(res.PATH));
                                _this.blur().prev().show();
                            }
                        });
                    }
                    break;
            }
            e.stopPropagation();
        });
        // 文件路径点击跳转
        $('.file_path_input .file_dir_view').on('click', '.file_dir', function() {
            that.reader_file_list({ path: $(this).attr('title'), is_operating: true });
        });

        // 文件操作前进或后退
        $('.forward_path span').click(function() {
            var index = $(this).index(),
                path = '';
            if (!$(this).hasClass('active')) {
                switch (index) {
                    case 0:
                        that.file_pointer = that.file_pointer - 1
                        path = that.file_operating[that.file_pointer];
                        break;
                    case 1:
                        that.file_pointer = that.file_pointer + 1
                        path = that.file_operating[that.file_pointer];
                        break;
                }
                that.reader_file_list({ path: path, is_operating: false });
            }
        });

        //展示已隐藏的目录
        $('.file_path_input .file_dir_view').on('click', '.file_dir_omit', function(e) {
            var _this = this,
                new_down_list = $(this).children('.nav_down_list');
            $(this).addClass('active');
            new_down_list.addClass('show');
            $(document).one('click', function() {
                $(_this).removeClass('active');
                new_down_list.removeClass('show');
                e.stopPropagation();
            });
            e.stopPropagation();
        });
        //目录获取子级所有文件夹(箭头图标)
        $('.file_path_input .file_dir_view').on('click', '.file_dir_item i', function(e) {
                var children_list = $(this).siblings('.nav_down_list')
                var _path = $(this).siblings('span').attr('title');
                children_list.show().parent().siblings().find('.nav_down_list').removeAttr('style');
                that.render_path_down_list(children_list, _path);
                $(document).one('click', function() {
                    children_list.removeAttr('style');
                    e.stopPropagation();
                });
                e.stopPropagation();
            })
            //目录子级文件路径跳转（下拉）
        $('.file_path_input .file_dir_view').on('click', '.file_dir_item .nav_down_list li', function(e) {
            that.reader_file_list({ path: $(this).data('path'), is_operating: true });
        });
        // 文件上一层
        $('.file_path_upper').click(function() {
            that.reader_file_list({ path: that.retrun_prev_path(that.file_path), is_operating: true });
        });

        // 文件刷新
        $('.file_path_refresh').click(function() {
            that.reader_file_list({ path: that.file_path }, function(res) {
                if (!res.msg) layer.msg('刷新成功')
            });
        });

        // 上传
        $('.upload_file').on('click', function(e) {
            that.file_drop.dialog_view();
        });
        // 下载
        $('.upload_download').on('click', function(e) {
            that.open_download_view();
        });

        // 新建文件夹或文件
        $('.file_nav_view .create_file_or_dir li').on('click', function(e) {
            if($(this).index() > 1){
                that.file_groud_event({open:'soft_link'});
                return false;
            }
            var type = $(this).data('type'), nav_down_list = $('.create_file_or_dir .nav_down_list');
                nav_down_list.css({
                'display': function() {
                    setTimeout(function() { nav_down_list.removeAttr('style') }, 100)
                    return 'none';
                }});
            if (!that.is_editor) {
                that.is_editor = true;
                // 首位创建“新建文件夹、文件”
                $('.file_list_content').prepend('<div class="file_tr createModel active">' +
                    '<div class="file_td file_checkbox"></div>' +
                    '<div class="file_td file_name">' +
                    '<div class="file_ico_type"><i class="file_icon ' + (type == 'newBlankDir' ? 'file_folder' : '') + '"></i></div>' +
                    (bt.get_cookie('rank') == 'icon' ? '<span class="file_title file_' + (type == 'newBlankDir' ? 'dir' : 'file') + '_status"><textarea name="createArea" onfocus="select()">' + (type == 'newBlankDir' ? '新建文件夹' : '新建文件') + '</textarea></span>' : '<span class="file_title file_' + (type == 'newBlankDir' ? 'dir' : 'file') + '_status"><input name="createArea" value="' + (type == 'newBlankDir' ? '新建文件夹' : '新建文件') + '" onfocus="select()" type="text"></span>') +
                    '</div>' +
                    '</div>'
                )

                // 输入增高、回车、焦点、失去焦点
                $((bt.get_cookie('rank') == 'icon' ? 'textarea' : 'input') + '[name=createArea]').on('input', function() {
                    if (bt.get_cookie('rank') == 'icon') {
                        this.style.height = 'auto';
                        this.style.height = this.scrollHeight + "px";
                    }
                }).keyup(function(e) {
                    if (e.keyCode == 13) $(this).blur();
                }).blur(function(e) {
                    var _val = $(this).val().replace(/[\r\n]/g, "");
                    if (that.match_unqualified_string(_val)) return layer.msg('名称不能含有 /\\:*?"<>|符号', { icon: 2 })
                    if (_val == '') _val = (type == 'newBlankDir' ? '新建文件夹' : '新建文件');
                    setTimeout(function() { //延迟处理，防止Li再次触发
                        that.create_file_req({ type: (type == 'newBlankDir' ? 'folder' : 'file'), path: that.file_path + '/' + _val }, function(res) {
                            if (res.status) that.reader_file_list({ path: that.file_path });
                            layer.msg(res.msg, { icon: res.status ? 1 : 2 });
                        })
                        $('.createModel').remove(); // 删除模板
                        that.is_editor = false;
                    }, 300)
                    e.preventDefault();
                }).focus();
            } else {
                return false;
            }
            e.stopPropagation();
            e.preventDefault();
        })
            // 收藏夹列表跳转
        $('.file_nav_view .favorites_file_path ul').on('click', 'li', function(e) {
                var _href = $(this).data('path'),
                    _type = $(this).data('type'),
                    nav_down_list = $('.favorites_file_path .nav_down_list');
                if (_type == 'dir') {
                    that.reader_file_list({ path: _href, is_operating: true });
                } else {
                    if ($(this).data('null') != undefined) return false;
                    var _file = $(this).attr('title').split('.'),
                        _fileT = _file[_file.length - 1],
                        _fileE = that.determine_file_type(_fileT);
                    switch (_fileE) {
                        case 'text':
                            openEditorView(0, _href)
                            break;
                        case 'video':
                            that.open_video_play(_href);
                            break;
                        case 'images':
                            that.open_images_preview({ filename: $(this).attr('title'), path: _href });
                            break;
                        default:
                            that.reader_file_list({ path: that.retrun_prev_path(_href), is_operating: true });
                            break;
                    }
                }
                //点击隐藏
                nav_down_list.css({
                    'display': function() {
                        setTimeout(function() { nav_down_list.removeAttr('style') }, 100)
                        return 'none';
                    }
                });
                e.stopPropagation();
                e.preventDefault();
            })
            // 打开终端
        $('.terminal_view').on('click', function() {
            web_shell();
        });

        // 分享列表
        $('.share_file_list').on('click', function() {
                that.open_share_view();
            })
            // 打开硬盘挂载的目录
        $('.mount_disk_list').on('click', '.nav_btn', function() {
            var path = $(this).data('menu');
            that.reader_file_list({ path: path, is_operating: true });
        });
        // 硬盘磁盘挂载
        $('.mount_disk_list').on('click', '.nav_down_list li', function() {
            var path = $(this).data('disk'),
                disk_list = $('.mount_disk_list.thezoom .nav_down_list');
            disk_list.css({
                'display': function() {
                    setTimeout(function() { disk_list.removeAttr('style') }, 100)
                    return 'none';
                }
            });
            that.reader_file_list({ path: path, is_operating: true });
        });

        // 回收站
        $('.file_nav_view').on('click', '.recycle_bin', function(ev) {
                that.recycle_bin_view();
                ev.stopPropagation();
                ev.preventDefault();
            })
            // 批量操作
        $('.file_nav_view .multi').on('click', '.nav_btn_group', function(ev) {
            var batch_type = $(this).data('type');
            if (typeof batch_type != 'undefined') that.batch_file_manage(batch_type);
            ev.stopPropagation();
            ev.preventDefault();
        });
        // 批量操作
        $('.file_nav_view .multi').on('click', '.nav_btn_group li', function(ev) {
            var batch_type = $(this).data('type');
            that.batch_file_manage(batch_type);
            ev.stopPropagation();
            ev.preventDefault();
        });
        // 全部粘贴按钮
        $('.file_nav_view').on('click', '.file_all_paste', function() {
            that.paste_file_or_dir();
        })

        // 表头点击事件，触发排序字段和排序方式
        $('.file_list_header').on('click', '.file_name,.file_size,.file_mtime,.file_accept,.file_user', function(e) {
            var _tid = $(this).attr('data-tid'),
                _reverse = $(this).find('.icon_sort').hasClass('active'),
                _active = $(this).hasClass('active');
            if (!$(this).find('.icon_sort').hasClass('active') && $(this).hasClass('active')) {
                $(this).find('.icon_sort').addClass('active');
            } else {
                $(this).find('.icon_sort').removeClass('active');
            }
            $(this).addClass('active').siblings().removeClass('active').find('.icon_sort').removeClass('active').empty();
            $(this).find('.icon_sort').html('<i class="iconfont icon-xiala"></i>');
            if (!_active) _reverse = true
            bt.set_cookie('files_sort', _tid);
            bt.set_cookie('name_reverse', _reverse ? 'True' : 'False');
            that.reader_file_list({ reverse: _reverse ? 'True' : 'False', sort: _tid });
            return false;
        });

        // 设置排序显示
        $('.file_list_header .file_th').each(function(index, item) {
            var files_sort = bt.get_cookie('files_sort'),
                name_reverse = bt.get_cookie('name_reverse');
            if ($(this).attr('data-tid') === files_sort) {
                $(this).addClass('active').siblings().removeClass('active').find('.icon_sort').removeClass('active').empty();
                $(this).find('.icon_sort').html('<i class="iconfont icon-xiala"></i>');
                if (name_reverse === 'False') $(this).find('.icon_sort').addClass('active');
            }
        });

        // 全选选中文件
        $('.file_list_header .file_check').on('click', function(e) {
            var checkbox = parseInt($(this).data('checkbox'));
            switch (checkbox) {
                case 0:
                    $(this).addClass('active').removeClass('active_2').data('checkbox', 1);
                    $('.file_list_content .file_tr').addClass('active').removeClass('active_2');
                    $('.nav_group.multi').removeClass('hide');
                    $('.file_menu_tips').addClass('hide');
                    that.file_table_arry = that.file_list.slice();
                    break;
                case 2:
                    $(this).addClass('active').removeClass('active_2').data('checkbox', 1);
                    $('.file_list_content .file_tr').addClass('active');
                    $('.nav_group.multi').removeClass('hide');
                    $('.file_menu_tips').addClass('hide');
                    that.file_table_arry = that.file_list.slice();
                    break;
                case 1:
                    $(this).removeClass('active active_2').data('checkbox', 0);
                    $('.file_list_content .file_tr').removeClass('active');
                    $('.nav_group.multi').addClass('hide');
                    $('.file_menu_tips').removeClass('hide');
                    that.file_table_arry = [];
                    break;
            }
            that.calculate_table_active();
        });
        // 文件勾选
        $('.file_list_content').on('click', '.file_checkbox', function(e) { //列表选择
            var _tr = $(this).parents('.file_tr'),
                index = _tr.data('index'),
                filename = _tr.data('filename');
            if (_tr.hasClass('active')) {
                _tr.removeClass('active');
                that.remove_check_file(that.file_table_arry, 'filename', filename);
            } else {
                _tr.addClass('active');
                _tr.attr('data-filename', that.file_list[index]['filename']);
                that.file_table_arry.push(that.file_list[index]);
            }
            that.calculate_table_active();
            e.stopPropagation();
        });


        // 文件列表滚动条事件
        $('.file_list_content').scroll(function(e) {
            if ($(this).scrollTop() == ($(this)[0].scrollHeight - $(this)[0].clientHeight)) {
                $(this).prev().css('opacity', 1);
                $(this).next().css('opacity', 0);
            } else if ($(this).scrollTop() > 0) {
                $(this).prev().css('opacity', 1);
            } else if ($(this).scrollTop() == 0) {
                $(this).prev().css('opacity', 0);
                $(this).next().css('opacity', 1);
            }
        });

        // 选中文件
        $('.file_table_view .file_list_content').on('click', '.file_tr', function(e) {
            if ($(e.target).hasClass('foo_menu_title') || $(e.target).parents().hasClass('foo_menu_title')) return true;
            $(this).addClass('active').siblings().removeClass('active');
            that.file_table_arry = [that.file_list[$(this).data('index')]];
            that.calculate_table_active();
            e.stopPropagation();
            e.preventDefault();
        });

        // 打开文件的分享、收藏状态
        $('.file_table_view .file_list_content').on('click', '.file_name .iconfont', function(e) {
            var file_tr = $(this).parents('.file_tr'),
                index = file_tr.data('index'),
                data = that.file_list[index];
            data['index'] = index
            if ($(this).hasClass('icon-share1')) { that.info_file_share(data); }
            if ($(this).hasClass('icon-favorites')) { that.cancel_file_favorites(data); }
            e.stopPropagation();
        });
        // 打开文件夹和文件 --- 双击
        $('.file_table_view .file_list_content').on('dblclick', '.file_tr', function(e) {
            var index = $(this).data('index'),
                data = that.file_list[index];
            if (
                $(e.target).hasClass('file_check') ||
                $(e.target).parents('.foo_menu').length > 0 ||
                $(e.target).hasClass('set_file_ps') ||
                that.is_editor
            ) return false;
            if (data.type == 'dir') {
                if (data['filename'] == 'Recycle_bin') return that.recycle_bin_view();
                that.reader_file_list({ path: that.file_path + '/' + data['filename'], is_operating: true });
            } else {
                switch (data.open_type) {
                    case 'text':
                        openEditorView(0, data.path)
                        break;
                    case 'video':
                        that.open_video_play(data);
                        break;
                    case 'images':
                        that.open_images_preview(data);
                        break;
                    case 'compress':
                        that.unpack_file_to_path(data)
                        break;
                }
            }
            e.stopPropagation();
            e.preventDefault();
        });

        // 打开文件夹或文件 --- 文件名单击
        $('.file_table_view .file_list_content').on('click', '.file_title i,.file_ico_type .file_icon', function(e) {
            var file_tr = $(this).parents('.file_tr'),
                index = file_tr.data('index'),
                data = that.file_list[index];
            if (data.type == 'dir') {
                if (data['filename'] == 'Recycle_bin') return that.recycle_bin_view();
                that.reader_file_list({ path: that.file_path + '/' + data['filename'], is_operating: true });
            } else {
                layer.msg(data.open_type == 'compress' ? '双击解压文件' : '双击文件编辑');
            }
            e.stopPropagation();
            e.preventDefault();
        });

        // 禁用浏览器右键菜单
        $('.file_list_content').on('contextmenu', function(ev) {
            if ($(ev.target).attr('name') == 'createArea' || $(ev.target).attr('name') == 'rename_file_input') {
                return true
            } else {
                return false;
            }
        });

        // 禁用菜单右键默认浏览器右键菜单
        $('.selection_right_menu').on('contextmenu', function(ev) {
            return false;
        });

        // 文件夹和文件鼠标右键
        $('.file_list_content').on('mousedown', '.file_tr', function(ev) {
            if (ev.which === 1 && ($(ev.target).hasClass('foo_menu_title') || $(ev.target).parents().hasClass('foo_menu_title'))) {
                that.render_file_groud_menu(ev, this);
                $(ev.target).parent().addClass('foo_menu_click');
                $(this).siblings().find('.foo_menu').removeClass('foo_menu_click');
                $(this).addClass('active').siblings().removeClass('active');
            } else if (ev.which === 3 && !that.is_editor) {
                if (that.file_table_arry.length > 1) {
                    that.render_files_multi_menu(ev);
                } else {
                    that.render_file_groud_menu(ev, this);
                    $('.content_right_menu').removeAttr('style');
                    $(this).addClass('active').siblings().removeClass('active');
                }
            } else { return true }
            ev.stopPropagation();
            ev.preventDefault();
        });


        //设置单页显示的数量，默认为100，设置local本地缓存
        $('.filePage').on('change', '.showRow', function() {
            var val = $(this).val();
            console.log(val);
            bt.set_storage('local','showRow',val);
            that.reader_file_list({ showRow: val, p: 1, is_operating: false });
        });

        // 页码跳转
        $('.filePage').on('click', 'div:nth-child(2) a', function(e) {
            var num = $(this).attr('href').match(/p=([0-9]+)$/)[1];
            that.reader_file_list({ path: that.path, p: num })
            e.stopPropagation();
            e.preventDefault();
        })

        // 获取文件夹大小
        $('.file_list_content').on('click', '.folder_size', function(e) {
            var data = that.file_list[$(this).parents('.file_tr').data('index')],
                _this = this;
            that.get_file_size({ path: data.path }, function(res) {
                $(_this).text(bt.format_size(res.size));
            });
            e.stopPropagation();
            e.preventDefault();
        });
        // 获取目录总大小
        $('.filePage').on('click', '#file_all_size', function(e) {
            if (that.file_path === '/') {
                layer.tips('当前目录为系统根目录（/）,执行获取文件大小将占用<span class="bt_danger">大量磁盘IO</span>,将导致服务器运行缓慢。', this, { tips: [1, 'red'], time: 5000 });
                return false;
            }
            that.get_dir_size({ path: that.file_path });
        });

        // 文件区域【鼠标按下】
        $('.file_list_content').on('mousedown', function(ev) {
                if (
                    $(ev.target).hasClass('file_checkbox') ||
                    $(ev.target).hasClass('file_check') ||
                    $(ev.target).hasClass('icon-share1') ||
                    $(ev.target).hasClass('icon-favorites') ||
                    ev.target.localName == 'i' ||
                    $(ev.target).parents('.app_menu_group').length > 0 ||
                    $(ev.target).hasClass('createModel') ||
                    $(ev.target).hasClass('editr_tr') ||
                    $(ev.target).attr('name') == 'createArea' ||
                    $(ev.target).attr('name') == 'rename_file_input' ||
                    $(ev.target).hasClass('set_file_ps') ||
                    that.is_editor
                ) return true;
                if (ev.which == 3 && !that.is_editor) {
                    $('.selection_right_menu').removeAttr('style');
                    that.render_file_all_menu(ev, this);
                    return true;
                } //是否为右键
                $('.file_list_content').bind('mousewheel', function() { return false; }); //禁止滚轮(鼠标抬起时解绑)
                var container = $(this), //当前选区容器
                    scroll_h = 0,
                    con_t = container.offset().top, //选区偏移上
                    con_l = container.offset().left //选区偏移左
                var startPos = { //初始位置
                    top: ev.clientY - $(this).offset().top,
                    left: ev.clientX - $(this).offset().left
                };
                // 鼠标按下后拖动
                bt_file.window_mousemove = function(ev) {
                    // 鼠标按下后移动到的位置
                    var endPos = {
                        top: ev.clientY - con_t > 0 && ev.clientY - con_t < container.height() ? ev.clientY - con_t : (ev.clientY - (con_t + container.height()) > 1 ? container.height() : 0),
                        left: ev.clientX - con_l > 0 && ev.clientX - con_l < container.width() ? ev.clientX - con_l : (ev.clientX - (con_l + container.width()) > 1 ? container.width() : 0)
                    };
                    var fixedPoint = { // 设置定点
                        top: endPos.top > startPos.top ? startPos.top : endPos.top,
                        left: endPos.left > startPos.left ? startPos.left : endPos.left
                    };
                    var enter_files_box = that.enter_files_box()
                    if (bt.get_cookie('rank') == 'list') { //在列表模式下减去表头高度
                        fixedPoint.top = fixedPoint.top + 40
                    }
                    // 拖拽范围的宽高
                    var w = Math.min(Math.abs(endPos.left - startPos.left), con_l + container.width() - fixedPoint.left);
                    var h = Math.min(Math.abs(endPos.top - startPos.top), con_t + container.height() - fixedPoint.top);

                    // 超出选区上时
                    if (ev.clientY - con_t < 0) {
                        var beyond_t = Math.abs(ev.clientY - con_t);
                        container.scrollTop(container.scrollTop() - beyond_t)
                        if (container.scrollTop() != 0) {
                            scroll_h += beyond_t
                        }
                        h = h + scroll_h
                    }
                    // 超出选区下时
                    if (ev.clientY - (con_t + container.height()) > 1) {
                        var beyond_b = ev.clientY - (con_t + container.height());
                        container.scrollTop(container.scrollTop() + beyond_b)
                        if (container[0].scrollHeight - container[0].scrollTop !== container[0].clientHeight) {
                            scroll_h += beyond_b
                        }
                        h = h + scroll_h
                        fixedPoint.top = fixedPoint.top - scroll_h
                    }
                    if (startPos.top == endPos.top || startPos.left == endPos.left) return true;
                    // if(Math.abs(startPos.top - endPos.top) <= 5 || Math.abs(startPos.left == endPos.left) <= 5) return true;
                    // 设置拖拽盒子位置
                    enter_files_box.show().css({
                        left: fixedPoint.left + 'px',
                        top: fixedPoint.top + 'px',
                        width: w + 'px',
                        height: h + 'px'
                    });

                    var box_offset_top = enter_files_box.offset().top;
                    var box_offset_left = enter_files_box.offset().left;
                    var box_offset_w = enter_files_box.offset().left + enter_files_box.width();
                    var box_offset_h = enter_files_box.offset().top + enter_files_box.height();
                    $(container).find('.file_tr').each(function(i, item) {
                        var offset_top = $(item).offset().top;
                        var offset_left = $(item).offset().left;
                        var offset_h = $(item).offset().top + $(item).height();
                        var offset_w = $(item).offset().left + $(item).width();
                        if (bt.get_cookie('rank') == 'icon') { // 为Icon模式时
                            if (offset_w >= box_offset_left && offset_left <= box_offset_w && offset_h >= box_offset_top && offset_top <= box_offset_h) {
                                $(item).addClass('active');
                            } else {
                                $(item).removeClass('active')
                            }
                        } else { // 为List模式时
                            if (offset_w >= box_offset_left && offset_h >= box_offset_top && offset_top <= box_offset_h) {
                                $(item).addClass('active')
                            } else {
                                $(item).removeClass('active')
                            }
                        }
                    });
                }


                // 鼠标抬起
                bt_file.window_mouseup = function() {
                    var _move_array = [],enter_files_box = that.enter_files_box();
                    var box_offset_top = enter_files_box.offset().top;
                    var box_offset_left = enter_files_box.offset().left;
                    var box_offset_w = enter_files_box.offset().left + enter_files_box.width();
                    var box_offset_h = enter_files_box.offset().top + enter_files_box.height();
                    $(container).find('.file_tr').each(function(i, item) {
                        var offset_top = $(item).offset().top;
                        var offset_left = $(item).offset().left;
                        var offset_h = $(item).offset().top + $(item).height();
                        var offset_w = $(item).offset().left + $(item).width();

                        if (bt.get_cookie('rank') == 'icon') { // 为Icon模式时
                            if (offset_w >= box_offset_left && offset_left <= box_offset_w && offset_h >= box_offset_top && offset_top <= box_offset_h) {
                                _move_array.push($(item).data('index'))
                            }
                        } else { // 为List模式时
                            if (offset_w >= box_offset_left && offset_h >= box_offset_top && offset_top <= box_offset_h) {
                                _move_array.push($(item).data('index'))
                            }
                        }
                    });
                    that.render_file_selected(_move_array); //渲染数据
                    enter_files_box.remove(); // 删除盒子
                    $('.file_list_content').unbind('mousewheel'); //解绑滚轮事件
                    // console.log(bt_file.window_mousemove,bt_file.window_mouseup,'---------')
                    $(document).unbind('mousemove',bt_file.window_mousemove);
                }
                $(document).one('mouseup',bt_file.window_mouseup);
                $(document).on('mousemove',bt_file.window_mousemove);
                ev.stopPropagation();
                ev.preventDefault();
            })
            // 备注设置
        $('.file_list_content').on('blur', '.set_file_ps', function(ev) {
            var tr_index = $(this).parents('.file_tr').data('index'),
                item = that.file_list[tr_index],
                nval = $(this).val(),
                oval = $(this).data('value'),
                _this = this;
            if (nval == oval) return false;
            bt_tools.send('files/set_file_ps', { filename: item.path, ps_type: 0, ps_body: nval }, function(rdata) {
                $(_this).data('value', nval);
            }, { tips: '设置文件/目录备注', tips: true });
        });
        // 备注回车事件 
        $('.file_list_content').on('keyup', '.set_file_ps', function(ev) {
            if (ev.keyCode == 13) {
                $(this).blur();
            }
            ev.stopPropagation();
        });
        // 表头拉伸
        $('.file_list_header').on('mousedown', '.file_width_resize', function(ev) {
                return false;
                if (ev.which == 3) return false;
                var th = $(this),
                    Minus_v = $(this).prev().offset().left,
                    _header = $('.file_list_header').innerWidth(),
                    maxlen = 0;
                maxlen = _header - $('.file_main_title').data
                $(document).unbind('mousemove').mousemove(function(ev) {
                    var thatPos = ev.clientX - Minus_v;
                    that.set_style_width(th.prev().data('tid'), thatPos);
                })
                $(document).one('mouseup', th, function(ev) {
                    $(document).unbind('mousemove');
                })
                ev.stopPropagation();
                ev.preventDefault();
            })
            // 视图调整
        $('.cut_view_model').on('click', function() {
            var type = $(this).data('type');
            $('.file_table_view').addClass(type == 'icon' ? 'icon_view' : 'list_view').removeClass(type != 'icon' ? 'icon_view' : 'list_view').scrollLeft(0);
            bt.set_cookie('rank', type);
            $(this).addClass('active').siblings().removeClass('active');

            // that.reader_file_list_content(that.file_list);
            // that.set_file_table_width();
        });

        //老版快捷操作
        $('.file_list_content').on('click', '.set_operation_group a', function(ev) {
            var data = $(this).parents('.file_tr').data(),
                type = $(this).data('type'),
                item = that.file_list[data.index]
            if (type == 'more') return true;
            item.open = type;
            item.index = data.index;
            item.type_tips = item.type == 'file' ? '文件' : '目录';
            that.file_groud_event(item);
        });
        $('.replace_content').on('click', function() {
            that.replace_content_view()
        })
    },
    /**
     * @descripttion: 文件拖拽范围
     * @author: Lifu
     * @return: 拖拽元素
     */
    enter_files_box: function() {
        if ($('#web_mouseDrag').length === 0) {
            $('<div></div>', {
                id: 'web_mouseDrag',
                style: [
                    'position:absolute; top:0; left:0;',
                    'border:1px solid #072246; background-color: #cce8ff;',
                    'filter:Alpha(Opacity=15); opacity:0.15;',
                    'overflow:hidden;display:none;z-index:9;'
                ].join('')
            }).appendTo('.file_table_view');
        }
        return $('#web_mouseDrag');
    },
    /**
     * @description 清除表格选中数据和样式
     * @returns void
     */
    clear_table_active: function() {
        this.file_table_arry = [];
        $('.file_list_header .file_check').removeClass('active active_2');
        $('.file_list_content .file_tr').removeClass('active app_menu_operation');
        $('.file_list_content .file_tr .file_ps .foo_menu').removeClass('foo_menu_click');
        $('.app_menu_group').remove();
    },
    /**
     * @description 计算表格中选中
     * @returns void
     */
    calculate_table_active: function() {
        var that = this,
            header_check = $('.file_list_header .file_check');
        //判断数量
        if (this.file_table_arry.length == 0) {
            header_check.removeClass('active active_2').data('checkbox', 0);
        } else if (this.file_table_arry.length == this.file_list.length) {
            header_check.addClass('active').removeClass('active_2').data('checkbox', 1);
        } else {
            header_check.addClass('active_2').removeClass('active').data('checkbox', 2);
        }
        //数量大于0开启键盘事件
        if (this.file_table_arry.length > 0) {
            $(document).unbind('keydown').on('keydown', function(e) {
                    var keyCode = e.keyCode,
                        tagName = e.target.localName.toLowerCase(),
                        is_mac = window.navigator.userAgent.indexOf('Mac') > -1
                    if (tagName == 'input' || tagName == 'textarea') return true;
                    // Ctrl + c   复制事件
                    if (e.ctrlKey && keyCode == 67) {
                        if (that.file_table_arry.length == 1) {
                            that.file_groud_event($.extend(that.file_table_arry[0], { open: 'copy' }));
                            $('.file_all_paste').removeClass('hide');
                        } else if (that.file_table_arry.length > 1) {
                            that.batch_file_manage('copy') //批量
                        }
                    }
                    // Ctrl + x   剪切事件
                    if (e.ctrlKey && keyCode == 88) {
                        if (that.file_table_arry.length == 1) {
                            that.file_groud_event($.extend(that.file_table_arry[0], { open: 'shear' }));
                            $('.file_all_paste').removeClass('hide');
                        } else if (that.file_table_arry.length > 1) {
                            that.batch_file_manage('shear') //批量
                        }
                    }
                })
                //数量超过一个显示批量操作
            if (this.file_table_arry.length > 1) {
                $('.nav_group.multi').removeClass('hide');
                $('.file_menu_tips').addClass('hide');
            } else {
                $('.nav_group.multi').addClass('hide');
                $('.file_menu_tips').removeClass('hide');
            }
        } else {
            $('.nav_group.multi').addClass('hide');
            $('.file_menu_tips.multi').removeClass('hide');
            $(document).unbind('keydown');
        }
        $('.selection_right_menu,.file_path_input .file_dir_item .nav_down_list').removeAttr('style'); // 删除右键样式、路径下拉样式
        that.set_menu_line_view_resize();
    },
    /**
     * @description 设置文件路径视图自动调整
     * @returns void
     */
    set_dir_view_resize: function() {
        var file_path_input = $('.file_path_input'),
            file_dir_view = $('.file_path_input .file_dir_view'),
            _path_width = file_dir_view.attr('data-width'),
            file_item_hide = null;
        if (_path_width) {
            parseInt(_path_width);
        } else {
            _path_width = file_dir_view.width();
            file_dir_view.attr('data-width', _path_width);
        }
        if (file_dir_view.width() - _path_width < 90) {
            var width = 0;
            $($('.file_path_input .file_dir_view .file_dir_item').toArray().reverse()).each(function() {
                var item_width = 0;
                if (!$(this).attr('data-width')) {
                    $(this).attr('data-width', $(this).width());
                    item_width = $(this).width();
                } else {
                    item_width = parseInt($(this).attr('data-width'));
                }
                width += item_width;
                if ((file_path_input.width() - width) <= 90) {
                    $(this).addClass('hide');
                } else {
                    $(this).removeClass('hide');
                }
            });
        }
        var file_item_hide = file_dir_view.children('.file_dir_item.hide').clone(true);
        if (file_dir_view.children('.file_dir_item.hide').length == 0) {
            file_path_input.removeClass('active').find('.file_dir_omit').addClass('hide');
        } else {
            file_item_hide.each(function() {
                if ($(this).find('.glyphicon-hdd').length == 0) {
                    $(this).find('.file_dir').before('<span class="file_dir_icon"></span>');
                }
            });
            file_path_input.addClass('active').find('.file_dir_omit').removeClass('hide');
            file_path_input.find('.file_dir_omit .nav_down_list').empty().append(file_item_hide);
            file_path_input.find('.file_dir_omit .nav_down_list .file_dir_item').removeClass('hide');
        }
    },
    /**
     * @descripttion 设置菜单栏视图自动调整
     * @return: 无返回值
     */
    set_menu_line_view_resize: function() {
        var menu_width = $('.file_nav_view').width(),
            disk_list_width = 0,
            batch_list_width = 0,
            _width = 0,
            disk_list = $('.mount_disk_list'),
            batch_list = $('.nav_group.multi');
        if (!disk_list.attr('data-width')) disk_list.attr('data-width', disk_list.innerWidth());
        if (!batch_list.attr('data-width') && batch_list.innerWidth() != 0 && batch_list.innerWidth() != -1) {
            batch_list.attr('data-width', batch_list.innerWidth())
        }
        disk_list_width = parseInt(disk_list.attr('data-width'));
        batch_list_width = parseInt(batch_list.attr('data-width'));
        $('.file_nav_view>.nav_group').not('.mount_disk_list').each(function() {
            _width += $(this).innerWidth();
        });
        _width += $('.menu-header-foot').innerWidth();
        if (menu_width - _width < (disk_list_width + 5)) {
            $('.nav_group.mount_disk_list').addClass('thezoom').find('.disk_title_group_btn').removeClass('hide');
        } else {
            $('.nav_group.mount_disk_list,.nav_group.multi').removeClass('thezoom');
        }
        if (this.area[0] < 1360) {
            indexs = Math.ceil(((1360 - this.area[0]) / 68));
            $('.batch_group_list>.nav_btn_group').each(function(index) {
                if (index >= $('.batch_group_list>.nav_btn_group').length - (indexs + 2)) {
                    $(this).hide()
                } else {
                    $(this).show();
                }
            });
            $('.batch_group_list>.nav_btn_group:last-child').removeClass('hide').show();
        } else {
            $('.batch_group_list>.nav_btn_group').css('display', 'inline-block');
            $('.batch_group_list>.nav_btn_group:last-child').addClass('hide');
        }
    },
    /**
     * @description 设置文件前进或后退状态
     * @returns void
     */
    set_file_forward: function() {
        var that = this,
            forward_path = $('.forward_path span');
        if (that.file_operating.length == 1) {
            forward_path.addClass('active');
        } else if (that.file_pointer == that.file_operating.length - 1) {
            forward_path.eq(0).removeClass('active');
            forward_path.eq(1).addClass('active');
        } else if (that.file_pointer == 0) {
            forward_path.eq(0).addClass('active');
            forward_path.eq(1).removeClass('active');
        } else {
            forward_path.removeClass('active');
        }
    },
    /**
     * @description 设置文件视图
     * @returns void
     */
    set_file_view: function() {
        var file_list_content = $('.file_list_content'),
            height = this.area[1] - $('.file_table_view')[0].offsetTop - 170;
        $('.file_bodys').height(this.area[1] - 100);
        if ((this.file_list.length * 50) > height) {
            file_list_content.attr('data-height', file_list_content.data('height') || file_list_content.height()).css({ 'overflow': 'hidden', 'overflow-y': 'auto', 'height': height + 'px' });
            $('.file_shadow_bottom').css('opacity', 1);
        } else {
            file_list_content.css({ 'overflow': 'hidden', 'overflow-y': 'auto', 'height': height + 'px' });
            $('.file_shadow_top,.file_shadow_bottom').css('opacity', 0);
        }
    },
    /**
     * @description 打开分享列表
     * @returns void
     */
    open_share_view: function() {
        var that = this;
        layer.open({
            type: 1,
            shift: 5,
            closeBtn: 2,
            area: ['850px', '580px'],
            title: '分享列表',
            content: '<div class="divtable mtb10 download_table" style="padding:5px 10px;">\
                    <table class="table table-hover" id="download_url">\
                        <thead><tr><th width="230px">分享名称</th><th width="300px">文件地址</th><th>过期时间</th><th style="text-align:right;width:120px;">操作</th></tr></thead>\
                        <tbody class="download_url_list"></tbody>\
                    </table>\
                    <div class="page download_url_page"></div>\
            </div>',
            success: function() {
                that.render_share_list();

                // 分享列表详情操作
                $('.download_url_list').on('click', '.info_down', function() {
                    var indexs = $(this).attr('data-index');
                    that.file_share_view(that.file_share_list[indexs], 'list');
                });

                // 分页
                $('.download_table .download_url_page').on('click', 'a', function(e) {
                    var _href = $(this).attr('href').match(/p=([0-9]+)$/)[1]
                    that.render_share_list({ p: _href });
                    e.stopPropagation();
                    e.preventDefault();
                });
            }
        })
    },
    /**
     * @description 渲染分享列表
     * @param {Number} page 分页
     * @returns void
     */
    render_share_list: function(param) {
        var that = this,
            _list = ''
        if (typeof param == 'undefined') param = { p: 1 }
        bt_tools.send('files/get_download_url_list', param, function(res) {
            that.file_share_list = res.data;
            if (res.data.length > 0) {
                $.each(res.data, function(index, item) {
                    _list += '<tr>' +
                        '<td><span style="width:230px;white-space: nowrap;overflow: hidden;text-overflow: ellipsis;display: inline-block;" title="' + item.ps + '">' + item.ps + '</span></td>' +
                        '<td><span style="width:300px;white-space: nowrap;overflow:hidden;text-overflow: ellipsis;display: inline-block;" title="' + item.filename + '">' + item.filename + '</span></td>' +
                        '<td><span>' + bt.format_data(item.expire) + '</span></td>' +
                        '<td style="text-align:right;">' +
                        '<a href="javascript:;" class="btlink info_down" data-id="' + item.id + '" data-index="' + index + '">详情</a>&nbsp;|&nbsp;' +
                        '<a href="javascript:;" class="btlink del_down" data-id="' + item.id + '" data-index="' + index + '" data-ps="' + item.ps + '">关闭</a>' +
                        '</td></tr>'
                })
            } else {
                _list = '<tr><td colspan="4">暂无分享数据</td></tr>'
            }
            $('.download_url_list').html(_list);
            $('.download_url_page').html(res.page);
            // 删除操作
            $('.download_table').on('click', '.del_down', function() {
                var id = $(this).attr('data-id'),
                    _ps = $(this).attr('data-ps');
                that.remove_download_url({ id: id, fileName: _ps }, function(res) {
                    if (res.status) that.render_share_list(param)
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                });
            });
        }, '获取分享列表');
    },

    /**
     * @description 删除选中数据
     * @param {Array} arry
     * @param {*} value 
     * @return void
     */
    remove_check_file: function(arry, key, value) {
        var len = arry.length;
        while (len--) {
            if (arry[len][key] == value) arry.splice(len, 1)
        }
    },

    /**
     * @description 打开文件下载视图
     * @return void
     */
    open_download_view: function() {
        var that = this;
        that.reader_form_line({
            url: 'DownloadFile',
            beforeSend: function(data) {
                return { url: data.url, path: data.path, filename: data.filename };
            },
            overall: { width: '310px' },
            data: [{
                    label: 'URL地址:',
                    name: 'url',
                    placeholder: 'URL地址',
                    value: 'http://',
                    eventType: ['input', 'focus'],
                    input: function() {
                        var value = $(this).val(),
                            url_list = value.split('/');
                        $('[name="filename"]').val(url_list[url_list.length - 1]);
                    }
                },
                { label: '下载到:', name: 'path', placeholder: '下载到', value: that.file_path },
                {
                    label: '文件名:',
                    name: 'filename',
                    placeholder: '保存文件名',
                    value: '',
                    eventType: 'enter',
                    enter: function() {
                        $('.download_file_view .layui-layer-btn0').click();
                    }
                }
            ]
        }, function(form, html) {
            var loadT = bt.open({
                type: 1,
                title: '下载文件',
                area: '500px',
                shadeClose: false,
                skin: 'download_file_view',
                content: html[0].outerHTML,
                btn: ['确认', '关闭'],
                success: function() {
                    form.setEvent();
                },
                yes: function(indexo, layero) {
                    var ress = form.getVal();
                    if (!bt.check_url(ress.url)) {
                        layer.msg('请输入有效的url地址..', { icon: 2 })
                        return false;
                    }
                    form.submitForm(function(res) {
                        that.render_present_task_list();
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                        loadT.close();
                    });
                }
            });
        });
    },

    /**
     * @description 设置样式文件
     * @param {String} type 表头类型
     * @param {Number} width 宽度
     * @return void 
     */
    set_style_width: function(type, width) {
        var _content = bt.get_cookie('formHeader') || $('#file_list_info').html(),
            _html = '',
            _reg = new RegExp("\\.file_" + type + "\\s?\\{width\\s?\\:\\s?(\\w+)\\s\\!important;\\}", "g"),
            _defined_config = { name: 150, type: 80, size: 80, mtime: 150, accept: 80, user: 80, ps: 150 };
        _html = _content.replace(_reg, function(match, $1, $2, $3) {
            return '.file_' + type + '{width:' + (width < 80 ? _defined_config[type] + 'px' : width + 'px') + ' !important;}'
        });
        $('#file_list_info').html(_html);
    },

    /**
     * @description 设置文件表格
     * @return void
     */
    set_file_table_width: function() {
        var that = this,
            file_header_width = $('.file_table_view')[0].offsetWidth,
            auto_num = 0,
            width = 0,
            auto_all_width = 0,
            css = '',
            _width = 0,
            tr_heigth = 45,
            other = '',
            config = {};
        $.each(this.file_header, function(key, item) {
            if (item == 'auto') {
                auto_num++;
                config[key] = 0;
            } else {
                width += item;
                css += '.' + key + '{width:' + (key != 'file_operation' ? item : item - 16) + 'px !important;}';
            }
        });
        if (this.is_mobile) $('.file_operation.file_th').attr('style', 'margin-right:-10px !important;');
        if ((this.file_list.length * tr_heigth) > $('.file_list_content').height()) {
            config['file_tr'] = file_header_width - (this.is_mobile ? 0 : this.scroll_width);
            file_header_width = file_header_width;
            other += '.file_td.file_operation{width:' + (this.file_header['file_operation'] - (this.is_mobile ? 0 : this.scroll_width) - 10) + 'px !important;}';
            other += '.file_th.file_operation{padding-right:' + (10 + (this.is_mobile ? 0 : this.scroll_width)) + 'px !important}';
        } else {
            file_header_width = file_header_width;
            config['file_tr'] = file_header_width;
            if (this.is_mobile) other += '.file_td.file_operation{width:' + (this.file_header['file_operation'] - 20) + 'px !important;}';
        }
        config['file_list_header'] = file_header_width;
        auto_all_width = file_header_width - width;
        _width = auto_all_width / auto_num;
        $.each(config, function(key, item) {
            css += '.' + key + '{width:' + (item == 0 ? _width : item) + 'px !important;}';
        });
        $('#file_list_info').html(css + other);
    },

    /**
     * @description 渲染路径列表
     * @param {Function} callback 回调函数
     * @return void
     */
    render_path_list: function(callback) {
        var that = this,
            html = '<div class="file_dir_omit hide" title="展开已隐藏的目录"><span></span><i class="iconfont icon-zhixiang-zuo"></i><div class="nav_down_list"></div></div>',
            path_before = '',
            dir_list = this.file_path.split("/").splice(1),
            first_dir = this.file_path.split("/")[0];
        if (bt.os === 'Windows') {
            if (dir_list.length == 0) dir_list = [];
            dir_list.unshift('<span class="glyphicon glyphicon-hdd"></span><span class="ml5">本地磁盘(' + first_dir + ')</span>');
        } else {
            if (this.file_path == '/') dir_list = [];
            dir_list.unshift('根目录');
        }
        for (var i = 0; i < dir_list.length; i++) {
            path_before += '/' + dir_list[i];
            if (i == 0) path_before = '/';
            html += '<div class="file_dir_item">\
                        <span class="file_dir" title="' + (path_before.replace('//', '/')) + '">' + dir_list[i] + '</span>\
                        <i class="iconfont icon-arrow-right"></i>\
                        <ul class="nav_down_list">\
                            <li data-path="*"><span>加载中</span></li>\
                        </ul>\
                    </div>';
        }
        $('.path_input').val('').attr('data-path', this.file_path);
        var file_dir_view = $('.file_path_input .file_dir_view');
        file_dir_view.html(html);
        file_dir_view.attr('data-width', file_dir_view.width());
        that.set_dir_view_resize.delay(that, 100);
    },

    /**
     * @description 渲染路径下拉列表
     * @param {Object} el Dom选择器
     * @param {String} path 路径
     * @param {Function} callback 回调函数
     */
    render_path_down_list: function(el, path, callback) {
        var that = this,
            _html = '',
            next_path = $(el).parent().next().find('.file_dir').attr('title');
        this.get_dir_list({
            path: path
        }, function(res) {
            $.each(that.data_reconstruction(res.DIR), function(index, item) {
                var _path = (path != '/' ? path : '') + '/' + item.filename;
                _html += '<li data-path="' + _path + '" title="' + _path + '" class="' + (_path === next_path ? 'active' : '') + '"><i class="file_menu_icon newly_file_icon"></i><span>' + item.filename + '</span></li>';
            });
            $(el).html(_html);
        });
    },

    /**
     * @description 渲染文件列表
     * @param {Object} data 参数对象，例如分页、显示数量、排序，不传参数使用默认或继承参数
     * @param {Function} callback 回调函数
     * @return void
     */
    reader_file_list: function(data, callback) {
        var that = this,
            select_page_num = '',
            next_path = '',
            model = bt.get_cookie('rank'),
            isPaste = bt.get_cookie('record_paste_type');
        if (isPaste != 'null' && isPaste != undefined) { //判断是否显示粘贴
            $('.file_nav_view .file_all_paste').removeClass('hide');
        } else {
            $('.file_nav_view .file_all_paste').addClass('hide');
        }
        $('.file_table_view').removeClass('.list_view,.icon_view').addClass(model == 'list' ? 'list_view' : 'icon_view');
        $('.cut_view_model:nth-child(' + (model == 'list' ? '2' : '1') + ')').addClass('active').siblings().removeClass('active');
        this.file_images_list = [];
        this.get_dir_list(data, function(res){
            if (res.status === false && res.msg.indexOf('指定目录不存在!') > -1) {
                return that.reader_file_list({ path: '/www' })
            }
            that.file_path = that.path_check(res.PATH);
            that.file_list = $.merge(that.data_reconstruction(res.DIR, 'DIR'), that.data_reconstruction(res.FILES));
            that.file_store_list = res.STORE;
            bt.set_cookie('Path', that.path_check(res.PATH));
            if(typeof res.FILE_RECYCLE == 'boolean')bt.set_cookie('file_recycle_status',res.FILE_RECYCLE)
            that.reader_file_list_content(that.file_list, function(rdata) {
                $('.path_input').attr('data-path', that.file_path);
                $('.file_nav_view .multi').addClass('hide');
                $('.selection_right_menu').removeAttr('style');
                var arry = ['100', '200', '500', '1000', '2000'];
                for (var i = 0; i < arry.length; i++){
                    var item = arry[i];
                    select_page_num += '<option value="' + item + '" ' + (item == bt.get_storage('local','showRow') ? 'selected' : '') + '>' + item + '</option>';
                }
                var page = $(res.PAGE);
                page.append('<span class="Pcount-item">每页<select class="showRow">' + select_page_num + '</select>条</span>');
                $('.filePage').html('<div class="page_num">共' + rdata.is_dir_num + '个目录，' + (that.file_list.length - rdata.is_dir_num) + '个文件，文件大小:<a href="javascript:;" class="btlink" id="file_all_size">计算</a></div>' + page[0].outerHTML);
                if(data.is_operating) data.is_operating = false;
                if(data.is_operating && that.file_operating[that.file_pointer] != res.PATH) {
                    next_path = that.file_operating[that.file_pointer + 1];
                    if (typeof next_path != "undefined" && next_path != res.PATH) that.file_operating.splice(that.file_pointer + 1);
                    that.file_operating.push(res.PATH);
                    that.file_pointer = that.file_operating.length - 1;
                }
                that.render_path_list(); // 渲染文件路径地址
                that.set_file_forward(); // 设置前进后退状态
                that.render_favorites_list(); //渲染收藏夹列表
                that.set_file_view(); // 设置文件视图
                that.set_file_table_width() //设置表格头部宽度
                if (callback) callback(res);
            });
        });
    },
    /**
     * @descripttion 重组数据结构
     * @param {Number} data  数据
     * @param {String} type  类型
     * @return: 返回重组后的数据
     */
    data_reconstruction: function(data, type, callback) {
        var that = this,
            arry = [],
            info_ps = [
                ['/etc', 'PS: 系统主要配置文件目录'],
                ['/home', 'PS: 用户主目录'],
                ['/tmp', 'PS: 公共的临时文件存储点'],
                ['/root', 'PS: 系统管理员的主目录'],
                ['/home', 'PS: 用户主目录'],
                ['/usr', 'PS: 系统应用程序目录'],
                ['/boot', 'PS: 系统启动核心目录'],
                ['/lib', 'PS: 系统资源文件类库目录'],
                ['/mnt', 'PS: 存放临时的映射文件系统'],
                ['/www', 'PS: 宝塔面板程序目录'],
                ['/bin', 'PS: 存放二进制可执行文件目录'],
                ['/dev', 'PS: 存放设备文件目录'],
                ['/www/wwwlogs', 'PS: 默认网站日志目录'],
                ['/www/server', 'PS: 宝塔软件安装目录'],
                ['/www/wwwlogs', 'PS: 网站日志目录'],
                ['/www/Recycle_bin', 'PS: 回收站目录,勿动'],
                ['/www/server/panel', 'PS: 宝塔主程序目录，勿动'],
                ['/www/server/panel/plugin', 'PS: 宝塔插件安装目录'],
                ['/www/server/panel/BTPanel', 'PS: 宝塔面板前端文件'],
                ['/www/server/panel/BTPanel/static', 'PS: 宝塔面板前端静态文件'],
                ['/www/server/panel/BTPanel/templates', 'PS: 宝塔面板前端模板文件'],
                [bt.get_cookie('backup_path'), 'PS: 默认备份目录'],
                [bt.get_cookie('sites_path'), 'PS: 默认建站目录']
            ];
        if (data.length < 1) return [];
        $.each(data, function(index, item) {
            var itemD = item.split(";"),
                fileMsg = '',
                fileN = itemD[0].split('.'),
                extName = fileN[fileN.length - 1];
            switch (itemD[0]) {
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
            if (itemD[0].indexOf('.upload.tmp') != -1) fileMsg = 'PS: 宝塔文件上传临时文件,重新上传从断点续传,可删除';
            for (var i = 0; i < info_ps.length; i++) {
                if (that.path_resolve(that.file_path, itemD[0]) === info_ps[i][0]) fileMsg = info_ps[i][1];
            }
            arry.push({
                caret: itemD[8] == '1' ? true : false, // 是否收藏
                down_id: parseInt(itemD[9]), // 是否分享 分享id
                ext: (type == 'DIR' ? '' : extName.toLowerCase()), // 文件类型
                filename: itemD[0], // 文件名称
                mtime: itemD[2], // 时间
                ps: fileMsg || itemD[10] || '', // 备注
                is_os_ps: fileMsg != '' ? true : false, // 是否系统备注信息
                size: itemD[1], // 文件大小
                type: type == 'DIR' ? 'dir' : 'file', // 文件类型
                user: itemD[3], // 用户权限
                root_level: itemD[4], // 所有者
                soft_link: itemD[5] || '', // 软连接
                is_search:$('.file_search_input').val()?true:false //判断是否搜索 
            });
        });
        return arry;
    },
    /**
     * @descripttion 渲染拖拽选中列表
     * @param {Array} _array 选中的区域
     * @return: 无返回值
     */
    render_file_selected: function(_array) {

        var that = this,
            tmp = [];
        that.clear_table_active()
        $.each(_array, function(index, item) {
            if (tmp.indexOf(item) == -1) {
                tmp.push(item)
            }
        })
        $.each(tmp, function(ind, items) {
            $('.file_list_content .file_tr').eq(items).addClass('active');
            that.file_table_arry.push(that.file_list[items]);
        })
        that.calculate_table_active();
    },
    /** 
     * @descripttion 渲染收藏夹列表
     * @return: 无返回值
     */
    render_favorites_list: function() {
        var html = '';
        if (this.file_store_list.length > 0) {
            $.each(this.file_store_list, function(index, item) {
                html += '<li title="' + item['name'] + '" data-path="' + item['path'] + '" data-type="' + item['type'] + '">' +
                    '<i class="' + (item['type'] == 'file' ? 'file_new_icon' : 'file_menu_icon create_file_icon') + '"></i>' +
                    '<span>' + item['name'] + '</span>' +
                    '</li>'
            })
            html += '<li data-manage="favorites" onclick="bt_file.set_favorites_manage()"><span class="iconfont icon-shezhi1"></span><span>管理</span></li>'
        } else { html = '<li data-null style="width: 150px;"><i></i><span>（空）</span></li>' }

        $('.favorites_file_path .nav_down_list').html(html)
    },
    /**
     * @descripttion 收藏夹目录视图
     * @return: 无返回值
     */
    set_favorites_manage: function() {
        var that = this;
        layer.open({
            type: 1,
            title: "管理收藏夹",
            area: ['850px', '580px'],
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            content: "<div class='stroe_tab_list bt-table pd15'>\
                    <div class='divtable' style='height:420px'>\
                    <table class='table table-hover'>\
                        <thead><tr><th>路径</th><th style='text-align:right'>操作</th></tr></thead>\
                        <tbody class='favorites_body'></tbody>\
                    </table></div></div>",
            success: function(layers) {
                that.render_favorites_type_list();
                setTimeout(function() {                 $(layers).css('top', ($(window).height()  -  $(layers).height())  / 2);             }, 50)

            },
            cancel: function() {
                that.reader_file_list({ path: that.file_path })
            }
        })
    },
    /**
     * @description 渲染收藏夹分类列表
     * @return void
     */
    render_favorites_type_list: function() {
        var _detail = '';
        this.$http('get_files_store', function(rdata) {
            if (rdata.length > 0) {
                $.each(rdata, function(ind, item) {
                    _detail += '<tr>' +
                        '<td><span class="favorites_span" title="' + item['path'] + '">' + item['path'] + '</span></td>' +
                        '<td style="text-align:right;">' +
                        '<a class="btlink" onclick="bt_file.del_favorites(\'' + item['path'] + '\')">删除</a>' +
                        '</td>' +
                        '</tr>'
                })
            } else {
                _detail = '<tr><td colspan="2">暂无收藏</td></tr>'
            }
            $('.favorites_body').html(_detail);
            if (jQuery.prototype.fixedThead) {
                $('.stroe_tab_list .divtable').fixedThead({ resize: false });
            } else {
                $('.stroe_tab_list .divtable').css({ 'overflow': 'auto' });
            }
        })
    },
    /**
     * @description 重新获取收藏夹列表
     * @return void
     */
    load_favorites_index_list: function() {
        var that = this;
        this.$http('get_files_store', function(rdata) {
            that.file_store_list = rdata;
            that.render_favorites_list()
        })
    },
    /**
     * @description 删除收藏夹
     * @param {String} path 文件路径
     * @return void
     */
    del_favorites: function(path) {
        var that = this
        layer.confirm('是否确定删除路径【' + path + '】？', { title: '删除收藏夹', closeBtn: 2, icon: 3 }, function(index) {
            that.$http('del_files_store', { path: path }, function(res) {
                if (res.status) {
                    that.render_favorites_type_list();
                }
                layer.msg(res.msg, { icon: res.status ? 1 : 2 })
            })
        })
    },
    /**
     * @description 渲染文件列表内容
     * @param {Object} data 文件列表数据
     * @param {Function} callback 回调函数
     * @return void
     */
    reader_file_list_content: function(data, callback) {
        var _html = '',
            that = this,
            is_dir_num = 0,
            images_num = 0;
        $.each(data, function(index, item) {
            var _title = item.filename,
                only_id = bt.get_random(10),
                path = (that.file_path + '/' + item.filename).replace('//', '/'),
                is_compress = that.determine_file_type(item.ext, 'compress'),
                is_editor_tips = (function() {
                    var _openTitle = '打开';
                    switch (that.determine_file_type(item.ext)) {
                        case 'images':
                            _openTitle = '预览';
                            break;
                        case 'video':
                            _openTitle = '播放';
                            break;
                        default:
                            if (that.determine_file_type(item.ext) == 'compress') {
                                _openTitle = '';
                            } else {
                                _openTitle = '编辑';
                            }
                            break;
                    }
                    item.type == 'dir' ? _openTitle = '打开' : '';
                    return _openTitle;
                }(item))
            that.file_list[index]['only_id'] = only_id;
            _html += '<div class="file_tr" data-index="' + index + '" data-filename="' + item.filename + '" ' + (bt.get_cookie('rank') == 'icon' ? 'title="' + path + '&#13;' + lan.files.file_size + ':' + bt.format_size(item.size) + '&#13;' + lan.files.file_etime + ':' + bt.format_data(item.mtime) + '&#13;' + lan.files.file_auth + ':' + item.user + '&#13;' + lan.files.file_own + ':' + item.root_level + '"' : '') + '>' +
                '<div class="file_td file_checkbox"><div class="file_check"></div></div>' +
                '<div class="file_td file_name">' +
                '<div class="file_ico_type"><i class="file_icon ' + (item.type == 'dir' ? 'file_folder' : (item.ext == '' ? '' : 'file_' + item.ext).replace('//', '/')) + '"></i></div>' +
                '<span class="file_title file_' + item.type + '_status" ' + (bt.get_cookie('rank') == 'icon' ? '' : 'title="' + path + '"') + '><i>' + item.filename + item.soft_link + '</i></span>' + (item.caret ? '<span class="iconfont icon-favorites" style="' + (item.down_id != 0 ? 'right:30px' : '') + '" title="文件已收藏，点击取消"></span>' : '') + (item.down_id != 0 ? '<span class="iconfont icon-share1" title="文件已分享，点击查看信息"></span>' : '') +
                '</div>' +
                '<div class="file_td file_type hide"><span title="' + (item.type == 'dir' ? '文件夹' : that.ext_type_tips(item.ext)) + '">' + (item.type == 'dir' ? '文件夹' : that.ext_type_tips(item.ext)) + '</span></div>' +
                '<div class="file_td file_accept"><span>' + item.user + ' / ' + item.root_level + '</span></div>' +
                '<div class="file_td file_size"><span>' + (item.type == 'dir' ? '<a class="btlink folder_size" href="javascript:;" data-path="' + path + '">计算</a>' : bt.format_size(item.size)) + '</span></div>' +
                '<div class="file_td file_mtime"><span>' + bt.format_data(item.mtime) + '</span></div>' +
                '<div class="file_td file_ps"><span class="file_ps_title" title="' + item.ps + '">' + (item.is_os_ps ? item.ps : '<input type="text" class="set_file_ps" data-value="' + item.ps + '" value="' + item.ps + '" />') + '</span></div>' +
                '<div class="file_td file_operation"><div class="set_operation_group ' + (that.is_mobile ? 'is_mobile' : '') + '">' +
                '<a href="javascript:;" class="btlink" data-type="open">' + is_editor_tips + '</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="copy">复制</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="shear">剪切</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="rename">重命名</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="authority">权限</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="' + (is_compress ? 'unzip' : 'compress') + '">' + (is_compress ? '解压' : '压缩') + '</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink" data-type="del">删除</a>&nbsp;|&nbsp;' +
                '<a href="javascript:;" class="btlink foo_menu_title" data-type="more">更多<i></i></a>' +
                '</div></div>' +
                '</div>';
            if (item.type == 'dir') is_dir_num++;
            item.path = path; // 文件路径;
            item.open_type = that.determine_file_type(item.ext); // 打开类型;
            if (item.open_type == 'images') {
                item.images_id = images_num;
                that.file_images_list.push(item.path);
                images_num++;
            }
        });
        $('.file_list_content').html(_html);
        if (callback) callback({ is_dir_num: is_dir_num })
        that.clear_table_active(); // 清除表格选中内容
    },

    /**
     * @description 渲染文件磁盘列表
     * @return void
     */
    render_file_disk_list: function() {
        var that = this,
            html = '',
            _li = '';
        that.get_disk_list(function(res) {
            $.each(res, function(index, item) {
                html += '<div class="nav_btn" data-menu="' + item.path + '">' +
                    '<span class="glyphicon glyphicon-hdd"></span>' +
                    '<span>' + (item.path == '/' ? '/(根目录)' : item.path) + ' (' + item.size[2] + ')</span>' +
                    '</div>';
                _li += '<li data-disk="' + item.path + '"><i class="glyphicon glyphicon-hdd"></i><span>' + (item.path == '/' ? '根目录' : item.path) + ' (' + item.size[2] + ')</span></li>'
            });
            $('.mount_disk_list').html('<div class="disk_title_group_btn hide"><span class="disk_title_group">磁盘分区</span><i class="iconfont icon-xiala"></i><ul class="nav_down_list">' + _li + '</ul></div><div class="file_disk_list">' + html + '</div>');
            that.set_menu_line_view_resize();
        });
    },

    /**
     * @description 渲染右键鼠标菜单
     * @param {Object} ev 事件event对象
     * @param {Object} el 事件对象DOM
     * @return void
     */
    render_file_groud_menu: function(ev, el) {
        var that = this,
          index = $(el).data('index'),
          _openTitle = '打开',
          data = that.file_list[index],
          compression = ['zip', 'rar', 'gz', 'war', 'tgz', 'bz2'],
          offsetNum = 0,
          config = {
            open:_openTitle,
            split_0:true,
            download:'下载',
            share:'分享目录/文件',
            cancel_share:'取消分享',
            favorites:'收藏目录/文件',
            cancel_favorites:'取消收藏',
            split_1:true,
            dir_kill:'目录查杀',
            authority:'权限',
            split_2:true,
            copy:'复制',
            shear:'剪切',
            rename:'重命名',
            del:'删除',
            split_3:true,
            compress:'创建压缩',
            unzip:'解压',
            open_find_dir:'打开文件所在目录',
            split_4:true,
            property:'属性'
          };
        // 文件类型判断
        switch (that.determine_file_type(data.ext)) {
            case 'images':
              _openTitle = '预览';
              break;
            case 'video':
              _openTitle = '播放';
              break;
            default:
              _openTitle = '编辑';
              break;
        }
        config['open'] = (data.type == 'dir' ? '打开' : _openTitle);
        if(data.type === 'dir') delete config['download']; // 判断是否文件或文件夹,禁用下载
        if(data.open_type == 'compress') delete config['open']; // 判断是否压缩文件,禁用操作
        if(data.down_id != 0){
          delete config['share']; //已分享
        }else{
          delete config['cancel_share']; //未分享
          config['share'] = (data.type == 'dir' ? '分享目录' : '分享文件');
        }
        if (data.caret !== false) {
          delete config['favorites']; // 已分享
        }else{
          delete config['cancel_favorites']; // 未分享
          config['favorites'] =  (data.type == 'dir' ? '收藏目录' : '收藏文件');
        }
        if (data.ext == 'php') config['dir_kill'] = '文件查杀';
        if (data.ext != 'php' && data.type != 'dir') delete config['dir_kill'];
        var num = 0;
        $.each(compression, function(index, item) { // 判断压缩文件
          if (item == data.ext) num++;
        });
        if(num == 0) delete config['unzip'];
        if(!data.is_search){
          delete config['open_find_dir']; // 判断是否为搜索文件，提供打开目录操作
        }else{
          config['open_find_dir'] = (data.type == 'dir' ? '打开该目录' : '打开文件所在目录');
        }
        that.file_selection_operating = config;
        that.reader_menu_list({ el: $('.selection_right_menu'), ev: ev, data: data, list: config });
    },

    /**
     * @description 渲染右键全局菜单
     * @param {Object} ev 事件event对象
     * @param {Object} el 事件对象DOM
     * @return void
     */
    render_file_all_menu: function(ev, el) {
        var that = this,
            config = {
              refresh:'刷新',
              split_0:true,
              upload:'上传',
              create:['新建文件夹/文件',{
                create_dir:'新建文件夹',
                create_files:'新建文件',
                soft_link:'软链接文件'
              }],
              web_shell:'终端',
              split_1:true,
              paste:'粘贴'
            },
            offsetNum = 0,
            isPaste = bt.get_cookie('record_paste_type');
        if (isPaste == 'null' || isPaste == undefined) {
          delete config['split_1']
          delete config['paste']
        }
        that.reader_menu_list({ el: $('.selection_right_menu'), ev: ev, data: {}, list: config });
    },
    /**
     * @descripttion 文件多选时菜单
     * @param {Object} ev 事件event对象
     * @return: 无返回值
     */
    render_files_multi_menu: function(ev) {
        var that = this,
            config_group = [
                ['copy', '复制'],
                ['shear', '剪切'],
                ['authority', '权限'],
                ['compress', '创建压缩'],
                ['del', '删除']
            ],
            el = $('.selection_right_menu').find('ul'),
            el_height = el.height(),
            el_width = el.width(),
            left = ev.clientX - ((this.area[0] - ev.clientX) < el_width ? el_width : 0);
        el.empty();
        $.each(config_group, function(index, mitem) {
            var $children = null;
            if (mitem[0] == 'split') {
                el.append('<li class="separate"></li>');
            } else {
                el.append($('<li><i class="file_menu_icon ' + mitem[0] + '_file_icon ' + (function(type) {
                    if (type == 'authority') return 'iconfont icon-authority';
                    return '';
                }(mitem[0])) + '"></i><span>' + mitem[1] + '</span></li>').append($children).on('click', { type: mitem[0], data: that.file_table_arry }, function(ev) {
                    $('.selection_right_menu').removeAttr('style');
                    that.batch_file_manage(ev.data.type);
                    ev.stopPropagation();
                    ev.preventDefault();
                }));
            }
        });
        $('.selection_right_menu').css({
            left: left,
            top: ev.clientY - ((this.area[1] - ev.clientY) < el_height ? el_height : 0)
        }).removeClass('left_menu right_menu').addClass(this.area[0] - (left + el_width) < 230 ? 'left_menu' : 'right_menu');
        $(document).one('click', function(e) {
            $(ev.currentTarget).removeClass('selected');
            $('.selection_right_menu').removeAttr('style');
            e.stopPropagation();
            e.preventDefault();
        });
    },

    /**
     * @description 渲染菜单列表
     * @param {Object} el 菜单DOM 
     * @param {Object} config 菜单配置列表和数据
     * @returns void
     */
    reader_menu_list: function(config) {
        var that = this,
          el = config.el.find('ul'),
          el_height = 0,
          el_width = el.width(),
          left = config.ev.clientX - ((this.area[0] - config.ev.clientX) < el_width ? el_width : 0),
          top = 0;
        el.empty();
        $.each(config.list, function(key, item){
            var $children = null,
                $children_list = null;
            if (typeof item == "boolean") {
                el.append('<li class="separate"></li>');
            } else {
                if (Array.isArray(item)) {
                  $children = $('<div class="file_menu_down"><span class="glyphicon glyphicon-triangle-right" aria-hidden="true"></span><ul class="set_group"></ul></div>');
                  $children_list = $children.find('.set_group');
                  $.each(item[1], function(keys, items) {
                      $children_list.append($('<li><i class="file_menu_icon ' + keys + '_file_icon"></i><span>' + items + '</span></li>').on('click', { type: keys, data: config.data }, function(ev) {
                          that.file_groud_event($.extend(ev.data.data, {
                              open: ev.data.type,
                              index: parseInt($(config.ev.currentTarget).data('index')),
                              element: config.ev.currentTarget,
                              type_tips: config.data.type == 'dir' ? '文件夹' : '文件'
                          }));
                          config.el.removeAttr('style');
                          ev.stopPropagation();
                          ev.preventDefault();
                      }))
                  });
                }
                el.append($('<li><i class="file_menu_icon ' + key + '_file_icon ' + (function(type) {
                  switch (type) {
                      case 'share':
                      case 'cancel_share':
                          return 'iconfont icon-share1';
                      case 'dir_kill':
                          return 'iconfont icon-dir_kill';
                      case 'authority':
                          return 'iconfont icon-authority';
                  }
                  return '';
                }(key)) + '"></i><span>' + (Array.isArray(item)?item[0]:item) + '</span></li>').append($children).on('click', { type: key, data: config.data }, function(ev) {
                    that.file_groud_event($.extend(ev.data.data, {
                        open: ev.data.type,
                        index: parseInt($(config.ev.currentTarget).data('index')),
                        element: config.ev.currentTarget,
                        type_tips: config.data.type == 'dir' ? '文件夹' : '文件'
                    }));
                    // 有子级拉下时不删除样式，其余删除
                    if (key != 'compress' && key != 'create') { config.el.removeAttr('style'); }
                    ev.stopPropagation();
                    ev.preventDefault();
                }));
            }
        });
        el_height = el.innerHeight();
        top = config.ev.clientY - ((this.area[1] - config.ev.clientY) < el_height ? el_height : 0);
        var element = $(config.ev.target);
        if (element.hasClass('foo_menu_title') || element.parents().hasClass('foo_menu_title')) {
            left = config.ev.clientX - el_width;
            top = ((this.area[1] - config.ev.clientY) < el_height) ? (config.ev.clientY - el_height - 20) : (config.ev.clientY + 15);
        }
        config.el.css({
            left: (left + 10),
            top: top
        }).removeClass('left_menu right_menu').addClass(this.area[0] - (left + el_width) < 230 ? 'left_menu' : 'right_menu');
    },

    /**
     * @description 返回后缀类型说明
     * @param {String} ext 后缀类型
     * @return {String} 文件类型
     */
    ext_type_tips: function(ext) {
      var config = { ai: "Adobe Illustrator格式图形", apk: "安卓安装包", asp: "动态网页文件", bat: "批处理文件", bin: "二进制文件", bas: "BASIC源文件", bak: "备份文件", css: 'CSS样式表', cad: "备份文件", cxx: "C++源代码文件", crt: "认证文件", cpp: "C++代码文件", conf: "配置文件", dat: "数据文件", der: "认证文件", doc: "Microsoft Office Word 97-2003 文档", docx: "Microsoft Office Word 2007 文档", exe: "程序应用", gif: "图形文件", go: "Go语言源文件", htm: "超文本文档", html: "超文本文档", ico: "图形文件", java: "Java源文件", access: '数据库文件', jsp: "HTML网页", jpe: "图形文件", jpeg: "图形文件", jpg: "图形文件", log: "日志文件", link: "快捷方式文件", js: "Javascript源文件", mdb: "Microsoft Access数据库", mp3: "音频文件", ape: 'CloudMusic.ape', mp4: "视频文件", avi: '视频文件', mkv: '视频文件', rm: '视频文件', mov: '视频文件', mpeg: '视频文件', mpg: '视频文件', rmvb: '视频文件', webm: '视频文件', wma: '视频文件', wmv: '视频文件', swf: 'Shockwave Flash Object', mng: "多映像网络图形", msi: "Windows Installe安装文件包", png: "图形文件", py: "Python源代码", pyc: "Python字节码文件", pdf: "文档格式文件", ppt: "Microsoft Powerpoint 97-2003 幻灯片演示文稿", pptx: "Microsoft Powerpoint2007 幻灯片演示文稿", psd: "Adobe photoshop位图文件", pl: "Perl脚本语言", rar: "RAR压缩文件", reg: "注册表文件", sys: "系统文件", sql: "数据库文件", sh: "Shell脚本文件", txt: "文本格式", vb: "Visual Basic的一种宏语言", xml: "扩展标记语言", xls: "Microsoft Office Excel 97-2003 工作表", xlsx: "Microsoft Office Excel 2007 工作表", gz: "压缩文件", zip: "ZIP压缩文件", z: "", "7z": "7Z压缩文件", json: 'JSON文本', php: 'PHP源文件', mht: 'MHTML文档', bmp: 'BMP图片文件', webp: 'WEBP图片文件', cdr: 'CDR文件' };
      return typeof config[ext] != "undefined" ? config[ext] : ('未知文件');
    },

    /**
     * @description 文件类型判断，或返回格式类型(不传入type)
     * @param {String} ext 
     * @param {String} type
     * @return {Boolean|Object} 返回类型或类型是否支持
     */
    determine_file_type: function(ext, type) {
        var config = {
                images: ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'ico', 'JPG', 'webp'],
                compress: ['zip', 'rar', 'gz', 'war', 'tgz'],
                video: ['mp4', 'mp3', 'mpeg', 'mpg', 'mov', 'avi', 'webm', 'mkv', 'mkv', 'mp3', 'rmvb', 'wma', 'wmv'],
                ont_text: ['iso', 'xlsx', 'xls', 'doc', 'docx', 'tiff', 'exe', 'so', '7z', 'bz', 'dmg', 'apk', 'pptx', 'ppt', 'xlsb', 'pdf']
            },
            returnVal = false;
        if (type != undefined) {
            if (type == 'text') {
                $.each(config, function(key, item) {
                    $.each(item, function(index, items) {
                        if (items == ext) {
                            returnVal = true;
                            return false;
                        }
                    })
                });
                returnVal = !returnVal
            } else {
                if (typeof config[type] == "undefined") return false;
                $.each(config[type], function(key, item) {
                    if (item == ext) {
                        returnVal = true;
                        return false;
                    }
                });
            }
        } else {
            $.each(config, function(key, item) {
                $.each(item, function(index, items) {
                    if (items == ext) {
                        returnVal = key;
                        return false;
                    }
                })
            });
            if (typeof returnVal == "boolean") returnVal = 'text';
        }
        return returnVal;
    },

    /**
     * @description 右键菜单事件组
     * @param {Object} data 当前文件或文件夹右键点击的数据和数组下标，以及Dom元素 
     * @return void 
     */
    file_groud_event: function(data) {
        var that = this;
        switch (data.open) {
            case 'open': // 打开目录、文件编辑、预览图片、播放视频
                if (data.type == 'dir') {
                    this.reader_file_list({ path: data.path });
                } else {
                    switch (data.open_type) {
                        case 'text':
                            openEditorView(0, data.path)
                            break;
                        case 'video':
                            this.open_video_play(data);
                            break;
                        case 'images':
                            this.open_images_preview(data);
                            break;
                    }
                }
                break;
            case 'download': //下载
                this.down_file_req(data);
                break;
            case 'share': // 添加分享文件
                this.set_file_share(data);
                break;
            case 'cancel_share': // 取消分享文件
                this.info_file_share(data);
                break;
            case 'favorites': //添加收藏夹
                this.$http('add_files_store', { path: data.path }, function(res) {
                    if (res.status) {
                        that.file_list[data.index] = $.extend(that.file_list[data.index], { caret: true });
                        that.reader_file_list_content(that.file_list);
                        that.load_favorites_index_list();
                    }
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 });
                });
                break;
            case 'cancel_favorites': //取消收藏
                this.cancel_file_favorites(data);
                break;
            case 'authority': // 权限
                this.set_file_authority(data);
                break;
            case 'dir_kill': //目录查杀
                this.set_dir_kill(data);
                break;
            case 'copy': // 复制内容
                this.copy_file_or_dir(data);
                break;
            case 'shear': // 剪切内容
                this.cut_file_or_dir(data);
                break;
            case 'rename': // 重命名
                this.rename_file_or_dir(data);
                break;
            case 'compress':
                data['open'] = 'tar_gz';
                this.compress_file_or_dir(data);
                break;
            case 'tar_gz': // 压缩gzip文件
            case 'rar': // 压缩rar文件
            case 'zip': // 压缩zip文件
                this.compress_file_or_dir(data);
                break;
            case 'unzip':
            case 'folad': //解压到...
                this.unpack_file_to_path(data)
                break;
            case 'refresh': // 刷新文件列表
                $('.file_path_refresh').click();
                break;
            case 'upload': //上传文件
                this.file_drop.dialog_view();
                break;
            case 'soft_link': //软链接创建
                this.set_soft_link();
                break;
            case 'create_dir': // 新建文件目录
                $('.file_nav_view .create_file_or_dir li').eq(0).click();
                break;
            case 'create_files': // 新建文件列表
                $('.file_nav_view .create_file_or_dir li').eq(1).click();
                break;
            case 'del': //删除
                this.del_file_or_dir(data);
                break;
            case 'paste': //粘贴
                this.paste_file_or_dir();
                break;
            case 'web_shell': // 终端
                web_shell()
                break;
            case 'open_find_dir': // 打开文件所在目录
                this.reader_file_list({ path: this.retrun_prev_path(data.path) });
                break;
            case 'property':
                this.open_property_view(data)
            break;
        }
    },
    /**
     * @descripttion 列表批量处理
     * @param {String} stype 操作
     * @return: 无返回值
     */
    batch_file_manage: function(stype) {
        var that = this,
            _api = '',
            _fname = [],
            _obj = {},
            _path = $('');
        $.each(this.file_table_arry, function(index, item) {
            _fname.push(item.filename)
        })
        switch (stype) {
            case 'copy': //复制
            case 'shear': //剪切
                _api = 'SetBatchData';
                _obj['data'] = JSON.stringify(_fname);
                _obj['type'] = stype == 'copy' ? '1' : '2';
                _obj['path'] = that.file_path;
                break;
            case 'del': //删除
                _obj['data'] = JSON.stringify(_fname);
                _obj['type'] = '4';
                _obj['path'] = that.file_path;
                return that.batch_file_delect(_obj)
                break;
            case 'authority': //权限
                _obj['filename'] = '批量';
                _obj['type'] = '3'
                _obj['filelist'] = JSON.stringify(_fname);
                _obj['path'] = that.file_path;
                return that.set_file_authority(_obj, true)
                break;
            case 'compress': //压缩
                var arry_f = that.file_path.split('/'),
                    file_title = arry_f[arry_f.length - 1];
                _obj['filename'] = _fname.join(',');
                _obj['open'] = 'tar_gz'
                _obj['path'] = that.file_path + '/' + file_title;
                return that.compress_file_or_dir(_obj, true)
                break;
        }
        // 批量标记
        that.$http(_api, _obj, function(res) {
            if (res.status) {
                bt.set_cookie('record_paste_type', stype == 'copy' ? '1' : '2')
                that.clear_table_active();
                $('.nav_group.multi').addClass('hide');
                $('.file_menu_tips').removeClass('hide');
                $('.file_nav_view .file_all_paste').removeClass('hide');
            }
            layer.msg(res.msg, { icon: res.status ? 1 : 2 })
        });
    },
    /**
     * @descripttion 批量删除
     * @param {Object} obj.data   需删除的数据
     * @param {Object} obj.type   批量删除操作
     * @return: 无返回值
     */
    batch_file_delect: function(obj) {
        var that = this;
        if (that.is_recycle) {
            layer.confirm('确认删除选中内容,删除后将移至回收站，是否继续操作?', { title: '批量删除', closeBtn: 2, icon: 3 }, function() {
                that.$http('SetBatchData', obj, function(res) {
                    if (res.status) that.reader_file_list({ path: that.file_path })
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                });
            })
        } else {
            bt.show_confirm('批量删除', '<span><i style="font-size: 15px;font-style: initial;color: red;">当前未开启回收站，批量删除后将无法恢复，是否继续删除?</i></span>', function() {
                that.$http('SetBatchData', obj, function(res) {
                    if (res.status) that.reader_file_list({ path: that.file_path })
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                });
            })
        }
    },
    /**
     * @description 批量文件粘贴
     * @return void
     */
    batch_file_paste: function() {
        var that = this,
            _pCookie = bt.get_cookie('record_paste_type');
        this.check_exists_files_req({ dfile: this.file_path }, function(result) {
            if (result.length > 0) {
                var tbody = '';
                for (var i = 0; i < result.length; i++) {
                    tbody += '<tr><td><span class="exists_files_style">' + result[i].filename + '</td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
                }
                var mbody = '<div class="divtable" style="max-height:350px;overflow:auto;"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
                            <tbody>' + tbody + '</tbody>\
                            </table></div>';
                SafeMessage('即将覆盖以下文件', mbody, function() {
                    that.$http('BatchPaste', { type: _pCookie, path: that.file_path }, function(rdata) {
                        if (rdata.status) {
                            bt.set_cookie('record_paste_type', null);
                            that.reader_file_list({ path: that.file_path })
                        }
                        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 })
                    })
                });
            } else {
                that.$http('BatchPaste', { type: _pCookie, path: that.file_path }, function(rdata) {
                    if (rdata.status) {
                        bt.set_cookie('record_paste_type', null);
                        that.reader_file_list({ path: that.file_path })
                    }
                    layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 })
                })
            }

        })
    },

    /**
     * @description 文件内容替换
     * @return void
     */
    replace_content_view: function() {
        layer.open({
            title:  '文件内容替换',
            type:1,
            skin:'replace_content_view',
            area:['795px','482px'],
            closeBtn:2,
            content:'<div class="replace_content_view">\
                <div class="tab-nav mlr20">\
                    <span class="on">查找</span><span>替换</span>\
                </div>\
                <div id="check_content" class="bt-form" style="height: 330px;padding: 20px 20px 0;">\
                    <div class="line">\
                        <span class="tname">查找</span>\
                        <div class="info-r">\
                            <input name="checkContentValue" id="checkContentValue" class="bt-input-text mr5" type="text" placeholder="请输入查找的文件内容，可点击右侧图标选择筛查方式" style="width:390px">\
                            <div class="file_search_config">\
                                <input type="checkbox" class="file_search_checked" id="outInfoOption" name="outInfoOption">\
                                <label class="laberText" for="outInfoOption">输出行信息</label>\
                            </div>\
                            <button class="btn btn-default btn-sm" onclick="bt_file.searchContent()" style="width: 75px;background-color: #10952a;color: #fff;">查找</button>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">文件类型</span>\
                        <div class="info-r">\
                            <input name="checkFileExtsType" id="checkFileExtsType" class="bt-input-text mr5" type="text" value="php,html" style="width:390px">\
                        </div>\
                    </div>\
                    <div class="line seniorOption" style="display: none;">\
                        <span class="tname"></span>\
                        <div class="info-r">\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="regularMatch" name="regularMatch">\
                                <label class="laberText" for="regularMatch">正则模式</label>\
                            </div>\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="allMatch" name="allMatch">\
                                <label class="laberText" for="allMatch">全词匹配</label>\
                            </div>\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="distinguishCase" name="distinguishCase">\
                                <label class="laberText" for="distinguishCase">不区分大小写</label>\
                            </div>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">目录</span>\
                        <div class="info-r">\
                            <input class="bt-input-text mr5" type="text" style="width:390px" id="checkContentPath">\
                            <div class="file_search_config">\
                                <input type="checkbox" class="file_search_checked" id="checkHasChild" name="checkHasChild">\
                                <label class="laberText" for="checkHasChild">包含子目录</label>\
                            </div>\
                            <span class="glyphicon cursor mr5 glyphicon-folder-open" onclick="bt.select_path(\'checkContentPath\')"></span>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname"></span>\
                        <div class="info-r">\
                            <button class="btn btn-default btn-sm seniorOptionBtn" style="width: 75px;" id="seniorOptionBtn" data="false">高级选项</button>\
                        </div>\
                    </div>\
                    <div class="line fileOutContent"></div>\
                </div>\
                <div id="replace_content" class="bt-form pd20" style="height: 300px;display:none;">\
                    <div class="line">\
                        <span class="tname">查找</span>\
                        <div class="info-r">\
                            <input id="replaceContentValue" class="bt-input-text mr5" type="text" placeholder="请输入查找的文件内容，可点击右侧图标选择筛查方式" style="width:390px">\
                            <div class="file_search_config">\
                                <input type="checkbox" class="file_search_checked" id="outInfoOptionRe" name="outInfoOptionRe">\
                                <label class="laberText" for="outInfoOptionRe">输出行信息</label>\
                            </div>\
                            <button class="btn btn-default btn-sm" onclick="bt_file.searchReplaceContent()" style="width: 75px;background-color: #10952a;color: #fff;">查找</button>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">文件类型</span>\
                        <div class="info-r">\
                            <input name="replaceFileExtsType" id="replaceFileExtsType" class="bt-input-text mr5" type="text" value="php,html" style="width:390px">\
                        </div>\
                    </div>\
                    <div class="line seniorOptionRe" style="display: none;">\
                        <span class="tname"></span>\
                        <div class="info-r">\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="regularMatchRe" name="regularMatchRe">\
                                <label class="laberText" for="regularMatchRe">正则模式</label>\
                            </div>\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="allMatchRe" name="allMatchRe">\
                                <label class="laberText" for="allMatchRe">全词匹配</label>\
                            </div>\
                            <div class="checkbox_config">\
                                <input type="checkbox" class="file_search_checked" id="distinguishCaseRe" name="distinguishCaseRe">\
                                <label class="laberText" for="distinguishCaseRe">不区分大小写</label>\
                            </div>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">替换</span>\
                        <div class="info-r">\
                            <input id="replaceFileValue" class="bt-input-text mr5" type="text" placeholder="请输入替换的内容" style="width:390px">\
                            <button class="btn btn-default btn-sm" style="width: 75px;background-color: #10952a;color: #fff;" onclick="bt_file.replaceContentFn()">替换</button>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname"></span>\
                        <div class="info-r" style="height:17px;">\
                            <span style="color: red;">替换内容可能导致程序无法正常运行，请确保替换内容正确，如果替换出错，请查看<a style="color:green;">备份文件</a></span>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname">目录</span>\
                        <div class="info-r">\
                            <input class="bt-input-text mr5" type="text" style="width:390px" id="replaceContentPath">\
                            <div class="file_search_config">\
                                <input type="checkbox" class="file_search_checked" id="replaceHasChild" name="replaceHasChild">\
                                <label class="laberText" for="replaceHasChild">包含子目录</label>\
                            </div>\
                            <span class="glyphicon cursor mr5 glyphicon-folder-open" onclick="bt.select_path(\'replaceContentPath\')"></span>\
                        </div>\
                    </div>\
                    <div class="line">\
                        <span class="tname"></span>\
                        <div class="info-r">\
                            <button class="btn btn-default btn-sm seniorOptionReplaceBtn" style="width: 75px;" id="seniorOptionReplaceBtn" data="false">高级选项</button>\
                            <button class="btn btn-default btn-sm" style="width: 75px;" onclick="bt_file.replaceContentLog()">操作日志</button>\
                        </div>\
                    </div>\
                    <div class="line reFileOutContent"></div>\
                </div>\
            </div>',
            success:function(){
            }
        });
        $(".replace_content_view").on('click', '.tab-nav span', function() {
            var index = $(this).index();
            $(this).addClass('on').siblings().removeClass('on');
            if (index == 0) {
                $("#check_content").show();
                $("#replace_content").hide();
            } else {
                $("#replace_content").show();
                $("#check_content").hide();
            }
        });
        $('#seniorOptionBtn').on('click', function() {
            var temp = $(this).attr('data')
            $(this).attr('data', temp == 'false' ? 'true':'false')
            if(temp == 'false') {
                $('.seniorOption').show()
                $('.seniorOptionBtn').css({
                    'background-color': '#10952a',
                    'color': '#fff',
                    'border-color': '#398439'
                })
            } else {
                $('.seniorOption').hide()
                $('.seniorOptionBtn').css({
                    'background-color': '#fff',
                    'color': '#555',
                    'border-color': '#ccc'
                })
            }
        })
        $('#seniorOptionReplaceBtn').on('click', function() {
            var temp = $(this).attr('data')
            $(this).attr('data', temp == 'false' ? 'true':'false')
            if(temp == 'false') {
                $('.seniorOptionRe').show()
                $('.seniorOptionReplaceBtn').css({
                    'background-color': '#10952a',
                    'color': '#fff',
                    'border-color': '#398439'
                })
            } else {
                $('.seniorOptionRe').hide()
                $('.seniorOptionReplaceBtn').css({
                    'background-color': '#fff',
                    'color': '#555',
                    'border-color': '#ccc'
                })
            }
        })
    },
    //text 搜索内容
    searchContent: function() {
        var data = {
            text: $('#checkContentValue').val(),
            exts: $("#checkFileExtsType").val(),    //参数例子 php,html
            path: $('#checkContentPath').val(),                             //路径
            is_subdir: !$('#checkHasChild').prop('checked') ? '0' : '1',    //不包含子目录 1 包含子目录
            mode: !$('#regularMatch').prop('checked') ? '0' : '1',          //为普通模式 1 为正则模式
            isword: !$('#allMatch').prop('checked') ? '0' : '1',            //全词匹配 0 默认
            iscase: !$('#distinguishCase').prop('checked') ? '0' : '1',     //不区分大小写 0 默认
            noword: !$('#outInfoOption').prop('checked') ? '0' : '1'        //不输出行信息 0 默认
        }
        this.$http('files_search',data,function(res) {
            if(res.error) {
                layer.msg(res.error, { icon: 2 })
            } else {
                if($('#outInfoOption').prop('checked') == true) {
                    var html = ''
                    for(var i = 0; i < res.length; i++) {
                        html += '<div>'+ i + '：' + res[i] +'</div>'
                    }
                    $('.fileOutContent').html(html)
                }
            }
        })
    },
    //text 替换搜索内容
    searchReplaceContent: function() {
        var data = {
            text: $('#replaceContentValue').val(),
            exts: $("#replaceFileExtsType").val(),     //参数例子 php,html
            path: $('#replaceContentPath').val(),     //路径
            is_subdir: !$('#replaceHasChild').prop('checked') ? '0' : '1',    //不包含子目录 1 包含子目录
            mode: !$('#regularMatchRe').prop('checked') ? '0' : '1',          //为普通模式 1 为正则模式
            isword: !$('#allMatchRe').prop('checked') ? '0' : '1',            //全词匹配 0 默认
            iscase: !$('#distinguishCaseRe').prop('checked') ? '0' : '1',     //不区分大小写 0 默认
            noword: !$('#outInfoOptionRe').prop('checked') ? '0' : '1'        //不输出行信息 0 默认
        }
        this.$http('files_search',data,function(res) {
            if(res.error) {
                layer.msg(res.error, { icon: 2 })
            } else {
                if($('#outInfoOptionRe').prop('checked') == true) {
                    var html = ''
                    for(var i = 0; i < res.length; i++) {
                        html += '<div>'+ i + '：' + res[i] +'</div>'
                    }
                    $('.reFileOutContent').html(html)
                }
            }
        })
    },
    //text 文件内容替换
    replaceContentFn: function() {
        var data = {
            text: $('#replaceContentValue').val(),
            is_subdir: !$('#replaceHasChild').prop('checked') ? '0' : '1',    //不包含子目录 1 包含子目录
            rtext: $('#replaceFileValue').val(),                              //替换内容
            exts: $("#replaceFileExtsType").val(),                            //参数例子 php,html
            path: $('#replaceContentPath').val(),                             //路径
            mode: !$('#regularMatchRe').prop('checked') ? '0' : '1',          //为普通模式 1 为正则模式
            isword: !$('#allMatchRe').prop('checked') ? '0' : '1',            //全词匹配 0 默认
            iscase: !$('#distinguishCaseRe').prop('checked') ? '0' : '1',     //不区分大小写 0 默认
            noword: !$('#outInfoOptionRe').prop('checked') ? '0' : '1'        //不输出行信息 0 默认
        }
        this.$http('files_replace', data,function(res) {

        })
    },
    //text 文件内容操作日志
    replaceContentLog: function() {
        this.$http('get_replace_logs', {},function(res) {
            layer.open({
                type:1,
                title: '文件内容替换日志',
                area: ['700px','490px'],
                shadeClose:false,
                closeBtn:2,
                content:'<div class="setchmod bt-form  pb70">\
                        <pre class="crontab-log" style="overflow: auto; border: 0 none; line-height:23px;padding: 15px; margin: 0;white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0;"></pre>\
                            <div class="bt-form-submit-btn" style="margin-top: 0">\
                            <button type="button" class="btn btn-danger btn-sm btn-title" id="clearLogs" style="margin-right:15px;">'+ lan['public']['empty'] +'</button>\
                            <button type="button" class="btn btn-success btn-sm btn-title" onclick="layer.closeAll()">'+ lan['public']['close'] +'</button>\
                        </div>\
                    </div>',
                success:function(){
                    var log_body = res.msg.data === '' ? '当前日志为空': res.msg.data, res = $(".setchmod pre"),crontab_log = $('.crontab-log')[0]
                    setchmod.text(log_body);
                    crontab_log.scrollTop = crontab_log.scrollHeight;
                }
            })
        })
    },
    /**
     * @description 回收站视图
     * @return void
     */
    recycle_bin_view: function() {
        var that = this;
        layer.open({
            title:lan.files.recycle_bin_title,
            type:1,
            skin:'recycle_view',
            area:['1100px','672px'],
            closeBtn:2,
            content:'<div class="recycle_bin_view">\
                <div class="re-head">\
                    <div style="margin-left: 3px;" class="ss-text">\
                        <em>' + lan.files.recycle_bin_on + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox">\
                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="bt_file.Set_Recycle_bin()"></label>\
                        </div>\
                        <em style="margin-left: 20px;">' + lan.files.recycle_bin_on_db + '</em>\
                        <div class="ssh-item">\
                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox">\
                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="bt_file.Set_Recycle_bin(1)"></label>\
                        </div>\
                    </div>\
                    <span style="line-height: 32px; margin-left: 30px;">' + lan.files.recycle_bin_ps + '</span>\
                    <button style="float: right" class="btn btn-default btn-sm" onclick="bt_file.CloseRecycleBin();">' + lan.files.recycle_bin_close + '</button>\
                </div>\
                <div class="re-con">\
                    <div class="re-con-menu">\
                        <p class="on" data-type="1">' + lan.files.recycle_bin_type1 + '</p>\
                        <p data-type="2">' + lan.files.recycle_bin_type2 + '</p>\
                        <p data-type="3">' + lan.files.recycle_bin_type3 + '</p>\
                        <p data-type="4">' + lan.files.recycle_bin_type4 + '</p>\
                        <p data-type="5">' + lan.files.recycle_bin_type5 + '</p>\
                        <p data-type="6">' + lan.files.recycle_bin_type6 + '</p>\
                    </div>\
                    <div class="re-con-con pd15" id="recycle_table"></div>\
                </div>\
            </div>',
            success:function(){
                if (window.location.href.indexOf("database") != -1) {
                    $(".re-con-menu p:last-child").addClass("on").siblings().removeClass("on");
                    $(".re-con-menu p:eq(5)").click();
                } else {
                    $(".re-con-menu p:eq(0)").click();
                }
                var render_config = that.render_recycle_list();
                $(".re-con-menu").on('click', 'p', function() {
                    var _type = $(this).data('type');
                    $(this).addClass("on").siblings().removeClass("on");
                    render_config.$refresh_table_list(true);
                });
            }
        })
    },
    // 回收站渲染列表
    render_recycle_list: function() {
        var that = this;
        $('#recycle_table').empty()
        var recycle_list = bt_tools.table({
            el:'#recycle_table',
            url:'/files?action=Get_Recycle_bin',
            height:480,
            dataFilter:function(res){
                var files = [];
                switch($('.re-con-menu p.on').index()){
                    case 0:
                        for (var i = 0; i < res.dirs.length; i++){
                            var item = res.dirs[i];
                            files.push($.extend(item,{type:'folder'}));
                        }
                        for (var j = 0; j < res.files.length; j++){
                            var item = res.files[j],ext_list =  item.dname.split('.') ,ext = that.determine_file_type(ext_list[ext_list.length - 1]);
                            if(item.name.indexOf('BTDB_') > -1) {
                                item.dname = item.dname.replace('BTDB_', '');
                                item.name = item.name.replace('BTDB_', '');
                                files.push($.extend(item,{type:'files'}));
                            }else if(ext == 'images'){
                                files.push($.extend(item,{type:ext}));
                            }else{
                                files.push($.extend(item,{type:'files'}));
                            }
                        }
                    break;
                    case 1:
                        for (var i = 0; i < res.dirs.length; i++){
                            var item = res.dirs[i];
                            files.push($.extend(item,{type:'folder'}));
                        }

                    break;
                    case 2:
                        for (var j = 0; j < res.files.length; j++){
                            var item = res.files[j],ext_list =  item.dname.split('.') ,ext = that.determine_file_type(ext_list[ext_list.length - 1]);
                            if(item.name.indexOf('BTDB') == -1) files.push($.extend(item,{type:ext}));
                        }
                    break;
                    case 3:
                        for (var j = 0; j < res.files.length; j++){
                            var item = res.files[j],ext_list =  item.dname.split('.') ,ext = that.determine_file_type(ext_list[ext_list.length - 1]);
                            if(ext == 'images') files.push($.extend(item,{type:ext}));
                        }

                    break;
                    case 4:
                        for (var j = 0; j < res.files.length; j++){
                            var item = res.files[j],ext_list =  item.dname.split('.') ,ext = that.determine_file_type(ext_list[ext_list.length - 1]);
                            if(ext != 'images' && ext != 'compress' && ext != 'video' && item.name.indexOf('BTDB') == -1) files.push($.extend(item,{type:ext}));
                        }
                    break;
                    case 5:
                        for (var j = 0; j < res.files.length; j++){
                            var item = res.files[j];
                            if(item.name.indexOf('BTDB_') > -1){
                                item.dname = item.dname.replace('BTDB_','');
                                item.name = item.name.replace('BTDB_','');
                                files.push($.extend(item,{type:'files'}));
                            }
                        }
                        // for (var filesKey in files) {
                        //     if(files.hasOwnProperty(filesKey))
                        // }
                    break;
                }
                $('#Set_Recycle_bin').attr('checked', res.status);
                $('#Set_Recycle_bin_db').attr('checked', res.status_db);
                return {data:files}
            },
            column:[
                {type:'checkbox','class':'',width:18},
                {fid:'name',title:lan.files.recycle_bin_th1,width:155,template:function(row){
                    return '<div class="text-overflow" title="'+ row.name +'"><i class="file_icon file_'+ row.type +'"></i><span style="width:100px">'+ row.name +'</span></div>';
                }},
                {fid:'dname',title:lan.files.recycle_bin_th2,width:310,template:function(row){
                    return '<span class="text-overflow" style="width:310px" title="'+ row.dname +'">'+ row.dname +'</span>';
                }},
                {fid:'size',title:lan.files.recycle_bin_th3,width:70,template:function(row){
                    return '<span class="text-overflow" style="width:70px" title="'+ row.size +'">'+ bt.format_size(row.size) +'</span>';
                }},
                {fid:'time',title:lan.files.recycle_bin_th4,width:120,template:function(row, index){
                    return '<span class="text-overflow" style="width:120px" title="'+ row.time +'">'+ bt.format_data(row.time) + '</span>'
                }},
                {type:'group',align:'right',width:95,title:lan.files.recycle_bin_th5,group:[{
                    title:lan.files.recycle_bin_re,
                    event:function(row, index, ev, key, that){
                        bt_file.ReRecycleBin(row.rname,function(){
                            that.$delete_table_row(index);
                        });
                    }
                },{
                    title:lan.files.recycle_bin_del,
                    event:function(row, index, ev, key, that){
                        bt_file.DelRecycleBin(row,function(){
                            that.$delete_table_row(index);
                        });
                    }
                }]}
            ],
            tootls: [{ // 批量操作
                type: 'batch',//batch_btn
                positon: ['left', 'bottom'],
                placeholder: '请选择批量操作',
                buttonValue: '批量操作',
                disabledSelectValue: '请选择需要批量操作的端口!',
                selectList:[{
                    title:"恢复",
                    url:'/files?action=Re_Recycle_bin',
                    load:true,
                    param:function(row){
                        return {path:row.rname};
                    },
                    callback:function(that){
                        bt.confirm({title:'批量恢复文件',msg:'是否批量恢复选中的文件，是否继续？',icon:0},function(index){
                            layer.close(index);
                            that.start_batch({},function(list){
                                var html = '';
                                for(var i=0;i<list.length;i++){
                                    var item = list[i];
                                    html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ (item.request.status?'恢复成功':'恢复失败') +'</span></div></td></tr>';
                                }
                                recycle_list.$batch_success_table({title:'批量恢复文件',th:'文件名称',html:html});
                                recycle_list.$refresh_table_list(true);
                            });
                        });
                    }
                },{
                    title:"永久删除文件",
                    url:'/files?action=Del_Recycle_bin',
                    load:true,
                    param:function(row){
                        return {path:row.rname};
                    },
                    callback:function(that){
                        bt.confirm({title:'批量删除文件',msg:'是否批量删除选中的文件，文件将彻底删除，不可恢复，是否继续？',icon:0},function(index){
                            layer.close(index);
                            that.start_batch({},function(list){
                                var html = '';
                                for(var i=0;i<list.length;i++){
                                    var item = list[i];
                                    html += '<tr><td>'+ item.name +'</td><td><div style="float:right;"><span style="color:'+ (item.request.status?'#20a53a':'red') +'">'+ (item.request.status?'删除成功':'删除失败') +'</span></div></td></tr>';
                                }
                                recycle_list.$batch_success_table({title:'批量删除文件',th:'文件名称',html:html});
                                recycle_list.$refresh_table_list(true);
                            });
                        });
                    }
                }]
            }]
        });
        bt_tools.$fixed_table_thead('#recycle_table .divtable');
        return recycle_list
    },
    // 回收站开关
    Set_Recycle_bin: function(db) {
        var loadT = layer.msg(lan['public'].the, { icon: 16, time: 0, shade: [0.3, '#000'] });
        var that = this,
            data = {}
        if (db == 1) {
            data = { db: db };
        }
        $.post('/files?action=Recycle_bin', data, function(rdata) {
            layer.close(loadT);
            if (rdata.status) {
                if (db == undefined){
                    var _status = $('#Set_Recycle_bin').prop('checked')
                    that.is_recycle = _status;
                    bt.set_cookie('file_recycle_status',_status);
                } 
            }
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
        });
    },
    // 回收站恢复
    ReRecycleBin: function(path,callback) {
        layer.confirm(lan.files.recycle_bin_re_msg, { title: lan.files.recycle_bin_re_title, closeBtn: 2, icon: 3 }, function() {
            var loadT = layer.msg(lan.files.recycle_bin_re_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.post('/files?action=Re_Recycle_bin', 'path=' + encodeURIComponent(path), function(rdata) {
                layer.close(loadT);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                if(callback) callback(rdata)
            });
        });
    },
    //回收站删除
    DelRecycleBin: function(row,callback) {
      bt.prompt_confirm(lan.files.recycle_bin_del_title, '您确定要删除文件['+ row.name +']吗，该操作将<span style="color:red;">永久删除改文件</span>，是否继续操作？', function () {
          var loadT = layer.msg(lan.files.recycle_bin_del_the, { icon: 16, time: 0, shade: [0.3, '#000'] });
            $.post('/files?action=Del_Recycle_bin', 'path=' + encodeURIComponent(row.rname), function(rdata) {
                layer.close(loadT);
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
                if(callback) callback(rdata)
            });
        });
    },
    //清空回收站
    CloseRecycleBin: function() {
      var _this = this;
      bt.prompt_confirm(lan.files.recycle_bin_close, '您确定要清空回收站吗，该操作将<span style="color:red;">永久删除文件</span>，是否继续操作？', function () {          var loadT = layer.msg("<div class='myspeed'>" + lan.files.recycle_bin_close_the + "</div>", { icon: 16, time: 0, shade: [0.3, '#000'] });
          setTimeout(function() {
            getSpeed('.myspeed');
          }, 1000);
          $.post('/files?action=Close_Recycle_bin', '', function(rdata) {
            layer.close(loadT);
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 5 });
            _this.render_recycle_list()
            $("#RecycleBody").html('');
          });
        });
    },
    /**0
     * @param {Object} data 当前文件的数据对象
     * @return void
    */
    open_property_view:function (data) { 
      var _this = this;
      _this.$http('get_file_attribute',{filename:data.path},function (res) { 
        layer.open({
          type: 1,
          closeBtn: 2,
          title: '[ ' + data.filename +' ] - '+ (data.is_dir?'文件夹':'文件') +'属性',
          area: ["580px", "500px"],
          shadeClose: false,
          // btn:['确认','取消'],
          content:'<div class="bt-property-setting pd15">\
            <div class="tab-nav">\
              <span class="on">常规</span>\
              <span>详细信息</span>\
              <span>历史版本</span>\
            </div>\
            <div class="tab-con">\
              <div class="property-box file_list_content  active">\
                <div class="attr-box">\
                  <div class="attr-name" style="height: 60px;line-height: 60px;"><i class="file_icon file_'+ (res.is_link?'link':(res.is_dir?'folder':res.st_type))  +'"></i></div>\
                  <div class="attr-content" style="height: 60px;line-height: 60px;"><input type="text" disabled value="'+ data.filename +'" /></div>\
                </div>\
                <div class="dividing"></div>\
                <div class="attr-box" >\
                  <div class="attr-name">类型:</div>\
                  <div class="attr-content">'+ ((res.is_dir || res.is_link)?res.st_type:_this.ext_type_tips(res.st_type)) +'</div>\
                </div>\
                <div class="attr-box" >\
                  <div class="attr-name">文件路径:</div>\
                  <div class="attr-content"><span title="'+ res.path +'">'+ res.path +'</span></div>\
                </div>\
                <div class="attr-box" >\
                  <div class="attr-name">大小:</div>\
                  <div class="attr-content">'+ bt.format_size(res.st_size) +' ('+(_this.font_thousandth(res.st_size) + ' 字节')+')'+'</div>\
                </div>\
                <div class="dividing"></div>\
                <div class="attr-box">\
                  <div class="attr-name">权限:</div>\
                  <div class="attr-content">'+ res.mode +'</div>\
                </div>\
                <div class="attr-box">\
                  <div class="attr-name">所属组:</div>\
                  <div class="attr-content">'+ res.group +'</div>\
                </div>\
                <div class="attr-box">\
                  <div class="attr-name">所属用户:</div>\
                  <div class="attr-content">'+ res.user +'</div>\
                </div>\
                <div class="dividing"></div>\
                <div class="attr-box">\
                  <div class="attr-name">访问时间:</div>\
                  <div class="attr-content">'+ bt.format_data(res.st_atime) +'</div>\
                </div>\
                <div class="attr-box">\
                  <div class="attr-name">修改时间:</div>\
                  <div class="attr-content">'+ bt.format_data(res.st_mtime) +'</div>\
                </div>\
              </div>\
              <div class="property-box details_box_view">\
                <table>\
                  <thead><tr><th><div style="width:100px">属性</div></th><th><div style="width:400px">值</div></th></tr></thead>\
                  <tbody class="details_list"></tbody>\
                </table>\
              </div>\
              <div class="property-box history_box_view" >\
                <table>\
                  <thead><tr><th><div style="width:140px;">修改时间</div></th><th><div style="width:85px;">文件大小</div></th><th><div >MD5</div></th><th><div style="width:90px;text-align:right;">操作</div></th></tr></thead>\
                  <tbody class="history_list"></tbody>\
                </table>\
              </div>\
            </div>\
          </div>',
          success:function(layero,index){
            $('.bt-property-setting .tab-nav span').click(function () {
              var index =  $(this).index();
              $(this).addClass('on').siblings().removeClass('on');
              $('.property-box:eq('+index +')').addClass('active').siblings().removeClass('active');
            })
            $('.history_box_view').on('click','.open_history_file',function(){
              var _history = $(this).attr('data-time');
              openEditorView(0,data.path)
              setTimeout(function () {
                aceEditor.openHistoryEditorView({filename:data.path,history:_history},function(){
                  layer.close(index)
                  $('.ace_conter_tips').show();
                  $('.ace_conter_tips .tips').html('只读文件，文件为'+ _item.path +'，历史版本 [ '+ bt.format_data(new Number(_history)) +' ]<a href="javascript:;" class="ml35 btlink" data-path="'+ _item.path +'" data-history="'+ _history +'">点击恢复当前历史版本</a>');
                });
              },500)
            });
            $('.history_box_view').on('click','.recovery_file_historys',function(){
              aceEditor.event_ecovery_file(this);
            });
            var config = {
              filename:['文件名',data.filename],
              type:['类型',(res.is_dir || res.is_link)?res.st_type:_this.ext_type_tips(res.st_type)],
              path:'文件路径',
              st_size:['文件大小',bt.format_size(res.st_size) +' ('+(_this.font_thousandth(res.st_size) + ' 字节')+')'],
              st_atime:['访问时间',bt.format_data(res.st_atime)],st_mtime:['修改时间',bt.format_data(res.st_mtime)],st_ctime:['元数据修改时间',bt.format_data(res.st_ctime)],
              md5:'文件MD5',sha1:'文件sha1',
              user:'所属用户',group:'所属组',mode:'文件权限',lsattr:'特殊权限',
              st_uid:'用户id',st_gid:'用户组id',
              st_nlink:'inode的链接数',st_ino:'inode的节点号',st_mode:'inode保护模式',st_dev:'inode驻留设备',
            },html = '',html2= '';
            for (var key in config) {
              if (Object.hasOwnProperty.call(config, key)) {
                var element = config[key],value = ($.isArray(element)?element[1]:res[key]);
                html += '<tr><td><div style="width:110px">'+ ($.isArray(element)?element[0]:element) +'</div></td><td><div class="ellipsis" style="width:400px" title="'+ value +'">'+ value +'</div></td></tr>';
              }
            }
            for (var i = 0; i < res.history.length; i++) {
              var item = res.history[i];
              html2 += '<tr><td><div style="width:140px;">'+ bt.format_data(item.st_mtime) +'</div></td><td><div style="width:85px;">'+ bt.format_size(item.st_size) +'</div></td><td><div>'+ item.md5 +'</div></td><td><div style="width:90px;text-align:right;"><a href="javascript:;" class="btlink open_history_file" data-time="'+ item.st_mtime +'">查看</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink recovery_file_historys" data-history="'+ item.st_mtime +'" data-path="'+ data.path +'">恢复</a></div></td></tr>'
            }
            if(html2 === '') html2 += '<tr><td colspan="4"><div style="text-align: center;">当前文件无历史版本</div></td></tr>'
            $('.details_list').html(html);
            $('.history_list ').html(html2);
            _this.fixed_table_thead('.details_box_view');
            _this.fixed_table_thead('.history_box_view ');
          }
        })
      })
    },
    /**
     * @description 固定表头
     * @param {string} el DOM选择器
     * @return void
    */
    fixed_table_thead:function(el) {
      $(el).scroll(function () {
          var scrollTop = this.scrollTop;
          this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
      })
    },
    /**
     * @description 字符千分隔符
     * @param {string} el DOM选择器
     * @return void
    */
    font_thousandth:function(num) {
      var source = String(num).split(".");//按小数点分成2部分
        source[0] = source[0].replace(new RegExp('(\\d)(?=(\\d{3})+$)','ig'),"$1,");//只将整数部分进行都好分割
      return source.join(".");//再将小数部分合并进来
    },

    /**
     * @description 打开图片预览
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    open_images_preview: function(data) {
        var that = this,
            mask = $('<div class="preview_images_mask">' +
                '<div class="preview_head">' +
                '<span class="preview_title">' + data.filename + '</span>' +
                '<span class="preview_small hidden" title="缩小显示"><span class="glyphicon glyphicon-resize-small" aria-hidden="true"></span></span>' +
                '<span class="preview_full" title="最大化显示"><span class="glyphicon glyphicon-resize-full" aria-hidden="true"></span></span>' +
                '<span class="preview_close" title="关闭图片预览视图"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></span>' +
                '</div>' +
                '<div class="preview_body"><img id="preview_images" src="/download?filename=' + data.path + '" data-index="' + data.images_id + '"></div>' +
                '<div class="preview_toolbar">' +
                '<a href="javascript:;" title="左旋转"><span class="glyphicon glyphicon-repeat reverse-repeat" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="右旋转"><span class="glyphicon glyphicon-repeat" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="放大视图"><span class="glyphicon glyphicon-zoom-in" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="缩小视图"><span class="glyphicon glyphicon-zoom-out" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="重置视图"><span class="glyphicon glyphicon-refresh" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="图片列表"><span class="glyphicon glyphicon-list" aria-hidden="true"></span></a>' +
                '</div>' +
                '<div class="preview_cut_view">' +
                '<a href="javascript:;" title="上一张"><span class="glyphicon glyphicon-menu-left" aria-hidden="true"></span></a>' +
                '<a href="javascript:;" title="下一张"><span class="glyphicon glyphicon-menu-right" aria-hidden="true"></span></a>' +
                '</div>' +
                '</div>'),
            images_config = { natural_width: 0, natural_height: 0, init_width: 0, init_height: 0, preview_width: 0, preview_height: 0, current_width: 0, current_height: 0, current_left: 0, current_top: 0, rotate: 0, scale: 1, images_mouse: false };
        if ($('.preview_images_mask').length > 0) {
            $('#preview_images').attr('src', '/download?filename=' + data.path);
            return false;
        }
        $('body').css('overflow', 'hidden').append(mask);
        images_config.preview_width = mask[0].clientWidth;
        images_config.preview_height = mask[0].clientHeight;
        // 图片预览
        $('.preview_body img').load(function() {
            var img = $(this)[0];
            if (!$(this).attr('data-index')) $(this).attr('data-index', data.images_id);
            images_config.natural_width = img.naturalWidth;
            images_config.natural_height = img.naturalHeight;
            auto_images_size(false);
        });
        //图片头部拖动
        $('.preview_images_mask .preview_head').on('mousedown', function(e) {
            e = e || window.event; //兼容ie浏览器
            var drag = $(this).parent();
            $('body').addClass('select'); //webkit内核和火狐禁止文字被选中
            $(this).onselectstart = $(this).ondrag = function() { //ie浏览器禁止文字选中
                return false;
            }
            if ($(e.target).hasClass('preview_close')) { //点关闭按钮不能拖拽模态框
                return;
            }
            var diffX = e.clientX - drag.offset().left;
            var diffY = e.clientY - drag.offset().top;
            $(document).on('mousemove', function(e) {
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
                    left: left,
                    top: top,
                    margin: 0
                });
            }).on('mouseup', function() {
                $(this).unbind('mousemove mouseup');
            });
        });
        //图片拖动
        $('.preview_images_mask #preview_images').on('mousedown', function(e) {
            e = e || window.event;
            $(this).onselectstart = $(this).ondrag = function() {
                return false;
            }
            var images = $(this);
            var preview = $('.preview_images_mask').offset();
            var diffX = e.clientX - preview.left;
            var diffY = e.clientY - preview.top;
            $('.preview_images_mask').on('mousemove', function(e) {
                e = e || window.event
                var offsetX = e.clientX - preview.left - diffX,
                    offsetY = e.clientY - preview.top - diffY,
                    rotate = Math.abs(images_config.rotate / 90),
                    preview_width = (rotate % 2 == 0 ? images_config.preview_width : images_config.preview_height),
                    preview_height = (rotate % 2 == 0 ? images_config.preview_height : images_config.preview_width),
                    left, top;
                if (images_config.current_width > preview_width) {
                    var max_left = preview_width - images_config.current_width;
                    left = images_config.current_left + offsetX;
                    if (left > 0) {
                        left = 0
                    } else if (left < max_left) {
                        left = max_left
                    }
                    images_config.current_left = left;
                }
                if (images_config.current_height > preview_height) {
                    var max_top = preview_height - images_config.current_height;
                    top = images_config.current_top + offsetY;
                    if (top > 0) {
                        top = 0
                    } else if (top < max_top) {
                        top = max_top
                    }
                    images_config.current_top = top;
                }
                if (images_config.current_height > preview_height && images_config.current_top <= 0) {
                    if ((images_config.current_height - preview_height) <= images_config.current_top) {
                        images_config.current_top -= offsetY
                    }
                }
                images.css({ 'left': images_config.current_left, 'top': images_config.current_top });
            }).on('mouseup', function() {
                $(this).unbind('mousemove mouseup');
            }).on('dragstart', function() {
                e.preventDefault();
            });
        }).on('dragstart', function() {
            return false;
        });
        //关闭预览图片
        $('.preview_close').click(function(e) {
            $('.preview_images_mask').remove();
        });
        //图片工具条预览
        $('.preview_toolbar a').click(function() {
            var index = $(this).index(),
                images = $('#preview_images');
            switch (index) {
                case 0: //左旋转,一次旋转90度
                case 1: //右旋转,一次旋转90度
                    images_config.rotate = index ? (images_config.rotate + 90) : (images_config.rotate - 90);
                    auto_images_size();
                    break;
                case 2:
                case 3:
                    if (images_config.scale == 3 && index == 2 || images_config.scale == 0.2 && index == 3) {
                        layer.msg((images_config.scale >= 1 ? '图像放大，已达到最大尺寸。' : '图像缩小，已达到最小尺寸。'));
                        return false;
                    }
                    images_config.scale = (index == 2 ? Math.round((images_config.scale + 0.4) * 10) : Math.round((images_config.scale - 0.4) * 10)) / 10;
                    auto_images_size();
                    break;
                case 4:
                    var scale_offset = images_config.rotate % 360;
                    if (scale_offset >= 180) {
                        images_config.rotate += (360 - scale_offset);
                    } else {
                        images_config.rotate -= scale_offset;
                    }
                    images_config.scale = 1;
                    auto_images_size();
                    break;
            }
        });
        // 最大最小化图片
        $('.preview_full,.preview_small').click(function() {
            if ($(this).hasClass('preview_full')) {
                $(this).addClass('hidden').prev().removeClass('hidden');
                images_config.preview_width = that.area[0];
                images_config.preview_height = that.area[1];
                mask.css({ width: that.area[0], height: that.area[1], top: 0, left: 0, margin: 0 }).data('type', 'full');
                auto_images_size();
            } else {
                $(this).addClass('hidden').next().removeClass('hidden');
                $('.preview_images_mask').removeAttr('style');
                images_config.preview_width = 750;
                images_config.preview_height = 650;
                auto_images_size();
            }
        });
        // 上一张，下一张
        $('.preview_cut_view a').click(function() {
            var images_src = '',
                preview_images = $('#preview_images'),
                images_id = parseInt(preview_images.attr('data-index'));
            if (!$(this).index()) {
                images_id = images_id === 0 ? (that.file_images_list.length - 1) : images_id - 1;
                images_src = that.file_images_list[images_id];
            } else {
                images_id = (images_id == (that.file_images_list.length - 1)) ? 0 : (images_id + 1);
                images_src = that.file_images_list[images_id];
            }
            preview_images.attr('data-index', images_id).attr('src', '/download?filename=' + images_src);
            $('.preview_title').html(that.get_path_filename(images_src));
        });
        // 自动图片大小
        function auto_images_size(transition) {
            var rotate = Math.abs(images_config.rotate / 90),
                preview_width = (rotate % 2 == 0 ? images_config.preview_width : images_config.preview_height),
                preview_height = (rotate % 2 == 0 ? images_config.preview_height : images_config.preview_width),
                preview_images = $('#preview_images'),
                css_config = {};
            images_config.init_width = images_config.natural_width;
            images_config.init_height = images_config.natural_height;
            if (images_config.init_width > preview_width) {
                images_config.init_width = preview_width;
                images_config.init_height = parseFloat(((preview_width / images_config.natural_width) * images_config.init_height).toFixed(2));
            }
            if (images_config.init_height > preview_height) {
                images_config.init_width = parseFloat(((preview_height / images_config.natural_height) * images_config.init_width).toFixed(2));
                images_config.init_height = preview_height;
            }
            images_config.current_width = parseFloat(images_config.init_width * images_config.scale);
            images_config.current_height = parseFloat(images_config.init_height * images_config.scale);
            images_config.current_left = parseFloat(((images_config.preview_width - images_config.current_width) / 2).toFixed(2));
            images_config.current_top = parseFloat(((images_config.preview_height - images_config.current_height) / 2).toFixed(2));
            css_config = {
                'width': images_config.current_width,
                'height': images_config.current_height,
                'top': images_config.current_top,
                'left': images_config.current_left,
                'display': 'inline',
                'transform': 'rotate(' + images_config.rotate + 'deg)',
                'opacity': 1,
                'transition': 'all 100ms',
            }
            if (transition === false) delete css_config.transition;
            preview_images.css(css_config);
        }
    },

    /**
     * @description 打开视频播放
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    open_video_play: function(data) {
        var old_filename = data.path,
            imgUrl = '/download?filename=' + data.path,
            p_tmp = data.path.split('/'),
            path = p_tmp.slice(0, p_tmp.length - 1).join('/')
        layer.open({
            type: 1,
            closeBtn: 2,
            title: '正在播放[<a class="btvideo-title">' + p_tmp[p_tmp.length - 1] + '</a>]',
            area: ["890px", "402px"],
            shadeClose: false,
            skin: 'movie_pay',
            content: '<div id="btvideo"><video type="" src="' + imgUrl + '&play=true" data-filename="' + data.path + '" controls="controls" autoplay="autoplay" width="640" height="360">您的浏览器不支持 video 标签。</video></div><div class="video-list"></div>',
            success: function() {
                $.post('/files?action=get_videos', { path: path }, function(rdata) {
                    var video_list = '<table class="table table-hover" style="margin-bottom:0;"><thead style="display: none;"><tr><th style="word-break: break-all;word-wrap:break-word;width:165px;">文件名</th><th style="width:65px" style="text-align:right;">大小</th></tr></thead>',
                        index = 0;
                    for (var i = 0; i < rdata.length; i++) {
                        var filename = path + '/' + rdata[i].name;
                        if (filename === old_filename) index = i;
                        video_list += '<tr class="' + (filename === old_filename ? 'video-avt' : '') + '"><td style="word-break: break-all;word-wrap:break-word;width:150px" onclick="bt_file.play_file(this,\'' + filename + '\')" title="文件: ' + filename + '\n类型: ' + rdata[i].type + '"><a>' +
                            rdata[i].name + '</a></td><td style="font-size: 8px;text-align:right;width:' + (65 + bt_file.scroll_width) + 'px;">' + ToSize(rdata[i].size) + '</td></tr>';
                    }
                    video_list += '</table>';
                    $('.video-list').html(video_list).scrollTop(index * 34);
                });
            }
        });
    },
    /**
     * @description 切换播放
     * @param {String} obj  
     * @param {String} filename 文件名
     * @return void
     */
    play_file: function(obj, filename) {
        if ($('#btvideo video').attr('data-filename') == filename) return false;
        var imgUrl = '/download?filename=' + filename + '&play=true';
        var v = '<video src="' + imgUrl + '" controls="controls" data-fileName="' + filename + '" autoplay="autoplay" width="640" height="360">您的浏览器不支持 video 标签。</video>'
        $("#btvideo").html(v);
        var p_tmp = filename.split('/')
        $(".btvideo-title").html(p_tmp[p_tmp.length - 1]);
        $(".video-avt").removeClass('video-avt');
        $(obj).parents('tr').addClass('video-avt');
    },
    /**
     * @description 复制文件和目录
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    copy_file_or_dir: function(data) {
        bt.set_cookie('record_paste', data.path);
        bt.set_cookie('record_paste_type', 'copy');
        $('.file_all_paste').removeClass('hide');
        layer.msg('复制成功，请点击粘贴按钮，或Ctrl+V粘贴');
    },

    /**
     * @description 剪切文件和目录
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    cut_file_or_dir: function(data) {
        bt.set_cookie('record_paste', data.path);
        bt.set_cookie('record_paste_type', 'cut');
        $('.file_all_paste').removeClass('hide');
        layer.msg('剪切成功，请点击粘贴按钮，或Ctrl+V粘贴');
    },
    /**
     * @descripttion 粘贴文件和目录
     * @return: 无返回值
     */
    paste_file_or_dir: function() {
        var that = this,
            _isPaste = bt.get_cookie('record_paste_type'),
            _paste = bt.get_cookie('record_paste'),
            _filename = '';
        if (_paste != 'null' && _paste != undefined) _filename = _paste.split('/').pop()
        if (that.file_path.indexOf(_paste) > -1) {
            layer.msg('文件夹禁止粘贴到项目本身！', { icon: 0 });
            return false;
        }
        if (_isPaste != 'null' && _isPaste != undefined) {
            switch (_isPaste) {
                case 'cut':
                case 'copy':
                    this.check_exists_files_req({ dfile: this.file_path, filename: _filename }, function(result) {
                        if (result.length > 0) {
                            var tbody = '';
                            for (var i = 0; i < result.length; i++) {
                                tbody += '<tr><td><span class="exists_files_style">' + result[i].filename + '</span></td><td>' + ToSize(result[i].size) + '</td><td>' + getLocalTime(result[i].mtime) + '</td></tr>';
                            }
                            var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>文件名</th><th>大小</th><th>最后修改时间</th></thead>\
                                        <tbody>' + tbody + '</tbody>\
                                        </table></div>';
                            SafeMessage('即将覆盖以下文件', mbody, function() {
                                that.config_paste_to(_paste, _filename);
                            });
                        } else {
                            that.config_paste_to(_paste, _filename);
                        }
                    })
                    break;
                case '1':
                case '2':
                    that.batch_file_paste();
                    break;
            }
        }
    },
    /**
     * @descripttion 粘贴到
     * @param {String} path         复制/剪切路径
     * @param {String} _filename     文件名称
     * @return: 无返回值
     */
    config_paste_to: function(path, _filename) {
        var that = this,
            _type = bt.get_cookie('record_paste_type');
        this.$http(_type == 'copy' ? 'CopyFile' : 'MvFile', { sfile: path, dfile: (this.file_path + '/' + _filename) }, function(rdata) {
            if (rdata.status) {
                bt.set_cookie('record_paste', null);
                bt.set_cookie('record_paste_type', null);
                that.reader_file_list({ path: that.file_path })
            }
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 })
        })
    },
    /**
     * @description 重命名文件和目录
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    rename_file_or_dir: function(data) {
        var that = this;
        that.is_editor = true;
        $('.file_list_content .file_tr:nth-child(' + (data.index + 1) + ')').addClass('editr_tr').find('.file_title').empty().append($((bt.get_cookie('rank') == 'icon' ? '<textarea name="rename_file_input" onfocus="this.select()">' + data.filename + '</textarea>' : '<input name="rename_file_input" onfocus="this.select()" type="text" value="' + data.filename + '">')))
        if (bt.get_cookie('rank') == 'icon') {
            $('textarea[name=rename_file_input]').css({ 'height': $('textarea[name=rename_file_input]')[0].scrollHeight })
        }
        $((bt.get_cookie('rank') == 'icon' ? 'textarea' : 'input') + '[name=rename_file_input]').on('input', function() {
            if (bt.get_cookie('rank') == 'icon') {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + "px";
            }
            if (data.type == 'file') {
                var ext_arry = $(this).val().split('.'),
                    ext = ext_arry[ext_arry.length - 1];
                $(this).parent().prev().find('.file_icon').removeAttr('class').addClass('file_icon file_' + ext);
            }
        }).keyup(function(e) {
            if (e.keyCode == 13) $(this).blur();
            e.stopPropagation();
            e.preventDefault();
        }).blur(function() {
            var _val = $(this).val().replace(/[\r\n]/g, ""),
                config = { sfile: data.path, dfile: that.path_resolve(that.file_path, _val) }
            if (data.filename == _val || _val == '') {
                $('.file_list_content .file_tr:nth-child(' + (data.index + 1) + ')').removeClass('editr_tr').find('.file_title').empty().append($('<i>' + data.filename + '</i>'));
                that.is_editor = false;
                return false;
            }
            if (that.match_unqualified_string(_val)) return layer.msg('名称不能含有 /\\:*?"<>|符号', { icon: 2 });
            that.rename_file_req(config, function(res) {
                that.reader_file_list({ path: that.file_path }, function() { layer.msg(res.msg, { icon: res.status ? 1 : 2 }) });
            });
            that.is_editor = false;
        }).focus();
    },

    /**
     * @description 设置文件和目录分享
     * @param {Object} data 当前文件的数据对象
     * @returns void
     */
    set_file_share: function(data) {
        var that = this;
        this.loadY = bt.open({
            type: 1,
            shift: 5,
            closeBtn: 2,
            area: '450px',
            title: '设置分享' + data.type_tips + '-[' + data.filename + ']',
            btn: ['生成外链', '取消'],
            content: '<from class="bt-form" id="outer_url_form" style="padding:30px 15px;display:inline-block">' +
                '<div class="line"><span class="tname">分享名称</span><div class="info-r"><input name="ps"  class="bt-input-text mr5" type="text" placeholder="分享名称不能为空" style="width:270px" value="' + data.filename + '"></div></div>' +
                '<div class="line"><span class="tname">有效期</span><div class="info-r">' +
                '<label class="checkbox_grourd"><input type="radio" name="expire" value="24" checked><span>&nbsp;1天</span></label>' +
                '<label class="checkbox_grourd"><input type="radio" name="expire" value="168"><span>&nbsp;7天</span></label>' +
                '<label class="checkbox_grourd"><input type="radio" name="expire" value="1130800"><span>&nbsp;永久</span></label>' +
                '</div></div>' +
                '<div class="line"><span class="tname">提取码</span><div class="info-r"><input name="password" class="bt-input-text mr5" placeholder="为空则不设置提取码" type="text" style="width:220px" value=""><button type="button" id="random_paw" class="btn btn-success btn-sm btn-title">随机</button></div></div>' +
                '</from>',
            yes: function(indexs, layers) {
                var ps = $('[name=ps]').val(),
                    expire = $('[name=expire]:checked').val(),
                    password = $('[name=password]').val();
                if (ps === '') {
                    layer.msg('分享名称不能为空', { icon: 2 })
                    return false;
                }
                that.create_download_url({
                    filename: data.path,
                    ps: ps,
                    password: password,
                    expire: expire
                }, function(res) {
                    if (!res.status) {
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                        return false;
                    } else {
                        var rdata = res.msg;
                        that.file_list[data.index] = $.extend(that.file_list[data.index], { down_id: rdata.id, down_info: rdata });
                        that.loadY.close();
                        that.info_file_share(data);
                        that.reader_file_list_content(that.file_list);
                    }
                });
            },
            success: function(layers, index) {
                $('#random_paw').click(function() {
                    $(this).prev().val(bt.get_random(6));
                });
            }
        });
    },

    /**
     * @description 分享信息查看
     * @param {Object} data 当前文件的数据对象
     * @returns void
     */
    info_file_share: function(data) {
        var that = this;
        if (typeof data.down_info == "undefined") {
            this.get_download_url_find({ id: data.down_id }, function(res) {
                that.file_list[data.index] = $.extend(that.file_list[data.index], { down_info: res });
                that.file_share_view(that.file_list[data.index], 'fonticon');
            })
            return false;
        }
        this.file_share_view(data, 'fonticon');
    },
    /**
     * @description 分享信息视图
     * @param {Object} data 当前文件的数据对象
     * @param {String} type 区别通过右键打开或是图标点击
     * @returns void
     */
    file_share_view: function(datas, type) {
        var data = datas
        if (type == 'fonticon') { data = datas.down_info }
        var that = this,
            download_url = location.origin + '/down/' + data.token;
        this.loadY = bt.open({
            type: 1,
            shift: 5,
            closeBtn: 2,
            area: '550px',
            title: '外链分享-[' + data.filename + ']',
            content: '<div class="bt-form pd20 pb70">' +
                '<div class="line"><span class="tname">分享名称</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:365px" value="' + data.ps + '"></div></div>' +
                '<div class="line external_link"><span class="tname">分享外链</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:280px" value="' + download_url + '"><button type="button" id="copy_url" data-clipboard-text="' + download_url + '" class="btn btn-success btn-sm btn-title copy_url" style="margin-right:5px" data-clipboard-target="#copy_url"><img style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABIUlEQVQ4T6XTsSuFURjH8d+3/AFm0x0MyqBEUQaUIqUU3YwWyqgMptud/BlMSt1SBiklg0K3bhmUQTFZDZTxpyOvznt7z3sG7/T2vOf5vM85z3nQPx+KfNuHkhoZ7xXYjNfEwIukXUnvNcg2sJECnoHhugpsnwBN21PAXVgbV/AEjNhuVSFA23YHWLNt4Cc3Bh6BUdtLcbzAgHPbp8BqCngAxjJbOANWUkAPGA8fE8icpD1gOQV0gclMBRfAYgq4BaZtz/YhA5IGgY7tS2AhBdwAM7b3JX1I+iz1G45sXwHzKeAa6P97qZgcEA6v/ZsR3v9aHCmt0P9UBVuShjKz8CYpXPkDYKJ0kaKhWpe0UwOFxDATx5VACFZ0Ivbuga8i8A3NFqQRZ5pz7wAAAABJRU5ErkJggg=="></button><button type="button" class="btn btn-success QR_code btn-sm btn-title"><img  style="width:16px" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABUklEQVQ4T6WSIU9DQRCEvwlYLIoEgwEECs3rDyCpobbtL6AKRyggMQ9TJBjUMzgMCeUnIEAREoICFAoEZMk2dy/Xo4KGNZu7nZ2bnT3xz1DsN7MFYCnhe5V0n/Kb2QowL2kY70cEoXAHVEnDG/ABXAJXmVDHVZKqSFAA58AqsAY8AW3A68/AQ7hbBG6BbeDGlaQEh8AucA3suzDgC5gFXHID2At5YxJBNwA6ocFBM8B3OL8DTaCcpMDN2QojxHHdk9Qrx9SeAyf1CMFIJ3DjYqxLOgo192gs4ibSNfrMOaj2yBvMrCnpImYHR4C/vizpIPkX/mpbUtfMepJKMxtKKsyslNTLCZxkBzgFjoE5oCVp08yKvyhwgkGyRl9nX1LDzDz3kzxS8kuBpFYygq8xJ4gjjBMEpz+BF+AxcXLg39XMOpLOciW1gtz9ac71GqdpSrE/8U20EQ3XLHEAAAAASUVORK5CYII="></button></div></div>' +
                '<div class="line external_link" style="' + (data.password == "" ? "display:none;" : "display:block") + '"><span class="tname">提取码</span><div class="info-r"><input readonly class="bt-input-text mr5" type="text" style="width:243px" value="' + data.password + '"><button type="button" data-clipboard-text="链接:' + download_url + ' 提取码:' + data.password + '"  class="btn btn-success copy_paw btn-sm btn-title">复制链接及提取码</button></div></div>' +
                '<div class="line"><span class="tname">过期时间</span><div class="info-r"><span style="line-height:32px; display: block;font-size:14px">' + ((data.expire > (new Date('2099-01-01 00:00:00').getTime()) / 1000) ? '<span calss="btlink">永久有效</span>' : bt.format_data(data.expire)) + '</span></div></div>' +
                '<div class="bt-form-submit-btn">' +
                '<button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan['public'].close + '</button>' +
                '<button type="button" id="down_del" class="btn btn-danger btn-sm btn-title close_down" style="color:#fff;background-color:#c9302c;border-color:#ac2925;" onclick="">关闭分享外链</button>' +
                '</div>' +
                '</div>',
            success: function(layers, index) {
                var copy_url = new ClipboardJS('.copy_url');
                var copy_paw = new ClipboardJS('.copy_paw');
                copy_url.on('success', function(e) {
                    layer.msg('复制链接成功!', { icon: 1 });
                    e.clearSelection();
                });
                copy_paw.on('success', function(e) {
                    layer.msg('复制链接及提取码成功!', { icon: 1 });
                    e.clearSelection();
                });
                $('.layer_close').click(function() {
                    layer.close(index);
                });
                $('.QR_code').click(function() {
                    layer.closeAll('tips');
                    layer.tips('<div style="height:140px;width:140px;padding:8px 0" id="QR_code"></div>', '.QR_code', {
                        area: ['150px', '150px'],
                        tips: [1, '#ececec'],
                        time: 0,
                        shade: [0.05, '#000'],
                        shadeClose: true,
                        success: function() {
                            jQuery('#QR_code').qrcode({
                                render: "canvas",
                                text: download_url,
                                height: 130,
                                width: 130
                            });
                        }
                    });
                });
                $('.close_down').click(function() {
                    that.remove_download_url({ id: data.id, fileName: data.filename }, function(res) {
                        that.loadY.close();
                        if (type == 'fonticon') {
                            that.file_list[datas.index].down_id = 0;
                            that.reader_file_list_content(that.file_list);
                        }
                        if (type == 'list') { that.render_share_list(); }
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                    })
                });
            }
        });
    },
    /**
     * @description 删除文件和目录
     * @param {Object} data 当前文件的数据对象
     * @return void
     */
    del_file_or_dir: function(data) {
        var that = this;
        if (that.is_recycle) {
            bt.confirm({
                title: '删除' + data.type_tips + '[&nbsp;' + data.filename + '&nbsp;]',
                msg: '<span>您确定要删除该' + data.type_tips + '[&nbsp;' + data.path + '&nbsp;]吗，删除后将移至回收站，是否继续操作?</span>'
            }, function() {
                that.del_file_req(data, function(res) {
                    that.reader_file_list({ path: that.file_path })
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                });
            });
        } else {
            bt.show_confirm('删除' + data.type_tips + '[&nbsp;' + data.filename + '&nbsp;]', '<i style="font-size: 15px;font-style: initial;color: red;">当前未开启回收站，删除该' + (data.type == 'dir' ? '文件夹' : '文件') + '后将无法恢复，是否继续删除？</i></span>', function() {
                that.del_file_req(data, function(res) {
                    that.reader_file_list({ path: that.file_path })
                    layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                });
            })
        }

    },

    /**
     * @description 取消文件收藏
     * @param {Object} data 当前文件的数据对象
     * @param {Object} el 当前元素对象
     * @returns void
     */
    cancel_file_favorites: function(data) {
        var that = this,
            index = data.index;
        this.loadY = bt.confirm({ title: '取消' + data['filename'] + '收藏', msg: '是否取消[' + data['path'] + ']的收藏，是否继续？' }, function() {
            that.$http('del_files_store', { path: data.path }, function(res) {
                if (res.status) {
                    that.file_list[index].caret = false;
                    that.reader_file_list_content(that.file_list);
                    that.load_favorites_index_list();
                }
                layer.msg(res.msg, { icon: res.status ? 1 : 2 })
            })
        });
    },
    /**
     * @description 创建软链接
     * @param {Object} data 当前文件的数据对象
    */
    set_soft_link:function(data){
        var that = this;
        bt_tools.open({
            title:'创建软链接',
            area:'520px',
            content:{
                'class':'pd20',
                formLabelWidth:'110px',
                form:[{
                    label:'文件夹或目录',
                    group:{
                        type:'text',
                        name:'sfile',
                        width:'280px',
                        placeholder:'请选择需要创建的软链的文件夹和文件',
                        icon:{type:'glyphicon-folder-open',event:function(ev){},select:'all'},
                        value:'',
                        input:function(ev){
                            console.log(arguments);
                        }
                    }
                },{
                    label:'',
                    group:{
                        type:'help',
                        style:{'margin-top':'0'},
                        'class':'none-list-style',
                        list:['提示：请选择需要创建的软链的文件夹和文件']
                    }
                }]
            },
            yes:function(data,indexs,layero){
                var sfile = data.sfile,dirList = sfile.split('/');
                data = $.extend(data,{dfile:that.file_path + '/' + dirList[dirList.length -1]})
                bt_tools.send('files/CreateLink',data,function(res) {
                    if(res.status){
                        layer.close(indexs);
                        bt.msg(res);
                        that.reader_file_list();
                    }
                },{tips:'创建软链接'});
            }
        });
    },

    /**
     * @description 设置文件权限 - ok
     * @param {Object} data 当前文件的数据对象
     * @param {Boolean} isPatch 是否多选
     * @returns void
     */
    set_file_authority: function(data, isPatch) {
        var that = this;
        that.get_file_authority({ path: data.path }, function(rdata) {
            that.loadY = layer.open({
                type: 1,
                closeBtn: 2,
                title: lan.files.set_auth + '[' + data.filename + ']',
                area: '400px',
                shadeClose: false,
                content: '<div class="setchmod bt-form ptb15 pb70">\
                            <fieldset>\
                                <legend>' + lan.files.file_own + '</legend>\
                                <p><input type="checkbox" id="owner_r" />' + lan.files.file_read + '</p>\
                                <p><input type="checkbox" id="owner_w" />' + lan.files.file_write + '</p>\
                                <p><input type="checkbox" id="owner_x" />' + lan.files.file_exec + '</p>\
                            </fieldset>\
                            <fieldset>\
                                <legend>' + lan.files.file_group + '</legend>\
                                <p><input type="checkbox" id="group_r" />' + lan.files.file_read + '</p>\
                                <p><input type="checkbox" id="group_w" />' + lan.files.file_write + '</p>\
                                <p><input type="checkbox" id="group_x" />' + lan.files.file_exec + '</p>\
                            </fieldset>\
                            <fieldset>\
                                <legend>' + lan.files.file_public + '</legend>\
                                <p><input type="checkbox" id="public_r" />' + lan.files.file_read + '</p>\
                                <p><input type="checkbox" id="public_w" />' + lan.files.file_write + '</p>\
                                <p><input type="checkbox" id="public_x" />' + lan.files.file_exec + '</p>\
                            </fieldset>\
                            <div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="' + rdata.chmod + '">' + lan.files.file_menu_auth + '，\
                            <span>' + lan.files.file_own + '\
                            <select id="chown" class="bt-input-text">\
                                <option value="www" ' + (rdata.chown == 'www' ? 'selected="selected"' : '') + '>www</option>\
                                <option value="mysql" ' + (rdata.chown == 'mysql' ? 'selected="selected"' : '') + '>mysql</option>\
                                <option value="root" ' + (rdata.chown == 'root' ? 'selected="selected"' : '') + '>root</option>\
                            </select></span>\
                            <span><input type="checkbox" id="accept_all" checked /><label for="accept_all" style="position: absolute;margin-top: 4px; margin-left: 5px;font-weight: 400;">应用到子目录</label></span>\
                            </div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-danger btn-sm btn-title layer_close">' + lan['public'].close + '</button>\
                                <button type="button" class="btn btn-success btn-sm btn-title set_access_authority">' + lan['public'].ok + '</button>\
                            </div>\
                        </div>',
                success: function(index, layers) {
                    that.edit_access_authority();
                    $("#access").keyup(function() {
                        that.edit_access_authority();
                    });
                    $("input[type=checkbox]").change(function() {
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
                    //提交
                    $('.set_access_authority').click(function() {
                        var chmod = $("#access").val();
                        var chown = $("#chown").val();
                        var all = $("#accept_all").prop("checked") ? 'True' : 'False';
                        var _form = {}
                        _form = {
                            user: chown,
                            access: chmod,
                            all: all
                        }
                        if (isPatch) {
                            _form['type'] = data.type
                            _form['path'] = data.path
                            _form['data'] = data.filelist
                        } else {
                            _form['filename'] = data.path
                        }
                        that.$http(isPatch ? 'SetBatchData' : 'SetFileAccess', _form, function(res) {
                            if (res.status) {
                                layer.close(layers);
                                that.reader_file_list({ path: that.file_path, is_operating: false })
                            }
                            layer.msg(res.msg, { icon: res.status ? 1 : 2 });
                        })
                    })
                    $('.layer_close').click(function() {
                        layer.close(layers);
                    })
                }
            });
        });
    },
    /**
     * @description 获取实时任务视图
     * @returns void
     */
    get_present_task_view: function() {
        this.file_present_task = layer.open({
            type: 1,
            title: "实时任务队列",
            area: '500px',
            closeBtn: 2,
            skin: 'present_task_list',
            shadeClose: false,
            shade: false,
            offset: 'auto',
            content: '<div style="margin: 10px;" class="message-list"></div>'
        })
    },
    /**
     * @description 渲染实时任务列表数据
     * @returns void
     */
    render_present_task_list: function() {
        var that = this;
        this.get_task_req({ status: -3 }, function(lists) {
            if (lists.length == 0) {
                layer.close(that.file_present_task)
                that.file_present_task = null;
                that.reader_file_list({ path: that.file_path, is_operating: false })
                return
            }
            var task_body = '',
                is_add = false;
            $.each(lists, function(index, item) {
                if (item.status == -1) {
                    if (!that.file_present_task) that.get_present_task_view();
                    if (item.type == '1') {
                        task_body += '<div class="mw-con">\
                            <ul class="waiting-down-list">\
                                <li>\
                                    <div class="down-filse-name"><span class="fname" style="width:80%;" title="正在下载: ' + item.shell + '">正在下载: ' + item.shell + '</span><span style="position: absolute;left: 84%;top: 25px;color: #999;">' + item.log.pre + '%</span><span class="btlink" onclick="bt_file.remove_present_task(' + item.id + ')" style="position: absolute;top: 25px;right: 20px;">取消</span></div>\
                                    <div class="down-progress"><div class="done-progress" style="width:' + item.log.pre + '%"></div></div>\
                                    <div class="down-info"><span class="total-size"> ' + item.log.used + '/' + ToSize(item.log.total) + '</span><span class="speed-size">' + (item.log.speed == 0 ? '正在连接..' : item.log.speed) + '/s</span><span style="margin-left: 20px;">预计还要: ' + item.log.time + '</span></div>\
                                </li>\
                            </ul>\
                            </div>'
                    } else {
                        task_body += '<div class="mw-title"><span style="max-width: 88%;display: block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;">' + item.name + ': ' + item.shell + '</span><span class="btlink" onclick="bt_file.remove_present_task(' + item.id + ')"  style="position: absolute;top: 10px;right: 15px;">取消</span></div>\
                        <div class="mw-con codebg">\
                            <code>' + item.log + '</code>\
                        </div>'
                    }
                } else {
                    if (!is_add) {
                        task_body += '<div class="mw-title">等待执行任务</div><div class="mw-con"><ul class="waiting-list">';
                        is_add = true;
                    }
                    task_body += '<li><span class="wt-list-name" style="width: 90%;">' + item.name + ': ' + item.shell + '</span><span class="mw-cancel" onclick="bt_file.remove_present_task(' + item.id + ')">X</span></li>';
                }
            })
            if (that.file_present_task) {
                if (is_add) task_body += '</ul></div>'
                $(".message-list").html(task_body);
            }
            setTimeout(function() { that.render_present_task_list(); }, 1000);
        })
    },
    /**
     * @description 取消实时任务列表
     * @returns void
     */
    remove_present_task: function(id) {
        var that = this;
        layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？', { title: '取消上传文件', icon: 0 }, function(indexs) {
            bt.send('remove_task', 'task/remove_task', { id: id }, function(rdata) {
                layer.msg(rdata.msg, { icon: 1 })
                layer.close(that.file_present_task)
                that.file_present_task = null;
            })
            layer.close(indexs);
        });
    },
    /**
     * @descripttion 设置访问权限
     * @returns void
     */
    edit_access_authority: function() {
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
    },
    /**
     * @description 获取文件权限 - ok
     * @param {Object} data 当前文件的数据对象
     * @param {Object} el 当前元素对象
     * @returns void
     */
    get_file_authority: function(data, callback) {
        this.$http('GetFileAccess', { filename: data.path }, function(rdata) { if (callback) callback(rdata) });
    },
    /**
     * @description 文件夹目录查杀
     * @param {Object} data 当前文件的数据对象
     * @returns void
     */
    set_dir_kill: function(data) {
        var that = this;
        if (data.ext == 'php') {
            that.$http('file_webshell_check', { filename: data.path }, function(rdata) {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 })
            })
        } else {
            layer.confirm('目录查杀将包含子目录中的php文件，是否操作？', { title: '目录查杀[' + data['filename'] + ']', closeBtn: 2, icon: 3 }, function(index) {
                that.$http('dir_webshell_check', { path: data.path }, function(rdata) {
                    layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 })
                })
            })
        }
    },
    /**
     * @description 文件路径合并
     * @param {String} paths 旧路径
     * @param {String} param 新路径
     * @return {String} 新的路径
     */
    path_resolve: function(paths, param) {
        var path = '',
            split = '';
        if (!Array.isArray(param)) param = [param];
        paths.replace(/([\/|\/]*)$/, function($1) {
            split = $1;
            return 'www';
        });
        $.each(param, function(index, item) {
            path += '/' + item;
        });
        return (paths + path).replace('//', '/');
    },

    /**
     * @descripttion 取扩展名
     * @return: 返回扩展名
     */
    get_ext_name: function(fileName) {
        var extArr = fileName.split(".");
        var exts = ["folder", "folder-unempty", "sql", "c", "cpp", "cs", "flv", "css", "js", "htm", "html", "java", "log", "mht", "php", "url", "xml", "ai", "bmp", "cdr", "gif", "ico", "jpeg", "jpg", "JPG", "png", "psd", "webp", "ape", "avi", "mkv", "mov", "mp3", "mp4", "mpeg", "mpg", "rm", "rmvb", "swf", "wav", "webm", "wma", "wmv", "rtf", "docx", "fdf", "potm", "pptx", "txt", "xlsb", "xlsx", "7z", "cab", "iso", "rar", "zip", "gz", "bt", "file", "apk", "bookfolder", "folder-empty", "fromchromefolder", "documentfolder", "fromphonefolder", "mix", "musicfolder", "picturefolder", "videofolder", "sefolder", "access", "mdb", "accdb", "fla", "doc", "docm", "dotx", "dotm", "dot", "pdf", "ppt", "pptm", "pot", "xls", "csv", "xlsm"];
        var extLastName = extArr[extArr.length - 1];
        for (var i = 0; i < exts.length; i++) {
            if (exts[i] == extLastName) {
                return exts[i];
            }
        }
        return 'file';
    },

    /**
     * @description 获取路径上的文件名称
     * @param {String} path 路径
     * @return {String} 文件名称
     */
    get_path_filename: function(path) {
        var paths = path.split('/');
        return paths[paths.length - 1];
    },

    /**
     * @description 返回上一层目录地址
     * @param {String} path 当前路径
     * @returns 返回上一层地址
     */
    retrun_prev_path: function(path) {
        var dir_list = path.split('/');
        dir_list.splice(dir_list.length - 1);
        if (dir_list == '') dir_list = ['/']
        return dir_list.join('/');
    },
    /**
     * @descripttion: 路径过滤
     * @return: 无返回值
     */
    path_check: function(path) {
        path = path.replace('//', '/');
        if (path === '/') return path;
        path = path.replace(/\/+$/g, '');
        return path;
    },

    /**
     * @description 获取文件权限信息
     * @param {Object} data 请求传入参数
     * @param {Function} callback 回调参数
     * @returns void
     */
    get_file_access: function(data, callback) {
        var that = this;
        this.layerT = bt.load('正在文件权限信息，请稍候...');
        bt.send('GetFileAccess', 'files/GetFileAccess', { path: data.path }, function(res) {
            that.loadT.close();
            if (callback) callback();
        });
    },

    /**
     * @description 创建外链下载
     * @param {Object} data 请求传入参数
     * @param {Function} callback 回调参数
     * @returns void
     */
    create_download_url: function(data, callback) {
        var that = this;
        this.layerT = bt.load('正在分享文件，请稍候...');
        bt.send('create_download_url', 'files/create_download_url', { filename: data.filename, ps: data.ps, password: data.password, expire: data.expire }, function(res) {
            that.layerT.close();
            if (callback) callback(res);
        });
    },

    /**
     * @description 获取外链下载数据
     * @param {Object} data 请求传入参数
     * @param {Function} callback 回调参数
     * @returns void
     */
    get_download_url_find: function(data, callback) {
        var that = this;
        this.layerT = bt.load('正在获取分享文件信息，请稍候...');
        bt.send('get_download_url_find', 'files/get_download_url_find', { id: data.id }, function(res) {
            that.layerT.close();
            if (callback) callback(res);
        });
    },

    /**
     * @description 删除外链下载
     * @param {Object} data 请求传入参数
     * @param {Function} callback 回调参数
     * @returns void
     */
    remove_download_url: function(data, callback) {
        var that = this;
        layer.confirm('是否取消分享该文件【' + data.fileName + '】，是否继续？', { title: '取消分享', closeBtn: 2, icon: 3 }, function() {
            this.layerT = bt.load('正在取消分享文件，请稍候...');
            bt.send('remove_download_url', 'files/remove_download_url', { id: data.id }, function(res) {
                if (callback) callback(res);
            });
        });
    },

    /**
     * @description 获取磁盘列表
     * @param {Function} callback 回调参数
     * @returns void
     */
    get_disk_list: function(callback) {
        bt_tools.send('system/GetDiskInfo', function(res) {
            if (callback) callback(res);
        }, '获取磁盘列表');
    },

    // 新建文件（文件和文件夹）
    create_file_req: function(data, callback) {
        var _req = (data.type === 'folder' ? 'CreateDir' : 'CreateFile')
        bt.send(_req, 'files/' + _req, {
            path: data.path
        }, function(res) {
            if (callback) callback(res);
        });
    },

    // 重命名文件（文件或文件夹）
    rename_file_req: function(data, callback) {
        bt_tools.send('files/MvFile', {
            sfile: data.sfile,
            dfile: data.dfile,
            rename: data.rename || true
        }, function(res) {
            if (callback) callback(res);
        }, '执行重命名');
    },

    // 剪切文件请求（文件和文件夹）
    shear_file_req: function(data, callback) {
        this.rename_file_req({
            sfile: data.sfile,
            dfile: data.dfile,
            rename: false
        }, function(res) {
            if (callback) callback(res);
        }, '执行剪切');
    },

    // 检查文件是否存在（复制文件和文件夹前需要调用）
    check_exists_files_req: function(data, callback) {
        var layerT = bt.load('正在粘贴文件，请稍候...');
        bt.send('CheckExistsFiles', 'files/CheckExistsFiles', {
            dfile: data.dfile,
            filename: data.filename
        }, function(res) {
            layerT.close();
            if (callback) callback(res);
        });
    },

    // 复制文件（文件和文件夹）
    copy_file_req: function(data, callback) {
        bt.send('CopyFile', 'files/CopyFile', {
            sfile: data.sfile,
            dfile: data.dfile
        }, function(res) {
            if (callback) callback(res);
        });
    },

    // 压缩文件（文件和文件夹）
    compress_file_req: function(data, callback) {
        bt.send('Zip', 'files/Zip', {
            sfile: data.sfile,
            dfile: data.dfile,
            z_type: data.z_type,
            path: data.path
        }, function(res) {
            if (callback) callback(res);
        });
    },

    // 获取实时任务
    get_task_req: function(data, callback) {
        bt.send('get_task_lists', 'task/get_task_lists', {
            status: data.status
        }, function(res) {
            if (callback) callback(res);
        });
    },

    // 获取文件权限
    get_file_access: function() {
        bt.send('GetFileAccess', 'files/GetFileAccess', {
            filename: data.filename
        }, function(res) {
            if (callback) callback(res);
        });
    },

    // 设置文件权限
    set_file_access: function() {
        bt.send('SetFileAccess', 'files/SetFileAccess', {
            filename: data.filename,
            user: data.user,
            access: data.access,
            all: data.all
        }, function(res) {
            if (callback) callback(res);
        });
    },

    /**
     * @description 删除文件（文件和文件夹）
     * @param {Object} data 文件目录参数
     * @param {Function} callback 回调函数
     * @return void
     */
    del_file_req: function(data, callback) {
        var _req = (data.type === 'dir' ? 'DeleteDir' : 'DeleteFile')
        var layerT = bt.load('正在删除文件，请稍候...');
        bt.send(_req, 'files/' + _req, { path: data.path }, function(res) {
            layerT.close();
            layer.msg(res.msg, { icon: res.status ? 1 : 2 })
            if (callback) callback(res);
        });
    },

    /**
     * @description 下载文件
     * @param {Object} 文件目录参数
     * @param {Function} callback 回调函数
     * @return void
     */
    down_file_req: function(data, callback) {
        window.open('/download?filename=' + encodeURIComponent(data.path));
    },

    /**
     * @description 获取文件大小（文件夹）
     * @param {*} data  文件目录参数
     * @param {Function} callback 回调函数
     * @return void
     */
    get_file_size: function(data, callback) {
        bt_tools.send('files/get_path_size', { path: data.path }, callback, '获取文件目录大小');
    },
    /**
     * @description 获取目录大小
     * @param {*} data  文件目录地址
     * @return void
     */
    get_dir_size: function(data, callback) {
        bt_tools.send('files/GetDirSize', { path: data.path }, function(rdata) {
            $("#file_all_size").text(rdata)
            if (callback) callback(rdata);
        }, { tips: '获取目录大小', verify: false });
    },
    /**
     * @description 获取文件目录
     * @param {*} data  文件目录参数
     * @param {Function} callback 回调函数
     */
    get_dir_list: function(data, callback) {
        var that = this,
            f_sort = bt.get_cookie('files_sort');
        if (f_sort){
            data['sort'] = f_sort;
            data['reverse'] = bt.get_cookie('name_reverse');
        }
        bt_tools.send('files/GetDir', $.extend({ 
            p: 1, 
            showRow:bt.get_storage('local','showRow') || that.file_page_num, 
            path: bt.get_cookie('Path') || data.path 
        }, data), callback, { tips: false });
        // (data.showRow ||  bt.get_storage('local','showRow') || that.file_page_num)
    },
    /**
     * @description 文件、文件夹压缩
     * @param {Object} data  文件目录参数
     * @param {Boolean} isbatch  是否批量操作
     */
    compress_file_or_dir: function(data, isbatch) {
        var that = this;
        console.log(data);
        $('.selection_right_menu').removeAttr('style');
        this.reader_form_line({
            url: 'Zip',
            overall: { width: '310px' },
            data: [{
                    label: '压缩类型',
                    type: 'select',
                    name: 'z_type',
                    value: data.open,
                    list: [
                        ['tar_gz', 'tar.gz (推荐)'],
                        ['zip', 'zip (通用格式)'],
                        ['rar', 'rar (WinRAR对中文兼容较好)']
                    ]
                },
                { label: '压缩路径', id: 'compress_path', name: 'dfile', placeholder: '保存的文件名', value: data.path + '_' + bt.get_random(6) + '.' + (data.open == 'tar_gz' ? 'tar.gz' : data.open) }
            ],
            beforeSend: function(updata) {
                var ind = data.path.lastIndexOf("\/"),
                    _url = data.path.substring(0, ind + 1); // 过滤路径文件名
                return { sfile: data.filename, dfile: updata.dfile, z_type: (updata.z_type == 'tar_gz' ? 'tar.gz' : updata.z_type), path: _url }
            }
        }, function(form, html) {
            var loadT = layer.open({
                type: 1,
                title: '压缩' + data.type_tips + '[ ' + data.filename + ' ]',
                area: '480px',
                shadeClose: false,
                closeBtn: 2,
                skin: 'compress_file_view',
                btn: ['压缩', '关闭'],
                content: html[0].outerHTML,
                success: function() {
                    // 切换压缩格式
                    $('select[name=z_type]').change(function() {
                            var _type = $(this).val(),
                                _inputVel = $('input[name=dfile]').val(),
                                path_list = [];
                            _type == 'tar_gz' ? 'tar.gz' : _type
                            _inputVel = _inputVel.substring(0, _inputVel.lastIndexOf('\/'))
                            path_list = _inputVel.split('/');
                            $('input[name=dfile]').val(_inputVel + '/' + (isbatch ? path_list[path_list.length - 1] : data.filename) + '_' + bt.get_random(6) + '.' + _type)
                        })
                        // 插入选择路径
                    $('.compress_file_view .line:nth-child(2)').find('.info-r').append('<span class="glyphicon glyphicon-folder-open cursor" style="margin-left: 10px;" onclick="ChangePath(\'compress_path\')"></span>');
                },
                yes: function() {
                    var ress = form.getVal();
                    if (ress.dfile == '') return layer.msg('请选择有效的地址', { icon: 2 })
                    form.submitForm(function(res, datas) {
                        setTimeout(function() {
                            that.reader_file_list({ path: datas.path })
                        }, 1000);
                        if (res == null || res == undefined) {
                            layer.msg(lan.files.zip_ok, { icon: 1 });
                        }
                        if (res.status) {
                            that.render_present_task_list();
                        }
                        layer.close(loadT)
                    })
                }
            })
        });
    },
    /**
     * @description 文件、文件夹解压
     * @param {*} data  文件目录参数
     */
    unpack_file_to_path: function(data) {
        var that = this,
            _type = 'zip',
            spath = '';
        spath = data.path.substring(0, data.path.lastIndexOf('\/'))
        this.reader_form_line({
            url: 'UnZip',
            overall: { width: '310px' },
            data: [
                { label: '文件名', name: 'z_name', placeholder: '压缩文件名', value: data.path },
                { label: '解压到', name: 'z_path', placeholder: '解压路径', value: spath },
                {
                    label: '编码',
                    name: 'z_code',
                    type: 'select',
                    value: 'UTF-8',
                    list: [
                        ['UTF-8', 'UTF-8'],
                        ['gb18030', 'GBK']
                    ]
                }
            ],
            beforeSend: function(updata) {
                return { sfile: updata.z_name, dfile: updata.z_path, type: _type, coding: updata.z_code, password: updata.z_password }
            }
        }, function(form, html) {
            var loadT = layer.open({
                type: 1,
                title: '解压文件 [ ' + data.filename + ' ]',
                area: '480px',
                shadeClose: false,
                closeBtn: 2,
                skin: 'unpack_file_view',
                btn: ['解压', '关闭'],
                content: html[0].outerHTML,
                success: function() {
                    if (data.ext == 'gz') _type = 'tar' //解压格式
                    if (_type == 'zip') { // 判断是否插入解压密码
                        $('.unpack_file_view .line:nth-child(2)').append('<div class="line"><span class="tname">解压密码</span><div class="info-r"><input type="text" name="z_password" class="bt-input-text " placeholder="无密码则留空" style="width:310px" value=""></div></div>')
                    }
                },
                yes: function() {
                    var ress = form.getVal();
                    if (ress.z_name == '') return layer.msg('请输入文件名路径', { icon: 2 })
                    if (ress.z_path == '') return layer.msg('请输入解压地址', { icon: 2 })
                    form.submitForm(function(res, datas) {
                        layer.close(loadT)
                        setTimeout(function() {
                            that.reader_file_list({ path: datas.path })
                        }, 1000);
                        if (res.status) {
                            that.render_present_task_list();
                        }
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                    })
                }
            })
        });
    },

    /**
     * @description 获取替换内容
     * @param {Object} data 请求传入参数
     * @param {Function} callback 回调参数
     * @returns void
     */
    get_replace_log: function() {
        bt_tools.send('files/GetDir', $.extend({
            p: 1,
            showRow:bt.get_storage('local','showRow') || that.file_page_num,
            path: bt.get_cookie('Path') || data.path
        }, data), { tips: false });
    },
    /**
     * @description 匹配非法字符
     * @param {Array} item 配置对象
     * @return 返回匹配结果
     */
    match_unqualified_string: function(item) {
        var containSpecial = RegExp(/[(\*)(\|)(\\)(\:)(\")(\/)(\<)(\>)(\?)(\)]+/);
        return containSpecial.test(item)
    },
    /**
     * @description 渲染表单
     * @param {Array} config 配置对象
     * @param {Function} callback 回调函数
     * @return void
     */
    reader_form_line: function(config, callback) {
        var that = this,
            random = bt.get_random(10),
            html = $('<form id="' + random + '" class="bt-form pd20"></form>'),
            data = config,
            eventList = [],
            that = this;
        if (!Array.isArray(config)) data = config.data;
        $.each(data, function(index, item) {
            var labelWidth = item.labelWidth || config.overall.labelWidth || null,
                event_random = bt.get_random(10),
                width = item.labelWidth || config.overall.width || null,
                form_line = $('<div class="line"><span class="tname" ' + (labelWidth ? ('width:' + labelWidth) : '') + '>' + (item.label || '') + '</span><div class="info-r"></div></div>'),
                form_el = $((function() {
                    switch (item.type) {
                        case 'select':
                            return '<select ' + (item.disabled ? 'disabled' : '') + ' ' + (item.readonly ? 'readonly' : '') + ' class="bt-input-text mr5 ' + (item.readonly ? 'readonly-form-input' : '') + '" name="' + item.name + '" ' + (item.eventType ? 'data-event="' + event_random + '"' : '') + ' style="' + (width ? ('width:' + width) : '') + '">' + (function(item) {
                                var options_list = '';
                                $.each(item.list, function(key, items) {
                                    if (!Array.isArray(items)) { //判断是否为二维数组
                                        options_list += '<option value="' + items + '" ' + (item.value === key ? 'selected' : '') + '>' + items + '</option>'
                                    } else {
                                        options_list += '<option value="' + items[0] + '" ' + (item.value === items[0] ? 'selected' : '') + '>' + items[1] + '</option>'
                                    }
                                })
                                return options_list;
                            }(item)) + '</select>';
                            break;
                        case 'text':
                        default:
                            return '<input ' + (item.disabled ? 'disabled' : '') + ' ' + (item.readonly ? 'readonly' : '') + ' ' + (item.eventType ? 'data-event="' + event_random + '"' : '') + ' type="text" name="' + item.name + '" ' + (item.id ? 'id="' + item.id + '"' : '') + ' class="bt-input-text ' + (item.readonly ? 'readonly-form-input' : '') + '" placeholder="' + (item.placeholder || '') + '" style="' + (width ? ('width:' + width) : '') + '" value="' + (item.value || '') + '"/>';
                            break;
                    }
                }(item)));
            if (item.eventType || item.event) {
                if (!Array.isArray(item.eventType)) item.eventType = [item.eventType];
                $.each(item.eventType, function(index, items) {
                    eventList.push({ el: event_random, type: items || 'click', event: item[items] || null });
                    if (config.el) {
                        var els = $('[data-event="' + item.el + '"]');
                        if (item[items]) {
                            if (items == 'enter') {
                                els.on('keyup', function(e) {
                                    if (e.keyCode == 13) item.event(e)
                                })
                            } else {
                                els.on(item || 'click', item.event);
                            }
                        } else {
                            if (items == 'focus') {
                                var vals = els.val();
                                if (vals != '') {
                                    els.val('').focus().val(vals);
                                }
                            } else {
                                els[items]();
                            }

                        }
                    }
                });
            }
            form_line.find('.info-r').append(form_el)
            html.append(form_line);
        });
        if (config.el) $(config.el).empty().append(html);
        if (callback) callback({
            // 获取内容
            getVal: function() {
                return $('#' + random).serializeObject();
            },
            // 设置事件，没有设置el参数，需要
            setEvent: function() {
                $.each(eventList, function(index, item) {
                    var els = $('[data-event="' + item.el + '"]');
                    if (item.event === null) {
                        if (item.type == 'focus') {
                            var vals = els.val();
                            if (vals != '') {
                                els.val('').focus().val(vals);
                            }
                        } else {
                            els[item.type]();
                        }
                    } else {
                        if (item.type == 'enter') {
                            els.on('keyup', function(e) {
                                if (e.keyCode == 13) item.event(e)
                            })
                        } else {
                            els.on(item.type, item.event);
                        }
                    }
                });
            },
            // 提交表单
            submitForm: function(callback) {
                var data = this.getVal();
                if (config.beforeSend) data = config.beforeSend(data);
                that.loadT = bt.load('提交表单内容');
                bt.send(config.url, ('files/' + config.url), data, function(rdata) {
                        that.loadT.close();
                        if (callback) callback(rdata, data)
                    })
                    // bt.http({tips:config.loading || '正在提交表单内容，请稍候...',url:config.url,data:data,success:function(rdata){if(callback) callback(rdata,data)}});
            }
        }, html);
    },

    /**
     * @description 文件管理请求方法
     * @param {*} data 
     * @param {*} parem
     * @param {*} callback
     */
    $http: function(data, parem, callback) {
        var that = this,
            loadT = '';
        if (typeof data == "string") {
            if (typeof parem != "object") callback = parem, parem = {};
            if (!Array.isArray(that.method_list[data])) that.method_list[data] = ['files', that.method_list[data]];
            that.$http({ method: data, tips: (that.method_list[data][1] ? '正在' + that.method_list[data][1] + '，请稍候...' : false), module: that.method_list[data][0], data: parem, msg: true }, callback);
        } else {
            if (typeof data.tips != 'undefined' && data.tips) loadT = bt.load(data.tips);
            bt.send(data.method, (data.module || 'files') + '/' + data.method, data.data || {}, function(res) {
                if (loadT != '') loadT.close();
                if (typeof res == "string") res = JSON.parse(res);
                if (res.status === false && res.msg) {
                    bt.msg(res);
                    return false;
                }
                if (parem) parem(res)
            });
        }
    }
}
bt_file.init();

Function.prototype.delay = function(that, arry, time) {
    if (!Array.isArray(arry)) time = arry, arry = [];
    if (typeof time == "undefined") time = 0;
    setTimeout(this.apply(that, arry), time);
    return this;
}

jQuery.prototype.serializeObject = function() {
    var a, o, h, i, e;
    a = this.serializeArray();
    o = {};
    h = o.hasOwnProperty;
    for (i = 0; i < a.length; i++) {
        e = a[i];
        if (!h.call(o, e.name)) {
            o[e.name] = e.value;
        }
    }
    return o;
}
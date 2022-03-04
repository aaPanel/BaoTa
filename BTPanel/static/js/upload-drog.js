'use strict';

/*
 * @Description:  上传文件，三合一组件
 * @Version: 1.0
 * @Autor: chudong
 * @Date: 2021-10-11 15:54:00
 * @LastEditors: chudong
 * @LastEditTime: 2021-11-04 17:12:51
 */
function UploadFile () {
  this.uploadPath = ''; // 上传文件位置
  this.init = false; // 是否初始化
  this.compatible = true; // 是否兼容当前系统，默认全部兼容
  this.uploadElement = null; // 更新视图
  this.isUpload = true; // 是否可上传
  this.limit = {
    size: 30 * 1024 * 1024 * 1024,
    number: 1000
  };
  this.init_data(); // 初始化数据
  this.initialize_view(); // 初始化视图
  this.event_bind(); // 事件绑定
}

var uploadListHtml = '<ul class="dropUpLoadFileHead " style="padding-right:17px;"><li class="fileTitle"><span class="filename">文件名</span><span class="filesize">文件大小</span><span class="fileStatus">上传状态</span></li></ul><ul class="dropUpLoadFile list-list"></ul>';

// 是否显示内容
function is_show (el, show) {
  el.style.display = show ? 'block' : 'none';
}

UploadFile.prototype = {

  /**
   * @description 创建节点
  */
  createEl: function createEl (name) {
    return document.createElement(name);
  },


  /**
   * @description 获取节点
  */
  queryEl: function queryEl (el) {
    return document.querySelector(el);
  },

  /**
   * @description 获取所有节点
  */
  queryElAll: function queryElAll (el) {
    return document.querySelectorAll(el);
  },


  /**
   * @description 绑定事件
  */
  bind: function bind (el, type, fn) {
    if (typeof el === 'string') el = this.queryElAll(el);
    if (typeof el.length !== 'number') el = [el];
    if (typeof type === "function") fn = type, type = "click";
    for (var i = 0; i < el.length; i++) {
      var item = el[i];
      (function (item) {
        item.addEventListener(type || 'click', function (ev) {
          var index = [].indexOf.call(el, item);
          fn.call(item, ev, index);
        },false);
      })(item);
    }
  },


  /**
   * @description 初始化数据
   */
  init_data: function () {
    this.uploadStatus = 0; // 上传状态 0:等待上传  1:上传成功  2:上传中
    this.uploadLimitSize = 1024 * 1024 * 2; // 上传限制字节
    this.uploadList = []; // 上传列表
    this.isUpload = true;
    this.uploadTime = {
      endTime: 0,
      startTime: 0
    };
    this.uploadInfo = { // 提示信息，用于通知当前上传状态
      estimatedTime: 0, // 上传预计耗时，时间戳
      uploadedSize: 0, // 已上传文件大小
      speedInterval: null, // 平局速度定时器
      speedAverage: 0, //平均速度
      uploadTime: 0, // 上传总耗时
      fileSize: 0, // 文件上传字节
      startTime: 0, // 文件上传开始时间
      endTime: 0 // 文件上传结束时间
    };

    this.fileList = []; // 文件列表
    this.fileTotalSize = 0; // 全部文件大小
    this.fileTotalNumber = 0; //全部文件数量

    this.uploadInterval = null;
    this.uploadCycleSize = []; // 上传周期的字段

    this.speedLastTime = 0;
    this.timerSpeed = 0;

    this.uploadError = 0;
  },

  /**
   * @description 初始化上传路径
   */
  init_upload_path: function (path) {
    this.uploadPath = path || bt.get_cookie('Path'); // 上传目录
  },

  /**
   * @description 视图初始化
   */
  initialize_view: function () {
    var title = this.createEl('span');
    this.uploadElement = this.createEl('div');
    this.uploadElement.setAttribute('style', 'position:fixed;top:0;left:0;right:0;bottom:0; background:rgba(255,255,255,0.6);border:3px #ccc dashed;z-index:99999999;color:#999;font-size:40px;text-align:center;overflow:hidden;');
    this.uploadElement.id = 'uploadView';
    is_show(this.uploadElement, false);
    title.setAttribute('style', 'position: fixed;top: 50%;left: 50%;margin-left: -200px;margin-top: -40px;z-index:99999998');
    title.innerText = '上传文件到当前目录下';
    this.uploadElement.appendChild(title);
    document.querySelector('body').appendChild(this.uploadElement);
  },


  /**
   * @description 绑定事件
   */
  event_bind: function event_bind () {
    var _this = this;

    // 进入目标
    this.bind(document, 'dragenter', function (ev) {
      _this.file_drag_hover(ev);
    });

    // 在放置目标上
    this.bind(this.uploadElement, 'dragover', function (ev) {
      _this.file_drag_hover(ev);
    });

    // 离开放置目录
    this.bind(this.uploadElement, 'dragleave', function (ev) {
      if(ev.path[0].id == 'uploadView') return false
      _this.file_drag_hover(ev);
    });

    // 放置目标
    this.bind(this.uploadElement, 'drop', function (ev) {
      if (_this.uploadStatus === 2) {
        layer.msg('正在上传文件，请稍候', {
          icon: 0
        });
        _this.file_drag_hover(ev);
        return false;
      }
      _this.upload_layer();
      _this.isUpload = true;
      _this.file_select_handler(ev);
    });
  },


  /**
   * @description 文件拖拽悬浮状态
   */
  file_drag_hover: function file_drag_hover (event) {
    try {
      if (event.dataTransfer.items[0].kind == 'string') return false;
    } catch (error) {}
    is_show(this.uploadElement, !(event.type === 'dragleave' || event.type === 'drop'));
    event.preventDefault();
    event.stopPropagation();
  },


  /**
   * @description 上传弹窗
   */
  upload_layer: function (list) {
    var _this2 = this;

    if (typeof list === 'undefined') list = [];

    if (this.layer) return false;
    var layerMax = null,
      layerShade = null,
      uploadPath = this.uploadPath || bt.get_cookie('Path');
    this.layer = layer.open({
      type: 1,
      closeBtn: 1,
      maxmin: true,
      area: ['650px', '605px'],
      title: '上传文件到【' + uploadPath + '】--- 支持断点续传',
      skin: 'file_dir_uploads',
      content: '<div class="flex pd15" style="flex-direction: column;-webkit-user-select:none;-moz-user-select:none;">\n                  <div class="upload_btn_groud">\n                    <div class="btn-group">\n                      <button type="button" class="btn btn-primary btn-sm upload_file_btn">上传文件</button>\n                      <button type="button" class="btn btn-primary  btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">\n                        <span class="caret"></span><span class="sr-only">Toggle Dropdown</span>\n                      </button>\n                      <ul class="dropdown-menu">\n                        <li><a href="#" data-type="file">上传文件</a></li>\n                        <li><a href="#" data-type="dir">上传目录</a></li>\n                      </ul>\n                    </div>\n                  <div class="pull-right"><button class="btn btn-sm btn-default empty-record">清空列表</button></div>\n                  <div class="file_upload_info hide">\n                    <span>总进度&nbsp;<i class="uploadProgress"></i>，正在上传&nbsp;<i class="uploadNumber"></i>,</span>\n                    <span class="hide">上传失败&nbsp;<i class="uploadError"></i></span>\n                    <span>上传速度&nbsp;<i class="uploadSpeed">获取中</i>，</span>\n                    <span>预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span>\n                    <i></i>\n                  </div>\n                </div>\n                <div class="upload_file_body ' + (list.length > 0 ? '' : 'active') + '">' + (list.length > 0 ? uploadListHtml : '<span>请将需要上传的文件拖到此处</span>') + '</div>\n              </div>\n              <div class="upload_file_gourp">\n                <button class="btn btn-defalut btn-sm cancelUpload" style="margin-right:15px">取消上传</button>\n                <button class="btn btn-success btn-sm startUpload">开始上传</button>\n              </div>',
      success: function success (layers, indexs) {
        layerMax = _this2.queryEl('.file_dir_uploads').querySelector('.layui-layer-max');
        layerShade = document.querySelector('.layui-layer-shade');
        layerMax.style.display = 'none';
        var cancelUpload = _this2.queryEl('.cancelUpload'),
          startUpload = _this2.queryEl('.startUpload'),
          uploadFileBtn = _this2.queryEl('.upload_file_btn'),
          dropdownItem = _this2.queryElAll('.dropdown-menu li');
        // 下拉选项
        _this2.bind(dropdownItem, function (ev) {
          var type = ev.target.dataset.type;
          if (type === 'file') {
            _this2.queryEl('.upload_file_input').removeAttribute('webkitdirectory');
          } else if (type === 'dir') {
            _this2.queryEl('.upload_file_input').setAttribute('webkitdirectory', '');
          }
          _this2.queryEl('.upload_file_input').click();
        });

        _this2.bind('.empty-record', function (ev) {
          var $li = _this2.queryElAll('.dropUpLoadFile li');
          if ($li.length <= 0) {
            layer.msg('请上传文件！', { icon: 0 });
          } else {
            layer.confirm('是否清空上传列表，是否继续？', {
              title: '清空列表',
              icon: 0
            }, function (indexs) {
              var dropUpLoadFile = _this2.queryEl('.dropUpLoadFile');
              for (var i = 0; i < $li.length; i++) {
                dropUpLoadFile.removeChild($li[i]);
              }
              _this2.init_data();
              var $head = _this2.queryEl('.dropUpLoadFileHead');
              if ($head) $head.removeAttribute('style');
              layer.close(indexs);
            });
          }
        });

        function create_upload_input () {
          // 选择文件或文件夹
          var uploadFileInput = _this2.createEl('input'), uploadBtnGroud = _this2.queryEl('.upload_btn_groud');
          uploadFileInput.setAttribute('type', 'file');
          uploadFileInput.setAttribute('multiple', 'multiple');
          uploadFileInput.style.display = 'none';
          uploadFileInput.classList.add('upload_file_input');
          uploadBtnGroud.appendChild(uploadFileInput);
          _this2.bind(uploadFileInput, 'change', function (ev) {
            _this2.isUpload = true;
            var files = ev.target.files;
            for (var i = 0; i < files.length; i++) {
              if (!_this2.file_upload_limit(files[i])) return false;
            }
            _this2.render_file_list(_this2.fileList);
            uploadBtnGroud.removeChild(uploadFileInput);
            create_upload_input();
          });
        }
        create_upload_input();


        // 点击上传文件按钮
        _this2.bind(uploadFileBtn, function (ev) {
          _this2.queryEl('.upload_file_input').click();
        });

        // 关闭文件视图
        _this2.bind(cancelUpload, function (ev) {
          _this2.cancel_upload(ev);
        });
        // 开始上传
        _this2.bind(startUpload, function () {
          if (_this2.fileList.length === 0) {
            layer.msg('请选择需要上传的文件')
            return false
          }
          _this2.upload_file();
        });
      },
      min: function () {
        layerMax.style.display = '';
        layerShade.style.display = 'none';
      },
      restore: function () {
        layerMax.style.display = 'none';
        layerShade.style.display = '';
      },
      cancel:function () { 
        _this2.cancel_upload();
        return false
      }
    });
  },


  /**
   * @description 获取实时时间
   */
  get_time_real: function get_time_real () {
    return new Date().getTime();
  },

  /**
   * @description 上传前检查文件是否存在
   */
  upload_file_exists: function (config) {
    var _this = this;
    var filename = config.path + config.name;
    var files = this.uploaded_files;
    if (!files) {
      this.uploaded_files = [];
      files = [];
    }
    var data = {
      filename: filename
    };
    // 判断是否上传过该文件名
    var isUploaded = false;
    for (var i = 0; i < files.length; i++) {
      if (files[i] == config.name) {
        isUploaded = true;
        break;
      }
    }
    // 上传过就直接跳过
    if (isUploaded) {
      config.success();
      return;
    }
    this.uploaded_files.push(config.name);
    bt.send('upload_file_exists', 'files/upload_file_exists', data, function (res) {
      if (res.status) {
        var is_open = _this.is_open_cover_layer;
        if (is_open === 0) {
          bt.open({
            type: 1,
            area: '400px',
            title: '上传文件到【' + config.path.substr(0, config.path.length - 1) + '】',
            btn: ['确定', '跳过'],
            content: '\
              <div class="warning_layer_box">\
                <div class="warning_layer_head">\
                  <i class="layui-layer-ico layui-layer-ico3"></i>\
                  <div class="cont">检测到有同命名文件【' + config.name + '】，是否覆盖？</div>\
                </div>\
                <div class="details">\
                  <div class="left">\
                    <input type="checkbox" id="all_operation" />\
                    <label for="all_operation">为之后文件冲突执行此操作</label>\
                  </div>\
                </div>\
              </div>\
            ',
            cancel: function () {
              config.error();
            },
            yes: function (index) {
              var checked = $('#all_operation').is(':checked');
              if (checked) {
                _this.is_open_cover_layer = 1;
              }
              config.success();
              layer.close(index);
            },
            btn2: function (index) {
              var checked = $('#all_operation').is(':checked');
              if (checked) {
                _this.is_open_cover_layer = 2;
              }
              config.error();
              layer.close(index);
            }
          });
        } else if (is_open === 1) {
          config.success();
        } else {
          config.error();
        }
      } else {
        config.success();
      }
    });
  },

  /**
   * @description 上传文件
   */
  upload_file: function (fileStart, index) {
    var _this3 = this;
    this.uploadPath = this.uploadPath || bt.get_cookie('Path');

    // 开始上传
    if (fileStart == undefined && this.uploadList.length == 0) {
      fileStart = 0, index = 0;
      this.is_open_cover_layer = 0;
      this.uploadStatus = 2;
      this.uploaded_files = []; // 上传过的文件
      this.uploadCycleSize = []; // 上传速度匹配
      this.uploadTime.startTime = this.get_time_real(); // 设置上传开始时间
      var startUpload = this.queryEl('.startUpload');
      startUpload.setAttribute('disabled','disabled')
      startUpload.innerText = '正在上传';
    }
    // 结束上传
    if (this.fileList.length === index) {
      clearTimeout(this.uploadInterval);
      this.uploadStatus = 1;
      this.uploadTime.endTime = this.get_time_real(); // 设置上传开始时间
      this.set_upload_view();
      this.init_data();
      bt_file.reader_file_list({ path: this.uploadPath });
      return false;
    }

    // 创建文件对象和切割文件
    var item = this.fileList[index],
      fileEnd = '';
    if (item == undefined) return false;

    // 检测文件是否存在
    var f_path = this.uploadPath + item.path + '/';
    f_path = f_path.replace(/\/\//g, '/');
    this.upload_file_exists({
      name: item.name,
      path: f_path,
      error: function () {
        $('.dropUpLoadFile li').eq(index).find('.fileStatus .upload_info').html('文件已存在');
        _this3.upload_file(0, ++index);
      },
      success: function () {
        // 设置切割文件时间段
        var uploadedSize = _this3.uploadInfo.uploadedSize;
        _this3.uploadInterval = setInterval(function () {
          if (_this3.uploadCycleSize.length === 4) _this3.uploadCycleSize.splice(0, 1);
          _this3.uploadCycleSize.push(Math.abs(_this3.uploadInfo.uploadedSize - uploadedSize));
        }, 1000);

        // 渲染上传时间和上传进度
        _this3.uploadInfo.endTime = _this3.get_time_real();
        _this3.reander_timer_speed();
        _this3.uploadInfo.startTime = _this3.get_time_real();

        // 获取上传速度
        var speed = _this3.get_update_speed(),
          // 获取上传速度
          limitSize = _this3.uploadLimitSize;
        // 判断速度是否操作阈值，超过阀值后，采用倍速的方案，最大只能支持4，8MB
        var maxDouble = Math.floor(speed / _this3.uploadLimitSize);
        if (maxDouble && index > 1) limitSize = (maxDouble > 4 ? 4 : maxDouble) * limitSize;

        // 实时反馈
        if (fileStart == 0) {
          _this3.uploadInfo.startTime = _this3.get_time_real();
          item = $.extend(item, {
            percent: '0%',
            upload: 2,
            upload_size: '0B'
          });
        }

        _this3.set_upload_view(index, item);

        fileEnd = Math.min(item.file.size, (fileStart + limitSize))

        _this3.uploadInfo.fileSize = fileEnd - fileStart;

        var form = new FormData();
        form.append("f_path", f_path);
        form.append("f_name", item.name);
        form.append("f_size", item.file.size);
        form.append("f_start", fileStart);
        form.append("blob", item.file.slice(fileStart, fileEnd));

        // 发送请求
        $.ajax({
          url: '/files?action=upload',
          type: "POST",
          data: form,
          async: true,
          processData: false,
          contentType: false,
          success: function success (rdata) {
            // 判断是否为数字
            if (typeof rdata === "number") {
              _this3.set_upload_view(index, $.extend(item, {
                percent: (rdata / item.file.size * 100).toFixed(2) + '%',
                upload: 2,
                upload_size: bt.format_size(rdata)
              }));

              // 判断是否为文件结束，已上传文件大小
              if (fileEnd != rdata) {
                _this3.uploadInfo.uploadedSize += rdata;
              } else {
                _this3.uploadInfo.uploadedSize += parseInt(fileEnd - fileStart);
              }

              // console.log(rdata, index);

              // 继续上传文件
              _this3.upload_file(rdata, index);
            } else {
              // 请求状态，判断文件是否上传成功
              if (rdata.status) {
                _this3.uploadInfo.endTime = _this3.get_time_real();
                _this3.uploadInfo.uploadedSize += parseInt(fileEnd - fileStart);
                _this3.set_upload_view(index, $.extend(item, {
                  upload: 1,
                  upload_size: item.size
                }));
              } else {
                _this3.set_upload_view(index, $.extend(item, {
                  upload: -1,
                  errorMsg: rdata.msg
                }));
                _this3.uploadError++;
              }
              _this3.upload_file(0, ++index);
            }
            // 实时更新文件上传状态
          },
          error: function (e) {
            if (_this3.fileList[index].req_error === undefined) _this3.fileList[index].req_error = 1;
            if (_this3.fileList[index].req_error > 2) {
              _this3.set_upload_view(index, $.extend(_this3.fileList[index], {
                upload: -1,
                errorMsg: e.statusText == 'error' ? '网络中断' : e.statusText
              }));
              _this3.uploadError++;
              _this3.upload_file(fileStart, index += 1);
              return false;
            }
            _this3.fileList[index].req_error += 1;
            _this3.upload_file(fileStart, index);
          }
        });
      }
    });
  },


  /**
   * @description 设置上传视图
   */
  set_upload_view: function set_upload_view (index, config) {
    var _this4 = this;
    if (typeof index === 'undefined') {
      var file_upload_info = this.queryEl('.file_upload_info'),
        time = this.get_time_real(),
        s_peed = this.to_size(this.uploadInfo.uploadedSize / ((time - this.uploadTime.startTime) / 1000));
      file_upload_info.innerHTML = '<span>上传成功 ' + (this.uploadList.length - this.uploadError) + '个文件，' + (this.uploadError ? '上传失败' + this.uploadError + '个文件，' : '') + '耗时' + this.diff_time(this.uploadTime.startTime, time) + ',平均速度 ' + s_peed + '/s</span><i class="ico-tips-close"></i>';
      this.bind(file_upload_info.querySelector('.ico-tips-close'), function (ev) {
        var parent = this.parentNode.parentNode;
        parent.querySelector('.btn-group').classList.remove('hide');
        parent.querySelector('.file_upload_info').classList.add('hide');
      });
      var startUpload = this.queryEl('.startUpload')
      startUpload.removeAttribute('disabled')
      startUpload.innerText = '开始上传'
      _this4.init_data();
      return false;
    }
    try {
      var item = document.querySelectorAll('.dropUpLoadFile li')[index];
      var file_info = this.queryEl('.file_upload_info');

      if (file_info.querySelectorAll('.uploadProgress').length === 0) {
        file_info.innerHTML = '<span>\n      总进度&nbsp;<i class="uploadProgress"></i>，\n      正在上传&nbsp;<i class="uploadNumber"></i>，</span>\n      <span style="display:none">上传失败&nbsp;<i class="uploadError"></i></span><span>\n      上传速度&nbsp;<i class="uploadSpeed">获取中</i>，</span><span>\n      预计上传时间&nbsp;<i class="uploadEstimate">获取中</i></span><i></i>';
      }

      var file_info_parent = file_info.parentElement;
      file_info_parent.querySelector('.btn-group').classList.add('hide');
      file_info_parent.querySelector('.file_upload_info').classList.remove('hide');

      var file_info_error = file_info.querySelector('.uploadError');
      file_info_error.innerText = '(' + this.uploadError + '份)';
      if (this.uploadError > 0) file_info_error.parentElement.style.display = 'block';

      if (config.upload === 1 || config.upload === -1) {
        this.fileList[index].is_upload = true;
        this.uploadList.push(this.fileList[index]);
        item.querySelector('.fileLoading').setAttribute('style', 'width:100%;opacity:.5;background:' + (config.upload == -1 ? '#ffadad' : '#20a53a21'));
        item.querySelector('.filesize').innerText = config.size;
        item.querySelector('.fileStatus').innerHTML = this.is_upload_status(config.upload, config.upload === 1 ? '(耗时:' + this.diff_time(this.uploadTime.startTime, this.uploadTime.endTime) + ')' : config.errorMsg);
        var dropUpLoadFile = this.queryEl('.dropUpLoadFile');
        if(this.uploadList.length === 1) dropUpLoadFile.scrollTop = 0
        if(this.uploadList.length > 1) dropUpLoadFile.scrollTop += 45.5
      } else {
        item.querySelector('.fileLoading').setAttribute('style', 'width:' + config.percent);
        item.querySelector('.filesize').innerText = config.upload_size + '/' + config.size;
        item.querySelector('.fileStatus').innerHTML = this.is_upload_status(config.upload, '(' + config.percent + ')');
      }

      file_info.querySelector('.uploadNumber').innerText = '(' + this.uploadList.length + '/' + this.fileList.length + ')';
      file_info.querySelector('.uploadProgress').innerText = ((this.uploadInfo.uploadedSize / this.fileTotalSize) * 100).toFixed(2) + '%';
    } catch (e) {
      console.log(e)
    }

  },


  /**
   * @description 上传状态
   * @param {*} status 
   * @param {*} val 
   * @returns 
   */
  is_upload_status: function is_upload_status (status, val) {
    if (val === undefined) val = '';
    switch (status) {
      case -1:
        return '<span class="upload_info upload_error" title="上传失败' + (val != '' ? ',' + val : '') + '">上传失败' + (val != '' ? ',' + val : '') + '</span>';
      case 0:
        return '<span class="upload_info upload_primary">等待上传</span>';
      case 1:
        return '<span class="upload_info upload_success">上传成功</span>';
      case 2:
        return '<span class="upload_info upload_warning">上传中' + val + '</span>';
      case 3:
        return '<span class="upload_info upload_success">已暂停</span>';
    }
  },

  /**
   * @description 取10秒内上传平均值
   */
  get_update_speed: function get_update_speed () {
    var sum = 0;
    for (var i = 0; i < this.uploadCycleSize.length; i++) {
      sum += this.uploadCycleSize[i];
    }
    var content = sum / this.uploadCycleSize.length;
    return isNaN(content) ? 0 : content;
  },


  // 渲染上传速度
  reander_timer_speed: function reander_timer_speed () {
    var done_time = new Date().getTime();
    if (done_time - this.speedLastTime > 1000) {
      var s_time = (this.uploadInfo.endTime - this.uploadInfo.startTime) / 1000;
      this.timerSpeed = (this.uploadInfo.fileSize / s_time).toFixed(2);
      if (this.timerSpeed < 2) return;
      this.queryEl('.file_upload_info').querySelector('.uploadSpeed').innerText = bt.format_size(isNaN(this.timerSpeed) ? 0 : this.timerSpeed) + '/s';
      var estimateTime = this.time(parseInt((this.fileTotalSize - this.uploadInfo.uploadedSize) / this.timerSpeed * 1000));
      if (!isNaN(this.timerSpeed)) this.queryEl('.file_upload_info').querySelector('.uploadEstimate').innerText = estimateTime.indexOf('NaN') == -1 ? estimateTime : '0秒';
      this.speedLastTime = done_time;
    }
  },
  to_size: function to_size (a) {
    var d = [" B", " KB", " MB", " GB", " TB", " PB"];
    var e = 1024;
    for (var b = 0; b < d.length; b += 1) {
      if (a < e) {
        var num = (b === 0 ? a : a.toFixed(2)) + d[b];
        return !isNaN(b === 0 ? a : a.toFixed(2)) && typeof num != 'undefined' ? num : '0B';
      }
      a /= e;
    }
  },
  time: function time (date) {
    var hours = Math.floor(date / (60 * 60 * 1000));
    var minutes = Math.floor(date / (60 * 1000));
    var seconds = parseInt(date % (60 * 1000) / 1000);
    var result = seconds + '秒';
    if (minutes > 0) {
      result = minutes + "分钟" + seconds + '秒';
    }
    if (hours > 0) {
      result = hours + '小时' + Math.floor((date - hours * (60 * 60 * 1000)) / (60 * 1000)) + "分钟";
    }
    return result;
  },
  diff_time: function diff_time (start_date, end_date) {
    if (typeof start_date !== "number") start_date = start_date.getTime();
    if (typeof end_date !== "number") end_date = end_date.getTime();
    var diff = end_date - start_date,
      minutes = Math.floor(diff / (60 * 1000)),
      leave3 = diff % (60 * 1000),
      seconds = leave3 / 1000,
      result = seconds.toFixed(minutes > 0 ? 0 : 2) + '秒';
    if (minutes > 0) {
      result = minutes + "分" + seconds.toFixed(0) + '秒';
    }
    return result;
  },

  /**
   * @description 取消上传
   */
  cancel_upload: function cancel_upload () {
    var _this4 = this;
    if (this.uploadStatus === 2) {
      layer.confirm('是否取消上传当前列表的文件，若取消上传，已上传的文件，需用户手动删除，是否继续？', {
        title: '取消上传文件',
        icon: 0
      }, function (indexs) {
        _this4.init_data();
        _this4.cancel_upload_layer();
        layer.close(indexs)
      });
    } else {
      _this4.init_data();
      _this4.cancel_upload_layer();
    }
  },


  /**
   * @description 关闭上传弹窗
   */
  cancel_upload_layer: function cancel_upload_layer () {
    layer.close(this.layer);
    this.layer = false;
    this.init_data();
  },


  /**
   * @description 渲染列表
   * 
   */
  render_file_list: function render_file_list (list) {
    var _this5 = this;
    var html = '';
    for (var i = 0; i < list.length; i++) {
      var item = list[i], name = ((item.path || '/') + '/' + item.name).replace(/\/\//g, '/');
      html += '<li><div class="fileItem"><span class="filename" title="文件名:' + item.name + '\r文件类型:' + item.file.type + '\r文件大小:' + item.size + '\r文件路径:' + name + '"><i class="ico ico-' + item.type + ' ico-file"></i><span>' + name + '</span></span>\n        <span class="filesize" title="' + item.size + '">' + item.size + '</span>\n        <span class="fileStatus"><span class="upload_info upload_primary">等待上传</span><a class="btlink cancel-btn"><span class="glyphicon glyphicon-remove" title="取消上传"></span></a></span>\n        <div class="fileLoading"></div>\n      </div></li>';
      this.uploadInfo.fileSize += item.file.size;
    }
    var upload_file_body = this.queryEl('.upload_file_body');
    upload_file_body.className = 'upload_file_body';
    upload_file_body.innerHTML = uploadListHtml;
    this.queryEl('.upload_file_gourp').className = 'upload_file_gourp';
    this.queryEl('.dropUpLoadFile').innerHTML = html;
    var dropUpLoadFileHead = this.queryEl('.dropUpLoadFileHead');
    if (list.length <= 10) {
      dropUpLoadFileHead.removeAttribute('style');
    } else {
      dropUpLoadFileHead.style.paddingRight = bt_file.upload_file_body_width + 'px';
      dropUpLoadFileHead.style.boxShadow = '0 5px 2px -3px #ececec';
    }
    var cancelBtn = this.queryElAll('.cancel-btn');
    this.bind(cancelBtn, function (ev, index) {
      _this5.fileTotalSize = _this5.fileTotalSize - _this5.fileList[index].file.size;
      _this5.fileTotalNumber = _this5.fileTotalNumber - 1;
      _this5.fileList.splice(index, 1);
      _this5.queryElAll('.dropUpLoadFile li')[index].remove();
    });
  },


  /**
   * @description 文件上传限制
   * @param {Object} e 文件对象
   */
  file_upload_limit: function file_upload_limit (e, path) {
    var extName = e.name.split('.');
    path = path || e.webkitRelativePath
    var paths = path.split('/');
    path = ('/' + paths.slice(0, paths.length - 1).join('/')).replace('//', '/');
    this.fileList.push({
      file: e,
      path: path,
      name: e.name,
      size: bt.format_size(e.size),
      type: extName.length > 1 ? extName[extName.length - 1] : 'txt',
      status: 0
    });
    this.fileTotalSize += e.size;
    this.fileTotalNumber ++;
    if (this.fileTotalNumber >= this.limit.number) {
      layer.msg('当前文件数量已超过文件上传上限' + this.limit.number + '个， 请压缩文件夹后重试！');
      return false;
    }
    if (this.fileTotalSize >= this.limit.size) {
      layer.msg('当前文件大小已超过文件上传' + bt.format_size(this.limit.size) + '限制， 请使用SFTP/FTP等工具上传文件！');
      return false;
    }
    return true
  },

  test_index:0,

  /**
   * @description 文件夹文件内容递归
   * @param {object} item 文件对象 
   */
  traverse_file_tree: function traverse_file_tree (item) {
    var _this6 = this;
    var path = item.fullPath || '';
    if (item.isFile) {
      item.file(function (e) {
        _this6.file_upload_limit(e, path);
      });
      clearTimeout(this.timeNumber);
      this.timeNumber = setTimeout(function () {
        _this6.load.close();
        if (_this6.isUpload) {
          _this6.render_file_list(_this6.fileList);
        } else {
          var layers = _this6.layer;
          _this6.init_data();
          _this6.layers = layers;
        }
      }, 10);
    } else if (item.isDirectory) {
      var dirReader = item.createReader();
      var fnReadEntries = function (entries) {
        [].forEach.call(entries,function (e) {
          if (!_this6.isUpload) return false;
          _this6.traverse_file_tree(e);
        });
        if (entries.length > 0) {
          dirReader.readEntries(fnReadEntries);
        }
      };    
      dirReader.readEntries(fnReadEntries)
      setTimeout(function () {
        if (_this6.fileList.length === 0) {
          layer.msg('拖拽上传文件夹内容为空')
        }
      }, 500)
    }
  },
  


  /**
   * @description 文件选择处理程序
   * @param {object} ev 事件
   */
  file_select_handler: function file_select_handler (ev) {
    var _this7 = this;
    this.file_drag_hover(ev);
    this.load = bt.load('正在获取文件信息，请稍候...');
    this.timeNumber = 0;
    if (ev.target.files) {
      var items = ev.target.files;
      [].forEach.call(items, function (item) {
        _this7.traverse_file_tree(item);
      });
    } else if (ev.dataTransfer.items) {
      var items = ev.dataTransfer.items;
      [].forEach.call(items, function (ev) {
        var getAsEntry = ev.webkitGetAsEntry || ev.getAsEntry;
        var item = getAsEntry.call(ev)
        if (item) {
          if (!_this7.isUpload){
            return false
          }
          _this7.traverse_file_tree(item);
        }
      });
    }
  }
};

var uploadFiles = new UploadFile();

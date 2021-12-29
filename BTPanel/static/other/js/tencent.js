$(function () {


    function get_tencent_info(is_refresh, callback) {
        bt_tools.send({ url: '/plugin?action=a&name=tencent&s=get_local_lighthouse', verify: false, data: (is_refresh ? { force: 1 } : {}) }, function (res) {
            console.log(res)
            if (callback) callback(res)
            if (location.pathname !== '/') return false
            if (!res) return false;
            var private = '<span>', public = '<span>', index = 0;
            for (var i = 0; i < res.PrivateAddresses.length; i++) {
                var item = res.PrivateAddresses[i];
                private += item + (i != res.PrivateAddresses.length - 1 ? '、' : '');
            }
            private += ' (内)</span>';

            for (var i = 0; i < res.PublicAddresses.length; i++) {
                var item = res.PublicAddresses[i]
                public += item + (i != res.PublicAddresses.length - 1 ? '、' : '')
            }
            public += ' (公)</span>'
            reader_tencent_info({
                ipv4_html: private + public,
                region_html: res.Region + '&nbsp;' + res.Region_title,
                edtime_html: res.ExpiredTime ? bt.format_data(new Date(res.ExpiredTime).getTime()) : '----',
                InstanceId: res.InstanceId,
                is_cvm: res.server_type === 'cvm' ? true : false,
            })
        }, false);
    }


    function reader_tencent_info(config) {
        if (typeof config == 'undefined') config = {}
        $('.tencent_tips').remove()
        var html = '<div class="conter-box bgw mtb15 tencent_tips">' +
            '<style>.tencent_tips{min-height:50px;line-height:50px;}.tencent_tips .tips_box{display:inline-block;position:relative;padding:0 15px;}.tips_box .tencent_ico{display:inline-block;height:25px;width:25px;position:relative;top:6.5px;background-image:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAYAAADE6YVjAAACvElEQVRIS+2VS0iUYRSGn/PPhNLFpPsQhiHhiNFFoUUXKKhFUQuLCslxIgKlzDKidNXMKouImNrkJp2iKwZFoIsgCSkDR1wYNk7BLDKDkG50UZw58c+MGs0/Y7ZwU2d7zvc+3znn/fiEKQiZAgb/GqRSFzAtsg1kNcgKkDAaHcAwmvFJYKKRTzyuqshRRI4CSy3FVBu4bKtIB0oPOaJ+UFdCIIDoE6LRBxh2J7AT1S2xnHAXn7EnFSg1pDpyBpXauIhU4JOGJJFqPYnq2UTNOXxyygpkDTmgs5hBCHQhKnVclvqU46iKeBA5HctnyEzOy9ffa60h1SMlqHEvXiyZXJKhtMs9prlclPCfjasjlIVt5Djfpm3ApjMYMgbIHr5PcUFjSkiTejBYirIE5RXQj1s8v9aPdxLo245oPaqFyYLSyILph8jJ+T6W8+ty4BKw0eICbSgVuKUv7gszOsMO5MdTIBehDdVmxHhNNFoIchAhH2jHbitl5bI3XNVV2LgJmC4DxYtBN8pcoAYoRLmOW2LOjEMCvRdAahB5QVG+ecPx6AzOw+BGzK5R9dLrfIhyCyEPGAZKKZfE/hLH/Po41qGwFZe0xiFdwZ7YmETXUlTwLKn9rtB8IiOHCTpbiXIbWAJ8wWAvZdKSVN+o6zBoR6nHLXWJcb0cRJhDsTP1u2nS9Qh3AAcwiLIbt5g3tg6/KtBGuWwa7eQ5qmtSdnJNN6LcBeYhvEXYRZl0pASMdiL4cYl7FFKL6hnLnTTpZoRmIAsljJ0S9kl32nczuhPTEG7xxCGhUAafI6a7isbcFaWHd441fJjtBTKBIBEq04rbWYxSF3OX0IJLto27a9zGV4AdMaFPWUH6HXko9rTCVknTvgZeXGI+ToufMdC7n4/ZJ+hf9H7S4hBAeGTa9tezE/8nf0H6/ch/yKSG+BPZWO0aiPkdwgAAAABJRU5ErkJggg==);}.tips_box .tencent_explain{font-size:14px;color:#666;font-weight:600;margin-left:5px;}.tips_box.tencent_division{padding-right:15px;}.tips_box.tencent_division::after{content:"";display:inline-block;position:absolute;border-right:1px solid #ececee;height:25px;padding-right:15px;top:12.5px;}.tips_box .tencent_content span{margin-left:8px;}.processing{background-image:url(static/layer/skin/default/loading-2.gif);width:12px;height:12px;display:inline-block;background-size:100% 100%;background-repeat:no-repeat;position:relative;top:2px;left:5px;}</style>' +
            '<div class="tips_box tencent_division"><span class="tencent_ico"></span><span class="tencent_explain">腾讯云专享版</span></div>' +
            '<div class="tips_box"><span class="tencent_title">主机IPv4:</span><span class="tencent_content">' + (config.ipv4_html || '<span>----</span>') + '</span></div>' +
            '<div class="tips_box" ><span class="tencent_title">区域:</span><span class="tencent_content"><span>' + (config.region_html || '<span>----</span>') + '</span></span></div>' +
            '<div class="tips_box" ><span class="tencent_title">到期时间:</span><span class="tencent_content"><span>' + (config.edtime_html || '<span>----</span>') + '</span></span></div>' +
            '<div class="tips_box ' + (typeof config.is_cvm === "boolean" && !config.is_cvm ? '' : 'hide') + '"><span class="tencent_title">流量包:</span><span class="tencent_content request_pack"><span><span>----</span></span>&nbsp;&nbsp;<a href="javascript:;" class="btlink" onclick="request_pack()">详情</a></span></div>' +
            '<div class="tips_box" style="display:' + (!(JSON.stringify(config) == '{}') ? 'inline-block' : 'none') + '">' +
            '<a class="btn btn-sm btn-success mr5"  target="_blank" href="https://console.cloud.tencent.com/lighthouse/instance/detail?id=' + config.InstanceId + '">续费</button>' +
            '<a class="btn btn-sm btn-success mr5" target="_blank" href="https://console.cloud.tencent.com/lighthouse/instance/detail?id=' + config.InstanceId + '">升级套餐</a>' +
            '<button class="btn btn-sm btn-default mr5 set_tencent_key"><span>密钥管理</span></button>' +
            '<button class="btn btn-sm btn-default mr5 set_tencent_snapshots"><span>快照</span></button>' +
            '<button class="btn btn-sm btn-default mr5 update_tencent" title="更新当前腾讯云专版数据" ><span>更新</span></button>' +
            '<button class="btn btn-sm btn-default mr5 refresh_tencent_info" title="重新获取服务器信息"><span class="glyphicon glyphicon-refresh mr5"></span><span>刷新</span></button>' +
            '<div class="tips_box" ><span class="tencent_title"><a href="https://www.bt.cn/bbs/thread-66887-1-1.html"  target="_blank"  title="查看教程" class="btlink">查看教程</a></span></div></div>' +
            '<div class="tips_box" style="display:' + (JSON.stringify(config) == '{}' ? 'inline-block' : 'none') + '">' +
            '<button class="btn btn-sm btn-success mr5 set_tencent_key" target="_blank" href="javascript:;">关联腾讯云API密钥</button>' +
            '</div>' +
            '</div>';
        $('.danger-tips').after(html);
        $('.tencent_tips .set_tencent_key').click(function () {
            bt_tools.send('tencent/get_config', function (res) {
                tencent_key_view(res);
            }, { plugin: true, load: '获取密钥中' });
        });
        $('.set_tencent_snapshots').click(function () {
            tencent_snapshots_view(config);
        })
        $('.refresh_tencent_info').click(function () {
            var loadT = bt.load('正在重新获取服务器信息，请稍候...');
            get_tencent_info(true, function () {
                $('.tencent_tips').remove()
                loadT.close();
            });
        })
        $('.update_tencent').click(function () {
            update_tencent()
        })
        if (typeof config.is_cvm === "boolean" && !config.is_cvm) {
            get_request_pack(function (res) {
                var packageSet = res.InstanceTrafficPackageSet[0], total = 0, used = 0
                for (var i = 0; i < packageSet.TrafficPackageSet.length; i++) {
                    var item = packageSet.TrafficPackageSet[i];
                    total += item.TrafficPackageTotal
                    used += item.TrafficUsed
                }
                $('.tencent_tips .request_pack span').html(bt.format_size(used) + '/' + bt.format_size(total));
            })
        }
    }


    // 腾讯云更新程序
    function update_tencent() {
        layer.confirm('更新当前腾讯专版功能 (面板功能除外，面板更新请使用自带更新功能) ，是否继续操作?', { title: '更新腾讯云专版数据', icon: 0, closeBtn: 2, area: '420px' }, function () {
            var loadT = bt.load('正在更新腾讯云专版数据，请稍后...');
            bt_tools.send('/plugin?action=a&name=tencent&s=update_tencent', function (rdata) {
                loadT.close();
                bt.msg(rdata);
                setTimeout(function () {
                    location.reload();
                }, 1500)
            })
        })
    }


    function tencent_key_view(data) {
        if (typeof data == "undefined") data = {};
        bt_tools.open({
            title: false,
            area: '450px',
            zIndex: 19891016,
            btn: false,
            content: '<div class="tx_key_bind">' +
                '<div class="tx_key_title"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAZCAYAAAC/zUevAAADk0lEQVRIS62WXWxTZRjHf88pqxIjIjXxA4k4nCLGTEagg0SF6IWYYEBCL8hgDjPR8O1HxCu3GyBe6NhClJigWPBmQYyIMXwkM4R1JUHDyJiDTpBGjVlWErMLieM85j3nrJx2bU/38d40fd//8+/vPM9znrfCWNcWnY+wBJgP1Hif3cBFIIXFflrkr7HYStni7Todm3dR3kG4s0Tcn8DnY4EpD2KzrsRiF/Bk2dDQh8XrtMjZoJhgiO36DDangRk+s6MIpxjmF/ZJgh1aic08lDeAFT7dDZR62uRYKZDSEG4JfgSijolwHGUXrdJZ1HSbrkbZD0Q8TQaLBbTItWIxpSG2aiuwxQv+HXiOVrkelF7c5v0eeMiD/5K90jBeiDTwsBOsrKZNvgkEGBFs1Z3AbuAm0I1FrFg2imdisy7H4gcPoIM2WVY2wIhwk9YQ5hqfSGZ8PbHD/o57/htkKPQAFfbX7A7HxwxhAg7rvdhUE6KXtfJ3IY/cTHRdmQYcAFkEzMoN0CNIaC/RyjOBMHF9EJuNWLwKPJ3VK2mEcwgbqJN/RvZvQyR6ZyMVXwHPlvwR1WYWVzUV1RzUJkI0ol5TFhaeYZj1NLhvjAuR7I2gU06DVOfFdACPZ7t85LAYiAGw+DAwU67gAjYvUC+DHkTqU5Q3fcEbCetRaqoGnL1EqhFxJuZ9WY1IE9E5zdnv+QBKPxYfc4tT2FyngkrgFdR5Y9wlfEadvCUkU+tRDmYPah8r/MYkf6tG7RZgqae9jNyKEX3iAvkAQjthNhET9yHyV1zVt1UvdKW+AF7z0D6gds6eounsTE9F/m0FWQf6EourOgoC1EmsZEniasa7maomG3EhkTLdutDZCFlzWVjZF1jTc1efZ9GjP40LwJgfUnPP9Di/o3QLyf4hVO9yNoqVohBVoRIEZcDv4yuJKcdVYLZLpcucFAetiQL4MyH0GIjjwMseROkZYEQTBTAecTWX2QGvJ9oNxEfAe7cfvuIpah+5VDAZkwHgQgwBbgvYNAud6RlYN89nS+KUxW5Ap55kyaw/sjATBTik07B5EcH8PZjp+X7LOlnlzoTE5ShidY1+eukGzZCJDDA4fY3vPLhvcs3uBhaM8r+DCDHJ+O6O/vcRHT0jMpH2PICgti3nvI9hVtIgvxpx7nRMXlmDytvmZXWcJh/gBDYJ6iXnAiw8ont6wqTvb2Qg4g6UyVjCz/7r22/5P8qBPGWz9M1HAAAAAElFTkSuQmCC" /><span>关联腾讯云API密钥</span><span></span></div>' +
                '<div class="tx_key_find"><span class="tips_placeholder">APPID</span><input type="text" autocomplete="off" autofocus="autofocus" name="appid" value="' + (data.appid || '') + '"/><span class="close_input hide"></span></div>' +
                '<div class="tx_key_find"><span class="tips_placeholder">SecretId</span><input type="text" autocomplete="off" name="secretId" value="' + (data.secretId || '') + '"/><span class="close_input hide"></span></div>' +
                '<div class="tx_key_find"><span class="tips_placeholder">SecretKey</span><input type="text" autocomplete="off" name="secretKey" value="' + (data.secretKey || '') + '"/><span class="close_input hide"></span></div>' +
                '<div class="tx_key_find" ' + (!$.isEmptyObject(data) ? 'style="padding-bottom:0"' : '') + ' ><button class="set_key_bind">' + ($.isEmptyObject(data) ? '关联API密钥' : '保存API密钥') + '</button></div>' +
                (!$.isEmptyObject(data) ? '<div class="tx_key_find"><button class="set_clear_bind">取消关联密钥</button></div>' : '') +
                '<div class="tx_key_help" style="color:red;">温馨提示：请确保当前关联的密钥是本服务器的，如果不一致，将会导致数据获取异常和不正确，请须知</div>' +
                '<div class="tx_key_help">您正在使用宝塔面板腾讯云联合定制版，请关联您的腾讯云API密钥，如何获取腾讯云API密钥，<a href="https://console.cloud.tencent.com/cam/capi" target="_blank" class="btlink">点击查看</a></div>' +
                '</div>',
            success: function (layero, index) {
                $('[name="secretKey"]').attr('type', 'password');
                var inputs = $('.tx_key_find input');
                inputs.each(function () {
                    if ($(this).val() != '') $(this).prev().addClass('offset');
                });
                inputs.prev().click(function () {
                    $(this).next().focus();
                });
                inputs.focus(function () {
                    var that = this;
                    var input_val = $(that).val();
                    if ($(that).attr('name') == 'secretKey') $(that).attr('type', 'password');
                    $(that).prev().addClass('offset');
                    if (input_val != '') $(that).next().removeClass('hide');
                }).blur(function () {
                    var that = this;
                    setTimeout(function () {
                        $(that).next().addClass('hide');
                    }, 500);
                    if ($(that).val() != '') {
                        $(that).prev().addClass('offset');
                    } else {
                        $(that).prev().removeClass('offset');
                    }
                }).on('input', function () {
                    var input_val = $(this).val(), close_btn = $(this).next(), name = $(this).attr('name');
                    $(this).val(input_val.replace(/(^\s*)|(\s*$)/g, ""));
                    if (input_val == '') {
                        close_btn.addClass('hide');
                    } else {
                        close_btn.removeClass('hide');
                    }
                    if (bt.check_chinese(input_val)) {
                        layer.tips('密钥内容不包含中文', this, { loadT: [2, 'red'] });
                    }
                }).next().click(function () {
                    $(this).prev().val('').focus();
                    $(this).addClass('hide');
                });
                $('.set_key_bind').click(function () {
                    var data = {};
                    inputs.each(function () { data[$(this).attr('name')] = $(this).val() });
                    for (let i = 0; i < inputs.length; i++) {
                        var item = inputs.eq(i), item_val = item.val();
                        if (item_val == '') {
                            layer.msg('腾讯云' + item.prev().text() + '字段，不能为空！', { icon: 0 });
                            item.focus();
                            return false;
                        }
                        data[item.attr('name')] = item_val;
                    }
                    bt_tools.send('tencent/set_config', data, function (res) {
                        layer.closeAll()
                        bt_tools.msg(res);
                        setTimeout(function () {
                            window.location.reload()
                        }, 1500)
                    }, { plugin: true, load: '配置密钥中' });
                });
                $('.set_clear_bind').click(function () {
                    layer.confirm('是否取消关联腾讯云API密钥,是否继续？', { title: '提示', icon: 0, closeBtn: 2, zIndex: 9999999999, btn: ['确认', '取消'] }, function (index, layero) {
                        bt_tools.send('tencent/cancel_config', function (res) {
                            bt_tools.msg(res);
                            layer.close(index);
                            location.reload();
                        }, { plugin: true, load: '取消API密钥关联' });
                    }, function (index) {
                        layer.close(index);
                    });
                });
            },
            end: function () {
                bt.set_storage('local', 'tencent', '1')
            }
        });
    }


    function tencent_snapshots_view(config) {
        var help = (!config.is_cvm ? ('1、每个地域的免费快照配额为已创建实例数<span style="font-weight:600;">(待回收实例和存储型套餐实例除外)乘以2</span>，且最多不超过4个。</br>' +
            '2、使用存储型套餐的实例不支持创建快照。</br>' +
            '3、创建快照通常可以在5分钟内完成，请耐心等待，创建过程中无需关机。</br>') : (
                '1、快照仅能捕获该时刻已经在云硬盘上的数据，而无法将在内存中的数据记录下来。因此，为了保证快照能尽可能回复完整的数据，建议您在制作快照前进行以下操作：</br>' +
                '<li>数据库业务：进行 flush and lock 表操作，加锁并下刷表数据</li>' +
                '<li>文件系统：进行 sync 操作，下刷内存数据</li>' +
                '2、快照已正式商业化，请您关注因此产生的费用。有关快照的更多信号可参考<a href="https://cloud.tencent.com/document/product/362/5754" class="btlink" target="_blank">快照概述</a>以及<a href="https://cloud.tencent.com/document/product/362/17935" class="btlink" target="_blank">快照商业化FAQ</a>'));
        bt_tools.open({
            title: '腾讯云硬盘快照',
            area: '600px',
            btn: false,
            content: '<div class="pd15">' +
                '<div class="alert alert-danger" style="line-height: 20px;">' +
                '温馨提示：</br>' + help + '</div>' +
                '<div class="snapshots_main">' +
                '<div class="snapshots_btn mtb10"><button type="button" title="创建快照" class="btn btn-success crete-snapshots btn-sm mr5">创建快照</button></div>' +
                '<div class="divtable" style="height:137px">' +
                '<table class="table table-hover"><thead><tr><th>快照名称</th><th width="145">创建时间</th><th style="text-align: right">操作</th></tr></thead><tbody class="snapshots-tbody"></tbody></table>' +
                '</div>' +
                '</div>' +
                '</div>',
            success: function () {
                render_snapshots_table(config)
                // 创建快照
                $('.crete-snapshots').click(function () {
                    bt_tools.open({
                        title: '创建快照',
                        area: '450px',
                        btn: ['创建', '取消'],
                        content: '<div class="pd15">' +
                            '<div class="alert alert-danger" style="line-height: 20px;">' +
                            '温馨提示：</br>' + help + '</div>' +
                            '<form class="bt-form">' +
                            '<div class="line">' +
                            '<span class="tname">快照名称</span>' +
                            '<div class="info-r">' +
                            '<input class="bt-input-text" type="text" name="snapshots-name" placeholder="请输入快照名称" style="width:290px">' +
                            '</div>' +
                            '</div>' +
                            '</form>' +
                            '</div>',
                        yes: function (layers, index) {
                            var sName = $('input[name=snapshots-name]').val()
                            if (sName == '') return layer.msg('请输入快照名称', { icon: 2 });
                            bt_tools.send(config.is_cvm ? 'tencent/create_disk_snapshots' : 'tencent/create_snapshots', { SnapshotName: sName }, function (res) {
                                if (res.status) {
                                    layer.close(layers)
                                    render_snapshots_table(config)
                                }
                                layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                            }, { plugin: true, load: '创建快照中' });
                        }
                    })
                })
                // 固定表格头部
                if (jQuery.prototype.fixedThead) {
                    $('.snapshots_main .divtable').fixedThead({ resize: false });
                    $('.snapshots_main .divtable').css({ 'overflow': 'hidden' });
                } else {
                    $('.snapshots_main .divtable').css({ 'overflow': 'auto' });
                }
            }
        })
    }


    function render_snapshots_table(config) {
        bt_tools.send(config.is_cvm ? 'tencent/get_disk_snapshots_list' : 'tencent/get_snapshots_list', function (data) {
            var _bhtml = '';
            if (data.SnapshotSet.length > 0) {
                $.each(data.SnapshotSet, function (index, item) {
                    _bhtml += '<tr>' +
                        '<td><span class="snap-hideen" title="' + item.SnapshotName + '">' + item.SnapshotName + '</span></td>' +
                        '<td>' + (!config.is_cvm ? bt.format_data(new Date(item.CreatedTime).getTime()) : item.CreateTime) + '</td>' +
                        '<td style="text-align: right">' +
                        '<a class="btlink" target="_blank" href="https://console.cloud.tencent.com/cvm/snapshot/list">回滚</a>&nbsp;&nbsp;|&nbsp;&nbsp;' +
                        '<a class="btlink snapshots-delete" data-snapshotid="' + item.SnapshotId + '" data-snapshotname="' + item.SnapshotName + '" href="javascript:;">删除</a>' +
                        '</td>' +
                        '</tr>'
                })
            } else {
                _bhtml = '<tr><td colspan="3" style="text-align:center">暂无快照</td></tr>'
            }
            $('.snapshots-tbody').html(_bhtml)
            $('.snapshots-delete').click(function () {
                var _id = $(this).data('snapshotid'), _sName = $(this).data('snapshotname');
                bt.confirm({ title: '提示', msg: '是否删除当前【' + _sName + '】快照，删除后将无法恢复，是否继续？', icon: 1 }, function (index) {
                    bt_tools.send(config.is_cvm ? 'tencent/delete_disk_snapshots' : 'tencent/delete_snapshots', { SnapshotId: _id }, function (res) {
                        if (res.status) render_snapshots_table(config)
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                    }, { plugin: true, load: '删除快照中' });
                })
            })
        }, { plugin: true, load: '获取快照列表中' });
    }

    /**
    * @description 获取流量包列表
    * @param {*} callback 
    */
    function get_request_pack(callback) {
        let loadT = bt.load('正在获取流量包数据，请稍后...');
        bt_tools.send('/plugin?action=a&name=tencent&s=get_request_pack', function (rdata) {
            loadT.close();
            callback && callback(rdata);
        })
    }


    /**
    * @deprecated 流量包视图
    */
    function request_pack() {
        bt_tools.open({
            title: '流量包管理',
            area: ['650px', '350px'],
            btn: false,
            content: '<div class="pd15">' +
                '<div div class="divtable">' +
                '<table class="table table-hover mb0">' +
                '<thead><tr><th>流量包ID</th><th>总流量</th><th>剩余流量</th><th>已使用</th><th>开始时间</th><th>结束时间</th></tr></thead>' +
                '<tbody id="requestList"></tbody>' +
                '</table>' +
                '</div>' +
                '</div>',
            success: function (layero, index) {
                get_request_pack(function (rdata) {
                    var parkList = rdata.InstanceTrafficPackageSet[0].TrafficPackageSet, table = '';
                    for (var i = 0; i < parkList.length; i++) {
                        var item = parkList[i];
                        table += '<tr><td>' + item.TrafficPackageId + '</td><td>' + bt.format_size(item.TrafficPackageTotal) + '</td><td>' + bt.format_size(item.TrafficPackageRemaining) + '</td><td>' + bt.format_size(item.TrafficUsed) + '</td><td>' + bt.format_data(new Date(item.StartTime).getTime()) + '</td><td>' + bt.format_data(new Date(item.EndTime).getTime()) + '</td></tr>'
                    }
                    $('#requestList').html(table)
                })
            }
        })
    }


    var tencent_firewall = {
        firewall_list: [],
        init: false,
        // 获取防火墙规则
        get_firewall_rules: function (callback) {
            var that = this;
            bt_tools.send({
                url: '/plugin?action=a&name=tencent&s=get_firewall_rules',
                verify: false
            }, function (res) {
                if (!Array.isArray(res.FirewallRuleSet)) return false
                $('#firewallBody').attr('data-init', '1')
                that.firewall_list = res.FirewallRuleSet
                if (callback) callback(res)
            })
        },
        // 打开腾讯防火墙视图
        open_tencent_firewall_view: function () {
            var _that = this;
            var loadT = bt_tools.load('获取轻量云防火墙规则')
            bt_tools.open({
                title: '轻量云防火墙规则',
                area: ['800px', '500px'],
                btn: false,
                content: '<div class="firewallRules pd20" id="firewallTable"></div>',
                success: function () {
                    var firewallTable = bt_tools.table({
                        el: '#firewallTable',
                        url: '/plugin?action=a&name=tencent&s=get_firewall_rules',
                        default: "防火墙规则列表为空", //数据为空时的默认提示
                        autoHeight: 'auto',
                        dataFilter: function (res) {
                            loadT.close()
                            if (!Array.isArray(res.FirewallRuleSet)) return { data: [] }
                            return { data: res.FirewallRuleSet }
                        },
                        column: [
                            { fid: 'AppType', title: '应用类型' },
                            { fid: 'CidrBlock', title: '来源' },
                            { fid: 'Protocol', title: '协议' },
                            { fid: 'Port', title: '	端口' },
                            {
                                fid: 'Action', title: '策略',
                                template: function (row, that) {
                                    return row.Action === 'ACCEPT' ? '<span class="btlink">允许</span>' : '<span style="color:red">拒绝</span>'
                                }
                            },
                            {
                                title: '操作', width: 80, type: 'group', align: 'right', group: [{
                                    title: '删除',
                                    template: function (row, that) {
                                        return that.data.length === 1 ? '<span>不可操作</span>' : '删除';
                                    },
                                    event: function (row, index, ev, key, that) {
                                        bt.show_confirm('删除防火墙规则', '删除后可能导致服务无法访问，是否继续？', function () {
                                            delete row.FirewallRuleDescription
                                            bt_tools.send({
                                                url: '/plugin?action=a&name=tencent&s=del_firewall_rules',
                                                data: row,
                                                verify: false
                                            }, function (res) {
                                                if (res.status) {
                                                    that.$delete_table_row(index);
                                                    _that.firewall_list.splice(index, 1)
                                                    $('#firewallBody').attr('data', '4')
                                                    bt.msg(res)
                                                }
                                            })
                                        })
                                    }
                                }]
                            }],
                        success: function (that) {
                            var table = $('#firewallTable .divtable');
                            table.find('thead').css({ 'position': 'relative', 'z-index': '9999' });
                            table.find('table').css({ 'border': 'none' });
                            table.css({ 'border': '1px solid #ddd', 'max-height': '360px' });
                            bt_tools.$fixed_table_thead(table);
                        },
                        tootls: [{ //按钮组
                            type: 'group',
                            positon: ['left', 'top'],
                            list: [{
                                title: '添加规则',
                                active: true,
                                event: function (ev) {
                                    _that.add_firewall_rules({}, function () {
                                        firewallTable.$refresh_table_list()
                                        $('#firewallBody').attr('data', '3')
                                    })
                                }
                            }]
                        }]
                    })
                }
            })
        },
        // 获取面板防火墙的信息
        capture_firewall_port_list: function (callback) {
            tencent_firewall.monitorObserver(function () {
                var tr = $('#firewallBody tbody tr'), array = []
                $.each(tr, function (index, item) {
                    var port = $(item).find('td:eq(1)').text(), data = port.match(/.*\[([0-9-]*)\]/)
                    if (data) array.push({ port: data[1], element: $(item) })
                });
                if (callback) callback(array)
            })
        },
        // 添加防火墙规则
        add_firewall_rules: function (data, callback) {
            if (typeof data != "object") data = {}
            bt_tools.open({
                title: '添加轻量云防火墙规则',
                area: ['540px', '330px'],
                btn: ['添加', '取消'],
                content: {
                    class: 'pd20',
                    formLabelWidth: '120px',
                    form: [{
                        label: '端口',
                        group: {
                            type: 'text',
                            name: 'Port',
                            width: '285px',
                            placeholder: "端口范围1到65535之间，支持端口放行范围80-90",
                            value: data.port || ''
                        }
                    }, {
                        label: '允许访问IP地址',
                        group: {
                            type: 'text',
                            name: 'CidrBlock',
                            width: '285px',
                            placeholder: "默认为空，表示所有来源，支持IP网段，可为空"
                        }
                    }, {
                        label: '备注',
                        group: {
                            type: 'textarea',
                            name: 'ps',
                            value: data.ps || '',
                            style: { 'height': '80px', 'width': '285px' },
                            placeholder: "备注和说明，可为空"
                        }
                    }]
                },
                yes: function (formData, indes, layers) {
                    if (formData.CidrBlock === '') formData.CidrBlock = '0.0.0.0/0'
                    formData.Protocol = 'ALL'
                    formData.ActionType = 'ACCEPT'
                    bt_tools.send({
                        url: '/plugin?action=a&name=tencent&s=add_firewall_rules',
                        data: formData,
                        verify: false
                    }, function (res) {
                        if (res.status) {
                            bt.msg(res)
                            layer.close(indes)
                            setTimeout(function () {
                                window.location.reload()
                            }, 2000)
                        }
                        if (callback) callback(res)
                    })
                }
            })
        },
        // 删除防火墙规则
        del_firewall_rules: function () {

        },
        monitorObserver: function (callback) {
            var targetNode = document.getElementById('firewallBody'), observer = null, delayTime = 0;
            observer = new MutationObserver(function (mutationsList, observer) {
                for (var mutation in mutationsList) {
                    var item = mutationsList[mutation]
                    if (item.type === 'childList' && (item.target.nodeName === 'TR' || item.target.nodeName === 'TD')) return false
                    if (item.type === 'childList' || item.type === 'attributes') {
                        clearTimeout(delayTime)
                        delayTime = setTimeout(function () {
                            if (callback) callback()
                        }, 100);
                    }
                }
            })
            observer.observe(targetNode, { childList: true, attributes: true, subtree: true });
            return observer
        }
    }

    function get_user_info(callback) {
        bt_tools.send({ url: '/ssl?action=GetUserInfo' }, function (res) {
            if (callback) callback(res)
        })
    }


    function init() {
        var pathname = window.location.pathname;
        switch (pathname) {
            case '/':
                reader_tencent_info()
                break;
            case '/site':
                bt_tools.send('/plugin?action=get_soft_find', { sName: 'dnspod' }, function (res) {
                    $('#bt_site_table').on('click', 'button:eq(0)', function (ev) {
                        var interval = setInterval(function () {
                            var add_site_form = $('.bt-form');
                            if (add_site_form.length > 0) {
                                clearInterval(interval);
                                var webname = $('[name="webname"]');
                                webname.next().after('<label class="inlineBlock add_domain_dns"><span class="bt-form-checkbox cursor-pointer mr5"></span><span class="btlink" style="font-weight: 500;">为当前域名添加解析，<span>请确保以上域名已添加至腾讯云DNS解析</span></span></label>')
                                $('.add_domain_dns').click(function () {
                                    let temcatKey = bt.get_storage('local', 'tencent_key') || 0;
                                    if (!parseInt(temcatKey)) {
                                        return tencent_key_view()
                                    }
                                    var that = this;
                                    if (!res.setup) {
                                        layer.msg('未安装腾讯云DNS解析插件，<a href="javascript:;" class="btlink installDnsSoft">点击安装</a>', { icon: 2, closeBtn: 2, time: 0, shade: 0.3 });
                                        $('.installDnsSoft').on('click', function () {
                                            bt.soft.install('dnspod');
                                            var installStatus = setInterval(function () {
                                                bt_tools.send('/plugin?action=get_soft_find', { sName: 'dnspod' }, function (res) {
                                                    if (res.setup) {
                                                        location.reload();
                                                        clearInterval(installStatus)
                                                    }
                                                })
                                            }, 2000)
                                        })
                                        webname.focus();
                                        return false;
                                    }
                                    if (webname.val() == '') {
                                        layer.msg('请先添加域名', { icon: 2 });
                                        webname.focus();
                                        return false;
                                    }
                                    bt.confirm({ title: '提示', msg: '是否为当前域名添加解析,如果当前域名已存在解析记录，将会覆盖当前域名解析记录，是否继续？', icon: 1 }, function (index) {
                                        $(that).find('.bt-form-checkbox').addClass('active');
                                        var arry = webname.val().split('\n'), domain = [];
                                        for (var i = 0; i < arry.length; i++) {
                                            var temps = arry[i].replace(/\r\n/, '').split(':');
                                            if (!bt.check_domain(temps[0])) {
                                                layer.msg('第' + i + '行，[' + temps[0] + ']域名格式错误。');
                                                return false;
                                            }
                                            domain.push(temps[0]);
                                        }
                                        var domains = JSON.stringify(domain);
                                        bt_tools.send('dnspod/create_record_bysite', { domains: domains }, function (res) {
                                            layer.close(index);
                                            var html = '';
                                            for (var i = 0; i < res.success.length; i++) {
                                                html += '<tr><td>' + res.success[i] + '</td><td><span>解析添加成功</span></td></tr>';
                                            }
                                            for (var j in res.error) {
                                                html += '<tr><td>' + j + '</td><td><span>' + res.error[j] + '</span></td></tr>';
                                            }
                                            bt_tools.$batch_success_table({ title: '添加解析域名', th: '域名', html: html });
                                        }, { verify: false, load: '添加解析', plugin: true });
                                    });
                                });
                            }
                        }, 100);
                    });
                });
                break;
            case '/files':
                bt_tools.send('/plugin?action=get_soft_find', { sName: 'cosfs' }, function (res) {
                    if (res.setup) {
                        bt_tools.send('cosfs/get_unmounted_buckets', function (res) {
                            var width = 0, file_nav_view = $('.file_nav_view').width();
                            var interval = setInterval(function () {
                                if ($('.file_disk_list .nav_btn').length > 0) {
                                    $('.file_nav_view .nav_group:not(.hide)').each(function (index, item) {
                                        width += $(this).width();
                                    });
                                    console.log((width + 165 + $('.nav_group.mount_disk_list').width()), file_nav_view)
                                    if ((width + 165 + $('.nav_group.mount_disk_list').width()) > file_nav_view) {
                                        $('.mount_disk_list').addClass('thezoom');
                                        $('.disk_title_group_btn').removeClass('hide');
                                    } else {
                                        $('.mount_disk_list').removeClass('thezoom');
                                        $('.disk_title_group_btn').addClass('hide');
                                    }
                                    clearInterval(interval);
                                }
                            }, 100);
                            var html = '';
                            for (var i = 0; i < res.list.length; i++) {
                                var item = res.list[i], minName = item.Name.split('-');
                                html += '<li data-index="' + i + '"><i class="glyphicon glyphicon-hdd"></i><span>' + minName[0] + '</span><span>挂载</span></li>';
                            }
                            $('.mount_disk_list').before('<div class="nav_group mr5 cosfs_downup_list">\
                          <div class="nav_btn create_file_or_dir">\
                              <span class="nav_btn_title">腾讯云COSFS挂载工具</span><i class="iconfont icon-xiala"></i>\
                              <ul class="nav_down_list">'+ html + '</ul>\
                          </div>\
                      </div>');
                            $('.create_file_or_dir li').click(function () {
                                var index = $(this).data('index'), data = res.list[index],
                                    regs = /([-][^-]+)$/, bucket_name = data['Name'].replace(regs, "");
                                bt_tools.open({
                                    title: '【' + data['Name'] + '】本地挂载',
                                    area: '400px',
                                    btn: ['挂载', '取消'],
                                    content: {
                                        url: '/plugin?action=a&name=cosfs&s=mount_cosfs',
                                        class: 'pd20',
                                        formLabelWidth: '80px',
                                        form: [{
                                            label: '挂载地址',
                                            group: [{
                                                type: 'text',
                                                name: 'path',
                                                width: '215px',
                                                icon: { type: 'glyphicon-folder-open', event: function (ev) { } },
                                                value: '/www/cosfs/' + bucket_name,
                                                placeholder: '请选择文件目录',
                                                verify: function (value, element) {
                                                    if (value == '') {
                                                        bt_tools.$verify_tips(element, '文件目录不能为空！');
                                                        return false;
                                                    }
                                                    return value;
                                                }
                                            }]
                                        }]
                                    },
                                    yes: function (form, indexs, layero) {
                                        this.$submit({ region: data['Location'], bucket_name: data['Name'] }, function (res) {
                                            if (res.status) {
                                                layer.close(indexs);
                                                setTimeout(function () {
                                                    window.location.reload();
                                                }, 2000);
                                            }
                                        })
                                    }
                                })
                            });
                        }, { verify: false, load: false, plugin: true });
                    }
                });
                break;
            case '/firewall':
                get_tencent_info(false, function (res) {
                    if (!res.server_type) {
                        tencent_firewall.get_firewall_rules()
                        tencent_firewall.capture_firewall_port_list(function (list) {
                            var is_exist_num = -1, match_num = 0, firewall = tencent_firewall.firewall_list.slice()
                            $.each(list, function (index, item) {
                                $.each(firewall, function (indexs, items) {
                                    if (item.port === items.Port) {
                                        is_exist_num = indexs;
                                        match_num++;
                                        return false
                                    } else {
                                        is_exist_num = -1;
                                        if ((firewall.length - 1) === indexs) {
                                            var port_td = item.element.find('td:eq(1)')
                                            if (port_td.find('.firewall_prot_release').length != 1) {
                                                port_td.append('&nbsp;&nbsp;<a href="javascript:;" class="btlink firewall_prot_release" data-port="' + item.port + '" data-ps="' + item.element.find('td:eq(4)').text() + '">点击放行，腾讯云轻量云防火墙端口</a>')
                                            }
                                        }
                                    }
                                })
                                if (is_exist_num >= 0) {
                                    firewall.splice(is_exist_num, 1)
                                }
                            })
                        })
                        $('#firewallBody').on('click', '.firewall_prot_release', function () {
                            tencent_firewall.add_firewall_rules($(this).data())
                        })
                        $('.firewall-port-box').find('')
                        $('.firewall-port-box').append('<button class="btn btn-default btn-sm" style="float:right" onclick="tencent_firewall.open_tencent_firewall_view()">轻量云防火墙规则</button>')
                    }
                })
                break;
        }
    }

    if (location.pathname !== '/bind') {
        get_user_info(function (res) {
            if (!res.status) return false
            bt_tools.send({ url: '/plugin?action=a&name=tencent&s=get_config', verify: false }, function (res) {
                if (res === false) {
                    bt.set_storage('local', 'tencent_key', 0)
                    if (bt.get_storage('local', 'tencent') == null) tencent_key_view()
                } else {
                    bt.set_storage('local', 'tencent_key', 1)
                    get_tencent_info()
                }
            })
        })
    }
    init()
}, 1500)

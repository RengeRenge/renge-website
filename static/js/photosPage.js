preventEnterEnable(true, function (e) {
    return true
})

onKeyupEnable(function (e) {
    if ($(':focus').length !== 0) {
        return
    }
    if (e.keyCode === 39 || e.keyCode === 40)
        next_oPic()
    else if (e.keyCode === 37 || e.keyCode === 38)
        last_oPic()
    else if (e.keyCode === 27)
        dismiss_oPic()
})

function show_oPic(e) {

    $(".fullScreen").show()
    // 全屏时禁止背景滚动并隐藏滚动条（内联样式优先级最高，防止被其他规则覆盖）
    $('html,body').addClass('overHidden');
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';

    let thumbUrl = e.getAttribute('name')
    let qUrl = e.id
    let pid = e.parentNode.id
    doLoadPic(thumbUrl, qUrl, pid)
}

function doLoadPic(thumb_url, qUrl, pid) {
    if (that.currentPid === pid) {
        return
    }
    that.currentPid = pid

    // 切换时先隐藏旧图（连同阴影框），避免新图加载完成前残留旧视觉
    $("#display_img").removeClass('img-loaded').addClass('img-switching')
    $("#display_img")[0].src = ''
    $('.weui-loading').show()
    $(".img_text").hide()

    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/preList",
        data: {
            'id': pid,
            'albumId': this.albumId,
            'size': 2
        },
        success: function (result) {
            if (pid !== that.currentPid)
                return
            $('.weui-loading').hide()
            if (result.code !== 1000) {
                alert('获取列表失败')
            } else {
                $(".img_text").show()
                // 新图加载完成后先确保图片已解码（naturalWidth 生效），再淡入显示；
                // 避免解码未完成时 display:block 产生拉伸空框闪现
                $("#display_img").one('load error', function () {
                    var img = this
                    var show = function () {
                        // 快速连续切换时，仅当仍停留在本次目标图片才显示
                        if (pid !== that.currentPid) {
                            return
                        }
                        $(img).removeClass('img-switching').addClass('img-loaded')
                    }
                    if (img.decode) {
                        img.decode().then(show).catch(show)
                    } else {
                        show()
                    }
                })
                $("#display_img")[0].src = qUrl

                RGBaster.colors(thumb_url, {
                    paletteSize: 1,
                    success: function (payload) {
                        if (pid !== that.currentPid) return
                        let rgb = payload.dominant
                        let a = rgb.rbgaTrim().split(',')

                        let grayScale = 0.212671 * a[0] + 0.715160 * a[1] + 0.072169 * a[2]
                        let titleRgb
                        if (grayScale > 126) {
                            $(".fullScreen .bgNoRepeatImage").css('filter', '')
                            $(".fullScreen .close").css('filter', '')
                            titleRgb = 'rgb(0,0,0)'
                            $(".img_text").removeClass('rich_white')
                            $(".img_text").addClass('rich_black')

                            $('.nav span').removeClass('white_class')

                        } else {
                            $(".fullScreen .bgNoRepeatImage").css('filter', 'invert(100%)')
                            $(".fullScreen .close").css('filter', 'invert(100%)')
                            titleRgb = 'rgb(255,255,255)'
                            $(".img_text").removeClass('rich_black')
                            $(".img_text").addClass('rich_white')

                            $('.cs-skin-border > span').addClass('white_class')
                            $('.nav span').addClass('white_class')
                        }
                        $(".fullScreen").css("background-color", rgb);
                        $(".img_text").css("color", titleRgb);
                        $('#display_img_exif').css('color', titleRgb);
                        if (!that.isHome)
                            $("#display_img_privacy").css("color", titleRgb);
                    }
                })

                that.picList = result.data

                let exif_lalo = that.picList['current']['exif_lalo']
                let exif_timestamp = that.picList['current']['exif_timestamp']

                $('#display_img_exif').text('').css('opacity', 0)
                if (exif_lalo) {
                    $.ajax({
                        type: 'GET',
                        dataType: "jsonp",
                        url: "https://api.map.baidu.com/geocoder/v2/",
                        data: {
                            'location': exif_lalo,
                            'output': 'json',
                            'ak': that.bdapi,
                            'pois': 1,
                            'coordtype': 'wgs84ll',
                        },
                        success: function (res) {
                            if (!res.status && that.picList['current']['exif_lalo'] === exif_lalo) {
                                res = res.result
                                exif_timestamp = (new Date(exif_timestamp)).Format(" 拍摄于:yyyy-MM-dd hh:mm:ss")
                                let desc = ' 「' + res.formatted_address + '」 ' + res.sematic_description + exif_timestamp
                                $('#display_img_exif').text(desc)
                                $('#display_img_exif').css('opacity', 1)
                                syncFullscreenLayout()
                            }
                        },
                        error: function (err) {

                        }
                    })    
                } else if (exif_timestamp) {
                    $('#display_img_exif').css('opacity', 1)
                    exif_timestamp = (new Date(exif_timestamp)).Format("拍摄于:yyyy-MM-dd hh:mm:ss")
                    $('#display_img_exif').text(exif_timestamp)
                }

                $('#display_img_title').text(that.picList['current']['title'])
                $('#display_img_desc').text(that.picList['current']['description'])
                let level = that.picList['current']['level']

                if (that.isHome) {
                    let html = '\
                    <select id="pic_privacy" style="min-height: 40px" class="cs-select cs-skin-border">\
                    <option value="0" {0}>所有人可见</option>\
                    <option value="1" {1}>仅好友可见</option>\
                    <option value="2" {2}>仅自己可见</option>\
                    </select>'.format(selectString(0, level), selectString(1, level), selectString(2, level))

                    $('#display_img_privacy')[0].innerHTML = html

                    new SelectFx($('#pic_privacy')[0], {
                        stickyPlaceholder: true,
                        onChange: function (val) {
                            let cLevel = parseInt(val)
                            if (cLevel === level) {
                                return
                            }
                            $.ajax({
                                type: 'POST',
                                dataType: "json",
                                url: "/photo/edit",
                                data: {
                                    'id': pid,
                                    'level': val
                                },
                                success: function (result) {
                                    level = cLevel
                                    if (result.code !== 1000) {
                                        alert('修改失败')
                                    }
                                },
                                error: function () {
                                },
                            })
                        }
                    });
                } else {
                    let displayLevel
                    switch (level) {
                        case 0:
                            displayLevel = '所有人可见'
                            break
                        case 1:
                            displayLevel = '仅好友可见'
                            break
                        case 2:
                            displayLevel = '仅自己可见'
                            break
                    }
                    $('#display_img_privacy').text(displayLevel)
                }

                if (that.picList['pre'].length) {
                    $('.photo-nav-prev').show()
                } else {
                    $('.photo-nav-prev').hide()
                }

                if (that.picList['next'].length) {
                    $('.photo-nav-next').show()
                } else {
                    $('.photo-nav-next').hide()
                }

                syncFullscreenLayout()
            }
        },
        error: function () {
        },
    })
}

function selectString(level, c_level) {
    if (level === c_level) {
        return 'selected="selected"'
    }
    return ''
}

function dismiss_oPic() {
    $(".fullScreen").hide()
    $(".fullScreen").css("background-color", '');
    $('html,body').removeClass('overHidden'); //使网页恢复可滚动
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
    $("#display_img")[0].src = ''
    $("#display_img").removeClass('img-switching img-loaded')
    $(".fullScreen .bgNoRepeatImage").css('filter', '')
    $(".fullScreen .close").css('filter', '')

    $('.cs-skin-border > span').removeClass('white_class')
    $('.cs-skin-border > span').removeClass('black_class')

    $('.nav span').removeClass('white_class')
    $('.nav span').removeClass('black_class')
    that.currentPid = null
}

function next_oPic() {
    if (!that.picList)
        return false
    if (!that.picList['next'].length)
        return false
    let next = that.picList['next'][0]
    doLoadPic(next.url, next.qUrl, next.id)
    return true
}

function last_oPic() {
    if (!that.picList)
        return false
    if (!that.picList['pre'].length)
        return false
    let pre = that.picList['pre'][0]
    doLoadPic(pre.url, pre.qUrl, pre.id)
    return true
}

function onBlurPicInfo(e) {
    e.blur()
    if (!that.currentPid) {
        return
    }

    let resultStr = e.innerText.replace(/[\r\n]/g, "")
    e.innerText = resultStr
    syncFullscreenLayout()

    let data = null
    let key = null
    if (e.id === 'display_img_title') {
        if (resultStr !== that.picList['current']['title']) {
            data = {
                title: resultStr
            }
            key = 'title'
        }
    } else if (e.id === 'display_img_desc') {
        if (resultStr !== that.picList['current']['description']) {
            data = {
                desc: resultStr
            }
            key = 'description'
        }
    }
    if (!data) {
        return
    }
    data['id'] = that.currentPid
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/edit",
        data: data,
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                that.picList['current'][key] = resultStr

                let item = $('#' + data['id'] + key)
                if (item) {
                    item.text(resultStr)
                }
            }
        },
        error: function () {
        },
    })
}

function onBlurTitle(e) {
    let resultStr = e.innerText.replace(/[\r\n]/g, "")
    if (that.recordABTitle === resultStr)
        return
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/edit",
        data: {
            'id': this.albumId,
            'title': resultStr
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                e.innerText = resultStr
                that.recordABTitle = resultStr
            }
        },
        error: function () {
        },
    })
}

function onBlurDesc(e) {
    let resultStr = e.innerText.replace(/[\r\n]/g, "")
    if (that.recordABDesc === resultStr)
        return
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/edit",
        data: {
            'id': that.albumId,
            'desc': resultStr
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                e.innerText = resultStr
                that.recordABDesc = resultStr
            }
        },
        error: function () {
        },
    })
}

function onChangeLevel(val) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/edit",
        data: {
            'id': this.albumId,
            'level': val
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                alert('修改成功')
            }
        },
        error: function () {
        },
    })
}

function coverSet() {
    let cPid = that.currentPid
    if (this.coverId === cPid)
        return
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/edit",
        data: {
            'id': this.albumId,
            'cover': that.currentPid
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                that.coverId = cPid
                alert('修改成功')
            }
        },
        error: function () {
        },
    })
}

function iconSet() {
    let fileId = that.picList['current']['fileId']
    if (that.iconId === '' + fileId)
        return
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/setInfo",
        data: {
            'iconId': fileId,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                alert('修改成功')
            }
        },
        error: function () {
        },
    })
}

function bgSet() {
    let fileId = '' + that.picList['current']['fileId']
    let bgUrl = that.picList['current']['qUrl']
    if (that.bgId === fileId)
        return
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/setInfo",
        data: {
            'bgId': fileId,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败')
            } else {
                that.bgId = fileId
                rgSetBgUrl(bgUrl)
                alert('修改成功👌')
            }
        },
        error: function () {
        },
    })
}

function delPic() {
    if (!confirm('删除此图片？')) {
        return
    }
    let pid = '' + that.picList['current']['id']
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/delete",
        data: {
            'id': pid,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('删除失败')
            } else {
                // 同步从相册网格移除该照片并更新分页
                var vm = that.photosVM;
                if (vm) {
                    vm.list = vm.list.filter(function (item) {
                        return String(item.id) !== pid;
                    });
                    vm.count = Math.max(0, vm.count - 1);
                    if (vm.count > 0 && vm.$refs.pagination) {
                        Pagination.Page($(vm.$refs.pagination), vm.nowPage - 1, vm.count, vm.pageSize);
                    }
                }
                if (next_oPic()) {

                } else if (last_oPic()) {

                } else {
                    alert('没有图片了👋')
                }
            }
        },
        error: function () {
        },
    })
}

function showOriginal() {
    let oUrl = that.picList['current']['oUrl']
    window.open('/photo/original?src=' + oUrl.originalRGSrc())
    // $("#display_img")[0].src = oUrl
}

function pageChange(i) {
    var nextUrl = '?' + 'page=' + (i + 1)
    window.location.href = nextUrl
}

/* ====== 上传照片（file_upload 内置秒传/直传，上传到当前相册） ====== */
function uploadPhotos() {
    if (typeof file_upload !== 'function') {
        alert('上传组件未加载，请刷新页面');
        return;
    }
    var input = document.getElementById('photo-upload-input');
    if (!input) {
        input = document.createElement('input');
        input.type = 'file';
        input.id = 'photo-upload-input';
        input.accept = 'image/*';
        input.multiple = true;
        input.style.display = 'none';
        document.body.appendChild(input);
        input.addEventListener('change', photoUploadChange);
    }
    input.value = '';
    input.click();
}

function photoUploadChange(e) {
    var files = Array.prototype.slice.call(e.target.files);
    if (!files.length) {
        return;
    }
    var btn = document.getElementById('uploadPhotosBtn');
    var btnText = btn ? btn.querySelector('span:last-child') : null;
    var originalText = btnText ? btnText.textContent : '';
    var total = files.length, done = 0, failed = 0, spaceFull = false;

    if (btn) {
        btn.disabled = true;
    }
    if (btnText) {
        btnText.textContent = '上传中 0/' + total;
    }

    function afterOne() {
        if (btnText) {
            btnText.textContent = '上传中 ' + done + '/' + total;
        }
        if (done < total) {
            return;
        }
        if (btn) {
            btn.disabled = false;
        }
        if (btnText) {
            btnText.textContent = originalText;
        }
        if (failed) {
            alert('有 ' + failed + ' 张图片上传失败' + (spaceFull ? '（空间不足）' : ''));
        }
        // 上传完成后刷新当前相册列表
        rgLoadContent(that.rg_contentUrl);
    }

    files.forEach(function (file) {
        file_upload({
            in_album: 1,
            album_id: that.albumId,
            file: file,
            success: function () {
                done++;
                afterOne();
            },
            error: function (err) {
                done++;
                failed++;
                if (err && err.code === 1015) {
                    spaceFull = true;
                }
                afterOne();
            }
        });
    });
}

/* ====== 移动照片到其他相册 ====== */
function movePic() {
    if (!that.currentPid) {
        return;
    }
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/list",
        success: function (result) {
            if (result.code !== 1000) {
                alert('获取相册列表失败');
                return;
            }
            var albums = result.data || [];
            var html = '';
            for (var i = 0; i < albums.length; i++) {
                var a = albums[i];
                var cur = String(a.id) === String(that.albumId);
                html += '<div class="move-album-item' + (cur ? ' move-album-current' : '') + '" data-id="' + a.id + '">'
                    + '<span class="move-album-name">' + (a.title || '未命名相册') + '</span>'
                    + (cur ? '<span class="move-album-tag">当前</span>' : '')
                    + '</div>';
            }
            $('#movePanelList').html(html);
            $('#moveMask').show();
            $('#movePanel').show();
        },
        error: function () {
            alert('获取相册列表失败');
        },
    });
}

function closeMovePanel() {
    $('#movePanel').hide();
    $('#moveMask').hide();
}

/* 同步全屏查看器布局：测量底部信息栏实际高度，为居中图片预留垂直空间
   （预留 = (信息栏高 + 底距 28 + 图片间隙 24) × 2），保证图片与信息栏互不挤压 */
function syncFullscreenLayout() {
    var $panel = $('.fullScreen .display_img_text_wrapper');
    var $fs = $('.fullScreen');
    if (!$panel.length || !$fs.length) {
        return;
    }
    var panelH = $panel.outerHeight() || 88;
    var reserve = (panelH + 28 + 24) * 2;
    $fs.css('--img-reserve', reserve + 'px');
}

$(function () {
    $('.nav span').hover(function () {
        $(this).find('ul').show();
    }, function () {
        $(this).find('ul').hide();
    });

    // 窗口尺寸变化时重新测量信息栏高度，保持图片不挤压信息栏
    $(window).resize(function () {
        if ($('.fullScreen').is(':visible')) {
            syncFullscreenLayout();
        }
    });

    // 移动照片：点击目标相册
    $('#movePanelList').on('click', '.move-album-item', function () {
        var $item = $(this);
        if ($item.hasClass('move-album-current')) {
            closeMovePanel();
            return;
        }
        var pid = that.currentPid;
        var albumId = $item.data('id');
        $.ajax({
            type: 'POST',
            dataType: "json",
            url: "/photo/move",
            data: {
                'id': pid,
                'albumId': albumId
            },
            success: function (result) {
                closeMovePanel();
                if (result.code !== 1000) {
                    alert('移动失败');
                    return;
                }
                // 移动成功后从当前相册移除该照片并刷新查看器/网格
                dismiss_oPic();
                var vm = that.photosVM;
                if (vm) {
                    vm.list = vm.list.filter(function (item) {
                        return String(item.id) !== String(pid);
                    });
                    vm.count = Math.max(0, vm.count - 1);
                    if (vm.count > 0 && vm.$refs.pagination) {
                        Pagination.Page($(vm.$refs.pagination), vm.nowPage - 1, vm.count, vm.pageSize);
                    }
                }
            },
            error: function () {
                closeMovePanel();
                alert('移动失败');
            },
        });
    });
})
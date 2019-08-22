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
    $('html,body').addClass('overHidden'); //使网页不可滚动

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
                        if (!that.isHome)
                            $("#display_img_privacy").css("color", titleRgb);
                    }
                })

                that.picList = result.data

                let exif_lalo = that.picList['current']['exif_lalo']
                let exif_timestamp = that.picList['current']['exif_timestamp']

                $('#display_img_exif').css('opacity', 0)
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
                    $('#last_button').show()
                } else {
                    $('#last_button').hide()
                }

                if (that.picList['next'].length) {
                    $('#next_button').show()
                } else {
                    $('#next_button').hide()
                }
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
    $("#display_img")[0].src = ''
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

$(function () {
    $('.nav span').hover(function () {
        $(this).find('ul').show();
    }, function () {
        $(this).find('ul').hide();
    });
})
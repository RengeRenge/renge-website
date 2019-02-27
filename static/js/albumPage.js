this.manageList = {}

preventEnterEnable(true, function (e) {
    return true
})

function albumOnBlur(e) {
    e.innerText = e.innerText.trim()
}

function goto_album(e) {
    let id = e.parentNode.id
    if (id === 'new_album_temp') {
        return
    }
    if (this.managing) {

        let selected = !this.manageList[id]

        let nodes = e.parentNode
        nodes = nodes.children
        for (let node in nodes) {
            node = nodes[node]
            if (node.className === 'album_select') {
                if (selected) {
                    node.style.backgroundImage = "url('../static/image/select-on.png')"
                } else {
                    node.style.backgroundImage = "url('../static/image/select-off.png')"
                }
                this.manageList[id] = selected
                break
            }
        }
        return
    }
    // var url = '/photo/' + this.userId +'/' + e.id
    // window.open(url)
    window.location.href = '' + id
}

function new_album(e) {
    if (this.managing)
        return

    let existed = $('#new_album_temp')
    if (existed[0]) {
        existed.shake(2, 20, 500);
        return
    }
    let new_album = $('<div id="new_album_temp" class="collectionCell collectionWrap wrapperItemBg" style="margin: 10px;">')

    let text =
        '<div onclick="goto_album(this)" class="bgNoRepeatImage" style="width: 100%;"> </div>\
            <div id="new_title" class="p_title nowrapText rich" contenteditable="true" placeholder="标题" style="margin-top: 0px;" onblur="albumOnBlur(this)"></div>\
            <div id="new_desc" class="p_desc nowrapText rich" contenteditable="true" placeholder="描述" onblur="albumOnBlur(this)"></div>\
            <div class="p_desc nowrapText secondTextColor"><div class="rgButton" onclick="do_new_album(this)">创建</div></div>'
    new_album.html(text)
    $('.collectionView').prepend(new_album)
}

function do_new_album(e) {
    let _that = this
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/photo/album/new",
        data: {
            'title': $('#new_title')[0].innerText,
            'desc': $('#new_desc')[0].innerText,
            'level': 2
        },
        success: function (result) {
            if (result.code != 1000) {
                alert('创建失败')
            } else {
                let album = result.data
                let text =
                    '<div class="album_sxwelect"></div>\
                    <div onclick="goto_album(this)" class="bgNoRepeatImage" style="width: 100%;"> </div>\
                    <div class="p_title nowrapText">{0}</div>\
                    <div class="p_desc nowrapText">{1}</div>\
                    <div class="p_desc nowrapText secondTextColor">{2}</div>'

                let timeStamp = album.timestamp
                let time = (new Date(timeStamp)).Format("yyyy MM dd hh:mm:ss")
                text = text.format(album.title.encodeHtml(), album.desc.encodeHtml(), time)
                $('#new_album_temp').html(text)
                $('#new_album_temp')[0].id = album.ID
                if (_that.managing) {
                    $('.album_select').show()
                }
            }
        },
        error: function () {
        },
    })
}

function manage_album() {
    this.managing = !this.managing
    if (this.managing) {
        $('.add_album').hide()
        $('.album_select').show()
        $("#del_button").show()

        $('#album_page').css('margin-bottom', '80px')
        $("#del_button").css('opacity', '1')
        $("#del_button").animate({bottom: 0}, 100, function () {

        })
    } else {
        $('.add_album').show()
        $('.album_select').hide()
        $("#del_button").animate({bottom: -64}, 100, function () {
        })
        setTimeout(function () {
            $("#del_button").css('opacity', '0')
        }, 100)
        $("#album_page").animate({marginBottom: 0}, 100, function () {
        })
    }
}

function del_albums(e) {
    if (!this.managing)
        return

    let _that = this
    let ids = []
    for (let key in this.manageList) {
        if (this.manageList[key] === true) {
            ids.push(key)
        }
    }

    if (!ids.length)
        return
    if (confirm('确定删除选中的' + ids.length + '个相册吗')) {
        $.ajax({
            type: 'POST',
            dataType: "json",
            url: "/photo/album/del",
            data: {
                'ids': ids
            },
            success: function (result) {
                if (result.code != 1000) {
                    alert('删除失败')
                } else {
                    for (let i in ids) {
                        $('#' + ids[i]).remove()
                    }
                    if (_that.managing)
                        manage_album()
                }
            },
            error: function () {
                alert('删除失败')
            },
        })
    }
}
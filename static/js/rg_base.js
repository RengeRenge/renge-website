that = this
that.isEditing = false

window.onload = function () {
    document.body.onkeypress =
        function (e) {
            if (that.onkeypressCallback) {
                if (!that.onkeypressCallback(e)) {
                    return false
                }
            }
            if (that.preventEnter && event.keyCode === 13) {
                if (that.callback) {
                    if (that.callback(e)) {
                        e.target.blur()
                        return false
                    }
                } else {
                    e.target.blur()
                    return false
                }
                return true
            }
        }

    document.body.onkeyup =
        function (e) {
            if (that.onkeyupCallback) {
                return that.onkeyupCallback(e)
            }
        }
    document.body.onkeydown =
        function (e) {
            if (that.onkeydownCallback) {
                return that.onkeydownCallback(e)
            }
        }
}

/*
@param: callback return true, auto blur
function callback(e) {
    console.log(e.target)
    return true
}
*/
function preventEnterEnable(enable, callback) {
    this.preventEnter = enable
    this.callback = callback
}

function onKeypressEnable(callback) {
    this.onkeypressCallback = callback
}

function onKeyupEnable(callback) {
    this.onkeyupCallback = callback
}

function onKeydownEnable(callback) {
    this.onkeydownCallback = callback
}

function autoTitleEnable(title, desc) {
    this.title = title
    this.desc = desc
    this.autoTitle = true
    preventEnterEnable(true, this.callback)
}

function follow(e) {
    e = $('#' + e.id)
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/follow",
        data: {
            'id': this.userId
        },
        success: function (result) {
            if (result.code == 1000) {
                that.relation = result.data['relation']
                that.re_relation = result.data['re_relation']
                configFollowItem()
            }
        },
        error: function () {

        },
    })
}

$(function () {
    configTitle()
    configFollowItem()
})

function configFollowItem() {
    var item = $('#followItem')
    if (!item)
        return
    item.removeClass('')
    if (this.relation == 0) {
        item.attr('onClick', 'follow(this)')
        item.addClass('boprt02')
        item.html('<em>好友</em>')
    } else if (this.relation == 1) {
        item.attr('onClick', '')
        if (this.re_relation == 1) {
            item.addClass('boprt07')
        } else {
            item.addClass('boprt06')
        }
        item.html('<em>好友</em>')
    } else if (this.relation == 2) {
        e.attr('onClick', '')
        item.addClass('boprt14')
        item.html('<em>已拉黑</em>')
    }
}

function recordName(e) {
    that.isEditing = true
    that.record_name = e.innerText
}

function recordDesc(e) {
    that.isEditing = true
    that.record_desc = e.innerText
}

function editName(e) {
    that.isEditing = false
    var record = that.record_name

    if (record == null || record == e.innerText)
        return

    that.record_name = null
    let resultStr = e.innerText.replace(/[\r\n]/g, "")
    e.innerText = resultStr

    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/editTitle",
        data: {
            'name': resultStr
        },
        success: function (result) {
            if (result.code != 1000) {
                e.innerText = record
            } else {
                e.innerText = resultStr
                that.title = resultStr
                configTitle()
            }
        },
        error: function () {
            e.innerText = record
        },
    })
}

function editDesc(e) {
    that.isEditing = false
    let record = that.record_desc

    if (record == null || record == e.innerText)
        return

    that.record_desc = null
    let resultStr = e.innerText.replace(/[\r\n]/g, "")
    e.innerText = resultStr

    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/editdesc",
        data: {
            'desc': resultStr
        },
        success: function (result) {
            if (result.code != 1000) {
                e.innerText = record
            } else {
                e.innerText = resultStr
                that.desc = resultStr
                configTitle()
            }
        },
        error: function () {
            e.innerText = record
        },
    })
}

function configTitle() {
    if (!that.autoTitle)
        return
    var title
    if (this.title && this.title.length)
        title = this.title + ' ' + this.desc
    else
        title = "My Blog" + ' ' + this.desc
    $("title").html(title)
}

String.prototype.format = function () {
    var values = arguments;
    return this.replace(/\{(\d+)\}/g, function (match, index) {
        if (values.length > index) {
            return values[index];
        } else {
            return ""
        }
    })
}

String.prototype.trim = function () {
    return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
}

String.prototype.rbgaTrim = function () {
    return this.replace('rgba(', '').replace('rgb(', '').replace(')', '');
}

String.prototype.trimRGBAToFull = function (defaultcolor) {
    let item = this.split(',')
    let length = item.length
    let a
    if (length < 3)
        return defaultcolor
    else if (length == 3)
        a = '1'
    else a = item[3]
    return 'rgba({0},{1},{2},{3})'.format(item[0], item[1], item[2], a)
}

String.prototype.getUrlRelativePath = function () {
    var url = this
    var arrUrl = url.split("//");

    var start = arrUrl[1].indexOf("/");
    var relUrl = arrUrl[1].substring(start);//stop省略，截取从start开始到结尾的所有字符

    // if (relUrl.indexOf("?") != -1) {
    //     relUrl = relUrl.split("?")[0];
    // }
    return relUrl;
}

function styleSafeGet(k) {
    if (this[k])
        return this[k]
    if (this.has && this.has(k))
        return this.get(k)
    return ''
}

function rg_getTimezone() {
    let d = -new Date().getTimezoneOffset() / 60
    return d
}

jQuery.fn.shake = function (intShakes /*Amount of shakes*/, intDistance /*Shake distance*/, intDuration /*Time duration*/) {
    this.each(function () {
        var jqNode = $(this);
        jqNode.css({position: 'relative'});
        for (var x = 1; x <= intShakes; x++) {
            jqNode.animate({left: (intDistance * -1)}, (((intDuration / intShakes) / 4)))
                .animate({left: intDistance}, ((intDuration / intShakes) / 2))
                .animate({left: 0}, (((intDuration / intShakes) / 4)));
        }
    });
    return this;
}
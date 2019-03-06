that = this
that.isEditing = false
that.bdapi = 'QU2tzWyb5MoEcgv54sijXzruRKLTy5gL'

function webpload() {
    let WebP = new Image();
    WebP.onload = WebP.onerror = function () {
        if (WebP.height !== 2) {
            let sc = document.createElement('script');
            sc.type = 'text/javascript';
            // sc.async = true;
            let s = document.getElementsByTagName('script')[0];
            sc.src = '/static/js/webpjs-0.0.2.min.js';
            s.parentNode.insertBefore(sc, s);
        }
    };
    WebP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
}

webpload()

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
        title = this.title.decodeHtml() + ' ' + this.desc.decodeHtml()
    else
        title = "My Blog" + ' ' + this.desc
    $("title").text(title)
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

String.prototype.getImageUrlRelativePath = function () {
    if (this.isRGImage()) {
        let arrUrl = this.split("//");
        let start = arrUrl[1].indexOf("/");
        let relUrl = arrUrl[1].substring(start);//stop省略，截取从start开始到结尾的所有字符

        // if (relUrl.indexOf("?") != -1) {
        //     relUrl = relUrl.split("?")[0];
        // }
        return relUrl;
    } else {
        return this;
    }
}

String.prototype.isRGImage = function () {
    let url = this
    let arrUrl = url.split("//");
    if (arrUrl.length === 0)
        return true
    let start = arrUrl[1].indexOf("/");
    let host = arrUrl[1].substr(0, start)
    return document.location.host === host
}

String.prototype.originalRGSrc = function () {
    if (this.isRGImage()) {
        let index = this.lastIndexOf('.')
        let ext = this.substring(index)
        let filename = this.substr(0, index)

        index = filename.lastIndexOf('_')
        if (index >= 0) {
            return filename.substr(0, index) + ext
        }
    }
    return this
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

function show_loading() {
    let h5string = '<i class="weui-loading"></i>'

    let container = document.createElement('div')
    container.className = 'fullScreen'
    container.id = 'LoadingFullScreen'
    container.innerHTML = h5string

    document.body.appendChild(container)
}

function dismiss_loading() {
    document.body.removeChild(document.getElementById('LoadingFullScreen'))
}

that.REGX_HTML_ENCODE = /“|&|’|<|>|[\x00-\x20]|[\x7F-\xFF]|[\u0100-\u2700]/g;
that.REGX_HTML_DECODE = /&\w+;|&#(\d+);/g;
that.HTML_DECODE = {
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
    "&nbsp;": " ",
    "&quot;": "\"",
    "&copy;": ""

    // Add more
};

String.prototype.encodeHtml = function () {
    let s = this
    return s.replace(that.REGX_HTML_ENCODE,
        function ($0) {
            var c = $0.charCodeAt(0), r = ["&#"];
            c = (c == 0x20) ? 0xA0 : c;
            r.push(c);
            r.push(";");
            return r.join("");
        });
};

String.prototype.decodeHtml = function () {
    let s = this
    let HTML_DECODE = that.HTML_DECODE;
    return s.replace(that.REGX_HTML_DECODE,
        function ($0, $1) {
            let c = HTML_DECODE[$0];
            if (c === undefined) {
                // Maybe is Entity Number
                if (!isNaN($1)) {
                    c = String.fromCharCode(($1 === 160) ? 32 : $1);
                } else {
                    c = $0;
                }
            }
            return c;
        });
};

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
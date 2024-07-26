that = this
that.isEditing = false
that.bdapi = 'QU2tzWyb5MoEcgv54sijXzruRKLTy5gL'
that.rg_contentUrl = null

function rgLoadContent(url, need_login=false) {
    that.rg_contentUrl = url
    function handleRes(res) {
        if (that.rg_contentUrl !== url)
            return
        if (res.code !== 1000) {
            return
        }
        let data = res["data"]
        that.auth = data['auth']

        if (need_login) {
            if (!that.auth) {
                document.location.href = '/loginPage'
                return
            }
        }

        let oldStyle = that.style

        that.userId = data['user']['ID']
        that.home = data['home']
        that.relation = data['relation']
        that.re_relation = data['re_relation']
        that.ubg = data['user']['bgImage']
        that.style = data['user']['style']

        that.title = data['user']['title']
        that.desc = data['user']['desc']


        let controlH5 =
        '<div id="topControl" class="boprt a-control" style="top: 20px; opacity: 1;">\
            <ul>\
                <li>\
                    <form>{0}\
                    </form>\
                </li>\
                <li>\
                    <form>{1}\
                    </form>\
                </li>\
            </ul>\
        </div>'

        let a = that.home ? '<a href="/blog/edit" class="boprt09" target="_top"><em>写日志</em></a>':
            that.auth&&that.userId ?
                '<a id="followItem" target="_top"><em></em></a>' :
                ''
        let b = that.home ? '<a href="/user/set" class="boprt05" target="_top"><em>设置</em></a>':
            that.auth ?
                '<a href="/" class="boprt01" target="_top"><em>回家</em></a>':
                '<a href="/" class="boprt01" target="_top"><em>登录</em></a>'
        $('#topControl').remove()
        $(document.body).append($(controlH5.format(a, b)))

        let equal = getJSONLength(oldStyle) === getJSONLength(that.style)
        if (equal) {
            for(let key in oldStyle) {

                let value = oldStyle[key]
                if (typeof (value) === 'function') continue

                if (that.style.hasOwnProperty(key)) {
                    if (that.style[key] !== value) {
                        equal = false
                        break
                    }
                } else {
                    equal = false
                    break;
                }
            }
        }

        that.style.styleSafeGet = styleSafeGet
        if (!equal) {
            applyStyle()
        }

        $('#title').text(that.title)
        $('#desc').text(that.desc)
        configTitle()

        configToolBarItem()
        configFollowItem()
        $("#rg_content").html(data['render'])
    };

    $.ajax({
        type: 'GET',
        dataType: "json",
        url: url,
        data: {'user_id': that.userId, 'needUserInfo':1},
        success: handleRes,
        error: function (e) {

        },
    })
}

function getJSONLength(object) {
    let count = 0;
    for(let key in object) { if (typeof(object[key]) !== 'function') count++;}
    return count;
}

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

function keyboardInit(mWindow=null) {
    if (!mWindow) mWindow = window
    window.document
    let _that = this
    mWindow.onload = function () {
        mWindow.document.body.onkeypress =
            function (e) {
                if (e.target.id === 'pageInput') {return true}
                if (_that.onkeypressCallback) {
                    if (!_that.onkeypressCallback(e)) {
                        return false
                    }
                }
                if (_that.preventEnter && event.keyCode === 13) {
                    if (_that.callback) {
                        if (_that.callback(e)) {
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

        mWindow.document.body.onkeyup =
            function (e) {
                if (_that.onkeyupCallback) {
                    return _that.onkeyupCallback(e)
                }
            }
        mWindow.document.body.onkeydown =
            function (e) {
                if (_that.onkeydownCallback) {
                    return _that.onkeydownCallback(e)
                }
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
            if (result.code === 1000) {
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
    configToolBarItem()
})

function configFollowItem() {
    var item = $('#followItem')
    if (!item)
        return
    item.removeClass('')
    if (this.relation === 0) {
        item.attr('onClick', 'follow(this)')
        item.addClass('boprt02')
        item.html('<em>好友</em>')
    } else if (this.relation === 1) {
        item.attr('onClick', '')
        if (this.re_relation === 1) {
            item.addClass('boprt07')
        } else {
            item.addClass('boprt06')
        }
        item.html('<em>好友</em>')
    } else if (this.relation === 2) {
        e.attr('onClick', '')
        item.addClass('boprt14')
        item.html('<em>已拉黑</em>')
    }
}

function configToolBarItem() {
    let controlH5 = null
    if (that.home) {
        if (!$('.toolBarLogin').length) {
            controlH5 = '<a id="tool-100" class="toolBarItem toolBarLogin" onclick="onChangeToolBar(this)">文件</a>'
            $('.toolBarWrapper').append($(controlH5))
            controlH5 = '<a id="tool-3" class="toolBarItem toolBarLogin" onclick="onChangeLoginToolBar(this)">好友</a>'
            $('.toolBarWrapper').append($(controlH5))
        }
    } else {
        $('.toolBarLogin').remove()
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

    if (record == null || record === e.innerText)
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
            if (result.code !== 1000) {
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

    if (record == null || record === e.innerText)
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
            if (result.code !== 1000) {
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
    let title
    if (this.title && this.title.length)
        title = this.title.decodeHtml() + ' ' + this.desc.decodeHtml()
    else
        title = "My Blog" + ' ' + this.desc
    $("title").text(title)
}

function getContentIdCookie()  {
    if (document.cookie.match(/contentId=([^;]+)(;|$)/)!=null){
        let arr=document.cookie.match(/contentId=([^;]+)(;|$)/); //cookies中不为空，则读取iframe的src
        let contentId = arr[1]
        if (contentId.length)
            return contentId
    }
    return null
}

function setContentIdCookie(contentId)  {
    document.cookie = "contentId={0}".format(contentId)
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
    const parsedUrl = new URL(url, window.location.href);
    return parsedUrl.protocol === window.location.protocol && parsedUrl.hostname === window.location.hostname
}

String.prototype.originalRGSrc = function () {
    if (this.isRGImage()) {
        let url = this
        const parsedUrl = new URL(url, window.location.href)
        const params = new URLSearchParams(parsedUrl.search)
        params.delete('side')
        params.delete('size')
        params.delete('quality')
        parsedUrl.search = params.toString()
        return parsedUrl.toString()
    }
    return this
}

String.prototype.isInvalidEmail = function () {
    if (this.indexOf(' ') >= 0) {
        return true
    }
    let reg = new RegExp("^[a-z0-9]+([._\\-]*[a-z0-9])*@([a-z0-9]+[-a-z0-9]*[a-z0-9]+.){1,63}[a-z0-9]+$"); //正则表达式
    if(!reg.test(this)){
        return true
    }
    return false
}

String.prototype.hasEmojiCharacter = function(){
    let substring = this
    if(substring){
        let reg = new RegExp("[~#^$@%&!?%*]", 'g');
        if (substring.match(reg)) {
            return true;
        }
        for ( let i = 0; i < substring.length; i++) {
            let hs = substring.charCodeAt(i);
            if (0xd800 <= hs && hs <= 0xdbff) {
                if (substring.length > 1) {
                    let ls = substring.charCodeAt(i + 1);
                    let uc = ((hs - 0xd800) * 0x400) + (ls - 0xdc00) + 0x10000;
                    if (0x1d000 <= uc && uc <= 0x1f77f) {
                        return true;
                    }
                }
            } else if (substring.length > 1) {
                let ls = substring.charCodeAt(i + 1);
                if (ls === 0x20e3) {
                    return true;
                }
            } else {
                if (0x2100 <= hs && hs <= 0x27ff) {
                    return true;
                } else if (0x2B05 <= hs && hs <= 0x2b07) {
                    return true;
                } else if (0x2934 <= hs && hs <= 0x2935) {
                    return true;
                } else if (0x3297 <= hs && hs <= 0x3299) {
                    return true;
                } else if (hs === 0xa9 || hs === 0xae || hs === 0x303d || hs === 0x3030
                    || hs === 0x2b55 || hs === 0x2b1c || hs === 0x2b1b
                    || hs === 0x2b50) {
                    return true;
                }
            }
        }
    }
};

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

function rg_privacyDesc(cate) {
    cate = parseInt(cate)
    switch (cate) {
        case 0:
            return '所有人可见'
        case 1:
            return '仅好友可见'
        default:
            return '仅自己可见'
    }
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

function getQueryVariable(variable) {
       let query = window.location.search.substring(1);
       let vars = query.split("&");
       for (let i=0;i<vars.length;i++) {
               let pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}

jQuery.fn.shake = function (intShakes /*Amount of shakes*/, intDistance /*Shake distance*/, intDuration /*Time duration*/) {
    this.each(function () {
        let jqNode = $(this);
        jqNode.css({position: 'relative'});
        for (let x = 1; x <= intShakes; x++) {
            jqNode.animate({left: (intDistance * -1)}, (((intDuration / intShakes) / 4)))
                .animate({left: intDistance}, ((intDuration / intShakes) / 2))
                .animate({left: 0}, (((intDuration / intShakes) / 4)));
        }
    });
    return this;
}

function rg_merge(obj, other) {
    for (const key in other) {
        if (other.hasOwnProperty(key)) {
            obj[key] = other[key]
        }
    }
}

function getZoomFactor() {
    return window.devicePixelRatio
}

String.prototype.my_cover = function ({side, quality, size, sf, applySF, coverIn}) {
    let url = this
    const parsedUrl = new URL(url, window.location.href)
    if (parsedUrl.protocol === window.location.protocol && parsedUrl.hostname === window.location.hostname) {
        const params = new URLSearchParams(parsedUrl.search)
        if (side) { params.set('side', side) }
        if (quality) { params.set('quality', quality) }
        if (size) { params.set('size', size) }
        if (sf) { params.set('sf', sf) }
        if (applySF) { params.set('sf', getZoomFactor()) }
        if (coverIn) { params.set('cover', 1) }
        parsedUrl.search = params.toString()
        return parsedUrl.toString()
    }
    return url
}
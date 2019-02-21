// loadjscssfile("../static/js/rg_base.js", "js")
// loadjscssfile("../static/css/rg_base.css", "css")

var scH
function autoHeight() {
    var h = window.screen.availHeight
    // console.log(h)
    scH = h
    if (isPhoneView()) {
        var vertical = document.documentElement.clientHeight > document.documentElement.clientWidth
        h = vertical ? window.screen.availHeight : window.screen.availWidth;
        var last = $(".hina_bg").css('height');
        if (last != '' + h + 'px') {
            $(".hina_bg").css('height', h);

            let w = vertical ? window.screen.availWidth : window.screen.availHeight;
            $(".hina_bg").css('width', '' + w + 'px');
        }
    }
    var min = h * 0.7
    var last = $(".articleWrapper").css('min-height');
    if (last != '' + min + 'px') {
        $(".articleWrapper").css('min-height', min);
    }

    min = h * 0.5
    last = $(".nothing").css('min-height');
    if (last != '' + min + 'px') {
        $(".nothing").css('min-height', min);
    }
    configMarginBottom()
}

function onSceenHeightChanged(callback) {
    this.sceenHeightCallback = callback
}

function loadjscssfile(filename, filetype) {
    if (window.location.pathname.split('/' >= 2)) {
        filename = '../' + filename
    }
    if (filetype == "js") {
        var fileref = document.createElement('script');
        fileref.setAttribute("type", "text/javascript");
        fileref.setAttribute("src", filename);
    } else if (filetype == "css") {

        var fileref = document.createElement('link');
        fileref.setAttribute("rel", "stylesheet");
        fileref.setAttribute("type", "text/css");
        fileref.setAttribute("href", filename);
    }
    if (typeof fileref != "undefined") {
        document.getElementsByTagName("head")[0].appendChild(fileref);
    }
}

function init() {
    if (!rgSetBgUrl(this.ubg)) {
        return
    }

    if (this.style) {
        this.style.styleSafeGet = styleSafeGet
        if (this.style.mainColor) {
            let color = this.style.mainColor
            if (color && color.length)
                $(".pageTitle").css("color", color)
        }
        if (this.style.marginTop) {
            $(".titleWrapper").css("margin-top", this.style.marginTop + 'px')
        }
    }
    autoHeight()
}

function rgSetBgUrl(url) {
    this.ubg = url

    let body = document.body
    if (!body)
        return false

    let bg = document.getElementById('rg_bgId')
    if (bg) {
        bg.style.backgroundImage = "url('" + url + "')"
        return true
    }

    let first = body.firstChild
    if (first.className == 'hina_bg') {
        return false
    }

    bg = document.createElement('div')
    bg.className = 'hina_bg'
    bg.id = 'rg_bgId'
    if (url) {
        bg.style.backgroundImage = "url('" + this.ubg + "')"
    }
    document.body.insertBefore(bg, first)
    return true
}

function configMarginBottom () {
    let height = $(".titleWrapper").height()
    let bottom = getCurrentTitleMarginBottom(height)
    $(".titleWrapper").css("margin-bottom", '' + bottom + 'px')

    if (this.sceenHeightCallback)
        this.sceenHeightCallback(scH, parseInt(scH - height))
}

function getCurrentTitleMarginBottom (height) {
    if (this.style && this.style.marginBottom) {
        if (this.style.marginBottom == 'onepage') {
            // full screen
            let top = this.style.styleSafeGet('marginTop')
            if (!top.length)
                top = '0'
            return Math.max(0, scH - parseInt(top) - height)
        } else {
            return parseInt(this.style.marginBottom)
        }
    }
}

$(function () {
    init()
    autoHeight()
    $(window).resize(autoHeight);
})

function isPhoneView() {
    if (/Android|webOS|iPhone|iPod|BlackBerry/i.test(navigator.userAgent)) {
        return true
    }
    return false
}
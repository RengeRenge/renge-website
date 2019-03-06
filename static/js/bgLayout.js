// loadjscssfile("../static/js/rg_base.js", "js")
// loadjscssfile("../static/css/rg_base.css", "css")

var scH

function autoHeight() {
    let css = document.getElementById("rg_base");
    let h = window.screen.availHeight

    if (isPhoneView()) {
        let vertical = document.documentElement.clientHeight > document.documentElement.clientWidth
        h = vertical ? window.screen.availHeight : window.screen.availWidth;
        let last = $(".hina_bg").css('height');
        if (last !== '' + h + 'px') {

            editRule(css.sheet, '.hina_bg', 'height:{0}'.format(h + 'px'))

            // $(".hina_bg").css('height', h);

            let w = vertical ? window.screen.availWidth : window.screen.availHeight;
            editRule(css.sheet, '.hina_bg', 'width:{0}'.format(w + 'px'))
            // $(".hina_bg").css('width', '' + w + 'px');
        }
    }
    if (scH !== h) {
        editRule(css.sheet, '.articleWrapper', 'min-height:{0}'.format(h * 0.7 + 'px'))
        editRule(css.sheet, '.nothing', 'min-height: {0}'.format(h * 0.5 + 'px'))
        editRule(css.sheet, '.simditor img', 'max-height: {0}'.format(h * 0.5 + 'px'))
    }
    configMarginBottom()
    scH = h
}

/*cssText 暂时只支持一种属性 'margin-top:80px'*/
function editRule(sheet, selectorText, cssText) {

    let rules = sheet.cssRules;

    if (!rules.length) return;

    for (let i = 0; i < rules.length; i++) {

        let o = rules[i]
        let patt = new RegExp("^" + selectorText + "\\s*{.*?}.*?$");
        if (patt.test(o.cssText)) {
            let ocssText = o.cssText
            ocssText = ocssText.substring(ocssText.indexOf('{') + 1, ocssText.lastIndexOf('}') - 1)

            let styles = ocssText.split(';')
            let splitIndex = cssText.indexOf(':')
            let changeSelector = cssText.substring(0, splitIndex)
            let newCSSText = ''

            let found = false
            for (let j = 0; j < styles.length; j++) {
                if (!styles[j]) {
                } else if (!found && styles[j].indexOf(changeSelector) >= 0) {
                    found = true
                    newCSSText += "{0}:{1};".format(changeSelector, cssText.substring(splitIndex + 1))
                } else {
                    newCSSText += "{0};".format(styles[j])
                }
            }
            if (!found) {
                newCSSText += "{0}:{1};".format(changeSelector, cssText.substring(splitIndex + 1))
            }
            deleteRule(sheet, i);
            insertRule(sheet, selectorText, newCSSText, i);
        }
    }
}

function modifyRule(sheet, selectorText, cssText) {

    let rules = sheet.cssRules;

    if (!rules.length) return;

    for (let i = 0; i < rules.length; i++) {

        let o = rules[i]
        let patt = new RegExp("^" + selectorText + "\\s*{.*?}.*?$");
        if (patt.test(o.cssText)) {
            deleteRule(sheet, i);
            insertRule(sheet, selectorText, cssText, i);
        }
    }
}

function insertRule(sheet, selectorText, cssText, position) {
    if (sheet.insertRule) {
        sheet.insertRule(selectorText + "{" + cssText + "}", position);
    } else if (sheet.addRule) {
        sheet.addRule(selectorText, cssText, poistion);
    }
}

function deleteRule(sheet, index) {
    if (sheet.deleteRule) {
        sheet.deleteRule(index);
    } else if (sheet.removeRule) {
        sheet.removeRule(index);
    }
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
    let css = document.getElementById("rg_base")

    if (this.style) {
        this.style.styleSafeGet = styleSafeGet

        let cssText
        if (this.style.mainColor) {
            let color = this.style.mainColor
            if (color && color.length) {
                cssText = "color:{0}".format(color)
                editRule(css.sheet, '.pageTitle', cssText)
            }
        }
        if (this.style.marginTop) {
            cssText = "margin-top:{0}".format(this.style.marginTop + 'px')
            editRule(css.sheet, '.titleWrapper', cssText)
            // $(".titleWrapper").css("margin-top", this.style.marginTop + 'px')
        }
        autoHeight()
    }
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
    if (first.className === 'hina_bg') {
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

function configMarginBottom() {
    let css = document.getElementById("rg_base");
    let height = $(".titleWrapper").height()
    let bottom = getCurrentTitleMarginBottom(height)
    editRule(css.sheet, '.titleWrapper', 'margin-bottom:{0}'.format(bottom + 'px'))
    // $(".titleWrapper").css("margin-bottom", '' + bottom + 'px')

    if (this.sceenHeightCallback)
        this.sceenHeightCallback(scH, parseInt(scH - height))
}

function getCurrentTitleMarginBottom(height) {
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

init()

$(function () {
    if (!rgSetBgUrl(that.ubg)) {
        // return
    }
    autoHeight()
    $(window).resize(autoHeight);
})

function isPhoneView() {
    if (/Android|webOS|iPhone|iPod|BlackBerry/i.test(navigator.userAgent)) {
        return true
    }
    return false
}
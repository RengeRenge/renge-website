function bindBox(id, backgroundClass, tip, autoTitleCallback, callback) {
    let box = document.querySelector('#' + id)
    configOriginalButton(box)

//鼠标拖拽进入该区域
    box.addEventListener('dragenter', function () {
        if (!autoTitleCallback())
            return
        box.innerHTML = '松开鼠标'     //区域内样式变化
    }, false)

//鼠标拖拽离开该区域
    box.addEventListener('dragleave', function () {
        if (!autoTitleCallback())
            return
        configOriginalButton(box)
        // box.innerHTML = '请将图片拖至此区域'      //区域内变回原来样式
    }, false)

//只要鼠标拖拽悬停在该区域就会触发
    box.addEventListener('dragover', function (e) {
        e.preventDefault()     //注意，如果dragover不阻止默认事件，drop事件就不会触发
        if (!autoTitleCallback())
            return
    }, false)

//鼠标拖拽释放
    box.addEventListener('drop', function (e) {
        e.preventDefault()     //浏览器默认会打开该文件，因此停掉该默认事件

        let files = e.dataTransfer.files
        let file = files[0] //获取file对象
        loadFile(e, file)

    }, false)

    function configOriginalButton(box) {
        let uuid = guid()
        if (autoTitleCallback()) {
            var temp = tip
            if (!temp || !temp.length) {
                temp = '点击或拖拽图片到此处'
            }
            box.innerHTML = '<p class="fileInputP vm">' + temp + '<input type="file" class="fileInput" id="' + uuid + '"></p>'
        } else
            box.innerHTML = '<p class="fileInputP vm" style="height:100%;width:100%"><input type="file" class="fileInput" id="' + uuid + '"></p>'

        let input = document.getElementById(uuid)

        if (typeof FileReader === "undefined") {
            if (!autoTitleCallback())
                return
            box.innerHTML = "抱歉，你的浏览器不支持 FileReader"
            input.setAttribute('disabled', 'disabled')
        } else {
            input.addEventListener('change', readFile, false)
        }

        function readFile(e) {
            let file = e.currentTarget.files[0]
            loadFile(e, file)
        }
    }

    function loadFile(e, file) {
        //判断file的类型是不是图片类型。
        if (!/image\/\w+/.test(file.type)) {
            alert("请选择图片类型的文件")
            return false
        }

        let reader = new FileReader()
        reader.readAsDataURL(file)
        reader.onload = function (e) {
            $('.' + backgroundClass).css('background-image', "url('" + e.target.result + "')")
            if (autoTitleCallback())
                box.innerHTML = ''
            configOriginalButton(box)

            if (callback)
                callback(e, file)
        }
    }

    //用于生成uuid
    function S4() {
        return (((1 + Math.random()) * 0x10000) | 0).toString(16).substring(1);
    }

    function guid() {
        return (S4() + S4() + "-" + S4() + "-" + S4() + "-" + S4() + "-" + S4() + S4() + S4());
    }
}


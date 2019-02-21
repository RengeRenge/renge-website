groupSelf = this
groupSelf.groupData = null
groupSelf.showGroup = false

groupSelf.customGroup = null
groupSelf.selectCallBack = null
groupSelf.submitArtGroupId = null

function initGroupModal(defaultId, triggerDomId, customGroup, selectCallBack) {

    let h5string =
        '    <i class="weui-loading"></i>\n' +
        '\n' +
        '    <img src="/static/image/add_group.png" class="toolIcon toolIconPoint RGTransition disblur" id="addGroupIcon" onclick="addGroup()" style="right: 170px">\n' +
        '    <img src="/static/image/rename.png" class="toolIcon toolIconPoint RGTransition disblur" id="renameIcon" onclick="rename()" style="right: 120px">\n' +
        '    <img src="/static/image/manager_order.png" class="toolIcon toolIconPoint RGTransition disblur" id="order_button" onclick="editOrder()">\n' +
        '    <img src="/static/image/close.png" class="close" onclick="hideGroup()">\n' +
        '\n' +
        '    <div id="groupWrapper">\n' +
        '\n' +
        '    </div>\n' +
        '\n' +
        '    <div id="addGroupModal" class="fullScreen" style="display: none">\n' +
        '        <div class="modal-wrapper">\n' +
        '        <div class="modal">\n' +
        '            <div class="modal-header">\n' +
        '                <!--<i class="modal-header-close iconfont icon-ic_close"></i>-->\n' +
        '                <img onclick="hideAddGroupModal()" class="modal-header-close" src="/static/image/close.png" style="width: 15px; height: 15px;">\n' +
        '                <div class="modal-title">\n' +
        '                    新建分组\n' +
        '                </div>\n' +
        '            </div>\n' +
        '            <div class="modal-body">\n' +
        '                <div class="be-input be-input--append">\n' +
        '                    <input type="input" placeholder="分组名称" class="be-input_inner" id="addGroupInput">\n' +
        '                </div>\n' +
        '                <div class="be-switch-container">\n' +
        '                    <input type="checkbox" checked="checked" id="groupAddCheck">\n' +
        '                    <label class="be-switch-label" for="groupAddCheck">\n' +
        '                        置顶\n' +
        '                    </label>\n' +
        '                </div>\n' +
        '            </div>\n' +
        '            <div class="modal-footer">\n' +
        '                <div style="display: inline-block; width: 50%">\n' +
        '                    <div class="rgButton" onclick="doAddGroup(this)">\n' +
        '                        确定\n' +
        '                    </div>\n' +
        '                </div>\n' +
        '            </div>\n' +
        '        </div>\n' +
        '    </div>\n' +
        '    </div>'

    let container = document.createElement('div')
    container.className = 'fullScreen'
    container.id = 'GroupFullScreen'
    container.style.display = 'none'
    container.innerHTML = h5string

    document.body.appendChild(container)

    groupSelf.selectCallBack = selectCallBack
    groupSelf.submitArtGroupId = defaultId
    groupSelf.customGroup = customGroup

    $('#'+triggerDomId).click(loadGroup)
}

function loadGroup() {
    groupSelf.showGroup = true
    $('html,body').addClass('overHidden'); //使网页不可滚动
    $('.boprt').addClass('blur')
    $('.hina_bg').removeClass('disblur')
    $('.hina_bg').addClass('blur')
    // $('.hina_bg').css('transform', 'scale(1.01)')
    $('.page_wrapper').addClass('blur')
    $('#GroupFullScreen').show()
    $('.weui-loading').show()
    $.ajax({
        type: 'GET',
        dataType: "json",
        url: "/blog/group/list",
        // data: data,
        success: function (result) {
            if (!groupSelf.showGroup)
                return
            if (result.code !== 1000) {
                alert('加载失败')
                groupSelf.groupData = null
            } else {
                $('.weui-loading').hide()
                groupSelf.groupData = result.data
                let h5str = '<img id="groupDeleteIcon" src="/static/image/delete.png" class="toolIcon" style="display: none; margin-right: 10%;margin-top:10px">'
                if (groupSelf.customGroup) {
                    h5str += '<div name="{1}" class="groupItem RGTransition nowrapText staticGroup" onclick="onGroupClick(this)">{0}</div>'.format(groupSelf.customGroup, '')
                }
                h5str += '<div id="defaultGroup" name="{1}" class="groupItem RGTransition nowrapText staticGroup" onclick="onGroupClick(this)">{0}</div>'.format('默认分类', -1)
                for (let index in result.data) {
                    let group = result.data[index]
                    h5str += '<div name="{1}" class="groupItem RGTransition nowrapText" oninput="onGroupInput(this)" onclick="onGroupClick(this)" onblur="onGroupItemBlur(this)">{0}</div>'.format(group.name, group.id)
                }
                $('#groupWrapper').html(h5str)

                setTimeout(function () {
                    $('.groupItem').css('opacity', '1')
                }, 1)
            }
        },
        error: function (e) {
            alert(e.statusText)
            groupSelf.groupData = null
        },
    })
}

function hideGroup() {
    groupSelf.showGroup = false
    $('html,body').removeClass('overHidden'); //使网页恢复可滚动
    $('.boprt').removeClass('blur')
    $('.hina_bg').removeClass('blur')
    $('.hina_bg').addClass('disblur')
    $('.hina_bg').css('transform', '')
    $('.page_wrapper').removeClass('blur')
    $('#GroupFullScreen').hide()
    $('#groupWrapper').html('')
    endDrag()
    endRename()
    hideAddGroupModal()
    groupSelf.groupData = null
}

function addGroup() {
    if (isEditOrder)
        return
    if (isRename)
        return
    if (isAddGroup) {
        hideAddGroupModal()
    } else {
        showAddGroupModal()
    }
}

function showAddGroupModal() {
    isAddGroup = true
    $('#addGroupModal').show()
}

function hideAddGroupModal() {
    isAddGroup = false
    $('#addGroupModal').hide()
    $('#addGroupInput')[0].value = null
}

function doAddGroup(e) {
    let name = $('#addGroupInput')[0].value.trim()
    if (!name) {
        alert('名称不能为空')
        return
    }

    let checked = $('#groupAddCheck')[0].checked
    let order = 0
    let before = false
    if (checked && groupSelf.groupData && groupSelf.groupData.length) {
        order = groupSelf.groupData[0].order + 1
        before = true
    }

    $.ajax({
        type: 'POST',
        url: "/blog/group/new",
        data: {
            name: name,
            order: order
        },
        success: function (result) {
            if (!groupSelf.showGroup)
                return
            if (result.code !== 1000) {
                if (result.code === 1005)
                    alert('请输入名称')
                else
                    alert('新建失败')
            } else {

                hideAddGroupModal()

                let newId = result.data.id
                let user_id = result.data.user_id
                let newGroupItem = {
                    id: newId,
                    name: name,
                    order: order,
                    user_id: user_id
                }
                let groupItemH5 = '<div name="{1}" class="groupItem RGTransition nowrapText" oninput="onGroupInput(this)" onclick="onGroupClick(this)" onblur="onGroupItemBlur(this)">{0}</div>'.format(name, newId)
                if (before) {
                    groupSelf.groupData.splice(0, 0, newGroupItem)
                    $('#defaultGroup').after(groupItemH5)
                } else {
                    groupSelf.groupData.push(newGroupItem)
                    $('#groupWrapper').append(groupItemH5)

                    let scrollHeight = $('#groupWrapper').prop("scrollHeight");
                    $('#groupWrapper').animate({scrollTop: scrollHeight}, 300);
                }
                setTimeout(function () {
                    $('.groupItem').css('opacity', '1')
                }, 500)
            }
        },
        error: function (e) {
            alert(e.statusText)
        },
    })
}

let isEditOrder = false
let isRename = false
let isAddGroup = false

function rename() {
    if (isEditOrder)
        return
    if (isRename) {
        endRename()
    } else {
        startRename()
    }
}

groupSelf.flashTimer = null

function startRename() {
    isRename = true
    let source = document.querySelectorAll('.groupItem')
    for (let i = 0; i < source.length; i++) {
        if (source[i].className.indexOf('staticGroup') >= 0) {
            continue
        }
        source[i].setAttribute("contenteditable", "true");
        $(source[i]).addClass("rich groupItemBorder")
        $(source[i]).removeClass("RGTransition")
    }

    clearInterval(groupSelf.flashTimer)

    let i = 0

    function flash() {
        $('#renameIcon')[0].style.opacity = i++ % 2 ? 1 : 0
        i = i % 2
    }

    groupSelf.flashTimer = setInterval(flash, 500)
    flash()
}

function endRename() {
    isRename = false
    clearInterval(groupSelf.flashTimer)
    $('#renameIcon')[0].style.opacity = 1

    let source = document.querySelectorAll('.groupItem')
    for (let i = 0; i < source.length; i++) {
        source[i].removeAttribute("contenteditable")
        $(source[i]).removeClass("rich groupItemBorder")
        $(source[i]).addClass("RGTransition")
    }
}

preventEnterEnable(true, function (e) {
    if (e.target.className.indexOf('groupItem') !== -1) {
        return true
    }
    return false
})

function onGroupInput(e) {
    if (event.inputType === 'insertFromPaste') {
        e.innerHTML = e.innerText
    }
}

function onGroupClick(e) {
    if (isRename || isEditOrder) {
        event.preventDefault()
        return
    }
    groupSelf.submitArtGroupId = e.attributes.name.value
    let name = e.innerText.trim()
    hideGroup()
    groupSelf.selectCallBack && groupSelf.selectCallBack(groupSelf.submitArtGroupId, name)
}

function onGroupItemBlur(e) {

    let id = parseInt(e.attributes.name.value)
    let name = e.innerHTML.trim()

    let citem = null
    for (let i = 0; i < groupSelf.groupData.length; i++) {
        let item = groupSelf.groupData[i]
        if (item.id === id) {
            citem = item
            break
        }
    }

    if (citem.name === name)
        return

    $.ajax({
        type: 'POST',
        url: "/blog/group/rename",
        data: {
            id: id,
            name: name,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('重命名失败🙅‍♂️')
            } else {
                if (groupSelf.submitArtGroupId && parseInt(groupSelf.submitArtGroupId) === id)
                    groupSelf.selectCallBack(groupSelf.submitArtGroupId, name)
                if (citem)
                    citem.name = name
            }
        },
        error: function (e) {
            alert(e.statusText)
        },
    })
}

function editOrder() {
    if (isRename)
        return
    if (isEditOrder) {
        submitOrders(function (flag) {
            if (flag)
                endDrag()
        })
    } else {
        configDrag()
    }
}

groupSelf.source = null
groupSelf.recycle = null
groupSelf.dragElement = null
groupSelf.nextDragElement = null
groupSelf.changeElement = null
groupSelf.lock = null

function configDrag() {
    isEditOrder = true
    $('.groupItem').css('width', '90%')
    $('.groupItem').css('margin', '0px 0px')
    $('.groupItem').css('padding', '10px 0px')
    $('#order_button')[0].src = '/static/image/save.png'

    clearInterval(groupSelf.flashTimer)

    var i = 0

    function flash() {
        $('#order_button')[0].style.opacity = i++ % 2 ? 1 : 0
        i = i % 2
    }

    groupSelf.flashTimer = setInterval(flash, 500)
    flash()

    groupSelf.groupDeleteIds = []
    var iosDragDropShim = {enableEnterLeave: true}                // 兼容移动端
    groupSelf.source = document.querySelectorAll('.groupItem')
    groupSelf.recycle = document.getElementById('groupDeleteIcon')
    groupSelf.dragElement = null                                         // 用于存放拖动元素
    groupSelf.nextDragElement = null
    groupSelf.changeElement = null
    groupSelf.lock = true                                               // 最后元素拖放拖放时会进入enter和leave的循环，用来锁住

    groupSelf.recycle.style.display = ''

    for (let i = 0; i < source.length; i++) {
        if (source[i].className.indexOf('staticGroup') >= 0) {
            continue
        }
        source[i].draggable = 'true'
        source[i].addEventListener('dragstart', groupDragstart, false);

        source[i].addEventListener('dragend', groupDragEnd, false)

        source[i].addEventListener('dragenter', groupDragEnter, false)

        source[i].addEventListener('dragleave', groupDragLeave, false)
    }

    groupSelf.recycle.addEventListener('drop', recycleDrop, false)

    document.ondragover = function (e) {
        e.preventDefault();
    }          // 必须设置dragover阻止默认事件
    document.ondrop = function (e) {
        e.preventDefault();
    }
}

function groupDragstart() {
    groupSelf.dragElement = this                                     // 用于存放拖动元素
    groupSelf.nextDragElement = groupSelf.dragElement.nextElementSibling
    if (groupSelf.nextDragElement && groupSelf.nextDragElement.className.indexOf('groupItem'))
        groupSelf.nextDragElement = null

    $(this).removeClass('RGTransition')
    this.style.backgroundColor = '#d0d0d0';                 // 设置拖动元素的背景
    // recycle.style.transform = 'scale(1.005);-ms-transform: scale(1.005);-moz-transform: scale(1.005);-webkit-transform: scale(1.005);-o-transform: scale(1.005);'
    groupSelf.recycle.style.transform = 'scale(1.205)'
    groupSelf.recycle.style.webkitTransform = 'scale(1.205)'
}

function groupDragEnd(ev) {
    ev.target.style.backgroundColor = '';               // 拖放结束还原拖动元素的背景
    groupSelf.recycle.style.transform = ''
    groupSelf.recycle.style.webkitTransform = ''
    $(ev.target).addClass('RGTransition')
    ev.preventDefault()

    if (!changeElement)
        return

    let id1 = parseInt(groupSelf.dragElement.attributes.name.value)
    let id2 = parseInt(groupSelf.changeElement.attributes.name.value)
    if (id1 === id2) return

    // delete
    let index1 = indexOfGroupId(id1)
    let dragItem = groupSelf.groupData[index1]
    groupSelf.groupData.splice(index1, 1)

    // insert
    if (!lock) {
        groupSelf.groupData.push(dragItem)
        dragItem.order = 0 // 修改order，触发请求（顺序不正确）
    } else {
        let index2 = indexOfGroupId(id2)
        groupSelf.groupData.splice(index2, 0, dragItem)
        dragItem.order = groupSelf.groupData.length - index2 // 修改order，触发请求（顺序不正确）
    }
}

function groupDragEnter(ev) {
    if (groupSelf.dragElement !== this) {
        groupSelf.changeElement = this.previousElementSibling
        if (!groupSelf.changeElement || groupSelf.changeElement.className.indexOf('groupItem') < 0)
            groupSelf.changeElement = this
        else
            groupSelf.changeElement = this
        this.parentNode.insertBefore(groupSelf.dragElement, this);     // 把拖动元素添加到当前元素的前面
    }
}

function groupDragLeave(ev) {
    if (groupSelf.dragElement !== this) {
        if (lock && (this === this.parentNode.lastElementChild || this === this.parentNode.lastChild)) {    // 当前元素时最后一个元素
            this.parentNode.appendChild(dragElement);       // 把拖动元素添加最后面
            groupSelf.lock = false;
        } else {
            groupSelf.lock = true;
        }
    }
}

function recycleDrop() {
    let id = parseInt(groupSelf.dragElement.attributes.name.value)
    let index = indexOfGroupId(id)
    if (index > -1) {

        this.parentNode.insertBefore(groupSelf.dragElement, groupSelf.nextDragElement)

        setTimeout(function () {
            if (confirm('是否要删除' + groupSelf.dragElement.innerText)) {
                $.ajax({
                    type: 'POST',
                    url: "/blog/group/delete",
                    data: {
                        id: id,
                    },
                    success: function (result) {
                        if (result.code !== 1000) {
                            alert('删除失败️')
                        } else {
                            let index = indexOfGroupId(id)
                            groupSelf.groupData.splice(index, 1)
                            groupSelf.dragElement.parentNode.removeChild(groupSelf.dragElement);
                        }
                    },
                    error: function (e) {
                        alert(e.statusText)
                    },
                })
            }
        }, 300)
    }
}

function endDrag() {
    isEditOrder = false
    $('.groupItem').css('width', '')
    $('.groupItem').css('margin', '')
    $('.groupItem').css('padding', '')
    $('#order_button')[0].src = '/static/image/manager_order.png'

    clearInterval(groupSelf.flashTimer)
    $('#order_button')[0].style.opacity = 1

    groupSelf.groupDeleteIds = null
    let source = document.querySelectorAll('.groupItem'),
        recycle = document.getElementById('groupDeleteIcon')
    if (recycle) {
        recycle.style.display = 'none'
        recycle.removeEventListener('drop', recycleDrop)
    }
    for (let i = 0; i < source.length; i++) {
        if (source[i].className.indexOf('staticGroup') >= 0) {
            continue
        }
        source[i].draggable = ''
        source[i].removeEventListener('dragstart', groupDragstart)
        source[i].removeEventListener('dragend', groupDragEnd)
        source[i].removeEventListener('dragenter', groupDragEnter)
        source[i].removeEventListener('dragleave', groupDragLeave)
    }
}

function indexOfGroupId(id) {
    for (let i = 0; i < groupSelf.groupData.length; i++) {
        let item = groupSelf.groupData[i]
        if (id === item.id)
            return i
    }
    return -1
}

function submitOrders(callback) {
    if (!groupSelf.groupData || !groupSelf.groupData.length) {
        callback(true)
        return
    }
    let ids = []
    let orders = []
    let allEqual = true
    let length = groupSelf.groupData.length
    for (let i = 0; i < length; i++) {
        let item = groupSelf.groupData[i]
        ids.push(item.id)
        let order = length - 1 - i
        orders.push(order)
        if (item.order !== order) {
            allEqual = false
        }
    }
    if (allEqual)
        callback(true)
    $.ajax({
        type: 'POST',
        url: "/blog/group/editOrder",
        data: {
            ids: ids,
            orders: orders,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('保存排序失败️')
                callback(false)
            } else {
                callback(true)
            }
        },
        error: function (e) {
            alert(e.statusText)
            callback(false)
        },
    })
}
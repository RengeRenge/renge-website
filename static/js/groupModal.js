let groupSelf = {}

function groupSelfInit() {
    groupSelf = {}
    groupSelf.groupData = null
    groupSelf.showGroup = false
    groupSelf.DOM = null

    groupSelf.customGroup = null
    groupSelf.groupSelectCallBack = null
    groupSelf.groupChangeCallBack = null
    groupSelf.modal_selected_groupId = null
}


/*
    groupSelectCallBack(groupId, name, level);
    customGroup 回调时 groupId 为空字符串 level 为 0;
    默认分类 id 为 -1 level 为 0;

    groupChangeCallBack(group) 服务器返回的结构
*/
function initGroupModal(defaultId, triggerDomId, customGroup, showTool, groupSelectCallBack, groupChangeCallBack) {

    groupSelfInit()

    let toolh5 =
        '<img src="/static/image/add_group.png" class="toolIcon toolIconPoint RGTransition disblur" id="addGroupIcon" onclick="addGroup()" style="right: 170px">\n' +
        '<img src="/static/image/rename.png" class="toolIcon toolIconPoint RGTransition disblur" id="renameIcon" onclick="editGroup()" style="right: 120px">\n' +
        '<img src="/static/image/manager_order.png" class="toolIcon toolIconPoint RGTransition disblur" id="order_button" onclick="editOrder()">\n'
    let h5string =
        '    <i class="weui-loading"></i>\n' +
        '\n' +
        (showTool ? toolh5 : '') +
        '    <img src="/static/image/close.png" class="close" onclick="hideGroup()">\n' +
        '\n' +
        '    <div id="groupWrapper">\n' +
        '\n' +
        '    </div>'

    let container = document.createElement('div')
    container.className = 'fullScreen'
    container.id = 'GroupFullScreen'
    container.style.display = 'none'
    container.innerHTML = h5string
    groupSelf.DOM = container

    groupSelf.groupSelectCallBack = groupSelectCallBack
    groupSelf.groupChangeCallBack = groupChangeCallBack
    groupSelf.modal_selected_groupId = defaultId
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

    document.body.appendChild(groupSelf.DOM)

    $('#GroupFullScreen').show()
    $('.weui-loading').show()
    $.ajax({
        type: 'GET',
        dataType: "json",
        url: "/blog/group/list",
        data: {
            userId: that.userId
        },
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
                for (let group of result.data) {
                    h5str += groupItemH5String(group)
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

function groupItemH5String (group) {
    return '<div name="{1}" class="groupItem RGTransition nowrapText" onclick="onGroupClick(this)" style="padding-left: 4px"><div id="groupItemName-{1}" style="display: inline-block">{0}</div><i class="fa fa-edit editIcon" style="margin-left: 4px; opacity: 0"></i></div>'.format(group.name.encodeHtml(), group.id)
}

let isEditOrder = false
let isEditGroup = false
let isAddGroup = false

function hideGroup() {
    groupSelf.showGroup = false
    $('html,body').removeClass('overHidden'); //使网页恢复可滚动
    $('.boprt').removeClass('blur')
    $('.hina_bg').removeClass('blur')
    $('.hina_bg').addClass('disblur')
    $('.hina_bg').css('transform', '')
    $('.page_wrapper').removeClass('blur')

    $('#GroupFullScreen').hide()

    endDrag()
    endEditGroup()
    dismissEditGroupModal()
    $('#groupWrapper').html('')
    groupSelf.groupData = null
    document.body.removeChild(groupSelf.DOM)
}

function addGroup() {
    if (isEditOrder)
        return
    if (isEditGroup)
        return
    if (isAddGroup) {
        dismissEditGroupModal()
    } else {
        showEditGroupModal(null)
    }
}

function editGroup() {
    if (isEditOrder)
        return
    if (isEditGroup) {
        endEditGroup()
    } else {
        startEditGroup()
    }
}

groupSelf.flashTimer = null

function startEditGroup() {
    isEditGroup = true
    let source = document.querySelectorAll('.groupItem')
    for (let i = 0; i < source.length; i++) {
        if (source[i].className.indexOf('staticGroup') >= 0) {
            continue
        }
        // source[i].setAttribute("contenteditable", "true");
        // $(source[i]).addClass("rich groupItemBorder");
        $(source[i]).removeClass("RGTransition")
    }
    $('.editIcon').css('opacity', 1)

    clearInterval(groupSelf.flashTimer)

    let i = 0

    function flash() {
        $('#renameIcon')[0].style.opacity = (i++ % 2) ? 1 : 0
        i = i % 2
    }

    groupSelf.flashTimer = setInterval(flash, 500)
    flash()
}

function endEditGroup() {
    isEditGroup = false
    if (that.relation >= 0) {
        return
    }
    $('.editIcon').css('opacity', 0)
    clearInterval(groupSelf.flashTimer)
    $('#renameIcon')[0].style.opacity = 1

    let source = document.querySelectorAll('.groupItem')
    for (let i = 0; i < source.length; i++) {
        // source[i].removeAttribute("contenteditable")
        // $(source[i]).removeClass("rich groupItemBorder")
        $(source[i]).addClass("RGTransition")
    }
}

function showEditGroupModal(id) {
    let isNew = id === null;
    if (isNew) {
        isAddGroup = true
        isEditGroup = false
    } else {
        isAddGroup = false
        isEditGroup = true
    }
    let name = ''
    let level = 0
    if (!isNew) {
        let group = groupSelf.groupData[indexOfGroupId(id)]
        name = group.name
        level = group.level
    }
    name = name ? name : ''
    id = id ? id : ''

    let h5String =
        '        <div class="modal-wrapper">' +
        '        <div class="modal">' +
        '            <div class="modal-header">' +
        '                <img onclick="dismissEditGroupModal()" class="modal-header-close" src="/static/image/close.png" style="width: 15px; height: 15px;">' +
        '                <div class="modal-title">' +
        (isNew ? '新建分组' : '编辑分组') +
        '                </div>' +
        '            </div>' +
        '            <div class="modal-body">' +
        '                <div class="be-input be-input--append">' +
        '                    <input type="input" placeholder="分组名称" class="be-input_inner" id="group-modal-nameInput" value="{5}">' +
        '                </div>' +
        '                <div class="be-switch-container">' +
        '                    <div>'+
        '隐私设置 :'+
        '<select id="group-modal-privacy" style="min-height: 40px;" class="cs-select cs-skin-border">'+
        '<option value="0" {1}>所有人可见</option>'+
        '<option value="1" {2}>仅好友可见</option>'+
        '<option value="2" {3}>仅自己可见</option>'+
        '</select>'+
        '</div>'+'{4}'+
        '                </div>' +
        '            </div>' +
        '            <div class="modal-footer">' +
        '                <div style="display:inline-block; width:50%">' +
        '                    <div class="rgButton" onclick="onEditGroupModalSubmit({0})">' +
        '                        确定' +
        '                    </div>' +
        '                </div>' +
        '            </div>' +
        '        </div>' +
        '    </div>';

    let topH5String = isNew ? (
        '<div class="be-switch-container">' +
        '<input type="checkbox" checked="checked" id="groupAddCheck">' +
        '<label class="be-switch-label" for="groupAddCheck">' +
        '置顶' +
        '</label>' +
        '</div>'
        )
        :
        ''

    let container = document.createElement('div');
    container.className = 'fullScreen';
    container.id = 'GroupFullScreenEdit';

    let selects = [];
    for (let i = 0; i < 3; i++) {
        let value = level === i ? 'selected="selected"' : '';
        selects.push(value);
    }
    container.innerHTML = h5String.format(id, selects[0], selects[1], selects[2], topH5String, name);
    document.body.appendChild(container)

    new SelectFx($('#group-modal-privacy')[0], {
        stickyPlaceholder: true,
        onChange: function (val) {
            // alert(val)
        }
    });
}

function dismissEditGroupModal() {
    if (that.relation >= 0) {
        return
    }
    isAddGroup = false
    let modal = document.getElementById('GroupFullScreenEdit');
    if (modal) document.body.removeChild(modal);
}

function onGroupClick(e) {

    let id = e.attributes.name.value
    let name = e.innerText.trim()

    if (isEditGroup && id > 0 && id !== '') {
        showEditGroupModal(id);
    }
    if (isEditGroup || isEditOrder) {
        event.preventDefault()
        return
    }
    groupSelf.modal_selected_groupId = id
    let index = indexOfGroupId(id)
    let level = index >= 0 ? groupSelf.groupData[index].level : 0
    hideGroup()

    groupSelf.groupSelectCallBack && groupSelf.groupSelectCallBack(id, name, level)
}

function onEditGroupModalSubmit(id) {
    if (!id) {
        doAddGroup()
    } else {
        doEditGroup(id)
    }
}

function doAddGroup() {
    let name = $('#group-modal-nameInput')[0].value.trim()
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

    let level = parseInt($("#group-modal-privacy").val())

    $.ajax({
        type: 'POST',
        url: "/blog/group/new",
        data: {
            name: name,
            order: order,
            level: level
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
                dismissEditGroupModal()

                let newId = result.data.id
                let user_id = result.data.user_id
                let newGroupItem = {
                    id: newId,
                    name: name,
                    order: order,
                    level: level,
                    user_id: user_id
                }
                let groupItemH5 = groupItemH5String(newGroupItem)
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

function doEditGroup(id) {

    id = parseInt(id)
    let name = $('#group-modal-nameInput')[0].value.trim()
    if (!name) {
        alert('名称不能为空')
        return
    }
    let level = parseInt($("#group-modal-privacy").val())

    $.ajax({
        type: 'POST',
        url: "/blog/group/edit",
        data: {
            id: id,
            name: name,
            level: level,
        },
        success: function (result) {
            if (result.code !== 1000) {
                alert('修改失败🙅‍♂️')
            } else {
                let group = groupSelf.groupData[indexOfGroupId(id)]
                if (group) {
                    group.name = name
                    group.level = level
                }
                $('#groupItemName-'+id)[0].innerText = name
                dismissEditGroupModal()
                if (groupSelf.modal_selected_groupId && parseInt(groupSelf.modal_selected_groupId) === id)
                    groupSelf.groupChangeCallBack(group)
            }
        },
        error: function (e) {
            alert(e.statusText)
        },
    })
}

function editOrder() {
    if (isEditGroup)
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

    let source = groupSelf.source
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

    if (!groupSelf.changeElement)
        return

    let id1 = parseInt(groupSelf.dragElement.attributes.name.value)
    let id2 = parseInt(groupSelf.changeElement.attributes.name.value)
    if (id1 === id2) return

    // delete
    let index1 = indexOfGroupId(id1)
    let dragItem = groupSelf.groupData[index1]
    groupSelf.groupData.splice(index1, 1)

    // insert
    if (!groupSelf.lock) {
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
        if (groupSelf.lock && (this === this.parentNode.lastElementChild || this === this.parentNode.lastChild)) {    // 当前元素时最后一个元素
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
            if (confirm('是否要删除「' + groupSelf.dragElement.innerText + '」该分组下的日志都将归入默认分组')) {
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
                            groupSelf.dragElement.parentNode.removeChild(groupSelf.dragElement)
                            $('#defaultGroup').text
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
    if (that.relation >= 0) {
        return
    }
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
        if (id+'' === item.id+'')
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

$(function () {
    loadjscssfile("../static/select/css/cs-select.css", "css")
    loadjscssfile("../static/select/css/cs-skin-border.css", "css")
    loadjscssfile("../static/font-awesome/css/font-awesome.min.css", "css")
    loadjscssfile("../static/select/js/classie.js", "js")
    loadjscssfile("../static/select/js/selectFx.js", "js")
})
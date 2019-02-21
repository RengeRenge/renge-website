function loadart() {
    // var token = $.cookie('rg_token')
    $.get('art/list', '', function (data) {
        console.log(data)
    })
}
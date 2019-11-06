this.isRequest = false;
function checkRequest() {
    if (this.isRequest)
        return true
    this.isRequest = true
    return false
}

function requestFine() {
    this.isRequest = false
}

function check(username, callback) {
    $.ajax({
        type: 'GET',
        dataType: "json",
        url: "/user/check",
        data: {'username': username},
        success: function (data) {
            if (callback)
                callback(data)
        },
        error: function (e) {
            if (callback)
                callback({'code': e.status})
        },
    })
}

function login(username, pwd, remember, callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/login",
        data: {
            'username': username,
            'pwd': pwd,
            'remember': remember,
            'type': 0,
            'channel': 'web'
        },
        success: function (data) {
            if (callback)
                callback(data)
        },
        error: function (e) {
            if (callback)
                callback({'code': e.status})
        },
    })
}

function logout(callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/logout",
        data: {'type': 0},
        success: function (result) {
            callback(result.code === 1000)
        },
        error: function (e) {
            callback(false)
        },
    })
}

function getVerifyCode(email, username, verifyType, callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/getVerifyCode",
        data: {
            'username': username,
            'email': email,
            'verifyType': verifyType
        },
        success: function (result) {
            /**
             * 1002 已存在
             * 1011 登陆状态验证失败
             * */
            if (callback)
                callback(result)
        },
        error: function (e) {
            if (callback)
                callback({'code': e.status})
        },
    })
}

function userVerify(username, pwd, code, remember, verifyType, callback) {
    switch (verifyType) {
        case 0:{
            $.ajax({
                type: 'POST',
                dataType: "json",
                url: "/user/new",
                data: {
                    'username': username,
                    'pwd': pwd,
                    'code': code,
                    'remember': remember,
                    'type': 0,
                    'channel': 'web'
                },
                success: function (result) {
                    if (callback)
                        callback(result)
                },
                error: function (e) {
                    if (callback)
                        callback({'code': e.status})
                },
            })
            break;
        }
        case 2:{
            $.ajax({
                type: 'POST',
                dataType: "json",
                url: "/user/password",
                data: {
                    'username': username,
                    'pwd': pwd,
                    'code': code,
                    'channel': 'web'
                },
                success: function (result) {
                    if (callback)
                        callback(result)
                },
                error: function (e) {
                    if (callback)
                        callback({'code': e.status})
                },
            })
            break;
        }
    }
}

function bindEmail(username, email, email_code, pwd, callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "/user/bind",
        data: {
            'username': username,
            'email': email,
            'pwd': pwd,
            'type': 0,
            'code': email_code,
            'channel': 'web'
        },
        success: function (result) {
            if (callback)
                callback(result)
        },
        error: function (e) {
            if (callback)
                callback({'code': e.status})
        },
    })
}
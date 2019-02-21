function check(username, callback) {
    $.get('user/check', {'username': username}, function (data, status, xhr) {
        if (callback)
            callback(data)
    })
    $.ajax({
        type: 'GET',
        dataType: "json",
        url: "user/check",
        data: {'username': username},
        success: function (data) {
            if (callback)
                callback(data)
        },
        error: function (e) {
            if (callback)
                callback(null)
        },
    })
}

function login(username, pwd, callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "user/login",
        data: {'username': username, 'pwd': pwd, 'type': 0},
        success: function (data) {
            if (callback)
                callback(data)
        },
        error: function (e) {
            if (callback)
                callback(null)
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

function regist(username, pwd, callback) {
    $.ajax({
        type: 'POST',
        dataType: "json",
        url: "user/new",
        data: {'username': username, 'pwd': pwd, 'type': 0},
        success: function (result) {
            if (callback)
                callback(result)
        },
        error: function (e) {
            if (callback)
                callback(null)
        },
    })
}
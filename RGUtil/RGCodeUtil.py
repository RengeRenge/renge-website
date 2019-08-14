from enum import IntEnum


class RGVerifyType(IntEnum):
    new = 0
    bind = 1
    forget_pwd = 2


class RGResCode(IntEnum):
    ok = 1000
    not_existed = 1001
    has_existed = 1002
    insert_fail = 1003
    del_fail = 1004
    lack_param = 1005
    update_fail = 1006
    database_error = 1007
    timeout = 1008
    frequent = 1009
    server_error = 1010
    auth_fail = 1011
    verify_code_incorrect = 1012
    password_incorrect = 1013
    user_has_existed = 1014

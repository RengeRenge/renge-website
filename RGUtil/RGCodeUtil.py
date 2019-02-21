from enum import IntEnum


class http_code(IntEnum):
    ok = 1000
    not_existed = 1001
    has_existed = 1002
    insert_fail = 1003
    del_fail = 1004
    lack_param = 1005
    update_fail = 1004

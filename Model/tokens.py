from DAO import rg_dao as dao
from RGUtil import RGTokenUtil, RGTimeUtil


def generate_token_ifneed(user_id, token_type):
    new_token = RGTokenUtil.generate_token(str(user_id))
    new_time = RGTimeUtil.timestamp()
    token_type = int(token_type)
    sql = "INSERT INTO tokens (user_id, type, token, timestamp) \
    VALUES ('%ld', %d, '%s', %ld) ON DUPLICATE KEY UPDATE token='%s', timestamp=%ld" \
          % (user_id, token_type, new_token, new_time, new_token, new_time)
    print (sql)

    result, count, new_id = dao.execute_sql(sql, neednewid=True)

    print (count)

    if count > 0:
        return new_token
    else:
        return None


def destroy_token(user_id, token_type):
    sql = 'delete from tokens where user_id=%ld and type=%d' % (user_id, token_type)
    try:
        dao.execute_sql(sql)
        return True
    except:
        return False


def certify_token(token, token_type=0):
    sql = "SELECT * FROM tokens where token='%s' AND type=%d" % (str(token), int(token_type))

    result, count, new_id = dao.execute_sql(sql)

    if count:
        user_id = result[0][0]
        return user_id, RGTokenUtil.certify_token(user_id, token)
    else:
        return None, False

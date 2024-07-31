from DAO import rg_dao as dao
from RGUtil import RGTokenUtil, RGTimeUtil
import logging as L

logging = L.getLogger("Renge")


def generate_token_ifneed(user_id, token_type):
    new_token = RGTokenUtil.generate_token(str(user_id))
    new_time = RGTimeUtil.timestamp()
    token_type = int(token_type)
    sql = "INSERT INTO tokens (user_id, type, token, timestamp) \
            VALUES (%(user_id)s, %(token_type)s, %(new_token)s, %(new_time)s) \
            ON DUPLICATE KEY UPDATE token=%(new_token)s, timestamp=%(new_time)s"
    result, count, new_id = dao.execute_sql(sql, new_id=True, args={
        'user_id': user_id,
        'token_type': token_type,
        'new_token': new_token,
        'new_time': new_time,
    })

    logging.info(count)

    if count > 0:
        return new_token
    else:
        return None


def destroy_token(user_id, token_type):
    sql = 'delete from tokens where user_id=%(user_id)s and type=%(token_type)s'
    try:
        dao.execute_sql(sql, args={
            'user_id': user_id,
            'token_type': token_type
        })
        return True
    except:
        return False


def certify_token(token, token_type=0):
    sql = "SELECT * FROM tokens where token=%(token)s AND type=%(token_type)s"

    result, count, new_id = dao.execute_sql(sql, args={
        'token': token,
        'token_type': token_type
    })

    if count:
        user_id = result[0][0]
        return user_id, RGTokenUtil.certify_token(user_id, token)
    else:
        return None, False

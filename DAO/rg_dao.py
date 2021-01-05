import threading

import pymysql
from flask import json

from RGUtil.RGLogUtil import LogUtil

with open('./RGIgnoreConfig/rg_database.json', 'r') as f:
    config = json.loads(f.read())

executeMutex = threading.RLock()


# conn = pymysql.connect(**config)


# conn.autocommit(True)


def get():
    return pymysql.connect(**config)


def close(conn, cursor):
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()


# def escape_string(string):
#     if string and len(string) >= 0:
#         return pymysql.escape_string(string)
#     return string
#
#
# def remove_none_key(args):
#     for k in list(args.keys()):
#         if args[k] is None:
#             del args[k]
#             continue
#     return args

def get_last_insert(cursor):
    cursor.execute('SELECT LAST_INSERT_ID();')
    return cursor.fetchone()


def execute_sql(sql, ret=True, kv=False, new_id=False, dp=0, args=None):
    """
    Execute a specific SQL and update data version if need.
    :param sql: sql string
    :param ret: need return execution result
    :param kv: 需要将结果转换成字典键值对
    :param new_id: 需要查询最新的ID
    :param dp: depth of exception stack
    :param args: sql 参数
    :return: execution result table
    """
    res, count, new_id, err = do_execute_sql(sql, ret=ret, kv=kv, new_id=new_id, dp=dp,
                                             args=args)
    return res, count, new_id


def do_execute_sql(sql, ret=True, kv=False, new_id=False, dp=0, args=None, conn=None, commit=False):
    """
    执行SQL语句

    :param sql: sql语句
    :param ret: 需要执行返回的结果
    :param kv: 需要将结果转换成字典键值对
    :param new_id: 需要查询最新的ID
    :param dp:
    :param args: sql 参数
    :param conn: 为空时会自己创建一个连接
    :param commit: 只有当连接为外部创建（conn 非空）时才生效
    :return: result, count, new_id, error
    """
    auto_conn = True if conn is None else False
    try:
        if auto_conn:
            conn = get()
        return \
            do_execute_sql_with_connect(sql=sql, ret=ret, kv=kv, new_id=new_id, dp=dp,
                                        args=args,
                                        conn=conn,
                                        commit=True if auto_conn else commit)
    except Exception as e:
        if auto_conn:
            conn.rollback()
            conn.commit()
        return None, 0, -1, e
    finally:
        if conn and auto_conn:
            conn.close()


def do_execute_sql_with_connect(sql, ret=True, kv=False, new_id=False, dp=0, args=None, conn=None,
                                commit=True):
    """
        Execute a specific SQL.
        :param sql: sql string
        :param ret: need return execution result
        :param kv: need dict result
        :param new_id: need new Id
        :param args: sql params
        :param conn: sql connection
        :param dp: depth of exception stack
        :param commit: auto commit
        :return: execution result table
        """
    executeMutex.acquire()
    cursor = None
    try:
        cursor = conn.cursor()
        count = cursor.execute(query=sql, args=args)
        find_new_id = -1
        if ret is True:
            if kv is True and cursor.description is not None:
                values = cursor.fetchall()
                names = [cd[0] for cd in cursor.description]

                if count > 0 and new_id:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    find_new_id = result[0]

                if commit:
                    conn.commit()
                return [dict(zip(names, v)) for v in values], count, find_new_id, None
            else:
                if count > 0 and new_id:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    find_new_id = result[0]

                if commit:
                    conn.commit()
                return cursor.fetchall(), count, find_new_id, None
        else:
            if commit:
                conn.commit()
            return None, count, -1, None
    except Exception as e:
        print(e)
        try:
            if dp > 1:
                return
            LogUtil.ErrorLog("In ExecuteSQL, " + str(e) + " | Query: << " + (u"%s" % sql) + " >>",
                             __name__, dp=dp + 1)
        except:
            from traceback import format_exc
            print('ExecuteSQL Exception:')
            print(format_exc())
        return None, 0, -1, e
    finally:
        if cursor:
            cursor.close()
        executeMutex.release()


def execute_sqls(sqls, ret=True, kv=False, new_id=False, dp=0):
    """
    Execute a specific SQLs.
    :param sqls: tuple or string Array like-> [(sql1, args1), (sql2, args2)] or [sql1, (sql2, args2)]
    :param ret: need return execution result
    :param kv: need dict result
    :param new_id: need new Id
    :param dp: depth of exception stack
    :return: execution result table
    """
    executeMutex.acquire()
    cursor = None
    conn = None
    sql = ''
    try:
        conn = get()
        cursor = conn.cursor()
        results = []
        for index in range(len(sqls)):

            sql = sqls[index]
            args = None
            if isinstance(sql, tuple):
                sql, args = sqls[index]

            count = cursor.execute(sql, args)
            result = None
            find_new_id = -1
            if ret is True:
                if kv is True and cursor.description is not None:

                    values = cursor.fetchall()
                    names = [cd[0] for cd in cursor.description]

                    if count > 0 and new_id:
                        cursor.execute('SELECT LAST_INSERT_ID();')
                        result = cursor.fetchone()
                        find_new_id = result[0]

                    result = [dict(zip(names, v)) for v in values]
                else:
                    if count > 0 and new_id:
                        cursor.execute('SELECT LAST_INSERT_ID();')
                        result = cursor.fetchone()
                        find_new_id = result[0]

            item = {
                'result': result,
                'count': count,
                'newId': find_new_id
            }
            results.append(item)
        conn.commit()
        return results
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()

        try:
            if dp > 1:
                return
            LogUtil.ErrorLog("In ExecuteSQL, " + str(e) + " | Query: << " + (u"%s" % sql) + " >>",
                             __name__, dp=dp + 1)
        except:
            from traceback import format_exc
            print('ExecuteSQL Exception:')
            print(format_exc())
        return None
    finally:
        close(conn, cursor)
        executeMutex.release()

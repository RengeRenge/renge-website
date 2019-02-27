import threading

import pymysql
from flask import json

from RGUtil.RGLogUtil import LogUtil

with open('rg_database.json', 'r') as f:
    config = json.loads(f.read())
    f.close()

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


def execute_sql(sql, needret=True, needdic=False, neednewid=False, dp=0, args=None, commit=True):
    """
    Execute a specific SQL and update data version if need.
    :param sql: sql string
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    res, count, new_id, err = do_execute_sql(sql, needret=needret, needdic=needdic, neednewid=neednewid, dp=dp,
                                             args=args, commit=commit)
    return res, count, new_id


def execute_sql_err(sql, needret=True, needdic=False, neednewid=False, dp=0, args=None, commit=True):
    """
    Execute a specific SQL and update data version if need.
    :param sql: sql string
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    return do_execute_sql(sql, needret=needret, needdic=needdic, neednewid=neednewid, dp=dp, args=args, commit=commit)


def do_execute_sql(sql, needret=True, needdic=False, neednewid=False, dp=0, args=None, commit=True):
    """
    Execute a specific SQL.
    :param sql: sql string
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    executeMutex.acquire()
    cursor = None
    conn = None
    try:
        conn = get()
        cursor = conn.cursor()
        count = cursor.execute(query=sql, args=args)
        new_id = -1
        if needret is True:
            if needdic is True and cursor.description is not None:
                values = cursor.fetchall()
                names = [cd[0] for cd in cursor.description]

                if count > 0 and neednewid:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    new_id = result[0]

                if commit:
                    conn.commit()
                return [dict(zip(names, v)) for v in values], count, new_id, None
            else:
                if count > 0 and neednewid:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    new_id = result[0]

                if commit:
                    conn.commit()
                return cursor.fetchall(), count, new_id, None
        else:
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
        close(conn, cursor)
        executeMutex.release()


def execute_sqls(sqls, needret=True, needdic=False, neednewid=False, dp=0):
    """
    Execute a specific SQLs.
    :param sqls: tuple or string Array like-> [(sql1, args1), (sql2, args2)] or [sql1, (sql2, args2)]
    :param needret: need return execution result
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
            new_id = -1
            if needret is True:
                if needdic is True and cursor.description is not None:

                    values = cursor.fetchall()
                    names = [cd[0] for cd in cursor.description]

                    if count > 0 and neednewid:
                        cursor.execute('SELECT LAST_INSERT_ID();')
                        result = cursor.fetchone()
                        new_id = result[0]

                    result = [dict(zip(names, v)) for v in values]
                else:
                    if count > 0 and neednewid:
                        cursor.execute('SELECT LAST_INSERT_ID();')
                        result = cursor.fetchone()
                        new_id = result[0]

            item = {
                'result': result,
                'count': count,
                'newId': new_id
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

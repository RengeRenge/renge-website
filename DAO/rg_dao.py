import threading

import pymysql
from flask import json
from sqlalchemy.dialects import mysql

from RGUtil import RGLogUtil

with open('rg_database.json', 'r') as f:
    config = json.loads(f.read())

executeMutex = threading.RLock()

conn = pymysql.connect(**config)


# conn.autocommit(True)


def get():
    return conn


def escape_string(string):
    if string and len(string) >= 0:
        return pymysql.escape_string(string)
    return string


def execute_sql(sql, needret=True, needdic=False, neednewid=False, dp=0):
    # type: (str, bool, bool, bool, int) -> (object, int, int)
    """
    Execute a specific SQL and update data version if need.
    :param sql: sql string
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    return do_execute_sql(sql, needret=needret, needdic=needdic, neednewid=neednewid, dp=dp)


def do_execute_sql(sql, needret=True, needdic=False, neednewid=False, dp=0):
    """
    Execute a specific SQL.
    :param sql: sql string
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    executeMutex.acquire()
    cursor = None
    try:
        cursor = get().cursor()
        count = cursor.execute(sql)
        new_id = -1
        if needret is True:
            if needdic is True and cursor.description is not None:
                values = cursor.fetchall()
                names = [cd[0] for cd in cursor.description]

                if count > 0 and neednewid:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    new_id = result[0]

                conn.commit()
                return [dict(zip(names, v)) for v in values], count, new_id
            else:
                if count > 0 and neednewid:
                    cursor.execute('SELECT LAST_INSERT_ID();')
                    result = cursor.fetchone()
                    new_id = result[0]

                conn.commit()
                return cursor.fetchall(), count, new_id
        else:
            return None, count, -1
    except mysql.connector.Error as e:
        try:
            if dp > 1:
                return
            RGLogUtil.ErrorLog("In ExecuteSQL, " + str(e) + " | Query: << " + (u"%s" % sql) + " >>",
                               __name__, dp=dp + 1)
        except:
            from traceback import format_exc
            print('ExecuteSQL Exception:')
            print(format_exc())
    finally:
        if cursor is not None:
            cursor.close()
        executeMutex.release()


def execute_sqls(sqls, needret=True, needdic=False, neednewid=False, dp=0):
    """
    Execute a specific SQLs.
    :param sqls: sqls string Array
    :param needret: need return execution result
    :param dp: depth of exception stack
    :return: execution result table
    """
    executeMutex.acquire()
    cursor = None
    try:
        cursor = get().cursor()
        results = []
        for sql in sqls:
            count = cursor.execute(sql)
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
            else:
                result = None

            results.append({
                'result': result,
                'count': count,
                'newId': new_id
            })
            conn.commit()
        return results
    except mysql.connector.Error as e:

        conn.rollback()
        conn.commit()

        try:
            if dp > 1:
                return
            RGLogUtil.ErrorLog("In ExecuteSQL, " + str(e) + " | Query: << " + (u"%s" % sql) + " >>",
                               __name__, dp=dp + 1)
        except:
            from traceback import format_exc
            print('ExecuteSQL Exception:')
            print(format_exc())
    finally:
        if cursor is not None:
            cursor.close()
        executeMutex.release()

from DAO import rg_dao as dao
from RGIgnoreConfig.RGFileGlobalConfigContext import url_with_name, RGFileMaxCapacity
from RGUtil import RGTimeUtil


def filter_return_file_info(file_info, need_id=False):
    user_file = {
        "hash": file_info['hash'],
        "mime": file_info['mime'],
        "size": file_info['size'],
        "filename": file_info['filename']
    }
    if need_id:
        user_file['id'] = file_info['id']
    return user_file


def new_file(conn=None, filename='', mime='', exif_time=0,
             exif_info=None, exif_lalo=None, file_hash=None, size=0, forever=0):
    timestamp = RGTimeUtil.timestamp()
    sql = "INSERT INTO `file` \
    (filename, mime, exif_timestamp, `timestamp`, `exif_info`, `exif_lalo`, `hash`, `size`, `forever`) \
    VALUES \
    (%(filename)s, %(mime)s, %(exif_timestamp)s, %(timestamp)s, \
    %(exif_info)s, %(exif_lalo)s, %(hash)s, %(size)s, %(forever)s)"
    args = {
        'filename': filename,
        'mime': mime,
        'exif_timestamp': exif_time,
        'timestamp': timestamp,
        'exif_info': exif_info,
        'exif_lalo': exif_lalo,
        'hash': file_hash,
        'size': str(size),
        'forever': forever
    }
    result, count, new_id, err = dao.do_execute_sql(
        sql=sql, conn=conn, new_id=True, args=args, commit=False)
    if count > 0:
        args['id'] = new_id
        return args
    else:
        return None


def format_path(dir_path, dir_id):
    if dir_path is None:
        dir_path = ''
    path_array = list(filter(None, dir_path.split(',')))
    if dir_id is not None and int(dir_id) >= 0:
        path_array.append(str(dir_id))
    return ',{},'.format(','.join(path_array))


def new_user_file(conn, user_id, file_id, type, directory_id, personal_name, add_timestamp, update_timestamp,
                  combined_file_info=None):
    sql = "SELECT * from user_file where id = %(directory_id)s and user_id=%(user_id)s limit 1"
    args = {
        'directory_id': directory_id,
        'user_id': user_id
    }

    directory_path = None
    d_id = None
    directory, count, new_id, err = \
        dao.do_execute_sql_with_connect(conn=conn, sql=sql, kv=True, new_id=True, args=args, commit=False)
    if count > 0:
        directory = directory[0]
        directory_path = directory['directory_path']
        d_id = directory['id']
    directory_path = format_path(dir_path=directory_path, dir_id=d_id)

    sql = "INSERT INTO user_file \
            (user_id, file_id, type, directory_path, directory_id, personal_name, add_timestamp, update_timestamp) \
            VALUES \
            (%(user_id)s, %(file_id)s, %(type)s, %(directory_path)s, %(directory_id)s, %(name)s,\
            %(add_timestamp)s, %(update_timestamp)s)"
    args = {
        'user_id': user_id,
        'file_id': file_id,
        'type': type,
        'directory_path': directory_path,
        'directory_id': directory_id,
        'name': personal_name,
        'add_timestamp': add_timestamp,
        'update_timestamp': update_timestamp
    }
    result, count, new_id, err = dao.do_execute_sql_with_connect(
        sql=sql,
        conn=conn,
        new_id=True,
        commit=False,
        args=args
    )
    if count > 0:
        args['id'] = new_id
        del args['user_id']
        if type == 1:
            del args['file_id']
        if combined_file_info is not None:
            args.update(filter_return_file_info(combined_file_info))
        return args
    return None


def new_directory(user_id, directory_id=-1, name=''):
    conn = None
    try:
        conn = dao.get()
        time = RGTimeUtil.timestamp()
        file = new_user_file(conn=conn, user_id=user_id, file_id=None, type=1, directory_id=directory_id,
                             personal_name=name, add_timestamp=time, update_timestamp=time)
        conn.commit()
        return file
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return None
    finally:
        if conn:
            conn.close()


def check_file(file_hash=None, forever=None, conn=None):
    if forever is None:
        sql = "SELECT * from file WHERE `hash` = %(hash)s limit 1"
    else:
        sql = "SELECT * from file WHERE `hash` = %(hash)s and `forever` = %(forever)s limit 1"
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql,
        conn=conn,
        kv=True,
        args={'hash': file_hash, 'forever': forever}
    )
    if count > 0:
        return result[0]
    return None


def check_and_new_user_file_with_hash(user_id, directory_id=-1, file_hash=None, name=''):
    conn = None
    user_file = None
    from RGUtil.RGCodeUtil import RGResCode
    code = RGResCode.server_error
    try:
        conn = dao.get()
        file_info = check_file(file_hash=file_hash, conn=conn)
        if file_info is None:
            code = RGResCode.not_existed
            raise Exception(code)

        if file_info is not None:
            if not capacity_enough(user_id=user_id, new_file_size=file_info['size'], conn=conn):
                code = RGResCode.full_size
                raise Exception('capacity not enough')

            time = RGTimeUtil.timestamp()
            user_file = new_user_file(conn=conn, user_id=user_id, file_id=file_info['id'], type=0,
                                      directory_id=directory_id,
                                      personal_name=name, add_timestamp=time, update_timestamp=time,
                                      combined_file_info=file_info)
            if user_file is None:
                code = RGResCode.insert_fail
                raise Exception('new_user_file failed')
        code = RGResCode.ok
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
    finally:
        if conn:
            conn.close()
        return user_file, code


def user_file_list(user_id, directory_id=None):
    conn = None
    try:
        conn = dao.get()
        sql = "SELECT \
        user_file.id as id, \
        personal_name as name, \
        file.filename as filename,\
        file.exif_timestamp as exif_timestamp,\
        directory_path, directory_id ,type, size, add_timestamp, update_timestamp, hash, mime \
        from user_file \
        left join file on user_file.file_id = file.id\
        WHERE user_id =  %(user_id)s and directory_id = %(directory_id)s"

        file, count, new_id, err = dao.do_execute_sql_with_connect(
            conn=conn,
            commit=False,
            sql=sql,
            kv=True,
            args={
                'directory_id': directory_id,
                'user_id': user_id
            }
        )

        sql = "SELECT \
        c.personal_name as name,\
        c.id as id,\
        c.type as type,\
        c.add_timestamp as add_timestamp,\
        c.update_timestamp as update_timestamp\
        FROM user_file c\
        LEFT JOIN ( \
            SELECT CONCAT_WS(',', directory_path, id) as path from user_file \
              where user_id=%(user_id)s and id=%(file_id)s) temp on true \
        WHERE (\
            SELECT FIND_IN_SET(c.id, CONCAT_WS(',', t.directory_path, t.id)) \
            from user_file t where t.user_id=%(user_id)s and t.id=%(file_id)s \
        )\
        order by FIND_IN_SET(c.id, temp.path)"

        directory, count, new_id, err = dao.do_execute_sql_with_connect(
            conn=conn,
            commit=False,
            sql=sql,
            kv=True,
            args={
                'file_id': directory_id,
                'user_id': user_id
            }
        )
        conn.commit()
        return {'files': file, 'path': directory}
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return False
    finally:
        if conn:
            conn.close()


# 查找该文件夹下的所有文件夹
def user_file_directory_list(user_id, directory_id=None):
    conn = None
    try:
        conn = dao.get()
        sql = "SELECT \
        user_file.id as id, \
        personal_name as name, \
        directory_path, directory_id ,type, size, add_timestamp, update_timestamp, hash, mime \
        from user_file \
        left join file on user_file.file_id = file.id\
        WHERE user_id =  %(user_id)s and directory_id = %(directory_id)s and type=1"

        file, count, new_id, err = dao.do_execute_sql_with_connect(
            conn=conn,
            commit=False,
            sql=sql,
            kv=True,
            args={
                'directory_id': directory_id,
                'user_id': user_id
            }
        )
        conn.commit()
        return {'files': file}
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return False
    finally:
        if conn:
            conn.close()


def user_file_list_with_name(user_id, name):
    # name.upper
    conn = None
    try:
        conn = dao.get()
        sql = "SELECT \
            user_file.id as id, \
            personal_name as name, \
            file.filename as filename,\
            directory_path, directory_id ,type, size, add_timestamp, update_timestamp, hash, mime \
            from user_file \
            left join file on user_file.file_id = file.id\
            WHERE user_id =  %(user_id)s and UPPER(user_file.personal_name) like BINARY %(personal_name)s"

        file, count, new_id, err = dao.do_execute_sql_with_connect(
            conn=conn,
            commit=False,
            sql=sql,
            kv=True,
            args={
                'personal_name': '%{}%'.format(name.upper()),
                'user_id': user_id
            }
        )
        conn.commit()
        return {'files': [] if file is None else file}
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return False
    finally:
        if conn:
            conn.close()


def user_file_info(user_id, id=None, type=0):
    sql = "SELECT \
    file.filename as filename, \
    user_file.personal_name as name, \
    file.mime as mime, \
    file.size as size, \
    file.hash as hash, \
    user_file.id as id \
    from user_file \
    left join file on user_file.file_id = file.id \
    WHERE user_file.id=%(id)s and user_file.user_id = %(user_id)s and user_file.type = %(type)s limit 1"
    result, count, new_id = dao.execute_sql(
        sql=sql,
        kv=True,
        args={
            'id': id,
            'user_id': user_id,
            'type': type
        }
    )
    if count > 0:
        return result[0]
    return None


def file_set(id, conn=None, args=None):
    if len(args.keys()) == 0:
        return False

    if args is None:
        args = {}

    params = ''
    for k, v in args.items():
        if len(params) > 0:
            params += ','
        params += '{}=%({})s'.format(k, k)

    sql = "UPDATE file SET {} where id=%(id)s".format(params)

    args['id'] = id
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, ret=False, commit=False, args=args)
    return True if error is None else False


def user_file_set(user_id, id, conn=None, args=None):
    if len(args.keys()) == 0:
        return False

    if args is None:
        args = {}

    params = ''
    for k, v in args.items():
        if len(params) > 0:
            params += ','
        params += '{}=%({})s'.format(k, k)

    sql = "UPDATE user_file SET {} where id=%(id)s and user_id=%(user_id)s".format(params)

    args['id'] = id
    args['user_id'] = user_id
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, ret=False, commit=False, args=args)
    return True if error is None else False


def user_file_files_relative_with_id(user_id, id, conn=None):
    sql = "SELECT \
            user_file.id as id, \
            user_file.file_id as file_id, \
            user_file.type as type,\
            user_file.personal_name as name, \
            file.mime as mime,\
            file.filename as filename,\
            file.forever as forever\
            from user_file \
            left join file on user_file.file_id = file.id\
            where ((find_in_set(%(id)s, user_file.directory_path) or (user_file.id=%(id)s)) \
            and user_file.type = 0 \
            and user_file.user_id=%(user_id)s)"
    args = {
        'id': '' if id == -1 else id,
        'user_id': user_id
    }
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, kv=True, commit=False, args=args)
    return result, error


def user_file_del(user_id, id, conn=None):
    sql = "DELETE from user_file where ((find_in_set(%(id)s, directory_path) or (id=%(id)s)) and user_id=%(user_id)s)"
    args = {
        'id': id,
        'user_id': user_id
    }
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, ret=True, commit=False, args=args)
    return error


def file_del(ids, conn=None):
    sql = "DELETE from file where find_in_set(id, %(ids)s) and forever = 0"
    args = {
        'ids': ','.join(ids),
    }
    result, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, ret=True, commit=False, args=args)
    return error


def user_file_need_remove_from_disk(delete_user_files, conn=None):
    file_ids = [str(file['file_id']) for file in delete_user_files if file['forever'] == 0]
    file_ids = list(set(file_ids))

    sql = "SELECT file_id from user_file where find_in_set(file_id, %(file_ids)s)"
    args = {
        'file_ids': ",".join(file_ids),
    }
    exist, count, new_id, error = dao.do_execute_sql(
        sql=sql, conn=conn, kv=True, ret=True, commit=False, args=args)
    if error is not None:
        return [], error

    exist_ids = [str(file['file_id']) for file in exist]
    file_ids = [file_id for file_id in file_ids if file_id not in exist_ids]
    return file_ids, None


def user_file_del_and_return_files(user_id, id, conn):
    files, error = user_file_files_relative_with_id(user_id=user_id, id=id, conn=conn)
    if error is not None:
        raise error

    error = user_file_del(user_id=user_id, id=id, conn=conn)
    if error is not None:
        raise error

    delete_file_ids, error = user_file_need_remove_from_disk(delete_user_files=files, conn=conn)
    if error is not None:
        raise error

    error = file_del(ids=delete_file_ids, conn=conn)
    if error is not None:
        raise error

    return [file['filename'] for file in files if str(file['file_id']) in delete_file_ids]


def filename(file_id, needUrl=False):
    if file_id is None:
        return None

    sql = 'SELECT * FROM file where id=%(file_id)s'
    result, count, new_id = dao.execute_sql(sql, kv=True, args={
        'file_id': file_id
    })
    if count > 0:
        name = result[0]['filename']
        if needUrl:
            return url_with_name(name)
        else:
            return name
    else:
        return None


def user_file_move(user_id, move_id, to_id):
    conn = None
    try:
        conn = dao.get()
        sql = "SELECT * from user_file where id=%(id)s and user_id=%(user_id)s"
        args = {
            'id': move_id,
            'user_id': user_id
        }
        file, count, new_id, err = dao.do_execute_sql_with_connect(conn=conn, sql=sql, commit=False, kv=True,
                                                                   args=args)
        if err or count <= 0:
            raise Exception
        file = file[0]

        args['id'] = to_id
        directory, count, new_id, err = dao.do_execute_sql_with_connect(conn=conn, sql=sql, commit=False, kv=True,
                                                                        args=args)
        if err:
            raise Exception

        dir_path = ''
        dir_id = None
        if count > 0:
            directory = directory[0]
            dir_path = directory['directory_path']
            dir_id = directory['id']

        to_directory_path = format_path(dir_path=dir_path, dir_id=dir_id)

        if file['type'] == 1:
            find_id = ',{},'.format(str(file['id']))
            # 防止文件夹挪动到自己内部
            if to_directory_path.find(find_id) >= 0:
                raise Exception
            # 改变文件夹内的所有文件路径
            del_pre = file['directory_path']
            new_pre = to_directory_path

            del_pre = del_pre.rstrip(',')
            new_pre = new_pre.rstrip(',')
            sql = "UPDATE user_file SET " \
                  "directory_path=CONCAT(" \
                  "%(new_pre)s, " \
                  "',', " \
                  "trim(BOTH ',' from trim(LEADING %(del_pre)s from directory_path)), " \
                  "',') " \
                  "where user_id=%(user_id)s and (FIND_IN_SET(%(move_id)s, directory_path))"

            args = {
                'user_id': user_id,
                'move_id': move_id,
                'new_pre': new_pre,
                'del_pre': del_pre
            }
            files, count, new_id, err = dao.do_execute_sql_with_connect(conn=conn, sql=sql, commit=False,
                                                                        kv=True,
                                                                        args=args)
            if err:
                raise Exception

        sql = "UPDATE user_file SET " \
              "directory_id=%(directory_id)s, " \
              "directory_path=%(directory_path)s " \
              "where id=%(id)s and user_id=%(user_id)s"
        args['directory_id'] = to_id
        args['directory_path'] = to_directory_path
        args['id'] = move_id

        new_fil, count, new_id, err = dao.do_execute_sql_with_connect(conn=conn, sql=sql, commit=False,
                                                                      kv=True,
                                                                      args=args)
        if err:
            raise Exception
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
        return False
    finally:
        if conn:
            conn.close()


def user_file_size(user_id, id, conn=None):
    sql = "SELECT \
                COALESCE(sum(size), 0) as size\
                from user_file \
                left join file on user_file.file_id = file.id\
                where ((find_in_set(%(id)s, user_file.directory_path) or (user_file.id=%(id)s)) \
                and user_file.type = 0 \
                and user_file.user_id=%(user_id)s)"
    args = {
        'id': '' if id == -1 else id,
        'user_id': user_id
    }
    result, count, new_id, error = dao.do_execute_sql(sql=sql, args=args, conn=conn, kv=True)
    capacity = 0
    if result is not None and len(result) > 0:
        capacity = result[0]['size']
    return error, capacity


def use_capacity(user_id, conn=None):
    sql = 'SELECT COALESCE(sum(size), 0) as sum from user_file left join file on user_file.file_id = file.id \
    where user_file.type = 0 and user_id = %(user_id)s'
    result, count, new_id, error = dao.do_execute_sql(sql=sql, args={'user_id': user_id}, conn=conn, kv=True)
    capacity = RGFileMaxCapacity
    if result is not None and len(result) > 0:
        capacity = result[0]['sum']
    return capacity


def capacity_enough(user_id, new_file_size, conn=None):
    capacity = use_capacity(user_id=user_id, conn=conn)
    return True if capacity + int(new_file_size) <= RGFileMaxCapacity else False

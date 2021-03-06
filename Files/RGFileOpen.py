from functools import wraps

from flask import request, jsonify

from Model import files
from RGUtil import RGRequestHelp
from RGUtil.RGCodeUtil import RGResCode
from RGUtil.RGRequestHelp import request_value, form_res
from DAO import rg_dao as dao


class RGFileOpen(object):
    pass


def file_open_handler(wrapper_code_key=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            code = request_value(request, 'open_code')
            if code is None:
                if wrapper_code_key is not None:
                    code = kwargs.get(wrapper_code_key)
                if code is None:
                    return jsonify(form_res(RGResCode.lack_param))
            try:
                f_id, u_id = RGRequestHelp.fid_decode(code)
            except Exception as e:
                return jsonify(form_res(RGResCode.param_error))
            conn = None
            try:
                conn = dao.get()
                open_code_info = files.user_file_info(user_id=u_id, id=f_id, open_code=code, conn=conn)
                if open_code_info is None:
                    return jsonify(form_res(RGResCode.not_existed))

                file_id = request_value(request, 'id')
                info = open_code_info
                if file_id is not None:
                    file_id = int(file_id)
                    if f_id != file_id:
                        file_info = files.user_file_info(user_id=u_id, id=file_id)
                        if file_info is None:
                            return jsonify(form_res(RGResCode.not_existed))
                        paths = file_info['directory_path'].split(sep=',')
                        open_path = str(open_code_info['id'])
                        if open_path in paths:
                            info = file_info

                kwargs.update({
                    'conn': conn,
                    'info': info,
                    'open_code_info': open_code_info,
                    'f_id': f_id,
                    'u_id': u_id,
                })
                response = func(*args, **kwargs)
                conn.commit()
                return response
            except Exception as e:
                print(e)
                conn.rollback()
                conn.commit()
                return jsonify(form_res(RGResCode.database_error))
            finally:
                if conn:
                    conn.close()
        return wrapper
    return decorator

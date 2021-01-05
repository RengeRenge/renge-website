import requests
from flask import json

from DAO import rg_dao as dao
from Model import files
from RGIgnoreConfig.RGFileGlobalConfigContext import RemoteFileHost, FilePreFix


def update_file_list():
    conn = None
    try:
        conn = dao.get()

        sql = 'select * from file'
        result, count, new_id, error = dao.do_execute_sql(sql=sql, ret=True, kv=True, conn=conn)
        filenames = []
        for file in result:
            filename = file['filename']
            filenames.append(filename)
        url = RemoteFileHost + '/' + FilePreFix + 'info'
        req = requests.get(url=url, json={"names": filenames})

        file_infos = req.json()
        for i in range(len(result)):
            id = result[i]['id']
            info = file_infos[i]
            if info['flag']:
                size = info['size']
                hash = info['hash']
                exif = info['exif']
                exif_info = exif.get('original', None)
                if exif_info:
                    exif_info = json.dumps(exif_info)
                args = {
                    'size': size,
                    'hash': hash,
                    'exif_info': exif_info
                }
                print('will update', result[i]['filename'], args)
                files.file_set(id=id, conn=conn, args=args)
        conn.commit()
    except Exception as e:
        print(e)
        conn.rollback()
        conn.commit()
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    update_file_list()

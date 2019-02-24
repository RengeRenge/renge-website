from DAO import rg_dao as dao
from Files.RGFileGlobalConfigContext import url_with_name
from RGUtil import RGTimeUtil


class RGFile:
    def __init__(self, ID, name, type, exif_timestamp, timestamp):
        self.ID = ID
        self.name = name
        self.type = type
        self.exif_timestamp = exif_timestamp
        self.timestamp = timestamp


def new_file(file_name, file_type='', exif=0):
    timestamp = RGTimeUtil.timestamp()

    sql = "INSERT INTO file (file_name, type, exif_timestamp, timestamp) VALUES \
          (%(file_name)s, %(file_type)s, %(exif)s, %(timestamp)s)"
    result, count, new_id = dao.execute_sql(sql, neednewid=True, args={
        'file_name': file_name,
        'file_type': file_type,
        'exif': exif,
        'timestamp': timestamp
    })
    if count > 0:
        file_id = new_id
    else:
        file_id = -1
    return RGFile(file_id, file_name, file_type, exif, timestamp)


def file_name(file_id, needUrl=False):
    if file_id is None:
        return None

    sql = 'SELECT * FROM file where id=%(file_id)s'
    result, count, new_id = dao.execute_sql(sql, needdic=True, args={
        'file_id': file_id
    })
    if count > 0:
        name = result[0]['file_name']
        if needUrl:
            return url_with_name(name)
        else:
            return name
    else:
        return None

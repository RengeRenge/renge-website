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

    sql = "INSERT INTO file (file_name, type, exif_timestamp, timestamp) VALUES ('%s', '%s', '%ld', %ld)" % \
          (file_name, file_type, exif, timestamp)
    result, count, new_id = dao.execute_sql(sql, neednewid=True)
    if count > 0:
        file_id = new_id
    else:
        file_id = -1
    return RGFile(file_id, file_name, file_type, exif, timestamp)


def file_name(file_id, needUrl=False):

    if file_id is None:
        return None

    file_id = int(file_id)
    sql = 'SELECT * FROM file where id=%ld' % file_id
    result, count, new_id = dao.execute_sql(sql, needdic=True)
    if count > 0:
        name = result[0]['file_name']
        if needUrl:
            return url_with_name(name)
        else:
            return name
    else:
        return None

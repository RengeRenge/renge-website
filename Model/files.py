from DAO import rg_dao as dao
from RGIgnoreConfig.RGFileGlobalConfigContext import url_with_name
from RGUtil import RGTimeUtil


class RGFile:
    def __init__(self, ID, name, type, exif_timestamp, timestamp, exif_lalo, exif_info):
        self.ID = ID
        self.name = name
        self.type = type
        self.exif_timestamp = exif_timestamp
        self.timestamp = timestamp
        self.exif_info = exif_info


def new_file(file_name, file_type='', exif_time=0, exif_info=None, exif_lalo=None):
    timestamp = RGTimeUtil.timestamp()

    sql = "INSERT INTO `file` (file_name, type, exif_timestamp, `timestamp`, `exif_info`, `exif_lalo`) VALUES \
          (%(file_name)s, %(file_type)s, %(exif_time)s, %(timestamp)s, %(exif_info)s, %(exif_lalo)s)"
    result, count, new_id = dao.execute_sql(sql, neednewid=True, args={
        'file_name': file_name,
        'file_type': file_type,
        'exif_time': exif_time,
        'timestamp': timestamp,
        'exif_info': exif_info,
        'exif_lalo': exif_lalo,
    })
    if count > 0:
        file_id = new_id
    else:
        file_id = -1
    return RGFile(file_id, file_name, file_type, exif_time, timestamp, exif_lalo, exif_info)


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

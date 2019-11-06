# -*- coding: utf-8 -*-
# @Time    : 2018/11/4 14:46
# @Author  : Renge
# @Email   : lidrkuft123@163.com
# @File    : models.py
# @Software: PyCharm
from datetime import datetime

from flask import Flask, json
from sqlalchemy import create_engine, Column, BigInteger, String, Text, Integer, TIMESTAMP
from sqlalchemy.databases import mysql
from sqlalchemy.ext.declarative import declarative_base

with open('rg_database.json', 'r') as f:
    config = json.loads(f.read())

DB_URI = "mysql+pymysql://{user}:{passwd}@{host}:{port}/{database}?charset={charset}".format(**config)
engine = create_engine(DB_URI)
Base = declarative_base(engine)

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:A_n20071214@localhost:3306/rg_database"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

# db = SQLAlchemy(app)

"""
用户表：
0.编号
1.账号
2.密码
3.注册的时间
"""

# utf8mb4_0900_as_cs 区分大小写
# ALTER TABLE art MODIFY create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP; 取消时间戳自动更新
class User(Base):
    __tablename__ = "user"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_as_cs'}

    id = Column(BigInteger, primary_key=True, comment='user id', autoincrement=True)
    username = Column(String(30), nullable=False, default='', unique=True, comment='login id')

    pwd = Column(String(100), nullable=False, comment='MD5 32')

    nickname = Column(String(50), nullable=True, default='', comment='nickname')
    title = Column(String(50), nullable=True, default='', comment='title')
    description = Column(String(1000), nullable=True, default='', comment='user desc')
    icon = Column(BigInteger, nullable=True, default='', comment='icon')
    bg_image = Column(BigInteger, nullable=True, default='', comment='blog background image')
    style = Column(Text, nullable=True, default='', comment='css style')

    tag = Column(String(20), nullable=True, default='', comment='tag')
    default_album_id = Column(BigInteger, nullable=False, default='', comment='default album')

    addtime = Column(BigInteger, nullable=False, comment='ms')

    info_payload = Column(mysql.LONGTEXT, nullable=True, default='', comment='user info')

    is_active = Column(mysql.TINYINT, nullable=True, default=1, comment='wait for check email')
    is_delete = Column(mysql.TINYINT, nullable=False, default=0)



class user_relation(Base):
    __tablename__ = "user_relation"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    m_user_id = Column(BigInteger, primary_key=True, comment='my id')
    o_user_id = Column(BigInteger, primary_key=True, comment='other id')

    relation = Column(Integer, nullable=False, comment='0 none, 1 follow, 100 friend, -100 block')
    addtime = Column(BigInteger, nullable=False, comment='ms')


"""
token表：
0.user_id
1.token
2.type
4.timestamp
"""


class tokens(Base):
    __tablename__ = "tokens"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    user_id = Column(BigInteger, primary_key=True, comment='user id')
    type = Column(Integer, primary_key=True, comment='web, mobile, pad')

    token = Column(String(100), nullable=False, comment='token')
    timestamp = Column(BigInteger, nullable=False, comment='ms')


"""
文章表
1.编号
2.标题
3.分类
4.作者
5.封面
6.内容
7.发布时间
"""


class Art(Base):
    __tablename__ = "art"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    title = Column(String(100), nullable=False)
    summary = Column(String(100), nullable=False, comment='short view')

    cate = Column(Integer, nullable=False, comment='0 all people, 1 friend and self, 2 only self')

    user_id = Column(BigInteger, nullable=False)

    group_id = Column(BigInteger, nullable=True)

    cover = Column(mysql.TEXT, nullable=True)

    content = Column(mysql.LONGTEXT, nullable=True)

    addtime = Column(BigInteger, nullable=False, comment='ms')
    updatetime = Column(BigInteger, nullable=False, comment='ms')
    create_time = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=None)
    read_count = Column(BigInteger, nullable=False, default=0)


"""
文章组
"""


class ArtGroup(Base):
    __tablename__ = "art_group"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    name = Column(String(100), nullable=False)

    user_id = Column(BigInteger)

    level = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False, comment='order like: 0,1,2,3,4')


"""
log表
"""


class log(Base):
    __tablename__ = "log"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    label = Column(String(100), nullable=False)
    level = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(String(30), nullable=False)


"""
图片表

id
用户id
相册id, 默认为0
文件id

图片名称
图片描述
可见等级

"""


class pic(Base):
    __tablename__ = "pic"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(BigInteger, nullable=False)
    album_id = Column(BigInteger, default=0)

    file_id = Column(BigInteger, primary_key=True)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    level = Column(Integer, nullable=True, comment='0 all people, 1 friend and self, 2 only self')


"""
相簿表
"""


class album(Base):
    __tablename__ = "album"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(BigInteger, nullable=False)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    cover = Column(BigInteger, nullable=True, comment='cover')
    level = Column(Integer, nullable=True, comment='0 all people, 1 friend and self, 2 only self')

    timestamp = Column(BigInteger, nullable=False)


"""
文件表
"""


class file(Base):
    __tablename__ = "file"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(BigInteger, primary_key=True)
    file_name = Column(Text, nullable=False)
    type = Column(String(20), comment='image/jpg')

    exif_timestamp = Column(BigInteger, nullable=True)
    timestamp = Column(BigInteger, nullable=False)
    exif_info = Column(Text, nullable=True, comment='EXIF original json info')
    exif_lalo = Column(String(50), nullable=True, comment='EXIF gps position')


if __name__ == "__main__":
    Base.metadata.create_all()

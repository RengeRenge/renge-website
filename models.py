# -*- coding: utf-8 -*-
# @Time    : 2018/11/4 14:46
# @Author  : Renge
# @Email   : lidrkuft123@163.com
# @File    : models.py
# @Software: PyCharm
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.databases import mysql

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:A_n20071214@localhost:3306/rg_database"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)

"""
用户表：
0.编号
1.账号
2.密码
3.注册的时间
"""


class User(db.Model):
    __tablename__ = "user"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, comment='user id', autoincrement=True)
    username = db.Column(db.String(30), nullable=False, default='', unique=True, comment='login id')

    pwd = db.Column(db.String(100), nullable=False, comment='MD5 32')

    nickname = db.Column(db.String(50), nullable=True, default='', comment='nickname')
    title = db.Column(db.String(50), nullable=True, default='', comment='title')
    description = db.Column(db.String(1000), nullable=True, default='', comment='user desc')
    icon = db.Column(db.BigInteger, nullable=True, default='', comment='icon')
    bg_image = db.Column(db.BigInteger, nullable=True, default='', comment='blog background image')
    style = db.Column(db.Text, nullable=True, default='', comment='css style')

    tag = db.Column(db.String(20), nullable=True, default='', comment='tag')
    default_album_id = db.Column(db.BigInteger, nullable=False, default='', comment='default album')

    addtime = db.Column(db.BigInteger, nullable=False, comment='ms')

    def __repr__(self):
        return "<User %r>" % self.name


class user_relation(db.Model):
    __tablename__ = "user_relation"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    m_user_id = db.Column(db.BigInteger, primary_key=True, comment='my id')
    o_user_id = db.Column(db.BigInteger, primary_key=True, comment='other id')

    relation = db.Column(db.Integer, nullable=False, comment='0 none, 1 follow, 100 friend, -100 block')
    addtime = db.Column(db.BigInteger, nullable=False, comment='ms')

    def __repr__(self):
        return "<User %r>" % self.name


"""
token表：
0.user_id
1.token
2.type
4.timestamp
"""


class tokens(db.Model):
    __tablename__ = "tokens"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    user_id = db.Column(db.BigInteger, primary_key=True, comment='user id')
    type = db.Column(db.Integer, primary_key=True, comment='web, mobile, pad')

    token = db.Column(db.String(100), nullable=False, comment='token')
    timestamp = db.Column(db.BigInteger, nullable=False, comment='ms')

    def __repr__(self):
        return "<User %r>" % self.name


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


class Art(db.Model):
    __tablename__ = "art"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    title = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.String(100), nullable=False, comment='short view')

    cate = db.Column(db.Integer, nullable=False, comment='0 all people, 1 friend and self, 2 only self')

    user_id = db.Column(db.BigInteger, nullable=False)

    group_id = db.Column(db.BigInteger, nullable=True)

    cover = db.Column(mysql.TEXT, nullable=True)

    content = db.Column(mysql.LONGTEXT, nullable=True)

    addtime = db.Column(db.BigInteger, nullable=False, comment='ms')
    updatetime = db.Column(db.BigInteger, nullable=False, comment='ms')
    create_time = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "<User %r>" % self.title


"""
文章组
"""


class ArtGroup(db.Model):
    __tablename__ = "art_group"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.BigInteger)

    level = db.Column(db.Integer, nullable=False)
    order = db.Column(db.Integer, nullable=False, comment='order like: 0,1,2,3,4')

    def __repr__(self):
        return "<User %r>" % self.title


"""
log表
"""


class log(db.Model):
    __tablename__ = "log"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    label = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return "<User %r>" % self.title


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


class pic(db.Model):
    __tablename__ = "pic"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    user_id = db.Column(db.BigInteger, nullable=False)
    album_id = db.Column(db.BigInteger, default=0)

    file_id = db.Column(db.BigInteger, primary_key=True)

    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, nullable=True, comment='0 all people, 1 friend and self, 2 only self')

    def __repr__(self):
        return "<User %r>" % self.title


"""
相簿表
"""


class album(db.Model):
    __tablename__ = "album"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    user_id = db.Column(db.BigInteger, nullable=False)

    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    cover = db.Column(db.BigInteger, nullable=True, comment='cover')
    level = db.Column(db.Integer, nullable=True, comment='0 all people, 1 friend and self, 2 only self')

    timestamp = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.title


"""
文件表
"""


class file(db.Model):
    __tablename__ = "file"
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = db.Column(db.BigInteger, primary_key=True)
    file_name = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), comment='image/jpg')

    exif_timestamp = db.Column(db.BigInteger, nullable=True)
    timestamp = db.Column(db.BigInteger, nullable=False)

    def __repr__(self):
        return "<User %r>" % self.title


if __name__ == "__main__":
    db.create_all()

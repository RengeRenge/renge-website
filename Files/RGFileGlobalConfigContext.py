#!/usr/bin/env python
# encoding: utf-8
"""
This module maintains runtime configurations.
"""
import os

from RGGlobalConfigContext import RGFullHost

FilePreFix = "file/"
RemoteFileHost = "http://127.0.0.1:5000"


def path_with_name(filename):
    return FilePreFix + filename


def full_path_with_name(filename):
    return RGFullHost + '/' + path_with_name(filename)


def url_with_name(filename, thumb=False, gifThumb=False):
    """
    文件外网访问的路径
    :param filename:文件名
    :param thumb: 是否返回缩略图地址
    :param gifThumb: gif 是否返回缩略图（不会动的）
    :return: 外网访问的 url
    :argument 此处上线时 RGFullHost 要替换成外网访问的域名+端口
    """
    if filename is None:
        return ''
    if thumb:
        (name, extension) = os.path.splitext(filename)
        if extension.endswith('gif'):
            if gifThumb:
                filename = name + '_thumbnail' + extension
        else:
            filename = name + '_thumbnail' + extension

    return RGFullHost + '/' + path_with_name(filename)

#!/usr/bin/env python
# encoding: utf-8
"""
This module maintains runtime configurations.
"""
import os
import urllib.parse

from RGIgnoreConfig.RGGlobalConfigContext import RGDomainName

FilePreFix = "file/"
RemoteFileHost = "http://127.0.0.1:5000"

# RGThumbnailName = '_thumbnail'
# RGQualityName = '_quality'
RGFileMaxCapacity = 5*1024*1024*1024


image_support = [
    'bmp',
    'dib',
    'gif',
    'tiff',
    'tif',
    'jpeg',
    'jpg',
    'jpe',
    'ppm',
    'png',
    'bufr',
    'pcx',
    'eps',
    'fits',
    'grib',
    'hdf5',
    'jpeg2000',
    'ico',
    'im',
    'mpo',
    'msp',
    'palm',
    'pdf',
    'sgi',
    'spider',
    'tga',
    'webp',
    'wmf',
    'xbm'
]


def path_with_name(filename):
    return FilePreFix + filename


# def name_fix(filename, original=False, thumb=False, gif_activity=True):
#     if filename is None:
#         return ''

#     if original is False:
#         (name, extension) = os.path.splitext(filename)
#         temp = (extension.split(sep='.')[-1]).lower()
#         if temp.endswith('gif'):
#             if gif_activity:
#                 filename = name + RGQualityName + extension
#             else:
#                 filename = name + RGThumbnailName + extension
#         elif temp.endswith('webp'):
#             if thumb:
#                 filename = name + RGThumbnailName + extension
#         elif temp in image_support:
#             if thumb:
#                 filename = name + RGThumbnailName + extension
#             else:
#                 filename = name + RGQualityName + extension
#     return filename


def support_image(filename):
    (name, extension) = os.path.splitext(filename)
    extension = (extension.split(sep='.')[-1]).lower()
    return extension in image_support


def url_with_name(filename, original=False, thumb=False, gif_activity=True, needhost=False):
    """
    文件外网访问的路径
    :param filename: 文件名
    :param original: 是否需要原图
    :param thumb: 是否返回缩略图地址
    :param gif_activity: gif 是否返回缩略图（不会动的）, True 代表不需要缩略图
    :param needhost: 是否需要加上主机地址
    :return: 外网访问的 url
    :argument 此处上线时 RGFullHost 要替换成外网访问的域名+端口
    """
    # filename = name_fix(filename=filename, original=original, thumb=thumb, gif_activity=gif_activity)
    params_str = ''
    if original is False:
        params = {'side': 640, 'quality': 'low'}
        extension = os.path.splitext(filename)[-1].split('.')[-1].lower()
        if extension.endswith('gif'):
            if gif_activity:
                params['side'] = 256
                params['quality'] = 'high'
        elif extension in image_support:
            if not thumb:
                params['side'] = 1920
                params['quality'] = 'high'
        params_str = '?' + urllib.parse.urlencode(params)

    if needhost:
        return 'https://' + RGDomainName + '/' + path_with_name(filename) + params_str
    else:
        return '/' + path_with_name(filename) + params_str

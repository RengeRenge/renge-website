# encoding: utf-8
import socket


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    # 获取本机计算机名称
    hostname = socket.gethostname()
    # 获取本机ip
    ip = socket.gethostbyname(hostname)
    return ip


RGNginxHost = get_host_ip()
RGNginxPort = '8080'

RGHost = '0.0.0.0'
RGPort = '12345'

RGFullThisServerHost = 'http://' + RGHost + ":" + RGPort
RGFullHost = 'http://' + RGNginxHost + ":" + RGNginxPort

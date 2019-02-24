#!/usr/bin/env python
# encoding: utf-8

"""
@module : WebUILogModel
@author : Rinkako
@time   : 2018/5/31
"""
import time


class WebUILogModel:
    """
    Model Class: Data model operation for runtime logging of Ren Web UI.
    """

    def __init__(self):
        pass

    @staticmethod
    def LogToSteady(label, level, message, timestamp, dp=0):
        """
        Write log to the runtime steady logging data model.
        :param label: event label
        :param level: event level
        :param message: event description
        :param timestamp: event timestamp
        :param dp: depth of exception stack
        """
        t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        sql = "INSERT INTO log(label, level, message, timestamp) VALUES \
        (%(label)s, %(level)s, %(message)s, %(t)s)"
        from DAO import rg_dao as dao
        dao.execute_sql(sql=sql, dp=dp, args={
            'label': label,
            'level': level,
            'message': message,
            't': t
        })

    @staticmethod
    def LogError(label, message, timestamp=None):
        """
        Quick log an error event.
        :param label: event label
        :param message: event description
        :param timestamp: event timestamp, current time if None
        """
        if timestamp is None:
            timestamp = time.time()
        WebUILogModel.LogToSteady(label, "Error", message, timestamp)

    @staticmethod
    def LogInformation(label, message, timestamp=None):
        """
        Quick log information event.
        :param label: event label
        :param message: event description
        :param timestamp: event timestamp, current time if None
        """
        if timestamp is None:
            timestamp = time.time()
        WebUILogModel.LogToSteady(label, "Info", message, timestamp)

    @staticmethod
    def LogUnauthorized(label, message, timestamp=None):
        """
        Quick log an unauthorized event.
        :param label: event label
        :param message: event description
        :param timestamp: event timestamp, current time if None
        """
        if timestamp is None:
            timestamp = time.time()
        WebUILogModel.LogToSteady(label, "Unauthorized", message, timestamp)

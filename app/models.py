# -*- coding:utf-8 -*-
import datetime
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from logging.config import dictConfig
import logging
from datetime import datetime
from math import pow


# 乐器
# author:hyb


class Instrument:
    def __init__(self, instrument_id, name, price, weight, description, transportation, imagePath):
        self.__id = instrument_id
        self.__Name = name
        self.__Price = price
        self.__Weight = weight
        self.__Description = description
        self.__Transportation = transportation
        self.__ImagePath = imagePath

    def getId(self):
        return self.__id

    def getName(self):
        return self.__Name

    def getPrice(self):
        return self.__Price

    def getWeight(self):
        return self.__Weight

    def getDescription(self):
        return self.__Description

    def getTransportation(self):
        return self.__Transportation

    def getImagePath(self):
        return self.__ImagePath

    def saveToDb(self):
        from .dbConnect import get_cursor
        cur = get_cursor()
        try:
            cur.execute('''INSERT INTO instrument(id,name,price,weight,description,
                                transportation_cost,image_path) VALUES(%s,%s,%s,%s,%s,%s,%s)''',
                        (self.__id, self.__Name, self.__Price, self.__Weight, self.__Description, self.__Transportation,
                         self.__ImagePath))
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "<'class:Instrument'>func_saveToDb:An error occurred while writing to the database instrument:%s" % e)
            return False
        else:
            cur.connection.commit()
            return True

    def modify(self):
        from .dbConnect import get_cursor
        cur = get_cursor()
        try:
            cur.execute('''UPDATE instrument SET name = %s,price = %s,weight = %s,description = %s,
                            transportation_cost = %s,image_path = %s WHERE id = %s''',
                        (self.__Name, self.__Price, self.__Weight, self.__Description, self.__Transportation,
                         self.__ImagePath, self.__id))
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "<'class:Instrument'>func_modify:An error occurred while writing to the database instrument:%s" % e)
            return False
        else:
            cur.connection.commit()
            return True


# 购物车
# author:hyb
class ShoppingCraft:
    def __init__(self, *args):
        self.__Instruments = list(args)
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])

    def getAllInstruments(self):
        return self.__Instruments

    def getTotalPrice(self):
        return self.__TotalPrice

    def pay(self, user_id, *args):
        pass

    def payAll(self, user_id):
        from .dbConnect import get_cursor
        curr = get_cursor()
        now = datetime.now()
        orderId = int(str((int(now.timestamp() * pow(10, 6))))[-8:])
        try:
            curr.execute('''INSERT INTO `order`(id,datetime,totalprice) VALUES(%s,%s,%s)''',
                         (orderId, now, self.__TotalPrice))
            curr.execute('''INSERT INTO user_order(user_id,order_id) VALUES(%s,%s)''', (user_id, orderId))
            for instrument in self.__Instruments:
                curr.execute('''INSERT INTO instrument_order(instrument_id,order_id) VALUES(%s,%s)''',
                             (instrument.getId(), orderId))
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "<'class:ShoppingCraft'>func_payAll:An error occurred while writing to the database:%s" % e)
            return False
        else:
            curr.connection.commit()
            return orderId

    def add(self, *args):
        for instrument in args:
            self.__Instruments.append(instrument)
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])

    def remove(self, *args):
        pass

    def removeAll(self):
        pass


# 订单
# author:hyb
class Order:
    def __init__(self, *args):
        self.__Instruments = list(args)
        self.__DateTime = datetime.datetime.now()
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])

    def getAllInstruments(self):
        return self.__Instruments

    def getDateTime(self):
        return self.__DateTime

    def getTotalPrice(self):
        return self.__TotalPrice


# 用户
# author:hyb
class User:
    def __init__(self, username, password):
        self.__username = username
        self.__password_hash = generate_password_hash(password)
        self.__shoppingCraft = ShoppingCraft()

    def getUsername(self):
        return self.__username

    def getId(self):
        from .dbConnect import get_cursor
        curr = get_cursor()
        curr.execute('SELECT id FROM user WHERE username = "%s"', self.__username)
        return curr.fetchone()[0]

    def payShoppingCraft(self, *args):
        return self.__shoppingCraft.pay(user_id=self.getId(), *args)

    def payAllShoppingCraft(self):
        return self.__shoppingCraft.payAll(user_id=self.getId())

    def addInstrumentToShoppingCraft(self, *args):
        self.__shoppingCraft.add(*args)

    def removeShoppingCraft(self, *args):
        self.__shoppingCraft.remove(*args)

    def removeAllShoppingCraft(self):
        self.__shoppingCraft.removeAll()

    def saveToDb(self, user_id=None):
        from .dbConnect import get_cursor
        cur = get_cursor()
        try:
            if user_id:
                cur.execute('INSERT INTO user(id,username,password_hash) VALUES(%s,"%s","%s")'
                            , (user_id, self.__username, self.__password_hash))
            else:
                cur.execute('INSERT INTO user(username,password_hash) VALUES("%s","%s")'
                            , (self.__username, self.__password_hash))
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "<'class:User'>saveToDb:An error occurred while writing to the database:%s" % e)
            return False
        else:
            cur.connection.commit()
            return True

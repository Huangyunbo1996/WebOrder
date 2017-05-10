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

    @staticmethod
    def removeFromDb(id):
        from .dbConnect import get_cursor
        curr = get_cursor()
        try:
            curr.execute('UPDATE instrument SET deleted=true WHERE id=%s', id)
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "page_instrumentDelete:An error occurred while writing to the database instrument:%s" % e)
            return False
        else:
            curr.connection.commit()
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
    def __init__(self, id, args):
        self.__Instruments = args
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])
        self.__Id = id

    def getAllInstruments(self):
        return self.__Instruments

    def getTotalPrice(self):
        return self.__TotalPrice

    def pay(self, user_id, args):
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

    def add(self, args):
        for instrument in args:
            self.__Instruments.append(instrument)
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])
        self.saveToDb()

    def remove(self, args):
        for instrument in args:
            self.__Instruments.pop(self.__Instruments.index(instrument))
        self.__TotalPrice = sum([instrument.getPrice()
                                 for instrument in self.__Instruments])
        self.saveToDb()

    def removeAll(self):
        self.__Instruments = list()
        self.__TotalPrice = 0
        self.saveToDb()

    def saveToDb(self):
        from .dbConnect import get_cursor
        curr = get_cursor()
        try:
            curr.execute('''SELECT instrument_id FROM shoppingcraft_instrument
                            WHERE shoppingcraft_id=%s''', self.__Id)
            all_in_database_instrument_id = curr.fetchall()
            all_in_database_instrument_id = [instrument_id for instrument_id in all_in_database_instrument_id]
            all_in_self_instrument_id = [instrument.getId() for instrument in self.__Instruments]
            all_in_database_instrument_id_set = set(all_in_database_instrument_id)
            all_in_self_instrument_id_set = set(all_in_self_instrument_id)
            # 在数据库中的数据而不在本类中的数据说明是要删除的数据
            # 在本类中的数据而不在数据库中的数据说明时要添加的数据
            need_save_to_database = all_in_self_instrument_id_set - all_in_database_instrument_id_set
            need_remove_to_database = all_in_database_instrument_id_set - all_in_self_instrument_id_set
            for instrument_id in need_save_to_database:
                curr.execute('''INSERT INTO shoppingcraft_instrument(shoppingcraft_id,instrument_id)
                                VALUES(%s,%s)''', (self.__Id, instrument_id))
            for instrument_id in need_remove_to_database:
                curr.execute('''DELETE FROM shoppingcraft_instrument WHERE
                                shoppingcraft_id=%s AND instrument_id=%s''', self.__Id, instrument_id)
        except Exception as e:
            dictConfig(current_app.config['LOGGING_CONFIG'])
            logger = logging.getLogger()
            logger.error(
                "<'class:ShoppingCraft'>func_saveToDb:An error occurred while writing to the database:%s" % e)
            return False
        else:
            curr.connection.commit()
            return True


# 订单
# author:hyb
class Order:
    def __init__(self, args):
        self.__Instruments = args
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
    def __init__(self, username, password, id=None):
        self.__username = username
        self.__password_hash = generate_password_hash(password)
        self.__id = id

        # 获取改用或购物车下所有商品，用来初始化购物车
        from .dbConnect import get_cursor
        curr = get_cursor()
        curr.execute('SELECT id FROM user WHERE username = "%s"', self.__username)
        this_user = curr.fetchone()
        # 如果user_id为空，则代表该用户还没有储存进数据库中，那么就需要对该用户进行存储
        if this_user == None:
            if self.__id == None:
                self.saveToDb()
            else:
                self.saveToDb(self.__id)
            try:
                curr.execute('INSERT INTO shopping_craft(user_id) VALUES(%s)',self.getId())
            except Exception as e:
                dictConfig(current_app.config['LOGGING_CONFIG'])
                logger = logging.getLogger()
                logger.error(
                    "<'class:User'>__init__:An error occurred while writing to the database:%s" % e)
            else:
                curr.connection.commit
        else:
            if this_user[0] != self.__id:
                raise ValueError('该用户在数据库中存储的ID值与传入的ID值不一致。')
        curr.execute('SELECT id FROM shopping_craft WHERE user_id=%s', self.getId())
        craft_id = curr.fetchone()[0]
        curr.execute('''SELECT st.instrument_id FROM user LEFT JOIN shopping_craft
                        ON user.id=shopping_craft.user_id LEFT JOIN shoppingcraft_instrument as st
                        ON shopping_craft.id=st.shoppingcraft_id WHERE user.id=%s''', self.getId())
        instruments_ids = [x for x in curr.fetchall() if x != (None,)]
        instruments = list()
        if instruments_ids:
            for instrument_id in instruments_ids:
                curr.execute('SELECT * FROM instrument WHERE id=%s and deleted=false', instrument_id[0])
                this_instrument_data = curr.fetchone()
                this_instrument = Instrument(this_instrument_data[0], this_instrument_data[1], this_instrument_data[2],
                                             this_instrument_data[3], this_instrument_data[4], this_instrument_data[5],
                                             this_instrument_data[6])
                instruments.append(this_instrument)
        self.__shoppingCraft = ShoppingCraft(craft_id, instruments)

    def getUsername(self):
        return self.__username

    def getId(self):
        if self.__id != None:
            return self.__id
        else:
            from .dbConnect import get_cursor
            curr = get_cursor()
            curr.execute('SELECT id FROM user WHERE username = "%s"', self.__username)
            return curr.fetchone()[0]

    def payShoppingCraft(self, args):
        return self.__shoppingCraft.pay(args, user_id=self.getId())

    def payAllShoppingCraft(self):
        return self.__shoppingCraft.payAll(user_id=self.getId())

    def addInstrumentToShoppingCraft(self, args):
        self.__shoppingCraft.add(args)

    def removeShoppingCraft(self, args):
        self.__shoppingCraft.remove(args)

    def removeAllShoppingCraft(self):
        self.__shoppingCraft.removeAll()

    def saveToDb(self, user_id=None):
        from .dbConnect import get_cursor
        cur = get_cursor()
        cur.execute('SELECT id FROM user WHERE username="%s"', self.__username)
        # 如果这个用户已经在数据库中了，就不需要再次进行存储。
        if not cur.fetchone():
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
        return True
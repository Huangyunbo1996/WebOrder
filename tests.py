import unittest
from os.path import join, dirname, abspath
from os import environ, system
from app import create_app
from flask import session
from werkzeug.security import check_password_hash
import requests
import pymysql
import threading
import time


def init_db(sql_file_path):
    command = 'mysql -uroot -p' + environ.get('mysql_password') + '< ' + sql_file_path
    try:
        system(command)
    except BaseException as e:
        print(e)
        return False
    else:
        return True


class WebOrderTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        import logging
        logger = logging.getLogger('werkzeug')
        logger.setLevel('ERROR')

        init_db(join(dirname(abspath(__file__)), 'Instruments_test.sql'))

        threading.Thread(target=cls.app.run).start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):

        # delete testing database
        conn = pymysql.Connect(**cls.app.config['MYSQL_CONNECT_ARGS'])
        curr = conn.cursor()
        curr.execute('drop database weborder_test')
        curr.close()
        conn.close()

        cls.app_context.pop()

    def setUp(self):
        self.conn = pymysql.Connect(**self.app.config['MYSQL_CONNECT_ARGS'])
        self.curr = self.conn.cursor()
        self.curr.execute('use weborder_test')

    def tearDown(self):
        self.curr.close()
        self.conn.close()

    def test_home_page(self):
        recive = requests.get('http://localhost:5000/')
        self.assertTrue('乐器销售网站' in recive.text)

    def test_register_page(self):
        recive = requests.post('http://localhost:5000/register', data=dict(username='testuser',
                                                          password='password_test',
                                                          re_password='password_test'))
        assert '注册' not in recive.text
        #assert session['logined'] == True and session['username'] == 'testuser'
        self.curr.execute('select password_hash from user where username = "\'testuser\'"')
        password_hash = self.curr.fetchone()
        assert password_hash is not None and \
               check_password_hash(password_hash[0].strip('\''), 'password_test') is True

        recive = requests.post('http://localhost:5000/register', data=dict(username='testuser2',
                                                          password='password_test',
                                                          re_password='password_not_repeat'))
        assert '重复密码与密码不一致' in recive.text

        recive = requests.post('http://localhost:5000/register', data=dict(username='testuser',
                                                          password='password_test',
                                                          re_password='password_test'))
        assert '此用户名已被占用' in recive.text


if __name__ == '__main__':
    unittest.main()
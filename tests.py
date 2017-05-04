import unittest
from os.path import join, dirname, abspath
from os import environ, system
from app import create_app
from flask import session,request
from werkzeug.security import check_password_hash
import pymysql


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
    def setUp(self):
        app = create_app('testing')
        self.app = app.test_client()
        self.conn = pymysql.Connect(**app.config['MYSQL_CONNECT_ARGS'])
        self.curr = self.conn.cursor()
        if not init_db(join(dirname(abspath(__file__)), 'Instruments_test.sql')):
            print('测试数据库初始化失败。')
            exit(0)

    def tearDown(self):
        self.curr.close()
        self.conn.close()

    def test_index(self):
        recive = self.app.get('main.index')
        assert '乐器销售网'.encode('utf-8') in recive.data

    def test_register(self):
        recive = self.app.post('/register', data=dict(username='testuser',
                                                          password='password_test',
                                                          re_password='password_test'))
        assert '注册'.encode('utf-8') not in recive.data
        #assert session['logined'] == True and session['username'] == 'testuser'
        self.curr.execute('select password_hash from user where username = "testuser"')
        password_hash = self.curr.fetchone()
        assert password_hash is not None and \
               check_password_hash(password_hash[0].strip('\''), 'password_test') is True

        recive = self.app.post('/register', data=dict(username='testuser2',
                                                          password='password_test',
                                                          re_password='password_not_repeat'))
        assert '重复密码与密码不一致'.encode('utf-8') in recive.data

        recive = self.app.post('/register', data=dict(username='testuser',
                                                          password='password_test',
                                                          re_password='password_test'))
        assert '此用户名已被占用'.encode('utf-8') in recive.data


if __name__ == '__main__':
    unittest.main()
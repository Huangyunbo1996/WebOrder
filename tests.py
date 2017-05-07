import unittest
from os.path import join, dirname, abspath
from os import environ, system
from app import create_app
from werkzeug.security import check_password_hash
from app.models import User, Instrument, Order
from flask import session, current_app
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

    # 测试主页访问
    def test_home_page(self):
        c = self.app.test_client()
        response = c.get('/', follow_redirects=True)
        assert '乐器销售网站'.encode('utf-8') in response.data

    def test_register_page(self):
        # 测试注册成功
        c = self.app.test_client()
        with self.app.app_context():
            response = c.post('/register', data=dict(username='testregisteruser',
                                                     password='password_test',
                                                     re_password='password_test'), follow_redirects=True)
            assert '注册'.encode('utf-8') not in response.data and '乐器销售网站'.encode('utf-8') in response.data

        # 测试注册用户密码是否被正确加密储存
        self.curr.execute('select password_hash from user where username = "\'testregisteruser\'"')
        password_hash = self.curr.fetchone()
        assert password_hash is not None and \
               check_password_hash(password_hash[0].strip('\''), 'password_test') is True

        # 测试密码与重复密码不一致时的注册
        with self.app.app_context():
            response = c.post('/register', data=dict(username='testuser2',
                                                     password='password_test',
                                                     re_password='password_not_repeat'), follow_redirects=True)
            assert '重复密码与密码不一致'.encode('utf-8') in response.data

        # 测试注册用户名已被注册时的注册
        with self.app.app_context():
            response = c.post('/register', data=dict(username='testregisteruser',
                                                     password='password_test',
                                                     re_password='password_test'), follow_redirects=True)
            assert '此用户名已被占用'.encode('utf-8') in response.data

    def test_login_page(self):
        with self.app.app_context():
            newUser = User('testloginuser', 'testpassword')
            newUser.saveToDb()

        # 测试密码错误的登录
        c = self.app.test_client()
        with self.app.app_context():
            response = c.post('/login', data=dict(username='testloginuser',
                                                  password='faultpassword'
                                                  ), follow_redirects=True)
            assert '用户名或密码错误，请重试。'.encode('utf-8') in response.data

        # 测试密码正确的登录
        with self.app.app_context():
            response = c.post('/login', data=dict(username='testloginuser',
                                                  password='testpassword'
                                                  ), follow_redirects=True)
            assert '登录'.encode('utf-8') not in response.data and '乐器销售网站'.encode('utf-8') in response.data

    def test_admin_page(self):
        # 测试没有登录管理员账号时访问管理页面
        c = self.app.test_client()
        response = c.get('/admin', follow_redirects=True)
        assert '管理员登录'.encode('utf-8') in response.data

        # 测试用错误的账号登录管理员页面
        c = self.app.test_client()
        response = c.post('/adminLogin', data=dict(username='fault', password='fault'), follow_redirects=True)
        assert '账号或密码错误。'.encode('utf-8') in response.data

        # 测试用正确的账号登录管理员页面
        c = self.app.test_client()
        response = c.post('/adminLogin', data=dict(
            username=environ.get('weborder_admin_username'),
            password=environ.get('weborder_admin_password')), follow_redirects=True)
        assert '后台管理'.encode('utf-8') in response.data

    def test_instrumentEdit_page(self):
        with self.app.app_context():
            testInstrument1 = Instrument("测试乐器1", 100, 200, "测试描述", 10, "测试图片")
            testInstrument1.saveToDb()

            testInstrument2 = Instrument("测试乐器2", 100, 200, "测试描述", 10, "测试图片")
            testInstrument2.saveToDb()

        # 测试在没有管理员权限时访问该页面
        c = self.app.test_client()
        with self.app.app_context():
            response = c.get('/instrumentEdit/1', follow_redirects=True)
            assert '管理员登录'.encode('utf-8') in response.data

        # 测试有管理员权限时访问不存在的商品页面
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/3')
            assert '404'.encode('utf-8') in response.data

        # 测试有管理员权限时访问存在的商品页面
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/1')
            assert '乐器信息编辑'.encode('utf-8') in response.data

        # 测试想要编辑的乐器是否能正确的在页面上显示
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/1')
            assert '测试乐器1'.encode('utf-8') in response.data
            response = c.get('/instrumentEdit/2')
            assert '测试乐器2'.encode('utf-8') in response.data

        # 测试能否正确修改乐器信息
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.post('/instrumentEdit/1', data=dict(name='测试乐器3', price=100, weight=200,
                                                             description='测试描述', transport_cost=300,
                                                             image='测试图片'), follow_redirects=True)
            self.curr.execute('SELECT name FROM instrument WHERE id = 1')
            instrument_edited_name = self.curr.fetchone()[0]
            assert instrument_edited_name == '测试乐器3' and '后台管理'.encode('utf-8') in response.data


if __name__ == '__main__':
    unittest.main()

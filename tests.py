import unittest
from os.path import join, dirname, abspath
from os import environ, system
from app import create_app
from werkzeug.security import check_password_hash
from app.models import User, Instrument, Order
from flask import session, current_app
from app.decorators import print_func_info
import pymysql
import threading
import time
from datetime import datetime
from random import randint


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
        with self.app.test_client():
            test_instrument_1_id = self.generate_random_instrument_id()
            test_instrument_1 = Instrument(test_instrument_1_id, '测试乐器1', 100, 10, '测试描述', 5, 'image_path')
            test_instrument_1.saveToDb()
            test_instrument_2_id = self.generate_random_instrument_id()
            test_instrument_2 = Instrument(test_instrument_2_id, '测试乐器2', 100, 10, '测试描述', 5, 'image_path')
            test_instrument_2.saveToDb()
            Instrument.removeFromDb(test_instrument_2_id)

        c = self.app.test_client()
        response = c.get('/', follow_redirects=True)
        assert '乐器销售网站'.encode('utf-8') in response.data
        assert '测试乐器1'.encode('utf-8') in response.data
        assert '测试乐器2'.encode('utf-8') not in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

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
        with self.app.test_client():
            test_instrument_1_id = self.generate_random_instrument_id()
            test_instrument_1 = Instrument(test_instrument_1_id, '测试乐器1', 100, 10, '测试描述', 5, 'image_path')
            test_instrument_1.saveToDb()
            test_instrument_2_id = self.generate_random_instrument_id()
            test_instrument_2 = Instrument(test_instrument_2_id, '测试乐器2', 100, 10, '测试描述', 5, 'image_path')
            test_instrument_2.saveToDb()

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

        # 测试删除功能
        c = self.app.test_client()
        with self.app.app_context():
            response = c.post('/adminLogin', data=dict(
                username=environ.get('weborder_admin_username'),
                password=environ.get('weborder_admin_password')), follow_redirects=True)
            delete_url = '/instrumentDelete/' + str(test_instrument_2_id)
            response = c.get(delete_url, follow_redirects=True)
            assert '测试乐器1'.encode('utf-8') in response.data
            assert '测试乐器2'.encode('utf-8') not in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_instrumentEdit_page(self):
        with self.app.app_context():
            testInstrument1 = Instrument(111, "测试乐器111", 100, 200, "测试描述", 10, "测试图片")
            testInstrument1.saveToDb()

            testInstrument2 = Instrument(222, "测试乐器222", 100, 200, "测试描述", 10, "测试图片")
            testInstrument2.saveToDb()

        # 测试在没有管理员权限时访问该页面
        c = self.app.test_client()
        with self.app.app_context():
            response = c.get('/instrumentEdit/111', follow_redirects=True)
            assert '管理员登录'.encode('utf-8') in response.data

        # 测试有管理员权限时访问不存在的商品页面
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/100')
            assert '404'.encode('utf-8') in response.data

        # 测试有管理员权限时访问存在的商品页面
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/111')
            assert '乐器信息编辑'.encode('utf-8') in response.data

        # 测试想要编辑的乐器是否能正确的在页面上显示
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/111')
            assert '测试乐器111'.encode('utf-8') in response.data
            response = c.get('/instrumentEdit/222')
            assert '测试乐器222'.encode('utf-8') in response.data

        # 测试能否正确修改乐器信息
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.post('/instrumentEdit/111', data=dict(name='测试乐器333', price=100, weight=200,
                                                               description='测试描述', transport_cost=300,
                                                               image='测试图片'), follow_redirects=True)
            self.curr.execute('SELECT name FROM instrument WHERE id = 111')
            instrument_edited_name = self.curr.fetchone()[0]
            assert instrument_edited_name == '测试乐器333' and '后台管理'.encode('utf-8') in response.data

        # 测试能否访问已被删除的商品编辑页面
        c = self.app.test_client()
        with self.app.app_context():
            Instrument.removeFromDb(222)
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/instrumentEdit/222', follow_redirects=True)
            assert '404'.encode('utf-8') in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_addInstrument_page(self):
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))

            # 测试是否能添加正确的乐器信息
            response = c.post('/addInstrument', data=dict(name='测试乐器', price=100, weight=200,
                                                          description='测试描述', transport_cost=300,
                                                          image='测试图片'), follow_redirects=True)
            assert '测试乐器'.encode('utf-8') in response.data

            # 测试是否能指出不合规的数据
            response = c.post('/addInstrument', data=dict(name='测试乐器2', price='错误数据', weight='错误数据',
                                                          description='测试描述', transport_cost='错误数据',
                                                          image='测试图片'), follow_redirects=True)
            assert '请输入正确的价格'.encode('utf-8') in response.data and \
                   '请输入正确的重量'.encode('utf-8') in response.data and \
                   '请输入正确的运输费用'.encode('utf-8') in response.data

    def test_allUser_page(self):
        with self.app.app_context():
            testuser1 = User('allUser_testuser_1', 'testpassword', id=66)
            testuser2 = User('allUser_testuser_2', 'testpassword', id=666)

        # 测试能否显示所有用户
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/allUser')
            assert 'allUser_testuser_1'.encode('utf-8') in response.data and \
                   'allUser_testuser_2'.encode('utf-8') in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table user')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_historyOrder_page(self):
        with self.app.app_context():
            testuser1 = User('historyOrder_testuser_1', 'testpassword', id=66)
            testuser2 = User('historyOrder_testuser_2', 'testpassword', id=666)
            instrument1 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器1', 100, 200, '测试描述1', 300, 'imagepath')
            instrument1.saveToDb()
            instrument2 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器2', 200, 200, '测试描述2', 300, 'imagepath')
            instrument2.saveToDb()
            instrument3 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器3', 300, 200, '测试描述3', 300, 'imagepath')
            instrument3.saveToDb()
            instruments = [instrument1, instrument2]
            testuser1.addInstrumentToShoppingCraft(instruments)
            order1_id = testuser1.payAllShoppingCraft()
            instruments = [instrument1, instrument3]
            testuser2.addInstrumentToShoppingCraft(instruments)
            order2_id = testuser2.payAllShoppingCraft()
            self.curr.execute("select totalprice from `order` where id=%s", order1_id)
            order1_totalprice = self.curr.fetchone()[0]
            self.curr.execute("select totalprice from `order` where id=%s", order2_id)
            order2_totalprice = self.curr.fetchone()[0]

        # 测试历史订单能否正确显示
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/historyOrder/66')
            assert 'historyOrder_testuser_1'.encode('utf-8') in response.data and str(order1_id).encode(
                'utf-8') in response.data and '300'.encode('utf-8') in response.data
            response = c.get('/historyOrder/666')
            assert 'historyOrder_testuser_2'.encode('utf-8') in response.data and str(order2_id).encode(
                'utf-8') in response.data and '400'.encode('utf-8') in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table user;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('truncate table `order`;')
        self.curr.execute('truncate table shopping_craft;')
        self.curr.execute('truncate table shoppingcraft_instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_allOrder_page(self):
        with self.app.app_context():
            testuser1 = User('historyOrder_testuser_1', 'testpassword', id=66)
            testuser2 = User('historyOrder_testuser_2', 'testpassword', id=666)
            instrument1 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器1', 100, 200, '测试描述1', 300, 'imagepath')
            instrument1.saveToDb()
            instrument2 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器2', 200, 200, '测试描述2', 300, 'imagepath')
            instrument2.saveToDb()
            instrument3 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器3', 300, 200, '测试描述3', 300, 'imagepath')
            instrument3.saveToDb()
            instruments = [instrument1, instrument2]
            testuser1.addInstrumentToShoppingCraft(instruments)
            order1_id = testuser1.payAllShoppingCraft()
            instruments = [instrument1, instrument3]
            testuser2.addInstrumentToShoppingCraft(instruments)
            order2_id = testuser2.payAllShoppingCraft()
            self.curr.execute("select totalprice from `order` where id=%s", order1_id)
            order1_totalprice = self.curr.fetchone()[0]
            self.curr.execute("select totalprice from `order` where id=%s", order2_id)
            order2_totalprice = self.curr.fetchone()[0]

            # 测试能否正确显示所有订单
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            response = c.get('/allOrder')
            assert 'historyOrder_testuser_1'.encode('utf-8') in response.data and \
                   'historyOrder_testuser_2'.encode('utf-8') in response.data and \
                   str(order1_id).encode('utf-8') in response.data and \
                   str(order2_id).encode('utf-8') in response.data and \
                   '300'.encode('utf-8') in response.data and \
                   '400'.encode('utf-8') in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table user;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('truncate table `order`;')
        self.curr.execute('truncate table shopping_craft;')
        self.curr.execute('truncate table shoppingcraft_instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_orderDetail_page(self):
        with self.app.app_context():
            testuser1 = User('orderDetail_testuser_1', 'testpassword', id=66)
            instrument1 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器1', 100, 200, '测试描述1', 300, 'imagepath')
            instrument1.saveToDb()
            instrument2 = Instrument(self.generate_random_instrument_id(),
                                     '测试乐器2', 200, 200, '测试描述2', 300, 'imagepath')
            instrument2.saveToDb()
            instrument3_id = self.generate_random_instrument_id()
            instrument3 = Instrument(instrument3_id,
                                     '测试乐器3', 300, 200, '测试描述3', 300, 'imagepath')
            instrument3.saveToDb()
            instruments = [instrument1, instrument3]
            testuser1.addInstrumentToShoppingCraft(instruments)
            orderId = testuser1.payAllShoppingCraft()
            Instrument.removeFromDb(instrument3_id)
            now = datetime.now()

        c = self.app.test_client()
        with self.app.app_context():
            c.post('/adminLogin', data=dict(username=environ.get('weborder_admin_username'),
                                            password=environ.get('weborder_admin_password')))
            orderDetail_url = '/orderDetail/' + str(orderId)
            response = c.get(orderDetail_url)
            assert str(orderId).encode('utf-8') in response.data
            assert str(now.year).encode('utf-8') in response.data
            assert str(now.day).encode('utf-8') in response.data
            assert 'orderDetail_testuser_1'.encode('utf-8') in response.data
            assert '400'.encode('utf-8') in response.data
            assert '测试乐器1'.encode('utf-8') in response.data
            assert (str(instrument3_id) + '(此商品已下架)').encode('utf-8') in response.data
            assert '测试乐器2'.encode('utf-8') not in response.data

        self.curr.execute('SET FOREIGN_KEY_CHECKS = 0;')
        self.curr.execute('truncate table user;')
        self.curr.execute('truncate table instrument;')
        self.curr.execute('truncate table `order`;')
        self.curr.execute('truncate table shopping_craft;')
        self.curr.execute('truncate table shoppingcraft_instrument;')
        self.curr.execute('SET FOREIGN_KEY_CHECKS = 1;')

    def test_addInstrumentToCraft_page(self):
        with self.app.app_context():
            testuser1 = User('test_add_craft_user_1', 'testpassword')
            instrument1_id = self.generate_random_instrument_id()
            instrument1 = Instrument(instrument1_id, '测试商品1', 100, 200, '测试描述', 100, 'www.test.com')
            instrument1.saveToDb()
            instrument2_id = self.generate_random_instrument_id()
            instrument2 = Instrument(instrument2_id, '测试商品2', 100, 200, '测试描述', 100, 'www.test.com')
            instrument2.saveToDb()

        # 测试能否正确加入购物车
        c = self.app.test_client()
        with self.app.app_context():
            c.post('/login', data=dict(username='test_add_craft_user_1', password='testpassword'))
            url = '/addInstrumentToCraft/' + str(instrument1_id)
            response = c.get(url, follow_redirects=True)
            assert '成功添加至购物车'.encode('utf-8') in response.data
            url = '/addInstrumentToCraft/' + str(instrument2_id)
            response = c.get(url, follow_redirects=True)
            assert '成功添加至购物车'.encode('utf-8') in response.data

            self.curr.execute('SELECT id FROM shopping_craft WHERE user_id=%s', testuser1.getId())
            craft_id = self.curr.fetchone()[0]
            self.curr.execute('SELECT instrument_id FROM shoppingcraft_instrument WHERE shoppingcraft_id=%s', craft_id)
            instrumens_id = [id[0] for id in self.curr.fetchall()]
            assert instrument1_id in instrumens_id
            assert instrument2_id in instrumens_id

    def generate_random_instrument_id(self):
        now = datetime.now()
        instrument_id = int(str(int(now.timestamp() * pow(10, 6)))[-8:] + str(randint(1, 9)))
        return instrument_id


if __name__ == '__main__':
    unittest.main()

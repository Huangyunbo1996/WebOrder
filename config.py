from os import environ


class Config:
    MYSQL_CONNECT_ARGS = {
        'host':'127.0.0.1',
        'user':'root',
        'db':'weborder',
        'password':environ.get('mysql_password'),
        'charset':'utf8'
    }
    SECRET_KEY = 'StrongKey'
    ADMIN_USERNAME = environ.get('weborder_admin_username')
    ADMIN_PASSWORD = environ.get('weborder_admin_password')


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    MYSQL_CONNECT_ARGS = {
        'host': '127.0.0.1',
        'user': 'root',
        'db': 'weborder_test',
        'password': environ.get('mysql_password'),
        'charset': 'utf8'
    }


class ProductionConfig(Config):
    pass


config = {
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'prodection':ProductionConfig,

    'default':DevelopmentConfig
}
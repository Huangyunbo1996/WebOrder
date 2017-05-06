from os import environ
import logging


class Config:
    MYSQL_CONNECT_ARGS = {
        'host': '127.0.0.1',
        'user': 'root',
        'db': 'weborder',
        'password': environ.get('mysql_password'),
        'charset': 'utf8'
    }
    SECRET_KEY = 'StrongKey'
    ADMIN_USERNAME = environ.get('weborder_admin_username')
    ADMIN_PASSWORD = environ.get('weborder_admin_password')
    LOGGING_CONFIG = {
        'version': 1,
        'loggers': {
            'weborder': {
                'level': logging.DEBUG
            }
        }
    }


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
    LOGGING_CONFIG = {
        'version': 1,
        'loggers': {
            'weborder': {
                'level': logging.ERROR,
                'filename': 'weborder_logging.log'
            }
        }
    }


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'prodection': ProductionConfig,

    'default': DevelopmentConfig
}

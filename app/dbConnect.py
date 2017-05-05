from pymysql import Connect,err
from flask import g, current_app as app
from .main import main
from os import environ, system


def init_db(sql_file_path):
    command = 'mysql -uroot -p' + environ.get('mysql_password') + '< ' + sql_file_path
    try:
        system(command)
    except BaseException as e:
        print(e)
        return False
    else:
        return True


def connect_db():
    conn = Connect(**app.config['MYSQL_CONNECT_ARGS'])
    return conn


def get_conn():
    if not hasattr(g, 'conn'):
        g.conn = connect_db()
    return g.conn


def get_cursor():
    if not hasattr(g, 'cursor'):
        g.cursor = get_conn().cursor()
    return g.cursor


@main.teardown_request
def close_db(error):
    if hasattr(g, 'cursor'):
        try:
            g.cursor.close()
        except err.Error as e:
            pass
    if hasattr(g, 'conn'):
        try:
            g.conn.close()
        except err.Error as e:
            pass

from . import main
from flask import url_for, render_template, g, redirect, session, current_app, abort
from ..models import Instrument, ShoppingCraft, Order, User
from .forms import LoginForm, RegisterForm, AdminForm, InstrumentForm
from ..dbConnect import get_cursor, connect_db, get_conn
from werkzeug.security import check_password_hash
from os import environ
from ..decorators import admin_required, login_required
import logging
from logging.config import dictConfig
from datetime import datetime
from random import randint


@main.route('/', methods=['GET', 'POST'])
def index():
    logined = session.get('logined')
    if logined:
        username = session.get('username')
    else:
        username = None
    curr = get_cursor()
    curr.execute('''SELECT id,name,price,description,image_path FROM instrument WHERE deleted=false''')
    instruments = curr.fetchall()
    instruments = [list(instrument) for instrument in instruments]
    for i in range(len(instruments)):
        instruments[i].append(i)
    return render_template('index.html', instruments=instruments, logined=logined, username=username,
                           per_line_nums=current_app.config['INSTRUMENT_NUM_PER_LINE'])


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    login_failed_flag = 0
    if form.validate_on_submit():
        conn = get_conn()
        cur = get_cursor()
        cur.execute('SELECT password_hash FROM user WHERE username="%s"', form.username.data)
        temp_data = cur.fetchone()
        if temp_data != None:
            password_hash = temp_data[0].strip('\'')
        else:
            password_hash = None
        if password_hash:
            if check_password_hash(password_hash, form.password.data):
                session['logined'] = True
                session['username'] = form.username.data
                return redirect(url_for('main.index'))
            else:
                form.password.data = ''
                login_failed_flag = 1
        else:
            form.password.data = ''
            login_failed_flag = 1
    return render_template('login.html', form=form, flag=login_failed_flag)


@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    username_already_used_flag = 0  # 用户名重复标记
    write_database_error_flag = 0  # 将新用户写入数据库时发生错误标记
    if form.validate_on_submit():
        cur = get_cursor()
        cur.execute('SELECT * FROM user WHERE username = "%s"', form.username.data)
        if cur.fetchone():
            username_already_used_flag = 1
            form.password.data = ''
        else:
            new_user = User(form.username.data, form.password.data)
            if new_user.saveToDb():
                session['logined'] = True
                session['username'] = form.username.data
                return redirect(url_for('main.index'))
            else:
                write_database_error_flag = 1
                form.password.data = ''
    return render_template('register.html', form=form,
                           username_flag=username_already_used_flag, database_flag=write_database_error_flag)


@main.route('/admin')
@admin_required
def admin():
    curr = get_cursor()
    curr.execute('SELECT * FROM instrument WHERE deleted=false')
    instrument_delete_failed_flag = 0
    temp_data = curr.fetchall()
    instruments = list()
    if temp_data != None:
        for instrument in temp_data:
            instruments.append(list(instrument))
    if session.get('instrument_delete_failed'):
        instrument_delete_failed_flag = 1
    return render_template('admin.html', instruments=instruments, delete_flag=instrument_delete_failed_flag)


@main.route('/adminLogin', methods=['GET', 'POST'])
def adminLogin():
    form = AdminForm()
    login_failed_flag = 0
    if form.validate_on_submit():
        if form.username.data == environ.get('weborder_admin_username') and \
                        form.password.data == environ.get('weborder_admin_password'):
            session['isAdmin'] = True
            return redirect(url_for('main.admin'))
        else:
            login_failed_flag = 1
            return render_template('adminLogin.html', form=form, flag=login_failed_flag)
    return render_template('adminLogin.html', form=form, flag=login_failed_flag)


@main.route('/adminLogout')
def adminLogout():
    session.clear()
    return redirect(url_for('main.index'))


@main.route('/instrumentEdit/<int:id>', methods=['GET', 'POST'])
@admin_required
def instrumentEdit(id):
    form = InstrumentForm()
    edit_fail_flag = 0
    conn = get_conn()
    curr = conn.cursor()
    if form.validate_on_submit():
        thisInstrument = Instrument(id, form.name.data, float(form.price.data), float(form.weight.data),
                                    form.description.data,
                                    float(form.transport_cost.data), form.image.data)
        if thisInstrument.modify():
            return redirect(url_for('main.admin'))
        else:
            edit_fail_flag = 1
            return render_template('instrumentEdit.html', form=form, edit_flag=edit_fail_flag)
    curr.execute('SELECT * FROM instrument WHERE id = %s and deleted=false', id)
    instrument_data = curr.fetchone()
    if instrument_data == None:
        abort(404)
    else:
        instrument_data = list(map((lambda i: i.strip('\'') if type(i) is str else i), [i for i in instrument_data]))
        form.name.data = instrument_data[1]
        form.price.data = instrument_data[2]
        form.weight.data = instrument_data[3]
        form.description.data = instrument_data[4]
        form.transport_cost.data = instrument_data[5]
        form.image.data = instrument_data[6]
    return render_template('instrumentEdit.html', form=form, edit_flag=edit_fail_flag)


@main.route('/instrumentDelete/<int:id>')
@admin_required
def instrumentDelete(id):
    curr = get_cursor()
    try:
        curr.execute('SELECT * FROM instrument WHERE id=%s', id)
        instrument_need_delete = curr.fetchone()
    except Exception as e:
        dictConfig(current_app.config['LOGGING_CONFIG'])
        logger = logging.getLogger()
        logger.error(
            "page_instrumentDelete:An error occurred while writing to the database instrument:%s" % e)
        return False
    if not instrument_need_delete:
        abort(404)
    else:
        if Instrument.removeFromDb(id):
            return redirect(url_for('main.admin'))
        else:
            session['instrument_delete_failed'] = True
            return redirect(url_for('main.admin'))


@main.route('/addInstrument', methods=['GET', 'POST'])
@admin_required
def addInstrument():
    form = InstrumentForm()
    conn = get_conn()
    curr = get_cursor()
    edit_fail_flag = 0
    if form.validate_on_submit():
        now = datetime.now()
        id = int(str(int(now.timestamp() * pow(10, 6)))[-8:] + str(randint(1, 9)))
        newInstrument = Instrument(id, form.name.data, float(form.price.data), float(form.weight.data),
                                   form.description.data,
                                   float(form.transport_cost.data), form.image.data)
        if newInstrument.saveToDb():
            return redirect(url_for('main.admin'))
        else:
            edit_fail_flag = 1
            return render_template('addInstrument.html', form=form, flag=edit_fail_flag)
    return render_template('addInstrument.html', form=form, flag=edit_fail_flag)


@main.route('/allUser')
@admin_required
def allUser():
    cur = get_cursor()
    cur.execute('''SELECT * FROM user''')
    users = cur.fetchall()
    users = [list(user) for user in users]
    return render_template('allUser.html', users=users)


@main.route('/historyOrder/<int:id>')
@admin_required
def historyOrder(id):
    cur = get_cursor()
    cur.execute('''SELECT ot.id,u.username,ot.totalprice,ot.datetime FROM `order`
                        AS ot LEFT JOIN user_order AS uo ON ot.id=uo.order_id 
                        LEFT JOIN user AS u ON uo.user_id=u.id WHERE u.id=%s''', id)
    orders = cur.fetchall()
    orders = [list(order) for order in orders]
    return render_template('historyOrder.html', orders=orders)


@main.route('/allOrder')
@admin_required
def allOrder():
    cur = get_cursor()
    cur.execute('''SELECT ot.id,u.username,ot.totalprice,ot.datetime FROM `order`
                    AS ot LEFT JOIN user_order AS uo ON ot.id=uo.order_id 
                    LEFT JOIN user AS u ON uo.user_id=u.id;''')
    orders = cur.fetchall()
    orders = [list(order) for order in orders]
    return render_template('allOrder.html', orders=orders)


@main.route('/orderDetail/<int:id>')
@admin_required
def orderDetail(id):
    cur = get_cursor()
    cur.execute('''SELECT ot.id,u.username,ot.totalprice,ot.datetime FROM `order`
                    AS ot LEFT JOIN user_order AS uo ON ot.id=uo.order_id 
                    LEFT JOIN user AS u ON uo.user_id=u.id WHERE ot.id=%s''', id)
    orders = cur.fetchall()[0]
    orders = list(orders)

    cur.execute('''SELECT it.id,it.name,it.price,it.image_path,it.deleted FROM `order` AS ot LEFT JOIN 
                    instrument_order AS io ON ot.id=io.order_id LEFT JOIN
                    instrument AS it ON io.instrument_id=it.id WHERE
                    ot.id=%s''', id)
    instruments = cur.fetchall()
    instruments = [list(instrument) for instrument in instruments]

    return render_template('orderDetail.html', orders=orders, instruments=instruments)

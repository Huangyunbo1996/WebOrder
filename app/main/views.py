from . import main
from flask import url_for,render_template,g,redirect,session
from ..models import Instrument,ShoppingCraft,Order,User
from .forms import LoginForm,RegisterForm,AdminForm
from ..dbConnect import get_cursor,connect_db,get_conn
from werkzeug.security import check_password_hash
from os import environ
from ..decorators import admin_required,login_required

@main.route('/',methods=['GET','POST'])
def index():
    logined = session.get('logined')
    if logined:
        username = session.get('username')
    else:
        username = None
    return render_template('index.html',logined=logined,username=username)

@main.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    login_failed_flag = 0
    if form.validate_on_submit():
        conn = get_conn()
        cur = get_cursor()
        cur.execute('SELECT password_hash FROM user WHERE username="%s"',form.username.data)
        temp_data = cur.fetchone()
        if temp_data != None:
            password_hash = temp_data[0].strip('\'')
        else:
            password_hash = None
        if password_hash:
            if check_password_hash(password_hash,form.password.data):
                session['logined'] = True
                session['username'] = form.username.data
                return redirect(url_for('main.index'))
            else:
                form.password.data = ''
                login_failed_flag = 1
        else:
            form.password.data = ''
            login_failed_flag = 1
    return render_template('login.html',form=form,flag=login_failed_flag)

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    username_already_used_flag = 0 # 用户名重复标记
    write_database_error_flag = 0 # 将新用户写入数据库时发生错误标记
    if form.validate_on_submit():
        cur = get_cursor()
        cur.execute('SELECT * FROM user WHERE username = "%s"', form.username.data)
        if  cur.fetchone():
            username_already_used_flag = 1
            form.password.data = ''
        else:
            new_user = User(form.username.data,form.password.data)
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
    curr.execute('SELECT * FROM instrument')
    temp_data = curr.fetchall()
    instruments = list()
    if temp_data != None:
        for instrument in temp_data:
            instruments.append(list(instrument))
    return render_template('admin.html',instruments=instruments)

@main.route('/adminLogin',methods=['GET','POST'])
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
            return render_template('adminLogin.html',form=form,flag=login_failed_flag)
    return render_template('adminLogin.html',form=form,flag=login_failed_flag)

@main.route('/instrumentEdit/<id>',methods=['GET','POST'])
def instrumentEdit(id):
    pass
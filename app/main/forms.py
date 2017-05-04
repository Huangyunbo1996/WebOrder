from flask_wtf import Form
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import Required,Length,EqualTo


class LoginForm(Form):
    username = StringField('用户名',validators=[Required(),Length(0,30)])
    password = PasswordField('密码',validators=[Required()])
    submit = SubmitField('登陆')


class RegisterForm(Form):
    username = StringField('用户名',validators=[Required(),Length(0,30)])
    password = PasswordField('密码',validators=[Required(),
                                                EqualTo('re_password',
                                                message='重复密码与密码不一致')])
    re_password = PasswordField('重复密码',validators=[Required()])
    submit = SubmitField('注册')


class AdminForm(Form):
    username = StringField('用户名',validators=[Required()])
    password = PasswordField('密码',validators=[Required()])
    submit = SubmitField('登陆')
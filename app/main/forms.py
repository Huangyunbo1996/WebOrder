from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import Required,Length,EqualTo,DataRequired


class LoginForm(FlaskForm):
    username = StringField('用户名',validators=[DataRequired(),Length(0,30)])
    password = PasswordField('密码',validators=[DataRequired()])
    submit = SubmitField('登陆')


class RegisterForm(FlaskForm):
    username = StringField('用户名',validators=[DataRequired(),Length(0,30)])
    password = PasswordField('密码',validators=[DataRequired(),
                                                EqualTo('re_password',
                                                message='重复密码与密码不一致')])
    re_password = PasswordField('重复密码',validators=[DataRequired()])
    submit = SubmitField('注册')


class AdminForm(FlaskForm):
    username = StringField('用户名',validators=[DataRequired()])
    password = PasswordField('密码',validators=[DataRequired()])
    submit = SubmitField('登陆')
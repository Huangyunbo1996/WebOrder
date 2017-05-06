from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, TextAreaField
from wtforms.validators import Required, Length, EqualTo, DataRequired, Regexp


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(0, 30)])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登陆')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(0, 30)])
    password = PasswordField('密码', validators=[DataRequired(),
                                               EqualTo('re_password',
                                                       message='重复密码与密码不一致')])
    re_password = PasswordField('重复密码', validators=[DataRequired()])
    submit = SubmitField('注册')


class AdminForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登陆')


class InstrumentForm(FlaskForm):
    name = StringField('名称', validators=[DataRequired(), Length(0, 30)])
    price = FloatField('价格（元）', validators=[DataRequired(message='请输入正确的价格')])
    weight = FloatField('重量（千克）', validators=[DataRequired(message='请输入正确的重量')])
    description = TextAreaField('商品描述', validators=[DataRequired(), Length(0, 200)])
    transport_cost = FloatField('运输费用(元)', validators=[DataRequired(message='请输入正确的运输费用')])
    image = StringField('图片路径', validators=[DataRequired(), Length(0, 150)])
    submit = SubmitField('确定')

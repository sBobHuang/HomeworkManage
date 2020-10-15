#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo

from ..models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired(), EqualTo('password2', message='两次输入的密码不一样！')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('账户已注册')


class AccountForm(FlaskForm):
    account_name = StringField('账务名称', validators=[DataRequired()])
    account_fee = IntegerField('金额', validators=[DataRequired()])
    income = BooleanField('收入(默认支出)')
    account_submit = SubmitField('提交')


class PayToTeacherForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    fee = IntegerField('金额', validators=[DataRequired()])
    classname = IntegerField('班级ID', validators=[DataRequired()])
    assistant = BooleanField('助教(默认教师)')
    pay_to_teacher_submit = SubmitField('提交')


class RefundForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    fee = IntegerField('金额', validators=[DataRequired()])
    classname = IntegerField('班级ID', validators=[DataRequired()])
    refund_submit = SubmitField('提交')


class BookForm(FlaskForm):
    students = PageDownField(u'赠书名单(每个人间隔一行)！', validators=[DataRequired()])
    book_submit = SubmitField('提交')


class CourseQueryForm(FlaskForm):
    student = StringField('学生姓名', validators=[DataRequired()])
    course_query_submit = SubmitField('提交')

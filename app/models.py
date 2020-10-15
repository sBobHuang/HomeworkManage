#!/usr/bin/python
# -*- coding: utf-8 -*-
from . import db, login_manage
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_moment import datetime

from .enum import PayType


@login_manage.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 权限
class Permission():
    FOLLOW = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


# 角色
class Role(db.Model):
    '''定义角色的数据库模型'''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 是否为默认角色（普通用户）
    permissions = db.Column(db.Integer)  # 设置权限
    user = db.relationship('User', backref='role', lazy='dynamic')  # 自身添加一个user属性，反过来给User添加一个role属性。属性可以赋值。

    @staticmethod
    def insert_roles():
        '''创建用户，版主和管理员三个角色的静态方法。'''
        roles = {
            "User": (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
            "Moderator": (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            "Administrator": (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        '''打印角色名字'''
        return '<Role %r>' % self.name


# 用户
class User(db.Model, UserMixin):
    '''定义使用者的数据库模型'''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    mobile_phone = db.Column(db.String(64))
    child_name = db.Column(db.String(64))
    wxid = db.Column(db.String(64))
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 为user表中添加添加一行外键，由该属性可以获得使用者的角色所对应的id值。
    confirmed = db.Column(db.Boolean, default=False)
    # 增加一个确认属性
    password_hash = db.Column(db.String(128))

    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        '''每个用户对象被调用时都会调用该方法。如果该用户没有被赋予角色，则判断是否为管理员，给与管理员或者默认角色'''
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.mobile_phone == current_app.config['FLASK_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def ping(self):
        '''载入最后一次访问的日期'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        '''验证用户是否拥有该权限的方法'''
        return self.role is not None and ((self.role.permissions & permissions) == permissions)

    def is_administrator(self):
        # 验证是否为管理员的方法
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        return self.can(Permission.MODERATE_COMMENTS)

    # 对密码进行哈希处理，密码无法直接读取
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        # 此函数生成令牌，返回token
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        # 此函数用来确认令牌，据此返回True或者False，并改变confirmed的值
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        '''打印使用者的名字'''
        return '<User %r>' % self.username


# 未登录用户
class AnonymousUser(AnonymousUserMixin):
    '''创建匿名用户类，实现can与is_administrator方法，实习多态，将未登陆的用户归为此类'''

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_moderator(self):
        return False


# 学生
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    real_name = db.Column(db.String(64))
    mobile_phone = db.Column(db.String(64))
    school = db.Column(db.String(64))
    grade = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    is_old = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    extended_info = db.Column(db.Text())

    def __init__(self, **kwargs):
        # 每个学生对象被调用时都会调用该方法
        super(Student, self).__init__(**kwargs)


# 课程
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_info_id = db.Column(db.String(64))
    mobile_phone = db.Column(db.String(64))
    real_name = db.Column(db.String(64))
    student_id = db.Column(db.Integer)
    order_status = db.Column(db.Integer)
    seat_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    # 支付方式 0(微信) 1(支付宝) 2(银行卡转账) 3(管理员确认) 4(未知)
    extended_info = db.Column(db.Text())

    def __init__(self, **kwargs):
        # 每门课程对象被调用时都会调用该方法
        super(Course, self).__init__(**kwargs)


class CourseCancel(db.Model):
    __tablename__ = 'courses_cancel'
    id = db.Column(db.Integer, primary_key=True)
    course_info_id = db.Column(db.String(64))
    mobile_phone = db.Column(db.String(64))
    real_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    # 支付方式 0(微信) 1(支付宝) 2(银行卡转账) 3(管理员确认) 4(未知)
    extended_info = db.Column(db.Text())

    def __init__(self, **kwargs):
        # 每门课程对象被调用时都会调用该方法
        super(CourseCancel, self).__init__(**kwargs)


# 课程信息
class CourseInfo(db.Model):
    __tablename__ = 'course_infos'
    id = db.Column(db.String(64), primary_key=True)
    location = db.Column(db.String(64))
    course_level = db.Column(db.String(64))
    course_period = db.Column(db.String(64))
    course_name = db.Column(db.String(64))
    price = db.Column(db.Integer)
    show_name = db.Column(db.String(64))
    front_name = db.Column(db.String(64))
    disabled = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        # 每门课程信息对象被调用时都会调用该方法
        super(CourseInfo, self).__init__(**kwargs)

    def courseToArr(self):
        return [self.location, self.course_level, self.course_name, self.getEnrollmentNumber(),
                self.course_period, self.price]

    def showStatus(self):
        return [self.location, self.show_name, self.getEnrollmentNumber(), self.course_period]

    def showExpectIncome(self):
        enrollment_number = len(Course.query.filter_by(course_info_id=self.id, order_status=4).all())
        return [self.location + self.show_name, enrollment_number, self.price, enrollment_number * self.price]

    def getEnrollmentNumber(self):
        enrollment_number = len(Course.query.filter(Course.course_info_id == self.id,
                                                    Course.order_status.in_([0, 4, 7])).all())
        location = str(self.id)[3]
        category = str(self.id)[4]
        if location == '1' and category == '0':
            if enrollment_number >= 36:
                enrollment_number = '36+' + str(enrollment_number - 36)
        else:
            if enrollment_number >= 30:
                enrollment_number = '30+' + str(enrollment_number - 30)
        return enrollment_number


class WxUser(db.Model):
    __tablename__ = 'wxusers'
    id = db.Column(db.String(100), primary_key=True)
    nick_name = db.Column(db.String(75))
    avatar_url = db.Column(db.Text())
    country = db.Column(db.String(75))
    province = db.Column(db.String(75))
    city = db.Column(db.String(75))
    gender = db.Column(db.Integer)
    language = db.Column(db.String(75))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        # 每门课程信息对象被调用时都会调用该方法
        super(WxUser, self).__init__(**kwargs)

    @staticmethod
    def insert(id, data):
        wxuser = WxUser()
        wxuser.id = id
        wxuser.nick_name = data['nick_name']
        wxuser.avatar_url = data['avatar_url']
        wxuser.city = data['city']
        wxuser.country = data['country']
        wxuser.province = data['province']
        wxuser.gender = data['gender']
        wxuser.language = data['language']
        db.session.add(wxuser)

    def update(self, data):
        self.avatar_url = data['avatar_url']
        self.city = data['city']
        self.country = data['country']
        self.province = data['province']
        self.nick_name = data['nick_name']
        self.gender = data['gender']
        self.language = data['language']
        self.last_updated_at = datetime.utcnow()
        db.session.add(self)


# 文章模型
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text())
    body_html = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # 关联到User模型
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, **kwargs):
        # 每门课程信息对象被调用时都会调用该方法
        super(Post, self).__init__(**kwargs)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(64))
    show_name = db.Column(db.String(64))
    real_name = db.Column(db.String(64))
    mobile_phone = db.Column(db.String(64))
    course_id = db.Column(db.Integer)
    course_info_id = db.Column(db.Integer)
    pay_type = db.Column(db.Integer, default=PayType.Others.value)
    fee = db.Column(db.Integer)
    refund_fee = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(Account, self).__init__(**kwargs)


class SchoolMapping(db.Model):
    __tablename__ = 'school_mapping'
    id = db.Column(db.Integer, primary_key=True)
    user_in = db.Column(db.String(64))
    location = db.Column(db.String(64))
    school = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(SchoolMapping, self).__init__(**kwargs)


# 将未登陆的用户归为AnonymousUser类
login_manage.anonymous_user = AnonymousUser

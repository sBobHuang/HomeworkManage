from . import db, login_manage
from flask_moment import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
import json

@login_manage.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 权限
class Permission():
    FOLLOW = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08f
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

# 学生
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Text(), primary_key=True)
    real_name = db.Column(db.Text())
    class_name = db.Column(db.Text())
    course_names = db.Column(db.Text())
    gender = db.Column(db.Integer)
    mobile_phone = db.Column(db.Text())
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    extended_info = db.Column(db.Text())

    def __init__(self, **kwargs):
        # 每个学生对象被调用时都会调用该方法
        super(Student, self).__init__(**kwargs)

    def getHomeWorkSubTime(self,home_work_id):
        files_query = FileRecord.query.filter_by(student_id=self.id, course_names=self.course_names,home_work_id=home_work_id).order_by(FileRecord.home_work_id).all()
        if len(files_query) == 0:
            return '未提交'
        ma = (datetime(2020, 1, 1), 0)
        for file in files_query:
            if file.created_at > ma[0]:
                ma = (file.created_at, file.id)
        return (ma[0].strftime("%m/%d"), ma[1])


# 文档提交记录
class FileRecord(db.Model):
    __tablename__ = 'fileRecords'
    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Text())
    real_name = db.Column(db.Text())
    home_work_id = db.Column(db.Integer())
    course_names = db.Column(db.Text())
    file_name = db.Column(db.Text())
    score = db.Column(db.FLOAT)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        # 每个学生对象被调用时都会调用该方法
        super(FileRecord, self).__init__(**kwargs)


# 课程信息
class CourseInfo(db.Model):
    __tablename__ = 'course_infos'
    course_period = db.Column(db.String(64))
    course_name = db.Column(db.String(64))
    course_names = db.Column(db.String(64), primary_key=True)
    extended_info = db.Column(db.Text())
    disabled = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        # 每门课程信息对象被调用时都会调用该方法
        super(CourseInfo, self).__init__(**kwargs)

    def showStatus(self):
        return [self.course_name, self.course_names, self.getEnrollmentNumber(), self.getZYStr()]

    def getEnrollmentNumber(self):
        enrollment_number = len(Student.query.filter_by(course_names=self.course_names).all())
        return enrollment_number

    def getZY(self):
        dic = {}
        if self.extended_info is not None:
            dic = json.loads(self.extended_info)
        for i in dic.keys():
            submitted_number = len(FileRecord.query.filter_by(course_names=self.course_names, home_work_id=i).
                                   group_by(FileRecord.student_id).all())
            dic[i] = (dic[i], submitted_number)
        return dic

    def getZYArr(self):
        zy_dic = self.getZY()
        return set('作业'+i for i in zy_dic if zy_dic[i][0] == 1)

    def getZYStr(self):
        return "、".join(self.getZYArr())


class CourseNames(db.Model):
    __tablename__ = 'course_names'
    id = db.Column(db.Integer(), primary_key=True)
    course_name = db.Column(db.Text())

    def __init__(self, **kwargs):
        # 每门课程信息对象被调用时都会调用该方法
        super(CourseNames, self).__init__(**kwargs)


# 网站报名信息
class InstitutionInfo(db.Model):
    __tablename__ = 'institution_infos'
    institution_id = db.Column(db.Integer, primary_key=True)
    institution_period = db.Column(db.Text())
    institution_name = db.Column(db.Text())
    institution_url = db.Column(db.Text())
    job_category = db.Column(db.Text())
    extended_info = db.Column(db.Text())
    disabled = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(InstitutionInfo, self).__init__(**kwargs)


class InstitutionJobInfo(db.Model):
    __tablename__ = 'institution_job_infos'
    institution_job_id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer)
    department_name = db.Column(db.Text())
    job_name = db.Column(db.Text())
    job_category = db.Column(db.Text())
    job_id = db.Column(db.Text())
    job_num = db.Column(db.Integer)
    confirmed = db.Column(db.Integer)
    un_confirmed = db.Column(db.Integer)
    succeeded = db.Column(db.Integer)
    total_num = db.Column(db.Integer)
    education = db.Column(db.Text())
    target = db.Column(db.Text())

    def __init__(self, **kwargs):
        super(InstitutionJobInfo, self).__init__(**kwargs)

    def cal_total(self):
        self.total_num = self.confirmed + self.un_confirmed + self.succeeded


class BuyInfo(db.Model):
    __tablename__ = 'buy_infos'
    id = db.Column(db.Integer, primary_key=True)
    buy_name = db.Column(db.Text())
    priority_status = db.Column(db.Integer)
    status = db.Column(db.Integer, default=0)
    note = db.Column(db.Text())
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    extended_info = db.Column(db.Text())

    def __init__(self, **kwargs):
        super(BuyInfo, self).__init__(**kwargs)

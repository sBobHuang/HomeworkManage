from . import db
from flask_moment import datetime


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


# 文档提交记录
class FileRecord(db.Model):
    __tablename__ = 'fileRecords'
    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Text())
    real_name = db.Column(db.Text())
    home_work_id = db.Column(db.Integer())
    courseName = db.Column(db.Text())
    score = db.Column(db.FLOAT)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(self, **kwargs):
        # 每个学生对象被调用时都会调用该方法
        super(FileRecord, self).__init__(**kwargs)

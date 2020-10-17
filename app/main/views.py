#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from flask import render_template, flash

from . import main
from .api_exception import RegisterSuccess
from .forms import UploadForm
from ..fuc import safe_copy, extendedInfoArrayAdd
from ..models import Student, FileRecord
from .. import db

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前项目的绝对路径


@main.route('/', methods=['POST', 'GET'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        student_query = Student.query.filter_by(id=form.studentID.data).first()
        if student_query is None:
            flash('学号填写错误')
            return render_template('index.html', form=form)
        student_query = Student.query.filter_by(id=form.studentID.data, real_name=form.name.data).first()
        if student_query is None:
            flash('学号与姓名不匹配')
            return render_template('index.html', form=form)
        file_dir = os.path.join(basedir, "../../ZY", form.course.data, form.homeWork.data,
                                student_query.course_names)  # 拼接成合法文件夹地址
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  # 文件夹不存在就创建
        filename = form.file.data.filename
        file = os.path.splitext(filename)
        filename, file_type = file
        new_filename = form.studentID.data + '_' + form.name.data + '_' + form.homeWork.data + file_type
        safe_copy(file_dir, new_filename, form)
        fileRecord = FileRecord(
            student_id=student_query.id,
            real_name=student_query.real_name,
            home_work_id=int(form.homeWork.data[2:]),
            courseName=student_query.course_names
        )
        db.session.add(fileRecord)
        db.session.commit()
        flash('作业上传成功')
    return render_template('index.html', form=form)


@main.route('/addStudent')
def addStudent():
    fp = open('students.txt')
    content = fp.read()
    items = content.split('\n')
    for item in items:
        stu = item.split('\t')
        if len(stu) < 4:
            print(item, '数据不全')
            continue
        student = Student(
            id=stu[0],
            real_name=stu[1],
            class_name=stu[2],
        )
        student.course_names = extendedInfoArrayAdd(student.course_names, stu[3])
        db.session.add(student)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            print(stu[1], '已插入')
    return RegisterSuccess('学生插入成功')

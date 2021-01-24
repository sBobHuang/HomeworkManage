#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from flask import render_template, flash, request, current_app
from flask_login import login_required

from app.auth.views import admin
from . import main
from .api_exception import RegisterSuccess
from .forms import UploadForm
from ..fuc import extendedInfoArrayAdd,courseInfoIDToStr,getSubmitHomeWork
from ..models import Student, FileRecord
from .. import db

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前项目的绝对路径


@main.route('/', methods=['POST', 'GET'])
def index():
    form = UploadForm()
    submit_homework = getSubmitHomeWork()
    form.course.choices = [(i, i) for i in submit_homework]
    form.homeWork.choices = []
    if bool(submit_homework):
        form.homeWork.choices = [(i,i) for i in submit_homework[list(submit_homework)[0]]]
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
        if not os.path.exists(os.path.join(file_dir, new_filename)):
            form.file.data.save(os.path.join(file_dir, new_filename))
            flash('作业上传成功')
        else:
            flash("您已成功覆盖上次提交")
            form.file.data.save(os.path.join(file_dir, new_filename))
        fileRecord = FileRecord(
            student_id=student_query.id,
            real_name=student_query.real_name,
            home_work_id=int(form.homeWork.data[2:]),
            course_names=student_query.course_names
        )
        db.session.add(fileRecord)
        db.session.commit()
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


@main.route('/preTerm')
@login_required
def preTerm():
    courseInfoIDSet = ['20上', '20下']
    courseInfoIDYEARSet = set([i[0:2] for i in courseInfoIDSet])
    print(courseInfoIDYEARSet)
    pre_term = []
    courseInfoIDStrSet = {}
    for courseInfoID in courseInfoIDSet:
        courseInfoIDStrSet[courseInfoID] = courseInfoIDToStr(courseInfoID)
    for i in courseInfoIDYEARSet:
        pre_term.append([year for year in courseInfoIDSet if year[0:2] == i])
    return render_template('pre_term.html',
                           pre_term=pre_term,
                           courseInfoIDStrSet=courseInfoIDStrSet
                           )


@main.route('/admin', methods=['GET', 'POST'])
@login_required
def mainAdmin():
    return admin()

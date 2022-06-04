#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import shutil

import requests
from flask import render_template, flash, request, current_app, Response
from contextlib import closing
from flask_login import login_required

from app.auth.views import admin
from . import main
from .api_exception import RegisterSuccess
from .forms import UploadForm, CalculatorForm, DownloadForm
from ..fuc import extendedInfoArrayAdd, courseInfoIDToStr, getSubmitHomeWork, get_filelist
from ..models import Student, FileRecord
from .. import db
from flask_moment import datetime


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
        basedir = current_app.config['BASE_DIR']
        file_dir = os.path.join(basedir, "ZY", form.course.data,
                                student_query.course_names,
                                form.homeWork.data)  # 拼接成合法文件夹地址
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  # 文件夹不存在就创建
        filename = form.file.data.filename
        file = os.path.splitext(filename)
        filename, file_type = file
        new_filename = form.studentID.data + '_' + form.name.data + '_' + form.homeWork.data + file_type
        files_query = FileRecord.query.filter_by(student_id=student_query.id,
                                                 course_names=student_query.course_names,
                                                 home_work_id=int(form.homeWork.data[2:])).first()
        if files_query is None:
            form.file.data.save(os.path.join(file_dir, new_filename))
            flash('作业上传成功')
            fileRecord = FileRecord(
                student_id=student_query.id,
                real_name=student_query.real_name,
                home_work_id=int(form.homeWork.data[2:]),
                course_names=student_query.course_names,
                file_name=os.path.join(file_dir, new_filename)
            )
            db.session.add(fileRecord)
        else:
            print(files_query.file_name)
            os.remove(files_query.file_name)
            files_query.file_name = os.path.join(file_dir, new_filename)
            files_query.created_at = datetime.utcnow()
            flash("您已成功覆盖上次提交")
            form.file.data.save(os.path.join(file_dir, new_filename))
        db.session.commit()
        # if not os.path.exists(os.path.join(file_dir, new_filename)):
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


@main.route('/fillFileName')
@login_required
def fillFileName():
    students_query = Student.query.filter_by().all()
    basedir = current_app.config['BASE_DIR']
    filelist = get_filelist(os.path.join(basedir, "ZY"), [])
    for stu in students_query:
        files_query = FileRecord.query.filter_by(student_id=stu.id, course_names=stu.course_names).order_by(
            FileRecord.home_work_id).all()
        for i in range(1, 3):
            tot = 0
            for file in files_query:
                if file.home_work_id == i:
                    filename = file.student_id + '_' + file.real_name + '_作业' + str(i)
                    if tot:
                        filename = filename + '_' + str(tot)
                    tot = tot + 1
                    for j in filelist:
                        if filename in j:
                            file.file_name = j
                            break
    return RegisterSuccess('更新成功')


@main.route('/IDE/<path:path>', methods=['GET', 'OPTIONS', 'POST'])
def ide_send(path=''):
    url = request.url
    if request.method == 'OPTIONS':
        return Response('', 200, '')
    url = 'http://150.158.55.167:2358' + url[url.index('/submissions'):]
    payload_header = {
        'Content-Type': 'application/json',
    }
    resp = requests.request(
        method=request.method,
        url=url,
        data=request.data,
        headers=payload_header
    )
    headers = filter_headers(resp.raw.headers.items())
    return Response(resp.content, resp.status_code, headers)


def filter_headers(headers):
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'access-control-allow-credentials', 'access-control-allow-origin']
    return [(name, value) for (name, value) in headers
            if name.lower() not in excluded_headers]


@main.route('/cal', methods=['GET', 'POST'])
def calculator():
    form = CalculatorForm()
    if form.validate_on_submit():
        try:
            import random, math
            answer = eval(form.calculator_string.data)
        except BaseException as e:
            answer = e
        finally:
            flash(answer)
    forms = [form]
    return render_template('auth/calculator.html',
                           forms=forms)


@main.route('/download', methods=['GET', 'POST'])
def download():
    form = DownloadForm()
    if form.validate_on_submit():
        file_dir = os.path.join(current_app.config['BASE_DIR'], 'File')
        temp_file_dir = os.path.join(file_dir, 't_down')
        get_empty_file_dir(temp_file_dir)
        res = os.system(f'cd {temp_file_dir}; wget {form.url.data}')
        if res == 0:
            filename = os.listdir(temp_file_dir)[0]
            shutil.copyfile(os.path.join(temp_file_dir, filename), os.path.join(file_dir, filename))
            file_record = FileRecord(
                course_names='oi_upload',
                real_name=filename,
                file_name=os.path.join(file_dir, filename)
            )
            db.session.add(file_record)
            db.session.commit()
            form.download_id = file_record.id
            flash(f'下载完成，文件名为{filename}')
        else:
            flash('下载失败')
    return render_template('download.html',
                           form=form)


def get_last_file(file_dir):
    file_list = os.listdir(file_dir)
    return max(file_list, key=lambda file: os.path.getmtime(os.path.join(file_dir, file)))


def get_empty_file_dir(file_dir):
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)
    for file in os.listdir(file_dir):
        os.remove(os.path.join(file_dir, file))

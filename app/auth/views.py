from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import current_user
from flask_login import login_user, logout_user, login_required
from flask_moment import datetime
from .forms import LoginForm, AddCourseForm, AddCoursesForm, UploadCoursesStus
from ..models import User, CourseInfo, Student

from ..fuc import courseInfoIDToStr, courseManageShow, homeWorkShow, \
    extendedInfoToDic, extendedInfoAdd, extendedInfoDel, getCourseNames, \
    addCourseName, addCourseNames
from . import auth
from ..main.export import exportOneHomeWorks
import os
from .. import db
from openpyxl import load_workbook


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if current_user.mobile_phone != current_app.config['FLASK_ADMIN']:
            if current_user.is_authenticated and not current_user.confirmed and request.endpoint[:5] != 'auth.':
                return redirect(url_for('auth.unconfirmed'))


@auth.route('/login', methods=['GET', 'POST'])
# 登录界面
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == current_app.config['FLASK_ADMIN']:
            user = User.query.filter_by(mobile_phone=form.username.data).first()
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('auth.courseAdmin'))
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('用户名或者密码错误')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
# 退出
@login_required
def logout():
    logout_user()
    flash('您已经退出账号!')
    return redirect(url_for('main.index'))


@auth.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    current_term = current_app.config['CURRENT_TERM']
    if current_user.is_administrator() is False:
        return redirect(url_for('main.index'))
    query_term = request.args.get('query_term', current_term, type=str)
    add_course_form = AddCourseForm()
    add_courses_form = AddCoursesForm()
    if add_course_form.validate_on_submit():
        flash(add_course_form.course_name.data+'已添加')
        addCourseName(add_course_form.course_name.data)
    course_names = getCourseNames()
    if len(course_names) > 0:
        add_course_form.form_body = '已有科目：' + "、".join(course_names)
        add_courses_form.course.choices = [(i, i) for i in course_names]
    else:
        add_course_form.form_body = '暂无科目'
    if add_courses_form.validate_on_submit():
        flash(add_courses_form.course.data + '新班级已添加')
        addCourseNames(add_courses_form.course.data)
    forms = [add_course_form, add_courses_form]
    currentCourseInfos = CourseInfo.query.filter_by(course_period=query_term, disabled=False).order_by(CourseInfo.course_names).all()
    statusLabels = ['课程名称', '班级', '班级人数', '正在收的作业']
    statusContent = [CourseInfo.showStatus(i) for i in currentCourseInfos]
    return render_template('auth/admin.html',
                           statuslabels=statusLabels, statusContent=statusContent,
                           query_term=query_term,
                           query_term_str=courseInfoIDToStr(query_term),
                           forms=forms)


@auth.route('/courseManage', methods=['GET', 'POST'])
@login_required
def courseManage():
    page = request.args.get('page', 1, type=int)
    current_term = current_app.config['CURRENT_TERM']
    query_term = request.args.get('query_term', current_term, type=str)
    new_homework = request.args.get('new_homework', None, type=bool)
    pagination = CourseInfo.query.filter_by(course_period=query_term, disabled=False).order_by(CourseInfo.course_names).paginate(page, per_page=1)
    course_names = pagination.items[0].course_names
    form = UploadCoursesStus()
    if form.validate_on_submit():
        basedir = current_app.config['BASE_DIR']
        filename = form.file.data.filename
        file = os.path.splitext(filename)
        filename, file_type = file
        save_filename1 = '班级名单上传-' + course_names + file_type
        file_dir = os.path.join(basedir, "Upload")  # 拼接成合法文件夹地址
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  # 文件夹不存在就创建
        save_filename = os.path.join(file_dir, save_filename1)
        form.file.data.save(save_filename)
        wb = load_workbook(save_filename)
        ws = wb.get_sheet_by_name(wb.get_sheet_names()[0])
        for row in ws.rows:
            # print(row[0].value, row[1].value, row[2].value)
            student = Student(
                id=row[0].value,
                real_name=row[1].value,
                class_name=row[2].value,
            )
            student.course_names = course_names
            db.session.add(student)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                print(row[1].value, '已插入')
    if new_homework is not None and new_homework is True:
        course = CourseInfo.query.filter_by(course_names=course_names).first()
        homework_dic = extendedInfoToDic(course.extended_info)
        # 并且不为空
        if course.extended_info is None or not bool(homework_dic):
            max_homework_id = 0
        else:
            max_homework_id = max([int(i) for i in homework_dic.keys()])
        course.extended_info = extendedInfoAdd(course.extended_info, max_homework_id+1, 1)
    homework_del_id = request.args.get('homework_del_id', None, type=str)
    course = CourseInfo.query.filter_by(course_names=course_names).first()
    if homework_del_id is not None:
        course.extended_info = extendedInfoDel(course.extended_info, homework_del_id)
    homework_pause_id = request.args.get('homework_pause_id', None, type=str)
    if homework_pause_id is not None:
        course.extended_info = extendedInfoAdd(course.extended_info, homework_pause_id, 0)
    homework_continue_id = request.args.get('homework_continue_id', None, type=str)
    if homework_continue_id is not None:
        course.extended_info = extendedInfoAdd(course.extended_info, homework_continue_id, 1)
    student_query = Student.query.filter_by(course_names=course_names).all()
    export = request.args.get('export', None, type=bool)
    homework_export_id = request.args.get('homework_export_id', None, type=str)
    if export is not None and export is True > 0:
        if homework_export_id is not None:
            return exportOneHomeWorks(course.course_name, course_names, '作业'+homework_export_id)
    homeWorkManageLabels = ['作业名称', '删除', '暂停接收', '已交作业人数', '打包下载']
    courseManageLabels = ['序号', '学号', '姓名', '班级']
    homeWorkContent = homeWorkShow(course_names)
    for homework in homeWorkContent:
        courseManageLabels.append('作业'+homework+'上交时间')
    return render_template('auth/course_manage.html',
                           course=pagination.items[0].course_names,
                           homeWorkManageLabels=homeWorkManageLabels,
                           courseManageLabels=courseManageLabels,
                           courseContent=courseManageShow(student_query, homeWorkContent),
                           homeWorkContent=homeWorkContent,
                           pagination=pagination,
                           query_term=query_term,
                           form=form)

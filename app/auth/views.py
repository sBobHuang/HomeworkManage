#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import current_user
from flask_login import login_user, logout_user, login_required
from flask_moment import datetime

from . import auth
from .forms import LoginForm, RegistrationForm, AccountForm, BookForm, CourseQueryForm, PayToTeacherForm, RefundForm
from .. import db
from ..email import send_emial
from ..enum import OrderStatus, PayType
from ..fuc import courseShows, extendedInfoAdd, \
    getStudentCurrentChargeCourses, courseCancelInTable, sendSMS, getAllCourseInfoSet, courseInfoIDToStr, \
    ConfirmCourseFuc
from ..main.api_exception import RegisterSuccess
from ..models import User, Course, CourseInfo, Account


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if current_user.mobile_phone != current_app.config['FLASK_ADMIN']:
            if current_user.is_authenticated and not current_user.confirmed and request.endpoint[:5] != 'auth.':
                return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


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


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'您已经确认过您的账户！感谢')
    else:
        flash(u'这个确认不合法')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_emial(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash(u'新的确认邮件已发至您的邮箱，请查收')
    return redirect(url_for('main.index'))


@auth.route('/course')
@login_required
def courseAdmin():
    page = request.args.get('page', 1, type=int)
    pagination = Course.query.filter(Course.order_status > 1, Course.order_status < 4).order_by(
        Course.last_updated_at.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'])
    enrollments = pagination.items
    courseInfoSet = getAllCourseInfoSet()
    return render_template('auth/course.html', shows=courseShows(enrollments, courseInfoSet), pagination=pagination)


@auth.route('/course/<int:id>', methods=['GET', 'POST'])
@login_required
def confirmCourse(id):
    ConfirmCourseFuc(id)
    return redirect(url_for('.courseAdmin'))


@auth.route('/cleanSeatID/<int:id>', methods=['GET', 'POST'])
@login_required
def cleanSeatID(id):
    course = Course.query.filter_by(id=id).first()
    course.order_status = 1
    course.seat_id = None
    course.last_updated_at = datetime.utcnow()
    db.session.add(course)
    return redirect(url_for('.courseAdmin'))


@auth.route('/cancelCourse', methods=['GET', 'POST'])
@login_required
def cancelCourse():
    page = request.args.get('page', 1, type=int)
    pagination = Course.query.filter_by(order_status=-1).order_by(Course.last_updated_at.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'])
    enrollments = pagination.items
    courseInfoSet = getAllCourseInfoSet()
    return render_template('auth/cancelCourse.html', shows=courseShows(enrollments, courseInfoSet),
                           pagination=pagination)


@auth.route('/confirmCancelCourse/<int:id>', methods=['GET', 'POST'])
@login_required
def confirmCancelCourse(id):
    course = Course.query.filter_by(id=id).first()
    courseCancelInTable(course)
    account = Account.query.filter_by(course_id=id).first()
    if account is not None:
        db.session.delete(account)
    db.session.commit()
    return redirect(url_for('.cancelCourse'))


@auth.route('/wrongCancelCourse/<int:id>', methods=['GET', 'POST'])
@login_required
def wrongCancelCourse(id):
    course = Course.query.filter_by(id=id).first()
    course.order_status = OrderStatus.EnrollmentSuccess.value
    course.last_updated_at = datetime.utcnow()
    db.session.add(course)
    db.session.commit()
    return redirect(url_for('.cancelCourse'))


@auth.route('/partCancelCourse/<int:id>', methods=['GET', 'POST'])
@login_required
def partCancelCourse(id):
    course = Course.query.filter_by(id=id).first()
    course.order_status = OrderStatus.PartialRefund.value
    course.seat_id = None
    course.last_updated_at = datetime.utcnow()
    db.session.add(course)
    db.session.commit()
    return redirect(url_for('.cancelCourse'))


@auth.route('/newUser', methods=['GET', 'POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if current_user.is_administrator():
            user = User(username=form.username.data,
                        password=form.password.data,
                        confirmed=True)
            db.session.add(user)
            db.session.commit()
            flash('您已注册新用户!')
            return redirect(url_for('main.index'))
        else:
            flash('非管理员不能注册用户')
    return render_template('auth/register.html', form=form)


@auth.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    current_term = current_app.config['CURRENT_TERM']
    query_term = request.args.get('query_term', current_term, type=str)
    if current_user.is_administrator() is False:
        return redirect(url_for('main.index'))
    account_form = AccountForm()
    book_form = BookForm()
    course_query_form = CourseQueryForm()
    pay_to_teacher_form = PayToTeacherForm()
    refund_form = RefundForm()
    if account_form.validate_on_submit():
        account = Account(
            show_name=account_form.account_name.data
        )
        account.course_info_id = query_term + '888'
        if account_form.income.data:
            account.fee = account_form.account_fee.data
        else:
            account.fee = -account_form.account_fee.data
            account.refund_fee = account_form.account_fee.data
        db.session.add(account)
        # print(account.__dict__)
        try:
            db.session.commit()
            flash('该账务已插入')
            return redirect(url_for('.admin'))
        except:
            db.session.rollback()
            flash('该账务插入失败')
    if book_form.validate_on_submit():
        students = book_form.students.data.split('\r\n')
        Str1 = '没报名正式课程，但是参与了活动:'
        Str2 = '报名了正式课程，但是没有缴费：'
        Str3 = '赠书失败:'
        for student in students:
            if student == '':
                continue
            courses = getStudentCurrentChargeCourses(student, query_term)
            if len(courses) == 0:
                Str1 = Str1 + student + ' '
                continue
            flag = True
            for course_ in courses:
                if course_.order_status == 4:
                    course_.extended_info = extendedInfoAdd(course_.extended_info, 'book_free', 1)
                    db.session.add(course_)
                    # print(account.__dict__)
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
                        Str3 = Str3 + student + ' '
                    flag = False
            if flag:
                Str2 = Str2 + student + ' '
        print(Str1)
        print(Str2)
        print(Str3)
    if course_query_form.validate_on_submit():
        Str1 = '您要查询的报名有：'
        courses = getStudentCurrentChargeCourses(course_query_form.student.data)
        for course in courses:
            print(course.__dict__)
    if pay_to_teacher_form.validate_on_submit():
        account = Account(
            real_name=pay_to_teacher_form.name.data,
            fee=-pay_to_teacher_form.fee.data,
            refund_fee=pay_to_teacher_form.fee.data,
            course_info_id=pay_to_teacher_form.classname.data
        )
        if pay_to_teacher_form.assistant.data:
            account.pay_type = PayType.payToAssistant.value
        else:
            account.pay_type = PayType.payToTeacher.value
        db.session.add(account)
        db.session.commit()
        flash('该老师已转账')
    if query_term == current_term:
        query_term = None
    return render_template('auth/admin.html',
                           forms=[account_form, book_form, course_query_form, pay_to_teacher_form],
                           query_term=query_term,
                           query_term_str=courseInfoIDToStr(query_term))

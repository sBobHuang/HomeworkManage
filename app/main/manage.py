#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import request, json, current_app, render_template
from flask_login import login_required
from flask_moment import datetime
from sqlalchemy import func

from . import main
from .api_exception import UpdateSuccess, RegisterFailed
from .. import db
from ..fuc import getPayType, getCourseInfoSet, courseIncomeShow, noneToInt, courseIncomeShowAll, calSummary, \
    quartReportIncomeShow, quartReportPayShow, courseManageShow, courseManageOtherShow, \
    getCurrentCourseInfos, getCurrentChargeCourses, extendedInfoToDic, getIsDiscount, getQueryChargeCourseInfos, \
    courseInfoIDToStr, extendedInfoToArray, getStudentCourseStr, getGenderSet, getGradeSet
from ..models import Course, CourseInfo, Account, Student


@main.route('/generateShowName', methods=['GET'])
@login_required
def generateShowName():
    currentCourseInfos = getCurrentCourseInfos()
    # todo 课程ID扩展一位用来表示等级
    for courseInfo in currentCourseInfos:
        if str(courseInfo.id)[4] == '0':
            course_str = '信奥公益课'
        elif str(courseInfo.id)[4] == '1':
            course_str = '信奥'
        elif str(courseInfo.id)[4] == '2':
            course_str = 'Python'
        elif str(courseInfo.id)[4] == '4':
            course_str = '信奥公益讲座'
        elif str(courseInfo.id)[4] == '5':
            course_str = '提前批信奥特训班'
        else:
            course_str = 'Error'
        courseInfo.show_name = course_str + courseInfo.course_name
        courseInfo.front_name = courseInfo.course_name + '(' + courseInfo.course_period + ')'
        db.session.add(courseInfo)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return RegisterFailed(msg="更新失败")
    return UpdateSuccess(msg="更新成功")


@main.route('/generateAccount', methods=['GET'])
@login_required
def generateAccount():
    max_course_id_in_Account = db.session.query(func.max(Account.course_id)).first()
    course_id = noneToInt(max_course_id_in_Account[0])
    course_query = Course.query.filter(Course.id > course_id, Course.order_status == 4).all()
    return insertAccount(course_query)


@main.route('/generateOtherAccount', methods=['GET'])
def generateOtherAccount():
    course_query = Course.query.filter(Course.order_status == 4).all()
    return insertAccount(course_query)


@main.route('/clearBook', methods=['GET'])
def clearBook():
    courses = getCurrentChargeCourses()
    for course in courses:
        json_dic = extendedInfoToDic(course.extended_info)
        if json_dic.get('book_free'):
            del json_dic['book_free']
        course.extended_info = json.dumps(json_dic)
        db.session.add(course)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return RegisterFailed(msg="更新数据失败")
    return UpdateSuccess(msg="更新成功")


def insertAccount(course_query):
    courseInfoSet = getCourseInfoSet()
    for course in course_query:
        account = Account.query.filter_by(course_id=course.id).first()
        if courseInfoSet.get(course.course_info_id) is None:
            continue
        courseInfo = courseInfoSet[course.course_info_id]
        if account is not None:
            # print(course.real_name + '已经统计过')
            if account.course_info_id != course.course_info_id:
                print(course.real_name + '发生过改变')
                account.location = courseInfo.location
                account.show_name = courseInfo.show_name
                account.fee = courseInfo.price
                if getIsDiscount(course.real_name, course.mobile_phone):
                    account.fee = courseInfo.price // 10 * 9
                account.course_info_id = course.course_info_id
                account.last_updated_at = course.last_updated_at
                db.session.add(account)
            if account.show_name != courseInfo.show_name:
                account.show_name = courseInfo.show_name
                db.session.add(account)
            continue
        account = Account(
            location=courseInfo.location,
            show_name=courseInfo.show_name,
            real_name=course.real_name,
            mobile_phone=course.mobile_phone,
            course_id=course.id,
            course_info_id=course.course_info_id,
            pay_type=getPayType(course.extended_info),
            fee=courseInfo.price,
            created_at=course.last_updated_at
        )
        if getIsDiscount(course.real_name, course.mobile_phone):
            account.fee = courseInfo.price // 10 * 9
        db.session.add(account)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            return RegisterFailed(msg="同步数据失败")
    return UpdateSuccess(msg="更新成功")


@main.route('/courseIncome', methods=['GET'])
@login_required
def courseIncome():
    generateAccount()
    page = request.args.get('page', 1, type=int)
    # 是当前期，且不为公益课
    current_term = current_app.config['CURRENT_TERM']
    pagination = CourseInfo.query.filter(CourseInfo.id.like(current_term + '___'),
                                         ~CourseInfo.id.like(current_term + '_0_')).paginate(page, per_page=1)
    accounts = Account.query.filter_by(course_info_id=pagination.items[0].id).all()
    courseIncomeLabels = ['姓名', '收入', '退款', '实收']
    return render_template('auth/course_income.html',
                           course=pagination.items[0].location + pagination.items[0].show_name,
                           courseIncomeLabels=courseIncomeLabels,
                           courseIncome=courseIncomeShow(accounts),
                           pagination=pagination)


@main.route('/income', methods=['GET'])
@login_required
def income():
    current_term = current_app.config['CURRENT_TERM']
    query_term = request.args.get('query_term', current_term, type=str)
    generateAccount()
    courseIncomeLabels = ['班级', '实收', '授课老师', '授课老师费', '助教', '助教费', '利润']
    currentChargeCourseInfos = getQueryChargeCourseInfos(query_term)
    incomes = [courseIncomeShowAll(courseInfo) for courseInfo in currentChargeCourseInfos]
    incomes.append(['', calSummary(incomes, 1),
                    '', calSummary(incomes, 3),
                    '', calSummary(incomes, 5),
                    calSummary(incomes, 6)])
    return render_template('auth/course_income_home.html',
                           courseIncomeLabels=courseIncomeLabels,
                           courseIncome=incomes,
                           query_term_str=courseInfoIDToStr(query_term))


@main.route('/quartReport', methods=['GET'])
@login_required
def quartReport():
    generateAccount()
    current_term = current_app.config['CURRENT_TERM']
    query_term = request.args.get('query_term', current_term, type=str)
    quartReportLabels = ['项目', '收入', '支出', '时间']
    quartReportContent = quartReportIncomeShow(query_term)
    quartReportContent.extend(quartReportPayShow(query_term))
    quartReportContent.append(['共计', calSummary(quartReportContent, 1),
                               calSummary(quartReportContent, 2),
                               datetime.now().strftime("%m/%d")])
    quartReportContent.append(['本期结余：' + str(quartReportContent[-1][1] - quartReportContent[-1][2])])
    return render_template('auth/quart_report.html',
                           quartReportLabels=quartReportLabels,
                           quartReport=quartReportContent,
                           query_term_str=courseInfoIDToStr(query_term))


@main.route('/courseManage', methods=['GET'])
@login_required
def courseManage():
    page = request.args.get('page', 1, type=int)
    current_term = current_app.config['CURRENT_TERM']
    query_term = request.args.get('query_term', current_term, type=str)
    pagination = CourseInfo.query.filter(CourseInfo.id.like(query_term + '___')).paginate(page, per_page=1)
    course_query = Course.query.filter(Course.course_info_id == pagination.items[0].id,
                                       Course.order_status.in_([0, 4, 7])) \
        .order_by(Course.seat_id, Course.last_updated_at).all()
    course_query_other = Course.query.filter(Course.course_info_id == pagination.items[0].id,
                                             Course.order_status.in_([1, 2, 3, 6])).order_by(~Course.order_status).all()
    courseManageLabels = ['序号', '座位号', '姓名', '家长手机号', '性别', '学校', '年级', '赠书', '确认', '报名时间']
    courseManageOtherLabels = ['序号', '姓名', '家长手机号', '性别', '学校', '年级', '目前状态', '报名时间']
    return render_template('auth/course_manage.html',
                           course=pagination.items[0].location + pagination.items[0].show_name,
                           courseManageLabels=courseManageLabels,
                           courseManageOtherLabels=courseManageOtherLabels,
                           courseContent=courseManageShow(course_query),
                           courseOtherContent=courseManageOtherShow(course_query_other),
                           pagination=pagination,
                           query_term=query_term)


@main.route('/schoolQuery')
@login_required
def schoolQuery():
    grade_set = getGradeSet()
    gender_set = getGenderSet()
    school_str = request.args.get('school_str', None, type=str)
    t_students = Student.query.filter().order_by(Student.school, Student.grade, Student.real_name).all()
    studentsLabels = ['序号', '年级', '姓名', '家长手机号', '性别', '参加班级(已经学习年份季度信奥/Python)']
    if school_str is None:
        studentsLabels = ['序号', '学校', '年级', '姓名', '家长手机号', '性别', '参加班级(已经学习年份季度信奥/Python)']
    students = []
    for student in t_students:
        schools = extendedInfoToArray(student.extended_info)
        if school_str is None:
            students.append([
                student.school,
                student.grade,
                student.real_name,
                student.mobile_phone,
                gender_set[student.gender],
                getStudentCourseStr(student.id)
            ])
        elif school_str == student.school:
            students.append([
                student.grade,
                student.real_name,
                student.mobile_phone,
                gender_set[student.gender],
                getStudentCourseStr(student.id)
            ])
        elif school_str in schools:
            students.append([
                13,
                student.real_name,
                student.mobile_phone,
                gender_set[student.gender],
                getStudentCourseStr(student.id)
            ])
    students.sort(key=lambda kv: (kv[0], kv[1]))
    if school_str is None:
        for student in students:
            student[1] = grade_set[student[1]]
        school_str = '全部学校'
    else:
        for student in students:
            student[0] = grade_set[student[0]]
    return render_template('auth/school_query.html',
                           studentsLabels=studentsLabels,
                           students=students,
                           school_str=school_str
                           )

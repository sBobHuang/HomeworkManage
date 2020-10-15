#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
from flask import request, current_app
from flask_moment import datetime
from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError

from . import main
from .api_exception import ApiSuccess, RegisterSuccess, AuthFailed, UpdateSuccess, ViewSuccess, RepeatError, \
    DeleteSuccess, EmptyError, RegisterFailed, SetSeatError
from .. import db
from ..auth.views import confirmCourse
from ..enum import OrderStatus
from ..fuc import getCourseInfoSet, getCourseDetailStr, getCurrentCourseInfos, getNextCourseInfos, \
    extendedInfoAdd, extendedInfoToDic, sendSMS, getCurrentChargeCourses, getOneCourses, getOneCourseInfo, \
    courseCancelInTable, getALLCourseOfStatus, getCurrentAccounts, getCourseIsDisable, \
    getCourseIsFinish, getAllCourseInfoSet, courseInfoIDToStr, extendedInfoArrayAdd, getSchoolMappingsSet, \
    ConfirmCourseFuc
from ..models import User, Student, Course, CourseInfo, WxUser, CourseCancel, SchoolMapping


@main.route('/v1/allCourse', methods=['GET'])
def allCourse():
    currentCourseInfos = getCurrentCourseInfos()
    content = [CourseInfo.courseToArr(i) for i in currentCourseInfos if getCourseIsFinish(i.id) is False]
    return ViewSuccess(msg="请求课程成功", data=content)


@main.route('/v1/sendSms', methods=['POST'])
def sendSms():
    # 发送短信
    data = request.json
    telNum = data.get('telNum')
    code = data.get('code')
    print(code)
    if not telNum or not code:
        return EmptyError()
    SMS_APP_ID = 1400372129
    SMS_APP_KEY = '11'
    template_id_login = 609917
    sms_sign = '天天快乐编程'
    ssender = SmsSingleSender(SMS_APP_ID, SMS_APP_KEY)
    try:
        result = ssender.send_with_param(86, telNum, template_id_login,
                                         [code], sign=sms_sign, extend="", ext="")
    except HTTPError as e:
        print(e)
    except Exception as e:
        print(e)
    print(result)
    return UpdateSuccess(msg="短信发送成功")


@main.route('/v1/addUser', methods=['POST'])
def addUser():
    data = request.json
    app_id = current_app.config.get('APP_ID')
    app_secret = current_app.config.get('APP_SECRET')
    code = data.get('code')
    if not code:
        raise AuthFailed()
    response = request_wx_api(app_id, app_secret, code)
    wxuser = WxUser.query.filter_by(id=response['openid']).first()
    if not wxuser:
        WxUser.insert(response['openid'], data)
        return RegisterSuccess(msg=u'用户信息保存成功', data=[response['openid']])
    else:
        wxuser.update(data)
        user = User.query.filter_by(wxid=response['openid']).first()
        if not user:
            return UpdateSuccess(msg=u'用户信息更新成功', data=[response['openid']])
        else:
            return UpdateSuccess(msg=u'用户已注册', data=[response['openid'], user.mobile_phone])


@main.route('/v1/get-enrollment', methods=['GET'])
def getEnrollment():
    currentCourseInfos = getCurrentCourseInfos()
    content = courseFilter(currentCourseInfos)
    return UpdateSuccess(msg="课程情况获取成功", data=content)


@main.route('/v1/transformEnrollment/<course_info_id>', methods=['GET'])
def transformEnrollment(course_info_id):
    location = str(course_info_id)[3]
    nextCourseInfos = getNextCourseInfos(location)
    content = courseFilter(nextCourseInfos)
    return UpdateSuccess(msg="课程情况获取成功", data=content)


@main.route('/v1/enrollmentConfirm', methods=['POST'])
def enrollmentConfirm():
    data = request.json
    course_info_id = data.get("course_info_id")
    id = data.get("course_id")
    course = Course.query.filter_by(id=id).first()
    add_course = Course(
        course_info_id=course_info_id,
        mobile_phone=course.mobile_phone,
        order_status=1,
        real_name=course.real_name,
        student_id=course.student_id
    )
    return addCourse(add_course)


@main.route('/v1/get-seats/<course_info_id>', methods=['GET'])
def getSeats(course_info_id):
    course_query = Course.query.filter(Course.course_info_id == course_info_id, Course.seat_id.isnot(None)).all()
    # 5排6列
    vis = [[1] * 8 for i in range(5)]
    names = [[''] * 8 for i in range(5)]
    for course in course_query:
        seat_id = course.seat_id - 1
        if seat_id >= 30:
            continue
        col = seat_id % 6 + seat_id % 6 // 2
        vis[seat_id // 6][col] = 3
        names[seat_id // 6][col] = course.real_name
    for i in range(5):
        vis[i][2] = 0
        vis[i][5] = 0
        vis.append(names[i])
    location = str(course_info_id)[3]
    if location == '0':
        # 临海25和26不可选
        disabled_set = [25, 26]
        for disabled in disabled_set:
            seat_id = disabled - 1
            col = seat_id % 6 + seat_id % 6 // 2
            if vis[seat_id // 6][col] == 1:
                vis[seat_id // 6][col] = 3
                names[seat_id // 6][col] = '不可选'
    return UpdateSuccess(msg="座位情况获取成功", data=vis)


@main.route('/v1/set-seatid', methods=['POST'])
def setSeatID():
    data = request.json
    seat_id = data.get("seat_id")
    id = data.get("id")
    course = Course.query.filter_by(id=id).first()
    if getCourseIsDisable(course.course_info_id):
        return SetSeatError()
    if course.seat_id is not None:
        print(course.real_name, '从', course.seat_id, '换到了', seat_id)
        if setSeat(course, seat_id):
            return RegisterFailed(msg="选座失败，您的位置已被抢走")
        return RegisterFailed(msg="您的座位已更改～")
    print(course.real_name, '选择了', seat_id)
    if course.order_status == 1:
        course.last_updated_at = datetime.utcnow()
        course.order_status = 2
    if setSeat(course, seat_id):
        return RegisterFailed(msg="选座失败，您的位置已被抢走")
    courseInfo_query = CourseInfo.query.filter_by(id=course.course_info_id).first()
    return UpdateSuccess(msg="选座成功，请在一小时内进行缴费，否则座位将放弃！", data=[courseInfo_query.price])


def setSeat(course, seat_id):
    course.seat_id = seat_id
    db.session.add(course)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return 1
    print('更改成功')
    return 0


@main.route('/v1/addNormalUser', methods=['POST'])
def addNormalUser():
    data = request.json
    user_name = data.get("user_name")
    mobile_phone = data.get("mobile_phone")
    password = data.get("password")
    user = User(mobile_phone=mobile_phone,
                username=user_name,
                password=password)
    db.session.add(user)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return RegisterFailed(msg="注册失败，请换个用户名")
    return RegisterSuccess(msg="注册成功")


@main.route('/v1/Userlogin', methods=['POST'])
def Userlogin():
    data = request.json
    user_name = data.get("user_name")
    password = data.get("password")
    user = User.query.filter_by(username=user_name).first()
    if user is not None and user.verify_password(password):
        return RegisterSuccess(msg="登录成功")
    user = User.query.filter_by(mobile_phone=user_name).first()
    if user is not None and user.verify_password(password):
        return RegisterSuccess(msg="登录成功")
    return RegisterFailed(msg="登录失败，请检查您的账号密码")


@main.route('/v1/enrollment', methods=['POST'])
def wxEnrollment():
    data = request.json
    real_name = data.get("real_name")
    mobile_phone = data.get("mobile_phone")
    school = data.get("school")
    grade = data.get("grade")
    gender = int(data.get("gender"))
    location = data.get("location")
    category = data.get("category")
    course_name = data.get("course_name")
    current_term = current_app.config['CURRENT_TERM']
    course_info_id = current_term + str(location) + str(category) + str(course_name)
    order_status = 1
    if category == 0 or category >= 4:
        order_status = 0
    student = Student.query.filter_by(real_name=real_name, mobile_phone=mobile_phone).first()
    if getCourseIsFinish(course_info_id):
        return RegisterFailed(msg="该课程已经结束，报名失败，请选择其他时段。有问题请联系黄老师")
    if student is None:
        student = Student(real_name=real_name,
                          mobile_phone=mobile_phone,
                          school=school,
                          grade=grade,
                          gender=gender)
        db.session.add(student)
    else:
        student.extended_info = extendedInfoArrayAdd(student.extended_info, student.school)
        student.school = school
        student.grade = grade
        db.session.add(student)
        print(student.real_name, '已注册', '学生id为', student.id, school, student.extended_info)
    course = Course(
        course_info_id=course_info_id,
        mobile_phone=mobile_phone,
        order_status=order_status,
        real_name=real_name)
    if category == 4:
        course_query = Course.query.filter(Course.course_info_id.like(course_info_id[0:5] + '_'),
                                           Course.student_id == student.id).first()
        if course_query is not None:
            # course_info_query = CourseInfo.query.filter_by(id=course.course_info_id).first()
            return RepeatError(msg="您已经已经报名了公益讲座")
        course.student_id = student.id
        db.session.add(course)
        db.session.commit()
        return RegisterFailed(msg="公益讲座报名成功")
    if category == 0:
        enrollment_number = len(Course.query.filter_by(course_info_id=course_info_id, order_status=0).all())
    else:
        enrollment_number = len(Course.query.filter_by(course_info_id=course_info_id, order_status=4).all())
    if category == 0 and enrollment_number >= 20 or enrollment_number >= 30:
        course = CourseCancel(
            course_info_id=course_info_id,
            mobile_phone=course.mobile_phone,
            real_name=course.real_name,
            extended_info=extendedInfoAdd(None, 'NoSpace', 1)
        )
        db.session.add(course)
        if category == 0:
            return RegisterFailed(msg="该公益课已经满员，报名失败，请等待下一次。有问题请联系黄老师")
        else:
            return RegisterFailed(msg="该课程已经满员，报名失败，请等待下一次。有问题请联系黄老师")
    if category == 0:
        course_query = Course.query.filter(Course.course_info_id.like(course_info_id[0:5] + '_'),
                                           Course.student_id == student.id).first()
        if course_query is not None:
            # course_info_query = CourseInfo.query.filter_by(id=course.course_info_id).first()
            return RepeatError(msg="该学生已经报名了公益课")
        course.student_id = student.id
        db.session.add(course)
        db.session.commit()
        courseInfoSet = getCourseInfoSet()
        ConfirmCourseFuc(course.id)
        return RegisterSuccess(msg='报名成功', data=[course.id, course.course_info_id,
                                                 getCourseDetailStr(course.course_info_id, courseInfoSet)])
    course_query = Course.query.filter_by(course_info_id=course.course_info_id, student_id=student.id).first()
    if course_query is not None:
        # course_info_query = CourseInfo.query.filter_by(id=course.course_info_id).first()
        return RepeatError(msg="该学生已经报名过这个课程", data=[course_query.id, course.course_info_id])
    else:
        course.student_id = student.id
        course_query = Course.query.filter_by(course_info_id=course.course_info_id, student_id=student.id).first()
        return addCourse(course)


def addCourse(course):
    if getCourseIsDisable(course.course_info_id):
        course.order_status = 2
        db.session.add(course)
        db.session.commit()
        courseInfo = getOneCourseInfo(course.course_info_id)
        return SetSeatError(data=[course.id, course.course_info_id, courseInfo.price])
    db.session.add(course)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return RegisterFailed(msg="报名失败")
    courseInfoSet = getCourseInfoSet()
    return RegisterSuccess(msg='报名成功', data=[course.id, course.course_info_id,
                                             getCourseDetailStr(course.course_info_id, courseInfoSet)])


@main.route('/v1/modifyUser', methods=['POST'])
def modifyUser():
    data = request.json
    wxid = data.get('wxid')
    mobile_phone = data.get('mobile_phone')
    user = User.query.filter_by(mobile_phone=mobile_phone).first()
    if not user:
        user = User(wxid=wxid, mobile_phone=mobile_phone)
        try:
            db.session.add(user)
        except e:
            print(e)
            db.session.rollback()
        return RegisterSuccess(msg='手机号保存成功')
    else:
        print('即将删除用户', user)
        db.session.remove(user)
        return DeleteSuccess(msg='删除手机号成功')


@main.route('/v1/payType', methods=['GET'])
def payType():
    payTypes = current_app.config['CURRENT_PAY_TYPE']
    return ViewSuccess(msg="支付方式获取成功", data=payTypes)


@main.route('/v1/phoneNumberQuery/', methods=['GET'])
def phoneNumberQueryNone():
    return ViewSuccess(msg="可以绑定")


@main.route('/v1/phoneNumberQuery/<mobile_phone>', methods=['GET'])
def phoneNumberQuery(mobile_phone):
    user = User.query.filter_by(mobile_phone=mobile_phone).first()
    if mobile_phone != '' and not user:
        return ViewSuccess(msg="可以绑定")
    else:
        return RegisterFailed()


@main.route('/v1/order/<mobile_phone>', methods=['GET'])
def order(mobile_phone):
    if mobile_phone == current_app.config['FLASK_ADMIN']:
        courses = getCurrentChargeCourses()
    else:
        courses = Course.query.filter_by(mobile_phone=mobile_phone).order_by(Course.created_at.desc()).all()
    if len(courses) == 0:
        return RegisterFailed(msg="您暂时还没有报名，请前往报名页面")
    # 标题 XXX已报名 2020暑假 临海 信奥基础班
    # 内容 具体班级，座位号
    # id
    # 支付状态
    # course_info_id
    # price
    # seat 展示名称
    a = []
    courseInfoSet = getAllCourseInfoSet()
    for course in courses:
        courseInfo = courseInfoSet[course.course_info_id]
        content = courseInfo.course_name + '(' + courseInfo.course_period + ')'
        if course.seat_id is not None:
            if course.order_status == 2:
                content = content + '您已选择' + str(course.seat_id) + '号座位'
            else:
                content = content + '您的座位号为' + str(course.seat_id)
        if courseInfo.location == '临海':
            content += ',学高教育邮政校区'
        else:
            content += ',周周清教育'
        json_dic = extendedInfoToDic(course.extended_info)
        book = ''
        if str(course.course_info_id)[4] != '0':
            if json_dic.get('book_free') is None:
                book = '，本期未参加赠书活动'
            else:
                book = '，本期已参加赠书活动'
        status = course.order_status
        # confirmed_set = [203100, 203101, 203102]
        confirmed_set = []
        if course.course_info_id in confirmed_set:
            if course.order_status in [0, 4]:
                json_dic = extendedInfoToDic(course.extended_info)
                if json_dic.get('confirmTime') is None:
                    status = 5
        a.append([course.real_name + '已报名' + courseInfoIDToStr(
            course.course_info_id) + courseInfo.location + courseInfo.course_level + book,
                  content,
                  course.id,
                  status,
                  course.course_info_id,
                  courseInfo.price,
                  getCourseDetailStr(courseInfo.id, courseInfoSet)
                  ])
    return RegisterSuccess(msg="获取报名信息成功", data=a)


@main.route('/v1/confirmTimeID/<course_info_id>', methods=['GET'])
def confirmTimeID(course_info_id):
    courses = Course.query.filter(course_info_id == Course.course_info_id,
                                  Course.order_status.in_([0, 4])).all()
    for course in courses:
        confirmTime(course.id)
    courses = Course.query.filter(course_info_id == Course.course_info_id,
                                  Course.order_status.in_([1, 2, 3])).all()
    for course in courses:
        course.seat_id = None
        course.order_status = 2
        db.session.add(course)
    return RegisterSuccess(msg="确认短信发送成功～")


@main.route('/v1/confirmTime/<course_id>', methods=['GET'])
def confirmTime(course_id):
    course = Course.query.filter_by(id=course_id).first()
    json_dic = extendedInfoToDic(course.extended_info)
    if json_dic.get('confirmTime') is not None:
        print(course.real_name, '已确认过')
        return RegisterFailed(msg='短信已经发送过')
    course.extended_info = extendedInfoAdd(course.extended_info, 'confirmTime', 1)
    db.session.add(course)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return RegisterFailed(msg="确认失败，请联系黄老师！")
    telNum = course.mobile_phone
    real_name = course.real_name
    course_info_id = course.course_info_id
    courseInfo = CourseInfo.query.filter_by(id=course_info_id).first()
    course_str = '秋季'
    if str(course_info_id)[4] == '0':
        course_str = course_str + '信奥公益课'
    elif str(course_info_id)[4] == '1':
        course_str = course_str + '信奥'
    else:
        course_str = course_str + 'Python'
    course_str = course_str + courseInfo.course_name
    loc = '椒江周周清教育'
    if courseInfo.location == '临海':
        loc = '临海学高教育邮政校区'
    course_date = courseInfo.course_period.split(' ')
    if str(course.course_info_id)[4] == '0':
        result = sendSMS(telNum, 718951, [real_name, course_str, course_date[0], course_date[1], course_date[2], loc])
    else:
        json_dic = extendedInfoToDic(course.extended_info)
        if json_dic.get('book_free') is None:
            book = '未'
        else:
            book = '已'
        if course.seat_id is None:
            seat_id = '待定'
        else:
            seat_id = course.seat_id
        if courseInfo.course_level == '信奥基础班':
            result = sendSMS(telNum, 668897,
                             [real_name, course_str, course_date[0], course_date[1], loc, book, seat_id])
        else:
            result = sendSMS(telNum, 711235,
                             [real_name, course_str, course_date[0], course_date[1], loc, seat_id])
    if result['result'] == 0:
        print(real_name, '发送成功!')
    else:
        print(real_name, '未发送成功!', result)
    return RegisterSuccess(msg="已确认，即将发送短信～")


@main.route('/v1/confirmPay/<course_id>', methods=['GET'])
def confirmPay(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course.order_status != 2:
        return RegisterFailed(msg='请确定是否已支付或者未选座！')
    course.order_status = 3
    course.last_updated_at = datetime.utcnow()
    db.session.add(course)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return RegisterFailed(msg='支付状态更新失败！')
    return RegisterSuccess(msg='您已确认完成课程的缴费，请尽快添加黄老师微信为您确认座位')


@main.route('/v1/confirmPay', methods=['POST'])
def confirmPAY():
    data = request.json
    course_id = data.get('course_id')
    pay_type = data.get('pay_type')
    course = Course.query.filter_by(id=course_id).first()
    if course.order_status != 2:
        return RegisterFailed(msg='请确定是否已支付或者未选座！')
    course.order_status = 3
    course.last_updated_at = datetime.utcnow()
    course.extended_info = extendedInfoAdd(course.extended_info, 'pay_type', pay_type)
    db.session.add(course)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return RegisterFailed(msg='支付状态更新失败！')
    return RegisterSuccess(msg='您已确认完成课程的缴费，请尽快添加黄老师微信为您确认座位')


@main.route('/v1/cancel/<course_id>', methods=['GET'])
def cancel(course_id):
    course = Course.query.filter_by(id=course_id).first()
    # 默认取消成功
    msg = '取消报名成功！'
    order_status = -2
    if course.order_status == OrderStatus.OrderFinish.value:
        return RegisterFailed(msg='该课程已经结束，取消报名失败！')
    if course.order_status == 4:
        msg = msg + '当前订单涉及款项，请主动联系Bob老师为你退款'
        course.order_status = OrderStatus.WaitRefund.value
        course.last_updated_at = datetime.utcnow()
        db.session.add(course)
    else:
        courseCancelInTable(course)
    return RegisterSuccess(msg=msg)


def request_wx_api(app_id, app_secret, code):
    """
    # 请求微信接口
    :param app_id:
    :param app_secret:　
    :param code: 用户登录凭证
    """
    errcode = {
        '-1': u'系统繁忙，此时请开发者稍候再试',
        '40029': u'code无效',
        '45011': u'频率限制，每个用户每分钟100次',
    }
    response = requests.get(current_app.config.get('AUTH_LOGIN_URL').format(app_id, app_secret, code))
    response.encoding = response.apparent_encoding
    content = response.json()
    if 'errcode' in content.keys() and content.get('errcode') != 0:
        raise AuthFailed(errcode[content.get('errcode')])
    return content


def courseFilter(course_infos):
    return [optionCovert(course_info) for course_info in course_infos]


def optionCovert(course_info):
    item = course_info.course_name + '(' + course_info.course_period + ')'
    return [course_info.id, item]


@main.route('/v1/courSeRecovery', methods=['GET'])
def courSeRecovery():
    fp = open('data.txt')
    content = fp.read()
    items = content.split('\n')
    items_length = len(items)
    i = 0
    while i < items_length:
        course = Course(
            id=items[i],
            course_info_id=items[i + 1],
            mobile_phone=items[i + 2],
            real_name=items[i + 3],
            student_id=items[i + 4],
            order_status=items[i + 5],
            seat_id=items[i + 6],
            user_id=items[i + 7],
            created_at=items[i + 8],
            last_updated_at=items[i + 9],
            extended_info=items[i + 10],
        )
        course.id = int(course.id)
        course.order_status = int(course.order_status)
        if course.seat_id == 'NULL':
            course.seat_id = None
        if course.extended_info == 'NULL':
            course.extended_info = None
        course.created_at = datetime.strptime(course.created_at, "%Y-%m-%d %H:%M:%S.%f")
        course.last_updated_at = datetime.strptime(course.last_updated_at, "%Y-%m-%d %H:%M:%S.%f")
        i = i + 11
        db.session.add(course)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            print(course.__dict__)
            print(course.real_name, '恢复失败')
    return RegisterSuccess('插入报名')


@main.route('/v1/OrderFinish/<course_info_id>', methods=['GET'])
def OrderFinish(course_info_id):
    courseInfo = getOneCourseInfo(course_info_id)
    courses = getOneCourses(course_info_id)
    for course in courses:
        course.order_status = OrderStatus.OrderFinish.value
        course.last_updated_at = datetime.utcnow()
        db.session.add(course)
    db.session.commit()
    return ApiSuccess(courseInfo.location + courseInfo.show_name + '已经上完课')


@main.route('/v1/batchCancelCourse', methods=['GET'])
def batchCancelCourse():
    courses = getALLCourseOfStatus(OrderStatus.Cancel.value)
    for course in courses:
        courseCancelInTable(course)
    db.session.commit()
    return ApiSuccess('取消课程已全部更新到另一张表')


@main.route('/v1/oldDiscount', methods=['GET'])
def oldDiscount():
    accounts = getCurrentAccounts()
    courseInfoSet = getCourseInfoSet()
    disabled_set = ['林暄博']
    for account in accounts:
        if courseInfoSet[account.course_info_id].course_level[-3:] == '基础班':
            continue
        if account.real_name not in disabled_set and account.fee == courseInfoSet[account.course_info_id].price:
            account.fee = account.fee // 10 * 9
            account.last_updated_at = datetime.utcnow()
            db.session.add(account)
    return ApiSuccess('请求成功')


@main.route('/v1/confirmTimeIDAdmin/<course_info_id>', methods=['GET'])
def confirmTimeIDAdmin(course_info_id):
    courses = Course.query.filter(course_info_id == Course.course_info_id,
                                  Course.order_status.in_([0, 4, 7])).all()
    for course in courses:
        course.extended_info = extendedInfoAdd(course.extended_info, 'confirmTime', 1)
        db.session.add(course)
    return RegisterSuccess(msg="确认短信发送系统记录成功～")


@main.route('/v1/clearCourse', methods=['GET'])
def clearCourse():
    courses = Course.query.filter_by(order_status=OrderStatus.InfoSuccess.value).all()
    for course in courses:
        course_query = Course.query.filter_by(course_info_id=course.course_info_id,
                                              order_status=OrderStatus.OrderFinish.value).first()
        course_info_query = getOneCourseInfo(course.course_info_id)
        if course_query is not None or course_info_query is None \
                or getCourseIsDisable(course.course_info_id):
            courseCancelInTable(course)
    courses = Course.query.filter_by().all()
    courseInfoSet = getAllCourseInfoSet()
    for course in courses:
        if courseInfoSet.get(course.course_info_id) is None \
                or course.mobile_phone == current_app.config['FLASK_ADMIN'] \
                or course.mobile_phone == '17857463110':
            courseCancelInTable(course)
    courses = CourseCancel.query.filter_by().all()
    for course in courses:
        if course.mobile_phone == current_app.config['FLASK_ADMIN'] \
                or course.mobile_phone == '17857463110':
            db.session.delete(course)
    students = Student.query.filter_by().all()
    for student in students:
        if student.mobile_phone == current_app.config['FLASK_ADMIN'] \
                or student.mobile_phone == '17857463110':
            db.session.delete(student)
    db.session.commit()
    return ApiSuccess('垃圾课程已全部更新到另一张表')


@main.route('/v1/clearStu', methods=['GET'])
def clearStu():
    courses = Course.query.filter_by().all()
    for course in courses:
        student = Student.query.filter(Student.real_name.like('%' + course.real_name + '%'),
                                       Student.mobile_phone == course.mobile_phone).all()
        if len(student) != 1 and len(student) != 0:
            print(course.real_name, course.student_id)
            for i in range(len(student)):
                print(student[i].id, student[i].real_name, '被删除')
                db.session.delete(student[i])
            db.session.add(student[-1])
            for t_course in courses:
                if t_course.real_name == course.real_name \
                        and t_course.mobile_phone == course.mobile_phone \
                        and t_course.student_id != student[-1].id:
                    print(t_course.real_name, 'id从', t_course.student_id, '到', student[-1].id)
                    t_course.student_id = student[-1].id
                    db.session.add(t_course)
    # 数据丢失 id 是308
    courses = Course.query.filter_by().all()
    for course in courses:
        student = Student.query.filter_by(id=course.student_id).first()
        if student is None:
            student = Student.query.filter_by(real_name=course.real_name,
                                              mobile_phone=course.mobile_phone).first()
            if student is not None:
                course.student_id = student.id
                db.session.add(course)
            else:
                stu = Student(
                    id=course.student_id,
                    mobile_phone=course.mobile_phone,
                    real_name=course.real_name,
                    school='数据丢失',
                    gender=2,
                    grade=10
                )
                db.session.add(stu)
    student = Student.query.filter(Student.real_name.like('%1%')).all()
    for stu in student:
        real_name = stu.real_name.replace('1', '')
        t_stu = Student.query.filter_by(real_name=real_name).first()
        if t_stu is not None:
            db.session.delete(t_stu)
        db.session.commit()
        stu.real_name = real_name
        db.session.add(stu)
    return ApiSuccess('query and update student')


@main.route('/v1/addSchoolMapping', methods=['GET'])
def addSchoolMapping():
    fp = open('school.txt')
    contents = fp.read().split('\n')
    for line in contents:
        items = line.split(' ')
        if len(items) < 3:
            print(line, '数据不完整')
            continue
        school = SchoolMapping(
            user_in=items[0],
            location=items[1],
            school=items[2]
        )
        db.session.add(school)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            print(items[0], '已存在')
    school_mappings = SchoolMapping.query.filter().all()
    for school_mapping in school_mappings:
        school = SchoolMapping(
            user_in=school_mapping.school,
            location=school_mapping.location,
            school=school_mapping.school
        )
        db.session.add(school)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            print(school_mapping.school, '已存在')
    updateSchool()
    return ApiSuccess('query and update school mapping')


@main.route('/v1/updateSchool', methods=['GET'])
def updateSchool():
    school_mappingsSet = getSchoolMappingsSet()
    students = Student.query.filter().all()
    for student in students:
        student.extended_info = extendedInfoArrayAdd(student.extended_info, student.school)
        if school_mappingsSet.get(student.school):
            student.school = school_mappingsSet[student.school].school
        else:
            school = SchoolMapping(
                user_in=student.school,
                school='待分类'
            )
            db.session.add(school)
        db.session.add(student)
    return ApiSuccess('update student school')

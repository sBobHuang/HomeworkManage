from flask import current_app
from flask_moment import datetime
import json

from qcloudsms_py import SmsSingleSender
from qcloudsms_py.httpclient import HTTPError
from sqlalchemy import func, or_, and_

from app.enum import PayType, OrderStatus
from app.models import CourseInfo, Account, Student, Course, CourseCancel, SchoolMapping
from . import db
from .main.api_exception import RegisterSuccess


def noneToInt(num):
    if num is None:
        return 0
    return num


def noneToNull(num):
    if num is None:
        return ''
    return num


def calSummary(content, i):
    summary = 0
    for item in content:
        if item[i] == '':
            continue
        summary = summary + item[i]
    return summary


def getPayType(extended_info):
    if extended_info is not None:
        json_dic = json.loads(extended_info)
    else:
        json_dic = {}
    payType = json_dic.get('pay_type')
    if payType is None:
        payType = PayType.unknown.value
    return payType


def courseShows(enrollments, courseInfos):
    return [courseShow(enrollment, courseInfos) for enrollment in enrollments]


def courseShow(enrollment, courseInfos):
    courseInfo = courseInfos[enrollment.course_info_id]
    course_info_id = courseInfo.id
    course_str = courseInfo.location + courseInfo.show_name
    payType = getPayType(enrollment.extended_info)
    msg = '无优惠'
    account = Account.query.filter_by(course_id=enrollment.id).first()
    if account is None:
        price = courseInfo.price
    else:
        price = account.fee
    if getIsDiscount(enrollment.real_name, enrollment.mobile_phone):
        msg = '该生可以享受9折优惠¥' + str(courseInfo.price // 10 * 9)
    return [enrollment.last_updated_at, enrollment.real_name,
            enrollment.mobile_phone, price, course_str, payType,
            enrollment.order_status, enrollment.id, course_info_id, enrollment.seat_id, msg]


def courseIncomeShow(accounts):
    courseIncome = []
    total = ['合计', 0, 0, 0]
    for account in accounts:
        if noneToInt(account.fee) < 0:
            continue
        total[1] = total[1] + noneToInt(account.fee) + noneToInt(account.refund_fee)
        total[2] = total[2] + noneToInt(account.refund_fee)
        total[3] = total[3] + noneToInt(account.fee)
        courseIncome.append(
            [account.real_name, noneToInt(account.fee) + noneToInt(account.refund_fee), noneToNull(account.refund_fee),
             noneToNull(account.fee)])
    courseIncome.append(total)
    return courseIncome


def getCourseInfoSet():
    currentCourseInfos = getCurrentCourseInfos()
    courseInfoSet = {}
    for item in currentCourseInfos:
        courseInfoSet[item.id] = item
    return courseInfoSet


def getAllCourseInfoSet():
    currentCourseInfos = getAllCourseInfos()
    courseInfoSet = {}
    for item in currentCourseInfos:
        courseInfoSet[item.id] = item
    return courseInfoSet


def getGenderSet():
    return {
        0: '男',
        1: '女',
        2: '未填写'
    }


def getPayTypeSet():
    return {PayType.weixin.value: '微信支付',
            PayType.alipay.value: '支付宝',
            PayType.cardTransfer.value: '银行卡转账',
            PayType.refund.value: '退款',
            PayType.payToTeacher.value: '授课老师',
            PayType.payToAssistant.value: '助教',
            PayType.Others.value: '其他'}


def getOrderStatusSet():
    return {
        -2: '退款成功',
        -1: '有退款，还在等待',
        0: '公益课报名成功',
        1: '报名信息填写成功',
        2: '已选座位',
        3: '缴费待确认',
        4: '报名成功',
        6: '部分退费',
        7: '已结束'
    }


def getGradeSet():
    return {
        4: '四年级',
        5: '五年级',
        6: '六年级',
        7: '初一',
        8: '初二',
        9: '初三',
        10: '高一',
        11: '高二',
        12: '高三',
        13: '已毕业'
    }


def courseManageShow(courses):
    grade_set = getGradeSet()
    gender_set = getGenderSet()
    courseManage = []
    for course in courses:
        student = Student.query.filter_by(id=course.student_id).first()
        if student is None:
            student = Student.query.filter_by(id=308).first()
        json_dic = extendedInfoToDic(course.extended_info)
        if json_dic.get('book_free') is None:
            book = ''
        else:
            book = '✅'
        if json_dic.get('confirmTime') is None:
            confirm = ''
        else:
            confirm = '✅'
        courseManage.append([
            course.seat_id,
            course.real_name,
            course.mobile_phone,
            gender_set[student.gender],
            student.school,
            grade_set[student.grade],
            book,
            confirm,
            course.last_updated_at.strftime("%m/%d")
        ])
    return courseManage


def courseManageOtherShow(courses):
    if courses is None:
        return None
    grade_set = getGradeSet()
    gender_set = getGenderSet()
    order_status_set = getOrderStatusSet()
    courseManage = []
    for course in courses:
        student = Student.query.filter_by(id=course.student_id).first()
        if student is None:
            student = Student.query.filter_by(id=308).first()
        courseManage.append([
            course.real_name,
            course.mobile_phone,
            gender_set[student.gender],
            student.school,
            grade_set[student.grade],
            order_status_set[course.order_status],
            course.last_updated_at.strftime("%m/%d")
        ])
    return courseManage


def courseIncomeShowAll(course_info):
    courseIncome = db.session.query(func.sum(Account.fee)). \
        filter(Account.course_info_id == course_info.id,
               Account.pay_type < PayType.payToTeacher.value).first()
    payToTeacher = accountNoneToNull(
        Account.query.filter_by(course_info_id=course_info.id, pay_type=PayType.payToTeacher.value).all())
    payToAssistant = accountNoneToNull(
        Account.query.filter_by(course_info_id=course_info.id, pay_type=PayType.payToAssistant.value).all())
    profit = db.session.query(func.sum(Account.fee)).filter_by(course_info_id=course_info.id).first()
    return [course_info.location + course_info.show_name, noneToInt(courseIncome[0]),
            payToTeacher.real_name, payToTeacher.refund_fee,
            payToAssistant.real_name, payToAssistant.refund_fee,
            noneToInt(profit[0])]


def quartReportIncomeShow(query_term):
    currentChargeCourseInfos = getCurrentChargeCourseInfos(query_term)
    reportIncome = []
    for course_info in currentChargeCourseInfos:
        profit = db.session.query(func.sum(Account.fee)).filter_by(course_info_id=course_info.id).first()
        if profit[0] is not None:
            reportIncome.append([course_info.location + course_info.show_name,
                                 profit[0],
                                 '',
                                 datetime.now().strftime("%m/%d")])
    return reportIncome


def quartReportPayShow(query_term):
    reportPay = []
    accounts_query = Account.query.filter(Account.pay_type == PayType.Others.value,
                                          Account.course_info_id == query_term + '888').all()
    for account in accounts_query:
        if account.fee < 0:
            reportPay.append([
                account.show_name,
                '',
                account.refund_fee,
                account.last_updated_at.strftime("%m/%d")
            ])
        else:
            reportPay.append([
                account.show_name,
                account.fee,
                '',
                account.last_updated_at.strftime("%m/%d")
            ])
    return reportPay


def accountNoneToNull(accounts):
    if len(accounts) == 0:
        account_result = Account(
            real_name='',
            refund_fee=''
        )
        return account_result
    fee = 0
    real_name = []
    for account in accounts:
        real_name.append(account.real_name)
        fee = fee + account.refund_fee
    account_result = Account(
        real_name="、".join(real_name),
        refund_fee=fee
    )
    return account_result


def getCourseStr(course_info_id, courseInfoSet):
    course_str = '秋季'
    if str(course_info_id)[4] == '1':
        course_str = course_str + '信奥'
    else:
        course_str = course_str + 'Python'
    return course_str + courseInfoSet[course_info_id].course_name


def getCourseDetailStr(course_info_id, courseInfoSet):
    if str(course_info_id)[4] == '1':
        course_str = '信奥'
    else:
        course_str = 'Python'
    return course_str + courseInfoSet[course_info_id].front_name


def sendSMS(telNum, template_id, param):
    result = ''
    SMS_APP_ID = 1400372129
    SMS_APP_KEY = '11'
    template_id = template_id
    sms_sign = '天天快乐编程'
    ssender = SmsSingleSender(SMS_APP_ID, SMS_APP_KEY)
    try:
        result = ssender.send_with_param(86, telNum, template_id,
                                         param, sign=sms_sign, extend="", ext="")
    except HTTPError as e:
        print(e)
    except Exception as e:
        print(e)
    return result


def ConfirmCourseFuc(id):
    course = Course.query.filter_by(id=id).first()
    telNum = course.mobile_phone
    real_name = course.real_name
    course_info_id = course.course_info_id
    courseInfo = CourseInfo.query.filter_by(id=course_info_id).first()
    course_str = '秋季'
    category = str(course_info_id)[4]
    if category == '0':
        course_str = course_str + '信奥公益课'
    elif category == '1':
        course_str = course_str + '信奥'
    else:
        course_str = course_str + 'Python'
    course_str = course_str + courseInfo.course_name
    loc = '椒江周周清教育'
    if courseInfo.location == '临海':
        loc = '临海学高教育邮政校区'
    if course.seat_id is None:
        seat_id = '待定'
    else:
        seat_id = course.seat_id
    if category == '0':
        result = sendSMS(telNum, 718940, [real_name, course_str, loc])
        print(result)
        return RegisterSuccess(msg='试听课短信发送成功')
    else:
        result = sendSMS(telNum, 668893, [real_name, course_str, loc, seat_id])
        print(result)
    if course.order_status == 2:
        course.last_updated_at = datetime.utcnow()
        course.extended_info = extendedInfoAdd(course.extended_info, 'pay_type', 4)
    course.order_status = 4
    db.session.add(course)


def extendedInfoToArray(extended_info):
    if extended_info is None:
        return []
    return extended_info.split(',')


def extendedInfoArrayAdd(extended_info, value):
    arr = extendedInfoToArray(extended_info)
    if value not in arr:
        arr.append(value)
    return ','.join(arr)


def extendedInfoToDic(extended_info):
    dic = {}
    if extended_info is not None:
        dic = json.loads(extended_info)
    return dic


def extendedInfoAdd(extended_info, key, value):
    json_dic = extendedInfoToDic(extended_info)
    json_dic[key] = value
    return json.dumps(json_dic)


def getCurrentCourseInfos():
    current_term = current_app.config.get('CURRENT_TERM')
    return CourseInfo.query.filter(CourseInfo.id.like(current_term + '___')).all()


def getAllCourseInfos():
    return CourseInfo.query.filter().all()


def getAllStudents():
    return Student.query.filter().all()


def getCurrentChargeCourseInfos(query_term):
    return CourseInfo.query.filter(CourseInfo.id.like(query_term + '___'),
                                   ~CourseInfo.id.like(query_term + '_0_')).all()


def getNextCourseInfos(location):
    current_term = current_app.config['CURRENT_TERM']
    return CourseInfo.query.filter(CourseInfo.id.like(current_term + location + '__'),
                                   CourseInfo.course_level == '信奥基础班').all()


def getCurrentCourses():
    current_term = current_app.config['CURRENT_TERM']
    return Course.query.filter(Course.course_info_id.like(current_term + '___'),
                               Course.order_status.in_([0, 4])).all()


def getOneCourses(course_info_id):
    return Course.query.filter(Course.course_info_id == course_info_id,
                               Course.order_status.in_([0, 4])).all()


def getOneCourseInfo(course_info_id):
    return CourseInfo.query.filter_by(id=course_info_id).first()


def getCurrentChargeCourses():
    current_term = current_app.config['CURRENT_TERM']
    return Course.query.filter(Course.course_info_id.like(current_term + '___'),
                               Course.order_status == 4). \
        order_by(Course.course_info_id, Course.seat_id).all()


def getStudentCurrentChargeCourses(real_name, query_term):
    return Course.query.filter(Course.real_name.like('%' + real_name + '%'),
                               Course.course_info_id.like(query_term + '___'),
                               Course.order_status > 0).all()


def getStudentCurrentCourses(real_name):
    current_term = current_app.config['CURRENT_TERM']
    return Course.query.filter(Course.real_name.like('%' + real_name + '%'),
                               Course.course_info_id.like(current_term + '___'),
                               Course.order_status >= 0).all()


def courseCancelInTable(course):
    course_cancel = CourseCancel(
        course_info_id=course.course_info_id,
        mobile_phone=course.mobile_phone,
        real_name=course.real_name,
        created_at=course.created_at,
        last_updated_at=datetime.utcnow(),
        extended_info=course.extended_info
    )
    db.session.add(course_cancel)
    db.session.delete(course)
    return course_cancel


def getALLCourseOfStatus(order_status):
    current_term = current_app.config['CURRENT_TERM']
    return Course.query.filter(Course.course_info_id.like(current_term + '___'),
                               Course.order_status == order_status).all()


def getALLChargeCourses():
    return Course.query.filter(
        or_(
            Course.order_status == 4,
            and_(Course.order_status == 7, ~Course.course_info_id.like('____0_')),
        )).order_by(Course.course_info_id, Course.seat_id).all()


def getStuChargeCourses(real_name):
    return Course.query.filter(
        and_(
            or_(
                Course.order_status == 4,
                and_(Course.order_status == 7, ~Course.course_info_id.like('____0_')),
            ),
            Course.real_name == real_name
        )).all()


def getIsDiscount(real_name, mobile_phone):
    courses = getStuChargeCourses(real_name)
    student = Student.query.filter_by(real_name=real_name,
                                      mobile_phone=mobile_phone).first()
    if len(courses) > 1 or student.is_old is not None:
        return True
    return False


def getCurrentAccounts():
    current_term = current_app.config['CURRENT_TERM']
    return Account.query.filter(Account.course_info_id.like(current_term + '___')).all()


def getCourseIsDisable(course_info_id):
    disabled_set = [203022]
    if course_info_id in disabled_set:
        return False
    courses = Course.query.filter(Course.course_info_id == course_info_id,
                                  Course.order_status.in_([0, 4, 7])).all()
    for course in courses:
        json_dic = extendedInfoToDic(course.extended_info)
        if json_dic.get('confirmTime') is None:
            return False
    if len(courses) == 0:
        return False
    return True


def getCourseIsFinish(course_info_id):
    courseInfo = CourseInfo.query.filter_by(id=course_info_id).first()
    if courseInfo.course_period == '取消':
        return True
    course = Course.query.filter_by(course_info_id=course_info_id, order_status=OrderStatus.OrderFinish.value).first()
    if course is None:
        return False
    return True


def queryTermTypeToStr(query_term):
    return str(query_term)


def getQueryCourseInfos(query_term):
    query_term = queryTermTypeToStr(query_term)
    return CourseInfo.query.filter(CourseInfo.id.like(query_term + '___')).all()


def getQueryChargeCourseInfos(query_term):
    query_term = queryTermTypeToStr(query_term)
    return CourseInfo.query.filter(CourseInfo.id.like(query_term + '___'),
                                   ~CourseInfo.id.like(query_term + '_0_')).all()


def courseInfoIDToStr(query_term):
    if query_term is None:
        query_term = current_app.config['CURRENT_TERM']
    query_term = queryTermTypeToStr(query_term)
    return '20' + query_term[0:2] + courseInfoDigitToStr(query_term[2])


def courseInfoDigitToStr(query_term_id):
    course_term_str = '寒假'
    if query_term_id == '2':
        course_term_str = '春季'
    elif query_term_id == '3':
        course_term_str = '暑假'
    elif query_term_id == '4':
        course_term_str = '秋季'
    return course_term_str


def courseInfoIDToDetailStr(course_info_id):
    course = getOneCourseInfo(course_info_id)
    return courseInfoIDToStr(course_info_id)+course.location+course.course_level


def getSchoolMappingsSet():
    school_mappings = SchoolMapping.query.filter().all()
    school_mappingsSet = {}
    for school_mapping in school_mappings:
        school_mappingsSet[school_mapping.user_in] = school_mapping
    return school_mappingsSet


def getStudentSchoolSet():
    studentSchoolSet = {}
    students = getAllStudents()
    for student in students:
        if studentSchoolSet.get(student.school) is None:
            studentSchoolSet[student.school] = None
        studentSchoolSet[student.school] = extendedInfoArrayAdd(studentSchoolSet[student.school],
                                                                student.real_name)
    for studentSchool in studentSchoolSet:
        studentSchoolSet[studentSchool] = extendedInfoToArray(studentSchoolSet[studentSchool])
        studentSchoolSet[studentSchool] = len(studentSchoolSet[studentSchool]), studentSchoolSet[studentSchool]
    return studentSchoolSet


def getSchoolLocationSet():
    school_mappingsSet = getSchoolMappingsSet()
    school_locationSet = {}
    for school_mapping in school_mappingsSet.values():
        if school_locationSet.get(school_mapping.location) is None:
            school_locationSet[school_mapping.location] = None
        school_locationSet[school_mapping.location] = extendedInfoArrayAdd(school_locationSet[school_mapping.location],
                                                                           school_mapping.school)
    return school_locationSet


def getStudentCourseStr(ID):
    courses = Course.query.filter_by(student_id=ID).order_by(Course.last_updated_at).all()
    student_course_str = ''
    for course in courses:
        if course.order_status == 4:
            student_course_str = student_course_str + '正在学习' + courseInfoIDToDetailStr(course.course_info_id) + '\n'
        elif course.order_status > 5:
            student_course_str = student_course_str + '已经学习' + courseInfoIDToDetailStr(course.course_info_id) + '\n'
    return student_course_str

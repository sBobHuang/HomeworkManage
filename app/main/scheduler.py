import os

from flask import current_app
from flask_apscheduler import APScheduler  # 主要插件

from config import bakSqlite
from . import main
from .api_exception import UpdateSuccess
from ..fuc import getCourseInfoSet, getCourseStr, sendSMS
from ..models import Course
from app import create_app
from .. import db
from datetime import datetime, timedelta


APP = create_app('default')
scheduler = APScheduler()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(func=bakSqlite, id='3', trigger='interval', seconds=600,
                      replace_existing=True)


def task1(a, b):
    print('mession1')


def task2():
    global APP
    with APP.app_context():
        getCourse()


def getCourse():
    course_query = Course.query.filter(Course.order_status > 1, Course.order_status < 4,
                                       Course.last_updated_at < datetime.utcnow() - timedelta(hours=1)).all()
    courseInfoSet = getCourseInfoSet()
    disabled_set = []
    ok = 0
    for course in course_query:
        if course.seat_id is None:
            continue
        if course.real_name[0:2] == '交换' and course.mobile_phone == current_app.config['FLASK_ADMIN']:
            continue
        if course.real_name in disabled_set:
            continue
        course_str = getCourseStr(course.course_info_id, courseInfoSet)
        if ok == 0:
            print(datetime.utcnow(), '执行了定时任务')
            ok = 1
        print(course.real_name + '报名的' + course_str + '座位号为'+str(course.seat_id)+'将被取消')
        result = sendSMS(course.mobile_phone, 627737, [course.real_name, course_str])
        if result['result'] == 0:
            course.order_status = 1
            course.seat_id = None
            course.last_updated_at = datetime.utcnow()
            db.session.add(course)
            try:
                db.session.commit()
                print('取消成功')
            except:
                db.session.rollback()
                print('取消失败')


@main.route('/pause/<int:id>', methods=['POST'])
def pause_task(id):  # 暂停
    scheduler.pause_job(str(id))
    return UpdateSuccess(msg="暂停成功")


@main.route('/resume/<int:id>', methods=['POST'])
def resume_task(id):  # 恢复
    scheduler.resume_job(str(id))
    return UpdateSuccess(msg="恢复成功")


@main.route('/get_task', methods=['POST'])
def get_task():  # 获取
    jobs = scheduler.get_jobs()
    print(jobs)
    return UpdateSuccess(msg="获取任务成功")


@main.route('/remove_task/<int:id>', methods=['POST'])
def remove_task(id):  # 移除
    scheduler.remove_job(str(id))
    return UpdateSuccess(msg="移除任务成功")


@main.route('/add_job/<int:id>', methods=['GET', 'POST'])
def add_task(id):
    if id == 1:
        scheduler.add_job(func=task1, id='1', args=(1, 2), trigger='cron', day_of_week='0-6', hour=18, minute=19,
                          second=10,
                          replace_existing=True)
        # trigger='cron' 表示是一个定时任务
    else:
        scheduler.add_job(func=task2, id='2', trigger='interval', seconds=120,
                          replace_existing=True)
        print('添加任务成功')
        # trigger='interval' 表示是一个循环任务，每隔多久执行一次
    return UpdateSuccess(msg="添加任务成功")

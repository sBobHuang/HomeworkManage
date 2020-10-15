from flask_apscheduler import APScheduler  # 主要插件

from app import create_app
from config import bakSqlite
from . import main
from .api_exception import UpdateSuccess

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
        pass


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

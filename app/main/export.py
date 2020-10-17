import os

from flask import send_file
from flask_moment import datetime

from . import main
from ..fuc import make_zip

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前项目的绝对路径
basedir = os.path.join(basedir, "../../")


@main.route('/export', methods=['GET', 'POST'])
def exportAllHomeWork():
    save_filename1 = '作业导出' + datetime.now().strftime('%m-%d_%H_%M_%S') + '.zip'
    save_filename = os.path.join(basedir, 'Download', save_filename1)
    if not os.path.exists(os.path.join(basedir, 'Download')):
        os.makedirs(os.path.join(basedir, 'Download'))  # 文件夹不存在就创建
    make_zip(os.path.join(basedir, 'ZY'), save_filename)
    print(save_filename1)
    return send_file(save_filename, as_attachment=True, attachment_filename=save_filename1)

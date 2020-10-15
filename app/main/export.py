from flask import send_file

from . import main
import os
from datetime import datetime
from ..fuc import make_zip

basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前项目的绝对路径
basedir = os.path.join(basedir, "../../")


@main.route('/export', methods=['GET', 'POST'])
def exportAllHomeWork():
    save_filename = '学生作业' + datetime.utcnow().strftime('%m-%d %H:%M:%S') + '.zip'
    save_filename = os.path.join(basedir, 'Download', save_filename)
    make_zip(os.path.join(basedir, 'ZY'), save_filename)
    return send_file(save_filename, as_attachment=True)

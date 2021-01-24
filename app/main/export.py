import os
from flask import current_app
from flask import make_response
from flask import send_file
from flask_moment import datetime


from . import main
from ..fuc import make_zip
from ..models import Student, FileRecord
import io
import pandas as pd
from pandas import ExcelWriter
import numpy as np
from urllib.parse import quote


@main.route('/export', methods=['GET', 'POST'])
def exportAllHomeWork():
    basedir = current_app.config['BASE_DIR']
    save_filename1 = '全部作业导出-' + datetime.now().strftime('%m-%d_%H_%M_%S') + '.zip'
    save_filename = os.path.join(basedir, 'Download', save_filename1)
    if not os.path.exists(os.path.join(basedir, 'Download')):
        os.makedirs(os.path.join(basedir, 'Download'))  # 文件夹不存在就创建
    make_zip(os.path.join(basedir, 'ZY'), save_filename)
    return send_file(save_filename, as_attachment=True, attachment_filename=save_filename1)


@main.route('/export/<course_names>', methods=['GET', 'POST'])
def exportHomeWorkTable(course_names):
    print(course_names)
    students_query = Student.query.filter_by(course_names=course_names).all()
    a = []
    for stu in students_query:
        files_query = FileRecord.query.filter_by(student_id=stu.id, course_names=stu.course_names).order_by(FileRecord.home_work_id).all()
        zyRecord = []
        for i in range(1, 3):
            max = datetime(2020, 1, 1)
            for file in files_query:
                if file.home_work_id == i and file.created_at > max:
                    max = file.created_at
            if max != datetime(2020, 1, 1):
                zyRecord.append(max.strftime("%m/%d"))
            else:
                zyRecord.append('未提交')
        a.append([
            stu.id,
            stu.real_name,
            stu.class_name,
            zyRecord[0],
            zyRecord[1],
        ])
    df = pd.DataFrame(np.array(a))
    out = io.BytesIO()
    # 实例化输出xlsx的writer对象
    writer = ExcelWriter(out, engine='openpyxl')
    # 简单数据切片,选择所有行,第六列到最后一列范围
    # 对df列名重命名
    # df.rename(columns={
    #     'xm': '姓名',
    #     'sfzh': '身份证号',
    #     'csny': '出生年月',
    #     'xb': '性别',
    #     'bm': '部门',
    #     'zw': '职务',
    #     'jb': '级别',
    #     'vcode': '校验码'
    # }, inplace=True)
    # 将df转excel保存在内存writer变量中,转换结果中不要包含index行号
    df.columns = ['学号','姓名','班级','作业1上交时间','作业2上交时间']
    df.to_excel(writer,course_names,index=False)
    # 这一步不能漏了,不save的话浏览器下载的xls文件里面啥也没有
    writer.save()
    # 重置一下IO对象的指针到开头
    out.seek(0)
    # IO对象使用getvalue()可以返回二进制的原始数据,用来给要生成的response的data
    # return send_file(out.getvalue(), as_attachment=True, attachment_filename=course_names+'作业完成情况.xlsx')
    resp = make_response(out.getvalue())
    # 设置response的header,让浏览器解析为文件下载行为
    resp.headers['Content-Disposition'] = 'attachment; filename*=UTF-8"{}"'.format(course_names)
    resp.headers['Content-Type'] = 'application/vnd.ms-excel; charset=UTF-8'

    return resp


@main.route('/exportOneHomeWork/<homework_export_id>', methods=['GET', 'POST'])
def exportOneHomeWork(homework_export_id):
    files_query = FileRecord.query.filter_by(id=homework_export_id).first()
    resp = make_response(send_file(files_query.file_name))
    file_name = os.path.split(files_query.file_name)[1]
    resp.headers['Content-Disposition'] = 'attachment;filename={0}'.format(quote(file_name))
    return resp


def exportOneHomeWorks(course_name, course_names, homework_export_id):
    basedir = current_app.config['BASE_DIR']
    save_filename1 = '作业导出-' + course_names+'-'+homework_export_id + '.zip'
    save_filename = os.path.join(basedir, 'Download', save_filename1)
    file_name = os.path.join(basedir, 'ZY', course_name, course_names, homework_export_id)
    print(file_name)
    make_zip(file_name, save_filename)
    resp = make_response(send_file(save_filename))
    resp.headers['Content-Disposition'] = 'attachment;filename={0}'.format(quote(save_filename1))
    return resp
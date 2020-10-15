from flask import  make_response

from app.models import Course
import io
import pandas as pd
from pandas import ExcelWriter
from . import main


@main.route('/export', methods=['GET', 'POST'])
def exportAllCourse():
    course_query = Course.query.filter_by(order_status=4)
    out = io.BytesIO()
    # 实例化输出xlsx的writer对象
    writer = ExcelWriter(out, engine='openpyxl')
    # 将SQLAlchemy模型的查询对象拆分SQL语句和连接属性传给pandas的read_sql方法
    df = pd.read_sql(course_query.statement, course_query.session.bind)
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
    df.to_excel(writer, index=False)
    # 这一步不能漏了,不save的话浏览器下载的xls文件里面啥也没有
    writer.save()
    # 重置一下IO对象的指针到开头
    out.seek(0)
    # IO对象使用getvalue()可以返回二进制的原始数据,用来给要生成的response的data
    resp = make_response(out.getvalue())
    # 设置response的header,让浏览器解析为文件下载行为
    resp.headers['Content-Disposition'] = 'attachement; filename=course.xlsx'
    resp.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'

    return resp


@main.route('/export/<course_info_id>', methods=['GET', 'POST'])
def exportCourse(course_info_id):
    course_query = Course.query.filter(Course.course_info_id == course_info_id,
                                       Course.order_status.in_([0, 4]))
    out = io.BytesIO()
    writer = ExcelWriter(out, engine='openpyxl')
    df = pd.read_sql(course_query.statement, course_query.session.bind)
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
    df.to_excel(writer, index=False)
    # 这一步不能漏了,不save的话浏览器下载的xls文件里面啥也没有
    writer.save()
    # 重置一下IO对象的指针到开头
    out.seek(0)
    # IO对象使用getvalue()可以返回二进制的原始数据,用来给要生成的response的data
    resp = make_response(out.getvalue())
    # 设置response的header,让浏览器解析为文件下载行为
    resp.headers['Content-Disposition'] = 'attachement; filename=course.xlsx'
    resp.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    return resp


@main.route('/exportByPhone', methods=['GET', 'POST'])
def exportByPhone():
    course_query = Course.query.filter(Course.order_status.in_([0, 4])).order_by(Course.mobile_phone)
    out = io.BytesIO()
    writer = ExcelWriter(out, engine='openpyxl')
    df = pd.read_sql(course_query.statement, course_query.session.bind)
    df.to_excel(writer, index=False)
    # 这一步不能漏了,不save的话浏览器下载的xls文件里面啥也没有
    writer.save()
    # 重置一下IO对象的指针到开头
    out.seek(0)
    # IO对象使用getvalue()可以返回二进制的原始数据,用来给要生成的response的data
    resp = make_response(out.getvalue())
    # 设置response的header,让浏览器解析为文件下载行为
    resp.headers['Content-Disposition'] = 'attachement; filename=course.xlsx'
    resp.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    return resp
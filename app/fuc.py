from app.model import *
from flask import current_app
import json
import os
import zipfile
import requests
import pandas as pd
from datetime import datetime, timedelta
from . import db


def noneToInt(num):
    if num is None:
        return 0
    return num


def noneToNull(num):
    if num is None:
        return ''
    return num


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


def extendedInfoDel(extended_info, key):
    json_dic = extendedInfoToDic(extended_info)
    if json_dic.get(key):
        json_dic.pop(key)
    return json.dumps(json_dic)


def safe_copy(out_dir, name, form):
    if not os.path.exists(os.path.join(out_dir, name)):
        form.file.data.save(os.path.join(out_dir, name))
    else:
        base, extension = os.path.splitext(name)
        i = 1
        while os.path.exists(os.path.join(out_dir, '{}_{}{}'.format(base, i, extension))):
            i += 1
        form.file.data.save(os.path.join(out_dir, '{}_{}{}'.format(base, i, extension)))


def make_zip(source_dir, output_filename):
    zip_file = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, dir_names, filenames in os.walk(source_dir):
        for filename in filenames:
            path_file = os.path.join(parent, filename)
            arc_name = path_file[pre_len:].strip(os.path.sep)  # 相对路径
            zip_file.write(path_file, arc_name)
    zip_file.close()


def courseInfoIDToStr(courseInfoID):
    return courseInfoID[0:2]+'~'+str(int(courseInfoID[0:2])+1)+courseInfoID[2:]


def courseManageShow(students, homeworks):
    courseManage = []
    for student in students:
        t = [
           student.id,
           student.real_name,
           student.class_name,
        ]
        for i in homeworks:
            t.append(student.getHomeWorkSubTime(i))
        courseManage.append(t)
    return courseManage


def homeWorkShow(course_names):
    course = CourseInfo.query.filter_by(course_names=course_names).all()
    if len(course) == 0:
        return []
    return course[0].getZY()


def getCurrentCourseInfos():
    current_term = current_app.config.get('CURRENT_TERM')
    return CourseInfo.query.filter_by(course_period=current_term).all()


def getSubmitHomeWork():
    course_infos = getCurrentCourseInfos()
    course_infos_dic = {}
    for course_info in course_infos:
        if len(course_info.getZYStr()) > 0:
            if course_infos_dic.get(course_info.course_name):
                course_infos_dic[course_info.course_name] = \
                    course_info.getZYArr().union(course_infos_dic[course_info.course_name])
            else:
                course_infos_dic[course_info.course_name] = \
                    course_info.getZYArr()
    return course_infos_dic


def getCourseNames():
    course_names = CourseNames.query.filter_by().all()
    return [i.course_name for i in course_names]


def addCourseName(course_name):
    course_names = CourseNames(
        course_name=course_name
    )
    db.session.add(course_names)


def addCourseNames(course_name):
    current_term = current_app.config.get('CURRENT_TERM')
    courses = CourseInfo.query.filter_by(course_period=current_term,course_name=course_name).all()
    if len(courses) > 0:
        course_id = int(max([i.course_names[-1] for i in courses]))+1
    else:
        course_id = 1
    course_info = CourseInfo(
        course_period=current_term,
        course_name=course_name,
        course_names=current_term+course_name.replace('计算机', '') + str(course_id)
    )
    db.session.add(course_info)


def get_filelist(dire, Filelist):
    newDir = dire
    if os.path.isfile(dire):
        Filelist.append(dire)
    elif os.path.isdir(dire):
        for s in os.listdir(dire):
            newDir = os.path.join(dire, s)
            get_filelist(newDir, Filelist)
    return Filelist


def add_institution_infos_fuc(institution_name, institution_url, job_category):
    institution_info = InstitutionInfo.query.filter_by(institution_name=institution_name).first()
    if institution_info is None:
        current_term = current_app.config.get('CURRENT_TERM')
        institution_info = InstitutionInfo(
            institution_period=current_term,
            institution_name=institution_name,
        )
    institution_info.institution_url = institution_url
    institution_info.job_category = job_category
    db.session.add(institution_info)
    db.session.commit()


def spider_institution_jobs_fuc(institution_info):
    print(datetime.now(), '进行了爬虫')
    df = pd.read_html(get_content(institution_info.institution_url), header=0)[0]
    for i in df.itertuples():
        job_id = i.职位名称[i.职位名称.index('[')+1:i.职位名称.index(']')]
        institution_job_info = InstitutionJobInfo.query.\
            filter_by(institution_id=institution_info.institution_id,
                      job_id=job_id).first()
        if institution_job_info is None:
            institution_job_info = InstitutionJobInfo(
                institution_id=institution_info.institution_id,
                department_name=i.部门名称,
                job_name=i.职位名称[0:i.职位名称.index('[')],
                job_id=job_id
            )
        institution_job_info.confirmed = i._3
        institution_job_info.un_confirmed = i._4
        institution_job_info.succeeded = i._5
        institution_job_info.cal_total()
        db.session.add(institution_job_info)
        db.session.commit()


def get_content(url):
    response = requests.post(
        url=url,
        headers={
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.163 Mobile/15E148 Safari/604.1',
            "Sec-Fetch-Dest": "script",
            "Accept": "*/*",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "no-cors",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip",
        },
        verify=False)
    response.encoding = 'utf-8'
    return response.text

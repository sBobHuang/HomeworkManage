#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import render_template
from flask_login import login_required

from . import main
from .api import updateSchool
from .forms import UploadForm
from ..fuc import calSummary, getCurrentCourseInfos, getQueryCourseInfos, courseInfoIDToStr, getAllCourseInfos, \
    getStudentSchoolSet, getSchoolLocationSet, extendedInfoToArray, getStudentCourseStr
from ..models import CourseInfo, Student


@main.route('/')
def index():
    form = UploadForm()
    return render_template('index.html',
                           form=form)


@main.route('/preTerm')
@login_required
def preTerm():
    courseInfos = getAllCourseInfos()
    courseInfoIDSet = set([str(i.id)[0:3] for i in courseInfos])
    courseInfoIDYEARSet = set([i[0:2] for i in courseInfoIDSet])
    pre_term = []
    courseInfoIDStrSet = {}
    for courseInfoID in courseInfoIDSet:
        courseInfoIDStrSet[courseInfoID] = courseInfoIDToStr(courseInfoID)
    for i in courseInfoIDYEARSet:
        pre_term.append([year for year in courseInfoIDSet if year[0:2] == i])
    return render_template('pre_term.html',
                           pre_term=pre_term,
                           courseInfoIDStrSet=courseInfoIDStrSet
                           )


@main.route('/schoolManagement')
@login_required
def schoolManagement():
    updateSchool()
    studentSchoolSet = getStudentSchoolSet()
    # school_locationSet = dict([(school_mappingsSet[i].location, 0) for i in school_mappingsSet])
    # for i in school_mappingsSet:
    #   school_locationSet[school_mappingsSet[i].location] = school_locationSet[school_mappingsSet[i].location] + 1
    # print(school_locationSet)
    # from collections import Counter
    # school_locationSet = Counter([school_mappingsSet[i].location for i in school_mappingsSet])
    # for school_location in school_locationSet:
    #     print()
    # fp = open("test.txt", "w")
    # fp.write("\n".join(schoolSet))
    school_locationSet = getSchoolLocationSet()
    for school_location in school_locationSet:
        school_list = extendedInfoToArray(school_locationSet[school_location])
        school_locationSet[school_location] = sorted(school_list,
                                                     key=lambda kv: (studentSchoolSet[kv][0]),
                                                     reverse=True
                                                     )
    school_locations_numSet = dict([(i, 0) for i in school_locationSet])
    for i in school_locations_numSet:
        school_locations_numSet[i] = sum([studentSchoolSet[j][0] for j in school_locationSet[i]])
    school_locations = sorted(school_locationSet.items(),
                              key=lambda kv: (sum([studentSchoolSet[i][0] for i in kv[1]])),
                              reverse=True)
    return render_template('school.html',
                           school_locations=school_locations,
                           studentSchoolSet=studentSchoolSet,
                           school_locations_numSet=school_locations_numSet
                           )

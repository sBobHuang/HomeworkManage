#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, ValidationError

from ..models import Role, User


class UploadForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired()])
    studentID = StringField('学号', validators=[DataRequired()])
    photo = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('提交')


class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('所在地', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(0, 64), Email()])
    username = StringField('用户名', validators=[DataRequired(), Length(0, 64)])
    confirmed = BooleanField('确认')
    role = SelectField('角色', coerce=int)
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('所在地', validators=[Length(0, 64)])
    about_me = TextAreaField('关于我')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(emial=field.data).first():
            raise ValidationError('邮箱已注册！')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已注册！')


class CommentForm(FlaskForm):
    body = PageDownField(u'欢迎吐槽！', validators=[DataRequired()])
    submit = SubmitField('Submit')


'''
class RenderForm(FlaskForm):
    class Meta(FlaskForm.Meta):
        """
        重写render_field，实现Flask-Bootstrap与render_kw的class并存
        """
        def render_field(self, field, render_kw):
            other_kw = getattr(field, 'render_kw', None)
            if other_kw is not None:
                class1 = other_kw.get('class', None)
                class2 = render_kw.get('class', None)
                if class1 and class2:
                    render_kw['class'] = class2 + ' ' + class1
                render_kw = dict(other_kw, **render_kw)
            return field.widget(field, **render_kw)
'''


class EnrollmentSelectForm(FlaskForm):
    location = SelectField(
        label='地点',
        choices=[(0, '临海'), (1, '椒江')
                 ],
        default=1,
        coerce=int,
        render_kw={
            'onchange': 'change();'
        }
    )
    category = SelectField(
        label='类别',
        choices=[(1, '信息学奥赛培训'), (2, '高中信息技术Python程序设计培训')
                 ],
        coerce=int,
        render_kw={
            'onchange': 'change();'
        }
    )
    course_name = SelectField(
        label='班级',
        choices=[(0, '基础班1(7.9~7.18 上午8:30～11:30)'),
                 (1, '基础班2(7.26~8.4 晚上6:00～9:00)'),
                 (2, '提高班1(7.26~8.4 上午8:30～11:30)'),
                 (3, '提高班2(8.13~8.22 上午8:30～11:30)'),
                 (4, '竞赛班(8.13~8.22 晚上6:00～9:00)')
                 ],
        coerce=int
    )
    student_name = StringField('学生姓名', validators=[DataRequired(), Length(1, 64)])
    gender = SelectField(
        label='性别',
        choices=[(0, '男'), (1, '女')
                 ],
        coerce=int
    )
    school = StringField('所在学校', validators=[DataRequired(), Length(1, 64)])
    grade = SelectField(
        label='年级',
        choices=[(4, '四年级'), (5, '五年级'), (6, '六年级'),
                 (7, '初一'), (8, '初二'), (9, '初三'),
                 (10, '高一'), (11, '高二'), (12, '高三')
                 ],
        default=6,
        coerce=int
    )
    mobile_phone = StringField('家长手机号', validators=[DataRequired(), Length(11, 11, message='您输入的手机号不合法')])
    submit = SubmitField('提交')


class AuditionForm(FlaskForm):
    location = SelectField(
        label='地点',
        choices=[(0, '临海'), (1, '椒江')
                 ],
        default=1,
        coerce=int,
        render_kw={
            'onchange': 'change();'
        }
    )
    course_name = SelectField(
        label='信奥基础班公益课',
        choices=[(0, '时段1(7.8 上午8:30～10:00)'),
                 (1, '时段2(7.8 下午1:30～3:00)')
                 ],
        coerce=int
    )
    student_name = StringField('学生姓名', validators=[DataRequired(), Length(1, 64)])
    gender = SelectField(
        label='性别',
        choices=[(0, '男'), (1, '女')
                 ],
        coerce=int
    )
    school = StringField('所在学校', validators=[DataRequired(), Length(1, 64)])
    grade = SelectField(
        label='年级',
        choices=[(4, '四年级'), (5, '五年级'), (6, '六年级'),
                 (7, '初一'), (8, '初二'), (9, '初三'),
                 (10, '高一'), (11, '高二'), (12, '高三')
                 ],
        default=6,
        coerce=int
    )
    mobile_phone = StringField('家长手机号', validators=[DataRequired(), Length(11, 11, message='您输入的手机号不合法')])
    submit = SubmitField('提交')
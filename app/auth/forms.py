from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, FileField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo

from ..models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class AddCourseForm(FlaskForm):
    form_title = '添加科目'
    form_body = ''
    course_name = StringField('名称', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('添加')


class AddCoursesForm(FlaskForm):
    form_title = '添加班级'
    course = SelectField(
        label='科目',
        choices=[],
        coerce=str
    )
    submit = SubmitField('添加')


class UploadCoursesStus(FlaskForm):
    form_title = '导入班级名单'
    form_body = '上传需为Excel表格，第一列为学号，第二列为姓名，第三列为行政班，无表头'
    file = FileField('上传文件', validators=[FileRequired(), FileAllowed(['xlsx', 'xls'])])
    submit = SubmitField('提交')

from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
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

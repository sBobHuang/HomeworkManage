from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, FileField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo


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


class UploadForm(FlaskForm):
    course = SelectField(
        label='科目',
        choices=[('计算机导论', '计算机导论')
                 ],
        coerce=str
    )
    file = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('提交')


class AccountForm(FlaskForm):
    form_title = '新增账务'
    account_name = StringField('账务名称', validators=[DataRequired()])
    account_fee = IntegerField('金额', validators=[DataRequired()])
    pay_type = SelectField(
        label='支付方式',
        choices=[('招商卡', '招商卡'),
                 ('微信', '微信')
                 ],
        coerce=str
    )
    income = BooleanField('收入(默认支出)')
    account_submit = SubmitField('提交')


class DelAccountForm(FlaskForm):
    account_id = IntegerField('删除账务ID', validators=[DataRequired()])
    account_submit = SubmitField('提交')


class AddInstitutionForm(FlaskForm):
    form_title = '添加招聘监控'
    institution_name = StringField('招聘名称', validators=[DataRequired()])
    institution_url = StringField('爬虫地址', validators=[DataRequired()])
    job_category = StringField('报考类别', validators=[DataRequired()])
    institution_submit = SubmitField('提交')


class CalculatorForm(FlaskForm):
    form_title = '计算器'
    calculator_string = StringField('算式', validators=[DataRequired()])
    calculator_submit = SubmitField('提交查看结果')

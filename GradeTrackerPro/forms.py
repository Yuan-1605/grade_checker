from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FileField, HiddenField, DateField, FloatField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('帳號', validators=[DataRequired()])
    password = PasswordField('密碼', validators=[DataRequired()])
    submit = SubmitField('登入')

class UserForm(FlaskForm):
    user_id = HiddenField('使用者ID')
    username = StringField('帳號', validators=[DataRequired()])
    email = StringField('電子郵件', validators=[DataRequired(), Email()])
    password = PasswordField('密碼', validators=[Optional()])
    role = SelectField('角色', choices=[('student', '學生'), ('teacher', '教師'), ('admin', '管理員')], validators=[DataRequired()])
    submit = SubmitField('儲存使用者')

class ClassForm(FlaskForm):
    class_id = HiddenField('班級ID')
    name = StringField('班級名稱', validators=[DataRequired()])
    teacher_id = SelectField('教師', coerce=int, validators=[DataRequired()])
    submit = SubmitField('儲存班級')

class GradeItemForm(FlaskForm):
    grade_item_id = HiddenField('成績項目ID')
    name = StringField('項目名稱', validators=[DataRequired()])
    class_id = SelectField('班級', coerce=int, validators=[DataRequired()])
    max_score = FloatField('最高分數', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('儲存成績項目')

class AccessCodeForm(FlaskForm):
    access_code_id = HiddenField('訪問碼ID')
    code = StringField('訪問碼', validators=[DataRequired()])
    role = SelectField('角色', choices=[('student', '學生'), ('teacher', '教師'), ('admin', '管理員')], validators=[DataRequired()])
    expiry_date = DateField('到期日期', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('儲存訪問碼')

class ExcelImportForm(FlaskForm):
    class_id = SelectField('班級', coerce=int, validators=[DataRequired()])
    file = FileField('Excel檔案', validators=[DataRequired()])
    submit = SubmitField('匯入成績')

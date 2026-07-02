from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, BooleanField, HiddenField, SelectField, DecimalField, 
                     IntegerField, TextAreaField, DateField,  SubmitField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp
from utils.validators import (EmailNotRegistered, EmailExists, CorrectCurrentPassword, UniqueCategoryName, 
                              FutureDateOnly, EndDateAfterStart, MaxFileSize)


# STRONG_PASSWORD_REGEXP= Regexp( r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).{8,}$',
#             message="Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 symbol.")


CURRENCY_CHOICES=[
    ('INR','INR - Indian Rupee'),
    ('USD','USD - US Dollar'),
    ('EUR','EUR - Euro'),
    ('GBP','GBP - British Pound'),
    ('JPY', 'JPY - Japanese Yen'),
    ('AUD', 'AUD - Australian Dollar'),
    ('CAD', 'CAD - Canadian Dollar'),
    ('SGD', 'SGD - Singapore Dollar'),
    ('AED', 'AED - UAE Dirham'),
]

MONTH_CHOICES=[(i, str(i)) for i in range(1, 13)]

PAYMENT_METHOD_CHOICES = [
    ('Cash', 'Cash'),
    ('Card', 'Card'),
    ('UPI', 'UPI'),
    ('Bank Transfer', 'Bank Transfer'),
    ('Other', 'Other'),
]
 
BANK_CHOICES = [
    ('', 'Select Bank'),
    ('hdfc', 'HDFC Bank'),
    ('sbi', 'State Bank of India'),
    ('icici', 'ICICI Bank'),
    ('axis', 'Axis Bank'),
    ('kotak', 'Kotak Bank'),
    ('other', 'Other'),
]

ICON_CHOICES = [
    ('', 'No Icon'),
    ('fa-utensils', 'Food'),
    ('fa-car', 'Transport'),
    ('fa-home', 'Home'),
    ('fa-shopping-cart', 'Shopping'),
    ('fa-heartbeat', 'Health'),
    ('fa-graduation-cap', 'Education'),
    ('fa-film', 'Entertainment'),
    ('fa-briefcase', 'Work'),
    ('fa-plane', 'Travel'),
    ('fa-gift', 'Gift'),
] 

# -------- Authentication Forms ----------

class RegisterForm(FlaskForm):
    
    first_name=StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name=StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email=StringField('Email', validators=[DataRequired(), Email(), EmailNotRegistered()])
    password=PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password=PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Password must match.')])
    submit=SubmitField('Register')
    
class LoginForm(FlaskForm):
    
    email=StringField('Email', validators=[DataRequired(), Email()])
    password=PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    remember_me=BooleanField('Remember Me')
    submit=SubmitField('Login')

class VerifyOTPForm(FlaskForm):
    otp = StringField("Enter OTP", validators=[DataRequired(), Length(min=6 , max=6),Regexp(r'^\d{6}$', message='OTP must be only digits.')])
    submit= SubmitField('Verify OTP')
    
class ResendOTPForm(FlaskForm):
    email = HiddenField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend OTP')
    
class ForgotPasswordForm(FlaskForm):
    email=StringField('Email', validators=[DataRequired(), Email(), EmailExists()])
    submit=SubmitField('Verify by otp')

class ResetPasswordForm(FlaskForm):
    new_password=PasswordField('New Password', validators=[DataRequired(),Length(min=6)])
    confirm_password=PasswordField('Confirm New Password', validators=[DataRequired(),EqualTo('new_password',message='Password must match')])
    submit=SubmitField('Reset Password')

class ChangePasswordForm(FlaskForm):
    current_password=PasswordField('Old Password', validators=[DataRequired(), CorrectCurrentPassword()])
    new_password=PasswordField('New Password', validators=[DataRequired(),Length(min=6)])
    confirm_password=PasswordField('Confirm New Password', validators=[DataRequired(),EqualTo('new_password',message='Password must match')])
    submit=SubmitField('Change Password')

class ProfileForm(FlaskForm):
    
    first_name=StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name=StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    profile_picture=FileField('Profile Picture', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png'],'image only.')])
    preferred_currency=SelectField('Preferred Currency', validators=[DataRequired()], choices=CURRENCY_CHOICES)
    monthly_income=DecimalField('Monthly Income', validators=[Optional(), NumberRange(min=0)])
    occupation=StringField('Occupation', validators=[Optional(),Length(max=100)])
    submit=SubmitField('Save Profile')
    

# -------------- Transaction & Upload Forms ----------------


class UploadStatementForm(FlaskForm):
    
    statement_file=FileField('Statement File', validators=[DataRequired(), FileAllowed(['csv','xlsx','xls']), MaxFileSize(max_size=5)])
    bank_name=SelectField('Bank Name', validators=[Optional()], choices=BANK_CHOICES)
    submit = SubmitField('Upload')
    
class TransactionForm(FlaskForm):
    date=DateField('Date', validators=[DataRequired()])
    description=StringField('Description' ,validators=[DataRequired(), Length(max=255)])
    amount=DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    type=SelectField('Type', validators=[DataRequired()], choices = [('income', 'Income'), ('expense', 'Expense')])
    category_id=SelectField('Category Id', validators=[DataRequired()], coerce=int)  # Choices populated dynamically in the route
    currency=SelectField('Currency', validators=[DataRequired()], choices =CURRENCY_CHOICES)
    notes=TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    payment_method=SelectField('Payment Method', validators=[Optional()], choices=PAYMENT_METHOD_CHOICES)
    merchant=StringField('Merchant', validators=[Optional(), Length(max=100)])
    submit=	SubmitField('Save Transaction')
    
# -------------- Category Forms -----------------

class CategoryForm(FlaskForm):
    name=StringField('Name', validators=[DataRequired(),Length(min=2, max=50), UniqueCategoryName()])
    type=SelectField('Type', validators=[DataRequired()], choices = [('income', 'Income'), ('expense', 'Expense')])
    icon=SelectField('Icon', validators=[Optional()], choices=ICON_CHOICES)
    color=StringField('Color', validators=[Optional(),  Regexp(r'^(#[0-9A-Fa-f]{6})?$', message='Enter a valid hex color code (e.g. #FF5733).')])
    submit = SubmitField('Save Category')
    

# ------------- Budget Forms -----------------

class BudgetForm(FlaskForm):
    
    category_id=SelectField('Category Id', validators=[DataRequired()], coerce=int)  # Choices populated dynamically in the route
    amount=DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    month=SelectField('Month', validators=[DataRequired()], coerce=int, choices=MONTH_CHOICES)
    year=IntegerField('Year', validators=[DataRequired(), NumberRange(min=2025, max=2100)])
    submit = SubmitField('Save Budget')
    
# -------------- Saving Goal Forms ----------------

class GoalForm(FlaskForm):
    goal_name = StringField('Goal Name', validators=[DataRequired(), Length(min=2, max=100)])
    target_amount = DecimalField('Target Amount', validators=[DataRequired(), NumberRange(min=1, message='Target must be at least 1.')], places=2)
    current_saved = DecimalField('Current Saved', validators=[Optional(), NumberRange(min=0)], places=2)
    deadline = DateField('Deadline', validators=[Optional(), FutureDateOnly()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    status = SelectField('Status', choices=[('active', 'Active'),('completed', 'Completed'),('abandoned', 'Abandoned'),])
    submit = SubmitField('Save Goal')
    
# ---------------  Report Forms ----------------

class ReportGenerationForm(FlaskForm):
    report_type = SelectField('Report Type', validators=[DataRequired()], choices=[('monthly', 'Monthly'),('yearly', 'Yearly'),('category', 'By Category'),('budget', 'Budget'),('saving', 'Saving Goals'),])
    format = SelectField('Export Format', validators=[DataRequired()], choices=[('pdf', 'PDF'),('excel', 'Excel'),('csv', 'CSV'),])
    period_start = DateField('Period Start', validators=[DataRequired()])
    period_end = DateField('Period End', validators=[DataRequired(), EndDateAfterStart()])
    category_id = SelectField('Category', validators=[Optional()], coerce=int)  # Relevant only when report_type='category'; populated in route
    submit = SubmitField('Generate Report')
    
# --------------- Currency Form -----------------

class CurrencyPreferenceForm(FlaskForm):
    base_currency = SelectField('Base Currency', validators=[DataRequired()], choices=CURRENCY_CHOICES)
    submit = SubmitField('Save Currency')
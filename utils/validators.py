from flask_login import current_user
from datetime import date
from werkzeug.security import check_password_hash
from wtforms.validators import ValidationError
from models import User, Category

class EmailNotRegistered():
    def __init__(self, message=None):
        self.message= message or "An account with this emial already extists."
        
    def __call__(self, form, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(self.message)
        
class EmailExists():
    def __init__(self, message=None):
        self.message = message or "No account found with this email address."
        
    def __call__(self, form, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError(self.message)
        
class CorrectCurrentPassword():
    def __init__(self, message=None):
        self.message = message or "Current password is incorrect."
    
    def __call__(self, form, field):
        if not check_password_hash(current_user.password, field.data):
            raise ValidationError(self.message)
        
class UniqueCategoryName:
    def __init__(self, message=None):
        self.message = message or "You already have a category with this name."
 
    def __call__(self, form, field):
        existing=Category.query.filter_by(user_id=current_user.id,name=field.data).first()
        
        if existing:
            raise ValidationError(self.message)
        
class FutureDateOnly:
    def __init__(self, message=None):
        self.message = message or "Deadline must be a future date."
 
    def __call__(self, form, field):
        if field.data and field.data <=date.today():
            raise ValidationError(self.message)
        
class EndDateAfterStart:
    def __init__(self, message=None):
        self.message = message or "End date must be after the start date."
 
    def __call__(self, form, field):
        start=form.period_start.data
        if start and field.data and field.data < start:
            raise ValidationError(self.message)
        
class MaxFileSize:
    def __init__(self, max_size=5, message=None):
        self.max_size = max_size
        self.message = message or f"File size must not exceed {max_size} MB."
        
    def __call__(self, form, field):
        if field.data:
            field.data.seek(0, 2)
            file_size_mb= field.data.tell() / (1024 * 1024)
            field.data.seek(0)
            
            if file_size_mb > self.max_size:
                raise ValidationError(self.message)
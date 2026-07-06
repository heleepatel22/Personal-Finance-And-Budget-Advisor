from functools import wraps
from flask import redirect, url_for, session, flash
from flask_login import current_user

def verified_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not current_user.is_verified:
            session['otp_email']=current_user.email
            session['otp_purpose']='email_verification'
            flash("Please verify your email address to continue.", "warning")
            return redirect(url_for("auth.verify_otp"))
        return f(*args, **kwargs)
 
    return decorated_function
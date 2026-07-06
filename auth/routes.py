from flask import flash, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_required, login_user, logout_user

from auth import auth_bp
from extensions import db
from models import User
from forms import(RegisterForm,
                  LoginForm,
                  VerifyOTPForm,
                  ResendOTPForm,
                  ForgotPasswordForm,
                  ResetPasswordForm,
                  ChangePasswordForm)
from auth.email import (send_verification_email, 
                        send_password_reset_email, 
                        send_password_changed_email)
from auth.helpers import (resend_cooldown,
                          log_activity,
                          is_account_locked,
                          handle_failed_login,
                          reset_failed_attempts)
from auth.otp import create_otp, get_latest_otp, verify_otp as check_otp



@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect (url_for("dashboard.index"))
    
    form= RegisterForm()
    
    if form.validate_on_submit():
        user=User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.strip().lower(),
            password=generate_password_hash(form.password.data),
            is_verified=False,
        )
        
        db.session.add(user)
        db.session.flush()
        
        otp=create_otp(user.id, 'email_verification')
        db.session.commit()
        
        send_verification_email(user, otp.code)
        log_activity(user.id,'register')
        db.session.commit()
        
        session['otp_email']=user.email
        session['otp_purpose']='email_verification'
        
        flash("Account created! Please check your email for the verification code.", "success")
        return redirect (url_for('auth.verify_otp'))
    
    return render_template('auth/register.html', form=form)




@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect (url_for("dashboard.index"))
    
    form=LoginForm()
    
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data.strip().lower()).first()
        
        if not user:
            flash("Email not found. Please register first.", "danger")
            return redirect(url_for("auth.register"))
        
        if is_account_locked(user):
            flash("Your account is temporarily locked due to too many failed attempts. Try again later.", "danger")
            return render_template("auth/login.html", form=form)
        
        if not check_password_hash(user.password, form.password.data):
            handle_failed_login(user)
            flash("Wrong password. Please try again.", "danger")
            return render_template("auth/login.html", form=form)
        
        
        if not user.is_verified:
            session['otp_email']=user.email
            session['otp_purpose']='email_verification'
            otp=create_otp(user.id, 'email_verification')
            db.session.commit()
            send_verification_email(user, otp.code)
            flash("Your email is not verified. A new code has been sent.", "warning")
            return redirect(url_for("auth.verify_otp"))
        
        reset_failed_attempts(user)
        login_user(user, remember=form.remember_me.data)
        log_activity(user.id, 'login')
        db.session.commit()
    
        flash(f"Welcome back, {user.first_name}!", "success")
        return redirect(url_for("dashboard.index")) 
    
    return render_template('auth/login.html', form=form)




@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email=session.get('otp_email')
    purpose=session.get('otp_purpose','email_verification')
    
    if not email:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("auth.login"))
    
    user=User.query.filter_by(email=email).first()
    if not user:
        flash("User not found. Please register first.", "danger")
        return redirect(url_for("auth.register"))
    
    form=VerifyOTPForm()
    resend_form=ResendOTPForm()
    
    if form.validate_on_submit():
        success, message= check_otp(user.id, purpose, form.otp.data)
        
        if success:
            if purpose=='email_verification':
                user.is_verified=True
                db.session.commit()
                log_activity(user.id, "email_verified")
                db.session.commit()
                login_user(user)
                session.pop('otp_email', None)
                session.pop('otp_purpose', None)
                flash("Email verified! Welcome to Personal Finance Advisor.", "success")
                return redirect(url_for("dashboard.index"))
            
            elif purpose=='password_reset':
                session['reset_verified']=True
                session.pop('otp_purpose', None)
                flash("OTP verified. Please set your new password.", "success")
                return redirect(url_for("auth.reset_password"))
            
        else:
            flash(message, "danger")
            
    latest_otp=get_latest_otp(user.id, purpose)
    cooldown = resend_cooldown(latest_otp)
    
    return render_template('auth/verify_otp.html', form=form, resend_form=resend_form, purpose=purpose, cooldown=cooldown,)




@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    form=ResendOTPForm()
    
    if form.validate_on_submit():
        email=form.email.data.strip().lower()
        purpose=session.get('otp_purpose', 'email_verification')
        
        user=User.query.filter_by(email=email).first()
        
        if not user:
            flash("User not found. Please register first.", "danger")
            return redirect(url_for("auth.register"))
        
        latest_otp=get_latest_otp(user.id, purpose)
        cooldown=resend_cooldown(latest_otp)
        
        if cooldown >0:
            flash(f"Please wait {cooldown} seconds before requesting a new code.", "warning")
        else:
            otp=create_otp(user.id, purpose)
            db.session.commit()
            
            if purpose=='email_verification':
                send_verification_email(user, otp.code)
            elif purpose=='password_reset':
                send_password_reset_email(user, otp.code)
                
            flash("A new OTP has been sent to your email.", "success")
 
    return redirect(url_for("auth.verify_otp"))




@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email=form.email.data.strip().lower()
        user=User.query.filter_by(email=email).first()
        
        if user:
            otp=create_otp(user.id, 'password_reset')
            db.session.commit()
            
            send_password_reset_email(user, otp.code)
            
            session['otp_email']=user.email
            session['otp_purpose']='password_reset'
            session.pop('reset_verified', None)
            
            flash("A password reset code has been sent to your email.", "success")
            return redirect(url_for("auth.verify_otp"))
 
    return render_template("auth/forgot_password.html", form=form)




@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("otp_email")
    reset_verified = session.get("reset_verified", False)
    
    if not email or not reset_verified:
        flash("Please complete OTP verification first.", "warning")
        return redirect(url_for("auth.forgot_password"))
    
    user=User.query.filter_by(email=email).first()
    
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))
    
    form=ResetPasswordForm()
    if form.validate_on_submit():
        user.password=generate_password_hash(form.new_password.data)
        db.session.commit()
        
        log_activity(user.id, 'password_reset')
        db.session.commit()
        
        send_password_changed_email(user)
        
        session.pop('otp_email', None)
        session.pop('reset_verified', None)
        
        flash("Password reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))
 
    return render_template("auth/reset_password.html", form=form)




@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form=ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password=generate_password_hash(form.new_password.data)
        db.session.commit()
        
        log_activity(current_user.id, 'password_change')
        db.session.commit()
        
        send_password_changed_email(current_user)
        
        flash("Password changed successfully.", "success")
        return redirect(url_for("dashboard.index"))
 
    return render_template("auth/change_password.html", form=form)
        


       
@auth_bp.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout')
    db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
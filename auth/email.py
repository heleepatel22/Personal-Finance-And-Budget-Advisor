from flask import render_template, current_app
from  flask_mail import Message
from extensions import mail

def _send(subject, recipients, html_body, text_body=None):
    
    msg=Message(
        subject=subject,
        recipients=recipients if isinstance(recipients, list) else [recipients],
        html=html_body,
        body=text_body or "",
    )
    try:
        mail.send(msg)
    except  Exception as e:
        current_app.logger.error(f'Failed to send email to {recipients}: {e}')
        

def send_verification_email(user, otp_code):
    
    _send(
        subject="Verify your email — Personal Finance Advisor",
        recipients=user.email,
        html_body=render_template('emails/otp_email.html',
                                  user=user,
                                  otp_code=otp_code,
                                  purpose='email_verification'),
        text_body=(
            f'Hi {user.first_name} {user.last_name},\n\n'
            f'Your verification code is: {otp_code}\n'
            f"It expires in 5 minutes.\n\n"
            f"If you did not register, please ignore this email."
            ),
    )
    
def send_welcome_email(user):
     _send(
        subject="Welcome to Personal Finance Advisor!",
        recipients=user.email,
        html_body=render_template("emails/welcome.html",user=user,),
        text_body=(
            f"Hi {user.first_name} {user.last_name} \n\n"
            f"Welcome to Personal Finance Advisor!\n"
            f"Your account is now verified and ready to use.\n\n"
            f"Start by adding your first transaction or uploading a bank statement."
        ),
    )
     
def send_password_reset_email(user, otp_code):
    """Send the password-reset OTP."""
    _send(
        subject="Password reset code — Personal Finance Advisor",
        recipients=user.email,
        html_body=render_template("emails/forgot_password.html",user=user,otp_code=otp_code,),
        text_body=(
            f"Hi {user.first_name} {user.last_name}\n\n"
            f"Your password reset code is: {otp_code}\n"
            f"It expires in 5 minutes.\n\n"
            f"If you did not request a password reset, please ignore this email."
        ),
    )
 
 
def send_password_changed_email(user):
    """Send a security confirmation after a password change."""
    _send(
        subject="Your password has been changed — Personal Finance Advisor",
        recipients=user.email,
        html_body=render_template("emails/password_changed.html",user=user,),
        text_body=(
            f"Hi {user.first_name} {user.last_name}\n\n"
            f"Your password was successfully changed.\n\n"
            f"If you did not make this change, please contact support immediately."
        ),
    )
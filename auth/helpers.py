from flask import request
from datetime import datetime, timedelta
from extensions import db
from models import ActivityLog

RESEND_COOLDOWN_SECONDS = 30

MAX_FAILD_ATTEMPTS = 3

LOCK_DURATION_MINUTES = 5


def resend_cooldown(otp_record):
    
    if otp_record is None:
        return 0
    
    
    seconds_till_now=(datetime.utcnow() - otp_record.created_at).total_seconds()
    remaining= RESEND_COOLDOWN_SECONDS - seconds_till_now
    
    return max(0, int(remaining))

def log_activity(user_id, action , details=None):
    
    log=ActivityLog(
        user_id=user_id,
        action=action,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:255] if request.user_agent else None,
        details=details,
    )
    
    db.session.add(log)
    
def is_account_locked(user):
    
    if user.locked_until is None:
        return False
    
    if datetime.utcnow() < user.locked_until:
        return True
    
    user.locked_until=None
    user.failed_login_attempts=0
    return False

def  handle_failed_login(user):
    
    user.failed_login_attempts=(user.failed_login_attempts or 0) + 1
    
    if user.failed_login_attempts >= MAX_FAILD_ATTEMPTS:
        user.locked_until= datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
        
        
def reset_failed_attempts(user):
    
    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts= 0
        user.locked_until= None

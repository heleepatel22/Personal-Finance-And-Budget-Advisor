import random
import string
from datetime import datetime, timedelta
from extensions import db
from models import OTPCode

OTP_EXPIRY_MINUTES= 5
OTP_MAX_ATTEMPTS= 3

def generate_otp_code():
    
    return "".join(random.choices(string.digits, k=6))

def create_otp(user_id, purpose):
    
     # Invalidate previous unused OTPs for the same purpose
     OTPCode.query.filter_by(user_id=user_id, purpose=purpose, is_used=False).update({"is_used": True})
     
     code=generate_otp_code()
     otp=OTPCode(
         user_id=user_id,
         code=code,
         purpose=purpose,
         is_used=False,
         attempts=0,
         expires_at= datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
     )
     db.session.add(otp)
     return otp
 
def verify_otp(user_id, purpose, submitted_code):
    
    otp=(
        OTPCode.query.filter_by(user_id=user_id, purpose=purpose, is_used=False)
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    
    if not otp:
        return False,  "No active OTP found. Please request a new one."
    
    if datetime.utcnow() > otp.expires_at:
        otp.is_used = True
        db.session.commit()
        return False, "OTP has expired. Please request a new one."
    
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        otp.is_used = True
        db.session.commit()
        return False, "Too many incorrect attempts. Please request a new OTP."
    
    if otp.code != submitted_code.strip():
        otp.attempts += 1
        remaining = OTP_MAX_ATTEMPTS - otp.attempts
        if remaining <= 0:
            otp.is_used = True
            db.session.commit()
            return False, "Too many incorrect attempts. Please request a new OTP."
        db.session.commit()
        return False, f"Incorrect OTP. {remaining} attempt(s) remaining."


    otp.is_used=True
    db.session.commit()
    return True, "OTP verified successfully."

def get_latest_otp(user_id, purpose):
    
    return (
        OTPCode.query.filter_by(user_id=user_id, purpose=purpose)
        .order_by(OTPCode.created_at.desc())
        .first()
    )
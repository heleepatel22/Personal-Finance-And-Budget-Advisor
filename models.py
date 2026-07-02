from flask_login  import UserMixin
from datetime import datetime
from extensions import db

class User(db.Model, UserMixin):
    __tablename__="users"
    
    id=db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(50), nullable=False)
    last_name=db.Column(db.String(50), nullable=False)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.String(255), nullable=False)
    is_verified=db.Column(db.Boolean, default=False)
    profile_picture=db.Column(db.String(255))
    preferred_currency=db.Column(db.String(3), default="INR", nullable=False)
    monthly_income=db.Column(db.Numeric(12, 2))
    occupation=db.Column(db.String(100))
    remember_token=db.Column(db.String(255))
    failed_login_attempts=db.Column(db.Integer, default=0)
    locked_until=db.Column(db.DateTime)
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<User{self.id}: Email={self.email}>"
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
class OTPCode(db.Model):
    __tablename__='otp_codes'
    
    __table_args__=(db.Index('ix_otp_code_user_purpose_used', 'user_id', 'purpose', 'is_used'),)
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    code=db.Column(db.String(6), nullable=False)
    purpose=db.Column(db.String(30), nullable=False)  # email_verification | login | password_reset
    is_used=db.Column(db.Boolean, default=False, nullable=False)
    attempts=db.Column(	db.Integer,	default=0, nullable=False)
    expires_at=db.Column(db.DateTime, nullable=False)	
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='otp_codes', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<OTPCode id={self.id} user_id={self.user_id} purpose={self.purpose}>'
    
class Category(db.Model):
    
    __tablename__="categories"
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    name=db.Column(db.String(50), nullable=False)
    type=db.Column(db.String(30), nullable=False) #income | expense
    icon=db.Column(db.String(50), nullable=True)
    color=db.Column(db.String(7), nullable=True)  # Hex color code for charts
    is_default=db.Column(db.Boolean, default=False, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='categories', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'Category id={self.id}, name={self.name}, typr={self.type}'
    
class Transaction(db.Model):
    __tablename__='transactions'
    
    __table_args__=(db.Index('ix_transactions_user_date', 'user_id', 'date'),)
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey("categories.id", ondelete='SET NULL'), nullable=True)
    date=db.Column(db.Date, nullable=False)
    description=db.Column(db.String(255), nullable=False)
    amount=db.Column(db.Numeric(12, 2), nullable=False)
    type=db.Column(db.String(30), nullable=False) #income | expense
    currency=db.Column(db.String(3), default="INR", nullable=False)
    notes=db.Column(db.Text, nullable=True)
    payment_method=db.Column(db.String(30), nullable=True) # Cash, Card, UPI, Bank Transfer, etc.
    merchant=db.Column(db.String(100), nullable=True)	
    source=db.Column(db.String(20),	default='manual', nullable=False) #manual | csv_import | excel_import
    is_recurring=db.Column(db.Boolean, default=False, nullable=False)
    is_anomaly=db.Column(db.Boolean, default=False, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user=db.relationship('User', backref='transactions', cascade='all, delete-orphan')
    category=db.relationship('Category', backref='transactions') # No cascade: deleting a category must not delete transaction history.
    
    def __repr__(self):
        return f'<Transaction id ={self.id}, amouny={self.amount}, type={self.type}>'
    
class Budget(db.Model):
    __tablename__='budgets'
    __table_args__=(db.UniqueConstraint("user_id", "category_id", "month", "year", name="uq_budget_user_category_month_year"),
                    db.Index("ix_user_month_year", "user_id", "month", "year"),)
    
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    category_id=db.Column(db.Integer, db.ForeignKey("categories.id", ondelete='RESTRICT'), nullable=False)
    amount=db.Column(db.Numeric(12, 2), nullable=False)
    month=db.Column(db.Integer, nullable=False) #1-12
    year=db.Column(db.Integer, nullable=False)
    alert_threshold_80=db.Column(db.Boolean, default=False)	#Whether 80% alert has been sent
    alert_threshold_90=db.Column(db.Boolean, default=False)
    alert_threshold_100=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user=db.relationship("User", backref='budgets', cascade='all, delete-orphan')
    category=db.relationship('Category', backref='budgets') # RESTRICT on the FK means category cannot be deleted while budgets reference it.
    
    def __repr__(self):
        return f'<Budget id={self.id}, category_id={self.category_id}, {self.month}{self.year}>'

class SavingGoal(db.Model):
    __tablename__='saving_goals'
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    goal_name=db.Column(db.String(100), nullable=False)
    target_amount=db.Column(db.Numeric(12, 2), nullable=False)
    current_saved=db.Column(db.Numeric(12, 2), default=0.00, nullable=False)
    deadline=db.Column(db.Date, nullable=True)
    description=db.Column(db.Text, nullable=True)
    status=db.Column(db.String(20), default='active', nullable=False)  # active | completed | abandoned
    created_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user=db.relationship("User", backref='saving_goals', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<saving_goal id={self.id}, goal_name={self.goal_name}>'
    
class  Currency(db.Model):
    __tablename__ = "currencies"

    id=db.Column(db.Integer, primary_key=True)
    code=db.Column(db.String(3), unique=True, nullable=False)  # ISO 4217: INR, USD, EUR, ...
    name=db.Column(db.String(50), nullable=False)
    symbol=db.Column(db.String(5), nullable=False)  # Display symbol (₹, $, €, etc.)
    exchange_rate_to_inr=db.Column(db.Numeric(12, 6), nullable=False)
    last_updated=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Currancy code={self.code}>'
    
class Report(db.Model):
    __tablename__='reports'
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    report_type=db.Column(db.String(20), nullable=False) # monthly | yearly | category | budget | saving
    format=db.Column(db.String(10), nullable=False) # pdf | excel | csv  
    period_start=db.Column(db.Date, nullable=False)
    period_end=db.Column(db.Date, nullable=False)
    file_path=db.Column(db.String(255), nullable=False)
    generated_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='reports', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Report id={self.id}, report typr={self.report_type}, report format={self.format}>'
    
class Notification(db.Model):
    __tablename__='notifications'
    __table_args__ = (db.Index("ix_notifications_user_read", "user_id", "is_read"),)
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    type=db.Column(db.String(30), nullable=False) # budget_alert | goal_completed | otp | email_verification | report_ready | password_changed
    title=db.Column(db.String(150), nullable=False)  
    message=db.Column(db.Text, nullable=False)
    is_read=db.Column(db.Boolean, default=False)
    related_id=db.Column(db.Integer, nullable=True)
    created_at=db.Column(db.DateTime,  default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='notifications', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Notification id={self.id} type={self.type!r} is_read={self.is_read}>'

class MLPrediction(db.Model):
    __tablename__='ml_predictions'
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    transaction_id=db.Column(db.Integer, db.ForeignKey("transactions.id", ondelete='SET NULL'), nullable=True)
    prediction_type=db.Column(db.String(30), nullable=False) # category | expense_forecast | anomaly_score | health_score
    predicted_value=db.Column(db.String(255), nullable=False)
    confidence=db.Column(db.Numeric(5, 4), nullable=True) # Model confidence score
    model_version=db.Column(db.String(20), nullable=True)
    created_at=db.Column(db.DateTime,  default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='ml_predictions', cascade='all, delete-orphan')
    transaction=db.relationship("Transaction", backref='ml_predictions')
    
    def __repr__(self):
        return f'<MLPrediction id={self.id} type={self.prediction_type!r}>'
    
class ActivityLog(db.Model):
    __tablename__='activity_logs'
    
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    action=db.Column(db.String(50), nullable=False) # login | logout | password_change | upload | export | budget_created, etc.
    ip_address=db.Column(db.String(45), nullable=True)
    user_agent=db.Column(db.String(255), nullable=True)
    details=db.Column(db.Text, nullable=True)
    created_at=db.Column(db.DateTime,  default=datetime.utcnow, nullable=False)
    
    user=db.relationship("User", backref='activity_logs', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'ActivityLog id={self.id} action={self.action}'
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    otp = db.Column(db.String(6), nullable=True)

    user_purchases = db.relationship('Purchase', backref='user', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    teacher_email = db.Column(db.String(255), db.ForeignKey('users.email'), nullable=False)
    teacher = db.relationship('User', backref=db.backref('courses', lazy=True))

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_email = db.Column(db.String(100), nullable=False)  # Remove ForeignKey constraint
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    # Define relationship with User model
    student = db.relationship('User', backref=db.backref('purchases', lazy=True))

    # Define relationship with Course model
    course = db.relationship('Course', backref=db.backref('purchases', lazy=True))

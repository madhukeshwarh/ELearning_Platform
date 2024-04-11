from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
import random
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
from model import User, Course, Purchase,db
from flask_sqlalchemy import SQLAlchemy
import warnings
from sqlalchemy.exc import SAWarning

warnings.filterwarnings('ignore', category=SAWarning)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# MySQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:madhu123@localhost/e-learn'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'madhu123'
app.config['MYSQL_DB'] = 'e-learn'
mysql = MySQL(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'bomnallimadhu@gmail.com'
app.config['MAIL_PASSWORD'] = 'qznv yoct colm fehx'
app.config['MAIL_DEFAULT_SENDER'] = 'hegdemadhukeshwar6@gmail.com'
mail = Mail(app)

# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Route for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            flash('An account already exists for this email. Please log in.')
            return redirect(url_for('login'))
        
        otp = generate_otp()
        cur.execute("INSERT INTO users (email, password, role, otp) VALUES (%s, %s, %s, %s)", (email, password, role, otp))
        mysql.connection.commit()
        cur.close()
        
        msg = Message('OTP for e-Learning Platform', recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)
        
        return redirect(url_for('verify'))
    
    return render_template('register.html')

# Route for OTP verification
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form['email']
        otp = request.form['otp']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s AND otp = %s", (email, otp))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['logged_in'] = True
            session['email'] = email
            return redirect(url_for('home'))
        else:
            return render_template('verify.html', message='Invalid OTP. Please try again.')
    
    return render_template('verify.html')

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if email and password match
        cur = mysql.connection.cursor(cursorclass=DictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['email'] = email
            role = user.get('role')
            if role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                flash('Role information is missing or invalid. Please contact the administrator.')
        else:
            flash('Invalid email or password. Please try again.')
    
    return render_template('login.html')
# Route for teacher dashboard
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'email' in session:
        # Retrieve the email from the session
        email = session['email']
        
        # Fetch courses associated with the logged-in teacher using SQLAlchemy
        teacher = User.query.filter_by(email=email).first()
        if teacher:
            courses = teacher.courses
            return render_template('teacher_dashboard.html', courses=courses)
        else:
            flash('Teacher not found.')
    else:
        # Redirect to login page if user is not logged in
        flash('Please log in to access the dashboard.')
    return redirect(url_for('login'))

# Route for student dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if 'email' in session:
        # Retrieve the email from the session
        email = session['email']
        
        # Fetch all courses and purchased courses associated with the logged-in student using SQLAlchemy
        student = User.query.filter_by(email=email).first()
        if student:
            courses = Course.query.all()
            purchased_courses = student.purchases
            return render_template('student_dashboard.html', courses=courses, purchased_courses=purchased_courses)
        else:
            flash('Student not found.')
    else:
        # Redirect to login page if user is not logged in
        flash('Please log in to access the dashboard.')
    return redirect(url_for('login'))

# Route for adding a course
@app.route('/add_course', methods=['POST'])
def add_course():
    if request.method == 'POST':
        course_name = request.form['course_name']
        duration = request.form['duration']
        price = request.form['price']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO courses (course_name, duration, price, teacher_email) VALUES (%s, %s, %s, %s)", (course_name, duration, price, session['email']))
        mysql.connection.commit()
        cur.close()
        
        return redirect(url_for('teacher_dashboard'))

# Route for deleting a course
@app.route('/delete_course', methods=['POST'])
def delete_course():
    if request.method == 'POST':
        course_name = request.form.get('course_name')
        cur = mysql.connection.cursor()  # Accessing cursor from the MySQL connection object
        cur.execute("DELETE FROM courses WHERE course_name = %s", (course_name,))
        mysql.connection.commit()
        cur.close()
        flash('Course deleted successfully.')
    
    return redirect(url_for('teacher_dashboard'))

# Route for buying a course
@app.route('/buy_course', methods=['POST'])
def buy_course():
    if request.method == 'POST':
        course_id = request.args.get('course_id')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        course = cur.fetchone()
        cur.execute("INSERT INTO purchases (user_id, course_id, student_email) VALUES (%s, %s, %s)", (session['id'], course_id, session['email']))
        mysql.connection.commit()
        cur.close()
        flash('Course purchased successfully.')
    
    return redirect(url_for('student_dashboard'))

# Route for payment
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'GET':
        course_id = request.args.get('course_id')
        course_name = request.args.get('course_name')
        duration = request.args.get('duration')
        price = request.args.get('price')
        course = Course.query.get(course_id)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
        course = cur.fetchone()
        cur.close()
        return render_template('payment.html', course_name=course_name, duration=duration, price=price)
    elif request.method == 'POST':
        course_id = request.form.get('course_id')  # Make sure to use correct field name
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO purchases (user_id, course_id, student_email) VALUES (%s, %s, %s)", (session.get('user_id'), course_id, session.get('email')))
        mysql.connection.commit()
        cur.close()
        flash('Payment successful.')
        return redirect(url_for('payment_success'))

# Payment success route
@app.route('/payment_success')
def payment_success():
    return render_template('payment_success.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('email', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

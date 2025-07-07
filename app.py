from flask import Flask, render_template,request,redirect,url_for,session, flash, Response, send_file
import sqlite3
from io import BytesIO
import os
import json
from collections import defaultdict
from datetime import datetime

import base64
#from PIL import Image, ImageDraw
#import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)

def database():
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                       user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       FullName TEXT NOT NULL,
                       Password TEXT NOT NULL,
                       Email TEXT NOT NULL
                       )''')
    cursor.execute( '''CREATE TABLE IF NOT EXISTS admin(
                       user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       Email TEXT NOT NULL UNIQUE,
                       Password TEXT NOT NULL UNIQUE)''')
    cursor.execute( '''CREATE TABLE IF NOT EXISTS info(
                       user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       Fullname TEXT NOT NULL,
                        Email TEXT NOT NULL,
                       Matric TEXT NOT NULL,
                       Department TEXT NOT NULL,
                       Level TEXT NOT NULL,
                       
                       FOREIGN KEY(user_id)
                       REFERENCES users(user_id) )''')
    cursor.execute( '''CREATE TABLE IF NOT EXISTS image (
                       uploaded_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       picture BLOB,
                       course_code TEXT NOT NULL DEFAULT 'general',
                       file_name TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                       FOREIGN KEY(user_id)
                       REFERENCES users(user_id) )''')
    conn.commit()
    conn.close()

database()  # Call the database initialization

def admin_signup():
    Email = 'admin334@gmail.com'
    Password = 'admin334'

    if not (Email and Password):
        flash('Error: All fields are required!')
    hashed_password = generate_password_hash(Password, method='pbkdf2:sha256')
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO admin(Email, Password) VALUES (?, ?)",
                        (Email, hashed_password))
        conn.commit()
        flash('Admin signed up', 'success')
        print('Admin Signed up')
    finally:
        conn.close()
@app.route('/as')
def a_s():
    admin_signup()
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Get the form data
        Email = request.form['Email']
        Password = request.form['Password']
        conn = sqlite3.connect('CBT1.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, Password FROM admin WHERE Email = ?", (Email,))
        user = cursor.fetchone()
        conn.close()

        # Verify the password
        if user and check_password_hash(user[1], Password ):
            # If password matches, set the session and redirect to dashboard
            session['user_id'] = user[0]  # Save user_id in session
            flash('Admin Login Successful', 'success')
            print('Admin Logged in')
            session['user'] = Email
            session['logged_in'] = True
            return redirect(url_for('Admin'))
        else:
            # If login fails, show an error (this is basic, you might want to flash a message)
            flash("Invalid email or password", 'error')
            print('Invalid Admin Email or Password')
    
    return render_template('admin_login.html') 
@app.route('/')
def Landing_Page():
    return render_template('land.html')



@app.route('/login', methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        # Get the form data
        Email = request.form['Email']
        print(f'Email: {Email} ')
        Password = request.form['Password']
        print(f'Password: {Password}')
        # Connect to the database
        conn = sqlite3.connect('CBT1.db')
        cursor = conn.cursor()

        # Check if the user exists in the database
        cursor.execute("SELECT user_id, Password FROM users WHERE Email = ?", (Email,))
        user = cursor.fetchone()

        conn.close()

        # Verify the password
        if user and check_password_hash(user[1], Password ):
            # If password matches, set the session and redirect to dashboard
            session['user_id'] = user[0]  # Save user_id in session
            flash('Login Successful', 'success')
            print('Login successful')
            session['user'] = Email
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            # If login fails, show an error (this is basic, you might want to flash a message)
            flash("Invalid email or password", 'error')
            print('Invalid email or password')

    return render_template('login.html')  # Show the login page for GET requests

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('Logged out', 'success')
    print('Logged out')
    return redirect(url_for('Login'))
    return render_template('logout.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        FullName = request.form.get('FullName')
        print(f'A new user registered: {FullName}')
        Email = request.form.get('Email')
        print(f'Email: {Email} ')
        Password = request.form['Password']
        print(f'Password: {Password}')

        if not (FullName and Email and Password):
            return 'Error: All fields are required!'

        # Hash the password for security
        hashed_password = generate_password_hash(Password, method='pbkdf2:sha256')

        conn = sqlite3.connect('CBT1.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users(FullName, Email, Password) VALUES (?, ?, ?)",
                           (FullName, Email, hashed_password))
            conn.commit()
            return redirect(url_for('Login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
            print('Email Already exists')
        finally:
            conn.close()

    return render_template('signup.html')

app.secret_key = 'fucktheexam_hahaha'  # Required for session management

@app.route('/admin')
def Admin():
    return render_template('admin.html')

@app.route('/admin/dashboard')
def dashboard():
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT course_code) FROM image")
    total_courses = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM image")
    total_uploads = cursor.fetchone()[0]

    cursor.execute("SELECT Department, COUNT(*) FROM info GROUP BY Department")
    dept_counts = cursor.fetchall()
    dept_data = [{'department': row[0], 'count': row[1]} for row in dept_counts]

    conn.close()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_uploads=total_uploads,
                           dept_data=dept_data)

@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    images = []
    course_code = ''
    
    if request.method == 'POST':
        course_code = request.form['course_code'].upper()

        conn = sqlite3.connect('CBT1.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT uploaded_id, file_name FROM image WHERE course_code = ?", (course_code,))
        images = cursor.fetchall()
        conn.close()

    return render_template('admin_search.html', images=images, course_code=course_code)


@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == 'POST':
            # user_id=session.get('user_id')
            img = request.files['image']
            img_data=img.read()
            course_code= request.form.get('course_code')
            file_name= request.form.get('file_name')
            conn = sqlite3.connect('CBT1.db')
            cursor = conn.cursor()
            user_id = session.get('user_id')
            try:
                cursor.execute("INSERT INTO image (user_id, picture, course_code, file_name) VALUES (?, ?, ?, ?)",
               (user_id, img_data, course_code, file_name))
                conn.commit()
                flash(f'{course_code} Uploaded successfully', 'success')
                print(f'{course_code} Uploaded Successfully')
            except Exception as e:
                print(f'{course_code} Upload Failed')   
            finally:     
                conn.close()
            
            return render_template('admin.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile_setup():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']
    if request.method == 'POST':
        Fullname = request.form.get('Fullname')
        Email = request.form.get('Email')
        Matric = request.form.get('Matric')
        Department = request.form.get('Department')
        Level = request.form.get('Level')
        
        # Optional picture handling (if you want file uploads later)
        pic = request.files.get('picture')
        pic_filename = None

        if pic and pic.filename != "":
            pic_filename = f"{pic.filename}"
            pic_path = os.path.join('static/uploads', pic_filename)
            pic.save(pic_path)

        # Store in database
        conn = sqlite3.connect('CBT1.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM info WHERE Email = ?", (Email,))
        existing = cursor.fetchone()

        if existing:
            flash("Profile already exists for this email.", "warning")
            print('priofile already exists')
            return redirect('/profile/view')

        cursor.execute(
            "INSERT INTO info (Fullname, Email, Matric, Department, Level, pic) VALUES (?, ?, ?, ?, ?, ?)",
            (Fullname, Email, Matric, Department, Level, pic_filename)
        )
        conn.commit()
        conn.close()

        flash('Profile successfully registered', 'success')
        print(f'Profile Set for {Fullname}')
        return redirect('/profile/view')  # Redirect to view page

    return render_template('profile.html')  # Show setup form
@app.route('/profile/view')
def profile_view():
    if not session.get('logged_in'):
        flash("You need to log in to view your profile", "error")
        return redirect('/login')

    email = session.get('user')

    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()
    cursor.execute("SELECT Fullname, Email, Matric, Department, Level, pic FROM info WHERE Email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = {
            "fullname": user[0],
            "email": user[1],
            "matric": user[2],
            "department": user[3],
            "level": user[4],
            "pic": user[5]
        }
        return render_template('profile_view.html', user=user_data)
    else:
        flash("No profile found for this account. Please set it up.", "warning")
        return redirect('/profile')

@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Grab updated fields
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        matric = request.form.get('matric')
        department = request.form.get('department')
        level = request.form.get('level')
        pic_file = request.files.get('picture')

        if pic_file and pic_file.filename != "":
            pic_filename = f"{pic_file.filename}"
            filepath = os.path.join('static/uploads', pic_filename)
            pic_file.save(filepath)
            cursor.execute("""UPDATE info SET Fullname=?, Email=?, Department=?, Level=?, pic=? WHERE Matric=?""",
                           (fullname, email, department, level, pic_filename, matric))
        else:
            cursor.execute("""UPDATE info SET Fullname=?, Email=?, Department=?, Level=? WHERE Matric=?""",
                           (fullname, email, department, level, matric))

        conn.commit()
        conn.close()
        flash("Profile updated successfully", "success")
        return redirect("/profile/view")

    else:
        # Fetch existing data
        cursor.execute("SELECT Fullname, Email, Matric, Department, Level, pic FROM info ORDER BY rowid DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            user = {
                "fullname": row[0],
                "email": row[1],
                "matric": row[2],
                "department": row[3],
                "level": row[4],
                "pic": row[5]
            }
            return render_template("profile_edit.html", user=user)
        else:
            flash("No profile found to edit.", "error")
            return redirect("/profile")
    #return render_template("profile_edit.html", user=user)


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Fetch the user's ID from the session

    # Connect to the database
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT FullName FROM users WHERE user_id = ?", (user_id,))
    FullName = cursor.fetchone()
    
    cursor.execute("SELECT pic FROM info WHERE user_id = ? ", (user_id,))
    pic=cursor.fetchone()
    return render_template('home1.html', FullName=FullName, user_photo_url=pic)
#return 'Welcome {FullName}'
class computer_science():
    @app.route('/comsci')
    def comsci():
        if 'user_id' not in session:
            return redirect(url_for('Login'))  # Redirect to login if not logged in
        user_id = session['user_id']  # Fetch the user's ID from the session
    # Connect to the database
        conn = sqlite3.connect('CBT1.db')
        cursor = conn.cursor()
    # Fetch user details
        cursor.execute("SELECT FullName FROM users WHERE user_id = ?", (user_id,))
        FullName = cursor.fetchone()
        return render_template('comsci.html', FullName=FullName)

    @app.route('/ND1_courses')
    def ND1_courses():
        return render_template('nd1_courses.html')

    @app.route('/ND2_courses')
    def ND2_courses():
        return render_template('nd2_courses.html')

    @app.route('/HND1_courses')
    def HND1_courses():
        return render_template('hnd1_courses.html')

    @app.route('/HND2_courses')
    def HND2_courses():
        return render_template('hnd2_courses.html')

@app.route('/display/<course_code>', methods=['GET'])
def display_images(course_code):

    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()
    cursor.execute("SELECT uploaded_id FROM image WHERE course_code = ?", (course_code,))
    rows = cursor.fetchall()
    conn.close()

    images = [{"id": row[0]} for row in rows]
    return render_template('display.html', images=images, course_code=course_code)

@app.route('/image/<int:image_id>')
def get_image(image_id):
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()
    cursor.execute("SELECT picture FROM image WHERE uploaded_id = ?", (image_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return send_file(BytesIO(row[0]), mimetype='image/jpeg')
    return "Image not found", 404


@app.route('/pharmtech')
def pharmtech():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Fetch the user's ID from the session

    # Connect to the database
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT FullName FROM users WHERE user_id = ?", (user_id,))
    FullName = cursor.fetchone()

    return render_template('pharmtech.html', FullName=FullName)

@app.route('/P_ND1_courses')    
def P_ND1_courses():
    return render_template('P_nd1_courses.html')

@app.route('/P_ND2_courses')
def P_ND2_courses():
    return render_template('P_nd2_courses.html')

@app.route('/P_HND1')
def P_HND1():
    return render_template('P_HND1.html')

@app.route('/P_HND1_courses')
def P_HND1_courses():
    return render_template('P_hnd1_courses.html')

@app.route('/P_HND2')
def P_HND2():
    return render_template('P_HND2.html')

@app.route('/P_HND2_courses')
def P_HND2_courses():
    return render_template('P_hnd2_courses.html')

@app.route('/hospitality')
def hospitality():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Fetch the user's ID from the session

    # Connect to the database
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT FullName FROM users WHERE user_id = ?", (user_id,))
    FullName = cursor.fetchone()
    return render_template('hospitality.html', FullName=FullName)

@app.route('/H_ND1_courses')
def H_ND1_courses():
    return render_template('H_ND1_courses.html')

@app.route('/H_ND2_courses')
def H_ND2_courses():
    return render_template('H_ND2_courses.html')

@app.route('/H_HND1_courses')
def H_HND1_courses():
    return render_template('H_HND1_courses.html')

@app.route('/H_HND2_courses')
def H_HND2_courses():
    return render_template('H_HND2_courses.html')
@app.route('/S&M')
def statmath():
    if 'user_id' not in session:
        return redirect(url_for('Login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Fetch the user's ID from the session

    # Connect to the database
    conn = sqlite3.connect('CBT1.db')
    cursor = conn.cursor()

    # Fetch user details
    cursor.execute("SELECT FullName FROM users WHERE user_id = ?", (user_id,))
    FullName = cursor.fetchone()
    return render_template('stat_math.html', FullName=FullName)

@app.route('/SM_ND1_courses')
def SM_ND1_courses():
    return render_template('SM_ND1_courses.html')

@app.route('/SM_ND2_courses')
def SM_ND2_courses():
    return render_template('SM_ND2_courses.html')

@app.route('/SM_HND1_courses')
def SM_HND1_courses():
    return render_template('SM_HND1_courses.html')

@app.route('/SM_HND2_courses')
def SM_HND2_courses():
    return render_template('SM_HND2_courses.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)

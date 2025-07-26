from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme")

DATABASE_URL = os.environ['DATABASE_URL']

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", 
                    (request.form['username'], request.form['password']))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect(url_for('admin' if user[3] else 'dashboard'))
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    return render_template("dashboard.html", username=session['username'])

@app.route('/checkin')
def checkin():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO hours (user_id, check_in) VALUES (%s, %s)",
                (session['user_id'], datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM hours WHERE user_id = %s AND check_out IS NULL ORDER BY check_in DESC LIMIT 1",
                (session['user_id'],))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE hours SET check_out = %s WHERE id = %s",
                    (datetime.now(), row[0]))
        conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect('/')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""SELECT u.username, h.check_in, h.check_out
                   FROM hours h JOIN users u ON h.user_id = u.id
                   ORDER BY h.check_in DESC""")
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin.html", logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

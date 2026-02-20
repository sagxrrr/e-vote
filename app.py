import os
import re
import base64
from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.urandom(20)

# ----------------------------
# Database connection (PostgreSQL)
# ----------------------------
def get_db_connection():
    conn = psycopg2.connect(
    host="localhost",
    database="e-voting-system",
    user="postgres",  # PostgreSQL username
    password="postgre",  # PostgreSQL user password
    port=5432,
    cursor_factory=RealDictCursor
    )
    return conn

# ----------------------------
# Home page
# ----------------------------
@app.route('/')
def home():
    return render_template('home.html')

# ==========register info==========
@app.route('/register_info')
def register_info():
    return render_template("register_info.html")

# ==========restrictions==========
@app.route('/restrictions')
def restrictions():
    return render_template("restrictions.html")

# ==========support==========
@app.route('/support', methods=["GET", "POST"])
def support():
    if request.method == "POST":
        name = request.form["s_name"]
        email = request.form["email"]
        message = request.form["message"]

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO support (name, email, message) VALUES (%s, %s, %s)
            """, (name, email, message))
            conn.commit()
        finally:
            conn.close()
        return "Submitted successfully, <a href='/help'>Go back</a>"

    return render_template('help.html')

# ==========registration user page==========
@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        if not re.match(r'^\d{10}$', mobile):
            flash("invalid mobile number.")
            return redirect('/registration')
        gender = request.form["gender"]
        dob = request.form["dob"]
        adhar_number = request.form["adhar_number"]
        if not re.match(r'^\d{12}$', adhar_number):
            flash("invalid adhar number.")
            return redirect('/registration')
        voter_id = request.form["voter_id"]
        if not re.match(r'^[A-Z0-9]{10}$', voter_id):
            flash("invalid voter id.")
            return redirect('/registration')
        password = request.form["password"]
        if not re.match(r'[A-Za-z]', password) and len(re.findall(r'\d', password)) >= 6:
            flash("invalid password.")
            return redirect('/registration')
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM registration_information WHERE adhar_number=%s", 
                        (adhar_number,))
            if cur.fetchone():
                flash("adhar number already registered.", "error")
                return redirect('/registration')
               
            cur.execute("SELECT 1 FROM registration_information WHERE voter_id=%s", 
                        (voter_id,))        
            if cur.fetchone():
                flash("voter id already registered.", "error")
                return redirect('/registration')
            
            cur.execute("""
                INSERT INTO registration_information
                (fullname, email, mobile, gender, dob, password, adhar_number, voter_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (fullname, email, mobile, gender, dob, hashed_password, adhar_number, voter_id))
            conn.commit()
        finally:
            conn.close()

            flash("Registration successful! Please log in.", "success")

    return render_template("registration.html", fullname="", email="", mobile="", gender="", dob="", adhar_number="", voter_id="", password="")

# ==========user login==========
@app.route('/user_login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM registration_information WHERE mobile=%s", (mobile,))
            user = cur.fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user['password'], password):
            session['voter_id'] = user['voter_id']
            return redirect('/user_home')
        else:
            return "Invalid mobile or password. <a href='/user_login'>Go Back</a>"

    return render_template('user_login.html')

# ==========user home==========
@app.route('/user_home')
def user_home():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT election_name FROM election_info ORDER BY eid DESC")
        elections = cur.fetchall()
    finally:
        conn.close()

    return render_template('user_home.html', elections=elections)

# ==========logout user==========
@app.route('/logout_user')
def logout_user():
    session.clear()
    return redirect(url_for('login'))

# ==========vote page==========
@app.route("/vote_page", methods=["GET"])
def vote_page():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate_information")
        rows = cur.fetchall()
    finally:
        conn.close()

    candidates = []
    for row in rows:
        logo = ""
        if row["party_logo"]:
            logo = base64.b64encode(row["party_logo"]).decode("utf-8")
        candidates.append({
            "id": row["id"],
            "candidate_name": row["candidate_name"],
            "party_name": row["party_name"],
            "party_logo": logo
        })

    message = "इथे काळजीपूर्वक उमेदवार पाहून त्याच्या समोरील बटण दाबा"
    return render_template("vote_page.html", candidates=candidates, message=message)

# ==========vote submission==========
@app.route("/vote_candidate", methods=["POST"])
def vote_candidate():
    candidate_id = request.form["candidate_id"]
    voter_id = session["voter_id"]

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM votes WHERE voter_id=%s", (voter_id,))
        existing_vote = cur.fetchone()
        if existing_vote:
            return "You have already voted. <a href='/user_home'>Go Back</a>"

        cur.execute("SELECT candidate_name FROM candidate_information WHERE id=%s", (candidate_id,))
        candidate_row = cur.fetchone()
        candidate_name = candidate_row['candidate_name']

        cur.execute(
            "INSERT INTO votes (candidate_id, candidate_name, voter_id) VALUES (%s, %s, %s)",
            (candidate_id, candidate_name, voter_id)
        )
        conn.commit()
    finally:
        conn.close()

    flash("Your vote has been cast successfully!", "success")
    return redirect("/user_home")

# ==========admin home==========
@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html', candidate_count=get_candidate_count(), voter_count=get_voter_count())

def get_candidate_count():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM candidate_information")
        count = cur.fetchone()['count']
    finally:
        conn.close()
    return count

def get_voter_count():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM registration_information")
        count = cur.fetchone()['count']
    finally:
        conn.close()
    return count

# ==========about==========
@app.route('/about')
def about():
    return render_template('about.html')

# ==========help==========
@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/help_request')
def help_request():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM support")
        rows = cur.fetchall()
    finally:
        conn.close()

    requests = []
    for row in rows:
        requests.append({
            "sid": row["sid"],
            "name": row["name"],
            "email": row["email"],
            "message": row["message"]
        })
    return render_template('help_request.html', requests=requests)

# ==========instruction user==========
@app.route('/instruction_user')
def instruction_user():
    return render_template('instruction_user.html')

# ==========election info==========
@app.route('/add_election', methods=['GET', 'POST'])
def add_election():
    if request.method == 'POST':
        election_name = request.form['election_name']
        election_date = request.form['election_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO election_info (election_name, election_date, start_time, end_time)
                VALUES (%s, %s, %s, %s)
            """, (election_name, election_date, start_time, end_time))
            conn.commit()
        finally:
            conn.close()
        flash("Election added successfully!", "success")

    return render_template("add_election.html")

# ==========admin login==========
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM admin_info WHERE username=%s AND password=%s", (username, password))
            user = cur.fetchone()
        finally:
            conn.close()

        if user and user['password'] == password:
            session['username'] = user['username']
            return redirect('/admin_home')
        else:
            return "Invalid username or password. <a href='/admin_login'>Go Back</a>"

    return render_template('admin_login.html')

# ==========logout admin==========
@app.route('/logout_admin')
def logout_admin():
    session.clear()
    return redirect(url_for('admin_login'))

# ==========reset data==========
@app.route('/reset_data')
def reset_data():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM candidate_information")
        cur.execute("DELETE FROM votes")
        cur.execute("DELETE FROM election_info")
        cur.execute("DELETE FROM support")
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "reset"})

# ==========remove all users==========
@app.route('/remove_all_users')
def remove_all_users():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM registration_information")
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "success", "message": "All users removed successfully"})

# ==========add candidate==========
@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        candidate_name = request.form['candidate_name']
        party_name = request.form['party_name']
        party_logo = request.files['party_logo'].read()
        election_date = request.form['election_date']

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO candidate_information (candidate_name, party_name, party_logo, election_date)
                VALUES (%s, %s, %s, %s)
            """, (candidate_name, party_name, party_logo, election_date))
            conn.commit()
        finally:
            conn.close()
            flash("Candidate added successfully!", "success")

        return render_template('add_candidate.html')

# ==========view candidates==========
@app.route("/view_candidates")
def view_candidates():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidate_information")
        rows = cur.fetchall()
    finally:
        conn.close()

    candidates = []
    for row in rows:
        logo = ""
        if row["party_logo"]:
            logo = base64.b64encode(row["party_logo"]).decode("utf-8")
        candidates.append({
            "id": row["id"],
            "candidate_name": row["candidate_name"],
            "party_name": row["party_name"],
            "election_date": row["election_date"],
            "party_logo": logo
        })

    return render_template("view_candidates.html", candidates=candidates)

# ==========results==========
@app.route('/result')
def view_result():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT candidate_id, candidate_name, COUNT(candidate_id) AS total_votes
            FROM votes
            GROUP BY candidate_id, candidate_name
            ORDER BY total_votes DESC
        """)
        results = cur.fetchall()
    finally:
        conn.close()

    return render_template('result.html', results=results)

# ==========show election==========
@app.route('/show_election')
def show_election():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT election_name FROM election_info ORDER BY eid DESC")
        elections = cur.fetchall()
    finally:
        conn.close()

    return render_template('show_election.html', elections=elections)

# ==========RUN APP==========
if __name__ == "__main__":
    app.run(debug=False)
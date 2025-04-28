import psycopg2
import json 
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
 
app = Flask(__name__)
app.secret_key = 'your_secret_key'
tracked_emails = []  # Ensure this is defined at the top
 
def get_db_connection():
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="postgres",
        password="guyi2123",
        host="localhost",
        port="5432"
    )
    return conn
 
# -------------------- AUTH ROUTES --------------------
 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form.get('age', type=int)  # Get age as an integer
 
        # Validate age
        if age is None or age < 18:
            flash('You must be at least 18 years old to register.', 'error')
            return redirect(url_for('register'))
 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cur.fetchone()
 
        if existing_user:
            flash('Username already exists, please choose another', 'error')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cur.execute('INSERT INTO users (username, password_hash, age) VALUES (%s, %s, %s)', (username, hashed_password, age))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
 
        cur.close()
        conn.close()
 
    return render_template('register.html')
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
 
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
 
        if user:
            hashed_password = user[2]  # Password hash stored in DB
            if check_password_hash(hashed_password, password):
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('email_results'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User does not exist', 'error')
 
        cur.close()
        conn.close()
 
    return render_template('login.html')
 
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
 
# -------------------- MAIN FUNCTIONALITY ROUTES --------------------
 
@app.route('/')
def home():
    return render_template('index.html')
 
@app.route('/about')
def about():
    return render_template('about.html')
 
@app.route('/services')
def services():
    return render_template('services.html')
 
@app.route('/confirmation')
def confirm():
    return render_template('confirmation.html')
 
@app.route('/api/track-email', methods=['POST'])
def track_email():
    data = request.json
    email = data.get('email')
    url = data.get("url")  
    timestamp = data.get("timestamp")
 
    if email:
        tracked_emails.append({
            "email": email,
            "url": url,
            "timestamp": timestamp
        })
        print(f"📩 Email Logged: {email} at {url} on {timestamp}")
 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO registrations (email, url, timestamp) VALUES (%s, %s, %s)", (email, url, timestamp))
    conn.commit()
    cur.close()
    conn.close()
 
    return jsonify({"message": "Email and URL tracked successfully"}), 200
 
# Track login attempts
@app.route('/api/track-login', methods=['POST'])
def track_login():
    data = request.json
    email = data.get('email')
    url = data.get('url')
    timestamp = data.get('timestamp')
 
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO logins (email, url, timestamp) VALUES (%s, %s, %s)", (email, url, timestamp))
    conn.commit()
    cur.close()
    conn.close()
 
    return jsonify({"message": "Login tracked successfully"}), 200
 
@app.route('/email_results')
def email_results():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch email registrations
    cur.execute("SELECT email, url, timestamp FROM registrations ORDER BY timestamp DESC")
    registrations = cur.fetchall()
 
    # Fetch login attempts
    cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
    logins = cur.fetchall()
 
    # Fetch visits
    cur.execute("SELECT url, timestamp, is_incognito FROM visited_websites WHERE child_id = 1")
    visits = cur.fetchall()
    print("🔄 Visits from DB:", visits)  # Debug line
 
    cur.execute("SELECT activity_type, data, timestamp FROM system_activities ORDER BY timestamp DESC")
    activities = cur.fetchall()

    cur.execute("SELECT keyword, context, timestamp FROM keyword_alerts ORDER BY timestamp DESC")
    keyword_alerts = cur.fetchall()
 
    cur.close()
    conn.close()
 
    return render_template('email_results.html', registrations=registrations, logins=logins, visits=visits, activities=activities, keyword_alerts=keyword_alerts)
 
@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    data = request.get_json(silent=True)  # Silent=True prevents None on parse errors
    if not data:
        print("❌ Invalid or empty JSON received")
        return jsonify({"error": "Invalid data"}), 400
    
    url = data.get('url', 'Unknown URL')
    timestamp = data.get('timestamp', 'Unknown Timestamp')
    is_incognito = data.get('is_incognito', False)
 
    # Insert into database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visited_websites (url, timestamp, child_id, is_incognito)
            SELECT %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM visited_websites 
                WHERE url = %s AND timestamp = %s
            )
        """, (url, timestamp, 1, is_incognito, url, timestamp))
        conn.commit()
        print(f"✅ Saved visit: {url} (Incognito: {is_incognito})")
    except Exception as e:
        print("❌ Database error:", e)
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    return jsonify({"message": "Visit tracked"}), 200
 
@app.route('/api/activity-data')
def activity_data():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Registrations
    cur.execute("SELECT email, url, timestamp FROM registrations ORDER BY timestamp DESC")
    registrations = [{"email": r[0], "url": r[1], "timestamp": r[2]} for r in cur.fetchall()]
    
    # Logins
    cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
    logins = [{"email": l[0], "url": l[1], "timestamp": l[2]} for l in cur.fetchall()]
    
    # Visits
    cur.execute("SELECT url, timestamp, is_incognito FROM visited_websites ORDER BY timestamp DESC")
    visits = [{"url": v[0], "timestamp": v[1], "is_incognito": v[2]} for v in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({
        "registrations": registrations,
        "logins": logins,
        "visits": visits
    })
 
@app.route('/api/track-activity', methods=['POST'])
def track_activity():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO system_activities (activity_type, data, timestamp) VALUES (%s, %s, %s)", (data['type'], json.dumps(data['data']), data['timestamp']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/api/track-keyword', methods=['POST'])
def track_keyword():
    data = request.json
    keyword = data.get('keyword')
    context = data.get('context')
    timestamp = data.get('timestamp')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO keyword_alerts (keyword, context, timestamp, child_id) VALUES (%s, %s, %s, %s)",
        (keyword, context, timestamp, 1)  # Assume child_id=1 for demo
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Keyword alert logged"}), 200
 
@app.route('/media/<path:filename>')
def media_files(filename):
    try:
        return send_from_directory('media', filename)
    except FileNotFoundError:
        abort(404)  # Return 404 if the file is not found
 
# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(debug=True) 

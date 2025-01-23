import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

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

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to database and check if the username already exists
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Username already exists, please choose another', 'error')
        else:
            # Hash the password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            # Insert the new user into the database
            cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        cur.close()
        conn.close()
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to database and verify username and password
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        
        if user:
            hashed_password = user[2]  # The password_hash is at index 2
            if check_password_hash(hashed_password, password):
                session['username'] = username  # Store username in session
                flash('Login successful!', 'success')
                return redirect(url_for('email_results'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User does not exist', 'error')
        
        cur.close()
        conn.close()

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from the session
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# -------------------- MAIN FUNCTIONALITY ROUTES --------------------

# Homepage route (optional)
@app.route('/')
def home():
    return render_template('index.html')

#Track Email Registrations  
@app.route('/api/track-email', methods=['POST'])
def track_email():
    data = request.json
    email = data.get('email')
    url = data.get("url")  # Capture URL
    timestamp = data.get("timestamp")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO registrations (email, url, timestamp) VALUES (%s, %s, %s)", (email, url, timestamp))
    conn.commit()
    cur.close()
    conn.close()

    if email:
        tracked_emails.append({
            "email": email,
            "url": url,  # Storing the URL
            "timestamp": timestamp
        })
    return jsonify({"message": "Email and URL tracked successfully"}), 200

# API route to receive registration data from the browser extension
@app.route('/api/register', methods=['POST'])
def register_data():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    email = data.get('email')
    url = data.get('url')
    timestamp = data.get('timestamp')

    # Store the registration data (email, website URL, and timestamp)
    registrations.append({
        'email': email,
        'url': url,
        'timestamp': timestamp
    })

    return jsonify({"status": "success"}), 200
 
tracked_emails = []



@app.route('/email_results')
def email_results():
    return render_template('email_results.html', emails=tracked_emails)

# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(debug=True)

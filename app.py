from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# In-memory user storage (you can replace this with a database later)
users = {}
registrations = []  # Store email registrations here

# -------------------- AUTH ROUTES --------------------

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            flash('Username already exists, please choose another', 'error')
        else:
            # Hash the password using a supported method
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            users[username] = hashed_password
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            hashed_password = users[username]
            if check_password_hash(hashed_password, password):
                session['username'] = username  # Store username in session
                flash('Login successful!', 'success')
                return redirect(url_for('email_results'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User does not exist', 'error')
    
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
    return render_template('index.html')  # Make sure you have an index.html file

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


# Email checking route (if needed for other functionalities)
@app.route('/check_email', methods=['POST'])
def check_email():
    if 'username' not in session:
        flash('You need to log in to access this page', 'error')
        return redirect(url_for('login'))

    email = request.form['email']
    # Add your email checking logic here
    return render_template('email_results.html', email=email)
    
tracked_emails = []

@app.route('/api/track-email', methods=['POST'])
def track_email():
    data = request.json
    email = data.get("email")
    if email:
        tracked_emails.append(email)
    return jsonify({"message": "Email tracked successfully"}), 200

@app.route('/email_results')
def email_results():
    return render_template('email_results.html', emails=tracked_emails)

# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash

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

        user_password = users.get(username)

        if user_password and check_password_hash(user_password, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('email_results'))  # Redirect to the dashboard
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
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

# Route to display the results of the email registrations (login required)
@app.route('/email_results')
def email_results():
    if 'username' not in session:
        flash('You need to log in to access this page', 'error')
        return redirect(url_for('login'))

    return render_template('email_results.html', registrations=registrations)

# Email checking route (if needed for other functionalities)
@app.route('/check_email', methods=['POST'])
def check_email():
    if 'username' not in session:
        flash('You need to log in to access this page', 'error')
        return redirect(url_for('login'))

    email = request.form['email']
    # Add your email checking logic here
    return render_template('email_results.html', email=email)

# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(debug=True)

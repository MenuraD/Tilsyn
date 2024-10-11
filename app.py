from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy credentials (username and password for the parent)
PARENT_USERNAME = 'parent'
PARENT_PASSWORD = 'password123'

# Dummy data for child activity which i will expand later
child_activity = [
    {"site": "example.com", "time": "10:30 AM"},
    {"site": "socialmedia.com", "time": "11:00 AM"},
    {"site": "educational.com", "time": "1:30 PM"},
]

# Simulated email registration data
email_registrations = {
    "test@example.com": ["socialmedia.com", "shopping.com", "forum.com"],
    "child@example.com": ["gamesite.com", "streaming.com", "eduportal.com"]
}

# Homepage route
@app.route('/')
def home():
    return "Welcome to Tilsyn!"

# Login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials are correct
        if username == PARENT_USERNAME and password == PARENT_PASSWORD:
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials. Please try again."

    return render_template('login.html')

# Dashboard route (after successful login)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', activity=child_activity)

# Email tracker route
@app.route('/email_tracker', methods=['GET', 'POST'])
def email_tracker():
    if request.method == 'POST':
        email = request.form['email']
        # Simulate checking where the email has been registered
        registered_sites = email_registrations.get(email, [])
        return render_template('email_results.html', email=email, registered_sites=registered_sites)
    return render_template('email_tracker.html')

if __name__ == '__main__':
    app.run(debug=True)
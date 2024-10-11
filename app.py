from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy credentials (username and password for the parent)
PARENT_USERNAME = 'parent'
PARENT_PASSWORD = 'password123'

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
    return "Welcome to the parent dashboard. Here you'll monitor the child's online activity."

if __name__ == '__main__':
    app.run(debug=True)
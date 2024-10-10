from flask import Flask, render_template, request

app = Flask(__name__)

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
        # Print the login info
        print(f'Username: {username}, Password: {password}')
        return f'Logged in as {username}'
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
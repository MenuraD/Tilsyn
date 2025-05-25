import psycopg2
import json 
import ipaddress
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory, abort
from utils import check_url_safety
from werkzeug.security import generate_password_hash, check_password_hash
 
GOOGLE_API_KEY = 'AIzaSyCRmQY4AI-QMeddt68nn82C7ME7nfeF1-o'
 
app = Flask(__name__)
app.secret_key = 'your_secret_key'
tracked_emails = []  
 
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
@app.template_filter('fromjson')
def fromjson_filter(data):
    try:
        return json.loads(data)
    except:
        return data 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        age = request.form.get('age', type=int)

        if age < 12 or age >= 18:
            flash('Child accounts must be between 12-17 years old', 'error')
            return redirect(url_for('register'))

        try:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('''
                INSERT INTO users (name, username, password_hash, age, is_child)
                VALUES (%s, %s, %s, %s, TRUE)
                RETURNING id
            ''', (name, username, hashed_password, age))

            child_id = cur.fetchone()[0]
            session['child_id'] = child_id  
            conn.commit()

            flash('Child account created. Please register parent account', 'success')
            return redirect(url_for('adult_register'))

        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            cur.close()
            conn.close()

    return render_template('register.html')
 
@app.route('/adult_register', methods=['GET', 'POST'])
def adult_register():
    if 'child_id' not in session:
        flash('Please register child first', 'error')
        return redirect(url_for('register'))

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        age = request.form.get('age', type=int)

        if age < 18:
            flash('Parent must be at least 18 years old', 'error')
            return redirect(url_for('adult_register'))

        try:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('''
                INSERT INTO users (name, username, password_hash, age, is_child)
                VALUES (%s, %s, %s, %s, FALSE)
                RETURNING id
            ''', (name, username, hashed_password, age))
            
            parent_user_id = cur.fetchone()[0]

            cur.execute('''
                INSERT INTO adults (user_id)
                VALUES (%s)
                RETURNING id
            ''', (parent_user_id,))
            
            adult_id = cur.fetchone()[0]

            cur.execute('''
                UPDATE users
                SET adult_id = %s
                WHERE id = %s
            ''', (adult_id, session['child_id']))

            conn.commit()
            session['parent_id'] = adult_id
            flash('Parent account created and linked successfully!', 'success')
            return redirect(url_for('welcome'))

        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            cur.close()
            conn.close()

    return render_template('adult_register.html')
 
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
            hashed_password = user[2]
            if check_password_hash(hashed_password, password):
                user_id = user[0]
                cur.execute('SELECT id FROM adults WHERE user_id = %s', (user_id,))
                is_adult = cur.fetchone() is not None
                cur.close()
                conn.close()

                session['username'] = username
                session['user_id'] = user_id  
                session['is_adult'] = is_adult  
                flash('Login successful!', 'success')
                if is_adult:
                    return redirect(url_for('parents_dashboard'))
                else:
                    return redirect(url_for('permissions_dashboard'))
            else:
                flash('Invalid password', 'error')
        else:
            flash('User does not exist', 'error')
        cur.close()
        conn.close()
    return render_template('login.html')

@app.route('/permissions_dashboard')
def permissions_dashboard():
    if 'username' not in session:
        flash('Please login to view this page.', 'error')
        return redirect(url_for('login'))
    
    return render_template('permissions_dashboard.html')
 
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
 
@app.route('/confirmation2')
def confirmation2():
    return render_template('confirmation-2.html')
 
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

@app.route('/api/email-visibility', methods=['GET', 'POST'])
def handle_email_visibility():
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]

        if request.method == 'GET':
            cur.execute('SELECT show_email_registrations FROM users WHERE id = %s', (user_id,))
            visible = cur.fetchone()[0]
            return jsonify({"visible": visible})

        elif request.method == 'POST':
            data = request.json
            new_state = data.get('visible', True)
            
            cur.execute('UPDATE users SET show_email_registrations = %s WHERE id = %s',
                       (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
 
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

@app.route('/api/login-visibility', methods=['GET', 'POST'])
def handle_login_visibility():
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT id FROM users WHERE username = %s', (session['username'],))
        user_id = cur.fetchone()[0]

        if request.method == 'GET':
            cur.execute('SELECT show_email_logins FROM users WHERE id = %s', (user_id,))
            visible = cur.fetchone()[0]
            return jsonify({"visible": visible})

        elif request.method == 'POST':
            data = request.json
            new_state = data.get('visible', True)
            cur.execute('UPDATE users SET show_email_logins = %s WHERE id = %s',
                        (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/ip-visibility', methods=['GET', 'POST'])
def handle_ip_visibility():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            cur.execute('SELECT show_ip_history FROM users WHERE id = %s', (user_id,))
            return jsonify({"visible": bool(cur.fetchone()[0])})
            
        elif request.method == 'POST':
            new_state = request.json.get('visible', True)
            cur.execute('''
                UPDATE users 
                SET show_ip_history = %s 
                WHERE id = %s
            ''', (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print(f"IP Visibility Error: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/visited-visibility', methods=['GET', 'POST'])
def handle_visited_visibility():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            cur.execute('SELECT show_visited_websites FROM users WHERE id = %s', (user_id,))
            return jsonify({"visible": bool(cur.fetchone()[0])})
            
        elif request.method == 'POST':
            new_state = request.json.get('visible', True)
            cur.execute('''
                UPDATE users
                SET show_visited_websites = %s
                WHERE id = %s
            ''', (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print(f"Visited Visibility Error: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/system-activities-visibility', methods=['GET', 'POST'])
def handle_system_activities_visibility():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            cur.execute('SELECT show_system_activities FROM users WHERE id = %s', (user_id,))
            return jsonify({"visible": bool(cur.fetchone()[0])})
            
        elif request.method == 'POST':
            new_state = request.json.get('visible', True)
            cur.execute('''
                UPDATE users
                SET show_system_activities = %s
                WHERE id = %s
            ''', (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print(f"System Activities Visibility Error: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/keyword-visibility', methods=['GET', 'POST'])
def handle_keyword_visibility():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            cur.execute('SELECT show_keyword_alerts FROM users WHERE id = %s', (user_id,))
            return jsonify({"visible": bool(cur.fetchone()[0])})
            
        elif request.method == 'POST':
            new_state = request.json.get('visible', True)
            cur.execute('''
                UPDATE users
                SET show_keyword_alerts = %s
                WHERE id = %s
            ''', (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print(f"Keyword Visibility Error: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/ip_tracking')
def ip_tracking():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
            SELECT show_ip_history 
            FROM users 
            WHERE adult_id = (
                SELECT id FROM adults WHERE user_id = %s
            )
        ''', (session['user_id'],))
        
        result = cur.fetchone()
        show_ip = result[0] if result else True
        ip_history = []
        common_country = None
        if show_ip:
            cur.execute('''
                SELECT ip_address, country, city, is_vpn, timestamp
                FROM ip_history
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                ORDER BY timestamp DESC
            ''', (session['user_id'],))
            
            ip_history = cur.fetchall()

            cur.execute('''
                SELECT country, COUNT(*) as count
                FROM ip_history
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                GROUP BY country
                ORDER BY count DESC
                LIMIT 1
            ''', (session['user_id'],))
            common_country = cur.fetchone()

    except Exception as e:
        print(f"IP Tracking Error: {str(e)}")
        flash('Error loading IP history', 'error')
    finally:
        cur.close()
        conn.close()

    return render_template('ip_tracking.html',
                         ip_history=ip_history,
                         common_country=common_country[0] if common_country else None,
                         show_ip=show_ip)

@app.route('/login_attempts')
def login_attempts():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    parent_user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        SELECT child.show_email_logins
        FROM users child
        JOIN adults a ON child.adult_id = a.id
        WHERE a.user_id = %s
    ''', (parent_user_id,))
    result_login = cur.fetchone()
    show_logins = result_login[0] if result_login else True

    if show_logins:
        cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
        logins = cur.fetchall()
    else:
        logins = []

    cur.close()
    conn.close()

    return render_template('login_attempts.html',
                         logins=logins,
                         show_logins=show_logins)

@app.route('/api/login-data')
def login_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
    logins = [{"email": l[0], "url": l[1], "timestamp": l[2]} for l in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"logins": logins})

@app.route('/visited_websites')
def visited_websites():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
            SELECT show_visited_websites 
            FROM users 
            WHERE adult_id = (
                SELECT id FROM adults WHERE user_id = %s
            )
        ''', (session['user_id'],))
        
        result = cur.fetchone()
        show_visited = result[0] if result else True

        visits = []
        if show_visited:
            cur.execute('''
                SELECT url, timestamp, is_incognito 
                FROM visited_websites 
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                ORDER BY timestamp DESC
            ''', (session['user_id'],))
            visits = cur.fetchall()

    except Exception as e:
        print(f"Visited Websites Error: {str(e)}")
        flash('Error loading visited websites', 'error')
    finally:
        cur.close()
        conn.close()

    return render_template('visited_websites.html', 
                         visits=visits,
                         show_visited=show_visited)

app.route('/api/visited-websites')
def visited_websites_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT show_visited_websites 
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        visible = cur.fetchone()[0]

        visits = []
        if visible:
            cur.execute('''
                SELECT url, timestamp, is_incognito 
                FROM visited_websites 
                ORDER BY timestamp DESC
            ''')
            visits = [{"url": v[0], "timestamp": v[1], "is_incognito": v[2]} 
                     for v in cur.fetchall()]
            
    except Exception as e:
        print(f"Visited Websites Data Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return jsonify({"visits": visits})

@app.route('/system_activities')
def system_activities():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    activities = []

    try:
        cur.execute('''
            SELECT show_system_activities 
            FROM users 
            WHERE adult_id = (
                SELECT id FROM adults WHERE user_id = %s
            )
        ''', (session['user_id'],))
        
        result = cur.fetchone()
        show_activities = result[0] if result else True

        if show_activities:
            cur.execute('''
                SELECT activity_type, data::text, timestamp
                FROM system_activities
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                ORDER BY timestamp DESC
            ''', (session['user_id'],))
            activities = cur.fetchall()

    except Exception as e:
        print(f"System Activities Error: {str(e)}")
        flash('Error loading system activities', 'error')
    finally:
        cur.close()
        conn.close()

    return render_template('system_activities.html', 
                         activities=activities,
                         show_activities=show_activities)

@app.route('/api/system-activities')
def system_activities_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    activities = []

    try:
        cur.execute('''
            SELECT show_system_activities 
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        visible = cur.fetchone()[0]

        if visible:
            cur.execute('''
                SELECT activity_type, data::text, timestamp
                FROM system_activities
                ORDER BY timestamp DESC
            ''')
            activities = [{
                "type": row[0],
                "details": row[1],
                "timestamp": row[2]
            } for row in cur.fetchall()]
            
    except Exception as e:
        print(f"System Activities Data Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return jsonify({"activities": activities})

@app.route('/keyword_alerts')
def keyword_alerts():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    alerts = []

    try:
        cur.execute('''
            SELECT show_keyword_alerts 
            FROM users 
            WHERE adult_id = (
                SELECT id FROM adults WHERE user_id = %s
            )
        ''', (session['user_id'],))
        
        result = cur.fetchone()
        show_keyword = result[0] if result else True

        if show_keyword:
            cur.execute('''
                SELECT keyword, context, timestamp 
                FROM keyword_alerts
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                ORDER BY timestamp DESC
            ''', (session['user_id'],))
            alerts = cur.fetchall()

    except Exception as e:
        print(f"Keyword Alerts Error: {str(e)}")
        flash('Error loading keyword alerts', 'error')
    finally:
        cur.close()
        conn.close()

    return render_template('keyword_alerts.html', 
                         keyword_alerts=alerts,
                         show_keyword=show_keyword)

@app.route('/api/keyword-data')
def keyword_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    keywords = []

    try:
        cur.execute('''
            SELECT show_keyword_alerts 
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        visible = cur.fetchone()[0]

        if visible:
            cur.execute('''
                SELECT keyword, context, timestamp 
                FROM keyword_alerts 
                ORDER BY timestamp DESC
            ''')
            keywords = [{
                "keyword": row[0], 
                "context": row[1], 
                "timestamp": row[2]
            } for row in cur.fetchall()]
            
    except Exception as e:
        print(f"Keyword Data Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return jsonify({"keywords": keywords})

@app.route('/api/screen-visibility', methods=['GET', 'POST'])
def handle_screen_visibility():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        user_id = session['user_id']
        
        if request.method == 'GET':
            cur.execute('SELECT show_screen_management FROM users WHERE id = %s', (user_id,))
            return jsonify({"visible": bool(cur.fetchone()[0])})
            
        elif request.method == 'POST':
            new_state = request.json.get('visible', True)
            cur.execute('''
                UPDATE users
                SET show_screen_management = %s
                WHERE id = %s
            ''', (new_state, user_id))
            conn.commit()
            return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        print(f"Screen Visibility Error: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        cur.close()
        conn.close()



@app.route('/unsafe_websites')
def unsafe_websites():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT url, timestamp, is_incognito 
        FROM visited_websites 
        WHERE is_safe = FALSE 
        ORDER BY timestamp DESC
    """)
    websites = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('unsafe_websites.html', websites=websites)

@app.route('/api/unsafe-websites')
def unsafe_websites_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT url, timestamp, is_incognito 
        FROM visited_websites 
        WHERE is_safe = FALSE 
        ORDER BY timestamp DESC
    """)
    websites = [{"url": w[0], "timestamp": w[1], "is_incognito": w[2]} for w in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"websites": websites})

@app.route('/screen_management')
def screen_management():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    screen_time = {}

    try:
        cur.execute('''
            SELECT show_screen_management 
            FROM users 
            WHERE adult_id = (
                SELECT id FROM adults WHERE user_id = %s
            )
        ''', (session['user_id'],))
        
        result = cur.fetchone()
        show_screen = result[0] if result else True

        if show_screen:
            cur.execute('''
                SELECT app_name, SUM(duration) as total
                FROM screen_time
                WHERE child_id = (
                    SELECT id FROM users WHERE adult_id = (
                        SELECT id FROM adults WHERE user_id = %s
                    )
                )
                AND date = CURRENT_DATE
                GROUP BY app_name
            ''', (session['user_id'],))
            screen_time = {row[0]: row[1] for row in cur.fetchall()}

    except Exception as e:
        print(f"Screen Management Error: {str(e)}")
        flash('Error loading screen time data', 'error')
    finally:
        cur.close()
        conn.close()

    return render_template('screen_management.html',
                         screen_time=screen_time,
                         show_screen=show_screen)

@app.route('/parents_dashboard')
def parents_dashboard():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))
    return render_template('parents_dashboard.html')

@app.route('/email_results')
def email_results():
    if 'user_id' not in session or not session.get('is_adult'):
        flash('Please login as a parent to view this page.', 'error')
        return redirect(url_for('login'))
    
    parent_user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        SELECT child.show_email_registrations
        FROM users child
        JOIN adults a ON child.adult_id = a.id
        WHERE a.user_id = %s
    ''', (parent_user_id,))
    result = cur.fetchone()
    show_emails = result[0] if result else True

    cur.execute('''
        SELECT child.show_email_registrations
        FROM users child
        JOIN adults a ON child.adult_id = a.id
        WHERE a.user_id = %s
    ''', (parent_user_id,))
    result = cur.fetchone()
    show_emails = result[0] if result else True

    if show_emails:
        cur.execute("SELECT email, url, timestamp FROM registrations ORDER BY timestamp DESC")
        registrations = cur.fetchall()
    else:
        registrations = []

    if show_emails:  
        cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
        logins = cur.fetchall()
    else:
        logins = []


    cur.execute('''
        SELECT child.show_email_logins
        FROM users child
        JOIN adults a ON child.adult_id = a.id
        WHERE a.user_id = %s
    ''', (parent_user_id,))
    result_login = cur.fetchone()
    show_logins = result_login[0] if result_login else True

    if show_logins:
        cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
        logins = cur.fetchall()
    else:
        logins = []
 
    cur.execute("SELECT url, timestamp, is_incognito, is_safe FROM visited_websites WHERE child_id = 1")
    visits = cur.fetchall()
    print("🔄 Visits from DB:", visits)  
 
    cur.execute("""
    SELECT DISTINCT ON (data->>'applications') 
        activity_type, data, timestamp 
    FROM system_activities 
    WHERE activity_type = 'application_usage' 
    ORDER BY data->>'applications', timestamp DESC
    """)
    activities = cur.fetchall()
    screen_time = cur.fetchall()  
 
    cur.close()
    conn.close()
 
    return render_template('email_results.html',
                           registrations=registrations,
                           logins=logins,
                           visits=visits,
                           show_emails=show_emails,
                           show_logins=show_logins,  
                           activities=activities,
                           keyword_alerts=keyword_alerts,
                           screen_time=dict(screen_time))
 
@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    data = request.get_json(silent=True)  
    if not data:
        print("❌ Invalid or empty JSON received")
        return jsonify({"error": "Invalid data"}), 400
    
    url = data.get('url', 'Unknown URL')
    timestamp = data.get('timestamp', 'Unknown Timestamp')
    is_incognito = data.get('is_incognito', False)
    is_safe = check_url_safety(url, GOOGLE_API_KEY)
 
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visited_websites 
            (url, timestamp, child_id, is_incognito, is_safe)
            SELECT %s, %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM visited_websites
                WHERE url = %s AND timestamp = %s
            )
        """, (url, timestamp, 1, is_incognito, is_safe, url, timestamp))
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
    
    cur.execute("SELECT email, url, timestamp FROM registrations ORDER BY timestamp DESC")
    registrations = [{"email": r[0], "url": r[1], "timestamp": r[2]} for r in cur.fetchall()]
    
    cur.execute("SELECT email, url, timestamp FROM logins ORDER BY timestamp DESC")
    logins = [{"email": l[0], "url": l[1], "timestamp": l[2]} for l in cur.fetchall()]
    
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
    activity_type = data.get('type')
    app_names = data.get('data', {}).get('applications', [])
 
    conn = get_db_connection()
    cur = conn.cursor()
 
    for app_name in app_names:
        cur.execute("""
            SELECT 1 FROM system_activities 
            WHERE activity_type = 'application_usage' 
            AND data->'applications' @> %s::jsonb  -- JSONB containment check
            AND timestamp >= NOW() - INTERVAL '5 minutes'
        """, (json.dumps([app_name]),)) 
 
        exists = cur.fetchone()
 
        if not exists:
            cur.execute(
                "INSERT INTO system_activities (activity_type, data, timestamp) VALUES (%s, %s, %s)",
                (activity_type, json.dumps({"applications": [app_name]}), data['timestamp'])
            )
 
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"}), 200
 
@app.route('/api/track-keyword', methods=['POST'])
def track_keyword():
    data = request.json
    keyword = data.get('data', {}).get('keyword')
    context = data.get('data', {}).get('context', 'Potential risk detected')
    timestamp = data.get('timestamp') or datetime.now().isoformat() 

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE age < 18 ORDER BY id DESC LIMIT 1")
        child_result = cur.fetchone()
        
        if not child_result:  
            print("🔥 No child users found")
            return jsonify({"error": "No child account exists"}), 400
            
        child_id = child_result[0]
        
        print(f"📢 Tracking keyword: {keyword} | Child: {child_id} | Time: {timestamp}")
        
        cur.execute(
            "INSERT INTO keyword_alerts (keyword, context, timestamp, child_id) VALUES (%s, %s, %s, %s)",
            (keyword, context, timestamp, child_id)
        )
        conn.commit()
        return jsonify({"message": "Keyword alert logged"}), 200
        
    except Exception as e:
        conn.rollback()
        print(f"🔥 Database Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()
 
@app.route('/media/<path:filename>')
def media_files(filename):
    try:
        return send_from_directory('media', filename)
    except FileNotFoundError:
        abort(404)  
 
@app.route('/api/track-screen-time', methods=['POST'])
def track_screen_time():
    data = request.json
    child_id = 1  
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for app_name, duration in data.get('app_usage', {}).items():
            duration_seconds = int(float(duration))
            
            cur.execute("""
                INSERT INTO screen_time (child_id, app_name, duration, date)
                VALUES (%s, %s, %s, CURRENT_DATE)
                ON CONFLICT (child_id, app_name, date)
                DO UPDATE SET duration = screen_time.duration + EXCLUDED.duration
                """, 
                (child_id, app_name, duration_seconds)
            )
        
        conn.commit()
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        if conn:
            cur.close()
            conn.close()
 
@app.route('/test-screen-time')
def test_screen_time():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO screen_time (child_id, app_name, duration, date)
        VALUES (1, 'chrome.exe', 3600, CURRENT_DATE)
    """)
    conn.commit()
    return "Test data added!"
 
@app.route('/api/screen-time-data')
def screen_time_data():
    if 'user_id' not in session or not session.get('is_adult'):
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    screen_time = []

    try:
        cur.execute('''
            SELECT show_screen_management 
            FROM users 
            WHERE id = %s
        ''', (session['user_id'],))
        visible = cur.fetchone()[0]

        if visible:
            cur.execute('''
                SELECT app_name, SUM(duration) as total
                FROM screen_time
                WHERE date = CURRENT_DATE
                GROUP BY app_name
            ''')
            screen_time = [{
                "app_name": row[0],
                "duration": row[1]
            } for row in cur.fetchall()]
            
    except Exception as e:
        print(f"Screen Time Data Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return jsonify({"screen_time": screen_time})
 
@app.route('/welcome')
def welcome():
    parent_id = session.get('parent_id')
    child_id = session.get('child_id')
    
    if not parent_id or not child_id:
        flash('Registration incomplete', 'error')
        return redirect(url_for('home'))
 
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT u.name, u.age 
            FROM adults a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = %s
        ''', (parent_id,))
        parent_data = cur.fetchone()
        
        cur.execute('''
            SELECT name, age FROM users
            WHERE id = %s
        ''', (child_id,))
        child_data = cur.fetchone()
 
        if not parent_data or not child_data:
            flash('Account linkage error', 'error')
            return redirect(url_for('home'))
 
        session.pop('parent_id', None)
        session.pop('child_id', None)
 
        return render_template('welcome.html',
            parent_name=parent_data[0],
            parent_age=parent_data[1],
            child_name=child_data[0],
            child_age=child_data[1]
        )
 
    except Exception as e:
        print(f"Welcome error: {str(e)}")
        flash('Failed to load welcome page', 'error')
        return redirect(url_for('home'))
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Database connection closed")

@app.route('/api/track-ip', methods=['POST'])
def track_ip():
    data = request.json
    child_id = 1  

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT country, COUNT(*) as count
            FROM ip_history
            WHERE child_id = %s
            GROUP BY country
            ORDER BY count DESC
            LIMIT 1
        """, (child_id,))
        common_country_result = cur.fetchone()
        common_country = common_country_result[0] if common_country_result else None

        new_country = data.get('country')
        is_vpn = data.get('is_vpn', False)  

        if common_country and new_country != common_country:
            is_vpn = True

        cur.execute("""
            INSERT INTO ip_history (child_id, ip_address, country, city, is_vpn)
            VALUES (%s, %s, %s, %s, %s)
        """, (child_id, data['ip_address'], new_country, data['city'], is_vpn))

        conn.commit()
    except Exception as e:
        print(f"IP Tracking Error: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({"status": "success"}), 200
 
 
# -------------------- RUN FLASK --------------------
if __name__ == '__main__':
    app.run(debug=True)  

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

DB_PATH = 'campus_lost_found.db'

# Initial setup
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Routes ---

@app.route('/')
def index():
    db = get_db()
    items = db.execute('SELECT * FROM items ORDER BY date DESC LIMIT 6').fetchall()
    return render_template('index.html', items=items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        
        if user:
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'user_id' not in session:
        flash('Please login to report an item.', 'warning')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form['item_name']
        description = request.form['description']
        category = request.form['category']
        location = request.form['location']
        contact_number = request.form['contact_number']
        status = request.form['status']
        file = request.files.get('image')
        
        # Server-side validation
        if not (name.replace(' ', '').isalnum() and len(name) <= 15):
            flash('Item name must contain only letters/numbers and be max 15 characters.', 'error')
            return redirect(url_for('report'))
        if not (location.replace(' ', '').isalnum() and len(location) <= 15):
            flash('Location must contain only letters/numbers and be max 15 characters.', 'error')
            return redirect(url_for('report'))
        if not (contact_number.isdigit() and len(contact_number) == 10):
            flash('Mobile number must be exactly 10 digits.', 'error')
            return redirect(url_for('report'))
        
        word_count = len(description.split())
        if word_count > 500:
            flash('Description must be below 500 words.', 'error')
            return redirect(url_for('report'))

        if not file or file.filename == '':
            flash('Item photo is required.', 'error')
            return redirect(url_for('report'))

        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        db = get_db()
        db.execute('''
            INSERT INTO items (item_name, description, category, location, contact_number, image_path, status, reported_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, category, location, contact_number, filename, status, session['user_id']))
        db.commit()
        flash('Item reported successfully!', 'success')
        return redirect(url_for('items'))
        
    return render_template('report.html')

@app.route('/items')
def items():
    db = get_db()
    user_id = session.get('user_id')
    if user_id:
        items = db.execute('''
            SELECT i.*, c.claim_status as user_claim_status 
            FROM items i 
            LEFT JOIN claims c ON i.item_id = c.item_id AND c.user_id = ?
            ORDER BY i.date DESC
        ''', (user_id,)).fetchall()
    else:
        items = db.execute('SELECT * FROM items ORDER BY date DESC').fetchall()
    return render_template('items.html', items=items)

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    db = get_db()
    user_id = session.get('user_id')
    item = db.execute('''
        SELECT i.*, u.name as reporter_name,
               (SELECT claim_status FROM claims WHERE item_id = i.item_id AND user_id = ?) as user_claim_status
        FROM items i 
        JOIN users u ON i.reported_by = u.user_id 
        WHERE i.item_id = ?
    ''', (user_id, item_id)).fetchone()
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('items'))
    return render_template('item_detail.html', item=item)

@app.route('/claim/<int:item_id>', methods=['POST'])
def claim_item(item_id):
    if 'user_id' not in session:
        flash('Please login to claim.', 'warning')
        return redirect(url_for('login'))
        
    db = get_db()
    # Check if already claimed
    existing = db.execute('SELECT 1 FROM claims WHERE item_id = ? AND user_id = ?', 
                          (item_id, session['user_id'])).fetchone()
    if existing:
        flash('You have already submitted a claim for this item.', 'info')
        return redirect(url_for('items'))

    db.execute('INSERT INTO claims (item_id, user_id) VALUES (?, ?)', (item_id, session['user_id']))
    db.commit()
    flash('item claim status is send to the admin approval', 'success')
    return redirect(url_for('items'))

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    db = get_db()
    items = db.execute('SELECT * FROM items').fetchall()
    claims = db.execute('''
        SELECT c.*, i.item_name, u.name as user_name 
        FROM claims c 
        JOIN items i ON c.item_id = i.item_id 
        JOIN users u ON c.user_id = u.user_id
    ''').fetchall()
    return render_template('admin.html', items=items, claims=claims)

@app.route('/admin/approve_claim/<int:claim_id>')
def approve_claim(claim_id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    db = get_db()
    # Update claim status
    db.execute('UPDATE claims SET claim_status = "Approved" WHERE claim_id = ?', (claim_id,))
    # Get item_id to update item status
    claim = db.execute('SELECT item_id FROM claims WHERE claim_id = ?', (claim_id,)).fetchone()
    db.execute('UPDATE items SET status = "Claimed" WHERE item_id = ?', (claim['item_id'],))
    db.commit()
    flash('Claim approved and item status updated.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/delete_item/<int:item_id>')
def delete_item(item_id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    db = get_db()
    db.execute('DELETE FROM claims WHERE item_id = ?', (item_id,))
    db.execute('DELETE FROM items WHERE item_id = ?', (item_id,))
    db.commit()
    flash('Item deleted successfully.', 'info')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)

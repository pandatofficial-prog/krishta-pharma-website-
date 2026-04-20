import os
import time
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import psycopg
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'krishat_pharma_secret_key_2024')

# Use /tmp on Render (writable), local filesystem otherwise
if os.environ.get('RENDER_SERVICE_ID'):
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder locally (Render uses /tmp which exists)
if not os.path.exists(UPLOAD_FOLDER) and not os.environ.get('RENDER_SERVICE_ID'):
    os.makedirs(UPLOAD_FOLDER)

DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if not USE_POSTGRES:
    DATABASE = 'pharma.db'

def get_db_connection():
    if USE_POSTGRES:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    if USE_POSTGRES:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id SERIAL PRIMARY KEY,
                      username VARCHAR(255) UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id SERIAL PRIMARY KEY,
                      name TEXT NOT NULL,
                      price REAL NOT NULL,
                      description TEXT,
                      image TEXT)''')
        conn.commit()
        c.execute("SELECT COUNT(*) as count FROM admins")
        row = c.fetchone()
        count = row['count']
        if count == 0:
            hashed_pw = generate_password_hash('admin123')
            c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", ('admin', hashed_pw))
            c.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", ('manager', generate_password_hash('manager123')))
        conn.close()
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      price REAL NOT NULL,
                      description TEXT,
                      image TEXT)''')
        c.execute("SELECT COUNT(*) as count FROM admins")
        row = c.fetchone()
        count = row['count'] if hasattr(row, '__getitem__') and isinstance(row, dict) else row[0]
        if count == 0:
            hashed_pw = generate_password_hash('admin123')
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hashed_pw))
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('manager', generate_password_hash('manager123')))
        conn.commit()
        conn.close()

# Initialize DB with retry (Render DB may not be ready immediately)
def init_db_retry(max_retries=5, delay=3):
    for attempt in range(max_retries):
        try:
            init_db()
            logger.info("Database initialized")
            return
        except Exception as e:
            logger.warning(f"DB init attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                logger.error("DB initialization failed after retries")
                raise

try:
    init_db_retry()
except Exception as e:
    logger.error(f"Fatal error during startup: {e}")
    exit(1)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def ensure_upload_folder():
    try:
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        return True
    except Exception as e:
        logger.error(f"Cannot create upload folder: {e}")
        return False

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/our-approach')
def approach():
    return render_template('approach.html')

@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/distribution-network')
def distribution():
    return render_template('distribution.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/job-openings')
def job_openings():
    return render_template('job_openings.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/press-releases')
def press():
    return render_template('press.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact_alt():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact_alt'))
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        if USE_POSTGRES:
            admin = conn.execute('SELECT * FROM admins WHERE username = %s', (username,)).fetchone()
        else:
            admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['username'] = admin['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('dashboard.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'admin_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        image = request.files['image']
        filename = None
        if image and allowed_file(image.filename):
            if ensure_upload_folder():
                filename = secure_filename(image.filename)
                try:
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    logger.error(f"Failed to save image: {e}")
                    flash('Failed to save image. Check folder permissions.', 'danger')
                    return redirect(url_for('add_product'))
        conn = get_db_connection()
        if USE_POSTGRES:
            conn.execute('INSERT INTO products (name, price, description, image) VALUES (%s, %s, %s, %s)',
                         (name, price, description, filename))
        else:
            conn.execute('INSERT INTO products (name, price, description, image) VALUES (?, ?, ?, ?)',
                         (name, price, description, filename))
        conn.commit()
        conn.close()
        flash('Product added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'admin_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    if USE_POSTGRES:
        product = conn.execute('SELECT * FROM products WHERE id = %s', (id,)).fetchone()
    else:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        image = request.files['image']
        filename = product['image']
        if image and allowed_file(image.filename):
            if ensure_upload_folder():
                filename = secure_filename(image.filename)
                try:
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                except Exception as e:
                    logger.error(f"Failed to save image: {e}")
                    flash('Failed to save image. Check folder permissions.', 'danger')
                    return redirect(url_for('edit_product', id=id))
        if USE_POSTGRES:
            conn.execute('UPDATE products SET name = %s, price = %s, description = %s, image = %s WHERE id = %s',
                         (name, price, description, filename, id))
        else:
            conn.execute('UPDATE products SET name = ?, price = ?, description = ?, image = ? WHERE id = ?',
                         (name, price, description, filename, id))
        conn.commit()
        conn.close()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'admin_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    if USE_POSTGRES:
        product = conn.execute('SELECT * FROM products WHERE id = %s', (id,)).fetchone()
    else:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    if product and product['image']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'])
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                logger.error(f"Failed to delete image {image_path}: {e}")
    if USE_POSTGRES:
        conn.execute('DELETE FROM products WHERE id = %s', (id,))
    else:
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

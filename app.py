import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'krishat_pharma_secret_key_2024'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

DATABASE = 'pharma.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
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
    
    c.execute("SELECT COUNT(*) FROM admins")
    if c.fetchone()[0] == 0:
        hashed_pw = generate_password_hash('admin123')
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hashed_pw))
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('manager', generate_password_hash('manager123')))
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/contacts')
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/contact')
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
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        conn = get_db_connection()
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
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        image = request.files['image']
        
        filename = product['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
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
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    
    if product and product['image']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'])
        if os.path.exists(image_path):
            os.remove(image_path)
    
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
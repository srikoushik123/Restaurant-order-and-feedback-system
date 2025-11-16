from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import create_app, mysql, User, MenuItem, Order, Feedback
from werkzeug.security import generate_password_hash, check_password_hash
import functools

app = create_app()

# Decorators
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            flash('Admin access required')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            User.create_user(username, email, hashed_password)
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Username or email already exists')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get_user_by_username(username)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            session.permanent = True
            
            if user['user_type'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Customer Routes
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if session['user_type'] != 'customer':
        flash('Access denied')
        return redirect(url_for('admin_dashboard'))
    
    menu_items = MenuItem.get_all_available()
    return render_template('customer/dashboard.html', menu_items=menu_items)

@app.route('/customer/order', methods=['POST'])
@login_required
def place_order():
    if session['user_type'] != 'customer':
        flash('Access denied')
        return redirect(url_for('admin_dashboard'))
    
    try:
        order_id = Order.create_order(session['user_id'])
        items_added = False
        
        for key, value in request.form.items():
            if key.startswith('item_'):
                item_id = key.split('_')[1]
                quantity = int(value)
                
                if quantity > 0:
                    items_added = True
                    item = MenuItem.get_by_id(item_id)
                    Order.add_order_item(order_id, item_id, quantity, item['price'])
        
        if not items_added:
            flash('Please select at least one item')
            return redirect(url_for('customer_dashboard'))
        
        flash('Order placed successfully!')
        return redirect(url_for('order_history'))
    
    except Exception as e:
        flash('Error placing order')
        return redirect(url_for('customer_dashboard'))

@app.route('/customer/orders')
@login_required
def order_history():
    if session['user_type'] != 'customer':
        return redirect(url_for('admin_orders'))
    
    orders = Order.get_customer_orders(session['user_id'])
    
    # Check feedback status for each order
    for order in orders:
        order['feedback_submitted'] = Feedback.check_feedback_exists(session['user_id'], order['order_id'])
    
    return render_template('customer/orders.html', orders=orders)

@app.route('/customer/order/<int:order_id>')
@login_required
def order_details(order_id):
    order, items = Order.get_order_details(order_id)
    
    if order['customer_id'] != session['user_id'] and session['user_type'] != 'admin':
        flash('Access denied')
        return redirect(url_for('customer_dashboard'))
    
    feedback = Feedback.get_feedback_for_order(order_id)
    return render_template('customer/order_details.html', order=order, items=items, feedback=feedback)

@app.route('/customer/feedback/<int:order_id>', methods=['POST'])
@login_required
def submit_feedback(order_id):
    if session['user_type'] != 'customer':
        flash('Access denied')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Check if feedback already exists
        if Feedback.check_feedback_exists(session['user_id'], order_id):
            flash('You have already submitted feedback for this order')
            return redirect(url_for('order_details', order_id=order_id))
        
        rating = request.form['rating']
        comment = request.form.get('comment', '')
        
        # Validate rating
        if not rating or int(rating) < 1 or int(rating) > 5:
            flash('Please provide a valid rating between 1 and 5')
            return redirect(url_for('order_details', order_id=order_id))
        
        Feedback.submit_feedback(session['user_id'], order_id, rating, comment)
        flash('Thank you for your valuable feedback!')
        
    except Exception as e:
        flash('Error submitting feedback. Please try again.')
    
    return redirect(url_for('order_details', order_id=order_id))

# Admin Routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = mysql.connection
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cursor.fetchone()['total_orders']
    
    cursor.execute("SELECT COUNT(*) as pending_orders FROM orders WHERE status = 'pending'")
    pending_orders = cursor.fetchone()['pending_orders']
    
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status = 'completed'")
    total_revenue = cursor.fetchone()['total_revenue']
    
    cursor.execute("SELECT COUNT(*) as total_customers FROM users WHERE user_type = 'customer'")
    total_customers = cursor.fetchone()['total_customers']
    
    cursor.close()
    
    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_revenue=total_revenue,
                         total_customers=total_customers)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.get_all_orders()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>/update_status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form['status']
    
    try:
        Order.update_order_status(order_id, new_status)
        flash('Order status updated successfully')
    except Exception as e:
        flash('Error updating order status')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/menu')
@admin_required
def admin_menu():
    conn = mysql.connection
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.*, c.name as category_name 
        FROM menu_items m 
        JOIN categories c ON m.category_id = c.category_id
        ORDER BY m.category_id, m.name
    """)
    menu_items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    cursor.close()
    
    return render_template('admin/menu.html', menu_items=menu_items, categories=categories)

@app.route('/admin/menu/add', methods=['POST'])
@admin_required
def add_menu_item():
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    category_id = int(request.form['category_id'])
    
    try:
        MenuItem.create_item(name, description, price, category_id)
        flash('Menu item added successfully')
    except Exception as e:
        flash('Error adding menu item')
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    feedback_list = Feedback.get_all_feedback()
    return render_template('admin/feedback.html', feedback_list=feedback_list)

# Setup Routes
@app.route('/setup-demo-users')
def setup_demo_users():
    try:
        conn = mysql.connection
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM users WHERE username IN ('admin', 'customer1', 'customer2')")
        
        users = [
            ('admin', 'admin@restaurant.com', generate_password_hash('admin123'), 'admin'),
            ('customer1', 'customer1@email.com', generate_password_hash('customer123'), 'customer'),
            ('customer2', 'customer2@email.com', generate_password_hash('customer123'), 'customer')
        ]
        
        for username, email, password, user_type in users:
            cursor.execute(
                "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
                (username, email, password, user_type)
            )
        
        conn.commit()
        cursor.close()
        
        flash('Demo users created successfully! Use: admin/admin123 or customer1/customer123')
        return redirect(url_for('login'))
        
    except Exception as e:
        flash(f'Error creating demo users: {str(e)}')
        return redirect(url_for('login'))

@app.route('/debug-users')
def debug_users():
    """Debug route to check user data"""
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, password, user_type FROM users")
    users = cursor.fetchall()
    cursor.close()
    
    result = []
    for user in users:
        result.append({
            'user_id': user['user_id'],
            'username': user['username'],
            'password': user['password'],
            'password_length': len(user['password']),
            'user_type': user['user_type'],
            'is_hashed': user['password'].startswith('$2b$')
        })
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
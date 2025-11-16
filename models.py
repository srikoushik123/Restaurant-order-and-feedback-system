from flask import Flask
from flask_mysqldb import MySQL
from config import Config

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    mysql.init_app(app)
    return app

class User:
    @staticmethod
    def create_user(username, email, password, user_type='customer'):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
                (username, email, password, user_type)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_user_by_username(username):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user

class MenuItem:
    @staticmethod
    def get_all_available():
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, c.name as category_name 
            FROM menu_items m 
            JOIN categories c ON m.category_id = c.category_id 
            WHERE m.is_available = TRUE
        """)
        items = cursor.fetchall()
        cursor.close()
        return items

    @staticmethod
    def get_by_id(item_id):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()
        cursor.close()
        return item

    @staticmethod
    def create_item(name, description, price, category_id, image_url=None):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO menu_items (name, description, price, category_id, image_url) VALUES (%s, %s, %s, %s, %s)",
                (name, description, price, category_id, image_url)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

class Order:
    @staticmethod
    def create_order(customer_id):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO orders (customer_id) VALUES (%s)",
                (customer_id,)
            )
            order_id = cursor.lastrowid
            conn.commit()
            return order_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def add_order_item(order_id, item_id, quantity, price):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO order_items (order_id, item_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, item_id, quantity, price)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_customer_orders(customer_id):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, 
                   COUNT(oi.order_item_id) as item_count,
                   SUM(oi.quantity) as total_quantity
            FROM orders o 
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.customer_id = %s 
            GROUP BY o.order_id 
            ORDER BY o.created_at DESC
        """, (customer_id,))
        orders = cursor.fetchall()
        cursor.close()
        return orders

    @staticmethod
    def get_order_details(order_id):
        conn = mysql.connection
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()
        
        cursor.execute("""
            SELECT oi.*, m.name as item_name, m.description
            FROM order_items oi 
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        
        cursor.close()
        return order, items

    @staticmethod
    def update_order_status(order_id, status):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                (status, order_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_all_orders():
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, u.username,
                   COUNT(oi.order_item_id) as item_count
            FROM orders o 
            JOIN users u ON o.customer_id = u.user_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id 
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
        cursor.close()
        return orders

class Feedback:
    @staticmethod
    def submit_feedback(customer_id, order_id, rating, comment):
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO feedback (customer_id, order_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (customer_id, order_id, rating, comment)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @staticmethod
    def get_feedback_for_order(order_id):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, u.username 
            FROM feedback f 
            JOIN users u ON f.customer_id = u.user_id 
            WHERE f.order_id = %s
        """, (order_id,))
        feedback = cursor.fetchone()
        cursor.close()
        return feedback

    @staticmethod
    def get_all_feedback():
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, u.username, o.order_id
            FROM feedback f 
            JOIN users u ON f.customer_id = u.user_id
            JOIN orders o ON f.order_id = o.order_id
            ORDER BY f.created_at DESC
        """)
        feedback_list = cursor.fetchall()
        cursor.close()
        return feedback_list

    @staticmethod
    def check_feedback_exists(customer_id, order_id):
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM feedback 
            WHERE customer_id = %s AND order_id = %s
        """, (customer_id, order_id))
        feedback = cursor.fetchone()
        cursor.close()
        return feedback is not None
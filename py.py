import mysql.connector
from werkzeug.security import generate_password_hash

def reset_database():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''  # Use your MySQL root password here
        )
        cursor = conn.cursor()
        
        # Drop and recreate database
        cursor.execute("DROP DATABASE IF EXISTS restaurant_db")
        cursor.execute("CREATE DATABASE restaurant_db")
        cursor.execute("USE restaurant_db")
        
        # Create tables
        tables_sql = """
        -- Users table
        CREATE TABLE users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            user_type ENUM('admin', 'customer') DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Categories table
        CREATE TABLE categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Menu items table
        CREATE TABLE menu_items (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            category_id INT,
            is_available BOOLEAN DEFAULT TRUE,
            image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        );

        -- Orders table
        CREATE TABLE orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            total_amount DECIMAL(10,2) DEFAULT 0,
            status ENUM('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id)
        );

        -- Order items table
        CREATE TABLE order_items (
            order_item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            item_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
        );

        -- Feedback table
        CREATE TABLE feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            order_id INT,
            rating INT CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );
        """
        
        # Execute table creation
        for statement in tables_sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        # Create triggers
        triggers_sql = """
        DELIMITER //
        CREATE TRIGGER update_order_total
        AFTER INSERT ON order_items
        FOR EACH ROW
        BEGIN
            UPDATE orders 
            SET total_amount = (
                SELECT SUM(quantity * price) 
                FROM order_items 
                WHERE order_id = NEW.order_id
            )
            WHERE order_id = NEW.order_id;
        END//
        
        CREATE TRIGGER update_order_total_on_update
        AFTER UPDATE ON order_items
        FOR EACH ROW
        BEGIN
            UPDATE orders 
            SET total_amount = (
                SELECT SUM(quantity * price) 
                FROM order_items 
                WHERE order_id = NEW.order_id
            )
            WHERE order_id = NEW.order_id;
        END//
        
        CREATE TRIGGER update_order_total_on_delete
        AFTER DELETE ON order_items
        FOR EACH ROW
        BEGIN
            UPDATE orders 
            SET total_amount = (
                SELECT COALESCE(SUM(quantity * price), 0) 
                FROM order_items 
                WHERE order_id = OLD.order_id
            )
            WHERE order_id = OLD.order_id;
        END//
        DELIMITER ;
        """
        
        for statement in triggers_sql.split('//'):
            if statement.strip():
                cursor.execute(statement)
        
        # Insert sample data with PROPERLY HASHED PASSWORDS
        admin_hash = generate_password_hash('admin123')
        customer_hash = generate_password_hash('customer123')
        
        # Insert users
        cursor.execute(
            "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
            ('admin', 'admin@restaurant.com', admin_hash, 'admin')
        )
        cursor.execute(
            "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
            ('customer1', 'customer1@email.com', customer_hash, 'customer')
        )
        cursor.execute(
            "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)",
            ('customer2', 'customer2@email.com', customer_hash, 'customer')
        )
        
        # Insert categories
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s)",
            ('Appetizers', 'Start your meal right')
        )
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s)",
            ('Main Course', 'Hearty main dishes')
        )
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s)",
            ('Desserts', 'Sweet endings')
        )
        cursor.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s)",
            ('Beverages', 'Refreshing drinks')
        )
        
        # Insert menu items
        menu_items = [
            ('Garlic Bread', 'Freshly baked bread with garlic butter', 4.99, 1),
            ('Bruschetta', 'Toasted bread topped with tomatoes and basil', 5.99, 1),
            ('Spaghetti Carbonara', 'Classic pasta with creamy sauce and bacon', 12.99, 2),
            ('Grilled Salmon', 'Fresh salmon with lemon butter sauce', 16.99, 2),
            ('Chocolate Cake', 'Rich chocolate cake with ganache', 6.99, 3),
            ('Tiramisu', 'Classic Italian dessert', 7.99, 3),
            ('Fresh Lemonade', 'Homemade lemonade', 3.99, 4),
            ('Iced Tea', 'Refreshing iced tea', 2.99, 4)
        ]
        
        for item in menu_items:
            cursor.execute(
                "INSERT INTO menu_items (name, description, price, category_id) VALUES (%s, %s, %s, %s)",
                item
            )
        
        conn.commit()
        print("Database reset successfully!")
        print("Admin credentials: admin / admin123")
        print("Customer credentials: customer1 / customer123")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    reset_database()


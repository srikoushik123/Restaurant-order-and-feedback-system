-- Drop and recreate database
DROP DATABASE IF EXISTS restaurant_db;
CREATE DATABASE restaurant_db;
USE restaurant_db;

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
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    UNIQUE KEY unique_order_feedback (order_id)  -- One feedback per order
);

-- TRIGGERS for automatic total calculation
DELIMITER //

-- Trigger when order items are inserted
CREATE TRIGGER after_order_item_insert
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

-- Trigger when order items are updated
CREATE TRIGGER after_order_item_update
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

-- Trigger when order items are deleted
CREATE TRIGGER after_order_item_delete
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

-- Function to get average rating for menu items
CREATE FUNCTION get_item_rating(item_id_param INT) 
RETURNS DECIMAL(3,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE avg_rating DECIMAL(3,2);
    
    SELECT AVG(f.rating) INTO avg_rating
    FROM feedback f
    JOIN orders o ON f.order_id = o.order_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.item_id = item_id_param;
    
    RETURN COALESCE(avg_rating, 0);
END//

DELIMITER ;

-- Insert sample data
INSERT INTO categories (name, description) VALUES 
('Appetizers', 'Start your meal right'),
('Main Course', 'Hearty main dishes'),
('Desserts', 'Sweet endings'),
('Beverages', 'Refreshing drinks');

INSERT INTO menu_items (name, description, price, category_id) VALUES 
('Garlic Bread', 'Freshly baked bread with garlic butter', 4.99, 1),
('Bruschetta', 'Toasted bread topped with tomatoes and basil', 5.99, 1),
('Spaghetti Carbonara', 'Classic pasta with creamy sauce and bacon', 12.99, 2),
('Grilled Salmon', 'Fresh salmon with lemon butter sauce', 16.99, 2),
('Chocolate Cake', 'Rich chocolate cake with ganache', 6.99, 3),
('Tiramisu', 'Classic Italian dessert', 7.99, 3),
('Fresh Lemonade', 'Homemade lemonade', 3.99, 4),
('Iced Tea', 'Refreshing iced tea', 2.99, 4);
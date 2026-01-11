import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE products_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    username TEXT DEFAULT 'Guest'
)
""")

# Copy data from the old table to the new table
cursor.execute("INSERT INTO products_new (name, description, price, username) SELECT name, description, price, username FROM products")

# Drop the old table
cursor.execute("DROP TABLE products")

# Rename the new table to the original table name
cursor.execute("ALTER TABLE products_new RENAME TO products")

# Commit the changes
conn.commit()
conn.close()
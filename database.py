import sqlite3

# Function to create and return the database connection
def create_connection():
    return sqlite3.connect("users.db")

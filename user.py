import sqlite3
import argparse
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Database setup
DB_NAME = 'instance/users.db'

class UserManager:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Initialize the database and create the users table if it doesn't exist."""
        if not os.path.exists(self.db_name):
            os.makedirs(os.path.dirname(self.db_name), exist_ok=True)
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            conn.commit()

    def create_user(self, email, password):
        """Create a new user with a hashed password."""
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
                conn.commit()
                print(f"User '{email}' created successfully.")
            except sqlite3.IntegrityError:
                print(f"Error: User with email '{email}' already exists.")

    def show_users(self):
        """Display all users in the database."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, email FROM users')
            users = cursor.fetchall()
            if not users:
                print("No users found.")
                return
            print("Users:")
            for user in users:
                print(f"ID: {user[0]}, Email: {user[1]}")

    def delete_user(self, email):
        """Delete a user by their email."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE email = ?', (email,))
            if cursor.rowcount > 0:
                conn.commit()
                print(f"User '{email}' deleted successfully.")
            else:
                print(f"Error: User with email '{email}' not found.")

    def authenticate_user(self, email, password):
        """Authenticate a user by their email and password."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if user and check_password_hash(user[0], password):
                print(f"Authentication successful for '{email}'.")
            else:
                print("Authentication failed: Invalid email or password.")


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description='User management CLI')
    parser.add_argument('command', choices=['create', 'show', 'delete', 'login'], help='Command to execute')
    parser.add_argument('--email', help='Email of the user')
    parser.add_argument('--password', help='Password of the user (required for create and login)')

    args = parser.parse_args()

    user_manager = UserManager()

    if args.command == 'create':
        if not args.email or not args.password:
            print("Error: Email and password are required to create a user.")
            return
        user_manager.create_user(args.email, args.password)

    elif args.command == 'show':
        user_manager.show_users()

    elif args.command == 'delete':
        if not args.email:
            print("Error: Email is required to delete a user.")
            return
        user_manager.delete_user(args.email)

    elif args.command == 'login':
        if not args.email or not args.password:
            print("Error: Email and password are required for login.")
            return
        user_manager.authenticate_user(args.email, args.password)


if __name__ == "__main__":
    main()

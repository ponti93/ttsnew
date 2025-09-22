import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
from getpass import getpass

def create_database():
    # Load environment variables
    load_dotenv()
    
    # Get password securely
    print("Please enter your PostgreSQL password:")
    password = getpass()
    
    # Connect to PostgreSQL server
    print("Connecting to PostgreSQL server...")
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password=password,
        host='localhost'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    # Create a cursor
    cur = conn.cursor()
    
    try:
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='pronunciation_app'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database 'pronunciation_app'...")
            cur.execute('CREATE DATABASE pronunciation_app')
            print("Database created successfully!")
        else:
            print("Database 'pronunciation_app' already exists.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()
    
    return True

def init_tables():
    print("Initializing database tables...")
    try:
        import sys
        from pathlib import Path
        
        # Add the project root directory to Python path
        project_root = str(Path(__file__).parent)
        if project_root not in sys.path:
            sys.path.append(project_root)
            
        from models.database import init_db
        init_db()
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if create_database():
        init_tables()
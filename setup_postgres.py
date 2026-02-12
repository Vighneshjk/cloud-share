
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "cloud_share"
DB_USER = "postgres"
DB_PASSWORD = "password"  # Update this if your password is different
DB_HOST = "localhost"
DB_PORT = "5432"

def create_db():
    try:
        con = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
            
        cur.close()
        con.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"Error connecting to PostgreSQL server: {e}")
        print("Please check if PostgreSQL is running and the credentials in 'settings.py' are correct.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    create_db()

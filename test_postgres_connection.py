
import psycopg2

def try_connect(password):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password=password,
            host="localhost",
            port="5432"
        )
        print(f"SUCCESS: Connected with password '{password}'")
        conn.close()
        return True
    except psycopg2.OperationalError:
        print(f"FAILED: Could not connect with password '{password}'")
        return False

if __name__ == "__main__":
    passwords = ["", "postgres", "password", "admin", "123456", "admin123"]
    success = False
    for p in passwords:
        if try_connect(p):
            success = True
            break
            
    if not success:
        print("COULD NOT CONNECT with common passwords. Please check your PostgreSQL installation and credentials.")

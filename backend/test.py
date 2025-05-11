import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="your_username",
        password="your_password"
    )
    print("Successfully connected to MySQL!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
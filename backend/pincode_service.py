import mysql.connector
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class PincodeService:
    def __init__(self):
        self.db_config = {
            'host': os.getenv("DB_HOST"),
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'database': os.getenv("DB_NAME")
        }

    def initialize_pincodes_table(self):
        """Initialize the pincodes table if it doesn't exist"""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pincodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                circle_name VARCHAR(100),
                region_name VARCHAR(100),
                division_name VARCHAR(100),
                office_name VARCHAR(100),
                pincode VARCHAR(10),
                office_type VARCHAR(10),
                delivery_type VARCHAR(20),
                district VARCHAR(100),
                state_name VARCHAR(100),
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pincode (pincode),
                INDEX idx_office_name (office_name),
                INDEX idx_district (district)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()

    def import_from_csv(self, file):
        """Import pincode data from CSV file"""
        try:
            csv_data = csv.DictReader(file.read().decode('utf-8').splitlines())
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute("TRUNCATE TABLE pincodes")
            
            # Batch insert for better performance
            batch_size = 1000
            batch = []
            
            for row in csv_data:
                batch.append((
                    row['CircleName'],
                    row['RegionName'],
                    row['DivisionName'],
                    row['OfficeName'],
                    row['Pincode'],
                    row['OfficeType'],
                    row['Delivery'],
                    row['District'],
                    row['StateName'],
                    float(row['Latitude']) if row['Latitude'] else None,
                    float(row['Longitude']) if row['Longitude'] else None
                ))
                
                if len(batch) >= batch_size:
                    cursor.executemany("""
                        INSERT INTO pincodes (
                            circle_name, region_name, division_name, office_name,
                            pincode, office_type, delivery_type, district,
                            state_name, latitude, longitude
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, batch)
                    conn.commit()
                    batch = []
            
            # Insert remaining records
            if batch:
                cursor.executemany("""
                    INSERT INTO pincodes (
                        circle_name, region_name, division_name, office_name,
                        pincode, office_type, delivery_type, district,
                        state_name, latitude, longitude
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch)
                conn.commit()
            
            cursor.close()
            conn.close()
            
            return True, "Pincodes imported successfully"
        
        except Exception as e:
            return False, str(e)

    def get_pincodes(self, page=1, per_page=50):
        """Get paginated list of pincodes"""
        try:
            offset = (page - 1) * per_page
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM pincodes")
            total = cursor.fetchone()['total']
            
            # Get paginated data
            cursor.execute("""
                SELECT * FROM pincodes
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            pincodes = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'data': pincodes,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        
        except Exception as e:
            raise Exception(f"Failed to fetch pincodes: {str(e)}")

    def search_pincodes(self, query, limit=10):
        """Search pincodes by pincode, office name or district"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM pincodes
                WHERE pincode LIKE %s OR office_name LIKE %s OR district LIKE %s
                LIMIT %s
            """, (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
        
        except Exception as e:
            raise Exception(f"Failed to search pincodes: {str(e)}")
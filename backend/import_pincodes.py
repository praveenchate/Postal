import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def create_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "parcelpro")
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def validate_coordinate(coord, coord_type):
    """Validate and normalize coordinates"""
    try:
        # Handle string representations of numbers
        if isinstance(coord, str):
            if coord.strip() in ['', 'NA', 'N/A']:
                return None
            coord = float(coord)
            
        # Check for clearly invalid values (like 4-digit numbers)
        if abs(coord) > 1000:
            # Check if it might be a decimal in wrong format (e.g., 123456 => 123.456)
            if 1000 < abs(coord) <= 9999:
                coord = coord / 100
            elif 10000 < abs(coord) <= 99999:
                coord = coord / 1000
            else:
                return None
                
        # Validate ranges
        if coord_type == 'lat' and not (-90 <= coord <= 90):
            return None
        if coord_type == 'lon' and not (-180 <= coord <= 180):
            return None
            
        return round(coord, 8)
    except (ValueError, TypeError):
        return None

def import_pincodes(csv_file):
    start_time = datetime.now()
    print(f"Import started at: {start_time}")
    
    print("\nLoading and validating CSV file...")
    try:
        # Load CSV with proper handling
        df = pd.read_csv(
            csv_file,
            dtype={
                'CircleName': 'str',
                'RegionName': 'str',
                'DivisionName': 'str',
                'OfficeName': 'str',
                'Pincode': 'str',
                'OfficeType': 'str',
                'Delivery': 'str',
                'District': 'str',
                'StateName': 'str',
                'Latitude': 'object',
                'Longitude': 'object'
            },
            na_values=['NA', 'N/A', ''],
            keep_default_na=False
        )
        
        # Rename columns to match database
        df.columns = [
            'circle_name', 'region_name', 'division_name', 'office_name',
            'pincode', 'office_type', 'delivery_type', 'district',
            'state_name', 'latitude', 'longitude'
        ]
        
        # Clean and validate coordinates
        df['latitude'] = df['latitude'].apply(lambda x: validate_coordinate(x, 'lat'))
        df['longitude'] = df['longitude'].apply(lambda x: validate_coordinate(x, 'lon'))
        
        # Count invalid coordinates
        invalid_coords = df[(df['latitude'].isna()) | (df['longitude'].isna())].shape[0]
        print(f"✅ Loaded {len(df)} records ({invalid_coords} with invalid coordinates)")
        
        # Remove records with invalid coordinates
        df = df.dropna(subset=['latitude', 'longitude'])
        print(f"📊 Proceeding with {len(df)} valid records")
        
        # Show sample of cleaned data
        print("\nSample of cleaned data:")
        print(df.head(3).to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return

    # Connect to database
    print("\nConnecting to MySQL database...")
    conn = create_db_connection()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        # Create table with extended precision
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
            latitude DECIMAL(12, 8),  -- Increased precision
            longitude DECIMAL(13, 8),  -- Increased precision
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_pincode (pincode),
            INDEX idx_location (latitude, longitude)
        )
        """)

        # Prepare insert query
        insert_query = """
        INSERT INTO pincodes (
            circle_name, region_name, division_name, office_name,
            pincode, office_type, delivery_type, district,
            state_name, latitude, longitude
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Batch processing
        batch_size = 1000
        total_records = len(df)
        inserted_rows = 0
        
        print(f"\nStarting import of {total_records:,} valid records...")

        for i in range(0, total_records, batch_size):
            batch = df.iloc[i:i + batch_size]
            
            # Convert to list of tuples with proper data types
            records = []
            for _, row in batch.iterrows():
                records.append((
                    str(row['circle_name'])[:100],
                    str(row['region_name'])[:100],
                    str(row['division_name'])[:100],
                    str(row['office_name'])[:100],
                    str(row['pincode'])[:10],
                    str(row['office_type'])[:10],
                    str(row['delivery_type'])[:20],
                    str(row['district'])[:100],
                    str(row['state_name'])[:100],
                    float(row['latitude']),
                    float(row['longitude'])
                ))
            
            try:
                cursor.executemany(insert_query, records)
                conn.commit()
                inserted_rows += len(records)
                print(f"Processed {min(i + batch_size, total_records):,}/{total_records:,} records", end='\r')
            except Error as e:
                print(f"\n⚠️ Batch failed at row {i}: {e}")
                # Save failed batch for inspection
                batch.to_csv(f"failed_batch_{i}.csv", index=False)
                conn.rollback()
                continue

        # Final report
        duration = datetime.now() - start_time
        print(f"\n\n✅ Successfully imported {inserted_rows:,} out of {total_records:,} valid records")
        print(f"⏱️  Total time: {duration.total_seconds():.2f} seconds")
        if inserted_rows > 0:
            print(f"🚀 Speed: {inserted_rows/duration.total_seconds():.1f} records/second")
        
        # Show summary of invalid records
        if invalid_coords > 0:
            print(f"\n⚠️ Note: {invalid_coords:,} records were skipped due to invalid coordinates")
            print("Check the original CSV for rows with these issues:")

    except Error as e:
        print(f"\n❌ Database error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    csv_file = "pincode.csv"  # Update path if needed
    import_pincodes(csv_file)
import sqlite3
import pandas as pd
import os

def setup_database():
    print("="*50)
    print("Setting up SQLite Database")
    print("="*50)
    
    # Create database connection
    conn = sqlite3.connect('business_data.db')
    cursor = conn.cursor()
    
    dataset_path = 'dataset'
    
    # Load and store E-commerce data
    try:
        ecommerce_df = pd.read_csv(os.path.join(dataset_path, 'ecomerce_cleaned_data.csv'))
        ecommerce_df.to_sql('ecommerce', conn, if_exists='replace', index=False)
        print(f"✅ E-commerce data loaded: {len(ecommerce_df)} records")
    except Exception as e:
        print(f"❌ Error loading e-commerce: {e}")
    
    # Load and store Startup data
    try:
        startup_df = pd.read_csv(os.path.join(dataset_path, 'cleaned_startup.csv'))
        startup_df.to_sql('startup', conn, if_exists='replace', index=False)
        print(f"✅ Startup data loaded: {len(startup_df)} records")
    except Exception as e:
        print(f"❌ Error loading startup: {e}")
    
    # Load and store Region data
    try:
        region_df = pd.read_csv(os.path.join(dataset_path, 'cleaned_region_demand.csv'))
        region_df.to_sql('region', conn, if_exists='replace', index=False)
        print(f"✅ Region data loaded: {len(region_df)} records")
    except Exception as e:
        print(f"❌ Error loading region: {e}")
    
    # Verify tables
    print("\n📊 Database Tables Created:")
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
    for table in tables['name']:
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
        print(f"  📁 {table}: {count.iloc[0]['count']} records")
    
    conn.close()
    print("\n✅ Database setup complete!")
    print("="*50)

if __name__ == "__main__":
    setup_database()
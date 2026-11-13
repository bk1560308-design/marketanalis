import os
import pandas as pd

print("="*50)
print("Checking CSV files in dataset folder")
print("="*50)

dataset_path = 'dataset'

# List all files in dataset folder
if os.path.exists(dataset_path):
    print(f"\nFiles in {dataset_path}:")
    for file in os.listdir(dataset_path):
        print(f"  - {file}")
else:
    print(f"\n❌ Dataset folder not found: {dataset_path}")
    exit()

print("\n" + "="*50)
print("Checking each CSV file")
print("="*50)

# Check E-commerce CSV
ecommerce_files = [f for f in os.listdir(dataset_path) if 'ecomerce' in f.lower() or 'ecommerce' in f.lower()]
if ecommerce_files:
    file_path = os.path.join(dataset_path, ecommerce_files[0])
    print(f"\n✅ Found E-commerce file: {ecommerce_files[0]}")
    df = pd.read_csv(file_path)
    print(f"   Records: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   First 2 rows:\n{df.head(2)}")
else:
    print("\n❌ No e-commerce CSV file found")

# Check Startup CSV
startup_files = [f for f in os.listdir(dataset_path) if 'startup' in f.lower()]
if startup_files:
    file_path = os.path.join(dataset_path, startup_files[0])
    print(f"\n✅ Found Startup file: {startup_files[0]}")
    df = pd.read_csv(file_path)
    print(f"   Records: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   First 2 rows:\n{df.head(2)}")
else:
    print("\n❌ No startup CSV file found")

# Check Region CSV
region_files = [f for f in os.listdir(dataset_path) if 'region' in f.lower() or 'demand' in f.lower()]
if region_files:
    file_path = os.path.join(dataset_path, region_files[0])
    print(f"\n✅ Found Region file: {region_files[0]}")
    df = pd.read_csv(file_path)
    print(f"   Records: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"   First 2 rows:\n{df.head(2)}")
else:
    print("\n❌ No region CSV file found")
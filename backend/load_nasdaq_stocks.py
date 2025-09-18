#!/usr/bin/env python3
"""
Standalone script to populate Stock model with NASDAQ screener data
Run this from the backend directory after activating your virtual environment
"""

import os
import sys
import csv
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Now import Django models
from stocks.models import Stock


def load_stocks_from_csv(csv_file_path, clear_existing=False):
    """Load stocks from CSV file into the Stock model"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return
    
    # Clear existing stocks if requested
    if clear_existing:
        count = Stock.objects.count()
        Stock.objects.all().delete()
        print(f"🗑️  Cleared {count} existing stocks")
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    print(f"📂 Loading stocks from: {csv_file_path}")
    print("="*60)
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, 1):
                symbol = row['Symbol'].strip().upper()
                name = row['Name'].strip()
                
                # Skip empty rows
                if not symbol or not name:
                    continue
                
                try:
                    # Use get_or_create to avoid duplicates
                    stock, created = Stock.objects.get_or_create(
                        symbol=symbol,
                        defaults={'name': name}
                    )
                    
                    if created:
                        created_count += 1
                        print(f"✅ Created: {symbol} - {name}")
                    else:
                        # Update name if stock exists but name is different
                        if stock.name != name:
                            stock.name = name
                            stock.save()
                            updated_count += 1
                            print(f"🔄 Updated: {symbol} - {name}")
                
                except Exception as e:
                    error_count += 1
                    print(f"❌ Error processing {symbol}: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error reading CSV file: {str(e)}")
        return
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"✅ Stocks created: {created_count}")
    print(f"🔄 Stocks updated: {updated_count}")
    if error_count > 0:
        print(f"❌ Errors encountered: {error_count}")
    
    total_stocks = Stock.objects.count()
    print(f"📈 Total stocks in database: {total_stocks}")
    print("="*60)
    print("🎉 Stock loading completed!")


if __name__ == "__main__":
    # Path to CSV file (in project root)
    csv_file = backend_dir.parent / "nasdaq_screener_1756622606980.csv"
    
    # You can change this to True if you want to clear existing stocks first
    clear_existing = False
    
    load_stocks_from_csv(csv_file, clear_existing)

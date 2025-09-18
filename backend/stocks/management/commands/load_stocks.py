import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from stocks.models import Stock


class Command(BaseCommand):
    help = 'Load stocks from NASDAQ screener CSV file into the Stock model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='nasdaq_screener_1756622606980.csv',
            help='Path to the CSV file (relative to project root or absolute path)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing stocks before loading new ones'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        # If it's not an absolute path, assume it's in the project root
        if not os.path.isabs(csv_file):
            project_root = settings.BASE_DIR.parent  # Go up from backend/ to project root
            csv_file = os.path.join(project_root, csv_file)
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {csv_file}')
            )
            return
        
        # Clear existing stocks if requested
        if options['clear']:
            count = Stock.objects.count()
            Stock.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Cleared {count} existing stocks')
            )
        
        # Load stocks from CSV
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
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
                            self.stdout.write(f'Created: {symbol} - {name}')
                        else:
                            # Update name if stock exists but name is different
                            if stock.name != name:
                                stock.name = name
                                stock.save()
                                updated_count += 1
                                self.stdout.write(f'Updated: {symbol} - {name}')
                    
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'Error processing {symbol}: {str(e)}')
                        )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading CSV file: {str(e)}')
            )
            return
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed CSV file: {csv_file}')
        )
        self.stdout.write(f'Stocks created: {created_count}')
        self.stdout.write(f'Stocks updated: {updated_count}')
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Errors encountered: {error_count}')
            )
        
        total_stocks = Stock.objects.count()
        self.stdout.write(f'Total stocks in database: {total_stocks}')
        self.stdout.write('='*50)

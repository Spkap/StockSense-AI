"""Validate local configuration without printing secrets or contacting providers."""
from pathlib import Path
import sys
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
backend = dotenv_values(root / '.env')
frontend = dotenv_values(root / 'frontend/.env')
missing = []
for source, values, keys in [
    ('.env', backend, ['FIREWORKS_API_KEY', 'NEWSAPI_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']),
    ('frontend/.env', frontend, ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY', 'VITE_API_URL']),
]:
    for key in keys:
        value = (values.get(key) or '').strip()
        if not value or value.startswith('your_') or 'your-project' in value:
            missing.append(f'{source}: {key}')
for front, back in [('VITE_SUPABASE_URL', 'SUPABASE_URL'), ('VITE_SUPABASE_ANON_KEY', 'SUPABASE_ANON_KEY')]:
    if frontend.get(front) and backend.get(back) and frontend[front] != backend[back]:
        missing.append(f'frontend/.env: {front} must match {back}')
if missing:
    print('Configuration needed:\n' + '\n'.join(f'  - {item}' for item in missing))
    sys.exit(1)
if not backend.get('SUPABASE_SERVICE_KEY'):
    print('Note: background thesis monitoring needs SUPABASE_SERVICE_KEY.')
print('Required local configuration is present. Provider access and database schema still require verification.')

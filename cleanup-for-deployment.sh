#!/bin/bash
# StockSense-Agent Cleanup Script
# Run this to remove all files not needed for deployment

echo "🧹 Cleaning up StockSense-Agent repository for deployment..."

# Remove unused requirements files
echo "Removing unused requirements files..."
rm -f requirements.txt
rm -f requirements-frontend.txt
rm -f requirements.in
rm -f requirements-frontend.in
rm -f requirements-backend.in

# Remove conda environment files (not used in deployment)
echo "Removing conda environment files..."
rm -f environment.yml
rm -f environment-backend.yml
rm -f environment-frontend.yml
rm -f environment-prod.yml

# Remove development/test files (optional)
echo "Removing development files..."
rm -f pytest.ini
rm -rf .pytest_cache/

# Remove Python cache files
echo "Removing Python cache files..."
rm -rf tests/__pycache__/
rm -rf stocksense/__pycache__/
find . -name "*.pyc" -delete

# Remove sample data files (optional - uncomment if you want to remove)
# echo "Removing sample data files..."
# rm -f nasdaq_screener.csv
# rm -f stocksense.db

echo "✅ Cleanup complete!"
echo ""
echo "📁 Files kept for deployment:"
echo "✅ app.py                      (Streamlit frontend)"
echo "✅ render.yaml                 (Render config)"
echo "✅ requirements-backend.txt    (Backend dependencies)"
echo "✅ requirements-streamlit.txt  (Frontend dependencies)"
echo "✅ .streamlit/secrets.toml     (Frontend config)"
echo "✅ stocksense/                 (Backend code)"
echo "✅ DEPLOYMENT.md               (Instructions)"
echo "✅ readme.md                   (Documentation)"

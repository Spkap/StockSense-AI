# 🔄 CI/CD Status

## Build Status

[![Python Application CI](https://github.com/Spkap/StockSense-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Spkap/StockSense-AI/actions/workflows/ci.yml)

## Quick Setup Commands

### 1. **Choose Your Workflow**

```bash
# Use the simple workflow (recommended)
cp .github/workflows/ci-simple.yml .github/workflows/ci.yml
rm .github/workflows/ci-simple.yml

# OR use the comprehensive workflow (advanced)
rm .github/workflows/ci-simple.yml
```

### 2. **Configure Secrets in GitHub**

Go to: **Repository Settings > Secrets and Variables > Actions**

Add these secrets:

- `GOOGLE_API_KEY` - Your Google AI API key
- `NEWSAPI_KEY` - Your News API key

### 3. **Deploy CI**

```bash
git add .github/
git commit -m "Add GitHub Actions CI pipeline"
git push origin main
```

## 🎯 What This Achieves

✅ **Automated Testing** - Every push and PR runs full test suite  
✅ **Quality Assurance** - Code quality gates prevent broken code  
✅ **Fast Feedback** - Know immediately if changes break anything  
✅ **Professional Standards** - Industry-standard CI/CD practices

## 📊 Monitoring

- **View CI Status**: Go to repository **Actions** tab
- **Debug Failures**: Click on failed runs for detailed logs
- **Badge Status**: Shows current build status in README

---

_Your StockSense Agent is now enterprise-ready with automated CI/CD! 🚀_

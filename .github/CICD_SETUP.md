# GitHub Actions CI Setup Guide

## 🚀 Setting Up Continuous Integration for StockSense Agent

This guide walks you through setting up automated testing with GitHub Actions for your StockSense Agent project.

## 📁 Files Created

### 1. Main CI Workflow: `.github/workflows/ci.yml`

**Complete enterprise-grade CI pipeline with:**

- ✅ Unit testing
- ✅ Integration testing
- ✅ Code quality checks
- ✅ Security scanning
- ✅ Coverage reporting
- ✅ Multi-job pipeline

### 2. Simple CI Workflow: `.github/workflows/ci-simple.yml`

**Minimal CI pipeline that exactly matches your requirements:**

- ✅ Triggers on push/PR to main
- ✅ Python 3.10 setup
- ✅ Dependency installation
- ✅ Pytest execution
- ✅ Environment variable support

## 🔧 Setup Instructions

### Step 1: Choose Your Workflow

**Option A: Use Simple Workflow (Recommended for start)**

```bash
# Keep only the simple workflow
mv .github/workflows/ci-simple.yml .github/workflows/ci.yml
rm .github/workflows/ci-simple.yml
```

**Option B: Use Full-Featured Workflow**

```bash
# Keep the comprehensive workflow
rm .github/workflows/ci-simple.yml
# The main ci.yml is already in place
```

### Step 2: Configure GitHub Secrets

In your GitHub repository, go to **Settings > Secrets and Variables > Actions**

Add the following secrets:

#### Required Secrets:

- **`GOOGLE_API_KEY`**: Your Google AI API key for sentiment analysis
- **`NEWSAPI_KEY`**: Your NewsAPI key for fetching news headlines

#### How to Add Secrets:

1. Go to your GitHub repository
2. Click **Settings** tab
3. Navigate to **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Add each secret with the exact names above

### Step 3: Push to GitHub

```bash
# Add the workflow files
git add .github/

# Commit the changes
git commit -m "Add GitHub Actions CI workflow for automated testing"

# Push to main branch (this will trigger the first CI run)
git push origin main
```

## 🎯 What Happens After Setup

### Automatic Triggers:

- **Every push to main**: Full CI pipeline runs
- **Every pull request to main**: CI validation runs
- **Manual trigger**: Can be run manually from GitHub Actions tab

### Test Execution:

- **Unit Tests**: Tests individual tools (news, price data)
- **Integration Tests**: Tests API endpoints (requires server)
- **Smoke Tests**: Quick functionality validation

### CI Pipeline Results:

- ✅ **Green checkmark**: All tests passed
- ❌ **Red X**: Tests failed (blocks merging)
- 🟡 **Yellow circle**: Tests running

## 📊 Monitoring CI Results

### View Results:

1. Go to your GitHub repository
2. Click **Actions** tab
3. See all workflow runs and their status

### Debug Failed Tests:

1. Click on the failed workflow run
2. Click on the **Build and Test** job
3. Expand the failed step to see error details
4. Review logs and fix issues locally

## 🔄 Workflow Customization

### Modify Test Commands:

Edit the workflow file to change test execution:

```yaml
# Run specific test types
- name: Run tests
  run: |
    python run_tests.py unit  # Only unit tests
    # OR
    python run_tests.py smoke  # Only smoke tests
    # OR  
    pytest tests/test_tools.py -v  # Specific test file
```

### Add More Python Versions:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

### Add Different Operating Systems:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
runs-on: ${{ matrix.os }}
```

## ⚠️ Troubleshooting

### Common Issues:

#### 1. **Tests fail due to missing secrets**

- Ensure `GOOGLE_API_KEY` and `NEWSAPI_KEY` are set in repository secrets
- Check secret names match exactly (case-sensitive)

#### 2. **Dependencies installation fails**

- Verify `requirements.txt` includes all needed packages
- Check for conflicts between package versions

#### 3. **Tests timeout**

- Network-dependent tests may be slow
- Consider mocking external API calls for CI

#### 4. **Import errors**

- Ensure project structure is correct
- Check that `__init__.py` files exist in packages

### Debug Commands:

```bash
# Test locally before pushing
python run_tests.py smoke
python run_tests.py unit

# Check requirements file
pip install -r requirements.txt

# Validate workflow syntax
# Use GitHub CLI or online YAML validators
```

## 🚀 Next Steps

### 1. **Add Branch Protection Rules**

- Require CI to pass before merging
- Require pull request reviews

### 2. **Add Code Coverage**

- Use codecov.io integration
- Set coverage thresholds

### 3. **Add Deployment Pipeline**

- Deploy on successful CI
- Environment-specific deployments

### 4. **Add Notifications**

- Slack/Discord integration
- Email notifications on failures

## 📝 Best Practices

### 1. **Keep Secrets Secure**

- Never commit API keys to code
- Use environment variables consistently
- Rotate secrets regularly

### 2. **Fast Feedback**

- Run quick tests first
- Fail fast on syntax errors
- Parallel job execution

### 3. **Reliable Tests**

- Mock external dependencies when possible
- Use deterministic test data
- Handle network timeouts gracefully

### 4. **Clear Documentation**

- Comment workflow steps
- Document secret requirements
- Maintain setup instructions

---

Your StockSense Agent now has **professional-grade Continuous Integration** that will automatically validate every code change and ensure quality standards! 🎉

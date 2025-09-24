# 🚀 NBA Monte Carlo Betting Analyzer - Installation Instructions

## Prerequisites

Ensure you have these installed:
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js/npm** ([Download](https://nodejs.org/)) - Optional, for convenience scripts

## Installation & Setup

### Option 1: NPM Scripts (Recommended - Windows)
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nba-monte-carlo-betting-analyzer.git
   cd nba-monte-carlo-betting-analyzer
   ```

2. **One-time setup** (installs all dependencies):
   ```bash
   npm run setup:venv
   ```

3. **Start the application**:
   ```bash
   npm run dev
   ```

### Option 2: Direct Python Setup (Cross-Platform)
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nba-monte-carlo-betting-analyzer.git
   cd nba-monte-carlo-betting-analyzer
   ```

2. **Create virtual environment**:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install Flask numpy nba_api pandas openpyxl
   ```

4. **Start the application**:
   ```bash
   python app.py
   ```

### Option 3: System Python (If virtual env not available)
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/nba-monte-carlo-betting-analyzer.git
   cd nba-monte-carlo-betting-analyzer
   ```

2. **Install dependencies globally** (not recommended for production):
   ```bash
   pip install Flask numpy nba_api pandas openpyxl
   ```

3. **Start the application**:
   ```bash
   python app.py
   ```

## Accessing the Application

Once started, open your browser to:
```
http://127.0.0.1:8000
```

## Testing the Installation

To verify everything works:
```bash
# Test NBA API connectivity
python nba_league_analytics.py

# Or if using npm scripts
npm run test-api
```

**Expected output**: Should show NBA API connection success and league average offensive rating calculation.

## 🚨 Troubleshooting

### Common Issues

**"Cannot proceed without real NBA data"**
- The NBA API is temporarily unavailable
- Check your internet connection
- Try again in a few minutes (API rate limiting)
- **No fallback data** - this ensures you only get real statistics

**"Missing required columns"**
- NBA.com data format may have changed
- File an issue with specific error details
- Check if season data is available yet

**Monte Carlo simulation taking too long**
- Normal: 100,000 simulations take 10-30 seconds; High precision (1,000,000) can take 5× longer
- Check console for progress updates: "25,000 games simulated"
- If stuck, refresh page and try again

**Team dropdown not working**
- Try typing team name or abbreviation (LAL, GSW, etc.)
- Use arrow keys to navigate dropdown
- Click outside dropdown to close, then try again

**Port 8000 already in use**
- Another application is using the port
- Close other programs or change port in `app.py`
- Try: `netstat -ano | findstr :8000` to find the process

### AI Agent Setup Issues

**"ModuleNotFoundError: No module named 'nba_api'"**
```bash
# Install missing dependencies
pip install Flask numpy nba_api pandas
```

**"Python command not found"**
```bash
# Try alternative Python commands
python3 app.py
py app.py
python.exe app.py
```

**"Permission denied" or "Access denied"**
```bash
# On Windows, try:
python -m pip install --user Flask numpy nba_api pandas

# On macOS/Linux, try:
sudo pip3 install Flask numpy nba_api pandas
```

**"Port 8000 already in use"**
```bash
# Kill existing processes on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

## Quick Verification Script

Create a file called `verify_setup.py`:
```python
#!/usr/bin/env python3
"""
Verification script for NBA Monte Carlo Betting Analyzer
Run this to test if everything is properly installed
"""

def verify_dependencies():
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError:
        print("❌ Flask not installed")
        return False
    
    try:
        import numpy
        print(f"✅ NumPy {numpy.__version__}")
    except ImportError:
        print("❌ NumPy not installed")
        return False
    
    try:
        import nba_api
        print(f"✅ NBA API {nba_api.__version__}")
    except ImportError:
        print("❌ NBA API not installed")
        return False
    
    try:
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Pandas not installed")
        return False
    
    return True

def test_nba_api():
    try:
        from nba_api.stats.static import teams
        nba_teams = teams.get_teams()
        print(f"✅ NBA API working - found {len(nba_teams)} teams")
        return True
    except Exception as e:
        print(f"❌ NBA API test failed: {e}")
        return False

def test_four_factors():
    try:
        from nba_stats_fetcher import get_four_factors_team_stats
        # Test with a known team
        stats = get_four_factors_team_stats("Los Angeles Lakers", 2025)
        if stats and 'EFG_PCT' in stats:
            print("✅ Four Factors integration working")
            return True
        else:
            print("❌ Four Factors data incomplete")
            return False
    except Exception as e:
        print(f"❌ Four Factors test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏀 NBA Monte Carlo Betting Analyzer - Setup Verification")
    print("=" * 60)
    
    deps_ok = verify_dependencies()
    if deps_ok:
        print("\n🔗 Testing NBA API connectivity...")
        api_ok = test_nba_api()
        
        print("\n📊 Testing Four Factors integration...")
        ff_ok = test_four_factors()
        
        if api_ok and ff_ok:
            print("\n🎯 All systems ready! Run: python app.py")
        else:
            print("\n⚠️  Some features may not work properly")
    else:
        print("\n❌ Missing dependencies. Run: pip install Flask numpy nba_api pandas")
```

Run with: `python verify_setup.py`

## Getting Help

1. **Check the browser console** (F12 → Console tab)
2. **Look at terminal output** for detailed error messages
3. **Run verification script**: `python verify_setup.py`
4. **Try the test command**: `npm run test-api` or `python nba_league_analytics.py`

## 🛠️ Available Commands

| Command | Purpose |
|---------|---------|
| `npm run setup:venv` | Install Python environment and all dependencies |
| `npm run dev` | Start the web application (development mode) |
| `npm run test-api` | Test NBA API connectivity and data retrieval |
| `npm run clean` | Remove virtual environment (fresh start) |

## 📦 Dependencies

### Required Python Packages
```
Flask>=2.3.0          # Web framework
numpy>=1.24.0         # Numerical computations
nba_api>=1.1.14       # Official NBA.com API wrapper
pandas>=2.0.0         # Data manipulation and analysis
```

### Installation Commands by Environment

**For AI Agents/Automated Setup:**
```bash
# Ensure pip is available
python -m ensurepip --upgrade

# Install all dependencies
pip install Flask numpy nba_api pandas

# Verify installation
python -c "import flask, numpy, nba_api, pandas; print('All dependencies installed successfully')"
```

**For Development:**
```bash
# Create isolated environment
python -m venv .venv

# Activate environment (Windows)
.venv\Scripts\activate

# Activate environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install Flask numpy nba_api pandas
```

**Development Tools:**
```
Node.js/npm          # Build scripts (optional)
```

---

**Ready to simulate 100k or 1M games? Follow the steps above and start analyzing!** 🚀

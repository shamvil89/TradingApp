# HERFOO_TRADES - Complete User Guide

This comprehensive guide explains how to set up, configure, and use the HERFOO_TRADES trading bot with its modern web dashboard. Everything is explained in simple terms so you can control the bot's behavior without reading code.

## 🤖 What This Bot Does

### Core Trading Features
- **Single Position Trading**: Buys and sells exactly one stock at a time per running bot instance
- **Automated Decision Making**: Uses configurable rules to automatically buy low and sell high
- **Risk Management**: Built-in stop-loss and take-profit mechanisms
- **Market Hours Protection**: Refuses to place orders outside configured market hours
- **Real-time Monitoring**: Live price tracking and position management

### Advanced Capabilities
- **Multiple Quote Sources**: Tries public feeds (Yahoo Finance, NSE) first, falls back to Breeze API
- **Web Dashboard**: Modern browser-based interface for monitoring and control
- **API Integration**: RESTful APIs for external applications
- **Real-time Logs**: Live activity tracking and decision logging
- **State Persistence**: Remembers positions and profits across restarts

## 📁 Project Files Overview

### Configuration Files
- **`creds.config`**: Your ICICIdirect Breeze API credentials
- **`rules.config`**: All trading parameters and behavior settings
- **`stocksymbol.txt`**: Stock symbol mapping (format: `DISPLAY|BREEZE_CODE`)
- **`state.json`**: Current position, profits, and trading history (auto-generated)

### Core Programs
- **`server.py`**: FastAPI web server with dashboard and bot management
- **`trader.py`**: Main trading bot (can run standalone or via server)
- **`breeze_client.py`**: ICICIdirect Breeze API wrapper
- **`rules.py`**: Trading rules engine and decision logic

### Web Interface
- **`web/index.html`**: Modern dashboard interface
- **`dist/`**: Pre-built executable files for easy deployment

### Support Files
- **`archive/`**: Older scripts and historical logs
- **`logs/`**: Real-time API and trading logs
- **`requirements.txt`**: Python dependencies

## 🚀 Quick Setup Guide

### Option 1: Standalone Executable (Easiest)
1. **Use the pre-built executable**: `dist/HERFOO_TRADES_Server_Fixed.exe`
2. **Configure your settings** (see Configuration section below)
3. **Double-click the executable**
4. **Open your browser** to http://localhost:8000/web

### Option 2: Python Installation
1. **Install Python 3.11+**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure your settings**
4. **Start the server**:
   ```bash
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```
5. **Access dashboard**: http://localhost:8000/web

## ⚙️ Configuration Guide

### 1. API Credentials (`creds.config`)
Get these from your ICICIdirect Breeze account:
```json
{
  "api_key": "your_api_key_here",
  "api_secret": "your_api_secret_here", 
  "session_token": "your_session_token_here"
}
```

**Important**: Never share these credentials or commit them to version control!

### 2. Trading Symbol (`stocksymbol.txt`)
Format: `DISPLAY_SYMBOL|BREEZE_CODE`
```
herfoo|HERFOO
```

**Examples**:
- `RELIANCE|RELIANCE` - Reliance Industries
- `TCS|TCS` - Tata Consultancy Services  
- `herfoo|HERFOO` - Your custom symbol
- `NIFTY50|NIFTY50` - Index trading

### 3. Trading Rules (`rules.config`)
Complete configuration with explanations:

```json
{
  "exchange_code": "NSE",
  "quantity": 10,
  "buy_drop_pct": 0.0018,
  "buy_drop_abs": 0.9,
  "take_profit_pct": 0.0018,
  "take_profit_abs": 0.9,
  "stop_loss_pct": 0.01,
  "poll_interval_sec": 15,
  "quote_source": "breeze",
  "debug": false,
  "min_warmup_samples": 3,
  "buy_immediate_on_start": true,
  "buy_mode": "drop_from_high",
  "sma_window": 20,
  "sma_drop_pct": 0.003,
  "market_tz": "Asia/Kolkata",
  "market_open": "09:15",
  "market_close": "15:30",
  "market_buffer_min": 1,
  "show_day_chart": false
}
```

## 📊 Trading Rules Explained (Plain English)

### Core Trading Logic
- **Single Position Rule**: The bot can hold only one position at a time. It won't buy again until it has sold the current position.
- **Immediate First Buy (Optional)**: You can tell the bot to buy the first time it sees a price, so you don't wait for a pattern.
- **Buy on Price Drop**: The bot watches the recent highest price and buys if the price drops by either:
  - A percentage you set (`buy_drop_pct`), or
  - A fixed rupee amount you set (`buy_drop_abs`)
- **Buy Below Average (SMA) (Optional)**: Instead of recent high logic, you can choose to buy when price falls below its recent moving average by a small percentage.
- **Take Profit**: The bot will sell when either:
  - Your rupee profit per share reaches your target (`take_profit_abs`), or
  - Your percent profit reaches your target (`take_profit_pct`)
- **Stop Loss**: The bot sells if the loss reaches your percent limit (`stop_loss_pct`)
- **Re-entry Rule**: After a sell, if the price drops below your last sell price and you have no position, the bot can buy again immediately.
- **Market Hours Guard**: The bot will not place any orders when the market is closed.
- **Safe MARKET Orders**: Orders are sent as MARKET (no price field) to avoid exchange rejections.
- **Price Sources with Fallback**: The bot tries public feeds first (yfinance, then NSE) and uses Breeze quotes if those are unavailable.

## 🌐 Web Dashboard Guide

### Accessing the Dashboard
1. **Start the server** (see Quick Setup above)
2. **Open your browser** to http://localhost:8000/web
3. **Bookmark the page** for easy access

### Dashboard Features

#### Real-Time Monitoring Panel
- **Live Position**: Shows current holdings, average buy price, quantity, and unrealized P&L
- **Last Traded Price (LTP)**: Real-time stock price with automatic updates
- **Market Status**: Displays if market is open/closed with timezone conversion
- **Total P&L**: Cumulative profit/loss from all completed trades

#### Trading Controls
- **Start/Stop Bot Button**: Control the automated trading bot with one click
- **Flatten Position Button**: Manually sell current position immediately (emergency exit)
- **Live Status Indicator**: Shows if bot is running, stopped, or in error state

#### Configuration Management
- **Rules Editor**: Modify trading parameters in real-time without restarting
- **Symbol Manager**: Change trading symbol on the fly
- **Credentials Update**: Update API credentials (requires server restart)
- **Market Hours**: View and modify trading hours

#### Advanced Features
- **Live Activity Logs**: Real-time display of bot decisions and market data
- **API Logs Viewer**: Detailed logs of all API calls for debugging
- **State Inspector**: View current trading state and reset if needed
- **Chart Viewer**: Intraday price charts with technical indicators

### Using the Dashboard Effectively

#### Daily Workflow
1. **Morning Setup**: Check market status and ensure bot is running
2. **Monitor Activity**: Watch live logs for trading decisions
3. **Adjust Rules**: Modify parameters based on market conditions
4. **Evening Review**: Check total P&L and position status

#### Emergency Procedures
- **Stop Bot**: Use the stop button to halt all trading immediately
- **Flatten Position**: Use flatten button to exit current position at market price
- **Reset State**: Clear all positions and P&L (use with caution)

## 📈 Complete Configuration Reference

### Trading Parameters
- **`exchange_code`**: "NSE" - Which exchange to trade on
- **`quantity`**: 10 - Number of shares per order (start small!)

### Buy Triggers
- **`buy_immediate_on_start`**: true/false - Buy right away when bot starts
- **`buy_mode`**: "drop_from_high" or "below_sma" - Which buy strategy to use
- **`buy_drop_pct`**: 0.0018 - Percent drop from recent high to trigger buy (0.18%)
- **`buy_drop_abs`**: 0.9 - Rupee drop from recent high to trigger buy
- **`sma_window`**: 20 - Number of recent prices for moving average calculation
- **`sma_drop_pct`**: 0.003 - Percent below SMA to trigger buy (0.3%)

### Sell Triggers
- **`take_profit_abs`**: 0.9 - Rupees profit per share to sell (90 paise)
- **`take_profit_pct`**: 0.0018 - Percent profit to sell (0.18%)
- **`stop_loss_pct`**: 0.01 - Percent loss to sell (1%)

### System Settings
- **`poll_interval_sec`**: 15 - Seconds between price checks
- **`quote_source`**: "breeze" - Price data source ("breeze", "yf", or "auto")
- **`debug`**: false - Enable detailed logging
- **`min_warmup_samples`**: 3 - Price samples needed before trading starts

### Market Hours (India Time)
- **`market_tz`**: "Asia/Kolkata" - Timezone
- **`market_open`**: "09:15" - Market opening time
- **`market_close`**: "15:30" - Market closing time
- **`market_buffer_min`**: 1 - Minutes before close to stop new orders

### Advanced Options
- **`show_day_chart`**: false - Display intraday charts in dashboard

## 💰 How Profits Are Tracked

### P&L Calculation
- **Trade Profit**: Calculated as `(Sell Price - Average Buy Price) × Quantity`
- **Total P&L**: Cumulative profit/loss from all completed trades
- **Unrealized P&L**: Current paper profit/loss on open positions
- **Last Sell Price**: Stored to help with re-entry decisions

### State Persistence
- **`state.json`**: Automatically saves position, profits, and trading history
- **Survives Restarts**: Bot remembers everything when restarted
- **Manual Reset**: Use dashboard or API to clear state if needed

## 🔄 Running Multiple Symbols

### Single Symbol (Recommended)
- **One bot instance** per symbol for stability
- **Simple management** through web dashboard
- **Clear separation** of positions and P&L

### Multiple Symbols Setup
1. **Separate Instances**: Run one server per symbol
2. **Different Ports**: Use ports 8000, 8001, 8002, etc.
3. **Individual Configuration**: Each symbol has its own config files
4. **Staggered Starts**: Start bots 10-30 seconds apart to spread API usage

### Multi-Symbol Best Practices
- **Monitor Separately**: Use different browser tabs for each symbol
- **Independent Rules**: Customize parameters per symbol's volatility
- **Resource Management**: Ensure adequate system resources for multiple instances

## 🛠️ Running the Bot

### Option 1: Web Server Mode (Recommended)
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
**Benefits**:
- Full web dashboard access
- Real-time monitoring
- Easy configuration changes
- Bot management controls

### Option 2: Direct Trading Mode
```bash
python trader.py
```
**Benefits**:
- Minimal resource usage
- Simple console output
- Direct bot control

### Option 3: Standalone Executable
```
Double-click: dist/HERFOO_TRADES_Server_Fixed.exe
```
**Benefits**:
- No Python installation required
- Easy distribution
- One-click startup

## 🚨 Safety Guidelines

### Pre-Trading Checklist
- ✅ **Verify Credentials**: Test API connection with small quantity
- ✅ **Check Market Hours**: Ensure bot won't trade outside hours
- ✅ **Set Stop Loss**: Always configure stop-loss protection
- ✅ **Start Small**: Begin with minimal quantity (1-10 shares)
- ✅ **Monitor Initially**: Watch first few trades closely

### Risk Management
- **Position Size**: Never risk more than you can afford to lose
- **Stop Loss**: Always set appropriate stop-loss levels
- **Market Hours**: Bot automatically respects trading hours
- **Emergency Exit**: Know how to use the flatten button

### Security Best Practices
- **Credentials**: Never share API keys or commit to version control
- **Local Only**: Run on localhost for security
- **Regular Updates**: Keep API credentials current
- **Backup State**: Regularly backup `state.json` file

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Yahoo Finance Rate Limiting
**Problem**: `too many 429 error responses`
**Solution**: 
- Set `"quote_source": "breeze"` in `rules.config`
- Or wait for rate limit to reset

#### 2. Symbol Not Found
**Problem**: `possibly delisted; no price data found`
**Solution**:
- Verify symbol format in `stocksymbol.txt`: `DISPLAY|BREEZE_CODE`
- Check if symbol is traded on NSE
- Ensure Breeze code is correct

#### 3. Port Already in Use
**Problem**: `[WinError 10013] An attempt was made to access a socket`
**Solution**:
- Close other applications using port 8000
- Or change port in server command: `--port 8001`

#### 4. Runaway Processes
**Problem**: Multiple server processes running
**Solution**:
```bash
taskkill /f /im HERFOO_TRADES_Server.exe
```

#### 5. No Trading Activity
**Problem**: Bot not buying/selling
**Solutions**:
- Enable `"debug": true` to see decision logic
- Lower buy thresholds (`buy_drop_pct`, `buy_drop_abs`)
- Try `"buy_immediate_on_start": true`
- Check market hours configuration

#### 6. API Connection Issues
**Problem**: Breeze API failures
**Solutions**:
- Verify credentials in `creds.config`
- Check internet connection
- Ensure API account is active
- Try different quote source

### Debug Mode
Enable detailed logging:
```json
{
  "debug": true
}
```

This shows:
- Recent high prices and thresholds
- SMA calculations
- Buy/sell decision reasoning
- Market data quality

### Testing Server
Run comprehensive tests:
```bash
python test_server.py
```

## 📊 API Reference

### Core Endpoints
- **`GET /api/state`**: Current trading state and position
- **`GET /api/ltp`**: Last traded price for configured symbol
- **`GET /api/trader/status`**: Bot status (running/stopped/error)
- **`POST /api/trader/start`**: Start the trading bot
- **`POST /api/trader/stop`**: Stop the trading bot

### Management Endpoints
- **`GET /api/trader/logs`**: Bot activity logs
- **`POST /api/flatten`**: Manually sell current position
- **`GET /api/rules`**: Current trading rules
- **`POST /api/rules`**: Update trading rules
- **`GET /api/symbol`**: Current trading symbol info

### Advanced Endpoints
- **`GET /api/chart/day`**: Intraday price charts
- **`GET /api/logs/api`**: API call logs
- **`POST /api/status/reset`**: Reset trading state

## 🚀 Advanced Features

### Custom Strategies
The bot supports multiple buy strategies:
- **Drop from High**: Buy when price drops from recent peak
- **Below SMA**: Buy when price falls below moving average
- **Custom Logic**: Extend `rules.py` for advanced strategies

### Integration Options
- **External APIs**: Use REST endpoints for integration
- **Webhooks**: Add webhook support for notifications
- **Database**: Connect to external databases for logging
- **Monitoring**: Integrate with monitoring systems

### Performance Optimization
- **Polling Intervals**: Adjust `poll_interval_sec` for performance
- **Quote Sources**: Use `breeze` for fastest execution
- **Resource Usage**: Monitor system resources with multiple bots

## 📞 Support and Resources

### Getting Help
1. **Check Logs**: Review dashboard logs for error messages
2. **Enable Debug**: Use debug mode for detailed information
3. **Test Configuration**: Use `test_server.py` to verify setup
4. **Review Documentation**: Check README.md for additional details

### Best Practices
- **Start Conservative**: Begin with small quantities and wide stops
- **Monitor Closely**: Watch bot behavior during initial runs
- **Regular Updates**: Keep configuration optimized for market conditions
- **Backup Data**: Regularly backup state and configuration files

### Future Enhancements
- **Machine Learning**: Add ML models for improved decision making
- **Multi-Exchange**: Support for multiple exchanges
- **Advanced Analytics**: Enhanced reporting and analytics
- **Mobile App**: Mobile dashboard for on-the-go monitoring

---

**Remember**: This is a sophisticated trading tool. Always test thoroughly with small quantities before deploying with significant capital. Market trading involves risk, and past performance does not guarantee future results.

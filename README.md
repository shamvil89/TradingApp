# HERFOO_TRADES - Breeze API Single-Position Trading Bot

A sophisticated trading bot that buys one stock at a time (single position) using ICICIdirect Breeze API, based on configurable rules for buying low and selling high. Features a modern web dashboard for real-time monitoring and control.

## 🚀 Quick Start

### Option 1: Standalone Executable (Recommended)
1. **Download**: Use the pre-built executable `dist/HERFOO_TRADES_Server_Fixed.exe`
2. **Configure**: Edit `creds.config`, `rules.config`, and `stocksymbol.txt`
3. **Run**: Double-click the executable
4. **Access**: Open http://localhost:8000/web in your browser

### Option 2: Python Installation
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure**: Set up your credentials and trading rules
3. **Run server**:
   ```bash
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```
4. **Access dashboard**: http://localhost:8000/web

## 📋 Prerequisites

- **ICICIdirect Breeze API Account**: Get your API credentials from ICICIdirect
- **Python 3.11+** (if not using executable)
- **Windows 10/11** (for executable version)

## ⚙️ Configuration

### 1. API Credentials (`creds.config`)
```json
{
  "api_key": "your_api_key_here",
  "api_secret": "your_api_secret_here", 
  "session_token": "your_session_token_here"
}
```

### 2. Trading Rules (`rules.config`)
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

**Key Parameters:**
- `quantity`: Number of shares per trade
- `buy_drop_pct`: Percentage drop to trigger buy (0.0018 = 0.18%)
- `take_profit_pct`: Profit percentage to sell (0.0018 = 0.18%)
- `stop_loss_pct`: Stop loss percentage (0.01 = 1%)
- `quote_source`: "breeze" (recommended) or "yf" (Yahoo Finance)
- `buy_immediate_on_start`: Whether to buy immediately when starting

### 3. Stock Symbol (`stocksymbol.txt`)
Format: `DISPLAY_SYMBOL|BREEZE_CODE`
```
herfoo|HERFOO
```

**Examples:**
- `RELIANCE|RELIANCE`
- `TCS|TCS`
- `herfoo|HERFOO`

## 🌐 Web Dashboard

Access the dashboard at **http://localhost:8000/web** for:

### Real-Time Monitoring
- **Live Position**: Current holdings, average price, quantity
- **Last Traded Price (LTP)**: Real-time stock price
- **P&L Tracking**: Current and total profit/loss
- **Market Status**: Open/closed with timezone conversion

### Trading Controls
- **Start/Stop Bot**: Control the automated trading bot
- **Flatten Position**: Manual sell button for immediate position closure
- **Live Logs**: Real-time bot activity and decision logs

### Configuration Management
- **Rules Editor**: Modify trading parameters in real-time
- **Symbol Management**: Change trading symbol
- **Credentials**: Update API credentials (restart required)

### Advanced Features
- **Market Data Charts**: Intraday price charts with technical indicators
- **API Logs**: Detailed API call logs for debugging
- **State Management**: View and reset trading state
- **Time Zone Conversion**: Market hours in different timezones

## 🔧 Running the Bot

### Direct Trading Mode
```bash
python trader.py
```
Runs the trading bot directly without web interface.

### Web Server Mode (Recommended)
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
Starts web server with dashboard and bot management.

### Building Executable
```bash
python build_executable_fixed.py
```
Creates standalone executable in `dist/` folder.

## 📊 API Endpoints

The server provides RESTful APIs for integration:

- `GET /api/state` - Current trading state and position
- `GET /api/ltp` - Last traded price for configured symbol
- `GET /api/trader/status` - Bot status (running/stopped)
- `POST /api/trader/start` - Start the trading bot
- `POST /api/trader/stop` - Stop the trading bot
- `GET /api/trader/logs` - Bot activity logs
- `POST /api/flatten` - Manually sell current position
- `GET /api/rules` - Current trading rules
- `POST /api/rules` - Update trading rules
- `GET /api/symbol` - Current trading symbol info

## 🛠️ Troubleshooting

### Common Issues

#### 1. Yahoo Finance Rate Limiting
**Error**: `too many 429 error responses`
**Solution**: Set `"quote_source": "breeze"` in `rules.config`

#### 2. Symbol Not Found
**Error**: `possibly delisted; no price data found`
**Solution**: Verify symbol format in `stocksymbol.txt` as `DISPLAY|BREEZE_CODE`

#### 3. Port Already in Use
**Error**: `[WinError 10013] An attempt was made to access a socket`
**Solution**: Close other applications using port 8000 or change port

#### 4. Runaway Processes
**Problem**: Multiple server processes running
**Solution**: Use `taskkill /f /im HERFOO_TRADES_Server.exe` to stop all

#### 5. API Connection Issues
**Error**: Breeze API connection failures
**Solution**: Verify credentials in `creds.config` and check internet connection

### Debug Mode
Enable debug mode in `rules.config`:
```json
"debug": true
```
This provides detailed logging of trading decisions and market data.

### Testing Server
```bash
python test_server.py
```
Runs comprehensive tests to verify server functionality.

## 📁 Project Structure

```
HERFOO_TRADES/
├── server.py              # FastAPI web server
├── trader.py              # Main trading bot
├── breeze_client.py       # Breeze API wrapper
├── rules.py               # Trading rules engine
├── state.py               # State management
├── quote_router.py        # Price data routing
├── symbols.py             # Symbol management
├── web/                   # Web dashboard files
├── dist/                  # Built executables
├── archive/               # Archived scripts
├── logs/                  # Log files
├── creds.config           # API credentials
├── rules.config           # Trading rules
├── stocksymbol.txt        # Trading symbol
└── requirements.txt       # Python dependencies
```

## 🔒 Security Notes

- **Credentials**: Never commit `creds.config` to version control
- **API Keys**: Rotate API keys regularly
- **Network**: Run on localhost for security
- **Firewall**: Consider firewall rules for production use

## 📈 Trading Strategy

The bot implements a **mean reversion strategy**:

1. **Entry**: Buys when price drops by configured percentage from recent high
2. **Exit**: Sells when price rises by configured percentage (profit target)
3. **Stop Loss**: Sells if price drops by configured percentage (risk management)
4. **Re-entry**: After selling, waits for new entry conditions

### Market Hours Protection
- Only trades during configured market hours
- Respects timezone settings
- Prevents after-hours trading

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review server logs in the web dashboard
3. Enable debug mode for detailed logging
4. Verify all configuration files are properly formatted

## 📝 License

This project is for educational and personal use. Please ensure compliance with your broker's terms of service and local trading regulations.

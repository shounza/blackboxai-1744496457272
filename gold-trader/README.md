# GOLD Auto Trader

An automated trading system specifically designed for trading GOLD (XAUUSD) using the PuPrime broker. The system implements advanced technical analysis and risk management strategies to maximize trading profits while maintaining strict risk controls.

## Features

- **Automated GOLD Trading**
  - Real-time market data analysis
  - Advanced technical indicators
  - Customizable trading strategies
  - Automated order execution
  - Risk management system

- **Technical Analysis**
  - Moving Averages (EMA, SMA)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Support and Resistance levels

- **Risk Management**
  - Position sizing
  - Stop-loss implementation
  - Take-profit targets
  - Maximum drawdown limits
  - Daily and weekly loss limits

- **User Interface**
  - Modern, responsive dashboard
  - Real-time performance monitoring
  - Trade history tracking
  - Account statistics
  - Strategy management

## Prerequisites

- Python 3.8+
- Node.js 14+
- PuPrime trading account with API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gold-trader.git
cd gold-trader
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```env
PORT=5000
DEBUG=True
DATABASE_URL=sqlite:///gold_trader.db
PUPRIME_API_KEY=your_api_key_here
PUPRIME_API_SECRET=your_api_secret_here
JWT_SECRET_KEY=your_jwt_secret_here
```

## Project Structure

```
gold-trader/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py             # Configuration settings
│   ├── logger.py             # Logging configuration
│   ├── trading_engine.py     # Trading engine core
│   ├── broker/              
│   │   └── puprime_api.py    # PuPrime API integration
│   ├── database/
│   │   ├── models.py         # Database models
│   │   └── database_setup.py # Database configuration
│   ├── routes/
│   │   ├── auth_routes.py    # Authentication endpoints
│   │   └── trade_routes.py   # Trading endpoints
│   ├── strategies/
│   │   └── gold_strategy.py  # Trading strategies
│   └── utils/
│       └── indicators.py     # Technical indicators
├── frontend/
│   ├── index.html           # Dashboard page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── css/
│   └── js/
│       ├── dashboard.js    # Dashboard functionality
│       ├── login.js       # Login handling
│       └── register.js    # Registration handling
└── tests/                 # Test files
```

## Usage

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Access the web interface:
Open `frontend/login.html` in your web browser to access the login page.

3. Register a new account:
- Click "Create new account"
- Fill in your details
- Add your PuPrime API credentials

4. Configure trading parameters:
- Set position size
- Configure risk management settings
- Choose technical indicator parameters

5. Start trading:
- Click "Start Trading" on the dashboard
- Monitor performance in real-time
- View trade history and statistics

## Trading Strategy

The system implements a multi-factor trading strategy for GOLD:

1. **Trend Analysis**
   - Multiple timeframe analysis
   - Moving average crossovers
   - Trend strength confirmation

2. **Entry Conditions**
   - Support/Resistance levels
   - Technical indicator confluence
   - Volume confirmation

3. **Exit Conditions**
   - Take profit targets
   - Trailing stop-loss
   - Technical indicator divergence

4. **Risk Management**
   - Position sizing based on account balance
   - Maximum drawdown limits
   - Daily/Weekly loss limits

## Security

- JWT authentication
- API key encryption
- Password hashing
- Rate limiting
- Input validation
- Error logging

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

Trading GOLD or any financial instrument carries significant risks. This software is for educational purposes only and should not be considered financial advice. Always conduct your own research and risk assessment before trading.

## Support

For support, please open an issue in the GitHub repository or contact the development team.

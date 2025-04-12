import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from logger import logger, log_error

class TechnicalIndicators:
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with price data DataFrame
        
        Args:
            data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        self.data = data
        self.validate_data()

    def validate_data(self):
        """Validate input data has required columns"""
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    def calculate_ema(self, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        Args:
            period: EMA period
            column: Column to calculate EMA on
        """
        try:
            ema = self.data[column].ewm(span=period, adjust=False).mean()
            logger.debug(f"Calculated EMA{period} successfully")
            return ema
        except Exception as e:
            log_error("EMA_CALCULATION_ERROR", str(e), period=period)
            raise

    def calculate_sma(self, period: int, column: str = 'close') -> pd.Series:
        """
        Calculate Simple Moving Average
        
        Args:
            period: SMA period
            column: Column to calculate SMA on
        """
        try:
            sma = self.data[column].rolling(window=period).mean()
            logger.debug(f"Calculated SMA{period} successfully")
            return sma
        except Exception as e:
            log_error("SMA_CALCULATION_ERROR", str(e), period=period)
            raise

    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index
        
        Args:
            period: RSI period
        """
        try:
            delta = self.data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            logger.debug(f"Calculated RSI{period} successfully")
            return rsi
        except Exception as e:
            log_error("RSI_CALCULATION_ERROR", str(e), period=period)
            raise

    def calculate_macd(self, fast_period: int = 12, slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
        
        Returns:
            Tuple containing MACD line, signal line, and histogram
        """
        try:
            fast_ema = self.calculate_ema(fast_period)
            slow_ema = self.calculate_ema(slow_period)
            
            macd_line = fast_ema - slow_ema
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            histogram = macd_line - signal_line
            
            logger.debug("Calculated MACD successfully")
            return macd_line, signal_line, histogram
        except Exception as e:
            log_error("MACD_CALCULATION_ERROR", str(e))
            raise

    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands
        
        Args:
            period: Moving average period
            std_dev: Number of standard deviations
        
        Returns:
            Tuple containing upper band, middle band, and lower band
        """
        try:
            middle_band = self.calculate_sma(period)
            rolling_std = self.data['close'].rolling(window=period).std()
            
            upper_band = middle_band + (rolling_std * std_dev)
            lower_band = middle_band - (rolling_std * std_dev)
            
            logger.debug("Calculated Bollinger Bands successfully")
            return upper_band, middle_band, lower_band
        except Exception as e:
            log_error("BOLLINGER_BANDS_ERROR", str(e))
            raise

    def calculate_support_resistance(self, window: int = 20, threshold: float = 0.02) -> Tuple[List[float], List[float]]:
        """
        Calculate Support and Resistance levels using price action
        
        Args:
            window: Lookback period for identifying levels
            threshold: Minimum price difference threshold
        
        Returns:
            Tuple containing lists of support and resistance levels
        """
        try:
            highs = self.data['high'].rolling(window=window, center=True).max()
            lows = self.data['low'].rolling(window=window, center=True).min()
            
            resistance_levels = []
            support_levels = []
            
            # Identify resistance levels
            for i in range(window, len(highs) - window):
                if highs[i] == highs[i-window:i+window].max():
                    if not any(abs(level - highs[i]) / highs[i] < threshold for level in resistance_levels):
                        resistance_levels.append(highs[i])
            
            # Identify support levels
            for i in range(window, len(lows) - window):
                if lows[i] == lows[i-window:i+window].min():
                    if not any(abs(level - lows[i]) / lows[i] < threshold for level in support_levels):
                        support_levels.append(lows[i])
            
            logger.debug("Calculated Support/Resistance levels successfully")
            return support_levels, resistance_levels
        except Exception as e:
            log_error("SUPPORT_RESISTANCE_ERROR", str(e))
            raise

    def calculate_atr(self, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range
        
        Args:
            period: ATR period
        """
        try:
            high_low = self.data['high'] - self.data['low']
            high_close = abs(self.data['high'] - self.data['close'].shift())
            low_close = abs(self.data['low'] - self.data['close'].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            logger.debug(f"Calculated ATR{period} successfully")
            return atr
        except Exception as e:
            log_error("ATR_CALCULATION_ERROR", str(e))
            raise

    def get_all_indicators(self, config: Dict) -> Dict[str, pd.Series]:
        """
        Calculate all technical indicators based on configuration
        
        Args:
            config: Dictionary containing indicator parameters
        
        Returns:
            Dictionary containing all calculated indicators
        """
        try:
            indicators = {}
            
            # Calculate EMAs
            if 'ema' in config:
                for period in config['ema']:
                    indicators[f'ema_{period}'] = self.calculate_ema(period)
            
            # Calculate RSI
            if 'rsi' in config:
                indicators['rsi'] = self.calculate_rsi(config['rsi'])
            
            # Calculate MACD
            if 'macd' in config:
                macd_line, signal_line, histogram = self.calculate_macd(
                    config['macd'].get('fast', 12),
                    config['macd'].get('slow', 26),
                    config['macd'].get('signal', 9)
                )
                indicators.update({
                    'macd_line': macd_line,
                    'macd_signal': signal_line,
                    'macd_histogram': histogram
                })
            
            # Calculate Bollinger Bands
            if 'bollinger' in config:
                upper, middle, lower = self.calculate_bollinger_bands(
                    config['bollinger'].get('period', 20),
                    config['bollinger'].get('std_dev', 2.0)
                )
                indicators.update({
                    'bb_upper': upper,
                    'bb_middle': middle,
                    'bb_lower': lower
                })
            
            # Calculate ATR
            if 'atr' in config:
                indicators['atr'] = self.calculate_atr(config['atr'])
            
            logger.info("Successfully calculated all technical indicators")
            return indicators
            
        except Exception as e:
            log_error("INDICATOR_CALCULATION_ERROR", str(e))
            raise

# Example usage:
"""
# Create sample data
data = pd.DataFrame({
    'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='H'),
    'open': np.random.randn(100).cumsum() + 1000,
    'high': np.random.randn(100).cumsum() + 1002,
    'low': np.random.randn(100).cumsum() + 998,
    'close': np.random.randn(100).cumsum() + 1000,
    'volume': np.random.randint(1000, 5000, 100)
})

# Initialize indicators
indicators = TechnicalIndicators(data)

# Calculate various indicators
rsi = indicators.calculate_rsi()
macd_line, signal_line, histogram = indicators.calculate_macd()
upper_band, middle_band, lower_band = indicators.calculate_bollinger_bands()

# Calculate all indicators with custom configuration
config = {
    'ema': [9, 21],
    'rsi': 14,
    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
    'bollinger': {'period': 20, 'std_dev': 2.0},
    'atr': 14
}

all_indicators = indicators.get_all_indicators(config)
"""

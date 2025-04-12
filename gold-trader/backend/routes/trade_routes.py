from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from database.database_setup import get_db_session
from database.models import Trade, Strategy, PerformanceMetrics
from broker.puprime_api import PuPrimeAPI
from trading_engine import TradingEngine
from routes.auth_routes import token_required
from config import Config
from logger import logger, log_error

trade_bp = Blueprint('trade', __name__)
trading_engine = TradingEngine()
broker = PuPrimeAPI()

@trade_bp.route('/start', methods=['POST'])
@token_required
def start_trading(current_user):
    """Start the trading engine"""
    try:
        if not current_user.api_key or not current_user.api_secret:
            return jsonify({'message': 'API credentials not configured'}), 400
            
        trading_engine.start()
        logger.info(f"Trading started by user: {current_user.username}")
        return jsonify({'message': 'Trading started successfully'}), 200
        
    except Exception as e:
        log_error("TRADING_START_ERROR", str(e))
        return jsonify({'message': 'Failed to start trading'}), 500

@trade_bp.route('/stop', methods=['POST'])
@token_required
def stop_trading(current_user):
    """Stop the trading engine"""
    try:
        trading_engine.stop()
        logger.info(f"Trading stopped by user: {current_user.username}")
        return jsonify({'message': 'Trading stopped successfully'}), 200
        
    except Exception as e:
        log_error("TRADING_STOP_ERROR", str(e))
        return jsonify({'message': 'Failed to stop trading'}), 500

@trade_bp.route('/account', methods=['GET'])
@token_required
def get_account_info(current_user):
    """Get account information and current status"""
    try:
        # Get account info from broker
        account_info = broker.get_account_info()
        
        # Get today's performance metrics
        with get_db_session() as session:
            today = datetime.utcnow().date()
            metrics = session.query(PerformanceMetrics).filter(
                PerformanceMetrics.date == today
            ).first()
            
            response = {
                'balance': float(account_info.get('balance', 0)),
                'equity': float(account_info.get('equity', 0)),
                'margin': float(account_info.get('margin', 0)),
                'free_margin': float(account_info.get('free_margin', 0)),
                'margin_level': float(account_info.get('margin_level', 0)),
                'profit_loss': float(metrics.total_profit_loss if metrics else 0),
                'win_rate': float(metrics.win_rate if metrics else 0),
                'open_trades': len(broker.get_open_positions())
            }
            
            return jsonify(response), 200
            
    except Exception as e:
        log_error("ACCOUNT_INFO_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch account information'}), 500

@trade_bp.route('/positions', methods=['GET'])
@token_required
def get_open_positions(current_user):
    """Get all open positions"""
    try:
        positions = broker.get_open_positions()
        return jsonify(positions), 200
        
    except Exception as e:
        log_error("POSITIONS_FETCH_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch open positions'}), 500

@trade_bp.route('/recent', methods=['GET'])
@token_required
def get_recent_trades(current_user):
    """Get recent trade history"""
    try:
        with get_db_session() as session:
            trades = session.query(Trade).filter_by(
                user_id=current_user.id
            ).order_by(
                Trade.entry_time.desc()
            ).limit(20).all()
            
            trade_list = [{
                'id': trade.id,
                'symbol': trade.symbol,
                'type': trade.order_type.value,
                'status': trade.status.value,
                'entry_price': float(trade.entry_price),
                'exit_price': float(trade.exit_price) if trade.exit_price else None,
                'quantity': float(trade.quantity),
                'profit_loss': float(trade.profit_loss) if trade.profit_loss else None,
                'entry_time': trade.entry_time.isoformat(),
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None
            } for trade in trades]
            
            return jsonify(trade_list), 200
            
    except Exception as e:
        log_error("TRADE_HISTORY_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch trade history'}), 500

@trade_bp.route('/performance', methods=['GET'])
@token_required
def get_performance_data(current_user):
    """Get trading performance data"""
    try:
        # Get date range from query parameters
        days = int(request.args.get('days', 30))
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        with get_db_session() as session:
            metrics = session.query(PerformanceMetrics).filter(
                PerformanceMetrics.user_id == current_user.id,
                PerformanceMetrics.date >= start_date,
                PerformanceMetrics.date <= end_date
            ).order_by(PerformanceMetrics.date).all()
            
            performance_data = {
                'dates': [m.date.isoformat() for m in metrics],
                'total_profit_loss': [float(m.total_profit_loss) for m in metrics],
                'win_rate': [float(m.win_rate) for m in metrics],
                'profit_factor': [float(m.profit_factor) for m in metrics],
                'max_drawdown': [float(m.max_drawdown) for m in metrics],
                'sharpe_ratio': [float(m.sharpe_ratio) for m in metrics],
                'sortino_ratio': [float(m.sortino_ratio) for m in metrics]
            }
            
            return jsonify(performance_data), 200
            
    except Exception as e:
        log_error("PERFORMANCE_DATA_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch performance data'}), 500

@trade_bp.route('/strategies', methods=['GET'])
@token_required
def get_strategies(current_user):
    """Get all trading strategies"""
    try:
        with get_db_session() as session:
            strategies = session.query(Strategy).filter_by(
                user_id=current_user.id
            ).all()
            
            strategy_list = [{
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'symbol': strategy.symbol,
                'timeframe': strategy.timeframe,
                'position_size': float(strategy.position_size),
                'stop_loss_percent': float(strategy.stop_loss_percent),
                'take_profit_percent': float(strategy.take_profit_percent),
                'max_daily_loss': float(strategy.max_daily_loss),
                'is_active': strategy.is_active,
                'created_at': strategy.created_at.isoformat()
            } for strategy in strategies]
            
            return jsonify(strategy_list), 200
            
    except Exception as e:
        log_error("STRATEGY_FETCH_ERROR", str(e))
        return jsonify({'message': 'Failed to fetch strategies'}), 500

@trade_bp.route('/strategies', methods=['POST'])
@token_required
def create_strategy(current_user):
    """Create a new trading strategy"""
    try:
        data = request.get_json()
        
        with get_db_session() as session:
            strategy = Strategy(
                user_id=current_user.id,
                name=data['name'],
                description=data.get('description'),
                symbol=data.get('symbol', 'XAUUSD'),
                timeframe=data.get('timeframe', '1h'),
                position_size=data['position_size'],
                stop_loss_percent=data['stop_loss_percent'],
                take_profit_percent=data['take_profit_percent'],
                max_daily_loss=data['max_daily_loss'],
                is_active=True
            )
            
            session.add(strategy)
            session.commit()
            
            # Add strategy to trading engine
            trading_engine.add_strategy(data)
            
            logger.info(f"New strategy created: {data['name']}")
            
            return jsonify({
                'message': 'Strategy created successfully',
                'strategy_id': strategy.id
            }), 201
            
    except Exception as e:
        log_error("STRATEGY_CREATE_ERROR", str(e))
        return jsonify({'message': 'Failed to create strategy'}), 500

@trade_bp.route('/strategies/<int:strategy_id>', methods=['PUT'])
@token_required
def update_strategy(current_user, strategy_id):
    """Update an existing trading strategy"""
    try:
        data = request.get_json()
        
        with get_db_session() as session:
            strategy = session.query(Strategy).filter_by(
                id=strategy_id,
                user_id=current_user.id
            ).first()
            
            if not strategy:
                return jsonify({'message': 'Strategy not found'}), 404
                
            # Update fields
            for key, value in data.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
                    
            session.commit()
            
            logger.info(f"Strategy updated: {strategy.name}")
            
            return jsonify({'message': 'Strategy updated successfully'}), 200
            
    except Exception as e:
        log_error("STRATEGY_UPDATE_ERROR", str(e))
        return jsonify({'message': 'Failed to update strategy'}), 500

@trade_bp.route('/strategies/<int:strategy_id>', methods=['DELETE'])
@token_required
def delete_strategy(current_user, strategy_id):
    """Delete a trading strategy"""
    try:
        with get_db_session() as session:
            strategy = session.query(Strategy).filter_by(
                id=strategy_id,
                user_id=current_user.id
            ).first()
            
            if not strategy:
                return jsonify({'message': 'Strategy not found'}), 404
                
            # Remove strategy from trading engine
            trading_engine.remove_strategy(strategy_id)
            
            # Mark strategy as inactive
            strategy.is_active = False
            session.commit()
            
            logger.info(f"Strategy deleted: {strategy.name}")
            
            return jsonify({'message': 'Strategy deleted successfully'}), 200
            
    except Exception as e:
        log_error("STRATEGY_DELETE_ERROR", str(e))
        return jsonify({'message': 'Failed to delete strategy'}), 500

# Error handlers
@trade_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request'}), 400

@trade_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({'message': 'Unauthorized'}), 401

@trade_bp.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

@trade_bp.errorhandler(500)
def internal_error(error):
    log_error("INTERNAL_SERVER_ERROR", str(error))
    return jsonify({'message': 'Internal server error'}), 500

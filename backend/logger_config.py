"""
Advanced Logging Configuration for WolfTrace Backend
Provides structured logging with rotation, filtering, and multiple handlers
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
from functools import wraps
import time

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',        # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if sys.stdout.isatty():  # Only colorize if terminal supports it
            levelname = record.levelname
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class RequestFormatter(logging.Formatter):
    """Specialized formatter for HTTP requests"""
    
    def format(self, record):
        # Extract request information
        method = getattr(record, 'method', 'UNKNOWN')
        path = getattr(record, 'path', 'UNKNOWN')
        status = getattr(record, 'status', 'UNKNOWN')
        duration = getattr(record, 'duration', 0)
        ip = getattr(record, 'ip', 'UNKNOWN')
        
        # Format timestamp
        record.asctime = self.formatTime(record, self.datefmt)
        
        return (
            f"{record.asctime} | {ip} | {method:6s} {path:40s} | "
            f"Status: {str(status):>3s} | Duration: {duration:6.3f}s"
        )


def setup_logging(
    log_dir: Optional[str] = None,
    log_level: str = None,
    enable_json: bool = False,
    enable_access_log: bool = True
) -> logging.Logger:
    """
    Configure comprehensive logging system for WolfTrace
    
    Args:
        log_dir: Directory for log files (default: logs/ in backend directory)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR) - from env or default INFO
        enable_json: Enable JSON structured logging
        enable_access_log: Enable separate access log for HTTP requests
    
    Returns:
        Configured root logger
    """
    # Determine log directory
    if log_dir is None:
        backend_dir = Path(__file__).resolve().parent
        log_dir = str(backend_dir / 'logs')
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get log level from environment or use default
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    level = getattr(logging, log_level, logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # Application log file with rotation
    app_log_file = log_path / 'wolftrace.log'
    app_handler = logging.handlers.RotatingFileHandler(
        filename=str(app_log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.DEBUG)  # Always log everything to file
    
    if enable_json:
        app_formatter = StructuredFormatter()
    else:
        app_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    app_handler.setFormatter(app_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log file (only errors and above)
    error_log_file = log_path / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(error_log_file),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)s:%(funcName)s:%(lineno)d | %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Access log for HTTP requests (if enabled)
    if enable_access_log:
        access_log_file = log_path / 'access.log'
        access_handler = logging.handlers.RotatingFileHandler(
            filename=str(access_log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_formatter = RequestFormatter(
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        access_handler.setFormatter(access_formatter)
        
        # Create separate logger for access logs
        access_logger = logging.getLogger('wolftrace.access')
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
    
        # Set levels for third-party loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask noise
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Create application logger
    app_logger = logging.getLogger('wolftrace')
    app_logger.info(f"Logging initialized - Level: {log_level}, Directory: {log_dir}")
    
    return app_logger


def log_performance(operation_name: str):
    """Decorator to log operation performance"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('wolftrace.performance')
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Performance: {operation_name} completed in {duration:.3f}s",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'function': f.__name__
                    }
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Performance: {operation_name} failed after {duration:.3f}s - {str(e)}",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'function': f.__name__,
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance with the wolftrace prefix"""
    if name:
        logger_name = f'wolftrace.{name}'
    else:
        logger_name = 'wolftrace'
    
    return logging.getLogger(logger_name)


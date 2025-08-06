"""
CineFusion Logging Configuration
Comprehensive logging system with file rotation, structured logging, and monitoring
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

from config import config


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""

    def format(self, record: logging.LogRecord) -> str:
        # Clean level name by removing any color codes
        clean_level = record.levelname
        if '\033[' in clean_level:
            # Remove ANSI color codes
            import re
            clean_level = re.sub(r'\033\[[0-9;]*m', '', clean_level)

        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': clean_level,  # Clean level name without colors
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_ip'):
            log_entry['user_ip'] = record.user_ip
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add stack trace if available
        if record.stack_info:
            log_entry['stack_trace'] = record.stack_info

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        # Create a copy of the record to avoid modifying the original
        import copy
        record_copy = copy.copy(record)
        color = self.COLORS.get(record_copy.levelname, self.RESET)
        record_copy.levelname = f"{color}{record_copy.levelname}{self.RESET}"
        return super().format(record_copy)


def setup_logging(
    environment: str = "development",
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, logging.Logger]:
    """
    Setup comprehensive logging system using JSON configuration

    Args:
        environment: Environment type (development/production)
        custom_config: Optional custom configuration override

    Returns:
        Dictionary of configured loggers
    """

    # Get logging configuration from JSON config
    log_config = config.data.get('logging', {})
    if custom_config:
        log_config.update(custom_config)

    # Setup directories
    logs_dir = log_config.get('directories', {}).get('logs_dir', 'logs')
    log_dir = Path(__file__).parent / logs_dir

    if log_config.get('directories', {}).get('create_if_missing', True):
        log_dir.mkdir(exist_ok=True)

    # Get environment-specific log level
    levels_config = log_config.get('levels', {})
    log_level = levels_config.get(environment, levels_config.get('default', 'INFO'))
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Clear existing handlers
    logging.getLogger().handlers.clear()

    # Create loggers dictionary
    loggers = {}

    # Get logger configurations
    logger_configs = log_config.get('loggers', {})
    files_config = log_config.get('files', {})
    rotation_config = log_config.get('rotation', {})

    # Create all configured loggers
    for logger_key, logger_config in logger_configs.items():
        logger_name = logger_config.get('name', f'CineFusion.{logger_key}')
        logger = logging.getLogger(logger_name)

        # Set logger level
        logger_level = logger_config.get('level', log_level)
        logger.setLevel(getattr(logging, logger_level.upper(), numeric_level))
        logger.handlers.clear()

        # Create file handler
        log_file = log_dir / logger_config.get('file', f'cinefusion_{logger_key}.log')

        if rotation_config.get('enabled', True):
            # Time-based rotation for daily logs, size-based for others
            if logger_key == 'daily':
                file_handler = logging.handlers.TimedRotatingFileHandler(
                    log_file,
                    when=rotation_config.get('when', 'midnight'),
                    interval=rotation_config.get('interval', 1),
                    backupCount=rotation_config.get('backup_count', 30),
                    encoding=files_config.get('encoding', 'utf-8'),
                    utc=rotation_config.get('utc', False)
                )
            else:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=files_config.get('max_size_mb', 10) * 1024 * 1024,
                    backupCount=files_config.get('backup_count', 5),
                    encoding=files_config.get('encoding', 'utf-8')
                )
        else:
            file_handler = logging.FileHandler(
                log_file,
                encoding=files_config.get('encoding', 'utf-8')
            )

        # Set formatter based on configuration
        format_type = logger_config.get('format', 'json')
        if format_type == 'json':
            file_handler.setFormatter(StructuredFormatter())
        else:
            formats_config = log_config.get('formats', {})
            format_string = formats_config.get(format_type, formats_config.get('default'))
            file_handler.setFormatter(logging.Formatter(
                format_string,
                datefmt='%Y-%m-%d %H:%M:%S'
            ))

        logger.addHandler(file_handler)

        # Add to daily log if not daily logger itself
        if logger_key != 'daily' and 'daily' in logger_configs:
            daily_file = log_dir / logger_configs['daily'].get('file', 'cinefusion_daily.log')
            daily_handler = logging.handlers.TimedRotatingFileHandler(
                daily_file,
                when=rotation_config.get('when', 'midnight'),
                interval=rotation_config.get('interval', 1),
                backupCount=rotation_config.get('backup_count', 30),
                encoding=files_config.get('encoding', 'utf-8'),
                utc=rotation_config.get('utc', False)
            )
            daily_handler.setFormatter(StructuredFormatter())
            logger.addHandler(daily_handler)

        loggers[logger_key] = logger

    # Setup console logging if enabled
    console_config = log_config.get('console', {})
    if console_config.get('enabled', True):
        console_level = console_config.get('level', log_level)
        console_handler = logging.StreamHandler(sys.stdout)

        if console_config.get('colored', True):
            formats_config = log_config.get('formats', {})
            console_format = formats_config.get('console', formats_config.get('default'))
            console_formatter = ColoredConsoleFormatter(
                console_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formats_config = log_config.get('formats', {})
            console_format = formats_config.get('console', formats_config.get('default'))
            console_formatter = logging.Formatter(
                console_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, console_level.upper(), numeric_level))

        # Add console handler to all loggers
        for logger in loggers.values():
            logger.addHandler(console_handler)

    # Log system startup
    if 'app' in loggers:
        loggers['app'].info(f"Logging system initialized - Environment: {environment}, Level: {log_level}")

    return loggers
    app_logger.info(f"Log directory: {log_dir}")
    app_logger.info(f"JSON logging: {enable_json}")
    app_logger.info(f"Console logging: {enable_console}")

    return loggers


def get_request_logger() -> logging.Logger:
    """Get logger for API requests"""
    return logging.getLogger("CineFusion.api")


def get_performance_logger() -> logging.Logger:
    """Get logger for performance metrics"""
    return logging.getLogger("CineFusion.performance")


def get_error_logger() -> logging.Logger:
    """Get logger for errors"""
    return logging.getLogger("CineFusion.errors")


def get_security_logger() -> logging.Logger:
    """Get logger for security events"""
    return logging.getLogger("CineFusion.security")


def log_request(
    request_id: str,
    method: str,
    endpoint: str,
    user_ip: str,
    user_agent: str = None,
    query_params: Dict[str, Any] = None
):
    """Log API request"""
    logger = get_request_logger()
    logger.info(
        f"API Request - {method} {endpoint}",
        extra={
            'request_id': request_id,
            'user_ip': user_ip,
            'endpoint': endpoint,
            'method': method,
            'user_agent': user_agent,
            'query_params': query_params
        }
    )


def log_response(
    request_id: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    response_size: int = None
):
    """Log API response"""
    logger = get_request_logger()
    logger.info(
        f"API Response - {endpoint} [{status_code}] {response_time:.2f}ms",
        extra={
            'request_id': request_id,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time': response_time,
            'response_size': response_size
        }
    )


def log_error(
    error: Exception,
    request_id: str = None,
    endpoint: str = None,
    user_ip: str = None,
    additional_context: Dict[str, Any] = None
):
    """Log error with context"""
    logger = get_error_logger()

    extra_data = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }

    if request_id:
        extra_data['request_id'] = request_id
    if endpoint:
        extra_data['endpoint'] = endpoint
    if user_ip:
        extra_data['user_ip'] = user_ip
    if additional_context:
        extra_data.update(additional_context)

    logger.error(
        f"Error in {endpoint or 'unknown'}: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra=extra_data
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    endpoint: str = None,
    additional_data: Dict[str, Any] = None
):
    """Log performance metric"""
    logger = get_performance_logger()

    extra_data = {
        'metric_name': metric_name,
        'metric_value': value,
        'metric_unit': unit
    }

    if endpoint:
        extra_data['endpoint'] = endpoint
    if additional_data:
        extra_data.update(additional_data)

    logger.info(
        f"Performance: {metric_name} = {value}{unit}",
        extra=extra_data
    )


def log_security_event(
    event_type: str,
    severity: str,
    user_ip: str = None,
    user_agent: str = None,
    details: Dict[str, Any] = None
):
    """Log security event"""
    logger = get_security_logger()

    extra_data = {
        'event_type': event_type,
        'severity': severity
    }

    if user_ip:
        extra_data['user_ip'] = user_ip
    if user_agent:
        extra_data['user_agent'] = user_agent
    if details:
        extra_data.update(details)

    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(
        level,
        f"Security Event: {event_type}",
        extra=extra_data
    )


# Initialize logging system on import
loggers = setup_logging()

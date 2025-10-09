# utils/logger.py
"""
Comprehensive logging utility for SearchAI project
Provides structured logging with performance metrics and cultural analysis tracking
"""

import logging
import logging.handlers
import os
import sys
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import wraps
from contextlib import contextmanager


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color codes for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class CulturalAnalysisFilter(logging.Filter):
    """Filter to add cultural analysis context to log records"""
    
    def filter(self, record):
        # Add cultural analysis context if available
        if hasattr(record, 'cultural_context'):
            record.cultural_info = f"[Cultural: {record.cultural_context}]"
        else:
            record.cultural_info = ""
        
        # Add performance context if available
        if hasattr(record, 'processing_time_ms'):
            record.perf_info = f"[{record.processing_time_ms:.2f}ms]"
        else:
            record.perf_info = ""
        
        return True


class SearchAILogger:
    """
    Main logger class for SearchAI project with specialized methods
    """
    
    def __init__(self, name: str = "searchai"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Performance tracking
        self.performance_stats = {}
        self.error_counts = {}
        
    def _setup_handlers(self):
        """Setup logging handlers for console and file output"""
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(cultural_info)s%(perf_info)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(CulturalAnalysisFilter())
        
        # File handler for detailed logs
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "searchai.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(cultural_info)s%(perf_info)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(CulturalAnalysisFilter())
        
        # Error handler for error-only logs
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Performance handler for metrics
        perf_handler = logging.handlers.RotatingFileHandler(
            log_dir / "performance.log",
            maxBytes=5*1024*1024,
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_formatter = logging.Formatter(
            '%(asctime)s - PERF - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        perf_handler.setFormatter(perf_formatter)
        
        # Add all handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(perf_handler)
        
        # Specialized loggers
        self.perf_logger = logging.getLogger(f"{self.name}.performance")
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.setLevel(logging.INFO)
        self.perf_logger.propagate = False
    
    # Core logging methods - FIXED to handle kwargs properly
    def debug(self, msg, *args, **kwargs):
        """Debug level logging - converts kwargs to string"""
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.debug(msg, *args, extra=extra if extra else None)
        else:
            self.logger.debug(msg, *args)

    def info(self, msg, *args, **kwargs):
        """Info level logging - converts kwargs to string"""
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.info(msg, *args, extra=extra if extra else None)
        else:
            self.logger.info(msg, *args)

    def warning(self, msg, *args, **kwargs):
        """Warning level logging - converts kwargs to string"""
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.warning(msg, *args, extra=extra if extra else None)
        else:
            self.logger.warning(msg, *args)

    def error(self, msg, *args, **kwargs):
        """Error level logging - converts kwargs to string and tracks errors"""
        error_type = kwargs.pop('error_type', 'unknown')
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.error(msg, *args, extra=extra if extra else None)
        else:
            self.logger.error(msg, *args)

    def critical(self, msg, *args, **kwargs):
        """Critical level logging - converts kwargs to string"""
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.critical(msg, *args, extra=extra if extra else None)
        else:
            self.logger.critical(msg, *args)

    def exception(self, msg, *args, **kwargs):
        """Exception logging with traceback"""
        if kwargs:
            # Extract extra dict if present
            extra = kwargs.pop('extra', {})
            # Convert remaining kwargs to string
            if kwargs:
                kwargs_str = ', '.join(f"{k}={v}" for k, v in kwargs.items())
                msg = f"{msg} - {kwargs_str}" if not str(msg).endswith(' - ') else f"{msg}{kwargs_str}"
            self.logger.exception(msg, *args, extra=extra if extra else None)
        else:
            self.logger.exception(msg, *args)
    
    # Specialized logging methods for SearchAI
    def log_cultural_analysis(self, item_id: str, analysis_result: Dict, processing_time: float):
        """Log cultural analysis results"""
        self.info(
            f"Cultural analysis completed for item: {item_id} - "
            f"craft:{analysis_result.get('craft_type', 'unknown')}, "
            f"region:{analysis_result.get('region', 'unknown')}, "
            f"processing_time_ms={processing_time * 1000:.2f}, "
            f"confidence={analysis_result.get('confidence', 0.0)}"
        )
    
    def log_search_query(self, query: str, results_count: int, processing_time: float, cultural_enhancement: bool = False):
        """Log search query execution"""
        enhancement_info = "with cultural enhancement" if cultural_enhancement else "standard search"
        self.info(
            f"Search query executed: '{query}' -> {results_count} results ({enhancement_info}) - "
            f"processing_time_ms={processing_time * 1000:.2f}, query_length={len(query)}"
        )
    
    def log_recommendation_request(self, request_type: str, item_id: str, rec_types: List[str], processing_time: float, results_count: int):
        """Log recommendation requests"""
        self.info(
            f"Recommendation request: {request_type} for {item_id} -> {results_count} results - "
            f"recommendation_types={rec_types}, processing_time_ms={processing_time * 1000:.2f}"
        )
    
    def log_cache_operation(self, operation: str, cache_type: str, key: str, hit: bool = None):
        """Log cache operations"""
        if hit is not None:
            status = "HIT" if hit else "MISS"
            self.debug(f"Cache {operation}: {cache_type}[{key[:50]}] -> {status}")
        else:
            self.debug(f"Cache {operation}: {cache_type}[{key[:50]}]")
    
    def log_database_operation(self, operation: str, collection: str, duration: float, record_count: int = None):
        """Log database operations"""
        count_info = f" -> {record_count} records" if record_count is not None else ""
        self.debug(
            f"Database {operation}: {collection}{count_info} - "
            f"processing_time_ms={duration * 1000:.2f}"
        )
    
    def log_api_request(self, method: str, endpoint: str, processing_time: float, status_code: int, user_id: str = None):
        """Log API requests"""
        user_info = f" (user: {user_id})" if user_id else ""
        self.info(
            f"API {method} {endpoint} -> {status_code}{user_info} - "
            f"processing_time_ms={processing_time * 1000:.2f}, status_code={status_code}"
        )
    
    def log_error_with_traceback(self, error: Exception, context: str = ""):
        """Log error with full traceback"""
        error_msg = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
        self.error(
            f"{error_msg} - error_type={type(error).__name__}, traceback={traceback.format_exc()}"
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms", context: Dict = None):
        """Log performance metrics"""
        context_str = json.dumps(context) if context else ""
        self.perf_logger.info(f"{metric_name}: {value}{unit} {context_str}")
        
        # Track in memory for stats
        if metric_name not in self.performance_stats:
            self.performance_stats[metric_name] = []
        self.performance_stats[metric_name].append(value)
    
    # Context managers and decorators
    @contextmanager
    def log_operation(self, operation_name: str, **context):
        """Context manager to log operation start/end with timing"""
        start_time = time.time()
        context_str = ', '.join(f"{k}={v}" for k, v in context.items()) if context else ""
        self.debug(f"Starting {operation_name}" + (f" - {context_str}" if context_str else ""))
        
        try:
            yield
            duration = (time.time() - start_time) * 1000
            self.info(f"Completed {operation_name} - processing_time_ms={duration}" + (f", {context_str}" if context_str else ""))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.error(f"Failed {operation_name}: {str(e)} - processing_time_ms={duration}" + (f", {context_str}" if context_str else ""))
            raise
    
    def log_function_performance(self, include_args: bool = False, include_result: bool = False):
        """Decorator to log function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                func_name = f"{func.__module__}.{func.__name__}"
                
                # Log function start
                log_parts = [f"Calling function {func_name}"]
                if include_args and args:
                    log_parts.append(f"args_count={len(args)}")
                if include_args and kwargs:
                    log_parts.append(f"kwargs={list(kwargs.keys())}")
                
                self.debug(" - ".join(log_parts))
                
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    # Log successful completion
                    result_parts = [f"Function {func_name} completed successfully", f"processing_time_ms={duration}"]
                    if include_result and result is not None:
                        result_type = type(result).__name__
                        result_parts.append(f"result_type={result_type}")
                        if hasattr(result, '__len__'):
                            result_parts.append(f"result_length={len(result)}")
                    
                    self.debug(" - ".join(result_parts))
                    return result
                    
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    self.error(
                        f"Function {func_name} failed: {str(e)} - "
                        f"processing_time_ms={duration}, error_type={type(e).__name__}"
                    )
                    raise
            
            return wrapper
        return decorator
    
    # Statistics and monitoring
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for metric, values in self.performance_stats.items():
            if values:
                stats[metric] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "recent": values[-10:]  # Last 10 values
                }
        return stats
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return dict(self.error_counts)
    
    def reset_stats(self):
        """Reset performance and error statistics"""
        self.performance_stats.clear()
        self.error_counts.clear()
        self.info("Statistics reset")
    
    # Configuration
    def set_level(self, level: str):
        """Set logging level"""
        numeric_level = getattr(logging, level.upper(), None)
        if isinstance(numeric_level, int):
            self.logger.setLevel(numeric_level)
            self.info(f"Logging level set to {level.upper()}")
        else:
            self.warning(f"Invalid logging level: {level}")


# Global logger instances for different components
def get_logger(name: str = "searchai") -> SearchAILogger:
    """Get or create a logger instance"""
    return SearchAILogger(name)


# Pre-configured loggers for different components
search_logger = get_logger("searchai.search")
recommendation_logger = get_logger("searchai.recommendation")
cultural_logger = get_logger("searchai.cultural")
api_logger = get_logger("searchai.api")
database_logger = get_logger("searchai.database")
performance_logger = get_logger("searchai.performance")

# Utility function for quick setup
def setup_logging(log_level: str = "INFO", enable_performance_logging: bool = True):
    """
    Quick setup function for SearchAI logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_performance_logging: Whether to enable detailed performance logging
    """
    # Set root logger level
    root_logger = get_logger()
    root_logger.set_level(log_level)
    
    # Configure specialized loggers
    if not enable_performance_logging:
        performance_logger.logger.setLevel(logging.WARNING)
    
    root_logger.info(f"SearchAI logging initialized with level: {log_level}")
    return root_logger


# Example usage and testing
if __name__ == "__main__":
    # Test the logging system
    logger = setup_logging("DEBUG")
    
    logger.info("Testing SearchAI logging system")
    
    # Test cultural analysis logging
    logger.log_cultural_analysis(
        "item_123",
        {"craft_type": "pottery", "region": "rajasthan", "confidence": 0.85},
        0.150
    )
    
    # Test search logging
    logger.log_search_query("handmade pottery", 25, 0.342, cultural_enhancement=True)
    
    # Test recommendation logging
    logger.log_recommendation_request("similar_items", "item_123", ["cultural_similarity", "regional_discovery"], 0.580, 8)
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.log_error_with_traceback(e, "testing error logging")
    
    # Test performance decorator
    @logger.log_function_performance(include_args=True, include_result=True)
    def test_function(arg1, arg2, keyword_arg="test"):
        time.sleep(0.1)  # Simulate processing
        return {"result": "success", "data": list(range(10))}
    
    test_function("value1", "value2", keyword_arg="custom")
    
    # Show stats
    print("\nPerformance Stats:", logger.get_performance_stats())
    print("Error Stats:", logger.get_error_stats())
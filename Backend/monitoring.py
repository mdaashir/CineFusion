"""
CineFusion Performance Monitoring and Health Check Utilities
Production-ready monitoring tools for tracking application performance
"""

import time
import psutil
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    response_time_ms: float
    cache_hit_rate: float
    active_connections: int
    total_requests: int
    error_rate: float

@dataclass
class HealthStatus:
    """System health status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    uptime_seconds: float
    database_connected: bool
    cache_operational: bool
    disk_space_available: bool
    memory_usage_normal: bool
    cpu_usage_normal: bool
    error_rate_acceptable: bool

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""

    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history: List[PerformanceMetrics] = []
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.cache_hits = 0
        self.cache_requests = 0
        self.start_time = time.time()

    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record a request for metrics"""
        self.request_count += 1
        self.response_times.append(response_time_ms)

        if is_error:
            self.error_count += 1

        # Keep only recent response times for moving average
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]

    def record_cache_hit(self, hit: bool = True):
        """Record cache hit/miss"""
        self.cache_requests += 1
        if hit:
            self.cache_hits += 1

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Application metrics
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        cache_hit_rate = (self.cache_hits / self.cache_requests * 100) if self.cache_requests > 0 else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0

        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_usage_percent=disk.percent,
            response_time_ms=avg_response_time,
            cache_hit_rate=cache_hit_rate,
            active_connections=len(psutil.net_connections()),
            total_requests=self.request_count,
            error_rate=error_rate
        )

        # Add to history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.history_size:
            self.metrics_history.pop(0)

        return metrics

    def get_health_status(self) -> HealthStatus:
        """Comprehensive health check"""
        current_metrics = self.get_current_metrics()
        uptime = time.time() - self.start_time

        # Health checks
        database_connected = True  # Would check actual DB connection
        cache_operational = True   # Would check cache service
        disk_space_available = current_metrics.disk_usage_percent < 85
        memory_usage_normal = current_metrics.memory_percent < 80
        cpu_usage_normal = current_metrics.cpu_percent < 80
        error_rate_acceptable = current_metrics.error_rate < 5.0

        # Determine overall status
        critical_issues = not (database_connected and disk_space_available)
        performance_issues = not (memory_usage_normal and cpu_usage_normal and error_rate_acceptable)

        if critical_issues:
            status = "unhealthy"
        elif performance_issues:
            status = "degraded"
        else:
            status = "healthy"

        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=uptime,
            database_connected=database_connected,
            cache_operational=cache_operational,
            disk_space_available=disk_space_available,
            memory_usage_normal=memory_usage_normal,
            cpu_usage_normal=cpu_usage_normal,
            error_rate_acceptable=error_rate_acceptable
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the last period"""
        if not self.metrics_history:
            return {"message": "No metrics available"}

        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements

        return {
            "current_status": self.get_health_status().status,
            "avg_response_time_ms": sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics),
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "cache_hit_rate": recent_metrics[-1].cache_hit_rate if recent_metrics else 0,
            "total_requests": self.request_count,
            "error_rate": recent_metrics[-1].error_rate if recent_metrics else 0,
            "uptime_hours": (time.time() - self.start_time) / 3600
        }

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "summary": self.get_performance_summary(),
            "health_status": asdict(self.get_health_status()),
            "metrics_history": [asdict(m) for m in self.metrics_history]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

class AlertManager:
    """Alert management for performance issues"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.alert_history: List[Dict[str, Any]] = []
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 80,
            "disk_usage_percent": 85,
            "response_time_ms": 1000,
            "error_rate": 5.0,
            "cache_hit_rate_min": 70
        }

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        metrics = self.monitor.get_current_metrics()
        alerts = []

        # CPU usage alert
        if metrics.cpu_percent > self.thresholds["cpu_percent"]:
            alerts.append({
                "type": "cpu_high",
                "severity": "warning",
                "message": f"High CPU usage: {metrics.cpu_percent:.1f}%",
                "threshold": self.thresholds["cpu_percent"],
                "current_value": metrics.cpu_percent,
                "timestamp": metrics.timestamp
            })

        # Memory usage alert
        if metrics.memory_percent > self.thresholds["memory_percent"]:
            alerts.append({
                "type": "memory_high",
                "severity": "warning",
                "message": f"High memory usage: {metrics.memory_percent:.1f}%",
                "threshold": self.thresholds["memory_percent"],
                "current_value": metrics.memory_percent,
                "timestamp": metrics.timestamp
            })

        # Disk usage alert
        if metrics.disk_usage_percent > self.thresholds["disk_usage_percent"]:
            alerts.append({
                "type": "disk_full",
                "severity": "critical",
                "message": f"Disk space low: {metrics.disk_usage_percent:.1f}% used",
                "threshold": self.thresholds["disk_usage_percent"],
                "current_value": metrics.disk_usage_percent,
                "timestamp": metrics.timestamp
            })

        # Response time alert
        if metrics.response_time_ms > self.thresholds["response_time_ms"]:
            alerts.append({
                "type": "slow_response",
                "severity": "warning",
                "message": f"Slow response time: {metrics.response_time_ms:.1f}ms",
                "threshold": self.thresholds["response_time_ms"],
                "current_value": metrics.response_time_ms,
                "timestamp": metrics.timestamp
            })

        # Error rate alert
        if metrics.error_rate > self.thresholds["error_rate"]:
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"High error rate: {metrics.error_rate:.1f}%",
                "threshold": self.thresholds["error_rate"],
                "current_value": metrics.error_rate,
                "timestamp": metrics.timestamp
            })

        # Cache hit rate alert
        if metrics.cache_hit_rate < self.thresholds["cache_hit_rate_min"]:
            alerts.append({
                "type": "low_cache_hit_rate",
                "severity": "warning",
                "message": f"Low cache hit rate: {metrics.cache_hit_rate:.1f}%",
                "threshold": self.thresholds["cache_hit_rate_min"],
                "current_value": metrics.cache_hit_rate,
                "timestamp": metrics.timestamp
            })

        # Store alerts in history
        for alert in alerts:
            self.alert_history.append(alert)
            logger.warning(f"ALERT: {alert['message']}")

        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alert_history = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]

        return alerts

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]

# Global monitoring instances
performance_monitor = PerformanceMonitor()
alert_manager = AlertManager(performance_monitor)

# Monitoring middleware decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        error_occurred = False

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_occurred = True
            raise
        finally:
            execution_time = (time.time() - start_time) * 1000
            performance_monitor.record_request(execution_time, error_occurred)

    return wrapper

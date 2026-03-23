# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Data Health Checker (v0.9.0)

Provides proactive health monitoring and auto-cleanup.

v0.9.0 Features:
- Periodic health checks (every 24 hours)
- Automatic issue detection
- Auto-cleanup for expired data
- Health reports
- Alert on critical issues

Performance Targets:
- Health check: <1 second
- Auto-cleanup: <5 seconds
- Memory overhead: <10MB
"""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading


@dataclass
class HealthStatus:
    """Health status for a component"""
    component: str
    healthy: bool
    message: str
    severity: str = "info"  # info, warning, error, critical
    details: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}


@dataclass
class HealthReport:
    """Complete health report"""
    overall_healthy: bool
    check_time: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    statuses: List[HealthStatus]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class HealthChecker:
    """
    Data Health Checker
    
    Monitors:
    - Index health
    - Data integrity
    - Disk space
    - Memory usage
    - Expired memories
    - Backup status
    """
    
    def __init__(self, config):
        """
        Initialize health checker
        
        Args:
            config: Configuration manager
        """
        self.config = config
        self.last_check = None
        self.last_report = None
        self._check_thread = None
        self._stop_flag = False
        
        # Health check interval
        interval_hours = config.get("health.check_interval_hours", 24)
        self.check_interval = timedelta(hours=interval_hours)
        
        # Auto-cleanup enabled
        self.auto_cleanup_enabled = config.get("health.auto_cleanup", True)
        
        # Max backup count
        self.max_backups = config.get("health.max_backup_count", 10)
        
        # Alert on issues
        self.alert_on_issues = config.get("health.alert_on_issues", True)
        
        # Workspace path
        self.workspace = Path(config.get("storage.workspace", "~/.openclaw/workspace")).expanduser()
        self.claw_mem_dir = Path.home() / ".claw-mem"
        
        print(f"✅ HealthChecker initialized (interval: {interval_hours}h)")
    
    def check_all(self) -> HealthReport:
        """
        Perform comprehensive health check
        
        Returns:
            HealthReport with all status information
        """
        start_time = time.time()
        statuses = []
        recommendations = []
        
        # Check all components
        statuses.append(self._check_index_health())
        statuses.append(self._check_data_integrity())
        statuses.append(self._check_disk_space())
        statuses.append(self._check_memory_usage())
        statuses.append(self._check_expired_memories())
        statuses.append(self._check_backup_status())
        
        # Count issues
        critical_count = sum(1 for s in statuses if s.severity == "critical")
        warning_count = sum(1 for s in statuses if s.severity == "warning")
        total_issues = critical_count + warning_count
        
        # Generate recommendations
        recommendations = self._generate_recommendations(statuses)
        
        # Overall health
        overall_healthy = critical_count == 0
        
        # Create report
        report = HealthReport(
            overall_healthy=overall_healthy,
            check_time=datetime.now().isoformat(),
            total_issues=total_issues,
            critical_issues=critical_count,
            warning_issues=warning_count,
            statuses=statuses,
            recommendations=recommendations,
        )
        
        # Update state
        self.last_check = datetime.now()
        self.last_report = report
        
        elapsed = (time.time() - start_time) * 1000
        print(f"✅ Health check completed in {elapsed:.2f}ms")
        
        # Alert if needed
        if self.alert_on_issues and total_issues > 0:
            self._send_alert(report)
        
        # Auto-cleanup if enabled
        if self.auto_cleanup_enabled:
            self.auto_cleanup()
        
        return report
    
    def _check_index_health(self) -> HealthStatus:
        """Check index health"""
        try:
            index_dir = self.claw_mem_dir / "index"
            
            if not index_dir.exists():
                return HealthStatus(
                    component="index",
                    healthy=True,
                    message="Index not found (will be created on first use)",
                    severity="info"
                )
            
            # Check index files
            index_files = list(index_dir.glob("*.pkl*"))
            
            if not index_files:
                return HealthStatus(
                    component="index",
                    healthy=False,
                    message="Index directory exists but no index files found",
                    severity="warning",
                    details={"path": str(index_dir)}
                )
            
            # Check file sizes
            total_size = sum(f.stat().st_size for f in index_files)
            total_size_mb = total_size / (1024 * 1024)
            
            return HealthStatus(
                component="index",
                healthy=True,
                message=f"Index healthy ({len(index_files)} files, {total_size_mb:.2f}MB)",
                severity="info",
                details={
                    "file_count": len(index_files),
                    "total_size_mb": total_size_mb,
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="index",
                healthy=False,
                message=f"Index check failed: {str(e)}",
                severity="error",
                details={"error": str(e)}
            )
    
    def _check_data_integrity(self) -> HealthStatus:
        """Check data integrity"""
        try:
            memory_dir = self.workspace / "memory"
            
            if not memory_dir.exists():
                return HealthStatus(
                    component="data",
                    healthy=True,
                    message="Memory directory not found (will be created on first use)",
                    severity="info"
                )
            
            # Check MEMORY.md
            memory_file = memory_dir / "MEMORY.md"
            if memory_file.exists():
                size = memory_file.stat().st_size
                size_kb = size / 1024
                
                # Check if file is readable
                try:
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        # Read first line to verify readability
                        f.readline()
                    
                    return HealthStatus(
                        component="data",
                        healthy=True,
                        message=f"MEMORY.md healthy ({size_kb:.2f}KB)",
                        severity="info",
                        details={"size_kb": size_kb}
                    )
                except Exception as e:
                    return HealthStatus(
                        component="data",
                        healthy=False,
                        message=f"MEMORY.md corrupted: {str(e)}",
                        severity="error",
                        details={"error": str(e)}
                    )
            
            return HealthStatus(
                component="data",
                healthy=True,
                message="Memory directory exists, no MEMORY.md yet",
                severity="info"
            )
        
        except Exception as e:
            return HealthStatus(
                component="data",
                healthy=False,
                message=f"Data integrity check failed: {str(e)}",
                severity="error",
                details={"error": str(e)}
            )
    
    def _check_disk_space(self) -> HealthStatus:
        """Check available disk space"""
        try:
            # Get disk usage
            total, used, free = shutil.disk_usage(str(self.workspace))
            
            free_gb = free / (1024 ** 3)
            free_percent = (free / total) * 100
            
            # Determine severity
            if free_percent < 5:
                severity = "critical"
                message = f"Critical: Only {free_percent:.1f}% disk space remaining ({free_gb:.2f}GB)"
            elif free_percent < 10:
                severity = "warning"
                message = f"Warning: Low disk space ({free_percent:.1f}%, {free_gb:.2f}GB)"
            else:
                severity = "info"
                message = f"Disk space healthy ({free_percent:.1f}%, {free_gb:.2f}GB free)"
            
            return HealthStatus(
                component="disk",
                healthy=free_percent >= 5,
                message=message,
                severity=severity,
                details={
                    "total_gb": total / (1024 ** 3),
                    "used_gb": used / (1024 ** 3),
                    "free_gb": free_gb,
                    "free_percent": free_percent,
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="disk",
                healthy=False,
                message=f"Disk space check failed: {str(e)}",
                severity="error",
                details={"error": str(e)}
            )
    
    def _check_memory_usage(self) -> HealthStatus:
        """Check memory usage (estimate)"""
        try:
            import resource
            rusage = resource.getrusage(resource.RUSAGE_SELF)
            
            # Get memory in MB (max resident set size)
            memory_mb = rusage.ru_maxrss / 1024  # Convert KB to MB on macOS
            
            max_memory_mb = self.config.get("performance.max_memory_mb", 500)
            
            # Determine severity
            if memory_mb > max_memory_mb * 0.9:
                severity = "warning"
                message = f"Warning: High memory usage ({memory_mb:.2f}MB / {max_memory_mb}MB)"
            else:
                severity = "info"
                message = f"Memory usage healthy ({memory_mb:.2f}MB / {max_memory_mb}MB)"
            
            return HealthStatus(
                component="memory",
                healthy=True,
                message=message,
                severity=severity,
                details={
                    "current_mb": memory_mb,
                    "max_mb": max_memory_mb,
                    "usage_percent": (memory_mb / max_memory_mb) * 100,
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="memory",
                healthy=True,
                message=f"Memory check not available: {str(e)}",
                severity="info",
                details={"error": str(e)}
            )
    
    def _check_expired_memories(self) -> HealthStatus:
        """Check for expired memories"""
        try:
            memory_dir = self.workspace / "memory"
            
            if not memory_dir.exists():
                return HealthStatus(
                    component="memories",
                    healthy=True,
                    message="No memories yet",
                    severity="info"
                )
            
            # Count memory files
            memory_files = list(memory_dir.glob("*.md"))
            total_files = len(memory_files)
            
            # Check for old files (>30 days)
            old_files = []
            now = datetime.now()
            
            for f in memory_files:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                age = now - mtime
                
                if age.days > 30:
                    old_files.append({
                        "file": f.name,
                        "age_days": age.days,
                    })
            
            if old_files:
                return HealthStatus(
                    component="memories",
                    healthy=True,
                    message=f"{total_files} memory files, {len(old_files)} old (>30 days)",
                    severity="info",
                    details={
                        "total_files": total_files,
                        "old_files": len(old_files),
                        "oldest_files": old_files[:5],  # Show first 5
                    }
                )
            
            return HealthStatus(
                component="memories",
                healthy=True,
                message=f"{total_files} memory files, all recent",
                severity="info",
                details={"total_files": total_files}
            )
        
        except Exception as e:
            return HealthStatus(
                component="memories",
                healthy=False,
                message=f"Memory check failed: {str(e)}",
                severity="error",
                details={"error": str(e)}
            )
    
    def _check_backup_status(self) -> HealthStatus:
        """Check backup status"""
        try:
            backup_dir = Path(self.config.get("storage.backup_dir", "~/.claw-mem/backups")).expanduser()
            
            if not backup_dir.exists():
                return HealthStatus(
                    component="backups",
                    healthy=True,
                    message="No backups yet",
                    severity="info"
                )
            
            # Count backups
            backup_files = list(backup_dir.glob("*.zip"))
            backup_count = len(backup_files)
            
            # Get latest backup
            latest_backup = None
            if backup_files:
                latest_file = max(backup_files, key=lambda f: f.stat().st_mtime)
                latest_backup = {
                    "file": latest_file.name,
                    "size_mb": latest_file.stat().st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
                }
            
            return HealthStatus(
                component="backups",
                healthy=True,
                message=f"{backup_count} backups available",
                severity="info",
                details={
                    "backup_count": backup_count,
                    "latest_backup": latest_backup,
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="backups",
                healthy=False,
                message=f"Backup check failed: {str(e)}",
                severity="error",
                details={"error": str(e)}
            )
    
    def _generate_recommendations(self, statuses: List[HealthStatus]) -> List[str]:
        """Generate recommendations based on health status"""
        recommendations = []
        
        for status in statuses:
            if status.severity == "critical":
                recommendations.append(f"CRITICAL: {status.message}")
            elif status.severity == "warning":
                recommendations.append(f"Warning: {status.message}")
        
        # Add specific recommendations
        disk_status = next((s for s in statuses if s.component == "disk"), None)
        if disk_status and disk_status.severity in ["warning", "critical"]:
            recommendations.append("Action: Free up disk space or increase storage capacity")
        
        memory_status = next((s for s in statuses if s.component == "memory"), None)
        if memory_status and memory_status.severity == "warning":
            recommendations.append("Action: Reduce cache sizes or increase memory limits")
        
        return recommendations
    
    def _send_alert(self, report: HealthReport):
        """Send alert for health issues"""
        print("\n" + "=" * 60)
        print("⚠️  HEALTH ALERT")
        print("=" * 60)
        print(f"Total issues: {report.total_issues}")
        print(f"Critical: {report.critical_issues}")
        print(f"Warnings: {report.warning_issues}")
        
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")
        
        print("=" * 60 + "\n")
    
    def auto_cleanup(self) -> Dict[str, int]:
        """
        Perform automatic cleanup
        
        Returns:
            Dict with cleanup statistics
        """
        start_time = time.time()
        stats = {
            "files_cleaned": 0,
            "backups_removed": 0,
            "space_freed_mb": 0,
        }
        
        try:
            # Cleanup old backups
            stats["backups_removed"] = self._cleanup_old_backups()
            
            # Cleanup temporary files
            stats["files_cleaned"] = self._cleanup_temp_files()
            
            elapsed = (time.time() - start_time) * 1000
            print(f"✅ Auto-cleanup completed in {elapsed:.2f}ms")
            
        except Exception as e:
            print(f"⚠️  Auto-cleanup failed: {e}")
        
        return stats
    
    def _cleanup_old_backups(self) -> int:
        """Remove old backups beyond max count"""
        try:
            backup_dir = Path(self.config.get("storage.backup_dir", "~/.claw-mem/backups")).expanduser()
            
            if not backup_dir.exists():
                return 0
            
            # Get all backups sorted by time
            backup_files = sorted(
                backup_dir.glob("*.zip"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            removed = 0
            if len(backup_files) > self.max_backups:
                for backup in backup_files[self.max_backups:]:
                    backup.unlink()
                    removed += 1
                    print(f"🗑️  Removed old backup: {backup.name}")
            
            return removed
        
        except Exception as e:
            print(f"⚠️  Backup cleanup failed: {e}")
            return 0
    
    def _cleanup_temp_files(self) -> int:
        """Cleanup temporary files"""
        try:
            temp_dir = self.claw_mem_dir / "tmp"
            
            if not temp_dir.exists():
                return 0
            
            # Remove all temp files
            removed = 0
            for f in temp_dir.glob("*"):
                try:
                    f.unlink()
                    removed += 1
                except:
                    pass
            
            return removed
        
        except Exception as e:
            print(f"⚠️  Temp file cleanup failed: {e}")
            return 0
    
    def start_periodic_checks(self):
        """Start periodic health checks in background"""
        if self._check_thread is not None:
            print("⚠️  Periodic checks already running")
            return
        
        self._stop_flag = False
        self._check_thread = threading.Thread(target=self._periodic_check_loop, daemon=True)
        self._check_thread.start()
        print("✅ Periodic health checks started")
    
    def stop_periodic_checks(self):
        """Stop periodic health checks"""
        self._stop_flag = True
        if self._check_thread:
            self._check_thread.join(timeout=5)
            self._check_thread = None
        print("✅ Periodic health checks stopped")
    
    def _periodic_check_loop(self):
        """Background loop for periodic checks"""
        while not self._stop_flag:
            try:
                self.check_all()
            except Exception as e:
                print(f"⚠️  Periodic check failed: {e}")
            
            # Sleep in small intervals to allow quick stop
            for _ in range(int(self.check_interval.total_seconds())):
                if self._stop_flag:
                    break
                time.sleep(1)
    
    def get_report(self) -> Optional[HealthReport]:
        """Get last health report"""
        return self.last_report
    
    def get_stats(self) -> Dict:
        """Get health checker statistics"""
        return {
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_interval_hours": self.check_interval.total_seconds() / 3600,
            "auto_cleanup_enabled": self.auto_cleanup_enabled,
            "has_report": self.last_report is not None,
        }

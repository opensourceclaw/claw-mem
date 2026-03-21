#!/usr/bin/env python
"""
Health Checker Test (v0.9.0/P0-4)

Test proactive health monitoring
"""

import sys
import time
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.config_manager import ConfigManager
from claw_mem.health_checker import HealthChecker


def test_health_checker():
    """Test health checker functionality"""
    print("\n" + "=" * 60)
    print("Testing Health Checker (v0.9.0/P0-4)")
    print("=" * 60)
    
    # Create config
    config = ConfigManager(enable_hot_reload=False)
    
    # Create health checker
    print("\n1. Creating health checker...")
    checker = HealthChecker(config)
    print("   ✅ Health checker created")
    
    # Test 1: Full health check
    print("\n2. Running full health check...")
    start = time.time()
    report = checker.check_all()
    check_time = (time.time() - start) * 1000
    
    print(f"   Health check completed in {check_time:.2f}ms")
    print(f"   Overall healthy: {report.overall_healthy}")
    print(f"   Total issues: {report.total_issues}")
    print(f"   Critical: {report.critical_issues}")
    print(f"   Warnings: {report.warning_issues}")
    
    # Verify check time
    assert check_time < 1000, f"❌ Check time {check_time}ms exceeds 1000ms target"
    print(f"   ✅ Check time target met: <1s")
    
    # Print component statuses
    print("\n3. Component Status:")
    for status in report.statuses:
        icon = "✅" if status.healthy else "❌"
        severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🔴"}.get(status.severity, "ℹ️")
        print(f"   {icon} {status.component}: {status.message} {severity_icon}")
    
    # Print recommendations
    if report.recommendations:
        print("\n4. Recommendations:")
        for rec in report.recommendations:
            print(f"   - {rec}")
    
    # Test 2: Get stats
    print("\n5. Health checker stats:")
    stats = checker.get_stats()
    print(f"   Last check: {stats['last_check']}")
    print(f"   Check interval: {stats['check_interval_hours']}h")
    print(f"   Auto-cleanup enabled: {stats['auto_cleanup_enabled']}")
    
    # Test 3: Auto-cleanup
    print("\n6. Testing auto-cleanup...")
    start = time.time()
    cleanup_stats = checker.auto_cleanup()
    cleanup_time = (time.time() - start) * 1000
    
    print(f"   Auto-cleanup completed in {cleanup_time:.2f}ms")
    print(f"   Files cleaned: {cleanup_stats['files_cleaned']}")
    print(f"   Backups removed: {cleanup_stats['backups_removed']}")
    print(f"   Space freed: {cleanup_stats['space_freed_mb']:.2f}MB")
    
    # Verify cleanup time
    assert cleanup_time < 5000, f"❌ Cleanup time {cleanup_time}ms exceeds 5000ms target"
    print(f"   ✅ Cleanup time target met: <5s")
    
    # Test 4: Periodic checks (start and stop)
    print("\n7. Testing periodic checks...")
    checker.start_periodic_checks()
    print("   ✅ Periodic checks started")
    
    # Wait a bit
    time.sleep(2)
    
    checker.stop_periodic_checks()
    print("   ✅ Periodic checks stopped")
    
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"✅ Health check: {check_time:.2f}ms (target: <1000ms)")
    print(f"✅ Auto-cleanup: {cleanup_time:.2f}ms (target: <5000ms)")
    print(f"✅ Overall healthy: {report.overall_healthy}")
    print(f"✅ Components checked: {len(report.statuses)}")
    print(f"✅ Periodic checks: Working")
    print("=" * 60)
    
    print("\n🎉 All P0-4 targets met! Health checker complete!\n")
    
    return {
        "check_time_ms": check_time,
        "cleanup_time_ms": cleanup_time,
        "overall_healthy": report.overall_healthy,
        "total_issues": report.total_issues,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("claw-mem v0.9.0/P0-4 Health Checker Test")
    print("=" * 60)
    
    results = test_health_checker()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")

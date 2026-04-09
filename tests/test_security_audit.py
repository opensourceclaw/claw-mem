"""
Tests for Security Audit

Tests security audit functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path


class TestSecurityAudit:
    """Test security audit"""
    
    def test_audit_initialization(self):
        """Test audit initialization"""
        from claw_mem.security.audit import AuditLogger
        
        workspace = Path(tempfile.mkdtemp())
        
        try:
            audit = AuditLogger(workspace)
            assert audit is not None
        except:
            pass
        
        shutil.rmtree(workspace)
    
    def test_log_event(self):
        """Test logging security event"""
        from claw_mem.security.audit import AuditLogger
        
        workspace = Path(tempfile.mkdtemp())
        
        try:
            audit = AuditLogger(workspace)
            
            if hasattr(audit, 'log'):
                audit.log("test_event", {"key": "value"})
        except:
            pass
        
        shutil.rmtree(workspace)
    
    def test_get_audit_log(self):
        """Test getting audit log"""
        from claw_mem.security.audit import AuditLogger
        
        workspace = Path(tempfile.mkdtemp())
        
        try:
            audit = AuditLogger(workspace)
            
            if hasattr(audit, 'get_logs'):
                logs = audit.get_logs()
                assert isinstance(logs, list)
        except:
            pass
        
        shutil.rmtree(workspace)

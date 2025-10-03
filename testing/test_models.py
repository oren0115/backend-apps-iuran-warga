"""
Data models untuk security testing
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class TestResult:
    """Result dari satu security test"""
    name: str
    passed: bool
    message: str
    severity: str  # "CRITICAL", "WARNING", "INFO"
    recommendation: Optional[str] = None
    
    def __post_init__(self):
        if self.severity not in ["CRITICAL", "WARNING", "INFO"]:
            raise ValueError("Severity must be CRITICAL, WARNING, or INFO")

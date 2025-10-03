#!/bin/bash
# Quick Security Test Script for Linux/Mac
# Usage: ./quick_test.sh [URL]

echo "================================================================================"
echo "🔒 QUICK SECURITY TEST"
echo "================================================================================"
echo ""

if [ -z "$1" ]; then
    echo "Using default URL: http://localhost:8000"
    python testing/run_security_tests.py http://localhost:8000
else
    echo "Testing URL: $1"
    python testing/run_security_tests.py $1
fi

echo ""
echo "================================================================================"
echo "Test completed!"
echo "================================================================================"

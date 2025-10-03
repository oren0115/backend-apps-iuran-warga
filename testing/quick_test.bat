@echo off
REM Quick Security Test Script for Windows
REM Usage: quick_test.bat [URL]

echo ================================================================================
echo 🔒 QUICK SECURITY TEST
echo ================================================================================
echo.

if "%1"=="" (
    echo Using default URL: http://localhost:8000
    python testing\run_security_tests.py http://localhost:8000
) else (
    echo Testing URL: %1
    python testing\run_security_tests.py %1
)

echo.
echo ================================================================================
echo Test completed!
echo ================================================================================
pause

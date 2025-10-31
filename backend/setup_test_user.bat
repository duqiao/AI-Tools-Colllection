@echo off
echo 🎯 Setting up Test User for AI Media Translation
echo =============================================

echo.
echo 📝 Creating test user token...
cd /d "%~dp0"

python test_user_token.py

echo.
echo ✅ Test user setup complete!
echo 📋 Test credentials saved to: test_user_credentials.txt
echo.
echo 🔧 To use in React Native:
echo    The app will automatically use 'test_user' and 'test_user_ai'
echo.
echo 🔧 To test manually:
echo    curl -H "Authorization: Bearer $(type test_user_credentials.txt | findstr ACCESS_TOKEN)"
echo           http://127.0.0.1:8001/api/v1/users/profile
echo.

pause
@echo off
chcp 65001 >nul 2>&1
cd /d "%"~dp0
netsh advfirewall firewall add rule name="WaterSystem" dir=in action=allow protocol=TCP localport=5000 profile=any >nul 2>&1
python --version >nul 2>&1 || (echo Need Python 3 & pause & exit /b 1)
python -c "import flask" 2>nul || pip install flask -q
echo.
echo ============================================
echo   ??????
echo   http://localhost:5000
echo.
echo   ??: admin/admin123
echo        cangguan/warehouse123
echo        songshui/delivery123
echo ============================================
echo.
python app.py
pause


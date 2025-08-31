@echo off
REM ========================================
REM FaceSwapTool Build Script (Final: Auto Copy + Clean + Always Ensure Folders)
REM ========================================

setlocal enabledelayedexpansion

REM Kill running exe if open
taskkill /f /im main.exe >nul 2>&1

REM Clean old builds
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1

REM Get site-packages
for /f "delims=" %%i in ('python -c "import site; print(site.getsitepackages()[0])"') do set SITEPKG=%%i

REM Always include models folder
set "MODELS_ARG=--add-data=models:models"

REM Optionally include setuptools lorem ipsum
set "ADD_LOREM="
if exist "%SITEPKG%\setuptools\_vendor\jaraco\text\Lorem ipsum.txt" (
    set "ADD_LOREM=--add-data=%SITEPKG%\setuptools\_vendor\jaraco\text\Lorem ipsum.txt;setuptools/_vendor/jaraco/text"
) else (
    echo [WARN] Lorem ipsum.txt not found. Skipping.
)

REM ==============================
REM Build EXE with PyInstaller
REM ==============================
pyinstaller main.py --noconsole --windowed --clean ^
 %ADD_LOREM% %MODELS_ARG% ^
 --collect-all cv2 ^
 --collect-all PIL ^
 --collect-all numpy ^
 --collect-all insightface ^
 --collect-all onnxruntime

REM ==============================
REM Always ensure models/ + output/ inside dist
REM ==============================
if exist dist\main (
    echo [INFO] Ensuring models/ folder...
    rmdir /s /q dist\main\models >nul 2>&1
    xcopy /E /I /Y models dist\main\models >nul 2>&1

    echo [INFO] Ensuring clean output/ folder...
    rmdir /s /q dist\main\output >nul 2>&1
    mkdir dist\main\output
) else if exist dist (
    echo [INFO] Ensuring models/ folder...
    rmdir /s /q dist\models >nul 2>&1
    xcopy /E /I /Y models dist\models >nul 2>&1

    echo [INFO] Ensuring clean output/ folder...
    rmdir /s /q dist\output >nul 2>&1
    mkdir dist\output
)

REM ==============================
REM Copy OpenCV ffmpeg DLLs
REM ==============================
echo.
echo [INFO] Checking for OpenCV ffmpeg DLLs...
for %%f in ("%SITEPKG%\cv2\opencv_videoio_ffmpeg*.dll") do (
    if exist "%%f" (
        echo Copying %%~nxf to dist\main\
        copy "%%f" dist\main\ >nul
    )
)

REM ==============================
REM Build complete
REM ==============================
echo.
if exist dist\main\main.exe (
    echo ✅ Build complete! Run: dist\main\main.exe
) else if exist dist\main.exe (
    echo ✅ Build complete! Run: dist\main.exe
) else (
    echo ❌ Build failed. Check errors above.
)
pause

REM ===== Create README.txt inside dist/main =====
(
    echo ============================================
    echo   FaceSwapTool - How to Use
    echo ============================================
    echo.
    echo 1. Extract this folder somewhere on your PC.
    echo 2. Open the "main" folder.
    echo 3. Double-click main.exe to start the tool.
    echo 4. Click "Choose Video" and select a .mp4/.avi file.
    echo 5. Click "Choose Target Image" and select a .jpg/.png file.
    echo 6. Press "Run Face Swap".
    echo 7. The swapped video will be saved in the "output" folder.
    echo.
    echo ⚠️ Do NOT move main.exe outside this folder.
    echo ⚠️ Keep "models/" and "output/" folders as they are.
    echo.
    echo Enjoy using FaceSwapTool!
) > dist\main\README.txt

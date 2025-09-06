@echo off
REM Install Vogue Manager Maya integration
REM Windows batch file

echo Installing Vogue Manager Maya integration...

REM Get Maya scripts directory
set MAYA_SCRIPTS_DIR=%USERPROFILE%\Documents\maya\scripts
if not exist "%MAYA_SCRIPTS_DIR%" (
    echo Creating Maya scripts directory: %MAYA_SCRIPTS_DIR%
    mkdir "%MAYA_SCRIPTS_DIR%"
)

REM Copy vogue_maya module
echo Copying vogue_maya module...
xcopy /E /I /Y "%~dp0..\src\vogue_maya" "%MAYA_SCRIPTS_DIR%\vogue_maya"

REM Copy vogue_core module
echo Copying vogue_core module...
xcopy /E /I /Y "%~dp0..\src\vogue_core" "%MAYA_SCRIPTS_DIR%\vogue_core"

REM Copy shelf script
echo Installing shelf script...
copy /Y "%~dp0..\src\vogue_maya\shelf.mel" "%MAYA_SCRIPTS_DIR%\vogue_manager_shelf.mel"

echo.
echo Installation complete!
echo.
echo To use Vogue Manager in Maya:
echo 1. Start Maya
echo 2. Run: python("import vogue_maya.tool as vm; vm.show_vogue_manager()")
echo 3. Or use the shelf button if installed
echo.

pause

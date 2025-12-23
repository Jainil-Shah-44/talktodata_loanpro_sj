@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   TalkToData LoanPro - Database Restore Tool
echo ==============================================
echo.

REM ----------------------------------------------------
REM 1) CHECK IF PSQL EXISTS IN PATH
REM ----------------------------------------------------
echo Checking for PostgreSQL on system PATH...
psql -V >nul 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo PostgreSQL tools NOT found on PATH.
    echo Please enter PostgreSQL 'bin' folder path.
    echo Example: C:\Program Files\PostgreSQL\15\bin
    echo.
    set /p PG_BIN="Enter PostgreSQL bin path: "
    
    IF NOT EXIST "%PG_BIN%\psql.exe" (
        echo.
        echo ERROR: psql.exe not found in "%PG_BIN%".
        echo Please verify the path and try again.
        pause
        exit /b 1
    )
    
    set "PSQL_CMD=%PG_BIN%\psql.exe"
) ELSE (
    echo PostgreSQL found.
    for /f "delims=" %%i in ('where psql') do set PSQL_CMD=%%i
)

echo Using psql at: %PSQL_CMD%
echo.


REM ----------------------------------------------------
REM 2) ASK USER FOR POSTGRES PASSWORD
REM ----------------------------------------------------
set /p POSTGRES_PASSWORD="Enter PostgreSQL 'postgres' user password: "
set "PGPASSWORD=%POSTGRES_PASSWORD%"
echo.


REM ----------------------------------------------------
REM 3) FIND BACKUP SQL OR ZIP FILE
REM ----------------------------------------------------
set "BACKUP_DIR=%~dp0backup"
set "DEFAULT_SQL=%BACKUP_DIR%\latest_ttd_loanpro.sql"
set "DEFAULT_ZIP=%BACKUP_DIR%\latest_ttd_loanpro.zip"

echo Looking for backup in: %BACKUP_DIR%
echo.

REM 3A) If .sql exists → use it
if exist "%DEFAULT_SQL%" (
    echo Found SQL backup: %DEFAULT_SQL%
    set "SQLFILE=%DEFAULT_SQL%"
    goto FILE_READY
)

REM 3B) If .sql NOT found, check for .zip
if exist "%DEFAULT_ZIP%" (
    echo SQL not found but ZIP backup found: %DEFAULT_ZIP%
    echo Extracting ZIP file...
    
    REM Windows built-in unzip (PowerShell)
    powershell -Command "Expand-Archive -Force '%DEFAULT_ZIP%' '%BACKUP_DIR%'"
    
    REM Check extracted SQL now
    if exist "%DEFAULT_SQL%" (
        echo Extraction successful.
        echo Found SQL backup: %DEFAULT_SQL%
        set "SQLFILE=%DEFAULT_SQL%"
        goto FILE_READY
    ) else (
        echo WARNING: ZIP extracted but SQL file still not found.
    )
)

REM 3C) If both not found → ask user
echo.
echo No SQL or ZIP backup found automatically.
echo Please enter FULL PATH to the .sql file.
echo Example: C:\Backups\talktodata_loanpro.sql
echo.

set /p SQLFILE="Enter SQL file path: "

if not exist "%SQLFILE%" (
    echo.
    echo ERROR: SQL file not found at: %SQLFILE%
    echo Exiting...
    pause
    exit /b 1
)

:FILE_READY
echo.
echo Using SQL backup file: %SQLFILE%
echo.


REM ----------------------------------------------------
REM 4) DROP DATABASE (IF EXISTS)
REM ----------------------------------------------------
echo Dropping database "talktodata_loanpro" (if exists)...
"%PSQL_CMD%" -U postgres -h localhost -d postgres -c "DROP DATABASE IF EXISTS talktodata_loanpro;"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to drop database.
    pause
    exit /b 1
)
echo Database dropped successfully.
echo.



REM ----------------------------------------------------
REM 5) CREATE DATABASE
REM ----------------------------------------------------
echo Creating fresh database "talktodata_loanpro"...
"%PSQL_CMD%" -U postgres -h localhost -d postgres -c "CREATE DATABASE talktodata_loanpro;"
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create database.
    pause
    exit /b 1
)
echo Database created successfully.
echo.


REM ----------------------------------------------------
REM 6) RESTORE DATABASE
REM ----------------------------------------------------
echo Starting restore process...
"%PSQL_CMD%" -U postgres -h localhost -d talktodata_loanpro -f "%SQLFILE%"
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Restore failed.
    pause
    exit /b 1
)

echo.
echo ==============================================
echo   RESTORE COMPLETED SUCCESSFULLY!
echo ==============================================
echo.

pause
exit /b 0

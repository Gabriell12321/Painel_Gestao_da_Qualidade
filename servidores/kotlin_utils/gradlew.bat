@echo off
setlocal
set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
set APP_BASE_NAME=%~n0
set WRAPPER_JAR=%DIRNAME%gradle\wrapper\gradle-wrapper.jar
set WRAPPER_DIR=%DIRNAME%gradle\wrapper

rem Ensure wrapper jar exists (auto-download if missing)
if not exist "%WRAPPER_JAR%" (
  echo Gradle wrapper jar not found. Downloading (8.9)...
  if not exist "%WRAPPER_DIR%" mkdir "%WRAPPER_DIR%" >nul 2>&1
  powershell -NoProfile -NonInteractive -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://repo1.maven.org/maven2/org/gradle/gradle-wrapper/8.9/gradle-wrapper-8.9.jar' -OutFile '%WRAPPER_JAR%'" || (
    echo [ERROR] Failed to download gradle-wrapper.jar. Ensure internet access or install Gradle locally.
    exit /b 1
  )
)

rem Find Java
if defined JAVA_HOME (
  set JAVA_EXE=%JAVA_HOME%\bin\java.exe
) else (
  set JAVA_EXE=java
)
"%JAVA_EXE%" -version >nul 2>&1 || (
  echo [ERROR] Java not found. Install JDK 17+ and ensure 'java' is in PATH.
  exit /b 1
)

set CLASSPATH=%WRAPPER_JAR%
"%JAVA_EXE%" -Dorg.gradle.appname=%APP_BASE_NAME% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
exit /b %ERRORLEVEL%

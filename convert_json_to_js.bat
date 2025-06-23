@echo off
REM Convert tagged_problems_repository.json to data.js format
REM Usage: convert_json_to_js.bat

set INPUT_FILE=tagged_problems_repository.json
set OUTPUT_FILE=data.js

REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo Error: %INPUT_FILE% not found!
    pause
    exit /b 1
)

echo Converting %INPUT_FILE% to %OUTPUT_FILE%...

REM Create the data.js file with the JavaScript variable declaration
echo const PROBLEMS_DATA = > "%OUTPUT_FILE%"

REM Append the JSON content
type "%INPUT_FILE%" >> "%OUTPUT_FILE%"

REM Add semicolon at the end
echo ; >> "%OUTPUT_FILE%"

echo Conversion complete! Created %OUTPUT_FILE%
pause
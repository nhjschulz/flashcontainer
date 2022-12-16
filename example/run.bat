@echo off
echo running python ..\src\flashcontainer\pargen.py  --ihex gen\example.hex --csrc gen\example  --gld gen\example.ld example.xml

python ..\src\flashcontainer\pargen.py  --ihex gen\example.hex --csrc gen\example  --gld gen\example.ld example.xml
echo.
echo Generated output in gen folder:
echo.
dir /b gen
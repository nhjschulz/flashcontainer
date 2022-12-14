@echo off
echo running python ..\src\pargen\pargen.py  --ihex gen\example.hex --csrc gen\example  --gld gen\example.ld example.xml

python ..\src\pargen\pargen.py  --ihex gen\example.hex --csrc gen\example  --gld gen\example.ld example.xml
echo.
echo Generated output in gen folder:
echo.
dir /b gen
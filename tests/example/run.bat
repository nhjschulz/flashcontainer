@echo off
echo running python ..\src\flashcontainer\pargen.py  --ihex --csrc  --gld  -o gen example.xml

python ..\src\flashcontainer\pargen.py  --ihex --csrc  --gld  -o gen example.xml
echo.
echo Generated output in gen folder:
echo.
dir /b gen
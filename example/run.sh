#/bin/sh
python3 ../src/flashcontainer/pargen.py  --ihex --csrc  --gld  -o gen example.xml
echo generated files in gen folder:
ls gen
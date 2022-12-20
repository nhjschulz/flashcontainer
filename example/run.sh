#/bin/sh
python3 ../src/flashcontainer/pargen.py  --ihex --csrc --dump --gld -o gen example.xml
echo generated files in gen folder:
ls gen
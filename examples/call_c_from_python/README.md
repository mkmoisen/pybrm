To compile and run this, follow these steps.

First, compile it (remove -m32 for 64 bit):

    gcc -c -I/path/to/pin/home/include -m32 c.c

Next link it and create the shared library (remove -m32 for 64 bit):

    gcc -shared c.o -L/path/to/pin/home/lib -Wl,-R/path/to/pin/home/lib -lportal -lpcmext -o libc.so -m32

Now run `bar.py`
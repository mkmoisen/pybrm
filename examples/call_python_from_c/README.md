To compile and run this, follow these steps.

First, compile it:

    gcc -c -I/path/to/python/include/python3.7m -I/path/to/pin/home/include -m32 c.c

Next link it and create the shared library:

    gcc c.o -L/path/to/python/lib/python3.7/config-3.7m-i386-linux-gnu -L/path/to/python/lib -Wl,-rpath=/path/to/python/lib -lpython3.7m -lpthread -lm -ldl -lutil -lrt -Xlinker -export-dynamic -L/path/to/pin/home/lib -Wl,-R/path/to/pin/home/lib -lportal -lpcmext -m32

Now run `./a.out`

If you are having trouble determine the `/path/to/python/`, search for the `python3-config` command on your system. It may already be in your path; if not, it will be in the same `bin` directory that the `python` executable is located in.

To see the include path for compiling:

    python3-config --cflags

To see the linking path:

    python3-config --ldflags
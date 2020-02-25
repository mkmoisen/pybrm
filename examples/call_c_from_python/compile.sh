export PYTHONPATH=`pwd`

gcc -c -I/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/include -m32 c.c

retval=$?
if [ $retval -eq 0 ]; then
        echo "COMPILATION SUCCESS";
else
        echo "COMPILATION FAILED";
        exit 1
fi


gcc -shared c.o -L/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/lib -Wl,-R/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/lib -lportal -lpcmext -o libc.so -m32

retval=$?
if [ $retval -eq 0 ]; then
        echo "LINKING SUCCESS";
else
        echo "LINKING FAILED";
        exit 1
fi

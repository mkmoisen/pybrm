export PYTHONPATH=`pwd`

gcc -c -I/apps/brm10/mmoisen/miniconda3/include/python3.7m -I/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/include -m32 c.c

retval=$?
if [ $retval -eq 0 ]; then
        echo "COMPILATION SUCCESS";
else
        echo "COMPILATION FAILED";
        exit 1
fi


gcc c.o -L/apps/brm10/mmoisen/miniconda3/lib/python3.7/config-3.7m-i386-linux-gnu -L/apps/brm10/mmoisen/miniconda3/lib -Wl,-rpath=/apps/brm10/mmoisen/miniconda3/lib -lpython3.7m -lpthread -lm -ldl -lutil -lrt -Xlinker -export-dynamic -L/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/lib -Wl,-R/apps/BRM/portal/brm10/webexBRM/opt/portal/7.5/lib -lportal -lpcmext -m32

retval=$?
if [ $retval -eq 0 ]; then
        echo "LINKING SUCCESS";
else
        echo "LINKING FAILED";
        exit 1
fi


./a.out
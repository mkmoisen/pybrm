#include <Python.h>
#include <stdio.h>
#include "pcm.h"

int main(void)
{
    int err = 1;

    Py_Initialize();
    PyObject *module_name = NULL;
    PyObject *module = NULL;
    PyObject *bar_function = NULL;

    pcm_context_t *ctxp = NULL;
    int64 database;
    pin_errbuf_t ebuf;
    pin_flist_t *flistp = NULL;
    pin_flist_t *return_flistp = NULL;


    PyObject *capsule = NULL;
    PyObject *args = NULL;
    PyObject *result = NULL;

    char *flist_string = NULL;
    int flist_string_length = 0;

    module_name = PyUnicode_FromString((char *) "foo");
    if (!module_name) { goto error; }
    module = PyImport_Import(module_name);
    if (!module) {
        printf("Cannot find foo module, need to set $PYTHONPATH to path where foo.py is located");
        goto error;
    }
    bar_function =  PyObject_GetAttrString(module, (char *) "bar");
    if (!bar_function) {
        printf("Cannot find bar function in foo module");
        goto error;
    }

    PIN_ERR_CLEAR_ERR(&ebuf);
    PCM_CONNECT(&ctxp, &database, &ebuf);
    flistp = PIN_FLIST_CREATE(&ebuf);
    PIN_FLIST_FLD_SET(flistp, PIN_FLD_STATUS, NULL, &ebuf);
    if (PIN_ERR_IS_ERR(&ebuf)) {
        PIN_ERR_LOG_EBUF(PIN_ERR_LEVEL_ERROR, "error", &ebuf);
        printf("Error creating flist, check default.pinlog\n");
        goto error;
    }

    // The second argument must be "pybrm.flistp"
    capsule = PyCapsule_New(flistp, "pybrm.flistp", NULL);
    if (!capsule) { goto error; }
    args = Py_BuildValue("(O)", capsule);
    if (!args) { goto error; }
    result = PyObject_CallObject(bar_function, args);
    if (!result) { goto error; }



    if (!PyCapsule_CheckExact((PyObject *) result)) {
        printf("Python failed to return PyCapsule back to C");
        goto error;
    }
    return_flistp = (pin_flist_t *) PyCapsule_GetPointer(result, "pybrm.flistp");
    if (!return_flistp) { goto error; }
    PIN_FLIST_TO_STR(return_flistp, &flist_string, &flist_string_length, &ebuf);
    if (PIN_ERR_IS_ERR(&ebuf)) { goto error; }
    printf("Back in C, flist from flist is\n%s\n", flist_string);

    err = 0;

error:
    PIN_FLIST_DESTROY_EX(&flistp, NULL);
    PIN_FLIST_DESTROY_EX(&return_flistp, NULL);
    PCM_CONTEXT_CLOSE(ctxp, 0, &ebuf);
    if (flist_string) {
        free(flist_string);
    }

    Py_XDECREF(module_name);
    Py_XDECREF(bar_function);
    Py_XDECREF(module);
    Py_XDECREF(capsule);
    Py_XDECREF(args);
    Py_XDECREF(result);

    Py_Finalize();
    if (err == 1) {
        printf("Failed");
    } else {
        printf("Success");
    }
    return err;
}
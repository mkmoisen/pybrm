#include <Python.h>
#include <time.h>
#include <stdlib.h>
#include "pythread.h"
#include "structmember.h"
#include "pcm.h"
#include "cm_fm.h"
#include "pin_errs.h"
#include "pinlog.h"
#include "pin_os.h"
#include "pin_os_getopt.h"

/*
*
* Macros
*
*/
#define CHECK_PIN_ERR(ebuf, format) \
    do { \
        if ((PIN_ERR_IS_ERR(&ebuf))) { \
            PIN_ERR_LOG_EBUF(PIN_ERR_LEVEL_ERROR, format, &ebuf); \
            PyObject *tuple = PyTuple_New(5); \
            PyTuple_SetItem(tuple, 0, PyUnicode_FromString(format)); \
            PyTuple_SetItem(tuple, 1, PyUnicode_FromString(PIN_ERRLOC_TO_STR(ebuf.location))); \
            PyTuple_SetItem(tuple, 2, PyUnicode_FromString(PIN_ERRCLASS_TO_STR(ebuf.pin_errclass))); \
            PyTuple_SetItem(tuple, 3, PyUnicode_FromString(PIN_PINERR_TO_STR(ebuf.pin_err))); \
            PyTuple_SetItem(tuple, 4, PyUnicode_FromString(PIN_FIELD_GET_NAME(ebuf.field))); \
            PyErr_SetObject(BRMError, tuple); \
            Py_XDECREF(tuple); \
            PIN_ERRBUF_RESET(&ebuf); \
            goto error; \
        } \
    } while (0);

#define MAX_ERROR_BUFFER 255

#define CHECK_PIN_ERR_FORMAT(ebuf, format, ...) \
    do { \
        if ((PIN_ERR_IS_ERR(&ebuf))) { \
            char buffer[MAX_ERROR_BUFFER + 1]; \
            snprintf(buffer, MAX_ERROR_BUFFER, format, __VA_ARGS__); \
            PIN_ERR_LOG_EBUF(PIN_ERR_LEVEL_ERROR, buffer, &ebuf); \
            PyObject *tuple = PyTuple_New(5); \
            PyTuple_SetItem(tuple, 0, PyUnicode_FromString(buffer)); \
            PyTuple_SetItem(tuple, 1, PyUnicode_FromString(PIN_ERRLOC_TO_STR(ebuf.location))); \
            PyTuple_SetItem(tuple, 2, PyUnicode_FromString(PIN_ERRCLASS_TO_STR(ebuf.pin_errclass))); \
            PyTuple_SetItem(tuple, 3, PyUnicode_FromString(PIN_PINERR_TO_STR(ebuf.pin_err))); \
            PyTuple_SetItem(tuple, 4, PyUnicode_FromString(PIN_FIELD_GET_NAME(ebuf.field))); \
            PyErr_SetObject(BRMError, tuple); \
            Py_XDECREF(tuple); \
            PIN_ERRBUF_RESET(&ebuf); \
            goto error; \
        } \
    } while (0);

/*
*
* Exceptions
*
*/
static PyObject *BRMError;

static PyObject *BRMError_getter_code(void)
{
    PyObject *dict = NULL;
    PyObject *output = NULL;
    const char* code =
        "@property\n"
        "def message(self):\n"
        "    return self.args[0] if len(self.args) > 0 else ''\n"
        "\n"
        "@property\n"
        "def errloc(self):\n"
        "    return self.args[1] if len(self.args) > 1 else None\n"
        "\n"
        "@property\n"
        "def errclass(self):\n"
        "    return self.args[2] if len(self.args) > 1 else None\n"
        "\n"
        "@property\n"
        "def err(self):\n"
        "    return self.args[3] if len(self.args) > 1 else None\n"
        "\n"
        "@property\n"
        "def field(self):\n"
        "   return self.args[4] if len(self.args) > 1 else None\n"
        "\n"
    ;


    if ((dict = PyDict_New()) == NULL) {
        goto error;
    }
    // This is necessary to get property and len
    if (PyDict_SetItemString(dict, "__builtins__", PyEval_GetBuiltins()) < 0) {
        goto error;
    };
    if ((output = PyRun_String(code, Py_file_input, dict, dict)) == NULL) {
        goto error;
    }
    Py_DECREF(output);
    // The example I got this from does a delete, but this breaks len
    //if (PyDict_DelItemString(dict, "__builtins__") < 0) {
    //    goto error;
    //};
    return dict;

error:
    Py_XDECREF(dict);
    Py_XDECREF(output);
    return NULL;
}



/*
*
* Client
*
*/
typedef struct {
    PyObject_HEAD
    int32 is_open;
    pcm_context_t *ctxp;
    int64 database;
    pin_errbuf_t ebuf;
} Client;


static PyObject *Client_is_open(Client *self)
{
    if (self->is_open) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject *Client_close(Client *self)
{
    if (!self->is_open) {
        Py_RETURN_NONE;
    }
    PCM_CONTEXT_CLOSE(self->ctxp, 0, &self->ebuf);

    self->is_open = 0;

    Py_RETURN_NONE;
}

static void Client_dealloc(Client *self)
{
    Client_close(self);

    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject * Client_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Client *self = NULL;

    self = (Client *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->is_open = 0;
    }
    return (PyObject *) self;
}


static PyObject *Client_open(Client *self, PyObject *args, PyObject *kwargs)
{

    if (self->is_open == 1) {
         return Py_BuildValue("L", self->database);
    }

    PIN_ERRBUF_CLEAR(&self->ebuf);
    // splint actually gives an error if the following ; is present, so remove it from splint
    // None of these PIN_ERR_ macros actually return anything

    PCM_CONNECT(&self->ctxp, &self->database, &self->ebuf);
    // 64 bytes in 1 blocks are definitely lost in loss record 14 of 192
    // Conditional jump or move depends on uninitialised value(s)
    // Client_open (test.c:87)

    CHECK_PIN_ERR(self->ebuf, "Error opening pcm_connection");

    self->is_open = 1;

    return Py_BuildValue("L", self->database);
error:

    return NULL;
}

static PyObject *Client_capsule(Client *self, PyObject *args, PyObject *kwargs)
{
    if (!self->is_open) {
        Py_RETURN_NONE;
    }

    return PyCapsule_New(self->ctxp, "pybrm.ctxp", NULL);
}

static PyObject *Client_ebufp_capsule(Client *self, PyObject *args, PyObject *kwargs)
{
    if (!self->is_open) {
        Py_RETURN_NONE;
    }

    return PyCapsule_New(&self->ebuf, "pybrm.ebufp", NULL);
}

static PyObject *Client_raise_ebuf_error(Client *self, PyObject *args, PyObject *kwargs)
{
    if (!self->is_open) {
        Py_RETURN_NONE;
    }

    CHECK_PIN_ERR(self->ebuf, "Error in ebuf")

    Py_RETURN_NONE;
error:
    return NULL;
}

/*
* This is just to test Client_raise_ebuf_error
*/
static PyObject *Client_set_ebuf_error(Client *self, PyObject *args, PyObject *kwargs)
{
    if (!self->is_open) {
        Py_RETURN_NONE;
    }

    pin_set_err(&self->ebuf, PIN_ERRLOC_APP, PIN_ERRCLASS_APPLICATION, PIN_ERR_BAD_VALUE, 0, 0, 0);

    Py_RETURN_NONE;
}


static PyMethodDef Client_methods[] = {
    {"open", (PyCFunction) Client_open, METH_VARARGS, "Opens a connection to the CM"},
    {"close", (PyCFunction) Client_close, METH_NOARGS, "Closes a connection to the CM"},
    {"is_open", (PyCFunction) Client_is_open, METH_NOARGS, "Checks if a connection is open"},
    {"capsule", (PyCFunction) Client_capsule, METH_NOARGS, "Returns a capsule to the ctxp"},
    {"ebufp_capsule", (PyCFunction) Client_ebufp_capsule, METH_NOARGS, "Returns a capsule to the ebufp"},
    {"raise_ebuf_error", (PyCFunction) Client_raise_ebuf_error, METH_NOARGS, "If the ebuf has an error, this will raise an exception and reset the ebuf"},
    {"set_ebuf_error", (PyCFunction) Client_set_ebuf_error, METH_NOARGS, "Sets the err buff. This is only for testing raise_ebuf_err"},
    {NULL, NULL, 0, NULL}
};


static PyTypeObject ClientType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "brm.Client",
    .tp_doc = "BRM CM wrapper",
    .tp_basicsize = sizeof(Client),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Client_new,
    .tp_dealloc = (destructor) Client_dealloc,
    .tp_methods = Client_methods
};


/*
*
* FList
*
*/


typedef struct {
    PyObject_HEAD

    Client *client;
    pin_flist_t *flistp;
    PyObject *iter_fields;
    int iter_length;
    PyObject *parent_flist;
    pin_fld_num_t parent_field;
    int32 elem_id;
    PyObject *children;
    PyObject *weakref;
} FList;

static PyMemberDef FList_members[] = {
    {NULL}
};


/*
* Removes a child from the children dictionary on the parent
* Parent FLists have a children dictionary containing weak references to children
*/
static int FList_remove_child_from_cache(FList *self, pin_fld_num_t field, int32 elem_id)
{
    PyObject *tuple = NULL;

    if ((tuple = PyTuple_New(2)) == NULL) {
        return -1;
    }

    PyTuple_SetItem(tuple, 0, Py_BuildValue("i", field));
    PyTuple_SetItem(tuple, 1, Py_BuildValue("i", elem_id));

    if (PyDict_DelItem(self->children, tuple) < 0) {
        Py_DECREF(tuple);
        return -1;
    };

    Py_DECREF(tuple);
    return 0;

}

/*
* Returns a weak reference from the cache
* Caller must call PyErr_Occurred()
* This can be used with FList_delete_child which requires a weakref
*
* Return value: New Reference, caller should Py_XDECREF
*/
static PyObject *FList_get_child_from_cache(FList *self, pin_fld_num_t field, int32 elem_id)
{
    PyObject *weakref = NULL;
    PyObject *tuple = NULL;

    if ((tuple = PyTuple_New(2)) == NULL) {
        return NULL;
    }
    PyTuple_SetItem(tuple, 0, Py_BuildValue("i", field));
    PyTuple_SetItem(tuple, 1, Py_BuildValue("i", elem_id));

    weakref = PyDict_GetItemWithError(self->children, tuple);
    Py_XINCREF(weakref);
    Py_DECREF(tuple);

    return weakref;
}



static int FList_disassociate_child(FList *self, PyObject **weakref, pin_fld_num_t field, int32 elem_id)
{
    FList *child_flist = NULL;
    int err = 0;
    if (*weakref != NULL) {
        /* Decref the parent since we are disassociating the child */
        Py_DECREF(self);
        child_flist = (FList *) PyWeakref_GetObject(*weakref);
        if ((PyObject *) child_flist == Py_None) {
            // This might happen if the delete from the dict in FList_dealloc had an OOM
            Py_DECREF(*weakref);
            *weakref = NULL;
            child_flist = NULL;
        } else {
            // child_flist will never be NULL
            child_flist->parent_flist = NULL;
            child_flist->parent_field = 0;
        }
        // This could fail in exceptional scenarios like OOM, leaving a child in cache
        err = FList_remove_child_from_cache(self, field, elem_id);
    }

    return err;
}


/*
* Either Drop the child C Flist or disassociate the child C Flist from the parent
* If there are no other references to the child, we must drop it
* If there are other references to the child, we cannot drop it, but must disassociate it
*
* Use FList_get_child_from_cache to get a weak reference
* Then call one of the PIN_*_TAKE Macros to remove the C Flist from the parent
* Then call this function which will decide whether to DESTROY the flist or not
*/
static int FList_delete_child(FList *self, PyObject *weakref, pin_flist_t **flistpp, pin_fld_num_t field, int32 elem_id)
{
    /* this function may mutate weakref to NULL, which means we can destroy the child */
    int err = FList_disassociate_child(self, &weakref, field, elem_id);

    if (weakref == NULL) {
        PIN_FLIST_DESTROY_EX(flistpp, NULL);
        *flistpp = NULL;
    }

    return err;
}


static void FList_dealloc(FList *self)
{
    Py_XDECREF(self->iter_fields);

    /*
    Here are the rules:
        A Parent Python FList is one where self->parent_flist == NULL

        A Child Python FList is one where self->parent_flist != NULL

        Only a Child Python FList has a strong reference to a Parent Python FList
        The Parent Python FList has weak references to the Child Python FLists

        If a Child Python FList has 0 references,
            it does NOT destroy any C Flists

        If a Parent Python FList has 0 references,
            it destroy's its own FList, which destroy all Child C Flists

        It cannot be that a Parent Python FList has 0 references
            and a Child Python Flist has 1 reference
            Because the Child has the ref to the parent

    */

    if (self->parent_flist) {
        // I am a child
        // Do NOT destroy any C Flist
        // When Python Parent has 0 references,
        // it will destroy the C Parent FList,
        // which will destroy the C Child Flist

        // It's possible this can fail, leaving the weak reference in the parent's cache
        // However there is no way to recover in a dealloc function like this
        // Thus code that pulls from the cache needs to check for Py_None
        FList_remove_child_from_cache((FList *) self->parent_flist, self->parent_field, self->elem_id);

        Py_XDECREF(self->parent_flist);

    } else {
        // I am a parent - go ahead and destroy the C parent which will destroy any children C flists
        PIN_FLIST_DESTROY_EX(&self->flistp, NULL);
        self->flistp = NULL;
    }
    Py_XDECREF(self->children);
    if (self->weakref != NULL) { // TODO this isn't getting triggered in the tests ... check this, I would have thought this would
        PyObject_ClearWeakRefs((PyObject *) self);
    }
    Py_XDECREF(self->client);
    Py_TYPE(self)->tp_free((PyObject *) self);

}

static PyObject *FList_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    FList *self = NULL;

    self = (FList *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->flistp = NULL;
        self->parent_flist = NULL;
        self->elem_id = 0;
        self->children = NULL;
        self->iter_fields = NULL;
    }
    return (PyObject *) self;
}

static int FList_init(FList *self, PyObject *args, PyObject *kwargs)
{
    PyObject *client = NULL;
    /* is_open: whether or not the flistp should be instantiated to empty flist */
    int is_open = 0;
    char *flist_string = NULL;

    if (!PyArg_ParseTuple(args, "O!|is", &ClientType, &client, &is_open, &flist_string)) {
        return -1;
    }

    if (client) {
        Py_INCREF(client);
        self->client = (Client *)client;
    }

    if (flist_string) {
        /* BRM always prints a message to stderr if the flist is invalid. Even if you turn debugging off */
        PIN_STR_TO_FLIST(flist_string, self->client->database, &self->flistp, &self->client->ebuf);
        CHECK_PIN_ERR(self->client->ebuf, "FList string is invalid");

    } else {
        if (is_open) {
            self->flistp = PIN_FLIST_CREATE(&self->client->ebuf);
            CHECK_PIN_ERR(self->client->ebuf, "Error opening flist");
        }
    }

    if ((self->children = PyDict_New()) == NULL) {
        goto error;
    };

    if ((self->iter_fields = PyDict_New()) == NULL) {
        goto error;
    };

    return 0;

error:
    return -1;
}


static PyTypeObject FListType;
/*
* Careful: FList_make_flist Vs FList_make_flist_on_parent
* Use FList_make_flist when you do not need to maintain a reference to Parent
* E.g. Copy, opcode
* Every other time you require a reference on the Parent
*
* Calling code should make sure to set flistp after doing something to the C Flist
*
* Returns a New Reference
*/

static PyObject *FList_make_flist(FList *self)
{
    FList *new_flist = NULL;
    PyObject *arg_list = NULL;

    if ((arg_list = Py_BuildValue("(Oi)", (Client *)self->client, 0)) == NULL) {
        goto error;
    }

    // New Reference, calling code needs to return it to Python or Py_XDECREF on error
    if ((new_flist = (FList *) PyObject_CallObject((PyObject *) &FListType, arg_list)) == NULL) {
        goto error;
    }

error:
    Py_XDECREF(arg_list);
    return (PyObject *) new_flist;
}


/*
* Either retrieves a preexisting child FList from cache, or creates a new FList with null flist->flistp
* Calling code needs to check if (flist->flistp) and decide on what to do.
*
* Careful: FList_make_flist Vs FList_make_flist_on_parent
* Use FList_make_flist_on_parent when you need to maintain a reference on parent
* E.g. Get a subflist, get a subarray, create a subflist, create a subarray
* Don't use this for copying.
*
* Calling code should make sure to set flistp after doing something to the C Flist
* Alternatively, calling code can simply decref this. It will immediately deallocate and remove itself
* from the parents cash, in FList_dealloc
*
* Returns a New Reference
*/
static PyObject *FList_make_flist_on_parent(FList *self, pin_fld_num_t parent_field, int32 elem_id)
{
    FList *new_flist = NULL;
    PyObject *weakref = NULL;
    PyObject *tuple = NULL;

    if ((tuple = PyTuple_New(2)) == NULL) {
        goto error;
    }
    PyTuple_SetItem(tuple, 0, Py_BuildValue("i", parent_field));
    PyTuple_SetItem(tuple, 1, Py_BuildValue("i", elem_id));

    weakref = PyDict_GetItemWithError(self->children, tuple);
    if (PyErr_Occurred()) {
        goto error;
    }

    if (weakref != NULL) {
        // Cache hit, but it's possible the cache is Py_None under some exceptional scenarios
        new_flist = (FList *) PyWeakref_GetObject(weakref);
        if ((PyObject *) new_flist == Py_None) {
            // This might happen if the delete from the dict in FList_dealloc had an OOM
            weakref = NULL;
            new_flist = NULL;
            // No need to delete the key from the dict, since we will put it back in below
        } else {
            // new_flist won't ever be NULL here
            Py_INCREF(new_flist);
        }
    }

    if (weakref == NULL) {
        new_flist = (FList *) FList_make_flist((FList *) self);
        if (new_flist == NULL) {
            goto error;
        }

        weakref = PyWeakref_NewRef((PyObject *) new_flist, NULL);
        if (weakref == NULL) {
            Py_DECREF(new_flist);
            new_flist = NULL;
            goto error;
        }

        if (PyDict_SetItem(self->children, tuple, weakref) < 0) {
            Py_DECREF(weakref);
            Py_DECREF(new_flist);
            new_flist = NULL;
            goto error;
        };
        Py_DECREF(weakref);

        new_flist->parent_flist = (PyObject *) self;
        new_flist->parent_field = parent_field;
        new_flist->elem_id = elem_id;
        Py_INCREF(self);
    }

error:
    Py_XDECREF(tuple);
    return (PyObject *) new_flist;
}




static PyObject *FList_set_capsule(FList *self, PyObject *args, PyObject *kwargs)
{
    PyObject *capsule = NULL;

    pin_flist_t *flistp = NULL;
    int is_copy = 1;

    if (!PyArg_ParseTuple(args, "Oi", &capsule, &is_copy)) {
        goto error;
    }

    if (!PyCapsule_CheckExact((PyObject *) capsule)) {
        PyErr_SetString(PyExc_TypeError, "Expecting a PyCapsule type\n");
        goto error;
    }

    if (self->flistp != NULL) {
        PyErr_SetString(PyExc_ValueError, "Do not call set_pointer on an open flist\n");
        goto error;
    }

    if ((flistp = (pin_flist_t *) PyCapsule_GetPointer(capsule, "pybrm.flistp")) == NULL){
        goto error;
    }

    self->flistp = flistp;
    if (is_copy) {
        self->flistp = PIN_FLIST_COPY(flistp, &self->client->ebuf);
        CHECK_PIN_ERR(self->client->ebuf, "Error copying flist");
    }
    assert(self->flistp);

    Py_RETURN_NONE;
error:
    return NULL;
}


static PyObject *FList_capsule(FList *self, PyObject *args, PyObject *kwargs)
{
    int is_copy = 1;
    pin_flist_t *flistp = NULL;

    if (!PyArg_ParseTuple(args, "i", &is_copy)) {
        goto error;
    }

    flistp = self->flistp;

    if (is_copy) {
        flistp = PIN_FLIST_COPY(self->flistp, &self->client->ebuf);
        CHECK_PIN_ERR(self->client->ebuf, "Error copying flist");
    }

    return PyCapsule_New(flistp, "pybrm.flistp", NULL);
error:
    return NULL;
}


static PyObject *FList_str(FList *self)
{
    char *flist_string = NULL;
    int flist_string_length = 0;
    PyObject *ret = NULL;

    PIN_FLIST_TO_STR(self->flistp, &flist_string, &flist_string_length, &self->client->ebuf);

    CHECK_PIN_ERR(self->client->ebuf, "Error converting flist to string.");

    ret = PyUnicode_FromString(flist_string);

    free(flist_string);
    flist_string = NULL;

error:
    return ret;
}

static PyObject *FList_str_compact(FList *self)
{
    char *flist_string = NULL;
    int flist_string_length = 0;
    PyObject *ret = NULL;

    PIN_FLIST_TO_STR_COMPACT_BINARY(self->flistp, &flist_string, &flist_string_length, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error converting flist to string.");

    ret = PyUnicode_FromString(flist_string);

    free(flist_string);
    flist_string = NULL;

error:
    return ret;
}


static PyObject *FList_xml(FList *self, PyObject *args, PyObject *kwargs)
{
    int flag = 0;
    char *root_element_name = NULL;

    char *flist_string = NULL;
    int flist_string_length = 0;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "i|s", &flag, &root_element_name)) {
        return NULL;
    }

    PIN_FLIST_TO_XML(self->flistp, flag, 0, &flist_string, &flist_string_length, root_element_name, &self->client->ebuf);

    CHECK_PIN_ERR(self->client->ebuf, "Error converting flist to xml.");

    ret = PyUnicode_FromString(flist_string);

    free(flist_string);
    flist_string = NULL;

error:
    return ret;
}


/*
* Calling code must return the result to Python or decref it
* Py_RETURN_NONE will incref the Py_None singleton
*/
static PyObject *FList_drop_field(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int32 elem_id = 0;
    int optional = 0;

    PyObject *weakref = NULL;
    pin_flist_t *temp = NULL;
    pin_fld_type_t field_type = 0;

    if (!PyArg_ParseTuple(args, "i|ii", &field, &elem_id, &optional)) {
        return NULL;
    }

    field_type = PIN_GET_TYPE_FROM_FLD(field);

    if (field_type == PIN_FLDT_SUBSTRUCT || field_type == PIN_FLDT_ARRAY) {
        weakref = FList_get_child_from_cache(self, field, elem_id);
        if (PyErr_Occurred()) {
            goto error;
        }
    }

    if (field_type == PIN_FLDT_SUBSTRUCT) {
        temp = (pin_flist_t *)PIN_FLIST_FLD_TAKE(self->flistp, PIN_MAKE_FLD(field_type, field), optional, &self->client->ebuf);

    } else if (field_type == PIN_FLDT_ARRAY) {
        temp = PIN_FLIST_ELEM_TAKE(self->flistp, PIN_MAKE_FLD(field_type, field), elem_id, optional, &self->client->ebuf);

    } else {
        PIN_FLIST_FLD_DROP(self->flistp, PIN_MAKE_FLD(field_type, field), &self->client->ebuf);
    }
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error dropping field %s", PIN_FIELD_GET_NAME(field));

    if (field_type == PIN_FLDT_SUBSTRUCT || field_type == PIN_FLDT_ARRAY) {
        if (FList_delete_child(self, weakref, &temp, field, elem_id) < 0) {
            goto error;
        };
    }

    Py_XDECREF(weakref);
    Py_RETURN_NONE;

error:
    Py_XDECREF(weakref);
    return NULL;
}


static PyObject *FList_drop_array(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;

    int32 elem_id = 0;
    pin_cookie_t cookie = NULL;
    pin_cookie_t last_cookie = NULL;
    pin_flist_t *temp = NULL;
    PyObject *weakref;
    PyObject *ret = NULL;

    int deleted_count = 0;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        return NULL;
    }

    while (1)
    {
        last_cookie = cookie;
        temp = PIN_FLIST_ELEM_GET_NEXT(self->flistp, field, &elem_id, 1, &cookie, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error dropping field %s", PIN_FIELD_GET_NAME(field));
        if (last_cookie == cookie) {
            break;
        }

        weakref = FList_get_child_from_cache(self, field, elem_id);
        if (PyErr_Occurred()) {
            goto error;
        }

        temp = PIN_FLIST_ELEM_TAKE(self->flistp, field, elem_id, 1, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error dropping field %s", PIN_FIELD_GET_NAME(field));

        if (FList_delete_child(self, weakref, &temp, field, elem_id) < 0) {
            Py_XDECREF(weakref);
            goto error;
        };

        // This will cause PIN_FLIST_ELEM_GET_NEXT to take the first item again
        // Without this it will not delete everything since the cookie shifts on each take
        cookie = NULL;
        deleted_count++;
        Py_XDECREF(weakref);

    }

    ret = Py_BuildValue("i", deleted_count);

error:
    return ret;
}

static PyObject *FList_set_poid(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    char *poid_string = NULL;

    poid_t *pdp = NULL;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$s", kwargs_names, &field, &poid_string)) {
        return NULL;
    }

     /*
     pdp = PIN_POID_FROM_STR allocates new memory on heap.
     If you use PIN_FLIST_FLD_PUT, calling code can no longer access pdp
     Also, calling PIN_FLIST_DESTROY on the flist will free the memory for this
     You can prove this by then calling PIN_POID_DESTROY on pdp which will fail
     If you use PIN_FLIST_FLD_SET, then PIN_FLIST_DESTROY does not free the mem
     You can prove this by calling PIN_POID_DESTROY on pdp which will not fail
     Calling PIN_POID_DESTROY a second time will then fail.

     Note also that you cannot trust `if (pdp)` - it will return true
     regardless if you PIN_POID_DESTROY or PIN_FLIST_DESTROY.
     */

    if (poid_string) {
        pdp = PIN_POID_FROM_STR(poid_string, NULL, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error creating POID from %s", poid_string);
    }

    PIN_FLIST_FLD_PUT(self->flistp, PIN_MAKE_FLD(PIN_FLDT_POID, field), (void *) pdp, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting poid from %s", poid_string);

    Py_RETURN_NONE;

error:
    return NULL;
}


static PyObject *FList_get_poid(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    poid_t *pdp = NULL;
    pin_const_poid_type_t poid_type = NULL;
    pin_poid_id_t id_poid = 0;
    pin_db_no_t database = 0;
    pin_poid_rev_t revision = 0;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    pdp = (poid_t *) PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_POID, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error creating poid from field %s", PIN_FIELD_GET_NAME(field));

    if (pdp) {
        poid_type = PIN_POID_GET_TYPE(pdp);
        id_poid = PIN_POID_GET_ID(pdp);
        database = PIN_POID_GET_DB(pdp);
        revision = PIN_POID_GET_REV(pdp);
        ret = Py_BuildValue("sLiL", poid_type, id_poid, revision, database);
    } else {
        Py_RETURN_NONE;
    }

    return ret;

error:
    return NULL;
}

static PyObject *FList_get_int(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;
    int *value = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    value = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_INT, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting pin_fld_num_t field %s", PIN_FIELD_GET_NAME(field));

    if (value == NULL) {
        Py_RETURN_NONE;
    }
    return Py_BuildValue("i", *value);
error:
    return NULL;
}

static PyObject *FList_get_enum(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;
    int *value = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    value = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ENUM, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting enum field %s", PIN_FIELD_GET_NAME(field));

    if (value == NULL) { // TODO remove this? Won't ever trigger
        Py_RETURN_NONE;
    }

    return Py_BuildValue("i", *value);

error:
    return NULL;
}


static PyObject *FList_get_str(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;
    char *value = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    value = (char *) PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_STR, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting str field %s", PIN_FIELD_GET_NAME(field));

    if (value == NULL) {
        Py_RETURN_NONE;
    }

    return Py_BuildValue("s", value);

error:
    return NULL;
}


static PyObject *FList_get_binstr(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    pin_binstr_t *binstrp;
    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        goto error;
    }

    binstrp = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_BINSTR, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting str field %s", PIN_FIELD_GET_NAME(field));

    // As far as I can tell binstrp will not be NULL
    if (binstrp == NULL || binstrp->data == NULL) {
        Py_RETURN_NONE;
    }

    // Apparently if you give a NULL pointer here it is smart enough to return None to Python
    return Py_BuildValue("y#", binstrp->data, binstrp->size);

error:
    return NULL;
}


static PyObject *FList_get_buf(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    pin_buf_t *buf;
    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        goto error;
    }

    buf = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_BUF, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting str field %s", PIN_FIELD_GET_NAME(field));

    // As far as I can tell buf will not be NULL
    if (buf == NULL || buf->data == NULL) {
        Py_RETURN_NONE;
    }

    // Apparently if you give a NULL pointer here it is smart enough to return None to Python
    return Py_BuildValue("y#", buf->data, buf->size);

error:
    return NULL;
}


static PyObject *FList_does_field_exist(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;

    int elem_id = 0;
    pin_cookie_t cookie = NULL;
    pin_fld_type_t field_type = 0;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        goto error;
    }

    field_type = PIN_GET_TYPE_FROM_FLD(field);

    if (field_type == PIN_FLDT_ARRAY) {
        /*Use optional=0 to account for the case where a NULL FList is added to an Array */
        PIN_FLIST_ELEM_GET_NEXT(self->flistp, field, &elem_id, 0, &cookie, &self->client->ebuf);

    } else {
        // Use optional=0 to account for the case where a NULL POID is added to an FList
        // because PIN_FLIST_FLD_GET will return NULL
        PIN_FLIST_FLD_GET(self->flistp, field, 0, &self->client->ebuf);


    }

    if (PIN_ERR_IS_ERR(&self->client->ebuf)) {
        PIN_ERRBUF_RESET(&self->client->ebuf);
        Py_RETURN_FALSE;
    } else {
        Py_RETURN_TRUE;
    }

    Py_RETURN_TRUE;
error:
    return NULL;
}


static PyObject *FList_does_flist_exist_on_array(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int elem_id = 0;

    if (!PyArg_ParseTuple(args, "ii", &field, &elem_id)) {
        goto error;
    }

    if (elem_id == -1) {
        elem_id = PIN_ELEMID_ANY;
    }

    /* Use optional=0 to account for case where a NULL Flist is added to the array */
    PIN_FLIST_ELEM_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), elem_id, 0, &self->client->ebuf);
    if (PIN_ERR_IS_ERR(&self->client->ebuf)) {
        PIN_ERRBUF_RESET(&self->client->ebuf);
        Py_RETURN_FALSE;
    } else {
        Py_RETURN_TRUE;
    }
error:
    return NULL;
}

static PyObject *FList_get_tstamp(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;
    int *value = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    value = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_TSTAMP, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting tstamp field %s", PIN_FIELD_GET_NAME(field));

    if (value == NULL) {
        Py_RETURN_NONE;
    }

    return Py_BuildValue("i", *value);

error:
    return NULL;
}

static PyObject *FList_get_decimal(FList *self, PyObject *args,
                                   PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    pin_decimal_t *decimal_value;
    double output_value;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    decimal_value = PIN_FLIST_FLD_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_DECIMAL, field), optional, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting decimal field %s", PIN_FIELD_GET_NAME(field));

    if (decimal_value == NULL) {
        // The assumption here is that optional is 1,
        // and that PIN_FLIST_FLD_GET won't return NUll
        // without setting the ebuf error
        // Is that accurate?
        Py_RETURN_NONE;
    }

    output_value = pbo_decimal_to_double(decimal_value, &self->client->ebuf);
    if (PIN_ERR_IS_ERR(&self->client->ebuf)) {
        if (self->client->ebuf.pin_err == PIN_ERR_IS_NULL) {
            /* I can't create this error but I've seen it when pulling flists stored by other applications
            * pretty sure we can just return None */
            PIN_ERRBUF_RESET(&self->client->ebuf);
            Py_RETURN_NONE;
        }
    }
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting pbo_decimal_to_double for field %s", PIN_FIELD_GET_NAME(field));

    return Py_BuildValue("d", output_value);

error:
    return NULL;
}


/*
* Returns a New Reference
*/
static PyObject *FList_get_flist(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    FList *sub_flist = NULL;

    if (!PyArg_ParseTuple(args, "i|i", &field, &optional)) {
        return NULL;
    }

    if ((sub_flist = (FList *) FList_make_flist_on_parent(self, field, 0)) == NULL) {
        goto error;
    }

    if (!sub_flist->flistp) {
        sub_flist->flistp = PIN_FLIST_SUBSTR_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_SUBSTRUCT, field), optional, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting flist for field %s", PIN_FIELD_GET_NAME(field));
    }

    if (!sub_flist->flistp) {
        // If optional is 1 and flist doesn't exist at this index, return None
        // decrefing the sub_flist will make it immediately deallocate, where it is removed from parents cache
        Py_XDECREF(sub_flist);
        Py_RETURN_NONE;
    }

    return (PyObject *) sub_flist;

error:
    Py_XDECREF(sub_flist);
    return NULL;
}


static PyObject *FList_set_str(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    char *value = NULL;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|s", kwargs_names, &field, &value)) {
        goto error;
    }

    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_STR, field), (void *) value, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting str for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}


static PyObject *FList_set_binstr(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    char *value = NULL;
    int size = 0;


    pin_binstr_t binstr;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|y#", kwargs_names, &field, &value, &size)) {
        goto error;
    }

    binstr.data = value;
    binstr.size = size; // This is wrong but I'm not going to support this now
    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_BINSTR, field), &binstr, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting str for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}


static PyObject *FList_set_buf(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    char *value = NULL;
    int size = 0;


    pin_buf_t buf;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|y#", kwargs_names, &field, &value, &size)) {
        goto error;
    }

    buf.flag = 0;
    buf.offset = 0;
    buf.data = value;
    buf.size = size;
    buf.xbuf_file = NULL;
    // TODO this doesn't handle xbuf, flag and offset ...
    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_BUF, field), &buf, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting str for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}


static PyObject *FList_set_tstamp(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    time_t value = 0;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$i", kwargs_names, &field, &value)) {
        goto error;
    }

    // For BRM time stamps, 0 behaves as null
    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_TSTAMP, field), (void *) &value, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting tstamp for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}

static PyObject *FList_set_int(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int value = 0;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$i", kwargs_names, &field, &value)) {
        goto error;
    }

    // For BRM int values, there is no null int, just 0
    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_INT, field), (void *) &value, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting int for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}

static PyObject *FList_set_enum(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int value = 0;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$i", kwargs_names, &field, &value)) {
        goto error;
    }

    // For BRM int values, there is no null enum, just 0
    PIN_FLIST_FLD_SET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ENUM, field), (void *) &value, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting int for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    return NULL;
}


static PyObject *FList_set_decimal(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    char *value = NULL;
    pin_decimal_t *decimal_value = NULL;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$s", kwargs_names, &field, &value)) {
        return NULL;
    }

    if (value) {
        decimal_value = pin_decimal(value, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error converting to decimal for setting field %s", PIN_FIELD_GET_NAME(field));
        if (decimal_value == NULL) {
            PyErr_SetString(BRMError, "Error converting to pin_decimal_t\n");
            goto error;
        }
    }

    PIN_FLIST_FLD_PUT(self->flistp, PIN_MAKE_FLD(PIN_FLDT_DECIMAL, field), (void *) decimal_value, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error setting decimal for field %s", PIN_FIELD_GET_NAME(field));

    Py_RETURN_NONE;

error:
    // pbo_decimal_destroy allows NULL values
    pbo_decimal_destroy(&decimal_value);
    return NULL;
}


/*
* Returns a New Reference
*/
static PyObject *FList_get_array_flist(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int32 elem_id = 0;
    int optional = 0;

    FList *sub_flist = NULL;

    if (!PyArg_ParseTuple(args, "iii", &field, &elem_id, &optional)) {
        return NULL;
    }

    if ((sub_flist = (FList *) FList_make_flist_on_parent(self, field, elem_id)) == NULL) {
        goto error;
    }

    if (!sub_flist->flistp) {
        sub_flist->flistp = PIN_FLIST_ELEM_GET(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), elem_id, optional, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting flist for field %s elem_id %i", PIN_FIELD_GET_NAME(field), elem_id);
    }

    if (!sub_flist->flistp) {
        // If optional is 1 and flist doesn't exist at this index, return None
        // decrefing the sub_flist will make it immediately deallocate, where it is removed from parents cache
        Py_XDECREF(sub_flist);
        Py_RETURN_NONE;
    }

    return (PyObject *) sub_flist;

error:
    Py_XDECREF(sub_flist);
    return NULL;
}


/*
* Returns a New Reference
*
* Returns the flist at the PIN_ELEMID_ANY position on this array.
* Remember that if nothing was directly set at PIN_ELEMID_ANY, this will return the very first flist placed on the array
*
* This will determine what the first flist on the array was, which is always identical to PIN_ELEMID_ANY
* It will pull the elem_id from that, which is -1 for PIN_ELEMID_ANY and 0+ for a non PIN_ELEMID_ANY.
* It uses this elem_id to look up in the cache.
*/
static PyObject *FList_get_any_array_flist(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int optional = 0;

    int32 elem_id = 0;
    pin_cookie_t cookie = NULL;

    PyObject *arg_list = NULL;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "ii", &field, &optional)) {
        return NULL;
    }

    /*
    * Normally you would use PIN_FLIST_ELEM_GET with PIN_ELEMID_ANY
    * However we cannot cache that and return the proper FList wrapper
    * So we will use PIN_FLIST_ELEM_GET_NEXT and set cookie = NULL
    * This appears to have identical behavior to PIN_FLIST_ELEM_GET/PIN_ELEMID_ANY
    * Note also that PIN_FLIST_ELEM_GET with -1 will do the same thing here...
    */

    PIN_FLIST_ELEM_GET_NEXT(self->flistp, field, &elem_id, 1, &cookie, &self->client->ebuf);
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error getting flist for field %s", PIN_FIELD_GET_NAME(field));

    if ((arg_list = Py_BuildValue("(iii)", field, elem_id, optional)) == NULL){
        goto error;
    }

    ret = FList_get_array_flist(self, arg_list, NULL);

error:
    Py_XDECREF(arg_list);
    return ret;
}


/*
* Utility function for FList_set_flist_on_array_any. Check the comments there.
*
* The calling code will first copy the top level parent.
* If there are any child python references to the parent, they need to point to flists on the new parent.
*
* This recurses through each child on the flist that is in cache, in other words, it recurses through all
* the python references for this flist, and it updates each flistp to point to the parent.
*
* The calling code MUST destroy the old super-parent flistp, or it will be a memory leak.
*/
static int FList_recurse_any(FList *self) {
    PyObject *key = NULL, *value = NULL;
    Py_ssize_t pos = 0;
    FList *child = NULL;
    PyObject *field_object = NULL, *elem_id_object = NULL;
    pin_fld_num_t field = 0;
    int elem_id = 0;
    int err = 0;

    while (PyDict_Next(self->children, &pos, &key, &value)) {
        // key is tuple of (field, elem_id)
        // value is weakref to an FList
        child = (FList *) PyWeakref_GetObject(value);
        if ((PyObject *) child != Py_None) {
            field_object = PyTuple_GetItem(key, 0);
            field = PyLong_AsLong(field_object);

            elem_id_object = PyTuple_GetItem(key, 1);
            elem_id = PyLong_AsLong(elem_id_object);
            if (PyErr_Occurred()) {
                goto error;
            }

            // Set the child's flistp to the flist on the parent.
            child->flistp = PIN_FLIST_ELEM_GET(self->flistp, field, elem_id, 1, &self->client->ebuf);
            CHECK_PIN_ERR_FORMAT(self->client->ebuf, "failed to get child %s", PIN_FIELD_GET_NAME(field));
            if (FList_recurse_any(child) < 0) {
                err = -1;
            }
        }
    }
    return err;
error:
    return -1;
}


static PyObject *FList_set_flist_on_array_any(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    FList *elem_flist = NULL;

    pin_flist_t *flist_to_set = NULL;
    PyObject *arg_list = NULL;
    FList *ret = NULL;
    PyObject *weakref = NULL;

    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$O!", kwargs_names, &field, &FListType, &elem_flist)) {
        goto error;
    }

    /* Check to see if there is a pre-existing flist at the PIN_ELEMID_ANY position */
    if ((arg_list = Py_BuildValue("(ii)", field, 1)) == NULL){
        goto error;
    }
    if ((ret = (FList *) FList_get_any_array_flist(self, arg_list, NULL)) == NULL) {
        goto error;
    }

    Py_DECREF(arg_list);
    arg_list = NULL;

    /*
    * If there is a pre-existing flistp at PIN_ELEMID_ANY, we have to take special care of it here.
    * The PIN_FLIST_ELEM_SET will destroy the pre-existing flistp and replace it with the new one.
    * However, we may have some python references to an FList that holds the pre-existing flistp.
    *
    * We CANNOT simply call the FList_drop_field (which disasscociates parent from child, and only drops if
    * there are no Python references. This strategy works fine in FList_set_flist_on_array
    * but it doesn't work here with PIN_ELEMID_ANY.
    *
    * It doesn't work because once we call FList_drop_field on the first flistp, the next call to
    * PIN_FLIST_ELEM_SET will simply overwrite the second flistp, which is now the first flistp after the call to
    * PIN_FLIST_ELEM_SET.
    *
    * Instead, we have to copy the first flistp, and find all the children, and the grandchildren, and etc.
    * and update the children to point to the new copy. Then we can disassociate child from the parent, but not delete.
    * After this, we can safely PIN_FLIST_ELEM_SET which will delete the original and destroy it's memory.
    *
    */
    if ((PyObject *) ret != Py_None) {
        weakref = FList_get_child_from_cache(self, field, ret->elem_id);
        if (PyErr_Occurred()) {
            goto error;
        }

        ret->flistp = PIN_FLIST_COPY(ret->flistp, &self->client->ebuf);
        CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error copying parent field %s", PIN_FIELD_GET_NAME(field));
        if (FList_recurse_any(ret) < 0) {
            goto error;
        }

        if (FList_disassociate_child(self, &weakref, field, ret->elem_id) < 0) {
            goto error;
        }
    }

    if (elem_flist) {
        // otherwise we are setting it to NULL
        flist_to_set = elem_flist->flistp;
    }

    PIN_FLIST_ELEM_SET(self->flistp, flist_to_set, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), PIN_ELEMID_ANY, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error setting element on array");

    Py_XDECREF(weakref);
    Py_XDECREF(ret);
    Py_RETURN_NONE;

error:
    Py_XDECREF(arg_list);
    Py_XDECREF(ret);
    Py_XDECREF(weakref);
    return NULL;
}


/*
* Set an flist on an array using a regular, numeric index.
* Do not use this for PIN_ELEMID_ANY - use FList_set_flist_on_array_any instead.
*/
static PyObject *FList_set_flist_on_array(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    FList *elem_flist = NULL;
    int elem_id = 0;

    pin_flist_t *flist_to_set = NULL;
    PyObject *arg_list = NULL;
    PyObject *result = NULL;

    char *kwargs_names[] = {"field", "elem_id", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|$O!", kwargs_names, &field, &elem_id, &FListType, &elem_flist)) {
        goto error;
    }

    /*
    * PIN_FLIST_SUBSTR_SET will DESTROY an flist if it already exists
    * Thus need to call FList_drop_field to disassociate it if it exists
    * FList_drop_field checks if there are any references to this child flist
    * If there are, we take the memory of the child flist from the parent flist
    * This way, the PIN_FLIST_ELEM_SET has nothing to destroy
    * If there are not any references to this child flist,
    * we both take the memory and then destroy it
    * So in either case, the PIN_FLIST_ELEM_SET isn't actually destroying any memory
    */

    /*
    * The PIN_ELEMID_ANY is a bit more complex, and is handled in this function:
    * FList_set_flist_on_array_any
    * The calling code should NOT call -1 for PIN_ELEMID_ANY
    */


    if ((arg_list = Py_BuildValue("(iii)", field, elem_id, 1)) == NULL) {
        goto error;
    }
    if ((result = FList_drop_field(self, arg_list, NULL)) == NULL) {
        goto error;
    }

    if (elem_flist) {
        // otherwise we are setting it to NULL
        flist_to_set = elem_flist->flistp;
    }
    /*
    Note: there is NO NEED to set the elem_flist->parent_flist = self
    Because PIN_FLIST_ELEM_SET will copy the elem_flist->flistp into self->flistp.
    If self->flistp is destroyed, we can still refer to elem_flist->flistp without segfaulting.
    */
    PIN_FLIST_ELEM_SET(self->flistp, flist_to_set, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), elem_id, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error setting element on array");

    Py_DECREF(arg_list);
    return result;

error:
    Py_XDECREF(arg_list);
    Py_XDECREF(result);
    return NULL;
}


/*
* COPY an flist onto this array
* To create a brand new subflist, use FList_add_flist
*/
static PyObject *FList_set_substr(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    FList *substr_flist = NULL;

    PyObject *arg_list = NULL;
    PyObject *ret = NULL;
    pin_flist_t *flist_to_set = NULL;

    /*
    if (!PyArg_ParseTuple(args, "iO!", &field, &FListType, &substr_flist)) {
        return NULL;
    }
    */
    char *kwargs_names[] = {"field", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|$O!", kwargs_names, &field, &FListType, &substr_flist)) {
        goto error;
    }

    /*
    Note:

    This will COPY the input flist onto this parent flist.
    Thus there is no need to set the substr_flist->parent_flist = self
    Likewise there is no need to set the cache here, until someone calls a get
    Because PIN_FLIST_SUBSTR_SET will COPY*** the substr_flist->flistp into self->flistp.
    If self->flistp is destroyed, we can still refer to substr_flist->flistp without segfaulting.
    */
    if ((arg_list = Py_BuildValue("(iii)", field, 0, 1)) == NULL) {
        goto error;
    }

    /*
    * PIN_FLIST_SUBSTR_SET will DESTROY an flist if it already exists
    * Thus need to call FList_drop_field to disassociate it if it exists
    */
    if ((ret = FList_drop_field(self, arg_list, NULL)) == NULL) {
        goto error;
    }

    if (substr_flist != NULL) {
        flist_to_set = substr_flist->flistp;
    }

    PIN_FLIST_SUBSTR_SET(self->flistp, flist_to_set, PIN_MAKE_FLD(PIN_FLDT_SUBSTRUCT, field), &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error setting substructure");

    Py_DECREF(arg_list);

    return ret;

error:
    Py_XDECREF(arg_list);
    Py_XDECREF(ret);
    return NULL;
}


static PyObject *FList_copy_flist(FList *self, PyObject *args, PyObject *kwargs)
{
    FList *flist_copy = NULL;

    if ((flist_copy = (FList *) FList_make_flist(self)) == NULL) {
        goto error;
    }

    flist_copy->flistp = PIN_FLIST_COPY(self->flistp, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error copying flist");
    assert(flist_copy->flistp);

    return (PyObject *) flist_copy;

error:
    Py_XDECREF(flist_copy);
    return NULL;
}



static PyObject *FList_sort_flist(FList *self, PyObject *args,
                                  PyObject *kwargs)
{
    FList *sort_flist = NULL;
    int sort_default = 0;

    if (!PyArg_ParseTuple(args, "O!i", &FListType, &sort_flist, &sort_default)) {
        goto error;
    }

    PIN_FLIST_SORT(self->flistp, sort_flist->flistp, 0, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error sorting flist");

    Py_RETURN_NONE;

error:
    return NULL;
}

static PyObject *FList_sort_reverse_flist(FList *self, PyObject *args,
                                          PyObject *kwargs)
{
    FList *sort_flist = NULL;
    int sort_default = 0;


    if (!PyArg_ParseTuple(args, "O!i", &FListType, &sort_flist, &sort_default)) {
        goto error;
    }

    PIN_FLIST_SORT_REVERSE(self->flistp, sort_flist->flistp, 0, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error sorting flist");

    Py_RETURN_NONE;


error:
    return NULL;
}



static PyObject *FList_concat(FList *self, PyObject *args, PyObject *kwargs)
{
    FList *other_flist = NULL;

    if (!PyArg_ParseTuple(args, "O!", &FListType, &other_flist)) {
        goto error;
    }

    PIN_FLIST_CONCAT(self->flistp, other_flist->flistp, &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error concatenating flist");

    Py_RETURN_NONE;


error:
    return NULL;
}


// There is a bug in PIN_FLIST_COUNT
// If substructs/arrays are set using PIN_FLIST_FLD_SET, then PIN_FLIST_COUNT will count recursively
// Instead, we are using the flist_iter_init as a workaround
// PIN_FLIST_ELEM_COUNT seems to work fine, however


static PyObject *FList_array_count(FList *self, PyObject *args,
                                   PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    int32 count = -1;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        return NULL;
    }

    count = PIN_FLIST_ELEM_COUNT(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), &self->client->ebuf);
    CHECK_PIN_ERR(self->client->ebuf, "Error counting flist");

    ret = Py_BuildValue("i", count);

error:
    return ret;
}

static PyObject *FList_init_iter(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t   fld_num = 0;
    int32       elem_id = 0;
    pin_cookie_t    cookie = NULL;
    pin_cookie_t    last_cookie = NULL;

    PyObject *fld_name_object = NULL;

    PyDict_Clear(self->iter_fields);

    /*
    * If two flists, which both have the same field, are concatenated with PIN_FLIST_CONCAT
    * BRM will actually have both fields on the flist, for some reason.
    * It's probably a bug. For example, if you call PIN_FLIST_FLD_GET, which field should it return?
    *   It returns the first field.
    * You can prove this by printing the flist. It will show the duplicating value.
    * The COUNT will also return one extra field.
    * However in the function, we are going to ignore this case and instead deduplicate with the self->iter_fields
    * which is a dictionary (that maintains order in Python 3.6)
    * Please remember that PIN_FLIST_COUNT also has bugs, and then the count() of the flist actually ends up
    * counting the number of items returned by this function in self->iter_fields.
    * This in this concatenated case, we will only return the count of unique fields, not duplicate bug fields.
    *
    * The reason we don't want to return the same key twice is to prevent something like this:
    * for k, v in flist.items():
    *     print(k, v)
    * For duplicate keys with distinct values, this will print the first value twice
    */


    while (1)
    {
        last_cookie = cookie;
        PIN_FLIST_ANY_GET_NEXT(self->flistp, &fld_num, &elem_id, &cookie, &self->client->ebuf);
        if (last_cookie == cookie) {
            // Err buf is always filled on the very last iteration
            PIN_ERRBUF_RESET(&self->client->ebuf);
            break;
        }
        CHECK_PIN_ERR(self->client->ebuf, "Error iterating flist");

        if ((fld_name_object = Py_BuildValue("s", pin_name_of_field(fld_num))) == NULL) {
            goto error;
        }

        switch (PyDict_Contains(self->iter_fields, fld_name_object)) {
            case 0:
                /* This field name is not yet in our dict, so add it */
                if (PyDict_SetItem(self->iter_fields, fld_name_object, Py_None) < 0) {
                    Py_DECREF(Py_None);
                    goto error;
                };
                break;
            case 1:
                /* this field name already exists and is a duplicate, so don't add it */
                break;
            case 2:
                /* error */
                goto error;

        }

        Py_DECREF(fld_name_object);
    }

    Py_INCREF(self->iter_fields);

    return self->iter_fields;

error:
    Py_XDECREF(fld_name_object);
    return NULL;
}

/*
Returns a list of Array indexes.
Remember that a BRM Array is more like a Hash but with numeric keys, "sparse array"
*/
static PyObject *FList_array_init_iter(FList *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;

    int elem_id = 0;
    pin_cookie_t cookie = NULL;
    pin_cookie_t last_cookie = NULL;
    PyObject *dict = NULL;
    PyObject *elem_id_object = NULL;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        goto error;
    }

    if ((dict = PyDict_New()) == NULL) {
        goto error;
    }

    while (1)
    {
        last_cookie = cookie;
        PIN_FLIST_ELEM_GET_NEXT(self->flistp, PIN_MAKE_FLD(PIN_FLDT_ARRAY, field), &elem_id, 1, &cookie, &self->client->ebuf);
        CHECK_PIN_ERR(self->client->ebuf, "Error iterating flist");
        if (last_cookie == cookie) {
            break;
        }

        if ((elem_id_object = Py_BuildValue("i", elem_id)) == NULL) {
            goto error;
        }
        if (PyDict_SetItem(dict, elem_id_object, Py_None) < 0) {
            goto error;
        }
        Py_DECREF(elem_id_object);
    }

    return dict;

error:
    Py_XDECREF(dict);
    Py_XDECREF(elem_id_object);
    return NULL;
}


static PyObject *FList_opcode(FList *self, PyObject *args, PyObject *kwargs)
{
    FList *output_flist = NULL;
    pin_flist_t *output_flistp = NULL;
    int code = 0;
    int flag = 0;
    int is_reference = 0;

    if (!PyArg_ParseTuple(args, "i|ii", &code, &flag, &is_reference)) {
        return NULL;
    }

    if (!self->client->is_open) {
        PyErr_SetString(BRMError, "Client is closed\n");
        goto error;
    }

    Py_BEGIN_ALLOW_THREADS
    if (!is_reference) {
        PCM_OP(self->client->ctxp, code, flag, self->flistp, &output_flistp, &self->client->ebuf);
    } else {
        PCM_OPREF(self->client->ctxp, code, flag, self->flistp, &output_flistp, &self->client->ebuf);
    }

    Py_END_ALLOW_THREADS
    CHECK_PIN_ERR_FORMAT(self->client->ebuf, "Error calling opcode %i", code);

    if ((output_flist = (FList *) FList_make_flist(self)) == NULL) {
        goto error;
    }
    output_flist->flistp = output_flistp;

    return (PyObject *) output_flist;

error:
    Py_XDECREF(output_flist);
    return NULL;
}


static PyMethodDef FList_methods[] = {
    {"xml", (PyCFunction) FList_xml, METH_VARARGS, "returns xml representation of flist"},
    {"str_compact", (PyCFunction) FList_str_compact, METH_VARARGS, "returns compact binary str representation of flist"},
    {"drop_field", (PyCFunction) FList_drop_field, METH_VARARGS, "drops a field from an flist"},
    {"drop_array", (PyCFunction) FList_drop_array, METH_VARARGS, "drops an array from an flist"},
    {"set_poid", (PyCFunction) FList_set_poid, METH_VARARGS | METH_KEYWORDS, "sets a poid on an flist"},
    {"get_poid", (PyCFunction) FList_get_poid, METH_VARARGS, "gets a poid from an flist"},
    {"set_str", (PyCFunction) FList_set_str, METH_VARARGS | METH_KEYWORDS, "sets a string on an flist"},
    {"set_binstr", (PyCFunction) FList_set_binstr, METH_VARARGS | METH_KEYWORDS, "sets a binstr on an flist"},
    {"set_buf", (PyCFunction) FList_set_buf, METH_VARARGS | METH_KEYWORDS, "sets a buf on an flist"},
    {"does_field_exist", (PyCFunction) FList_does_field_exist, METH_VARARGS, "checks if field exists on flist"},
    {"does_flist_exist_on_array", (PyCFunction) FList_does_flist_exist_on_array, METH_VARARGS, "checks if field exists on flist"},
    {"get_str", (PyCFunction) FList_get_str, METH_VARARGS, "sets a string on an flist"},
    {"get_binstr", (PyCFunction) FList_get_binstr, METH_VARARGS, "sets a string on an flist"},
    {"get_buf", (PyCFunction) FList_get_buf, METH_VARARGS, "gets a buf from an flist"},
    {"set_tstamp", (PyCFunction) FList_set_tstamp, METH_VARARGS | METH_KEYWORDS, "sets a tstamp on an flist"},
    {"get_tstamp", (PyCFunction) FList_get_tstamp, METH_VARARGS, "gets a tstamp from an flist"},
    {"set_int", (PyCFunction) FList_set_int, METH_VARARGS | METH_KEYWORDS, "sets a tstamp on an flist"},
    {"set_enum", (PyCFunction) FList_set_enum, METH_VARARGS | METH_KEYWORDS, "sets a tstamp on an flist"},
    {"get_int", (PyCFunction) FList_get_int, METH_VARARGS, "sets a tstamp on an flist"},
    {"get_enum", (PyCFunction) FList_get_enum, METH_VARARGS, "sets a tstamp on an flist"},
    {"set_decimal", (PyCFunction) FList_set_decimal, METH_VARARGS | METH_KEYWORDS, "sets a tstamp on an flist"},
    {"get_decimal", (PyCFunction) FList_get_decimal, METH_VARARGS, "sets a tstamp on an flist"},
    {"get_flist", (PyCFunction) FList_get_flist, METH_VARARGS, "gets a sub flist"},
    {"set_flist_on_array", (PyCFunction) FList_set_flist_on_array, METH_VARARGS | METH_KEYWORDS, "sets an element on an array"},
    {"set_flist_on_array_any", (PyCFunction) FList_set_flist_on_array_any, METH_VARARGS | METH_KEYWORDS, "sets an element on an array at PIN_ELEMID_ANY"},
    {"set_substr", (PyCFunction) FList_set_substr, METH_VARARGS | METH_KEYWORDS, "sets an element on an array"},
    {"get_array_flist", (PyCFunction) FList_get_array_flist, METH_VARARGS, "gets a sub flist from array"},
    {"get_any_array_flist", (PyCFunction) FList_get_any_array_flist, METH_VARARGS, "gets any sub flist using PIN_ELEMID_ANY"},
    {"copy_flist", (PyCFunction) FList_copy_flist, METH_VARARGS, "copies an flist flist"},
    {"sort_flist", (PyCFunction) FList_sort_flist, METH_VARARGS, "sorts an flist"},
    {"sort_reverse_flist", (PyCFunction) FList_sort_reverse_flist, METH_VARARGS, "sort reverse an flist"},
    {"array_count", (PyCFunction) FList_array_count, METH_VARARGS, "counts an array"},
    {"init_iter", (PyCFunction) FList_init_iter, METH_VARARGS, "iter for flist"},
    {"array_init_iter", (PyCFunction) FList_array_init_iter, METH_VARARGS, "iter for an array"},
    {"opcode", (PyCFunction) FList_opcode, METH_VARARGS, "issues an opcode on the flist"},
    {"concat", (PyCFunction) FList_concat, METH_VARARGS, "issues an opcode on the flist"},
    {"set_capsule", (PyCFunction) FList_set_capsule, METH_VARARGS, "returns a capsule wrapper of the c flist pointer"},
    {"capsule", (PyCFunction) FList_capsule, METH_VARARGS, "returns a capsule wrapper of the c flist pointer"},
    {NULL}
};

static PyTypeObject FListType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "brm.FList",
    .tp_doc = "FList wrapper",
    .tp_basicsize = sizeof(FList),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = FList_new,
    .tp_init = (initproc) FList_init,
    .tp_dealloc = (destructor) FList_dealloc,
    .tp_members = FList_members,
    .tp_methods = FList_methods,
    .tp_str = (reprfunc) FList_str,
    .tp_repr = (reprfunc) FList_str,
    .tp_weaklistoffset = offsetof(FList, weakref),
};


static PyObject *brm_pcm_opname_to_opcode(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *opname = NULL;

    pin_opcode_t opcode = 0;

    if (!PyArg_ParseTuple(args, "s", &opname)) {
        return NULL;
    }

    opcode = pcm_opname_to_opcode(opname);

    if (opcode == 0) {
        PyErr_Format(PyExc_KeyError, "Do not know opname %s\n", opname);
        return NULL;
    }

    return Py_BuildValue("i", (int) opcode);
}

static PyObject *brm_pin_field_of_name(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *field_name = NULL;

    pin_fld_num_t field = 0;

    if (!PyArg_ParseTuple(args, "s", &field_name)) {
        return NULL;
    }

    field = PIN_FIELD_OF_NAME(field_name);

    if (field == 0) {
        PyErr_Format(PyExc_KeyError, "Do not know field %s\n", field_name);
        return NULL;
    }

    return Py_BuildValue("i", (int) field);
}


static PyObject *brm_pin_field_get_name(PyObject *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;
    const char *field_name = NULL;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        return NULL;
    }

    field_name = PIN_FIELD_GET_NAME(field);

    char *has_letters = NULL;
    strtol(field_name, &has_letters, 10);

    if (*has_letters) {
        return Py_BuildValue("s", field_name);
    } else {
        PyErr_Format(PyExc_KeyError, "Do not know field %i\n", field);
        return NULL;
    }
}


static PyObject *brm_pin_field_get_type(PyObject *self, PyObject *args, PyObject *kwargs)
{
    pin_fld_num_t field = 0;

    pin_fld_type_t field_type = 0;

    if (!PyArg_ParseTuple(args, "i", &field)) {
        return NULL;
    }

    field_type = PIN_FIELD_GET_TYPE(field);

    if (field_type == 0) {
        PyErr_Format(PyExc_KeyError, "Do not know field %i\n", field);
        return NULL;
    }

    return Py_BuildValue("i", (int) field_type);
}


static PyObject *brm_pin_virtual_time(PyObject *self)
{
    time_t current_t = 0;
    PyObject *ret = NULL;

    current_t = pin_virtual_time((time_t *) NULL);

    ret = Py_BuildValue("i", current_t);

    return ret;
}


static PyObject *brm_pin_err_log_msg(PyObject *self, PyObject *args, PyObject *kwargs)
{
    int32 level = 0;
    const char *message = NULL;
    const char *file_name = NULL;
    pin_err_line_no_t line_number = 0;

    if (!PyArg_ParseTuple(args, "issi", &level, &message, &file_name, &line_number)) {
        return NULL;
    }

    Py_BEGIN_ALLOW_THREADS
    pin_err_log_msg(level, message, file_name, line_number);
    Py_END_ALLOW_THREADS

    Py_RETURN_NONE;
}


/* Python will wrap this and return integer */
static PyObject *brm_pin_conf(PyObject *self, PyObject *args, PyObject *kwargs)
{
    const char *program_name = NULL;
    const char *key = NULL;
    char *char_value = NULL;
    PyObject *ret = NULL;

    if (!PyArg_ParseTuple(args, "ss", &program_name, &key)) {
        return NULL;
    }

    int32 err = 0;

    pin_conf(program_name, key, PIN_FLDT_STR, (caddr_t *)&(char_value), &err);
    if (char_value != NULL) {
        ret = Py_BuildValue("s", char_value);
        pin_free(char_value);
        return ret;
    }
    Py_RETURN_NONE;
}


static PyObject *brm_pin_err_set_level(PyObject *self, PyObject *args, PyObject *kwargs)
{
    int log_level = 0;

    if (!PyArg_ParseTuple(args, "i", &log_level)) {
        return NULL;
    }

    PIN_ERR_SET_LEVEL(log_level);

    Py_RETURN_NONE;
}

static PyObject *brm_pin_err_set_logfile(PyObject *self, PyObject *args, PyObject *kwargs)
{
    char *log_file = NULL;

    if (!PyArg_ParseTuple(args, "s", &log_file)) {
        return NULL;
    }

    PIN_ERR_SET_LOGFILE(log_file);

    Py_RETURN_NONE;
}


static PyObject *brm_pin_err_set_program(PyObject *self, PyObject *args, PyObject *kwargs)
{
    char *program = NULL;

    if (!PyArg_ParseTuple(args, "s", &program)) {
        return NULL;
    }

    PIN_ERR_SET_PROGRAM(program);

    Py_RETURN_NONE;
}


static PyMethodDef BrmMethods[] = {
    {"pcm_opname_to_opcode", (PyCFunction) brm_pcm_opname_to_opcode, METH_VARARGS, "get field number by field name"},
    {"pin_field_of_name", (PyCFunction) brm_pin_field_of_name, METH_VARARGS, "get field number by field name"},
    {"pin_field_get_name", (PyCFunction) brm_pin_field_get_name, METH_VARARGS, "get field name by field number"},
    {"pin_field_get_type", (PyCFunction) brm_pin_field_get_type, METH_VARARGS, "get field type by field number"},
    {"pin_virtual_time", (PyCFunction) brm_pin_virtual_time, METH_NOARGS, "returns the pin virtual time"},
    {"pin_err_log_msg", (PyCFunction) brm_pin_err_log_msg, METH_VARARGS, "logs a message"},
    {"pin_conf", (PyCFunction) brm_pin_conf, METH_VARARGS, "logs a message"},
    {"pin_err_set_level", (PyCFunction) brm_pin_err_set_level, METH_VARARGS, "sets the log level"},
    {"pin_err_set_logfile", (PyCFunction) brm_pin_err_set_logfile, METH_VARARGS, "sets the logfile"},
    {"pin_err_set_program", (PyCFunction) brm_pin_err_set_program, METH_VARARGS, "sets the log program name"},
    {NULL, NULL, 0, NULL}
};


static PyModuleDef cbrm = {
    PyModuleDef_HEAD_INIT,
    .m_name = "brm",
    .m_doc = "Python wrapper for BRM C APIs.",
    .m_size = -1,
    BrmMethods
};


PyMODINIT_FUNC
PyInit_cbrm(void) {
    PyObject *m = NULL;
    PyObject *exc_dict = NULL;

    if (PyType_Ready(&FListType) < 0) {
        goto error;
    }
    if (PyType_Ready(&ClientType) < 0) {
        goto error;
    }

    if ((m = PyModule_Create(&cbrm)) == NULL) {
        goto error;
    }

    Py_INCREF(&FListType);
    if (PyModule_AddObject(m, "_FList", (PyObject *) &FListType) < 0) {
        goto error;
    }

    Py_INCREF(&ClientType);
    if (PyModule_AddObject(m, "_Client", (PyObject *) &ClientType) < 0) {
        goto error;
    };

    if ((exc_dict = BRMError_getter_code()) == NULL) {
        goto error;
    }
    BRMError = PyErr_NewException("cbrm.BRMError", NULL, exc_dict);

    Py_XINCREF(BRMError);
    if (PyModule_AddObject(m, "BRMError", BRMError) < 0) {
        goto error;
    };


    return m;

error:
    Py_XDECREF(&FListType);
    Py_XDECREF(&ClientType);
    Py_XDECREF(BRMError);
    Py_CLEAR(BRMError);
    Py_XDECREF(exc_dict);
    Py_XDECREF(m);
    return NULL;
}

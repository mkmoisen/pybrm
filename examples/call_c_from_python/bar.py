from pybrm import Client, BRMError
import ctypes

# Tell ctypes what the argument and response types are for our libc.baz function
# Just make all the arguments void pointer
libc = ctypes.CDLL("libc.so")
libc.baz.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
libc.baz.restype = ctypes.c_void_p

# Tell ctypes what the argument and response types are for PyCapsule_GetPointer
ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]

# Tell ctypes what the argument and response types are for PyCapsule_New
ctypes.pythonapi.PyCapsule_New.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
ctypes.pythonapi.PyCapsule_New.restype = ctypes.py_object


if __name__ == '__main__':
    c = Client()
    f = c.flist()
    f['PIN_FLD_POID'] = 'pybrm'
    print("In python, flist is")
    print(f)
    # Since we are using ctypes, and the function might modify the flist, do not copy it
    # However the function we are calling better not destroy the flist, or else we will segfault when `f` deallocates
    flistp_capsule = f.capsule(copy_capsule=False)

    # Get the flistp pointer from the capsule
    flistp = ctypes.pythonapi.PyCapsule_GetPointer(
        flistp_capsule,
        b"pybrm.flistp"
    )

    ctxp_capsule = c.capsule()
    ctxp = ctypes.pythonapi.PyCapsule_GetPointer(
        ctxp_capsule,
        b"pybrm.ctxp"
    )

    ebufp_capsule = c.ebufp_capsule()
    ebufp = ctypes.pythonapi.PyCapsule_GetPointer(
        ebufp_capsule,
        b"pybrm.ebufp"
    )

    # Call the c library via ctypes, and receive a response_flistp
    # In this case, the response_flistp was allocated in C but we are responsible for deallocating it
    response_flistp = libc.baz(ctxp, flistp, ebufp)
    if response_flistp is None:
        # C probably had an error and returned Null flist
        # cannot make a Capsule from a null pointer
        print("ERROR: C returned NULL pointer")
        new = c.flist()
    else:
        # Very important: this name has to be defined in a variable before creating the Capsule
        try:
            c.raise_ebuf_error()
        except BRMError as ex:
            print("Caught error and reset error buffer: %s" % ex)
        else:
            print("errbuf didnt have errors")

        name = b"pybrm.flistp"
        # Wrap the pointer in a Capsule
        capsule = ctypes.pythonapi.PyCapsule_New(response_flistp, name, None)
        # Create our FLIst from the capsule
        # In this case, we are responsible for destroying, so we must not copy it
        new = c.flist(capsule=capsule, copy_capsule=False)
        # do not use capsule after this point! Delete it!
        del capsule
    print("back in python, response flist is")
    print(new)

from pybrm import Client


def bar(capsule):
    c = Client()
    f = c.flist(capsule=capsule)
    print("In Python, printing the flist from C")
    print(f)
    f['PIN_FLD_POID'] = '/python'
    f['PIN_FLD_USAGE_TYPE'] = "foo"
    f['PIN_FLD_QUANTITY'] = 100
    return f.capsule()

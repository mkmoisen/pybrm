# pybrm
A Python C wrapper for Oracle BRM.

`pybrm` requires >= Python 3.6 and is tested with Python 3.6.5 and 3.7.1, on BRM 7.5 (GCC 4.4.7) and BRM 12 (GCC 4.8.5). It has been tested on both 32bit and 64bit.

# Installation
To install and compile `pybrm`, your `PIN_HOME` environment variable must point to the BRM home directory.

Install it with `pip` like this:

    pip install pybrm

The installation will determine if you are on 32bit or 64bit Python and attempt to install correctly.

# Usage

Imports:

    from pybrm import Client
    from datetime import datetime
    
Open up a client CM connection:

    c = Client()
    
Create an empty flist:

    f = c.flist()
    
Set some scalar data on the flist:

    f['PIN_FLD_POID'] = '/account'  # type /account, id -1, revision 0
    f['PIN_FLD_STATUS'] = 1
    f['PIN_FLD_CREATED_T'] = datetime.now()  # you can also set it to an integer

Or if you prefer `flist.FIELD` notation:

    f.PIN_FLD_POID = '/account'  # type /account, id -1, revision 0
    f.PIN_FLD_STATUS = 1
    f.PIN_FLD_CREATED_T = datetime.now()  # you can also set it to an integer

Create a substructure in one shot, the preferred way:

    f['PIN_FLD_INHERITED_INFO'] = {
        'PIN_FLD_POID': ('/service', 1234), # type service, id 1234, revision 0
        'PIN_FLD_STATUS': 2,
    }

Or if you prefer `flist.FIELD` notation:

    f.PIN_FLD_INHERITED_INFO = {}
    f.PIN_FLD_INHERITED_INFO.PIN_FLD_POID = ('/service', 1234) # type service, id 1234, revision 0
    f.PIN_FLD_INHERITED_INFO.PIN_FLD_STATUS = 2

Print the flist:

    >>> print(f)
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_STATUS         ENUM [0] 1
    0 PIN_FLD_CREATED_T    TSTAMP [0] (1582600707) Mon Feb 24 19:18:27 2020
    0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
    1     PIN_FLD_STATUS         ENUM [0] 2

You can also build up a substruct it up piece by piece:

    f['PIN_FLD_EVENT'] = {}  # Creates an empty substruct
    f['PIN_FLD_EVENT']['PIN_FLD_POID'] = ('/service', 1234, 1)  # type service, id 1234, revision 1
    
    # You can pull a subsctruct out into its own variable if you like
    substruct = f['PIN_FLD_EVENT']
    substruct['PIN_FLD_STATUS'] = 3

which is equivalent to:

    f.PIN_FLD_EVENT = {}
    f.PIN_FLD_EVENT.PIN_FLD_POID = ('/service', 1234, 1)  # type service, id 1234, revision 1

    # You can pull a subsctruct out into its own variable if you like
    substruct = f.PIN_FLD_EVENT
    substruct.PIN_FLD_STATUS = 3

Let's print it again:

    >>> print(f)
    # number of field entries allocated 20, used 5
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_STATUS         ENUM [0] 1
    0 PIN_FLD_CREATED_T    TSTAMP [0] (1582600707) Mon Feb 24 19:18:27 2020
    0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
    1     PIN_FLD_STATUS         ENUM [0] 2
    0 PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 1
    1     PIN_FLD_STATUS         ENUM [0] 3

Create an array in one shot, the preferred way with dict syntax `{}`. The keys are the elem_ids, and the values are flists. In this example, we will creates two flists on elem_id 4 and 16:

    f['PIN_FLD_ARGS'] = {
        4: {'PIN_FLD_STATUS': 4},
        16: {'PIN_FLD_STATUS': 5},
    }

Let's print it again:

    >>> print(f)
    # number of field entries allocated 20, used 9
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_STATUS         ENUM [0] 1
    0 PIN_FLD_CREATED_T    TSTAMP [0] (1582600707) Mon Feb 24 19:18:27 2020
    0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
    1     PIN_FLD_STATUS         ENUM [0] 2
    0 PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 1
    1     PIN_FLD_STATUS         ENUM [0] 3
    0 PIN_FLD_ARGS          ARRAY [4] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 4
    0 PIN_FLD_ARGS          ARRAY [16] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 5    

You can instead use list syntax `[]`, and not specify the elem_ids. This will automatically start the elem_id off at 0 and increase it by one for each flist.

    f['PIN_FLD_RESULTS'] = [
        {'PIN_FLD_STATUS': 6},  # sets at elem_id 0
        {'PIN_FLD_STATUS': 7},  # sets at elem_id 1 
    ]

or

    f.PIN_FLD_RESULTS = [{}, {}]
    f.PIN_FLD_RESULTS[0].PIN_FLD_STATUS = 6
    f.PIN_FLD_RESULTS[1].PIN_FLD_STATUS = 7

Let's print it again:

    >>> print(f)
    # number of field entries allocated 20, used 9
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_STATUS         ENUM [0] 1
    0 PIN_FLD_CREATED_T    TSTAMP [0] (1582600707) Mon Feb 24 19:18:27 2020
    0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
    1     PIN_FLD_STATUS         ENUM [0] 2
    0 PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 1
    1     PIN_FLD_STATUS         ENUM [0] 3
    0 PIN_FLD_ARGS          ARRAY [4] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 4
    0 PIN_FLD_ARGS          ARRAY [16] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 5
    0 PIN_FLD_RESULTS       ARRAY [0] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 6
    0 PIN_FLD_RESULTS       ARRAY [1] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 7
    
You can also build up an array piece by piece:

    f['PIN_FLD_VALUES'] = {}  #  Creates an empty array
    f['PIN_FLD_VALUES'][0] = {'PIN_FLD_STATUS': 8}  # Adds an flist on the 0th elem_id of this array
    
    # You can pull an array out into its own variable if you like
    array = f['PIN_FLD_VALUES']
    array[1] = {}  # Create empty flist on the 1st elem_id of this array
    array[1]['PIN_FLD_STATUS'] = 9  # set one field on the flist we just created

alternatively:

    f.PIN_FLD_VALUES = {}  #  Creates an empty array
    f.PIN_FLD_VALUES[0] = {'PIN_FLD_STATUS': 8}  # Adds an flist on the 0th elem_id of this array

    # You can pull an array out into its own variable if you like
    array = f.PIN_FLD_VALUES
    array[1] = {}  # Create empty flist on the 1st elem_id of this array
    array[1].PIN_FLD_STATUS = 9  # set one field on the flist we just created


Let's print it again:

    >>> print(f)
    # number of field entries allocated 20, used 11
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_STATUS         ENUM [0] 1
    0 PIN_FLD_CREATED_T    TSTAMP [0] (1582600707) Mon Feb 24 19:18:27 2020
    0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
    1     PIN_FLD_STATUS         ENUM [0] 2
    0 PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 2
    1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 1
    1     PIN_FLD_STATUS         ENUM [0] 3
    0 PIN_FLD_ARGS          ARRAY [4] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 4
    0 PIN_FLD_ARGS          ARRAY [16] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 5
    0 PIN_FLD_RESULTS       ARRAY [0] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 6
    0 PIN_FLD_RESULTS       ARRAY [1] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 7
    0 PIN_FLD_VALUES        ARRAY [0] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 8
    0 PIN_FLD_VALUES        ARRAY [1] allocated 20, used 1
    1     PIN_FLD_STATUS         ENUM [0] 9

However, it's better to just create it all with a dict. This will keep your code clean:

    f = c.flist({
        'PIN_FLD_POID': '/account',
        'PIN_FLD_STATUS': 1,
        'PIN_FLD_CREATED_T': datetime.now(),
        'PIN_FLD_INHERITED_INFO': {
            'PIN_FLD_POID': ('/service', 1234),
            'PIN_FLD_STATUS': 2,
        },
        'PIN_FLD_EVENT': {
            'PIN_FLD_POID': ('/service', 1234, 1),
            'PIN_FLD_STATUS': 3,
        },
        'PIN_FLD_ARGS': {
            4: {'PIN_FLD_STATUS': 4},
            16: {'PIN_FLD_STATUS': 5},
        },
        'PIN_FLD_RESULTS': [
            {'PIN_FLD_STATUS': 6},
            {'PIN_FLD_STATUS': 7},
        ],
        'PIN_FLD_VALUES': {
            0: {'PIN_FLD_STATUS': 8},
            1: {'PIN_FLD_STATUS': 9},
        },
    })

Call an opcode via PCM_OP with no flags:
    
    output = f('PCM_OP_TEST_LOOPBACK')  # or f.opcode('PCM_OP_TEST_LOOPBACK')

Call an opcode via PCM_OP with one flag:

    output = f('PCM_OP_TEST_LOOPBACK', flags='SRCH_DISTINCT')

Call an opcode via PCM_OP with multiple flags:

    output = f('PCM_OP_TEST_LOOPBACK', flags=('SRCH_DISTINCT', 'PCM_OPFLG_REV_CHECK'))

You can also use the `f.opcode` function. One benefit is you can ctrl+f to find all opcode calls.

    output = f.opcode('PCM_OP_TEST_LOOPBACK', flags='SRCH_DISTINCT')
 
To use PCM_OPREF, which passes the reference of the flist to the opcode, instead of a copy like PCM_OP:
    
    output = f('PCM_OP_TEST_LOOPBACK', reference=True)  # or f.opcode('PCM_OP_TEST_LOOPBACK', reference=True)


Get some data off the flist:

    status = f['PIN_FLD_STATUS']
    assert status == 1
    
    poid = f.PIN_FLD_POID
    assert poid.type == '/account'
    assert poid.id == -1
    assert poid.revision == 0
    print(poid.database)  # this is picked up dynamically, but is probably 1
    
    assert f['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type == '/service'
    assert len(f['PIN_FLD_VALUES']) == 2
    assert f.PIN_FLD_VALUES[0].PIN_FLD_STATUS == 8

Get the length:


    assert len(f) == 8
    assert f.count() == 8  # same as len
    assert f.count(recursive=True) == 18  # counts items in arrays/substructs
    
    assert len(f['PIN_FLD_INHERITED_INFO']) == 2  # count of a substruct
    assert f['PIN_FLD_INHERITED_INFO'].count() == 2 # same as len
    
    
    assert len(f.PIN_FLD_VALUES) == 2  # count of an array
    assert f.PIN_FLD_VALUES.count() == 2  # same as len

Get all the field names:

    >>> print(list(f.keys())
    ['PIN_FLD_POID', 'PIN_FLD_STATUS', 'PIN_FLD_CREATED_T', 'PIN_FLD_INHERITED_INFO', 'PIN_FLD_EVENT', 'PIN_FLD_ARGS', 'PIN_FLD_RESULTS', 'PIN_FLD_VALUES']

Check if a field exists on our flist:

    >>> 'PIN_FLD_POID' in f
    True
    >>> 'PIN_FLD_EVENT' in f
    True
    >>> 'PIN_FLD_VALUES' in f
    True
    >>> 'PIN_FLD_QUANTITY' in f
    False

Get an flist at a particular elem_id from an array:

    child = f['PIN_FLD_VALUES'][0]
    child = f.PIN_FLD_VALUES[1]

Get any flist from an array (PIN_ELEMID_ANY):

    child = f['PIN_FLD_VALUES']['*']
    # This is equivalent
    child = f.PIN_FLD_VALUES['PIN_ELEMID_ANY']
    # This is also equivalent
    child = f['PIN_FLD_VALUES'][-1]

Delete a field:

    assert 'PIN_FLD_STATUS' in f
    del f['PIN_FLD_STATUS']
    assert 'PIN_FLD_STATUS' not in f

    assert 'PIN_FLD_VALUES' in f
    del f.PIN_FLD_VALUES
    assert 'PIN_FLD_VALUES' not in f

# Searching Shortcuts for PCM_OP_SEARCH

You can create your own flists and call `PCM_OP_SEARCH` yourself, however the `client.search()` make searching convenient with syntactic sugar:

    output = c.search(
        template=' select X from /foo where F1 = V1 and F2 = V2',
        search_flags='SRCH_DISTINCT',
        args={'PIN_FLD_LOGIN': 'bar', 'PIN_FLD_USAGE_TYPE': 'foo'},
    )

This would build the following search flist and execute it, returning the results:

    # number of field entries allocated 20, used 6
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 256
    0 PIN_FLD_TEMPLATE        STR [0] " select X from /foo where F1 = V1 and F2 = V2"
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_LOGIN           STR [0] "bar"
    0 PIN_FLD_ARGS          ARRAY [2] allocated 20, used 1
    1     PIN_FLD_USAGE_TYPE      STR [0] "foo"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 0, used 0

For the `args` parameter, you may specify it with a dict, or a list of tuples. These two are the same:

    output = c.search(
        template=' select X from /foo where F1 = V1 and F2 = V2',
        args={'PIN_FLD_LOGIN': 'bar', 'PIN_FLD_USAGE_TYPE': 'foo'},
    )
    
    output = c.search(
        template=' select X from /foo where F1 = V1 and F2 = V2',
        args=[('PIN_FLD_LOGIN', 'bar'), ('PIN_FLD_USAGE_TYPE', 'foo')],
    )

Using a dict in args is just syntactic sugar to save a few keystrokes.
Sometimes you cannot use the dict, for example if you have a template like `select C from /foo where F1 IN (V1, V2)`.
A dict will not work because a dict can only have unique keys.

    output = c.search(
        template=' select X from /foo where F1 IN (V1, V2) ',
        args=[
            ('PIN_FLD_USAGE_TYPE', 'FOO'),
            ('PIN_FLD_USAGE_TYPE', 'BAR')
        ]
    )

This would build the following search flist:

    # number of field entries allocated 20, used 6
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 0
    0 PIN_FLD_TEMPLATE        STR [0] " select C from /foo where F1 IN (V1, V2) "
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_USAGE_TYPE      STR [0] "FOO"
    0 PIN_FLD_ARGS          ARRAY [2] allocated 20, used 1
    1     PIN_FLD_USAGE_TYPE      STR [0] "BAR"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 0, used 0

You can use nested substructs and arrays in the `args` param like the following:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_EVENT': {'PIN_FLD_USAGE_TYPE': 'bar'}}
    )

This would create the following search flist:

    # number of field entries allocated 20, used 5
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 0
    0 PIN_FLD_TEMPLATE        STR [0] " select X from /foo where F1 = V1 "
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 1
    2         PIN_FLD_USAGE_TYPE      STR [0] "bar"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 0, used 0

You may customize the results of the search by using the `results` argument. By default, it will return all all the fields.

This will return only the three fields specified in `results`:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE'}
    )

Here is the search flist that would be created:

    # number of field entries allocated 20, used 5
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 0
    0 PIN_FLD_TEMPLATE        STR [0] " select X from /foo where F1 = V1 "
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_LOGIN           STR [0] "bar"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 20, used 3
    1     PIN_FLD_EVENT_TYPE      STR [0] NULL str ptr
    1     PIN_FLD_USAGE_TYPE      STR [0] NULL str ptr
    1     PIN_FLD_SERVICE_TYPE    STR [0] NULL str ptr

These three are identical:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE'}
    )
    
    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_EVENT_TYPE': None, 'PIN_FLD_SERVICE_TYPE': None}
    )
    
    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results=['PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE']
    )

The following will return all the fields in the substructure:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_INHERITED_INFO'}
    )


This will return only the subset of fields in the substructure:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_INHERITED_INFO': {
            'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE'
        }}
    )

Here is the search flist that would be created:

    # number of field entries allocated 20, used 5
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 0
    0 PIN_FLD_TEMPLATE        STR [0] " select X from /foo where F1 = V1 "
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_LOGIN           STR [0] "bar"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 20, used 1
    1     PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
    2         PIN_FLD_EVENT_TYPE      STR [0] NULL str ptr
    2         PIN_FLD_USAGE_TYPE      STR [0] NULL str ptr

You can do the same with arrays, for example `PIN_FLD_FIELD`.

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
        results={'PIN_FLD_FIELD': {
            'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE'
        }}
    )

Here is the search flist that would be created:

    # number of field entries allocated 20, used 5
    0 PIN_FLD_POID           POID [0] 0.0.0.1 /search -1 0
    0 PIN_FLD_FLAGS           INT [0] 0
    0 PIN_FLD_TEMPLATE        STR [0] " select X from /foo where F1 = V1 "
    0 PIN_FLD_ARGS          ARRAY [1] allocated 20, used 1
    1     PIN_FLD_LOGIN           STR [0] "bar"
    0 PIN_FLD_RESULTS       ARRAY [*] allocated 20, used 1
    1     PIN_FLD_FIELD         ARRAY [*] allocated 20, used 2
    2         PIN_FLD_EVENT_TYPE      STR [0] NULL str ptr
    2         PIN_FLD_USAGE_TYPE      STR [0] NULL str ptr

You can specify the search flags in `PIN_FLD_FLAGS` via the `search_flags` parameter:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        search_flags='SRCH_DISTINCT',
        args={'PIN_FLD_LOGIN': 'bar'},
    )

You can pass in more than one search flag in a sequence:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        search_flags=('SRCH_DISTINCT', 'SRCH_EXACT'),
        args={'PIN_FLD_LOGIN': 'bar'},
    )

You can specify the opcode flags via the `opcode_flags` parameter:

    output = c.search(
        template=' select X from /foo where F1 = V1 ',
        search_flags=('SRCH_DISTINCT', 'SRCH_EXACT'),
        args={'PIN_FLD_LOGIN': 'bar'},
        opcode_flags='PCM_OPFLG_CACHEABLE',
    )


In fact, if you want to examine the search flist, and not execute it, you can use `c.search_build_flist()`:

    search =c.search_build_flist(
        template=' select X from /foo where F1 = V1 ',
        args={'PIN_FLD_LOGIN': 'bar'},
    )
    print(search)

# Substructures and Arrays

One important thing to note about substructures is that when you add one flist to another flist, it is ALWAYS copied.
 

    c = Client()
    f = c.flist({'PIN_FLD_STATUS': 1}) 
    f2 = c.flist()
    
    # COPY f onto f2
    f2['PIN_FLD_INHERITED_INFO'] = f
    
    # Change f, which does not change anything on f2
    f['PIN_FLD_STATUS'] = 2
    # The copy on f2['PIN_FLD_INHERITED_INFO'] was not changed!
    assert f2['PIN_FLD_INHERITED_INFO']['PIN_FLD_STATUS'] == 1

The same is true for arrays:

    c = Client()
    f = c.flist({'PIN_FLD_STATUS': 1})
    f2 = c.flist()
    
    # COPY f2 onto f's PIN_FLD_VALUES array
    f2['PIN_FLD_VALUES'] = {0: f}
    
    # Change f, which does not change anything on f2
    f['PIN_FLD_STATUS'] = 2
    # The copy on f['PIN_FLD_VALUES'][0] was not changed!
    assert f2['PIN_FLD_VALUES'][0]['PIN_FLD_STATUS'] == 1
    
Both the FList and the BRMArray classes implement the Python dictionary protocol. What this means is that they both have a key that maps to a value. 
In the case of an flist, the key is the field, and the value is the value of the flist at that field. 
In the case of a BRMArray, the key is the elem_id, and the value is the flist at that elem_id.


Do not try to iterate over a BRMArray like a Python list:

    f = c.flist({
        'PIN_FLD_VALUES': [
            {'PIN_FLD_STATUS': 2},
            {'PIN_FLD_STATUS': 4},
        ]
    })
    
    # Wrong, probably not what you want:
    >>> for v in f['PIN_FLD_VALUES']:
    >>>     v
    0
    1

Doing it that way will return the keys, or elem_ids of the BRMArray, which in this case are `0` and `1`.

Instead, you have to use the `.values()` function, like you would on a dict in python:

    >>> for v in f['PIN_FLD_VALUES'].values():
    >>>     v
    {'PIN_FLD_STATUS': 2}
    {'PIN_FLD_STATUS': 4}
    
Likewise, to get the keys and the values, use `.items()`:

    >>> for k, v in f['PIN_FLD_VALUES'].items():
    >>>     k, v
    (0, {'PIN_FLD_STATUS': 2})
    (1, {'PIN_FLD_STATUS': 4})


## Empty Array Behavior

There is some behavior with empty arrays that is important to keep in mind.

In the following example, does anything happen to the C flist?

    c = client()
    f = c.flist()
    f['PIN_FLD_RESULTS'] = {}
    
No, nothing has happened. We have not added any flists at all. However in Python we can access this array:

    ar = f['PIN_FLD_RESULTS']
    
Most importantly to keep in mind, we can check if `PIN_FLD_RESULTS` exists on our flist:

    if 'PIN_FLD_RESULTS' in f:
        print('yes it exists')

However, in fact there is nothing on the C flist at this point, until you add your first flist:

    ar[0] = {'PIN_FLD_POID': '/foo'}

It's worth repeating: the BRMArray class is not implemented as a list, but rather as a dictionary.
Why was this decision made? An array in brm is sparse array where each value is an flist.
You can put an flist at index 2 of an array, and then place another flist on the 9th position, leaving gaps in between.
Due to this sparse nature, it is better to represent it as a dict of keys (elem_ids) to values (flists)

# Logging

`pybrm` integrates with the normal `pinlog` logging that the BRM C API does.

    import logging
    import pybrm
    from pybrm import Client, BRMHandler
    
    # These three are the defaults
    pybrm.pin_err_set_level(pybrm.PIN_ERR_LEVEL_ERROR)
    pybrm.pin_err_set_program('pybrm')
    pybrm.pin_err_set_logfile('default.pinlog')
    
    logging.basicConfig(level=pybrm.brm_to_python_log_level(pybrm.PIN_ERR_LEVEL_ERROR))
    logger = logging.getLogger(__name__)
    logger.addHandler(BRMHandler())
    
    logger.error('This is visible')
    logger.debug('This is not visible')

Note how we are passing through two loggers here, the regular python logger as well as the BRM logger.

Therefore we have to sync the python log level with the BRM log level, 
which is what `pybrm.brm_to_python_log_level` does.

Later on in your program, you can change the logging parameters like the following:

    pybrm.pin_err_set_level(pybrm.PIN_ERR_LEVEL_DEBUG)
    logger.setLevel(pybrm.brm_to_python_log_level(pybrm.PIN_ERR_LEVEL_DEBUG))
    pybrm.pin_err_set_program('new_program_name')
    pybrm.pin_err_set_logfile('new.pinlog')

# Transactions

You can use transactions like the following:

    c = Client()
    t = c.transaction('/poid')
    try:
        f = c.flist()
        f['PIN_FLD_POID'] = '/foo'
        f('PCM_OP_TEST_LOOPBACK')
    except Exception:
        t.rollback()
    else:
        t.commit()

Better yet, use the context manager:

    c = Client()
    with c.transaction('/poid') as t:
        f = c.flist()
        f['PIN_FLD_POID'] = '/foo'
        f('PCM_OP_TEST_LOOPBACK')
        t.commit()

Using the context manager will result in a rollback if a) an exception is raised or b) no commit was issued.

For example, this will rollback, since `commit` was never executed:

    c = Client()
    with c.transaction('/poid') as t:
        f = c.flist()
        f['PIN_FLD_POID'] = '/foo'
        f('PCM_OP_TEST_LOOPBACK')
        # Rollback occurs now, since commit was not invoked.

# Multi Threading

`pybrm` is thread safe, as long as each `Client()`, and all the flists owned by a client, are accessed by a single thread.
Just as with the BRM C API, it is not thread safe to have multiple threads access a single `Client()` or touching flists with shared error buffers.

For example, if you needed to split up some work and run them in multiple threads, each thread must have its own `Client()`:

    import threading
    
    def work(data):
        # do NOT pass a parent flist to a thread; rather serialize it with .asdict()
        with Client() as c:
            flist = c.flist(data)
            out = flist('PCM_OP_TEST_LOOPBACK')
            print(out)
    
    def main():
        with Client() as c:
            flists = [
                c.flist({'PIN_FLD_POID': ('/account', i)})  # account with id = i
                for i in range(10)
            ]
            # do NOT pass parent flists to a thread; serialize it with .asdict() first
            threads = [
                threading.Thread(target=work, args=(flist.asdict(),))  # serialize the flist to a dict
                for flist in flists
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
    

One important fact to keep in mind is that the flists created from a client belong to that client.

You should not pass flists created in one thread to another thread. Instead, you should serialize them to a dictionary and back:

    c = Client()
    c2 = Client()
    f = c.flist()
    f['PIN_FLD_POID'] = '/account'
    data = f.asdict()  # serialize from flist to dict
    f2 = c2.flist(data)  # deserialize from dict to flist

# Miscellaneous

To get the `pin_virtual_time`:

    import pybrm
    print(pybrm.pin_virtual_time())

If you want to set `pin_virtual_time`, you can create a function like the following:

    import subprocess
    from datetime import datetime
    
    def set_pin_virtual_time(time, mode='2'):
        mode = str(mode)
        assert mode in ('0', '1', '2')
        if isinstance(time, datetime):
            time = time.strftime('%m%d%H%M%Y.%S')
        args = ["pin_virtual_time", "-m", mode]
        if mode != "0":
            args.append(time)
        subprocess.run(args)

Please note that this should not ever be run in prod, which is why it is not built into the library.


You can also create an flist from a BRM formatted flist string:

    f = c.flist('''
        # number of field entries allocated 20, used 8
        0 PIN_FLD_POID           POID [0] 0.0.0.1 /account -1 0
        0 PIN_FLD_STATUS         ENUM [0] 1
        0 PIN_FLD_CREATED_T    TSTAMP [0] (1582071028) Tue Feb 18 16:10:28 2020
        0 PIN_FLD_INHERITED_INFO SUBSTRUCT [0] allocated 20, used 2
        1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 0
        1     PIN_FLD_STATUS         ENUM [0] 2
        0 PIN_FLD_EVENT        SUBSTRUCT [0] allocated 20, used 2
        1     PIN_FLD_POID           POID [0] 0.0.0.1 /service 1234 1
        1     PIN_FLD_STATUS         ENUM [0] 3
        0 PIN_FLD_ARGS          ARRAY [4] allocated 20, used 1
        1     PIN_FLD_STATUS         ENUM [0] 4
        0 PIN_FLD_ARGS          ARRAY [16] allocated 20, used 1
        1     PIN_FLD_STATUS         ENUM [0] 5
        0 PIN_FLD_VALUES        ARRAY [0] allocated 20, used 1
        1     PIN_FLD_STATUS         ENUM [0] 6
        0 PIN_FLD_VALUES        ARRAY [1] allocated 20, used 1
        1     PIN_FLD_STATUS         ENUM [0] 7
    ''')

Additionally, you can create serialize an flist to XML, and create an flist via XML:

    xml = f.xml()
    f2 = c.flist(xml)
    
Likewise you can serialize an flist to JSON, and create an flist from JSON

    j = f.json()
    f2 = c.flist(j)



## Python3 Installation

It is easiest to install Miniconda, which contains precompiled Python binaries for both 32 and 64bit.

32 bit (Python 3.7):

    wget https://repo.anaconda.com/miniconda/Miniconda3-4.5.12-Linux-x86.sh

64 bit (Python 3.7):

    wget https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh

To install it, chose a path you want it to be installed on, like `/path/to/miniconda3`

    sh Miniconda3-4.5.12-Linux-x86.sh -b -p /path/to/miniconda3
    rm Miniconda3-4.5.12-Linux-x86.sh

You can alternatively build Python from source which will take up less space than Miniconda.

# Run the tests

The tests require a valid CM up and running. It only calls `PCM_OP_TEST_LOOPBACK`.

cd into the tests directory, and edit pin.conf. Change this line to point to the correct CM:

    - nap cm_ptr ip ${HOSTNAME} ${BRM_CM_PORT}

Additionally, cd into the `pin_conf_test` directory, and do the same for the pin.conf there.

After this, run the tests from inside the `tests/` directory like:

    python3 tests.py

# pin.conf
A `pin.conf` file has to be created in the same directory you run Python from

At a minimum it needs these lines:

    - nap cm_ptr ip ${HOSTNAME} ${BRM_CM_PORT}
    - nap login_type 1
    - nap login_name root.0.0.0.1
    - nap login_pw   password
    - - userid 0.0.0.1 /service/pcm_client 1

You should also include this:

     - - pin_virtual_time ${PIN_HOME}/lib/pin_virtual_time_file
     - - ops_fields_extension_file ${PIN_HOME}/include/custom_ops_dat.dat
     
where `custom_ops_dat.dat` points to your custom opcode file.

Just like with normal BRM C code, you need this file in order to get access to custom fields and opcodes.

# Calling C from Python

Check out the examples/call_c_from_python/ for an example of calling C from Python using ctypes.

# Calling Python from C

Check out the examples/call_python_from_c/ for an example of calling Python from C.

import faulthandler
import operator

faulthandler.enable()
from pybrm.cbrm import _FList, _Client, BRMError
from pybrm.cbrm import pin_virtual_time as _pin_virtual_time, pin_field_of_name, pin_field_get_name, pin_field_get_type
from pybrm.cbrm import pin_err_log_msg, pin_conf, pin_err_set_level as _pin_err_set_level, pin_err_set_logfile as _pin_err_set_logfile, pin_err_set_program
from pybrm.constants import field_by_identifier, field_type_by_identifier, field_name_by_identifier, opcode_by_name, all_flags
from datetime import datetime
from decimal import Decimal
from collections import namedtuple
import functools
import logging
import xml.etree.ElementTree as ET
import json

pin_err_set_program("pybrm")


PIN_FLDT_INT = 1
PIN_FLDT_ENUM = 3
PIN_FLDT_TSTAMP = 8
PIN_FLDT_DECIMAL = 14
PIN_FLDT_STR = 5
PIN_FLDT_POID = 7
PIN_FLDT_ARRAY = 9
PIN_FLDT_SUBSTRUCT = 10
PIN_FLDT_BINSTR = 12
PIN_FLDT_BUF = 6

PIN_ERR_LEVEL_DEBUG = 3
PIN_ERR_LEVEL_WARNING = 2
PIN_ERR_LEVEL_ERROR = 1
PIN_ERR_LEVEL_NONE = 0


# Poid's database will default to the value provided by PCM_CONNECT when it is set on an Flist
Poid = namedtuple('Poid', ('type', 'id', 'revision', 'database'))
Poid.__new__.__defaults__ = (None, -1, 0, None)
Poid.is_type_only = lambda poid: poid.id == -1
Poid.__str__ = lambda poid: f'0.0.0.{poid.database} {poid.type} {poid.id} {poid.revision}'


def pin_virtual_time():
    """Returns the pin_virtual_time of the system, in local time"""
    ts = _pin_virtual_time()
    return datetime.fromtimestamp(ts)


def _check_log_file_is_legal(logfile):
    """If we pass in an illegal log_file, BRM actually segfaults during PCM_CONNECT"""
    try:
        with open(logfile, 'a'):
            pass
    except Exception as ex:
        raise IOError("The logfile cannot be written to: %s" % ex)


def pin_err_set_level(log_level=PIN_ERR_LEVEL_DEBUG):
    """
    Sets the logging level via PIN_ERR_SET_LEVEL
    :param log_level: the BRM logging level:
        pybrm.PIN_ERR_LEVEL_NONE, pybrm.PIN_ERR_LEVEL_ERROR, pybrm.PIN_ERR_LEVEL_WARNING, pybrm.PIN_ERR_LEVEL_DEBUG
    """
    if log_level not in (PIN_ERR_LEVEL_NONE, PIN_ERR_LEVEL_ERROR, PIN_ERR_LEVEL_WARNING, PIN_ERR_LEVEL_DEBUG):
        raise ValueError('Invalid log_level')
    _pin_err_set_level(log_level)


def pin_err_set_logfile(logfile):
    """
    Sets the logfile via PIN_ERR_SET_LOGFILE
    This raises an execption if the path cannot be written
    :param log_file: the path to the log file
    """
    _check_log_file_is_legal(logfile)
    _pin_err_set_logfile(logfile)


class _Transaction:
    """
    A Transaction Wrapper for BRM.

    Don't create this directly; instead use client.transaction(poid='/poid')
    Or, use the context manager:
        with client.transaction(poid='/poid') as trans:
            trans.rollback()

    A client may only have one open transaction at a time.

    Multithreading isn't a good idea; BRM seems to hang once more than a few clients open a transaction
    """
    def __init__(self, client, poid, flags=None):
        """
        Don't invoke this directly, instead use client.transaction()
        :param client: `Client` to maintain the transaction on
        :param poid: the poid of the transaction. It seems this can be any value.
        :param flags: the transactions flags. Defaults to PCM_TRANS_OPEN_READWRITE
        """
        self._transaction_flist = None
        if flags is None:
            flags = ['PCM_TRANS_OPEN_READWRITE']

        flags = _bitwise_or_flags(flags)
        input_flist = client.flist({
            'PIN_FLD_POID': poid
        })

        self._transaction_flist = input_flist('PCM_OP_TRANS_OPEN', flags=flags)

    def commit(self):
        """Commit the transaction"""
        if self._transaction_flist is None:
            raise BRMError("No transaction has started")

        try:
            self._transaction_flist.opcode('PCM_OP_TRANS_COMMIT')
        finally:
            self._transaction_flist = None

    def rollback(self):
        """
        Rollback the transaction

        Will not raise an error if a transaction has already been comitted/rolledback or isn't in progress.
        """
        if self._transaction_flist is None:
            return

        try:
            self._transaction_flist.opcode('PCM_OP_TRANS_ABORT')
        finally:
            self._transaction_flist = None

    def is_open(self):
        """
        Checks if there is currently an open transaction that should be committed or rolled back.
        :return: bool
        """
        return self._transaction_flist is not None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def __del__(self):
        self.rollback()


class Client:
    """
    The Client connection to the CM.

    You must be in a directory with a `pin.conf` file.

    The client will try to connect as soon as you instantiate it with `Client()`
    unless you open it like Client(open=False)
    """
    def __init__(self, open=True):
        """
        Instantiate a Client connection to the CM.

        You can use this in a context manager to ensure the CM closes:

        with Client() as c:
            pass

        :param program: passed to PIN_ERR_SET_PROGRAM
        :param log_file: passed to PIN_ERR_SET_LOGFILE
        :param log_level: passed to PIN_ERR_SET_LOGFILE
        """
        self._transaction = None
        self.database = 1  # this will get set during the call to open() if its not actually 1
        self._client = _Client()
        if open:
            self.open()

    def flist(self, data=None, capsule=None, copy_capsule=True):
        """
        Create an flist and associate it to this client.

        Do not attempt to create an flist via `FList()` - use this `client.flist()` instead.

        :param data:
            if None, returns an empty flist.
            if a dictionary, it will populate the flist with the keys and values on the dict, recursively
            if a string, it will attempt to convert the string into an flist
                The string can be json, xml, or a brm flist string.
                It will attempt to parse it each way, and if only after all three fail will it raise an exception.
        :param capsule:
            Sets the flist to the flistp in the PyCapsule
            This is for advanced users who want to call C from Python or Python from C
            Normally just leave this as None
        :param copy_capsule
            If using `capsule`, this should ALWAYS be True
            It's only False for code coverage
        :return: FList instance
        """
        if capsule is not None:
            _flist = _FList(self._client, False)
            _flist.set_capsule(capsule, copy_capsule)
            return FList(self, _flist=_flist)

        return FList(self, data=data)

    def open(self):
        """
        Opens a connection to the CM.
        A client will connect automatically when instantiated with `Client()`
        unless it is instantiated with Client(open=False)
        """
        try:
            database = self._client.open()
        except BRMError as ex:
            if ex.err in ('PIN_ERR_NAP_CONNECT_FAILED', 'PIN_ERR_CM_ADDRESS_LOOKUP_FAILED', 'PIN_ERR_STREAM_IO'):
                print("Check if CM is up with psme | grep cm\n")
            if ex.err in ('PIN_ERR_INVALID_CONF', 'PIN_ERR_FILE_IO'):
                print("Missing pin.conf file in this directory\n")
            if ex.err == 'PIN_ERR_MISSING_ARG':
                print('pin.conf most likely missing "- nap cm_ptr ip ${HOSTNAME} ${BRM_CM_PORT}"')
            raise ex
        self.database = database

    def close(self):
        """
        Closes a connection to the CM.
        Rolls back any open transaction.
        """
        if self._transaction is not None:
            self._transaction.rollback()

        # self._client won't exist if no pin.conf was set up
        self._client.close() if hasattr(self, '_client') else None

    def is_open(self):
        """
        Checks if the client has an open connection to the CM
        :return: bool
        """
        return self._client.is_open()

    def transaction(self, poid, flags=None):
        """
        Opens a transaction on this client.

        An exception is raised if more than one transaction is opened at a time.

        Use this in a context manager, which will rollback if either an exception occurred
        or if you do not issue `commit`
            client = Client()
            with client.transaction() as t:
                ...
                t.commit()

        :param poid: the transaction poid, can be any value
        :param flags: defaults to PCM_TRANS_OPEN_READWRITE
        :return:
        """
        if self._transaction is not None and self._transaction.is_open():
            raise BRMError("A transaction has already been started, cannot do more than one at the same time")

        self._transaction = _Transaction(client=self, poid=poid, flags=flags)

        return self._transaction

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def search_build_flist(self, template, args, results='*', search_flags=0, is_count_only=False):
        """
        Build a search flist and return it.
        Normally, this is called by the `search` function, although you may use this while debugging
        to confirm that the search flist is built as you intended.
        This function does not execute the PCM_OP_SEARCH opcode. - `search` function will.
        See the docstring in `search` for more information.
        """
        flist = self.flist()
        search_flags = _bitwise_or_flags(search_flags)
        flist['PIN_FLD_POID'] = '/search'
        flist['PIN_FLD_FLAGS'] = search_flags
        flist['PIN_FLD_TEMPLATE'] = template
        iter = args
        if isinstance(args, dict):
            iter = args.items()
            # If its not a dict, assume its a list of tuples with two values

        flist['PIN_FLD_ARGS'] = {
            i: {key: self._search_recurse_args(key, value)}
            for i, (key, value) in enumerate(iter, start=1)
        }

        if results == '*':
            flist['PIN_FLD_RESULTS'] = {'*': {}}
        elif results is None:
            flist['PIN_FLD_RESULTS'] = None
        else:
            # ar = flist['PIN_FLD_RESULTS']['*']
            flist['PIN_FLD_RESULTS'] = {'*': {}}
            self._search_recurse_results(flist['PIN_FLD_RESULTS']['*'], results)
        if is_count_only:
            flist['PIN_FLD_RESULTS'] = None

        return flist

    def _search_recurse_results(self, flist, results):
        if not isinstance(results, dict):
            # results is a set, list, tuple
            results = {k: None for k in results}
        for k, v in results.items():
            if field_type_by_identifier(k) == PIN_FLDT_ARRAY:
                # sub = flist[k]['*']
                flist[k] = {'*': {}}
                if v:
                    self._search_recurse_results(flist[k]['*'], v)
            else:
                flist[k] = v

    def _search_recurse_args(self, key, value):
        if not isinstance(value, dict):
            return value
        result = {}
        for k, v in value.items():
            result[k] = self._search_recurse_args(k, v)
        if field_type_by_identifier(key) == PIN_FLDT_ARRAY:
            result = [result]
        return result

    def search(self, template, args, results='*', search_flags=0, opcode_flags=0, is_count_only=False):
        """
        Convenience wrapper for PCM_OP_SEARCH to conduct searching in BRM.

        :param template: SQL like string for BRM queries
        :param args:
            There are two ways of specifying args, with a dict or list of tuples.
            Dict:
                search(
                    ...,
                    args={
                        'PIN_FLD_USAGE_TYPE': 'FOO',
                        'PIN_FLD_STATUS': 1
                    }
                )
            List of tuples:
                search(
                    ...,
                    args=[
                        ('PIN_FLD_USAGE_TYPE', 'FOO'),
                        ('PIN_FLD_STATUS': 1)
                    ]
                )

            Using a dict here is just syntactic sugar to save a few keystrokes.
            Sometimes you cannot use a dict, for example if you have a template like
                select X from foo where F1 IN (V1, V2, V3)
                In this case, you must use a list of tuples, as a dict cannot have multiple values
                    args = [
                        ('PIN_FLD_USAGE_TYPE': 'FOO'),
                        ('PIN_FLD_USAGE_TYPE': 'BAR')
                    ]
        :param results:
            Results defaults to '*' which will return all the data from the database, which is not recommended.
                Better performance can be achieved by returning only the fields that you need.
            Setting results to None will create a null flist, which is not useful in most situations.
                An exception is when using the PCM_OPFLG_COUNT_ONLY flag,
                however `is_count_only` does this automatically
            Otherwise, set results to a dict, which can be nested with substructures or arrays.

            This returns only the three fields:
                search(
                    ...,
                    results={'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE'}
                )

                Which is identical to:

                search(
                    ...,
                    results={'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_EVENT_TYPE': None, 'PIN_FLD_SERVICE_TYPE': None},
                )

                search(
                    ...,
                    results=['PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE']
                )

            This returns all the fields in the substruct PIN_FLD_INHERITED_INFO
                search(
                    ...,
                    results={'PIN_FLD_INHERITED_INFO'},
                )

                Which is identical to:

                search(
                    ...,
                    results={'PIN_FLD_INHERITED_INFO': {}},
                )

            This returns only the three fields in the substruct PIN_FLD_INHERITED_INFO:
                search(
                    ...,
                    results={'PIN_FLD_INHERITED_INFO': {
                        'PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE'
                    },
                )

                Which is identical to

                search(
                    ...,
                    results={'PIN_FLD_INHERITED_INFO': {
                        'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_EVENT_TYPE': None, 'PIN_FLD_SERVICE_TYPE': None
                    },
                )

            This returns all the fields in the array PIN_FLD_FIELDS array:
                search(
                    ...,
                    results=['PIN_FLD_FIELDS'],
                )

                Which is identical to

                search(
                    ...,
                    results={'PIN_FLD_FIELDS': {}},
                )

            This returns only the three fields in the array PIN_FLD_FIELDS:
                search(
                    ...,
                    results={'PIN_FLD_FIELDS': {
                        ('PIN_FLD_USAGE_TYPE', 'PIN_FLD_EVENT_TYPE', 'PIN_FLD_SERVICE_TYPE')
                    },
                )

        :param search_flags: flags that will go in the search_flist['PIN_FLD_FLAGS']
        :param opcode_flags: flags that will be called in the execution of the opcode
        :param is_count_only: convenience wrapper for PCM_OPFLG_COUNT_ONLY
            Setting this to true will take care of the search flistp, notably by setting PIN_FLD_RESULTS to a null array
            As well as setting the search opcode flags to PCM_OPFLG_COUNT_ONLY
            In addition it returns the actual count, not an output flist.
        :return:
            output flist of the PCM_OP_SEARCH opcode
            unless is_count_only=True, which will return an int instead.
        """
        flist = self.search_build_flist(template, args, results, search_flags, is_count_only)

        if is_count_only:
            opcode_flags = _bitwise_or_flags([opcode_flags, 'PCM_OPFLG_COUNT_ONLY'])

        out = flist('PCM_OP_SEARCH', opcode_flags)

        if is_count_only:
            return next(out['PIN_FLD_RESULTS'].keys())

        return out

    def __del__(self):
        self.close()

    def capsule(self):
        """
        Returns a PyCapsule that wraps the ctxp pointer for this client.
        This is for advanced usage only, if you need to call external C functions using ctypes.
        Check the docstring in `Flist.capsule`
        :return: PyCapsule
        """
        return self._client.capsule()

    def ebufp_capsule(self):
        """
        Returns a PyCapsule that wraps the ebufp error buffer pointer for this client.
        This is for advanced usage only, if you need to call external C functions using ctypes.
        Check the docstring in `Flist.capsule`
        Moreover, if the External C function you call takes an ebufp, it's possible it can set the error buffer
        but not clear it. If that happens, the next python call will fail, since every python call checks the error
        buffer.
        Make sure to call `raise_ebuf_error` after calling a ctypes function that takes an ebufp.
        :return: PyCapsule
        """
        return self._client.ebufp_capsule()

    def raise_ebuf_error(self):
        """
        Raises an exception if the ebuf is full, and resets the ebuf.
        This is only useful if you are calling an external C function via ctypes with the `ebufp_capsule`.
        If the external C function sets the buffer without clearing it, the next call in Python will fail.
        You should always call this after calling a ctypes function that takes an ebufp.

        clib.foo(bar, ebufp)
        try:
            c.raise_ebuf_error()
        except BRMError as ex:
            printf("ebuf is now clear")
        :return:
        """
        self._client.raise_ebuf_error()

    def _set_ebuf_error(self):
        """
        Don't use this. This is only used for testing raise_ebuf_error.
        :return:
        """
        self._client.set_ebuf_error()


class FList:
    __slots__ = ['client', '_flist', '_virtual_arrays']
    """
    Wrapper for a BRM flist
    To instantiate, call `client.flist()`; do not call `FList()` directly
    """
    def __init__(self, client, data=None, _flist=None):
        """
        Do not call FList(...) directly, instead call `client.flist(...)`
        :param client: the `Client` which owns this flist
        :param data:
            if None, returns an empty flist.
            if a dictionary, it will populate the flist with the keys and values on the dict, recursively
            if a string, it will attempt to convert the string into an flist
                The string can be json, xml, or a brm flist string.
                It will attempt to parse it each way, and if only after all three fail will it raise an exception.

        :param _flist: a C wrapper flist. Calling code should not use this.
        """
        self.client = client

        """
        _virtual_arrays
        
        Remember that an "array" in BRM is not a real thing.
        If you do:
            f = c.flist()
            f['PIN_FLD_RESULTS'] = {}
        
        Nothing actually happened to the flist on the inside, since you haven't put any flists on that array.
        
        The point of _virtual_arrays is to record which fields on this parent flist that an "empty" or "virtual array"
        have been created, and to handle KeyErrors and __contains__ in a way that makes sense from a Python perspective.
        
        This will raise a KeyError:
            f = c.flist()
            ar = f['PIN_FLD_RESULTS']  # nothing in _virtual_arrays
        
        This will not:
            f = c.flist()
            f['PIN_FLD_RESULTS'] = {}  # entry added to _virtual_arrays
            ar = f['PIN_FLD_RESULTS']  # dont raise KeyError because entry is in _virtual_arrays
            'PIN_FLD_RESULTS' in ar  # returns True, HOWEVER there are no actual subflists on the c flist.
        
        In the above example, `f['PIN_FLD_RESULTS'] = {}`, an entry is added into _virtual_arrays for PIN_FLD_RESULTS
        This way, the next time the user does an access, like `ar = f['PIN_FLD_RESULTS']`, we don't raise a KeyError.
        As soon as an flist is added to the array, the entry will be removed from _virtual_arrays.
        Likewise, if all the subflists on the array are deleted, the entry will be added back to _virtual_arrays.
        
        """
        self._virtual_arrays = set()

        if _flist is not None:
            self._flist = _flist
            return

        if isinstance(data, str):
            # Here we will try to parse json, xml, or regular flist string
            data = self._parse_flist_data(data)
            if data is None:
                # It's either a flist str, or xml.
                # json will return a dict that is populated a few lines down
                return

        self._flist = _FList(self.client._client, True)

        if isinstance(data, (dict, FList)):
            for k, v in data.items():
                self[k] = v

        elif data is not None:
            # E.g if it is a set, list, tuple then default values to None
            # In particular, client.search() makes use of this for its syntactic sugar
            for k in data:
                self[k] = None

    def _parse_flist_data(self, data):
        """
        For convenience, this will attempt to parse the input as json, xml, and a BRM flist string.
        Only after failing all three will it raise an exception.

        If the data was in json, this returns a dict. Calling code must populate the flist.

        Otherwise, it returns None, and calling code should return immedaitely.

        :param data: json, xml, or brm flist string representing an flist
        :return: None or a dict
        """
        try:
            data = json.loads(data)
        except ValueError:
            pass
        else:
            return data

        try:
            data = ET.fromstring(data)
        except ET.ParseError:
            pass
        else:
            self._flist = _FList(self.client._client, True)
            self._flist_from_xml(self, data)
            return

        try:
            self._flist = _FList(self.client._client, True, data)
        except BRMError as ex:
            if ex.err != 'PIN_ERR_BAD_ARG':
                raise ex
            is_error = True
        else:
            return

        if is_error:
            # The data string failed to be parsed in json, xml, or flist string format
            raise ValueError("Illegal flist string")

    def _flist_from_xml(self, f, root):
        """
        Recursively iterates over an xml root and populates the flist

        Note that when BRM serializes an flist into XML, it serializes null substructures and empty structures
        identically. So there is no way to know if it was null or empty. This assumes the common case
        and deserializes to an empty substructure.

        This function cannot handle data serialized by PIN_XML_BY_SHORT_NAME.
        If it's just out of box BRM fields, it would be trivial to add PIN_FLD_*_T where * is the short name
        However with custom fields, I'm not sure how to find the prefix.

        :param f: flist to populate on
        :param root: xml root
        """
        for element in root:
            # This handles both cases of PIN_XML_BY_TYPE and PIN_XML_BY_NAME
            name = element.attrib.get('name', element.tag)
            field_type = field_type_by_identifier(name)
            if field_type == PIN_FLDT_SUBSTRUCT:
                f[name] = {}  # Remember that BRM will set null flists to empty flists when it serializes to xml
                substruct = f[name]
                self._flist_from_xml(substruct, element)
            elif field_type == PIN_FLDT_ARRAY:
                if name not in f:
                    f[name] = {}
                f[name][int(element.attrib['elem'])] = {}
                substruct = f[name][int(element.attrib['elem'])]
                self._flist_from_xml(substruct, element)
            else:
                f[name] = element.text

    def asdict(self):
        """
        Serialize the flist to a dictionary

        Especially useful if you need to communicate flists between different threads.
        Each client may only have one thread associated to it, and you cannot transfer
            and flist from one client to another.

        Instead, the thread can serialize the flist to a dict and then pass it to another thread.
        """
        d = {}
        for k, v in self.items():
            if isinstance(v, FList):
                d[k] = v.asdict()
            elif isinstance(v, BRMArray):
                d[k] = {elem_id: f.asdict() if f is not None else None for elem_id, f in v.items()}
            else:
                d[k] = v
        return d

    def _json_formatted(self):
        """Recurvisely formats this flist to JSON"""
        d = {}
        for k, v in self.items():
            if isinstance(v, FList):
                d[k] = v._json_formatted()
            elif isinstance(v, BRMArray):
                d[k] = {elem_id: f._json_formatted() if f is not None else None for elem_id, f in v.items()}
            elif isinstance(v, Poid):
                d[k] = str(v)
            elif isinstance(v, datetime):
                d[k] = int(v.timestamp())
            else:
                d[k] = v
        return d

    def json(self):
        """
        Serialize the flist to a json string.

        Unlike BRM's xml function, this will disambiguate between an empty substruct and a NULL substruct.

        :param timestamp_format: if None, serializes PIN_FLDT_TSTAMP to float
            Otherwise, a datetime format specifier, like '%Y-%m-%dT%H:%M:%S.%f' may convert it to a string
        :return: json serialized string
        """
        d = self._json_formatted()

        return json.dumps(d)

    # getters

    def __getitem__(self, item):
        """Get a value from this flist by field_name"""
        return self._get_field(item)

    def __getattr__(self, name):
        """Get a field value from this flist by field_name"""
        try:
            return self._get_field(name)
        except KeyError as ex:
            raise AttributeError

    def get(self, name, default=None):
        """
        Get the value of a field off an flist.
        This will return None or `default` if the field does not exist.
        :param name: The name of the field
        :param default: value to return if the field does not exist
        :return:
        """
        value = self._get_field(name, optional=1)
        if value is None:
            value = default
        return value

    def _get_field(self, name, optional=0):
        field_number = field_by_identifier(name)
        field_type = field_type_by_identifier(name)

        try:
            if field_type == PIN_FLDT_POID:
                return self._get_poid(field_number, optional)
            elif field_type == PIN_FLDT_STR:
                return self._get_str(field_number, optional)
            elif field_type == PIN_FLDT_INT:
                return self._get_int(field_number, optional)
            elif field_type == PIN_FLDT_ENUM:
                return self._get_enum(field_number, optional)
            elif field_type == PIN_FLDT_TSTAMP:
                return self._get_tstamp(field_number, optional)
            elif field_type == PIN_FLDT_DECIMAL:
                return self._get_decimal(field_number, optional)
            elif field_type == PIN_FLDT_SUBSTRUCT:
                return self._get_flist(field_number, optional)
            elif field_type == PIN_FLDT_ARRAY:
                return self._get_array(field_number, optional)
            elif field_type == PIN_FLDT_BINSTR:
                return self._get_binstr(field_number, optional)
            elif field_type == PIN_FLDT_BUF:
                return self._get_buf(field_number, optional)
            else:
                raise NotImplementedError('We do not support this data type %i for field %s' % (field_type, name))
        except BRMError as ex:
            if ex.err == 'PIN_ERR_NOT_FOUND':
                raise KeyError('Field %s not found' % field_name_by_identifier(name))
            raise ex

    def _get_poid(self, name, optional=0):
        poid = self._flist.get_poid(field_by_identifier(name), optional)
        if poid is not None:
            poid = Poid(*poid)

        return poid

    def _get_int(self, name, optional=0):
        return self._flist.get_int(field_by_identifier(name), optional)

    def _get_enum(self, name, optional=0):
        return self._flist.get_enum(field_by_identifier(name), optional)

    def _get_str(self, name, optional=0):
        return self._flist.get_str(field_by_identifier(name), optional)

    def _get_binstr(self, name, optional=0):
        return self._flist.get_binstr(field_by_identifier(name), optional)

    def _get_buf(self, name, optional=0):
        return self._flist.get_buf(field_by_identifier(name), optional)

    def _get_tstamp(self, name, optional=0):
        ts = self._flist.get_tstamp(field_by_identifier(name), optional)
        if ts is None:
            return None
        return datetime.fromtimestamp(ts)

    def _get_decimal(self, name, optional=0):
        return self._flist.get_decimal(field_by_identifier(name), optional)

    def _get_flist(self, name, optional=0):
        _flist = self._flist.get_flist(field_by_identifier(name), optional)
        if _flist is None:
            return None
        return FList(self.client, _flist=_flist)

    def _get_array(self, name, optional=0):
        exists = name in self
        if optional == 0 and not exists and field_by_identifier(name) not in self._virtual_arrays:
            raise KeyError(f'Field {field_name_by_identifier(name)} not found')
        if optional == 1 and not exists and field_by_identifier(name) not in self._virtual_arrays:
            return None

        return BRMArray(parent_flist=self, parent_name=name, cflist=self._flist)

    # Setters

    def __setitem__(self, item, value):
        """Sets value onto this flist by field_name"""
        return self._set_field(item, value)

    def __setattr__(self, name, value):
        """Sets value onto this flist by field_name"""
        try:
            field_number = field_by_identifier(name)
            return self._set_field(name, value)
        except KeyError as ex:
            pass
        super().__setattr__(name, value)

    def _set_field(self, name, value):
        field_number = field_by_identifier(name)
        field_type = field_type_by_identifier(name)

        try:
            if field_type == PIN_FLDT_POID:
                return self._set_poid(field_number, value)
            elif field_type == PIN_FLDT_STR:
                return self._set_str(field_number, value)
            elif field_type == PIN_FLDT_TSTAMP:
                return self._set_tstamp(field_number, value)
            elif field_type == PIN_FLDT_INT:
                return self._set_int(field_number, value)
            elif field_type == PIN_FLDT_ENUM:
                return self._set_enum(field_number, value)
            elif field_type == PIN_FLDT_DECIMAL:
                return self._set_decimal(field_number, value)
            elif field_type == PIN_FLDT_ARRAY:
                return self._set_array(field_number, value)
            elif field_type == PIN_FLDT_SUBSTRUCT:
                return self._set_substr(field_number, value)
            elif field_type == PIN_FLDT_BINSTR:
                return self._set_binstr(field_number, value)
            elif field_type == PIN_FLDT_BUF:
                return self._set_buf(field_number, value)
            else:
                raise NotImplementedError('We do not support this data type yet: %s' % field_type)
        except BRMError as ex:
            # BRM actually won't raise an error if you set to a field that doesn't exist or is a wrong data type
            # This will never execute, but perhaps this issue will be resolved in a later BRM release
            if ex.err == 'PIN_ERR_NOT_FOUND':
                raise KeyError('Field %s not found' % field_name_by_identifier(name))
            raise ex

    def _set_poid(self, name, value, id=-1, revision=0, database=None):
        poid_string = None
        if isinstance(value, tuple):
            # Short cut to allow the user to do:
            # f['PIN_FLD_POID'] = '/account',
            # f['PIN_FLD_POID'] = '/account', 100
            # f['PIN_FLD_POID'] = '/account', 100, 1
            # f['PIN_FLD_POID'] = '/account', 100, 1, 2
            value += tuple(x for i, x in enumerate((id, revision, database)) if i >= len(value) - 1)
            if len(value) != 4:
                raise TypeError("Expecting tuple length of less than 5")
            value = Poid(*value)
        if isinstance(value, Poid):
            value, id, revision, database, = value.type, value.id, value.revision, value.database
        else:
            if not isinstance(value, str) and value is not None:
                raise TypeError('value must be Poid, tuple, str, or None')

        if isinstance(value, str) and len(value.split()) == 4:
            # value is a real Poid string like 0.0.0.1 /account -1 0
            database, value, id, revision = value.split()

        if database is None:
            database = self.client.database

        if value is not None:
            if value[0] in '0123456789':
                # I think types should start with / anyways, could simply raise error here for that
                raise ValueError("PIN_POID_FROM_STR cannot take a type starting with integer: %s" % value)
            if isinstance(database, int):
                database = '0.0.0.%i' % database
            poid_string = f'{database} {value} {id} {revision}'

        try:
            if poid_string is not None:
                self._flist.set_poid(field_by_identifier(name), value=poid_string)
            else:
                self._flist.set_poid(field_by_identifier(name))
        except BRMError as ex:
            if ex.err == 'PIN_ERR_BAD_ARG':
                raise ValueError('Invalid POID string: %s' % poid_string)
            raise ex

    def _set_str(self, name, value):
        if not isinstance(value, str) and value is not None:
            value = str(value)

        if value is not None:
            self._flist.set_str(field_by_identifier(name), value=value)
        else:
            self._flist.set_str(field_by_identifier(name))

    def _set_binstr(self, name, value):
        if value is not None:
            self._flist.set_binstr(field_by_identifier(name), value=value)
        else:
            self._flist.set_binstr(field_by_identifier(name))

    def _set_buf(self, name, value):
        if value is not None:
            self._flist.set_buf(field_by_identifier(name), value=value)
        else:
            self._flist.set_buf(field_by_identifier(name))

    def _set_tstamp(self, name, value):
        if isinstance(value, datetime):
            value = int(value.timestamp())

        if value is not None:
            # This will truncate floats which is OK because time date type is time_t
            try:
                value = int(value)
            except ValueError:
                raise TypeError('Expected int not %s' % value)

        if value is not None:
            self._flist.set_tstamp(field_by_identifier(name), value=value)
        else:
            self._flist.set_tstamp(field_by_identifier(name))

    def _set_int(self, name, value):
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                try:
                    # This has one purpose: f['PIN_FLD_FLAGS'] = 'SRCH_EXACT'
                    # This will attempt to find the string from the all_flags dict
                    value = all_flags[value]
                except KeyError:
                    raise TypeError('Expected int or a string flag, not %s' % value)

        if value is not None:
            try:
                self._flist.set_int(field_by_identifier(name), value=value)
            except OverflowError:
                raise OverflowError("BRM's int data type is 32 bits, you provided too big of an integer")
        else:
            self._flist.set_int(field_by_identifier(name))

    def _set_enum(self, name, value):
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise TypeError('Expected int not %s' % value)

        if value is not None:
            self._flist.set_enum(field_by_identifier(name), value=value)
        else:
            self._flist.set_enum(field_by_identifier(name))

    def _set_decimal(self, name, value):
        if isinstance(value, str):
            try:
                float(value)
            except ValueError:
                raise TypeError('expecting a float or decimal, not %s' % value)

        if isinstance(value, (int, float, Decimal)):
            # `_flist.set_decimal` expects a char *
            value = str(value)

        if value is not None:
            self._flist.set_decimal(field_by_identifier(name), value=value)
        else:
            self._flist.set_decimal(field_by_identifier(name))

    def _set_flist_on_array(self, name, value, elem_id):
        if value is not None and not isinstance(value, FList):
            value = self.client.flist(data=value)

        func = self._flist.set_flist_on_array
        args = (field_by_identifier(name), elem_id)
        if elem_id in ('*', 'PIN_ELEMID_ANY', -1):
            func = self._flist.set_flist_on_array_any
            args = (field_by_identifier(name),)

        kwargs = dict()
        if value is not None:
            kwargs = dict(value=value._flist)

        func(*args, **kwargs)

    def _set_array(self, name, value):
        self._drop_array(name, optional=1)

        if value is None:
            self._set_flist_on_array(name, value=None, elem_id=0)
            self._virtual_arrays.discard(field_by_identifier(name))

        elif len(value) == 0:
            self._virtual_arrays.add(field_by_identifier(name))

        elif isinstance(value, list):
            for elem_id, val in enumerate(value):
                f = self.client.flist(data=val)
                self._set_flist_on_array(name, value=f, elem_id=elem_id)

            self._virtual_arrays.discard(field_by_identifier(name))

        elif isinstance(value, BRMArray):
            for elem_id, f in value.items():
                self._set_flist_on_array(name, value=f, elem_id=elem_id)

            self._virtual_arrays.discard(field_by_identifier(name))

        elif isinstance(value, dict):
            """
            Edge case with PIN_ELEMID_ANY:
            Need to place PIN_ELEMID_ANY on first, before all the other keys.
            Otherwise, if PIN_ELEMID_ANY is placed on later, it will overwrite the first key.
            
            If the user tries adding multiple PIN_ELEMID_ANY's, just take one of them while removing the others.
            """
            any_flist = None
            for elem_id in ('*', 'PIN_ELEMID_ANY', -1, "-1"):
                any_flist = value.pop(elem_id, any_flist)

            if any_flist is not None:
                f = self.client.flist(data=any_flist)
                self._set_flist_on_array(name, value=f, elem_id='*')

            for elem_id, val in value.items():
                if val is not None:
                    val = self.client.flist(data=val)
                # converting this to json gives string values for the elem_ids because keys must be string in json
                # so use int(elem_id) here in case it comes from a json string
                if isinstance(elem_id, str) and elem_id.isdigit():
                    elem_id = int(elem_id)
                self._set_flist_on_array(name, value=val, elem_id=elem_id)

            self._virtual_arrays.discard(field_by_identifier(name))
        else:
            raise TypeError('Expecting a BRMArray, not %s' % value)

    def _set_substr(self, name, value):
        if value is not None and not isinstance(value, FList):
            value = self.client.flist(data=value)

        if value is None:
            self._flist.set_substr(field_by_identifier(name))
        else:
            self._flist.set_substr(field_by_identifier(name), value=value._flist)

    def copy(self):
        """
        Creates a copy of this flist
        :return: FList
        """
        return FList(self.client, _flist=self._flist.copy_flist())

    def sort(self, field, sort_keys=None, sort_default=0):
        """
        Sorts an array on this flist

        :param field: the field of the array to sort
        :param sort_keys: the keys in the array to sort
        :param sort_default: the BRM sort default behavior (-1, 0, 1)
        """
        if sort_keys is None:
            raise ValueError('Provide at least one sort key')

        if isinstance(sort_keys, str):
            sort_keys = [sort_keys]

        sort_flist = self.client.flist()

        sort_flist[field] = [
            {sort_key: None}
            for sort_key in sort_keys
        ]

        self._flist.sort_flist(sort_flist._flist, sort_default)

    def sort_reverse(self, field, sort_keys=None, sort_default=0):
        """
        Sorts an array on this flist in reverse order

        :param field: the field of the array to sort
        :param sort_keys: the keys in the array to sort
        :param sort_default: the BRM sort default behavior (-1, 0, 1)
        """
        if sort_keys is None:
            raise ValueError('Provide at least one sort key')

        if isinstance(sort_keys, str):
            sort_keys = [sort_keys]

        sort_flist = self.client.flist()

        sort_flist[field] = [
            {sort_key: None}
            for sort_key in sort_keys
        ]

        self._flist.sort_reverse_flist(sort_flist._flist, sort_default)

    def opcode(self, code, flags=None, reference=False):
        """
        Calls an opcode for this flist
        You can also just do `flist('PCM_OP_TEST_LOOPBACK')` instead of `flist.opcode('PCM_OP_TEST_LOOPBACK')`
        :param code: the opcode to execute
        :param flags: the opcode flags, may be a string or a list/tuple of strings
        :param reference: if False, the opcode is executed by passing a copy of the input flist; e.g PCM_OP
            if True, the opcode is executed by passing a reference to the input flist; e.g. PCM_OPREF
        :return:
        """
        if isinstance(code, str):
            try:
                code = opcode_by_name(code)
            except KeyError:
                raise KeyError("No opcode found for %s" % code)

        flags = _bitwise_or_flags(flags)

        c_flist = self._flist.opcode(code, flags, reference)

        return FList(self.client, _flist=c_flist)

    def __call__(self, code, flags=None, reference=False):
        """
        Allows you to call an opcode via `flist('PCM_OP_TEST_LOOPBACK')`
        instead of `flist.opcode('PCM_OP_TEST_LOOPBACK')
        """
        return self.opcode(code, flags=flags, reference=reference)

    def update(self, other):
        """
        Adds the keys on the other flist to this flist, and overwites it it already exists
        This is similar to PIN_FLIST_OONCAT, except that PIN_FLIST_CONCAT has a bug where it will just duplicate
        the fields if they already exist, resulting in strange behavior.
        If you really need this behavior, you can use `_concat` but it is unlikely you need this.

        You can also + two flists together. It results in a brand new flist, and doesn't mutate the original flists.

        """
        if other is not None and not isinstance(other, FList):
            other = self.client.flist(data=other)

        for k, v in other.items():
            if isinstance(v, (FList, BRMArray)):
                self[k].update(v)
            else:
                self[k] = v

    def __add__(self, other_flist):
        """
        Returns a new flist that is the result of `other_flist` updated onto this flist
        :param other_flist:
        :return:
        """
        ret = self.copy()
        ret.update(other_flist)
        return ret


    def _concat(self, other_flist):
        """
        Do not use this - use `update` instead.
        Concatenates `other_flist` onto this flist via PIN_FLIST_CONCAT
        PIN_FLIST_CONCAT has a bug where it will duplicate fields if both flist have the same field
        `update` doesn't do this.
        """
        self._flist.concat(other_flist._flist)


    def count(self, recursive=False):
        """
        Returns the count of the items on this flist.

        :param recursive: set to True to count all the items in substructures and arrays
        :return:
        """
        # PIN_FLIST_COUNT has a bug, where if you use PIN_ELEM_FLD_SET to place an item on the array,
        # PIN_FLIST_COUNT will then return the recursive count, instead of the top-level count.
        # As a workaround, just return the count of the keys on this flist.
        c = len([k for k in self.keys()])
        if not recursive:
            return c

        for name, field in self.items():
            if isinstance(field, FList):
                c += field.count(recursive=True)

            if isinstance(field, BRMArray):
                c += field.count(recursive=True)

        return c

    def __len__(self):
        """Return the non-recursive count of this flist"""
        return self.count()

    def __iter__(self):
        yield from self._flist.init_iter()

    def __dir__(self):
        return super().__dir__() + list(self.keys())

    def items(self):
        """Returns the (key, values) of this flist"""
        for name in self:
            yield name, self._get_field(name)

    def keys(self):
        """Returns the field names of this flist"""
        for name in self:
            yield name

    def values(self):
        """Return the values of thist flist"""
        for name in self:
            yield self._get_field(name)

    def __delitem__(self, item):
        """Deletes the field_name from this flist"""
        field_type = field_type_by_identifier(item)
        if field_type == PIN_FLDT_ARRAY:
            return self._drop_array(item)
        else:
            return self._drop_field(item)

    def __delattr__(self, item):
        """Deletes the field_name from this flist"""
        if item in self:
            return self.__delitem__(item)
        else:
            return self.super(item)

    def _drop_field(self, name, elem_id=0, optional=0):
        """
        Drops a field from an flist.
        Instead, use `del flist['PIN_FLD_POID']` which calls this.
        :param name: The name of the field to drop
        :param elem_id: for non-array fields, this should always be 0. For arrays, this is the elem_id.
        :param optional: 0 for optional, 1 for not optional
        :return:
        """
        field_number = field_by_identifier(name)
        try:
            return self._flist.drop_field(field_number, elem_id, optional)
        except BRMError as ex:
            if ex.err == 'PIN_ERR_NOT_FOUND':
                if name not in self:
                    # We are calling _drop_field on an flist for a field that doesn't exist
                    raise KeyError("Field %s not found" % field_name_by_identifier(name))
                else:
                    # We are calling _drop_field on an BRMArray for an flist elem_id that doesn't exist.
                    raise KeyError("elem_id %i not in range" % elem_id)
            raise ex

    def _drop_array(self, name, optional=0):
        """
        Drops an array from an flist
        Instead, use `del flist['PIN_FLD_ARGS']`
        :param name: name of the field to drop
        :param optional:0 for optional, 1 for not optional
        """
        field_number = field_by_identifier(name)
        deleted_count = self._flist.drop_array(field_number)

        # optional is

        if not deleted_count and field_number not in self._virtual_arrays and not optional:
            raise KeyError("Field %s not found" % field_name_by_identifier(name))

        self._virtual_arrays.discard(field_number)

        return deleted_count

    def pop(self, item, default=None):
        """Pops a field from the flist"""
        val = default
        if item in self:
            val = self[item]
            del self[item]

        return val

    def clear(self):
        """Removes everything from ths flist"""
        for k in self:
            # This is safe to delete while iterating
            # because FListIterator pre-fetches the entire list of keys
            del self[k]

    def __str__(self):
        """Return the string representation of an flist"""
        return str(self._flist)

    def __repr__(self):
        return repr(self.asdict())

    def __contains__(self, key):
        field_number = field_by_identifier(key)
        return self._flist.does_field_exist(field_number) or field_number in self._virtual_arrays

    def xml(self, flags=None, root_element_name=None):
        """Returns an xml representation of the flist"""
        if flags is None:
            flags = ['PIN_XML_BY_TYPE']

        flags = _bitwise_or_flags(flags)

        if root_element_name is not None:
            return self._flist.xml(flags, root_element_name)

        return self._flist.xml(flags)

    def str_compact(self):
        """Returns a compact string representation of this flist"""
        return self._flist.str_compact()

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        if not isinstance(other, FList):
            other = self.client.flist(data=other)
        for k in self:
            if k not in other:
                return False

            if self[k] != other[k]:
                return False

        return True

    def capsule(self, copy_capsule=True):
        """
        Return a PyCapsule wrapping the flistp pointer for this FList.

        The name of the PyCapsule is `pybrm.flistp`.

        This is for advanced users who want to either:
            Invoke a Python function from a C application
            Invoke a C function from Python using ctypes

            Be careful here; you are now responsible for managing memory. If used incorrect, it will segfault.

        Invoking a Python script from a C application
            WARNING: is_copy MUST be True in this case. Otherwise it will memory leak.

            Check the examples/call_python_from_c for a comprehensive example.


        Invoking a C function from Python using ctypes
            WARNING: is_copy SHOULD be False in this case. Otherwise the C functions you call can not mutate the flistp.

            Check the examples/call_c_from_python for a comprehensive example.

        :return: PyCapsule
        """
        return self._flist.capsule(copy_capsule)


class BRMArray:
    """
    A wrapper for an array of flists. Do not call this directly.
    Instead, create one one an flist, and then access it later.

        f = c.flist()
        f['PIN_FLD_ARGS'] = {}
        f['PIN_FLD_ARGS'][0] = {'PIN_FLD_STATUS': 1}
        ar = f['PIN_FLD_ARGS']

    A BRMArray can be better understood as a dict/Hash Map of elem_ids to flists
    Try to not think of a BRMArray as a list/array.
    The elem_ids/keys are sparse, and the values are always flists
    """
    def __init__(self, parent_flist, parent_name, cflist):
        self._parent_flist = parent_flist  # The Python Flist
        self._parent_name = parent_name  # The field number of the parent field
        self._cflist = cflist  # The C Flist

    def __len__(self):
        """Return the number of flists in this array"""
        return self.count()

    def __bool__(self):
        """
        Normally, if len(self) > 1 this returns True
        However, if there is only 1 flist on the array, and the flist is a Null flist
            return False
        One confusing part is that if there are two or more NULL flists on this array, it returns True
        The reason is because we don't want to iterate through all the values to check if they are all not null
        The common case for a "null array" is an array with a single Null flist
        :return:
        """
        count = self.count()
        if count > 1:
            return True
        if count == 1 and next(self.values()) is not None:
                return True
        return False

    def __iter__(self):
        yield from self._cflist.array_init_iter(field_by_identifier(self._parent_name))

    def __contains__(self, elem_id):
        field_number = field_by_identifier(self._parent_name)
        if elem_id in ('*', 'PIN_ELEMID_ANY', -1):
            elem_id = -1

        return self._cflist.does_flist_exist_on_array(field_number, elem_id)

    def _get_array_flist(self, elem_id, optional=0):
        if elem_id in ('*', 'PIN_ELEMID_ANY', -1):
            _flist = self._cflist.get_any_array_flist(field_by_identifier(self._parent_name), optional)
        else:
            _flist = self._cflist.get_array_flist(field_by_identifier(self._parent_name), elem_id, optional)

        if _flist is None:
            return None

        return FList(self._parent_flist.client, _flist=_flist)

    def items(self):
        """Returns the (elem_id, flist) items from this array"""
        for elem_id in self:
            yield (elem_id, self._get_array_flist(elem_id))

    def values(self):
        """Returns the flists from this array"""
        for elem_id in self:
            yield self._get_array_flist(elem_id)

    def keys(self):
        """Returns the elem_ids from this array"""
        yield from self

    def pop(self, elem_id, default=None):
        """Pops an flist off the array by elem_id"""
        val = default
        if elem_id in self:
            val = self[elem_id]
            del self[elem_id]
        return val

    def clear(self):
        """Removes all the flists from this array"""
        for elem_id in self:
            # This is safe to delete while iterating
            # because BRMArrayIterator pre-fetches the entire list of keys
            del self[elem_id]

    def count(self, recursive=False):
        """
        Returns the count of this array
        :param recursive: if true, counts all the items in the flists as well as the number of flists
        :return: int
        """
        if not recursive:
            return self._cflist.array_count(field_by_identifier(self._parent_name))

        return sum([flist.count(recursive=True) if flist is not None else 1 for flist in self.values()])

    def __setitem__(self, elem_id, value):
        """Copy an flist into the array and this index"""
        self._parent_flist._set_flist_on_array(self._parent_name, value, elem_id)
        self._parent_flist._virtual_arrays.discard(field_by_identifier(self._parent_name))

    def _get(self, elem_id, optional=0):
        try:
            flist = self._get_array_flist(elem_id, optional=optional)
        except BRMError as ex:
            # BRM actually won't raise an error if you set to a field that doesn't exist or is a wrong data type
            # This will never execute, but perhaps this issue will be resolved in a later BRM release
            if ex.err == 'PIN_ERR_NOT_FOUND':
                raise KeyError('elem_id %s not found' % elem_id)
            raise ex

        return flist

    def get(self, elem_id, default=None):
        flist = self._get(elem_id, optional=1)
        return flist or default

    def __getitem__(self, elem_id):
        return self._get(elem_id, optional=0)

    def __delitem__(self, elem_id):
        f = self._parent_flist._drop_field(self._parent_name, elem_id)
        if len(self) == 0:
            self._parent_flist._virtual_arrays.add(field_by_identifier(self._parent_name))
        return f

    def __str__(self):
        flist = self._parent_flist.client.flist()
        flist[self._parent_name] = self
        return str(flist)

    def __repr__(self):
        flist = self._parent_flist.client.flist()
        flist[self._parent_name] = self
        return repr(flist.asdict())

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for elem_id in self:
            if elem_id not in other:
                return False

            if self[elem_id] != other[elem_id]:
                return False

        return True

    def update(self, other):
        """Similar to concat, except does not duplicate keys on the flist"""
        if isinstance(other, list):
            other = {elem_id: flist for elem_id, flist in enumerate(other)}

        for elem_id, flist in other.items():
            self[elem_id] = flist


def _bitwise_or_flags(flags):
    if flags is None:
        flags = []

    if isinstance(flags, (str, int)):
        flags = [flags]

    try:
        flags = [all_flags[flag] if isinstance(flag, str) else flag for flag in flags]
    except KeyError:
        raise KeyError("No flag found for %s, check pybrm/fields.py" % flags)

    # This will bit wise or each flag into one result, or return 0 if no flags are given
    flags = functools.reduce(lambda a, b: operator.ior(a, b), flags, 0)

    return flags


_python_to_brm_level = {
    logging.DEBUG: PIN_ERR_LEVEL_DEBUG,
    logging.INFO: PIN_ERR_LEVEL_DEBUG,
    logging.WARNING: PIN_ERR_LEVEL_WARNING,
    logging.ERROR: PIN_ERR_LEVEL_ERROR,
    logging.CRITICAL: PIN_ERR_LEVEL_ERROR,
}

_brm_to_python_level = {
    PIN_ERR_LEVEL_DEBUG: logging.DEBUG,
    PIN_ERR_LEVEL_WARNING: logging.WARNING,
    PIN_ERR_LEVEL_ERROR: logging.ERROR
}


def brm_to_python_log_level(brm_log_level):
    """
    Converts the BRM log level to the Python logging module's log level.
    :param brm_log_level:
    :return:
    """
    try:
        return _brm_to_python_level[brm_log_level]
    except KeyError:
        raise KeyError(f'{brm_log_level} is an invalid BRM log level. Value should be [0-3]')


class BRMHandler(logging.StreamHandler):
    """
    Logging Handler that integrates with BRM Logging.

    import logging
    import pybrm
    from pybrm import Client, BRMHandler

    logging.basicConfig(level=pybrm.brm_to_python_log_level(pybrm.PIN_ERR_LEVEL_ERROR))
    logger = logging.getLogger(__name__)
    logger.addHandler(BRMHandler())

    c = Client(
        # These are the defaults, you don't need to write them:
        log_level=pybrm.PIN_ERR_LEVEL_ERROR,
        program='pybrm',
        log_file='default.pinlog'
    )
    c.pin_err_set_level(pybrm.PIN_ERR_LEVEL_ERROR)  # It actually defaults to PIN_ERR_LEVEL_ERROR

    logger.error('This is visible')
    logger.debug('This is not visible')
    """
    def emit(self, record):
        level = _python_to_brm_level.get(record.levelno, PIN_ERR_LEVEL_ERROR)
        message = self.format(record)
        file_name = record.filename
        line_number = record.lineno
        pin_err_log_msg(level, message, file_name, line_number)

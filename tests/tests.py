import os
import ctypes


# DO NOT MOVE THIS BELOW THE import pybrm !
# As soon as we import pybrm, it attempts to access pin.conf
# These tests rely on modification timestamps of pin.conf
utime_value = 0
current_directory = os.path.split(os.path.abspath(__file__))[0]


def utime_pin_conf():
    global utime_value
    utime_value += 1
    os.utime('pin.conf', (utime_value, utime_value))


def change_into_pin_conf_test_directory(update_utime=True):
    os.chdir(os.path.join(current_directory, 'pin_conf_test'))
    if update_utime:
        utime_pin_conf()


def change_into_test_directory(update_utime=True):
    os.chdir(current_directory)
    if update_utime:
        utime_pin_conf()

utime_pin_conf()

change_into_pin_conf_test_directory(update_utime=True)
change_into_test_directory(update_utime=False)

# After this runs, the tests/pin.conf will be 1
# and the pin_conf_test/pin.conf will be 2
# after import pybrm, we load the tests/pin.conf directory.

# DO NOT MOVE THIS BELOW THE import pybrm !
# As soon as we import pybrm, it attempts to access pin.conf
# These tests rely on modification timestamps of pin.conf

import pybrm
from pybrm import cbrm
from pybrm import Client, FList, BRMError, Poid, BRMArray
from pybrm import pin_field_get_name, pin_field_get_type, pin_field_of_name, pin_virtual_time
from pybrm import constants, pin_conf
from datetime import datetime
import unittest
from unittest.mock import Mock
from decimal import Decimal
import sys
import logging


class TestBrm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Client()
    
    def setUp(self):
        # If some test closed it for some reason
        self.c.open()
    
    @classmethod
    def tearDownClass(cls):
        cls.c.close()


class TestAddFields(TestBrm):
    
    def test_close(self): # TODO move this elsewhere
        self.c.close()
        self.assertEquals(self.c.is_open(), False)

    def test_unknown_field(self):
        f = self.c.flist()
        self.assertRaises(KeyError, f.__setitem__, 'not_real', 'abc')
        self.assertRaises(KeyError, f._set_poid, 'not_real', 'abc')
        self.assertRaises(KeyError, f._set_str, 'not_real', 'abc')
        self.assertRaises(KeyError, f._set_tstamp, 'not_real', 123)
        self.assertRaises(AttributeError, f.__setattr__, 'not_real', 'abc')

    def test_PIN_FLD_POID(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_POID', 123)
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_POID', 123)
        f._set_poid('PIN_FLD_POID', '/event/pybrm')
        s = str(f)
        print(s)

    def test_poid_tuple_set(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = '/account',
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, -1)
        self.assertEquals(f['PIN_FLD_POID'].revision, 0)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '/account', 2
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 0)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '/account', 2, 100
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 100)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '/account', 2, 100, 3
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 100)
        self.assertEquals(f['PIN_FLD_POID'].database, 3)
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_POID', ('/account', 2, 100, 3, 5))

    def test_attr_poid_tuple_set(self):
        f = self.c.flist()
        f.PIN_FLD_POID = '/account',
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, -1)
        self.assertEquals(f.PIN_FLD_POID.revision, 0)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '/account', 2
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 0)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '/account', 2, 100
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 100)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '/account', 2, 100, 3
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 100)
        self.assertEquals(f.PIN_FLD_POID.database, 3)
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_POID', ('/account', 2, 100, 3, 5))

    def test_poid_real_poid_string(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = '0.0.0.1 /account -1 0'
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, -1)
        self.assertEquals(f['PIN_FLD_POID'].revision, 0)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '0.0.0.1 /account 2 0'
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 0)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '0.0.0.1 /account 2 100'
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 100)
        self.assertEquals(f['PIN_FLD_POID'].database, 1)
        f['PIN_FLD_POID'] = '0.0.0.3 /account 2 100'
        self.assertEquals(f['PIN_FLD_POID'].type, '/account')
        self.assertEquals(f['PIN_FLD_POID'].id, 2)
        self.assertEquals(f['PIN_FLD_POID'].revision, 100)
        self.assertEquals(f['PIN_FLD_POID'].database, 3)

    def test_attr_poid_real_poid_string(self):
        f = self.c.flist()
        f.PIN_FLD_POID = '0.0.0.1 /account -1 0'
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, -1)
        self.assertEquals(f.PIN_FLD_POID.revision, 0)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '0.0.0.1 /account 2 0'
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 0)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '0.0.0.1 /account 2 100'
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 100)
        self.assertEquals(f.PIN_FLD_POID.database, 1)
        f.PIN_FLD_POID = '0.0.0.3 /account 2 100'
        self.assertEquals(f.PIN_FLD_POID.type, '/account')
        self.assertEquals(f.PIN_FLD_POID.id, 2)
        self.assertEquals(f.PIN_FLD_POID.revision, 100)
        self.assertEquals(f.PIN_FLD_POID.database, 3)

    def test_poid_real_poid_string_error(self):
        f = self.c.flist()
        self.assertRaises(ValueError, f.__setitem__, 'PIN_FLD_POID', 'abcd /account -1 0')
        self.assertRaises(ValueError, f.__setitem__, 'PIN_FLD_POID', '0.0.0.1 /account abcd 0')
        self.assertRaises(ValueError, f.__setattr__, 'PIN_FLD_POID', 'abcd /account -1 0')
        self.assertRaises(ValueError, f.__setattr__, 'PIN_FLD_POID', '0.0.0.1 /account abcd 0')
        # this next one actually doesn't fail, instead it sets revision to 0
        #self.assertRaises(ValueError, f.__setitem__, 'PIN_FLD_POID', '0.0.0.1 /account -1 abcd')

    def test_PIN_FLD_POID_with_poid_object(self):
        f = self.c.flist()
        p = Poid('/event/pybrm', -1, 0, 1)
        f._set_poid('PIN_FLD_POID', p)
        poid = f._get_poid('PIN_FLD_POID')
        self.assertEqual(p, poid)

    def test_PIN_FLD_SERVICE_OBJ(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_SERVICE_OBJ', 123)
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_SERVICE_OBJ', 123)
        f._set_poid('PIN_FLD_SERVICE_OBJ', '/service/pybrm')
        s = str(f)
        print(s)

    def test_PIN_FLD_CREATED_T(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_CREATED_T', "hello")
        f['PIN_FLD_CREATED_T'] = 1.9
        self.assertEquals(f['PIN_FLD_CREATED_T'].timestamp(), 1)
        f['PIN_FLD_CREATED_T'] = int(datetime.now().timestamp())
        f['PIN_FLD_CREATED_T'] = datetime.now()
        s = str(f)
        print(s)

    def test_attr_PIN_FLD_CREATED_T(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_CREATED_T', "hello")
        f.PIN_FLD_CREATED_T = 1.9
        self.assertEquals(f.PIN_FLD_CREATED_T.timestamp(), 1)
        f.PIN_FLD_CREATED_T = int(datetime.now().timestamp())
        f.PIN_FLD_CREATED_T = datetime.now()
        s = str(f)
        print(s)

    def test_xml(self):
        f = self.c.flist()
        f._set_poid('PIN_FLD_POID', '/event/pybrm')
        s = f.xml()
        s = f.xml(root_element_name='foo')
        s = f.xml('PIN_XML_BY_TYPE')
        s = f.xml('PIN_XML_BY_TYPE', 'foo')
        s = f.xml('PIN_XML_BY_NAME')
        s = f.xml('PIN_XML_BY_NAME', 'foo')
        s = f.xml('PIN_XML_BY_SHORT_NAME')
        s = f.xml('PIN_XML_BY_SHORT_NAME', 'foo')
        s = f.xml('PIN_XML_FLDNO')
        s = f.xml('PIN_XML_FLDNO', 'foo')
        s = f.xml('PIN_XML_TYPE')
        s = f.xml('PIN_XML_TYPE', 'foo')
        self.assertRaises(KeyError, f.xml, 'illegalflag')

    def test_str(self):
        f = self.c.flist()
        f._set_poid('PIN_FLD_POID', '/event/pybrm')
        s = str(f)
        s = repr(f)
        f._flist.set_str(pin_field_of_name('PIN_FLD_STATUS'), 'hello')
        self.assertRaises(ValueError, self.c.flist, 'foo')

    def test_binstr(self):
        f = self.c.flist()
        f['PIN_FLD_PROVIDER_IPADDR'] = b'abc'
        self.assertEqual(f['PIN_FLD_PROVIDER_IPADDR'], b'abc')
        f['PIN_FLD_PROVIDER_IPADDR'] = None
        self.assertEqual(f['PIN_FLD_PROVIDER_IPADDR'], None)

    def test_buf(self):
        f = self.c.flist()
        f['PIN_FLD_SELECTOR'] = b'abc'
        self.assertEqual(f['PIN_FLD_SELECTOR'], b'abc')
        f['PIN_FLD_SELECTOR'] = None
        self.assertEqual(f['PIN_FLD_SELECTOR'], None)

    def test_attr_buf(self):
        f = self.c.flist()
        f.PIN_FLD_SELECTOR = b'abc'
        self.assertEqual(f.PIN_FLD_SELECTOR, b'abc')
        f.PIN_FLD_SELECTOR = None
        self.assertEqual(f.PIN_FLD_SELECTOR, None)

    def test_str_compact(self):
        f = self.c.flist()
        f._set_poid('PIN_FLD_POID', '/event/pybrm')
        self.assertIn('/event/pybrm', f.str_compact())

    def test_PIN_FLD_QUANTITY(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_QUANTITY', "hello")
        f['PIN_FLD_QUANTITY'] = "1.0"
        f['PIN_FLD_QUANTITY'] = "1.5"
        f['PIN_FLD_QUANTITY'] = 1
        f['PIN_FLD_QUANTITY'] = 1.0
        f['PIN_FLD_QUANTITY'] = 1.5
        f['PIN_FLD_QUANTITY'] = Decimal('1.0')
        f['PIN_FLD_QUANTITY'] = Decimal('1.5')
        s = str(f)
        print(s)

    def test_attr_PIN_FLD_QUANTITY(self):
        f = self.c.flist()
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_QUANTITY', "hello")
        f.PIN_FLD_QUANTITY = "1.0"
        f.PIN_FLD_QUANTITY = "1.5"
        f.PIN_FLD_QUANTITY = 1
        f.PIN_FLD_QUANTITY = 1.0
        f.PIN_FLD_QUANTITY = 1.5
        f.PIN_FLD_QUANTITY = Decimal('1.0')
        f.PIN_FLD_QUANTITY = Decimal('1.5')
        s = str(f)
        print(s)

    def test_add(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = '/a'
        f2 = self.c.flist()
        f2['PIN_FLD_QUANTITY'] = 1
        f3 = f + f2
        self.assertEquals(f3['PIN_FLD_POID'].type, '/a')
        self.assertEquals(f3['PIN_FLD_QUANTITY'], 1)
        self.assertNotIn('PIN_FLD_QUANTITY', f)
        self.assertNotIn('PIN_FLD_POID', f2)

    def test_attr_add(self):
        f = self.c.flist()
        f.PIN_FLD_POID = '/a'
        f2 = self.c.flist()
        f2.PIN_FLD_QUANTITY = 1
        f3 = f + f2
        self.assertEquals(f3.PIN_FLD_POID.type, '/a')
        self.assertEquals(f3.PIN_FLD_QUANTITY, 1)
        self.assertNotIn('PIN_FLD_QUANTITY', f)
        self.assertNotIn('PIN_FLD_POID', f2)

    def test_concat(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = '/a'
        f2 = self.c.flist()
        f2['PIN_FLD_QUANTITY'] = 1
        f._concat(f2)
        self.assertEquals(f['PIN_FLD_QUANTITY'], 1)
        self.assertEquals(f['PIN_FLD_POID'].type, '/a')
        self.assertNotIn('PIN_FLD_POID', f2)

    def test_attr_concat(self):
        f = self.c.flist()
        f.PIN_FLD_POID = '/a'
        f2 = self.c.flist()
        f2.PIN_FLD_QUANTITY = 1
        f._concat(f2)
        self.assertEquals(f.PIN_FLD_QUANTITY, 1)
        self.assertEquals(f.PIN_FLD_POID.type, '/a')
        self.assertNotIn('PIN_FLD_POID', f2)

    def test_concat_and_iterate(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = 'a'
        f2 = self.c.flist()
        f2['PIN_FLD_POID'] = 'b'
        f2['PIN_FLD_STATUS'] = 1
        f._concat(f2)
        for k, v in f.items():
            pass

    def test_concat_duplicate_flist(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        f['PIN_FLD_POID'] = '/a'
        f['PIN_FLD_USAGE_TYPE'] = 'b'
        f2 = self.c.flist()
        f2['PIN_FLD_QUANTITY'] = 1
        f2['PIN_FLD_DURATION'] = 2
        f['PIN_FLD_STATUS'] = 1
        f._concat(f2)
        self.assertEquals(len(f), 5)
        self.assertEquals(len([k for k in f]), 5)

    def test_concat_duplicate_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {0: {'PIN_FLD_STATUS': 0}}
        f2 = self.c.flist()
        f2['PIN_FLD_RESULTS'] = {3: {'PIN_FLD_STATUS': 3}, 5: {'PIN_FLD_STATUS': 5}, 0: {'PIN_FLD_STATUS': 10}}
        f._concat(f2)
        # Remember the weird thing here
        # This count is 4 even though we concatted, whereas with a non array flist it would be the non deduplicated count
        # The reason is because flist.count() has to count the keys, which are non duplicates
        #   because of the PIN_FLIST_COUNT bug
        # However the array count works fine, so we dn't need to count the keys for it
        self.assertEquals(len(f['PIN_FLD_RESULTS']), 4)
        self.assertEquals(len([elem_id for elem_id in f['PIN_FLD_RESULTS']]), 3)


class TestTransaction(TestBrm):
    def test_errors(self):
        t = self.c.transaction('/event/pybrm')
        # Cannot open a new transaction without closing the first one
        self.assertRaises(BRMError, self.c.transaction, '/event/pybrm')
        t.commit()
        self.assertIsNone(t._transaction_flist)
        # Cannot commit a transaction that was already committed
        self.assertRaises(BRMError, t.commit)
        # Its fine to rollback a transaction that was already committed
        t.rollback()
        self.assertIsNone(t._transaction_flist)

        t = self.c.transaction('/event/pybrm')
        t.rollback()
        self.assertIsNone(t._transaction_flist)
        t.rollback()
        self.assertIsNone(t._transaction_flist)

        t = self.c.transaction('/event/pybrm')
        t.rollback()
        self.assertIsNone(t._transaction_flist)
        self.assertRaises(BRMError, t.commit)

    def test_flag_happy(self):
        t = self.c.transaction('/event/pybrm', flags='PCM_TRANS_OPEN_READONLY')
        t.rollback()
        t = self.c.transaction('/event/pybrm', flags='PCM_TRANS_OPEN_READWRITE')
        t.rollback()

    def test_flag_errors(self):
        c = Client()
        self.assertRaises(BRMError, c.transaction, '/event/pybrm', flags=1234)
        self.assertIsNone(c._transaction)

    def test_with(self):
        with self.c.transaction('/event/pybrm') as t:
            t.commit()

        with self.c.transaction('/event/pybrm') as t:
            t.rollback()

        with self.c.transaction('/event/pybrm') as t:
            pass

        with self.c.transaction('/event/pybrm') as t:
            self.assertRaises(BRMError, self.c.transaction, '/event/pybrm')

        with Client() as c:
            f = c.flist()
            f['PIN_FLD_POID'] = '/pybrm'
            f('PCM_OP_TEST_LOOPBACK')
            f('PCM_OP_TEST_LOOPBACK', reference=True)

        with Client() as c:
            with c.transaction('/event/pybrm') as t:
                f = c.flist()
                f['PIN_FLD_POID'] = '/pybrm'
                f('PCM_OP_TEST_LOOPBACK')
                t.commit()

        with Client() as c:
            with c.transaction('/event/pybrm') as t:
                f = c.flist()
                f['PIN_FLD_POID'] = '/pybrm'
                f('PCM_OP_TEST_LOOPBACK')
                t.rollback()

        with Client() as c:
            with c.transaction('/event/pybrm') as t:
                f = c.flist()
                self.assertRaises(BRMError, f, 'PCM_OP_TEST_LOOPBACK')  # Fails without PIN_FLD_POID

    def test_bad_opcode(self):
        f = self.c.flist()
        self.assertRaises(KeyError, f, 'FAKE_OPCODE')

    def test_closed_client_and_opcode(self):
        f = self.c.flist()
        self.c.close()
        self.assertRaises(BRMError, f, 'PCM_OP_TEST_LOOPBACK')
        try:
            f('PCM_OP_SEARCH')
        except BRMError as ex:
            self.assertIn('Client is closed', str(ex))


class TestFlist(TestBrm):
    def test_get_poid(self):
        flist = self.c.flist()
        flist['PIN_FLD_POID'] = '/event/pybrm'
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, -1)
        self.assertEqual(poid.revision, 0)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, -1)
        self.assertEqual(poid.revision, 0)

        poid = Poid(type='/event/pybrm', id=123)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 0)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 0)

        poid = Poid(type='/event/pybrm', id=123, revision=1)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 1)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 1)

        # Test long id
        poid = Poid(type='/event/pybrm', id=313123319462649664, revision=1)
        flist['PIN_FLD_POID'] = poid
        poid = flist['PIN_FLD_POID']
        self.assertEqual(poid.id, 313123319462649664)

        flist['PIN_FLD_POID'] = None
        self.assertEqual(flist['PIN_FLD_POID'], None)

        del flist['PIN_FLD_POID']
        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_POID')

        self.assertRaises(BRMError, flist._flist.set_poid, pin_field_of_name('PIN_FLD_POID'), value='foo')

    def test_attr_get_poid(self):
        flist = self.c.flist()
        flist.PIN_FLD_POID = '/event/pybrm'
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, -1)
        self.assertEqual(poid.revision, 0)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, -1)
        self.assertEqual(poid.revision, 0)

        poid = Poid(type='/event/pybrm', id=123)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 0)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 0)

        poid = Poid(type='/event/pybrm', id=123, revision=1)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 1)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, 123)
        self.assertEqual(poid.revision, 1)

        # Test long id
        poid = Poid(type='/event/pybrm', id=313123319462649664, revision=1)
        flist.PIN_FLD_POID = poid
        poid = flist.PIN_FLD_POID
        self.assertEqual(poid.id, 313123319462649664)

        flist.PIN_FLD_POID = None
        self.assertEqual(flist.PIN_FLD_POID, None)

        del flist.PIN_FLD_POID
        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_POID')

        self.assertRaises(BRMError, flist._flist.set_poid, pin_field_of_name('PIN_FLD_POID'), value='foo')

    def test_copy(self):
        flist = self.c.flist()
        flist['PIN_FLD_POID'] = '/event/pybrm'
        flist2 = flist.copy()
        poid = flist2['PIN_FLD_POID']
        self.assertEqual(poid.database, 1)
        self.assertEqual(poid.type, '/event/pybrm')
        self.assertEqual(poid.id, -1)

    def test_get_flist(self):
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        hello = flist['PIN_FLD_INHERITED_INFO']
        self.assertTrue(isinstance(hello, FList))

    def test_get_flist_sad(self):
        flist = self.c.flist()
        substruct = flist.get('PIN_FLD_INHERITED_INFO')
        self.assertIsNone(substruct)
        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_INHERITED_INFO')

    def test_get_decimal(self):
        # Ok so optional works for decimal, so long as its on the EDR_FLIST and not the outer flist for some reason
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        substruct['PIN_FLD_QUANTITY'] = 2.5
        duration = substruct['PIN_FLD_QUANTITY']
        self.assertEqual(duration, 2.5)
        del substruct['PIN_FLD_QUANTITY']
        duration = substruct.get('PIN_FLD_QUANTITY')
        self.assertIsNone(duration)
        self.assertRaises(KeyError, substruct.__getitem__, 'PIN_FLD_QUANTITY')
        substruct['PIN_FLD_QUANTITY'] = None
        self.assertEqual(substruct['PIN_FLD_QUANTITY'], None)

        self.assertRaises(BRMError, substruct._flist.set_decimal, pin_field_of_name('PIN_FLD_QUANTITY'), value='foo')

    def test_get_int(self):
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        substruct['PIN_FLD_RUM_ID'] = 2
        call_type = substruct['PIN_FLD_RUM_ID']
        self.assertEqual(call_type, 2)

        del substruct['PIN_FLD_RUM_ID']
        call_type = substruct.get('PIN_FLD_RUM_ID')
        self.assertIsNone(call_type)
        self.assertRaises(KeyError, substruct.__getitem__, 'PIN_FLD_RUM_ID')

        # Test long
        self.assertRaises(OverflowError, flist.__setitem__, 'PIN_FLD_RUM_ID', 313123319462649664)

        substruct['PIN_FLD_RUM_ID'] = None
        self.assertEqual(substruct['PIN_FLD_RUM_ID'], 0)

        substruct['PIN_FLD_RUM_ID'] = '2'
        self.assertEquals(substruct['PIN_FLD_RUM_ID'], 2)
        self.assertRaises(TypeError, substruct.__setitem__, 'PIN_FLD_RUM_ID', 'abc')
        # doesnt raise error
        #self.assertRaises(BRMError, substruct._flist.set_int, pin_field_of_name('PIN_FLD_POID'), value=1234)

    def test_get_tstamp(self):
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        d = datetime.now()
        d = datetime.fromtimestamp(int(d.timestamp()))
        substruct['PIN_FLD_CREATED_T'] = d
        out = substruct['PIN_FLD_CREATED_T']
        self.assertEqual(d, out)

        del substruct['PIN_FLD_CREATED_T']
        out = substruct.get('PIN_FLD_CREATED_T')
        self.assertIsNone(out)

        self.assertRaises(KeyError, substruct.__getitem__, 'PIN_FLD_CREATED_T')

        substruct['PIN_FLD_CREATED_T'] = None
        # There are no NULL timestamps, it will be 0
        self.assertNotEqual(substruct['PIN_FLD_CREATED_T'], None)
        # doesn't raise error
        #self.assertRaises(BRMError, substruct._flist.set_tstamp, pin_field_of_name('PIN_FLD_POID'), value=1234)

    def test_get_str(self):
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        substruct['PIN_FLD_RATE_TAG'] = 'foo'
        department = substruct['PIN_FLD_RATE_TAG']
        self.assertEqual(department, 'foo')

        del substruct['PIN_FLD_RATE_TAG']
        department = substruct.get('PIN_FLD_RATE_TAG')
        self.assertIsNone(department)

        self.assertRaises(KeyError, substruct.__getitem__, 'PIN_FLD_RATE_TAG')

        substruct['PIN_FLD_RATE_TAG'] = None
        self.assertEqual(substruct['PIN_FLD_RATE_TAG'], None)

        substruct['PIN_FLD_RATE_TAG'] = 5
        self.assertEqual(substruct['PIN_FLD_RATE_TAG'], '5')

    def test_from_str(self):
        for _ in range(10):
            flist = self.c.flist('''0 PIN_FLD_POID    POID [0] 0.0.0.1 /account -1 0
    0 PIN_FLD_CUSTOMER_SEGMENT_LIST     STR [0] "10007"''')

    def test_from_xml(self):
        f = self.c.flist({
            'PIN_FLD_POID': '/account',
            'PIN_FLD_STATUS': 1,
            'PIN_FLD_CREATED_T': datetime.now(),
            'PIN_FLD_INHERITED_INFO': {
                'PIN_FLD_POID': ('/service', 1234)
            },
            'PIN_FLD_VALUES': [
                {'PIN_FLD_STATUS': 1},
                {'PIN_FLD_STATUS': 2},
            ],
            'PIN_FLD_ARGS': [
                {'PIN_FLD_STATUS': 3},
                {'PIN_FLD_STATUS': 4},
            ],
            'RESULTS': {
                -1: {'PIN_FLD_STATUS': 5},
                0: {'PIN_FLD_STATUS': 6},
            }
        })
        self.assertTrue(f == self.c.flist(f.xml('PIN_XML_BY_TYPE')) == self.c.flist(f.xml('PIN_XML_BY_NAME')))

    def test_from_xml_null_empty(self):
        f = self.c.flist({
            'PIN_FLD_POID': '/account',
            'PIN_FLD_INHERITED_INFO': None,
            'PIN_FLD_EVENT': {},
            'PIN_FLD_VALUES': None,
            'PIN_FLD_ARGS': {0: {}}
        })
        # When BRM serializes to XML, it's not possible to disambiguate between Empty and NULL
        # Thus we are always going to assume its an Empty
        expected = self.c.flist({
            'PIN_FLD_POID': '/account',
            'PIN_FLD_INHERITED_INFO': {},
            'PIN_FLD_EVENT': {},
            'PIN_FLD_VALUES': {0: {}},
            'PIN_FLD_ARGS': {0: {}}
        })

        self.assertTrue(expected == self.c.flist(f.xml('PIN_XML_BY_TYPE')) == self.c.flist(f.xml('PIN_XML_BY_NAME')))

    def test_from_json(self):
        f = self.c.flist({
            'PIN_FLD_POID': '/account',
            'PIN_FLD_STATUS': 1,
            'PIN_FLD_CREATED_T': datetime.now(),
            'PIN_FLD_INHERITED_INFO': {
                'PIN_FLD_POID': ('/service', 1234)
            },
            # Using list syntax will set the elem_ids to 0, 1, ...
            'PIN_FLD_VALUES': [
                {'PIN_FLD_STATUS': 1, 'PIN_FLD_CREATED_T': datetime.now(), 'PIN_FLD_POID': '/account'},
                {'PIN_FLD_STATUS': 2, 'PIN_FLD_CREATED_T': datetime.now(), 'PIN_FLD_POID': '/account'},
            ],
            # Using dict syntax allows you to specify the elem_ids if it is sparse
            'PIN_FLD_ARGS': {
                4: {'PIN_FLD_STATUS': 3, 'PIN_FLD_CREATED_T': datetime.now(), 'PIN_FLD_POID': '/account'},
                16: {'PIN_FLD_STATUS': 4, 'PIN_FLD_CREATED_T': datetime.now(), 'PIN_FLD_POID': '/account'},
            },
            'RESULTS': {
                -1: {'PIN_FLD_STATUS': 5},
                0: {'PIN_FLD_STATUS': 6},
            }
        })

        self.assertTrue(f == self.c.flist(f.json()))

    def test_from_json_null_empty(self):
        f = self.c.flist({
            'PIN_FLD_POID': '/account',
            'PIN_FLD_INHERITED_INFO': None,
            'PIN_FLD_EVENT': {},
            'PIN_FLD_VALUES': None,
            'PIN_FLD_ARGS': {0: {}}
        })

        self.assertEquals(f, self.c.flist(f.json()))

    def test_get_enum(self):
        flist = self.c.flist()
        flist['PIN_FLD_STATUS'] = 0
        status = flist['PIN_FLD_STATUS']
        self.assertEqual(status, 0)
        flist['PIN_FLD_STATUS'] = 1
        status = flist['PIN_FLD_STATUS']
        self.assertEqual(status, 1)

        flist = self.c.flist()
        # doesnt work: flist._drop_field('PIN_FLD_STATUS')
        # Cant get this working
        #status = flist.get_field('PIN_FLD_STATUS', optional=1)
        #self.assertIsNone(status)

        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_STATUS')

        flist['PIN_FLD_STATUS'] = None
        self.assertEqual(flist['PIN_FLD_STATUS'], 0)

        flist['PIN_FLD_STATUS'] = '1'
        self.assertEquals(flist['PIN_FLD_STATUS'], 1)
        self.assertRaises(TypeError, flist.__setitem__, 'PIN_FLD_STATUS', 'abc')

        del flist['PIN_FLD_STATUS']
        self.assertIsNone(flist.get('PIN_FLD_STATUS'))
        # doesn't raise an error
        #self.assertRaises(BRMError, flist._flist.set_enum, pin_field_of_name('PIN_FLD_POID'), value=1234)

    def test_get_item(self):
        flist = self.c.flist()
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        substruct['PIN_FLD_RATE_TAG'] = 'foo'
        department = substruct['PIN_FLD_RATE_TAG']
        self.assertEqual(department, 'foo')

        del substruct['PIN_FLD_RATE_TAG']
        department = substruct.get('PIN_FLD_RATE_TAG')
        self.assertIsNone(department)
        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_RATE_TAG')

        department = substruct.get('PIN_FLD_RATE_TAG')
        self.assertIsNone(department)
        self.assertRaises(KeyError, flist.__getitem__, 'PIN_FLD_RATE_TAG')

    def test_count(self):
        flist = self.c.flist()
        self.assertEqual(flist.count(), 0)
        self.assertEqual(len(flist), 0)
        flist['PIN_FLD_POID'] = '/event/pybrm'
        self.assertEqual(flist.count(), 1)
        self.assertEqual(len(flist), 1)
        flist['PIN_FLD_SERVICE_OBJ'] = '/service/pybrm'
        self.assertEqual(flist.count(), 2)
        self.assertEqual(len(flist), 2)
        flist['PIN_FLD_SERVICE_OBJ'] = '/service/pybrm'
        self.assertEqual(flist.count(), 2)
        self.assertEqual(len(flist), 2)
        flist['PIN_FLD_INHERITED_INFO'] = {}
        substruct = flist['PIN_FLD_INHERITED_INFO']
        self.assertEqual(flist.count(), 3)
        self.assertEqual(len(flist), 3)
        substruct['PIN_FLD_RATE_TAG'] = 'foo'
        self.assertEqual(flist.count(), 3)
        self.assertEqual(len(flist), 3)
        self.assertEqual(flist.count(recursive=True), 4)
        flist['PIN_FLD_ARGS'] = {0: {'PIN_FLD_STATUS': 1}}
        self.assertEqual(flist.count(), 4)
        self.assertEqual(len(flist), 4)
        self.assertEqual(flist.count(recursive=True), 6)
        flist['PIN_FLD_ARGS'][0]['PIN_FLD_POID'] = '/a'
        self.assertEqual(flist.count(), 4)
        self.assertEqual(len(flist), 4)
        self.assertEqual(flist.count(recursive=True), 7)
        flist['PIN_FLD_ARGS'][1] = {'PIN_FLD_STATUS': 2}
        self.assertEqual(flist.count(), 4)
        self.assertEqual(len(flist), 4)
        self.assertEqual(flist.count(recursive=True), 8)
        flist['PIN_FLD_ARGS'][1]['PIN_FLD_POID'] = '/b'
        self.assertEqual(flist.count(), 4)
        self.assertEqual(len(flist), 4)
        self.assertEqual(flist.count(recursive=True), 9)

        self.assertEqual(substruct.count(), 1)
        del substruct['PIN_FLD_RATE_TAG']
        self.assertEqual(substruct.count(), 0)

    def test_count_with_null_substructures(self):
        flist = self.c.flist()
        flist['PIN_FLD_POID'] = '/event/pybrm'
        self.assertEqual(flist.count(), 1)
        self.assertEqual(flist.count(recursive=True), 1)
        flist['PIN_FLD_ARGS'] = None
        self.assertEqual(flist.count(), 2)
        self.assertEqual(flist.count(recursive=True), 3)
        flist['PIN_FLD_ARGS'][1] = None
        self.assertEqual(flist.count(), 2)
        self.assertEqual(flist.count(recursive=True), 4)
        flist['PIN_FLD_INHERITED_INFO'] = None
        self.assertEqual(flist.count(), 3)
        self.assertEqual(flist.count(recursive=True), 5)

    def test_iter(self):
        flist = self.c.flist()
        for name in flist:
            pass
        flist['PIN_FLD_POID'] = '/event/pybrm'
        self.assertEqual(list(iter(flist)), ['PIN_FLD_POID'])
        self.assertEqual(next(iter(flist)), 'PIN_FLD_POID')
        flist['PIN_FLD_SERVICE_OBJ'] = '/service/pybrm'
        self.assertEqual(list(iter(flist)), ['PIN_FLD_POID', 'PIN_FLD_SERVICE_OBJ'])

    def test_in(self):
        f = self.c.flist()
        self.assertTrue('PIN_FLD_POID' not in f)
        f['PIN_FLD_POID'] = None
        self.assertTrue('PIN_FLD_POID' in f)
        f['PIN_FLD_POID'] = 'abc'
        self.assertTrue('PIN_FLD_POID' in f)
        del f['PIN_FLD_POID']
        self.assertTrue('PIN_FLD_POID' not in f)

        self.assertTrue('PIN_FLD_USAGE_TYPE' not in f)
        f['PIN_FLD_USAGE_TYPE'] = None
        self.assertTrue('PIN_FLD_USAGE_TYPE' in f)
        f['PIN_FLD_USAGE_TYPE'] = 'abc'
        self.assertTrue('PIN_FLD_USAGE_TYPE' in f)
        del f['PIN_FLD_USAGE_TYPE']
        self.assertTrue('PIN_FLD_USAGE_TYPE' not in f)

        self.assertTrue('PIN_FLD_INHERITED_INFO' not in f)
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        self.assertTrue('PIN_FLD_INHERITED_INFO' in f)
        del f['PIN_FLD_INHERITED_INFO']
        self.assertTrue('PIN_FLD_INHERITED_INFO' not in f)

        self.assertTrue('PIN_FLD_RESULTS' not in f)
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': '/a'}]
        self.assertTrue('PIN_FLD_RESULTS' in f)
        del f['PIN_FLD_RESULTS']
        self.assertTrue('PIN_FLD_RESULTS' not in f)
        f['PIN_FLD_RESULTS'] = {}
        self.assertTrue('PIN_FLD_RESULTS' in f)

    def test_del(self):
        f = self.c.flist()
        self.assertFalse('PIN_FLD_POID' in f)
        f['PIN_FLD_POID'] = 'abc'
        self.assertTrue('PIN_FLD_POID' in f)
        del f['PIN_FLD_POID']
        self.assertFalse('PIN_FLD_POID' in f)
        self.assertFalse('PIN_FLD_RESULTS' in f)
        self.assertRaises(KeyError, f.__delitem__, 'PIN_FLD_POID')
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS'][10] = {'PIN_FLD_POID': 'abc'}
        f['PIN_FLD_RESULTS'][20] = {'PIN_FLD_POID': 'def'}
        f['PIN_FLD_RESULTS'][30] = {'PIN_FLD_POID': 'ghi'}
        self.assertTrue('PIN_FLD_RESULTS' in f)
        del f['PIN_FLD_RESULTS']
        self.assertFalse('PIN_FLD_RESULTS' in f)
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS'][10] = {'PIN_FLD_POID': 'abc'}
        f['PIN_FLD_RESULTS'][20] = {'PIN_FLD_POID': 'def'}
        f['PIN_FLD_RESULTS'][30] = {'PIN_FLD_POID': 'ghi'}
        self.assertTrue('PIN_FLD_RESULTS' in f)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 3)
        del f['PIN_FLD_RESULTS'][20]
        self.assertTrue('PIN_FLD_RESULTS' in f)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 2)
        self.assertEqual(f['PIN_FLD_RESULTS'][10]['PIN_FLD_POID'].type, 'abc')
        self.assertEqual(f['PIN_FLD_RESULTS'][30]['PIN_FLD_POID'].type, 'ghi')
        self.assertRaises(KeyError, f['PIN_FLD_RESULTS'].__delitem__, 20)
        f['PIN_FLD_ARGS'] = {}
        self.assertRaises(KeyError, f['PIN_FLD_ARGS'].__delitem__, 10)
        del f['PIN_FLD_ARGS']
        self.assertRaises(KeyError, f.__delitem__, 'PIN_FLD_ARGS')

    def test_asdict(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = 'a'
        f['PIN_FLD_STATUS'] = 1
        f['PIN_FLD_INHERITED_INFO'] = {'PIN_FLD_POID': 'b', 'PIN_FLD_STATUS': 2}
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'c', 'PIN_FLD_STATUS': 3}]

        d = f.asdict()

        f2 = self.c.flist(d)

        self.assertEquals(f, f2)

    def test_pop(self):
        f = self.c.flist()
        self.assertIsNone(f.pop('PIN_FLD_STATUS'))
        f['PIN_FLD_STATUS'] = 1
        self.assertIn('PIN_FLD_STATUS', f)
        self.assertEquals(f.pop('PIN_FLD_STATUS'), 1)
        self.assertNotIn('PIN_FLD_STATUS', f)

    def test_clear(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        self.assertIn('PIN_FLD_STATUS', f)
        f.clear()
        self.assertNotIn('PIN_FLD_STATUS', f)

    def test_update(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        f.update({'PIN_FLD_STATUS': 2})
        self.assertEquals(f['PIN_FLD_STATUS'], 2)

    def test_update_big(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        f['PIN_FLD_USAGE_TYPE'] = 'foo'
        f['PIN_FLD_RESULTS'] = {0: {'PIN_FLD_STATUS': 0}, 2: {'PIN_FLD_STATUS': 2}}
        f['PIN_FLD_ARGS'] = {1: {'PIN_FLD_STATUS': 0}, 2: {'PIN_FLD_STATUS': 5}}
        f['PIN_FLD_VALUES'] = {-1: {'PIN_FLD_STATUS': 0}, 0: {'PIN_FLD_STATUS': 1}}
        f.update(
            {
                'PIN_FLD_STATUS': 2,
                'PIN_FLD_RESULTS': {
                    0: {'PIN_FLD_STATUS': 10},
                    1: {'PIN_FLD_STATUS': 1}
                },
                'PIN_FLD_ARGS': [
                    {'PIN_FLD_STATUS': 2},
                    {'PIN_FLD_STATUS': 4},
                ],
                'PIN_FLD_VALUES': {
                    -1: {'PIN_FLD_STATUS': 5},
                    2: {'PIN_FLD_STATUS': 6},
                }
            }
        )
        self.assertEquals(f, {
            'PIN_FLD_STATUS': 2,
            'PIN_FLD_USAGE_TYPE': 'foo',
            'PIN_FLD_RESULTS': {
                0: {'PIN_FLD_STATUS': 10},
                1: {'PIN_FLD_STATUS': 1},
                2: {'PIN_FLD_STATUS': 2}
            },
            'PIN_FLD_ARGS': {
                0: {'PIN_FLD_STATUS': 2},
                1: {'PIN_FLD_STATUS': 4},
                2: {'PIN_FLD_STATUS': 5},
            },
            'PIN_FLD_VALUES': {
                -1: {'PIN_FLD_STATUS': 5},
                0: {'PIN_FLD_STATUS': 1},
                2: {'PIN_FLD_STATUS': 6},
            }
        })
        f['PIN_FLD_ARGS'].update([
            {'PIN_FLD_STATUS': 20},
            {'PIN_FLD_STATUS': 30},
        ])
        self.assertEquals(f['PIN_FLD_ARGS'], {
            0: {'PIN_FLD_STATUS': 20},
            1: {'PIN_FLD_STATUS': 30},
            2: {'PIN_FLD_STATUS': 5}
        })

    def test_equals(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        f['PIN_FLD_POID'] = '/a'
        f2 = self.c.flist()
        f2['PIN_FLD_STATUS'] = 1

        self.assertNotEquals(f, f2)
        f2['PIN_FLD_USAGE_TYPE'] = 'foo'
        self.assertNotEquals(f, f2)
        del f2['PIN_FLD_USAGE_TYPE']
        f2['PIN_FLD_POID'] = '/b'
        self.assertNotEquals(f, f2)
        f2['PIN_FLD_POID'] = '/a'
        self.assertEquals(f, f2)

        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        f2 = self.c.flist()
        f2['PIN_FLD_POID'] = '/a'
        self.assertNotEquals(f, f2)


class TestDealloc(TestBrm):
    def test_delete_parent_then_child(self):
        c = Client()
        parent = c.flist()
        del c
        parent['PIN_FLD_SERVICE_OBJ'] = '/abc'
        parent['PIN_FLD_INHERITED_INFO'] = {}
        child = parent['PIN_FLD_INHERITED_INFO']
        child['PIN_FLD_CREATED_T'] = 123
        del parent
        child['PIN_FLD_RATE_TAG'] = 'foo'
        del child

    def test_delete_child_then_parent(self):
        c = Client()
        parent = c.flist()
        parent['PIN_FLD_SERVICE_OBJ'] = '/abc'
        parent['PIN_FLD_INHERITED_INFO'] = {}
        child = parent['PIN_FLD_INHERITED_INFO']
        d = datetime(2019, 1, 1)
        child['PIN_FLD_CREATED_T'] = d
        del child
        parent['PIN_FLD_POID'] = 'def'
        child = parent['PIN_FLD_INHERITED_INFO']
        self.assertEqual(child['PIN_FLD_CREATED_T'], d)
        del parent
        del c


class TestCache(TestBrm):
    def assert_refcount(self, flist, expected_count):
        self.assertEqual(sys.getrefcount(flist._flist) - 1,expected_count)

    def test_first(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_POID'] = 'f'
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        a['PIN_FLD_POID'] = 'a'
        del f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 1)
        result = str(a)

    def test_second(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_POID'] = 'f'
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        a['PIN_FLD_POID'] = 'a'
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        del a
        self.assert_refcount(f, 1)
        result = str(f)
        del f['PIN_FLD_INHERITED_INFO']
        result = str(f)

    def test_third(self):
        c = Client()
        f = c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        c = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 3)
        self.assert_refcount(b, 3)
        self.assert_refcount(c, 3)
        self.assertTrue(a._flist is b._flist is c._flist)
        a['PIN_FLD_POID'] = 'a'
        self.assertTrue(a['PIN_FLD_POID'] == b['PIN_FLD_POID'] == c['PIN_FLD_POID'])
        del c
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        del b
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        del a
        self.assert_refcount(f, 1)

    def test_fourth(self):
        c = Client()
        f = c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        c = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 3)
        self.assert_refcount(b, 3)
        self.assert_refcount(c, 3)
        self.assertTrue(a._flist is b._flist is c._flist)
        del f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 3)
        self.assert_refcount(b, 3)
        self.assert_refcount(c, 3)
        a['PIN_FLD_POID'] = 'a'
        self.assertTrue(a['PIN_FLD_POID'] == b['PIN_FLD_POID'] == c['PIN_FLD_POID'])
        del c
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        del b
        self.assert_refcount(a, 1)
        del f
        result = str(a)

    def test_fifth(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_RESULTS'] = {}
        self.assert_refcount(f, 1)
        arr = f['PIN_FLD_RESULTS']
        self.assert_refcount(f, 2)  # arr has a reference to _flist
        arr[0] = {'PIN_FLD_POID': 'a'}
        arr[1] = {'PIN_FLD_POID': 'b'}
        self.assert_refcount(f, 2)
        del arr
        self.assert_refcount(f, 1)
        a = f['PIN_FLD_RESULTS'][0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = f['PIN_FLD_RESULTS'][0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        self.assertTrue(a._flist is b._flist)
        del f['PIN_FLD_RESULTS']
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        result = str(a)
        del f
        result = str(b)

    """
    def test_fifth(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_RESULTS'] = {}
        self.assert_refcount(f, 1)
        arr = f['PIN_FLD_RESULTS']
        self.assert_refcount(f, 1)
        arr[0] = {'PIN_FLD_POID': 'a'}
        arr[1] = {'PIN_FLD_POID': 'b'}
        self.assert_refcount(f, 1)  # _items bug i think
        a = arr[0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = f['PIN_FLD_RESULTS'][0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        self.assertTrue(a._flist is b._flist)
        del f['PIN_FLD_RESULTS']
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        result = str(a)
        del f
        result = str(b)
    """

    def test_sixth(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_RESULTS'] = [
            {'PIN_FLD_POID': 'a'},
            {'PIN_FLD_POID': 'b'},
        ]
        self.assert_refcount(f, 1)
        a = f['PIN_FLD_RESULTS'][0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = f['PIN_FLD_RESULTS'][1]
        self.assert_refcount(f, 3)
        self.assert_refcount(a, 1)
        self.assert_refcount(b, 1)
        self.assertTrue(a._flist is not b._flist)
        self.assertEqual(a['PIN_FLD_POID'].type, 'a')
        self.assertEqual(b['PIN_FLD_POID'].type, 'b')
        del f['PIN_FLD_RESULTS']
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 1)
        self.assert_refcount(b, 1)
        result = str(a)
        del f
        result = str(b)

    def test_seventh(self):
        f = self.c.flist()
        z = self.c.flist()
        self.assert_refcount(f, 1)
        self.assert_refcount(z, 1)
        z['PIN_FLD_POID'] = 'abc'
        f['PIN_FLD_INHERITED_INFO'] = z  # This is a copy, it does not add z as child
        self.assert_refcount(f, 1)
        self.assert_refcount(z, 1)
        z['PIN_FLD_POID'] = 'def'
        self.assertEqual(f['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type, 'abc')

    def test_eighth(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        f['PIN_FLD_POID'] = 'f'
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        a['PIN_FLD_POID'] = 'a'
        b = f['PIN_FLD_INHERITED_INFO']
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(b, 2)
        self.assertTrue(a._flist is b._flist)

    def test_elemid_any(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {
            10: {'PIN_FLD_POID': 'a'},
            20: {'PIN_FLD_POID': 'b'},
            30: {'PIN_FLD_POID': 'c'},
            0: {'PIN_FLD_POID': 'z'},
        }
        elemid_any = f['PIN_FLD_RESULTS']['*']
        self.assert_refcount(elemid_any, 1)
        a = f['PIN_FLD_RESULTS'][10]
        self.assertTrue(elemid_any._flist is a._flist)
        self.assert_refcount(elemid_any, 2)
        self.assert_refcount(a, 2)
        del a
        self.assert_refcount(elemid_any, 1)

    def test_elem_id_any2(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS'][4] = {'PIN_FLD_POID': 'a'}
        f['PIN_FLD_RESULTS'][10] = {'PIN_FLD_POID': 'b'}
        f['PIN_FLD_RESULTS'][16] = {'PIN_FLD_POID': 'c'}
        a = f['PIN_FLD_RESULTS'][4]
        a['PIN_FLD_INHERITED_INFO'] = {}
        a2 = a['PIN_FLD_INHERITED_INFO']
        a2['PIN_FLD_POID'] = 'a2'
        a2['PIN_FLD_INHERITED_INFO'] = {}
        a3 = a2['PIN_FLD_INHERITED_INFO']
        a3['PIN_FLD_POID'] = 'a3'
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 2)
        self.assert_refcount(a2, 2)
        self.assert_refcount(a3, 1)
        f['PIN_FLD_RESULTS']['*'] = {'PIN_FLD_POID': '/any'}
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 2)
        self.assert_refcount(a2, 2)
        self.assert_refcount(a3, 1)
        a3['PIN_FLD_POID'] = '/delta'
        self.assertEquals(a['PIN_FLD_INHERITED_INFO']['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type, '/delta')
        a['PIN_FLD_INHERITED_INFO']['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'] = '/delta2'
        self.assertEquals(a3['PIN_FLD_POID'].type, '/delta2')

    def test_missed_cache(self):
        f = self.c.flist()
        self.assert_refcount(f, 1)
        a = f.get('PIN_FLD_INHERITED_INFO')
        self.assert_refcount(f, 1)
        a = f.get('PIN_FLD_INHERITED_INFO')
        self.assert_refcount(f, 1)
        a = f.get('PIN_FLD_INHERITED_INFO')
        self.assert_refcount(f, 1)

        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS']._get_array_flist(10, 1)
        self.assert_refcount(f, 1)
        f['PIN_FLD_RESULTS']._get_array_flist(10, 1)
        self.assert_refcount(f, 1)
        f['PIN_FLD_RESULTS']._get_array_flist(10, 1)
        self.assert_refcount(f, 1)


class TestPinFieldFunctions(unittest.TestCase):
    def test_all(self):
        field_number = pin_field_of_name('PIN_FLD_POID')
        # in pcm_fields it is actually defined as 16
        self.assertEqual(field_number, 117440528)
        field_type = pin_field_get_type(field_number)
        self.assertEqual(field_type, 7)
        field_name = pin_field_get_name(field_number)
        self.assertEqual(field_name, 'PIN_FLD_POID')

        field_number = 16
        field_name = pin_field_get_name(field_number)
        self.assertEqual(field_name, 'PIN_FLD_POID')
        # This is some strange BRM issue
        # 16 and 117440528 both map to PIN_FLD_POID
        # but 16 cant get the type
        self.assertRaises(KeyError, pin_field_get_type, field_number)


class TestFields(unittest.TestCase):
    def setUp(self):
        constants._fields.clear()
        constants._fields_by_number.clear()

    def test_a(self):
        field_number = constants.field_by_identifier('PIN_FLD_POID')
        self.assertEqual(field_number, 117440528)
        self.assertEqual(constants._fields['PIN_FLD_POID'], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })
        self.assertEqual(constants._fields_by_number[field_number], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })
        field_number = constants.field_by_identifier('PIN_FLD_POID')
        self.assertEqual(field_number, 117440528)

    def test_b(self):
        field_number = 117440528
        field_number = constants.field_by_identifier(field_number)
        self.assertEqual(field_number, 117440528)
        self.assertEqual(constants._fields['PIN_FLD_POID'], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })
        self.assertEqual(constants._fields_by_number[field_number], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })

    def test_c(self):
        field_number = 16
        field_number = constants.field_by_identifier(field_number)
        self.assertEqual(field_number, 117440528)
        self.assertEqual(constants._fields['PIN_FLD_POID'], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })
        self.assertEqual(constants._fields_by_number[field_number], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })
        self.assertEqual(constants._fields_by_number[16], {
            'field_name': 'PIN_FLD_POID',
            'field_number': field_number,
            'field_type': 7,
        })

    def test_errors(self):
        self.assertRaises(TypeError, constants.field_by_identifier, ('a', 'b'))
        self.assertRaises(TypeError, constants.field_type_by_identifier, ('a,', 'b'))
        self.assertRaises(TypeError, constants.field_name_by_identifier, ('a,', 'b'))


class TestFlistCombos(unittest.TestCase):
    def test_same_flist(self):
        c = Client()
        f = c.flist()
        f['PIN_FLD_INHERITED_INFO'] = {}
        a = f['PIN_FLD_INHERITED_INFO']
        b = f['PIN_FLD_INHERITED_INFO']
        self.assertIs(a._flist, b._flist)


class ToDoTests(unittest.TestCase):
    # TODO move elsewhere
    def test_poid_type_start_with_int(self):
        c = Client()
        f = c.flist()
        self.assertRaises(ValueError, f.__setitem__, 'PIN_FLD_POID', '123foo')


class TestArray(TestBrm):
    def assert_refcount(self, flist, expected_count):
        self.assertEqual(sys.getrefcount(flist._flist) - 1, expected_count)

    def test_happy(self):
        flist = self.c.flist()
        flist['PIN_FLD_RESULTS'] = []
        results = flist['PIN_FLD_RESULTS']
        self.assertEqual(len(results), 0)
        results[0] = {'PIN_FLD_STATUS': 1}
        self.assertEqual(len(results), 1)
        first = results[0]
        self.assertEqual(first['PIN_FLD_STATUS'], 1)
        results[1] = {}
        second = results[1]
        second['PIN_FLD_STATUS'] = 0
        self.assertEqual(len(results), 2)
        self.assertEqual(second['PIN_FLD_STATUS'], 0)

    def test_key_error(self):
        flist = self.c.flist()
        flist['PIN_FLD_RESULTS'] = []
        self.assertRaises(KeyError, flist['PIN_FLD_RESULTS'].__getitem__, 1)
        self.assertIsNone(flist['PIN_FLD_RESULTS'].get(1))

    def test_set_flist_on_array_star(self):
        f = self.c.flist()
        a = self.c.flist()
        a['PIN_FLD_POID'] = 'any'
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS']['*'] = a
        self.assertEqual(f['PIN_FLD_RESULTS']['*']['PIN_FLD_POID'].type, 'any')

    def test_set_flist_on_array_pin_elemid_any(self):
        f = self.c.flist()
        a = self.c.flist()
        a['PIN_FLD_POID'] = 'any'
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS']['PIN_ELEMID_ANY'] = a
        self.assertEqual(f['PIN_FLD_RESULTS']['PIN_ELEMID_ANY']['PIN_FLD_POID'].type, 'any')

    def test_set_flist_on_array_int(self):
        f = self.c.flist()
        a = self.c.flist()
        a['PIN_FLD_POID'] = 'a'
        f['PIN_FLD_RESULTS'] = {10: a}
        self.assertEqual(f['PIN_FLD_RESULTS'][10]['PIN_FLD_POID'].type, 'a')

    def test_set_flist_on_array_bad(self):
        f = self.c.flist()
        a = self.c.flist()
        self.assertRaises(BRMError, f._flist.set_flist_on_array, pin_field_of_name('PIN_FLD_STATUS'), 1, value=a._flist)
        self.assertRaises(BRMError, f._flist.set_substr, pin_field_of_name('PIN_FLD_STATUS'), value=a._flist)

    def test_set_null_flist(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = '/a'
        self.assertEquals(f.count(), 1)
        self.assertNotIn('PIN_FLD_INHERITED_INFO', f)
        f['PIN_FLD_INHERITED_INFO'] = None
        self.assertIn('PIN_FLD_INHERITED_INFO', f)
        self.assertEquals(f.count(), 2)
        self.assertEquals(f.count(True), 2)
        self.assertIsNone(f['PIN_FLD_INHERITED_INFO'])
        del f['PIN_FLD_INHERITED_INFO']
        self.assertNotIn('PIN_FLD_INHERITED_INFO', f)
        self.assertEquals(f.count(), 1)
        self.assertEquals(f.count(True), 1)
        f['PIN_FLD_INHERITED_INFO'] = None
        self.assertFalse(bool(f['PIN_FLD_INHERITED_INFO']))
        items = f.items()
        k, v = next(items)
        self.assertEquals(k, 'PIN_FLD_POID')
        k, v = next(items)
        self.assertEquals(k, 'PIN_FLD_INHERITED_INFO')
        self.assertIsNone(v)

    def test_overwrite(self):
        f = self.c.flist()
        f2 = self.c.flist()
        f2['PIN_FLD_POID'] = 'a'
        f['PIN_FLD_INHERITED_INFO'] = f2
        self.assert_refcount(f2, 1)
        self.assert_refcount(f, 1)
        temp = f['PIN_FLD_INHERITED_INFO']
        self.assertEqual(temp['PIN_FLD_POID'].type, 'a')
        self.assertEqual(f2['PIN_FLD_POID'].type, 'a')
        self.assert_refcount(f2, 1)
        self.assert_refcount(temp, 1)
        self.assert_refcount(f, 2)
        self.assertIsNot(temp._flist, f2._flist)
        temp['PIN_FLD_POID'] = 'b'
        self.assertEqual(temp['PIN_FLD_POID'].type, 'b')
        self.assertEqual(f2['PIN_FLD_POID'].type, 'a')
        f3 = self.c.flist()
        f3['PIN_FLD_POID'] = 'c'
        f['PIN_FLD_INHERITED_INFO'] = f3
        self.assertEqual(f['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type, 'c')
        self.assert_refcount(f2, 1)
        self.assert_refcount(f3, 1)
        self.assert_refcount(temp, 1)
        self.assert_refcount(f, 1)
        self.assertEqual(f2['PIN_FLD_POID'].type, 'a')
        self.assertEqual(temp['PIN_FLD_POID'].type, 'b')
        self.assertEqual(f3['PIN_FLD_POID'].type, 'c')
        self.assertEqual(f['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type, 'c')
        del f
        result = str(f2)
        result = str(temp)
        result = str(f3)

    def test_overwrite_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        a = f['PIN_FLD_RESULTS'][0]
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b = self.c.flist()
        b['PIN_FLD_POID'] = 'b'
        f['PIN_FLD_RESULTS'][0] = b
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 1)
        self.assert_refcount(b, 1)
        self.assertEqual(f['PIN_FLD_RESULTS'][0]['PIN_FLD_POID'].type, 'b')
        self.assertEqual(b['PIN_FLD_POID'].type, 'b')
        self.assertEqual(a['PIN_FLD_POID'].type, 'a')
        del f
        result = str(b)

    def test_overwrite_any_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {10: {'PIN_FLD_POID': 'a'}}
        a = f['PIN_FLD_RESULTS'][10]
        b = self.c.flist()
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b['PIN_FLD_POID'] = 'b'
        f['PIN_FLD_RESULTS']['*'] = b
        self.assertEqual(a['PIN_FLD_POID'].type, 'a')
        self.assertEqual(b['PIN_FLD_POID'].type, 'b')
        self.assertEqual(f['PIN_FLD_RESULTS']['*']['PIN_FLD_POID'].type, 'b')
        self.assertIsNot(a._flist, b._flist)
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 1)
        self.assert_refcount(b, 1)

    def test_overwrite_any_array2(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {'*': {'PIN_FLD_POID': 'a'}}
        a = f['PIN_FLD_RESULTS']['*']
        b = self.c.flist()
        self.assert_refcount(f, 2)
        self.assert_refcount(a, 1)
        b['PIN_FLD_POID'] = 'b'
        f['PIN_FLD_RESULTS']['*'] = b
        self.assertEqual(a['PIN_FLD_POID'].type, 'a')
        self.assertEqual(b['PIN_FLD_POID'].type, 'b')
        self.assertEqual(f['PIN_FLD_RESULTS']['*']['PIN_FLD_POID'].type, 'b')
        self.assertIsNot(a._flist, b._flist)
        self.assert_refcount(f, 1)
        self.assert_refcount(a, 1)
        self.assert_refcount(b, 1)

    def test_get_on_empty(self):
        f = self.c.flist()
        f['PIN_FLD_ARGS'] = {}
        self.assertRaises(BRMError, f['PIN_FLD_ARGS']._get_array_flist, 1)
        f['PIN_FLD_ARGS'] = {}
        self.assertIsNone(f['PIN_FLD_ARGS'].get('*'))

    def test_str(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{"PIN_FLD_POID": "a"}]
        result = repr(f['PIN_FLD_RESULTS'])
        result = str(f['PIN_FLD_RESULTS'])

    def test_count(self):
        f = self.c.flist()
        f['PIN_FLD_POID'] = 'a'
        self.assertEqual(f.count(), 1)
        self.assertEqual(f.count(True), 1)
        f['PIN_FLD_INHERITED_INFO'] = {'PIN_FLD_POID': 'b'}
        self.assertEqual(f.count(), 2)
        self.assertEqual(f.count(True), 3)
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'c'}]
        self.assertEqual(f.count(), 3)
        self.assertEqual(f.count(True), 5)
        f['PIN_FLD_RESULTS'][0]['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'd'}]
        self.assertEqual(f.count(), 3)
        self.assertEqual(f.count(True), 7)

    def test_iter(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        for elem_id, flist in f['PIN_FLD_RESULTS'].items():
            self.assertEqual(elem_id, 0)
            self.assertEqual(flist['PIN_FLD_POID'].type, 'a')
        del f['PIN_FLD_RESULTS']
        f['PIN_FLD_RESULTS'] = {
            10: {'PIN_FLD_POID': 'b'}
        }
        self.assertTrue(list(f['PIN_FLD_RESULTS'].items()))
        for elem_id, flist in f['PIN_FLD_RESULTS'].items():
            self.assertEqual(elem_id, 10)
            self.assertEqual(flist['PIN_FLD_POID'].type, 'b')

        self.assertTrue(list(f['PIN_FLD_RESULTS'].keys()))
        for elem_id in f['PIN_FLD_RESULTS'].keys():
            self.assertEquals(elem_id, 10)

        self.assertTrue(list(f['PIN_FLD_RESULTS'].values()))
        for flist in f['PIN_FLD_RESULTS'].values():
            self.assertEqual(flist['PIN_FLD_POID'].type, 'b')

        for name in f.keys():
            self.assertEquals(name, 'PIN_FLD_RESULTS')

        for value in f.values():
            self.assertTrue(isinstance(value, BRMArray))

    def test_bool(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = []
        ar = f['PIN_FLD_RESULTS']
        self.assertFalse(bool(ar))
        ar[0] = {'PIN_FLD_POID': 'a'}
        self.assertTrue(bool(ar))
        ar[1] = {'PIN_FLD_POID': 'b'}
        self.assertTrue(bool(ar))

    def test_sort(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_STATUS': 1}, {'PIN_FLD_STATUS': 3}, {'PIN_FLD_STATUS': 2}]
        self.assertEquals([row['PIN_FLD_STATUS'] for row in f['PIN_FLD_RESULTS'].values()], [1, 3, 2])
        f.sort('PIN_FLD_RESULTS', 'PIN_FLD_STATUS')
        self.assertEquals([row['PIN_FLD_STATUS'] for row in f['PIN_FLD_RESULTS'].values()], [1, 2, 3])
        f.sort_reverse('PIN_FLD_RESULTS', 'PIN_FLD_STATUS')
        self.assertEquals([row['PIN_FLD_STATUS'] for row in f['PIN_FLD_RESULTS'].values()], [3, 2, 1])
        f.sort('PIN_FLD_RESULTS', ['PIN_FLD_STATUS'])
        self.assertEquals([row['PIN_FLD_STATUS'] for row in f['PIN_FLD_RESULTS'].values()], [1, 2, 3])
        f.sort_reverse('PIN_FLD_RESULTS', ['PIN_FLD_STATUS'])
        self.assertEquals([row['PIN_FLD_STATUS'] for row in f['PIN_FLD_RESULTS'].values()], [3, 2, 1])
        self.assertRaises(ValueError, f.sort, 'PIN_FLD_RESULTS')
        self.assertRaises(ValueError, f.sort_reverse, 'PIN_FLD_RESULTS')

        #fail = c.flist() # None of these raise an error
        #fail['PIN_FLD_STATUS'] = 1
        #self.assertRaises(BRMError, f._flist.sort_flist, fail._flist, 1)
        #self.assertRaises(BRMError, f._flist.sort_flist_reverse, fail._flist, 1)

    def test_in(self):
        f = self.c.flist({'PIN_FLD_RESULTS': [{'PIN_FLD_STATUS': 1}]})
        self.assertIn(0, f['PIN_FLD_RESULTS'])
        self.assertNotIn(1, f['PIN_FLD_RESULTS'])

    def test_pop(self):
        f = self.c.flist({'PIN_FLD_RESULTS': [{'PIN_FLD_STATUS': 1}]})
        self.assertIn(0, f['PIN_FLD_RESULTS'])
        self.assertEquals(f['PIN_FLD_RESULTS'].pop(0)['PIN_FLD_STATUS'], 1)
        self.assertNotIn(1, f['PIN_FLD_RESULTS'])

    def test_equals(self):
        f = self.c.flist({'PIN_FLD_RESULTS': [{'PIN_FLD_STATUS': 1}, {'PIN_FLD_STATUS': 2}]})
        f2 = self.c.flist({'PIN_FLD_RESULTS': [{'PIN_FLD_STATUS': 1}]})
        self.assertNotEquals(f, f2)
        f2['PIN_FLD_RESULTS'][1] = {'PIN_FLD_STATUS': 3}
        self.assertNotEquals(f, f2)
        f2['PIN_FLD_RESULTS'][1]['PIN_FLD_STATUS'] = 2
        self.assertEquals(f, f2)
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_STATUS': 1}]
        f2 = self.c.flist()
        f2['PIN_FLD_RESULTS']= {1: {'PIN_FLD_STATUS': 1}}
        self.assertNotEquals(f, f2)

    def test_in_with_null(self):
        f = self.c.flist()
        self.assertFalse('PIN_FLD_RESULTS' in f)
        f['PIN_FLD_RESULTS'] = {10: None}
        self.assertTrue('PIN_FLD_RESULTS' in f)
        self.assertTrue(10 in f['PIN_FLD_RESULTS'])
        self.assertFalse(0 in f['PIN_FLD_RESULTS'])

        del f
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS']['*'] = None
        self.assertIsNone(f['PIN_FLD_RESULTS']['*'])
        self.assertIsNone(f['PIN_FLD_RESULTS']['*'])
        self.assertIn('*', f['PIN_FLD_RESULTS'])
        self.assertFalse(bool(f['PIN_FLD_RESULTS']))

    def test_set_whole_array_null(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {10: {'PIN_FLD_POID': '/a'}}
        first = f['PIN_FLD_RESULTS'][10]
        f['PIN_FLD_RESULTS'] = None
        k, v = next(f['PIN_FLD_RESULTS'].items())
        self.assertEqual(k, 0)
        self.assertIsNone(v)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 1)
        f['PIN_FLD_RESULTS'][10] = {'PIN_FLD_POID': '/a'}
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 2)
        f['PIN_FLD_RESULTS'] = None
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 1)

        del f
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = None
        k, v = next(f['PIN_FLD_RESULTS'].items())
        self.assertEqual(k, 0)
        self.assertIsNone(v)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 1)

    def test_null_flist_on_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS'][10] = None
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])
        k, v = next(f['PIN_FLD_RESULTS'].items())
        self.assertEqual(k, 10)
        self.assertIsNone(v)
        self.assertIn('PIN_FLD_RESULTS', f)
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {10: None}
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])
        k, v = next(f['PIN_FLD_RESULTS'].items())
        self.assertEqual(k, 10)
        self.assertIsNone(v)
        self.assertIn('PIN_FLD_RESULTS', f)

    def test_null_access(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS'][10] = None
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {10: None}  # TODO this wasnt working (cough wasn't tested) on the old pybrm anyways however probably good thing to do
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])
        self.assertIsNone(f['PIN_FLD_RESULTS'][10])

    def test_clear_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {
            0: {'PIN_FLD_STATUS': 1},
            1: {'PIN_FLD_STATUS': 2},
        }
        self.assertEquals(len(f['PIN_FLD_RESULTS']), 2)
        f['PIN_FLD_RESULTS'].clear()
        self.assertEquals(len(f['PIN_FLD_RESULTS']), 0)


class TestMisc(TestBrm):
    def test_pin_virtual_time(self):
        pin_virtual_time()

    def test_client_log_level(self):
        self.assertRaises(ValueError, pybrm.pin_err_set_level, 100)

    def test_dict(self):
        f = self.c.flist({'PIN_FLD_POID': 'a'})
        self.assertEqual(f['PIN_FLD_POID'].type, 'a')
        f['PIN_FLD_INHERITED_INFO'] = {'PIN_FLD_POID': 'b'}
        self.assertEqual(f['PIN_FLD_INHERITED_INFO']['PIN_FLD_POID'].type, 'b')
        self.assertRaises(ValueError, f.__setitem__, 'PIN_FLD_INHERITED_INFO', 'abc')

    def test_attr(self):
        f = self.c.flist()
        f.PIN_FLD_POID = 'a'
        self.assertEqual(f.PIN_FLD_POID.type, 'a')
        f.PIN_FLD_INHERITED_INFO = {}
        f.PIN_FLD_INHERITED_INFO.PIN_FLD_POID = 'b'
        self.assertEqual(f.PIN_FLD_INHERITED_INFO.PIN_FLD_POID.type, 'b')
        self.assertRaises(ValueError, f.__setattr__, 'PIN_FLD_INHERITED_INFO', 'abc')

    def test_list_flist(self):
        f = self.c.flist(['PIN_FLD_POID', 'PIN_FLD_STATUS'])
        self.assertIsNone(f['PIN_FLD_POID'])
        self.assertEqual(f['PIN_FLD_STATUS'], 0)

    def test_set_flist(self):
        f = self.c.flist({'PIN_FLD_POID', 'PIN_FLD_STATUS'})
        self.assertIsNone(f['PIN_FLD_POID'])
        self.assertEqual(f['PIN_FLD_STATUS'], 0)

    def test_list_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        self.assertEqual(f['PIN_FLD_RESULTS'][0]['PIN_FLD_POID'].type, 'a')
        self.assertRaises(TypeError, f.__setitem__, 'PIN_FLD_RESULTS', 'abc')
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_RESULTS', 'abc')
        f['PIN_FLD_RESULTS'] = {}
        ar = f['PIN_FLD_RESULTS']
        ar[0] = {"PIN_FLD_POID": 'b'}
        self.assertEquals(ar[0]['PIN_FLD_POID'].type, 'b')

        del f['PIN_FLD_RESULTS']
        f['PIN_FLD_RESULTS'] = []
        self.assertEqual(len(f), 0)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 0)
        del f['PIN_FLD_RESULTS']
        self.assertEqual(len(f), 0)
        f['PIN_FLD_RESULTS'] = {}
        self.assertEqual(len(f), 0)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 0)

    def test_dict_array(self):
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {4: {'PIN_FLD_POID': 'a'}, 16: {'PIN_FLD_POID': 'b'}, '*': {'PIN_FLD_POID': 'any'}}
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 3)
        self.assertEqual(f['PIN_FLD_RESULTS'][4]['PIN_FLD_POID'].type, 'a')
        self.assertEqual(f['PIN_FLD_RESULTS'][16]['PIN_FLD_POID'].type, 'b')
        self.assertEqual(f['PIN_FLD_RESULTS']['*']['PIN_FLD_POID'].type, 'any')

        f['PIN_FLD_RESULTS'] = {
            0: {'PIN_FLD_POID': 'zero'},
            'PIN_ELEMID_ANY': {'PIN_FLD_POID': 'a'},
            -1: {'PIN_FLD_POID': 'b'},
            '*': {'PIN_FLD_POID': 'c'},
            '-1': {'PIN_FLD_POID': 'd'},
        }

        self.assertEqual(len(f['PIN_FLD_RESULTS']), 2)
        self.assertEqual(f['PIN_FLD_RESULTS'][0]['PIN_FLD_POID'].type, 'zero')
        self.assertEqual(f['PIN_FLD_RESULTS']['*']['PIN_FLD_POID'].type, 'd')

    def test_attr_array(self):
        f = self.c.flist()
        f.PIN_FLD_RESULTS = [{'PIN_FLD_POID': 'a'}]
        self.assertEqual(f.PIN_FLD_RESULTS[0].PIN_FLD_POID.type, 'a')
        self.assertRaises(TypeError, f.__setattr__, 'PIN_FLD_RESULTS', 'abc')
        f.PIN_FLD_RESULTS = {}
        ar = f.PIN_FLD_RESULTS
        ar[0] = {}
        ar[0].PIN_FLD_POID = 'b'
        self.assertEquals(ar[0].PIN_FLD_POID.type, 'b')

        del f.PIN_FLD_RESULTS
        f.PIN_FLD_RESULTS = []
        self.assertEqual(len(f), 0)
        self.assertEqual(len(f.PIN_FLD_RESULTS), 0)
        del f.PIN_FLD_RESULTS
        self.assertEqual(len(f), 0)
        f.PIN_FLD_RESULTS = {}
        self.assertEqual(len(f), 0)
        self.assertEqual(len(f.PIN_FLD_RESULTS), 0)

    def test_client_misc(self):
        pybrm.pin_err_set_level(1)
        self.assertRaises(ValueError, pybrm.pin_err_set_level, 100)
        pybrm.pin_err_set_logfile('default.pinlog')
        pybrm.pin_err_set_program('new_program')

    def test_bad_field_name(self):
        self.assertRaises(KeyError, pin_field_get_name, -1234)

    def test_parse_args_error(self):
        def do(func, *args, **kwargs):
            self.assertRaises(TypeError, func, *args, **kwargs)
        do(cbrm._FList, "a")
        f = self.c.flist()
        do(f._flist.xml, "hello")
        do(f._flist.drop_field, "hello")
        do(f._flist.drop_array, "hello")
        do(f._flist.set_poid, field="hello")
        do(f._flist.get_poid, "hello")
        do(f._flist.get_int, "hello")
        do(f._flist.get_enum, 'hello')
        do(f._flist.get_str, 'hello')
        do(f._flist.does_field_exist, "hello")
        do(f._flist.get_tstamp, 'hello')
        do(f._flist.get_decimal, 'hello')
        do(f._flist.get_flist, 'hello')
        do(f._flist.set_str,"hello")
        do(f._flist.set_tstamp, "hello")
        do(f._flist.set_int, "hello")
        do(f._flist.set_enum, "hello")
        do(f._flist.set_decimal, "hello")
        do(f._flist.get_array_flist, "a", "b", "c")
        do(f._flist.get_any_array_flist, "a", "b")
        do(f._flist.set_flist_on_array, "a", "a", "a")
        do(f._flist.set_substr, "a", value="a")
        do(f._flist.sort_flist, "hello", "hello")
        do(f._flist.sort_reverse_flist, "hello", "hello")
        do(f._flist.concat, "hello")
        do(f._flist.array_count, "hello")
        do(f._flist.array_init_iter, "hello")
        do(f._flist.opcode, "hello")
        do(pin_field_of_name, 1)
        do(pin_field_get_name, "foo")
        do(pin_field_get_type, "foo")
        do(f._flist.set_binstr, "hello")
        do(f._flist.get_binstr, "hello")
        do(f._flist.set_buf, "hello")
        do(f._flist.get_buf, "hello")
        do(f._flist.does_flist_exist_on_array, "hello", "hello")
        do(pybrm.pin_conf, 1, 1)


class TestSearch(TestBrm):
    def setUp(self):
        self.template = ' select X from foo where F1 = V1 '

    def assert_core(self, search):
        self.assertEqual(search['PIN_FLD_POID'].type, '/search')
        self.assertEqual(search['PIN_FLD_POID'].id, -1)
        self.assertEqual(search['PIN_FLD_POID'].revision, 0)
        self.assertEquals(search['PIN_FLD_TEMPLATE'], ' select X from foo where F1 = V1 ')

    def test_simple(self):
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1},
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertFalse(result_value)

        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_USAGE_TYPE': 'FOO'},
            results={'PIN_FLD_STATUS': None, 'PIN_FLD_USAGE_TYPE': None}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_USAGE_TYPE': 'FOO'})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEquals(result_value, {'PIN_FLD_STATUS': None, 'PIN_FLD_USAGE_TYPE': None})

        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1)],
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})

    def test_composite_struct(self):
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}},
            results={'PIN_FLD_INHERITED_INFO': {}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_INHERITED_INFO', result_value)
        self.assertFalse(result_value['PIN_FLD_INHERITED_INFO'])

        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}},
            results={'PIN_FLD_INHERITED_INFO': {'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_STATUS': 0}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_INHERITED_INFO', result_value)
        self.assertTrue(result_value['PIN_FLD_INHERITED_INFO'])
        self.assertEquals(result_value['PIN_FLD_INHERITED_INFO'], {'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_STATUS': 0})

    def test_special_args(self):
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 0}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 0}})

        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_FIELD': {'PIN_FLD_STATUS': 0}}
        )

        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_FIELD': [{'PIN_FLD_STATUS': 0}]})

        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_FIELD': [{'PIN_FLD_ARGS': [{'PIN_FLD_STATUS': 0}]}]}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_FIELD': [{'PIN_FLD_ARGS': [{'PIN_FLD_STATUS': 0}]}]})

        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_FIELD': {'PIN_FLD_RESULTS': {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_ARGS': {'PIN_FLD_STATUS': 1}}}}}
        )

        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1],
            {'PIN_FLD_FIELD': [
                {'PIN_FLD_RESULTS': [{
                    'PIN_FLD_INHERITED_INFO': {
                        'PIN_FLD_ARGS': [
                            {'PIN_FLD_STATUS': 1}
                        ]
                    }
                }]}
            ]}
        )

    def test_composite_array(self):
        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1)],
            results={'PIN_FLD_FIELD': {}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_FIELD', result_value)
        self.assertTrue(result_value)  # Because this has a subarray - even though the subarray is empty
        result_key, result_value = next(s['PIN_FLD_RESULTS']['*']['PIN_FLD_FIELD'].items())
        self.assertEquals(result_key, -1)
        self.assertFalse(result_value)  # subarray is empty

        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1), ('PIN_FLD_INHERITED_INFO', {'PIN_FLD_STATUS': 2})],
            results={'PIN_FLD_FIELD': {'PIN_FLD_USAGE_TYPE': None}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_FIELD', result_value)
        self.assertTrue(result_value)  # Because this has a subarray - even though the subarray is empty
        result_key, result_value = next(s['PIN_FLD_RESULTS']['*']['PIN_FLD_FIELD'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertTrue(result_value)  # subarray is empty  # TODO PIN_FLD_USAGE_TYPE is not getting set on the result
        self.assertEquals(len(result_value), 1)
        self.assertIn('PIN_FLD_USAGE_TYPE', result_value)
        self.assertEquals(result_value['PIN_FLD_USAGE_TYPE'], None)

    def test_null_result(self):
        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1)],
            results=None
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertIn('PIN_FLD_RESULTS', s)
        self.assertFalse(s['PIN_FLD_RESULTS'])
        self.assertIsNone(next(s['PIN_FLD_RESULTS'].values()))

    def test_non_dict_results(self):
        # Simple limited
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_USAGE_TYPE': 'FOO'},
            results=('PIN_FLD_STATUS', 'PIN_FLD_USAGE_TYPE')
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_USAGE_TYPE': 'FOO'})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEquals(result_value, {'PIN_FLD_STATUS': None, 'PIN_FLD_USAGE_TYPE': None})

        # Substruct all
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}},
            results={'PIN_FLD_INHERITED_INFO'}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_INHERITED_INFO', result_value)
        self.assertFalse(result_value['PIN_FLD_INHERITED_INFO'])

        # Substruct limited
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1, 'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}},
            results={'PIN_FLD_INHERITED_INFO': {'PIN_FLD_USAGE_TYPE', 'PIN_FLD_STATUS'}}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_INHERITED_INFO', result_value)
        self.assertTrue(result_value['PIN_FLD_INHERITED_INFO'])
        self.assertEquals(result_value['PIN_FLD_INHERITED_INFO'], {'PIN_FLD_USAGE_TYPE': None, 'PIN_FLD_STATUS': 0})

        # Array all
        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1)],
            results=['PIN_FLD_FIELD']
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_FIELD', result_value)
        self.assertTrue(result_value)  # Because this has a subarray - even though the subarray is empty
        result_key, result_value = next(s['PIN_FLD_RESULTS']['*']['PIN_FLD_FIELD'].items())
        self.assertEquals(result_key, -1)
        self.assertFalse(result_value)  # subarray is empty

        # Array limited
        s = self.c.search_build_flist(
            template=self.template,
            args=[('PIN_FLD_STATUS', 1), ('PIN_FLD_INHERITED_INFO', {'PIN_FLD_STATUS': 2})],
            results={'PIN_FLD_FIELD': ['PIN_FLD_USAGE_TYPE']}
        )
        self.assert_core(s)
        self.assertEquals(s['PIN_FLD_ARGS'][1], {'PIN_FLD_STATUS': 1})
        self.assertEquals(s['PIN_FLD_ARGS'][2], {'PIN_FLD_INHERITED_INFO': {'PIN_FLD_STATUS': 2}})
        result_key, result_value = next(s['PIN_FLD_RESULTS'].items())
        self.assertEquals(result_key, -1)  # elem any
        self.assertEqual(len(result_value), 1)
        self.assertIn('PIN_FLD_FIELD', result_value)
        self.assertTrue(result_value)  # Because this has a subarray - even though the subarray is empty
        result_key, result_value = next(s['PIN_FLD_RESULTS']['*']['PIN_FLD_FIELD'].items())
        self.assertEquals(result_key, -1)
        self.assertTrue(result_value)  # subarray is empty # TODO PIN_FLD_USAGE_TYPE not being set
        self.assertEquals(len(result_value), 1)
        self.assertIn('PIN_FLD_USAGE_TYPE', result_value)
        self.assertEquals(result_value['PIN_FLD_USAGE_TYPE'], None)

    def test_search_count_only(self):
        s = self.c.search_build_flist(
            template=self.template,
            args={'PIN_FLD_STATUS': 1},
            is_count_only=True
        )
        self.assert_core(s)
        self.assertIsNone(s['PIN_FLD_RESULTS'][0])

    def test_mock_search(self):
        c = Client()
        _search_build_flist = c.search_build_flist

        def opcode(*args, **kwargs):
            return 1

        def search_build_flist(*args, **kwargs):
            flist = Mock(_search_build_flist(*args, **kwargs))
            flist.side_effect = opcode
            return flist

        c.search_build_flist = search_build_flist

        out = c.search(
            template=self.template,
            args={'PIN_FLD_STATUS': 1},
        )

        self.assertEqual(out, 1)

    def test_mock_search_count_only(self):
        c = Client()
        _search_build_flist = c.search_build_flist

        class Fake:
            def keys(self):
                return (i for i in [10])

        def opcode(*args, **kwargs):
            return {'PIN_FLD_RESULTS': Fake()}

        def search_build_flist(*args, **kwargs):
            flist = Mock(_search_build_flist(*args, **kwargs))
            flist.side_effect = opcode
            return flist

        c.search_build_flist = search_build_flist

        out = c.search(
            template=self.template,
            args={'PIN_FLD_STATUS': 1},
            is_count_only=True
        )

        self.assertEquals(out, 10)


class TestBadCMInPinConf(unittest.TestCase):

    def test_cm_is_down(self):
        pin_conf_path = os.path.join(current_directory, 'pin_conf_test', 'pin.conf')
        with open(pin_conf_path, 'r') as f:
            old_contents = f.read()

        try:
            new_contents = old_contents.replace('${BRM_CM_PORT}', '22')
            with open(pin_conf_path, 'w') as f:
                f.write(new_contents)
            change_into_pin_conf_test_directory(True)
            self.assertEquals(pin_conf('-', 'abc'), 'xyz')
            self.assertRaises(BRMError, Client)
        finally:
            change_into_test_directory(True)
            with open(pin_conf_path, 'w') as f:
                f.write(old_contents)

    def test_missing_pin_conf_arg(self):
        pin_conf_path = os.path.join(current_directory, 'pin_conf_test', 'pin.conf')
        with open(pin_conf_path, 'r') as f:
            old_contents = f.read()

        try:
            new_contents = old_contents.replace('- nap cm_ptr', '#- nap cm_ptr')
            with open(pin_conf_path, 'w') as f:
                f.write(new_contents)
            change_into_pin_conf_test_directory(True)
            self.assertEquals(pin_conf('-', 'abc'), 'xyz')
            self.assertRaises(BRMError, Client)
        finally:
            change_into_test_directory(True)
            with open(pin_conf_path, 'w') as f:
                f.write(old_contents)


class TestLogging(unittest.TestCase):
    def test_illegal_log_file(self):
        log_file = 'pybrm_test_illegal_log'
        try:
            os.mkdir(log_file)
            self.assertRaises(IOError, pybrm.pybrm._check_log_file_is_legal, log_file)
        finally:
            os.rmdir(log_file)

    def test_brm_to_python_log_leve(self):
        self.assertEquals(logging.DEBUG, pybrm.brm_to_python_log_level(3))
        self.assertRaises(KeyError, pybrm.brm_to_python_log_level, 10)

    def test_log_handler(self):
        # TODO interesting, if you delete default.pinlog, all new writes dont do anything, you have to change to something else and change back
        # It may be helpful to detect this condition and do it automatically somehow?
        self.assertEquals(pin_conf('-', 'abc'), 'def')
        try:
            os.remove('test_log_handler.pinlog')
        except IOError:
            pass
        pybrm.pin_err_set_logfile('test_log_handler.pinlog')
        try:
            logger = logging.getLogger(__name__)
            logger.addHandler(pybrm.BRMHandler())
            logger.setLevel(logging.DEBUG)

            pybrm.pin_err_set_level(pybrm.PIN_ERR_LEVEL_ERROR)
            logger.error("pybrm_log_test error error")
            logger.warning('pybrm_log_test error warning')
            logger.debug("pybrm_log_test error debug")

            pybrm.pin_err_set_level(pybrm.PIN_ERR_LEVEL_WARNING)
            logger.error("pybrm_log_test warning error")
            logger.warning('pybrm_log_test warning warning')
            logger.debug("pybrm_log_test warning debug")

            pybrm.pin_err_set_level(pybrm.PIN_ERR_LEVEL_DEBUG)
            logger.error("pybrm_log_test debug error")
            logger.warning('pybrm_log_test debug warning')
            logger.debug("pybrm_log_test debug debug")

            with open('test_log_handler.pinlog', 'r') as f:
                contents = f.read()

            self.assertIn('pybrm_log_test error error', contents)
            self.assertNotIn('pybrm_log_test error warning', contents)
            self.assertNotIn('pybrm_log_test error debug', contents)

            self.assertIn('pybrm_log_test warning error', contents)
            self.assertIn('pybrm_log_test warning warning', contents)
            self.assertNotIn('pybrm_log_test warning debug', contents)

            self.assertIn('pybrm_log_test debug error', contents)
            self.assertIn('pybrm_log_test debug warning', contents)
            self.assertIn('pybrm_log_test debug debug', contents)

            pybrm.pin_err_set_logfile('default.pinlog')
        finally:
            try:
                os.remove('test_log_handler.pinlog')
            except IOError:
                pass


class TestPinConf(unittest.TestCase):
    def test_missing_pin_conf(self):
        self.assertIsNone(pybrm.pin_conf('pybrm', 'missing_value'))


class TestCapsule(TestBrm):
    def test_from_c_call_python(self):
        # Pretend we are from C here:

        c_flist = self.c.flist()
        c_flist['PIN_FLD_STATUS'] = 1
        c_capsule = c_flist.capsule()  # New copy, need to dealloc

        # pretend we are in Python here:
        py_flist = self.c.flist(capsule=c_capsule)
        py_flist['PIN_FLD_STATUS'] = 2
        py_capsule = py_flist.capsule()  # New copy, need to dealloc

        # pretend we are in C here:
        result = self.c.flist(capsule=py_capsule)
        self.assertEquals(result['PIN_FLD_STATUS'], 2)
        # C would dealloc via PIN_FLIST_DESTROY_EX here:
        # This is how to deallocate a new copy capsule in Python, by creating a new FList with copy_capsule=False
        # when the FList deallocates, it will destroy the memory associated with the capsule
        del_c_capsule = self.c.flist(capsule=c_capsule, copy_capsule=False)
        del_py_capsule = self.c.flist(capsule=py_capsule, copy_capsule=False)

        # If after this point you tried to create a new flist using this capsule, it would segfault

    def test_from_python_call_c_with_ctypes(self):
        py_flist = self.c.flist()
        py_flist['PIN_FLD_STATUS'] = 1
        # Not taking a copy, so cannot use py_capsule once py_flist is deallocated!
        py_capsule = py_flist.capsule(copy_capsule=False)
        client_capsule = self.c.capsule()  # client capsule never copies
        ebufp_capsule = self.c.ebufp_capsule()  # ebufp capsule never copies

        ## pretend to call some ctypes with the capsule
        # pretend it sets the ebuf but doesn't reset it
        self.c._set_ebuf_error()  # this function only exists for this next test
        self.assertRaises(BRMError, self.c.raise_ebuf_error)
        # this shouldn't raise as it's cleared the ebuf
        self.c.raise_ebuf_error()

    def test_no_memory_leaks(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        for _ in range(1024):
            # No memory leak, but cannot result capsule after `f` deallocates or it will segfault
            capsule = f.capsule(copy_capsule=False)

    def test_no_memory_leaks_2(self):
        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        for _ in range(1024):
            # No memory leak
            capsule = f.capsule(copy_capsule=True)
            a = self.c.flist(capsule=capsule, copy_capsule=False)

    def test_errors(self):
        self.assertRaises(TypeError, self.c.flist, capsule='hello')
        try:
            self.c.flist(capsule="hello")
        except TypeError as ex:
            self.assertIn('Expecting a PyCapsule type', str(ex))

        f = self.c.flist()
        f['PIN_FLD_STATUS'] = 1
        capsule = f.capsule(copy_capsule=False)  # not a copy, cannot use capsule once f deallocates~

        f2 = self.c.flist()
        # Cannot set capsule on previously open flist
        self.assertRaises(ValueError, f2._flist.set_capsule, capsule, True)

        ctypes.pythonapi.PyCapsule_New.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
        ctypes.pythonapi.PyCapsule_New.restype = ctypes.py_object
        capsule = ctypes.pythonapi.PyCapsule_New(b"foo", b"bar", None)
        self.assertRaises(ValueError, self.c.flist, capsule=capsule)
        try:
            self.c.flist(capsule=capsule)
        except ValueError as ex:
            self.assertIn('PyCapsule_GetPointer called with incorrect name', str(ex))

    def test_not_open(self):
        c = Client()
        self.assertTrue(c.is_open())
        c.close()
        self.assertFalse(c.is_open())
        self.assertIsNone(c.capsule())
        self.assertIsNone(c.ebufp_capsule())
        self.assertIsNone(c.raise_ebuf_error())
        self.assertIsNone(c._set_ebuf_error())


class TestVirtualArray(TestBrm):
    def test_all(self):
        field_num = pin_field_of_name('PIN_FLD_RESULTS')
        f = self.c.flist()
        self.assertFalse(f._virtual_arrays)
        self.assertRaises(KeyError, f.__getitem__, 'PIN_FLD_RESULTS')
        self.assertFalse(f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)
        self.assertIn('PIN_FLD_RESULTS', f)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 0)
        self.assertFalse(bool(f['PIN_FLD_RESULTS']))

        del f['PIN_FLD_RESULTS']
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        self.assertRaises(KeyError, f.__getitem__, 'PIN_FLD_RESULTS')

        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)
        self.assertIn('PIN_FLD_RESULTS', f)
        self.assertEqual(len(f['PIN_FLD_RESULTS']), 0)
        self.assertFalse(bool(f['PIN_FLD_RESULTS']))

        f['PIN_FLD_RESULTS'][0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f['PIN_FLD_RESULTS'][0]
        self.assertIn(field_num, f._virtual_arrays)

        f['PIN_FLD_RESULTS'][0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f['PIN_FLD_RESULTS'][1] = {'PIN_FLD_STATUS': 2}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f['PIN_FLD_RESULTS'][1]
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f['PIN_FLD_RESULTS'][0]
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f['PIN_FLD_RESULTS'][0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f['PIN_FLD_RESULTS'].pop(0)
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f['PIN_FLD_RESULTS'][0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f['PIN_FLD_RESULTS'][1] = {'PIN_FLD_STATUS': 2}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f['PIN_FLD_RESULTS'].clear()
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f = self.c.flist()
        self.assertIsNone(f.get('PIN_FLD_RESULTS'))
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        self.assertIsNotNone(f.get('PIN_FLD_RESULTS'))
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        self.assertIsNotNone(f.get('PIN_FLD_RESULTS'))

        f = self.c.flist()
        self.assertRaises(KeyError, f.__getitem__, 'PIN_FLD_RESULTS')
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        f['PIN_FLD_RESULTS']
        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        f['PIN_FLD_RESULTS']

        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = [{'PIN_FLD_POID': 'a'}]
        self.assertNotIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = {0: {'PIN_FLD_POID': 'a'}}
        self.assertNotIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = []
        self.assertIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = None
        self.assertNotIn(field_num, f._virtual_arrays)
        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)

        f = self.c.flist()
        f['PIN_FLD_RESULTS'] = {}
        self.assertIn(field_num, f._virtual_arrays)
        del f['PIN_FLD_RESULTS']
        self.assertNotIn(field_num, f._virtual_arrays)

    def test_attr_all(self):
        field_num = pin_field_of_name('PIN_FLD_RESULTS')
        f = self.c.flist()
        self.assertFalse(f._virtual_arrays)
        self.assertRaises(AttributeError, f.__getattr__, 'PIN_FLD_RESULTS')
        self.assertFalse(f._virtual_arrays)
        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)
        self.assertIn('PIN_FLD_RESULTS', f)
        self.assertEqual(len(f.PIN_FLD_RESULTS), 0)
        self.assertFalse(bool(f.PIN_FLD_RESULTS))

        del f.PIN_FLD_RESULTS
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        self.assertRaises(AttributeError, f.__getattr__, 'PIN_FLD_RESULTS')

        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)
        self.assertIn('PIN_FLD_RESULTS', f)
        self.assertEqual(len(f.PIN_FLD_RESULTS), 0)
        self.assertFalse(bool(f.PIN_FLD_RESULTS))

        f.PIN_FLD_RESULTS[0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f.PIN_FLD_RESULTS[0]
        self.assertIn(field_num, f._virtual_arrays)

        f.PIN_FLD_RESULTS[0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f.PIN_FLD_RESULTS[1] = {'PIN_FLD_STATUS': 2}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f.PIN_FLD_RESULTS[1]
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        del f.PIN_FLD_RESULTS[0]
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f.PIN_FLD_RESULTS[0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f.PIN_FLD_RESULTS.pop(0)
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f.PIN_FLD_RESULTS[0] = {'PIN_FLD_STATUS': 1}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f.PIN_FLD_RESULTS[1] = {'PIN_FLD_STATUS': 2}
        self.assertNotIn(field_num, f._virtual_arrays)
        self.assertFalse(f._virtual_arrays)
        f.PIN_FLD_RESULTS.clear()
        self.assertIn(field_num, f._virtual_arrays)
        self.assertTrue(f._virtual_arrays)

        f = self.c.flist()
        self.assertIsNone(f.get('PIN_FLD_RESULTS'))
        f = self.c.flist()
        f.PIN_FLD_RESULTS = {}
        self.assertIsNotNone(f.get('PIN_FLD_RESULTS'))
        f = self.c.flist()
        f.PIN_FLD_RESULTS = [{'PIN_FLD_POID': 'a'}]
        self.assertIsNotNone(f.get('PIN_FLD_RESULTS'))

        f = self.c.flist()
        self.assertRaises(AttributeError, f.__getattr__, 'PIN_FLD_RESULTS')
        f = self.c.flist()
        f.PIN_FLD_RESULTS = {}
        f.PIN_FLD_RESULTS
        f = self.c.flist()
        f.PIN_FLD_RESULTS = [{'PIN_FLD_POID': 'a'}]
        f.PIN_FLD_RESULTS

        f = self.c.flist()
        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = [{'PIN_FLD_POID': 'a'}]
        self.assertNotIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = {0: {'PIN_FLD_POID': 'a'}}
        self.assertNotIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = []
        self.assertIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = None
        self.assertNotIn(field_num, f._virtual_arrays)
        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)

        f = self.c.flist()
        f.PIN_FLD_RESULTS = {}
        self.assertIn(field_num, f._virtual_arrays)
        del f.PIN_FLD_RESULTS
        self.assertNotIn(field_num, f._virtual_arrays)

if __name__ == '__main__':
    unittest.main()

from pybrm.cbrm import pin_field_of_name, pin_field_get_type, pin_field_get_name, pcm_opname_to_opcode

_fields = {}
_fields_by_number = {}
_opcodes = {}


def opcode_by_name(opname):
    opcode = _opcodes.get(opname)
    if opcode is None:
        opcode = pcm_opname_to_opcode(opname)
        _opcodes[opname] = opcode
    return opcode


def _field_info_by_name(field_name):
    field_info = _fields.get(field_name)
    if field_info is None:
        field_info = _cache_field_name(field_name)
    return field_info


def _field_info_by_number(field_number):
    field_info = _fields_by_number.get(field_number)
    if field_info is None:
        field_info = _cache_field_number(field_number)
    return field_info


def field_by_identifier(identifier):
    if isinstance(identifier, str):
        field_info = _field_info_by_name(identifier)
    elif isinstance(identifier, int):
        field_info = _field_info_by_number(identifier)
    else:
        raise TypeError('identifier should be str or int, not %s' % identifier)
    return field_info['field_number']


def field_type_by_identifier(identifier):
    if isinstance(identifier, str):
        field_info = _field_info_by_name(identifier)
    elif isinstance(identifier, int):
        field_info = _field_info_by_number(identifier)
    else:
        raise TypeError('identifier should be str or int, not %s' % identifier)
    return field_info['field_type']


def field_name_by_identifier(identifier):
    if isinstance(identifier, str):
        field_info = _field_info_by_name(identifier)
    elif isinstance(identifier, int):
        field_info = _field_info_by_number(identifier)
    else:
        raise TypeError('identifier should be str or int, not %s' % identifier)
    return field_info['field_name']


def _cache_field_name(field_name):
    field_number = pin_field_of_name(field_name)
    field_type = pin_field_get_type(field_number)
    field_info = {
        'field_name': field_name,
        'field_number': field_number,
        'field_type': field_type
    }
    _fields[field_name] = field_info
    _fields_by_number[field_number] = field_info
    return field_info


def _cache_field_number(field_number):
    field_name = pin_field_get_name(field_number)
    # Cannot trust field_number !
    # E.g. PIN_FIELD_GET_NAME(16) == 'PIN_FLD_POID'
    #      PIN_FIELD_GET_TYPE(16) == 0 !
    # But  PIN_FIELD_OG_NAME('PIN_FLD_POID') = 117440528
    #      PIN_GET_FET_TYPE(117440528) == 7 <-- correct
    # Therefore if user passes in 16, then return 117440528
    real_field_number = pin_field_of_name(field_name)
    field_type = pin_field_get_type(real_field_number)
    field_info = {
        'field_name': field_name,
        'field_number': real_field_number,
        'field_type': field_type
    }
    _fields_by_number[field_number] = field_info
    _fields_by_number[real_field_number] = field_info
    _fields[field_name] = field_info
    return _fields_by_number[field_number]


all_flags = {
    'PCM_BUF_FLAG_XBUF': 0x0001,
    'PCM_BUF_FLAG_XBUF_READ': 0x0002,
    'PCM_FLDFLG_TYPE_ONLY': 0x0002,
    'PCM_FLDFLG_NO_QUOTE': 0x0004,
    'PCM_FLDFLG_WRWNP': 0x0008,
    'PCM_FLDFLG_FIFO': 0x0100,
    'PCM_FLDFLG_CMPREV': 0x0010,
    'PCM_FLDFLG_UNICODE': 0x0020,
    'PCM_FLDFLG_ENCRYPTED': 0x0040,
    'PCM_FLDFLG_FLIST_HEAP': 0x0100,
    'PCM_FLDFLG_DO_ROBJ': 0x0200,
    'PCM_FLDFLG_DB_ONLY': 0x0400,
    'PCM_FLDFLG_ID_ONLY': 0x0800,
    'PCM_FLDFLG_REV_ONLY': 0x1000,
    'PCM_RECID_ALL': 0xFFFFFFFF,
    'PCM_RECID_ASSIGN': 0xFFFFFFFe,
    'PCM_RECID_MAX': 0xFFFF0000,
    'PIN_ELEMID_ANY': 0xFFFFFFFF,  # PCM_RECID_ALL,
    'PIN_ELEMID_ASSIGN': 0xFFFFFFFe,  # PCM_RECID_ASSIGN,
    'PIN_ELEMID_MAX': 0xFFFF0000,  # PCM_RECID_MAX,
    'SRCH_CALC_ONLY': 0xFF,
    'SRCH_CALC_ONLY_1': 1,
    'SRCH_DISTINCT': 256,
    'SRCH_EXACT': 512,
    'SRCH_WITHOUT_POID': 1024,
    'SRCH_UNION_TT': 2048,
    'SRCH_ACCURATE': 4096,
    'PIN_TYPE_NO': 0,
    'PIN_TYPE_YES': 1,
    'PIN_BOOLEAN_FALSE': 0,
    'PIN_BOOLEAN_TRUE': 1,
    'PIN_RESULT_FAIL': 0,
    'PIN_RESULT_PASS': 1,
    'PCM_CONTEXT_CLOSE_FD_ONLY': 0x01,
    'PCM_OPFLG_NO_DESCEND': 0x0002,
    'PCM_OPFLG_CM_LOOPBACK': 0x0002,
    'PCM_OPFLG_META_ONLY': 0x0004,
    'PCM_OPFLG_EM_LOOPBACK': 0x0004,
    'PCM_OPFLG_SUPPRESS_DESC': 0x0008,
    'PCM_OPFLG_CUST_FLDS_ONLY': 0x8000,
    'PCM_OPFLG_REV_CHECK': 0x0008,
    'PCM_OPFLG_SET_REV_DELETED': 0x0008,
    'PCM_OPFLG_FM_LOOPBACK': 0x0008,
    'PCM_OPFLG_TIMOS_LOOPBACK': 0x0010,
    'PCM_OPFLG_TIMOS_PEER_LOOPBACK': 0x0020,
    'PCM_OPFLG_READ_DB': 0x2000000,
    'PCM_OPFLG_COUNT_ONLY': 0x0010,
    'PCM_OPFLG_NO_LOCK': 0x8000000,
    'PCM_OPFLG_ADD_ENTRY': 0x0020,
    'PCM_OPFLG_USE_POID_GIVEN': 0x0040,
    'PCM_OPFLG_USE_LOCATOR_SRVC': 0x0040,
    'PCM_OPFLG_CALC_ONLY': 0x0080,
    'PCM_OPFLG_READ_RESULT': 0x0100,
    'PCM_OPFLG_SORT_DESC': 0x0010,
    'PCM_OPFLG_SORT_ASCE': 0x0080,
    'PCM_OPFLG_NO_RESULTS': 0x0200,
    'PCM_OPFLG_CACHEABLE': 0x0400,
    'PCM_OPFLG_SUPPRESS_AUDIT': 0x0800,
    'PCM_OPFLG_IGNORE_ERR': 0x1000,
    'PCM_OPFLG_READ_UNCOMMITTED': 0x0800,
    'PCM_OPFLG_READ_DELETED_FIELDS': 0x200000,
    'PCM_OPFLG_USE_NULL': 0x1000,
    'PCM_OPFLG_NO_DB_FILTER': 0x1000,
    'PCM_OPFLG_USE_POID_NEAREST': 0x8000,
    'PCM_OPFLG_USE_POID_PREV': 0x2000,
    'PCM_OPFLG_USE_POID_NEXT': 0x4000,
    'PCM_OPFLG_BRAND_READ': 0x2000,
    'PCM_OPFLG_USE_ROUTING_DB_CACHE': 0x10000,
    'PCM_OPFLG_LOCK_OBJ': 0x20000,
    'PCM_TRANS_OPEN_LOCK_OBJ': 0x20000,  # PCM_OPFLG_LOCK_OBJ,
    'PCM_OPFLG_LOCK_DEFAULT': 0x400000,
    'PCM_TRANS_OPEN_LOCK_DEFAULT': 0x400000,  # PCM_OPFLG_LOCK_DEFAULT,
    'PCM_OPFLG_LOCK_NONE': 0x200000,
    'PCM_OPFLG_SEARCH_DB': 0x800000,
    'PCM_OPFLG_SEARCH_PARTITIONS': 0x10000000,
    'PCM_OPFLG_SEARCH_ONE_PARTITION': 0x20000000,
    'PCM_OPFLG_EXEC_SPROC_ON_DB': 0x800000,
    'PCM_OPFLG_SEARCH_SDS': 0x40000,
    'PCM_OPFLG_ORDER_BY_REC_ID': 0x80000,
    'PCM_OPFLG_SRCH_CALC_RESULTS': 0x100000,
    'PCM_TRANS_OPEN_READONLY': 0x00000,
    'PCM_TRANS_OPEN_READWRITE': 0x10000,
    'PCM_TRANS_OPEN_GLOBALTRANSACTION': 0x20000000,
    'PCM_OPFLG_USE_GIVEN_POID_DB_NUMBER': 0x40000000,
    'PCM_OPFLG2_BY_REF': 0x00000001,
    'PCM_OPFLG_RATE_WITH_DISCOUNTING': 0x100000,
    'PCM_SEARCH_EXEC_ONTIMOS': 0x10000,
    'PIN_FLD_PLATFORM_SOLARIS': 1,
    'PIN_FLD_PLATFORM_HP': 2,
    'PIN_XML_TYPE': 0x000001,
    'PIN_XML_FLDNO': 0x000002,
    'PIN_XML_BY_TYPE': 0x000004,
    'PIN_XML_BY_NAME': 0x000008,
    'PIN_XML_BY_SHORT_NAME': 0x000010,
    'PIN_STR_MODE_DETAIL': 0,
    'PIN_STR_MODE_COMPACT': 1,
    'PIN_STR_MODE_BINARY': 2,
    'PIN_STR_MODE_MASK': 4,
    'PCM_CANON_INFLAG_ALLOW_WCARDS': 1,
    'PCM_CANON_OUTFLAG_CANON_ESCAPE': 1,
    'PIN_VALIDITY_UNIT_MASK': 0x00000F00,
    'PIN_VALIDITY_OFFSET_MASK': 0xFFFFF000,
    'PIN_VALIDITY_MODE_MASK': 0x000000FF,
    'PIN_VALIDITY_OFFSET_SHIFT': 12,
    'PIN_VALIDITY_UNIT_SHIFT': 8,
    'PIN_VALIDITY_MAX_OFFSET_SIZE': 0xFFFFF,
    'PIN_VALIDITY_MAX_UNIT_SIZE': 0xF,
    'PIN_VALIDITY_MAX_MODE_SIZE': 0xFF,
    'XA_TRANS_NOFLAGS': 0,
    'XA_TRANS_FOR_RECOVERY_OPS': 1,
    'XA_TRANS_TMJOIN': 2,
    'XA_TRANS_TMRESUME': 3,
    'XA_TRANS_TWOPHASE': 0,
    'XA_TRANS_ONEPHASE': 1,
}

from dateutil import parser

from dlms_cosem import cosem, enumerations
from dlms_cosem.cosem import selective_access
from dlms_cosem.cosem.selective_access import RangeDescriptor
from dlms_cosem.cosem.capture_object import CaptureObject
from dlms_cosem.cosem import CosemAttribute, Obis
from dlms_cosem.protocol.xdlms import GetRequestFactory


def test_capture_object_definition():
    x = selective_access.CaptureObject(
        cosem_attribute=cosem.CosemAttribute(
            interface=enumerations.CosemInterface.CLOCK,
            instance=cosem.Obis(0, 0, 1, 0, 0, 255),
            attribute=2,
        ),
        data_index=0,
    )

    assert x.to_bytes() == (
        b"\x02\x04"  # structure of 4 elements
        b"\x12\x00\x08"  # Clock interface class (unsigned long int)
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # Clock instance octet string of 0.0.1.0.0.255
        b"\x0f\x02"  # attribute index  = 2 (integer)
        b"\x12\x00\x00"  # data index  = 0 (long unsigned)
    )


def test_range_descriptor1():
    data = (
        b"\xc0"  # Get request
        b"\x01"  # normal
        b"\xc1"  # invoke id and priority
        b"\x00\x07"  # Profile generic
        b"\x01\x00c\x01\x00\xff"  # 1.0.99.1.0.255
        b"\x02"  # Attribute 2 =  buffer
        b"\x01"  # non default value
        b"\x01"  # descriptor 1 (range-access)
        b"\x02\x04"  # strucutre of 4 elements
        b"\x02\x04"  # strucutre of 4 elements
        b"\x12\x00\x08"  # clock interface class
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # clock instance name. 0.0.1.0.0.255
        b"\x0f\x02"  # attribute 2
        b"\x12\x00\x00"  # data index = 0
        b"\t\x0c\x07\xe2\x06\x01\xff\x00\x03\x00\xff\xff\x88\x80"  # from date
        b"\t\x0c\x07\xe5\x01\x06\xff\x00\x03\x00\xff\xff\xc4\x00"  # to date
        b"\x01\x00"  # all columns
    )
    assert data

    data2 = (
        b"\xc0\x01\xc1\x00\x07\x01\x00c\x01\x00\xff\x02\x01\x01"
        b"\x02\x04"
        b"\x02\x04"
        b"\x12\x00\x08"
        b"\t\x06\x00\x00\x01\x00\x00\xff"
        b"\x0f\x02"
        b"\x12\x00\x00"
        b"\t\x0c\x07\xe2\x02\x0c\xff\x00\x00\x00\x00\x80\x00\x00"
        b"\t\x0c\x07\xe3\x02\x0c\xff\x00\x00\x00\x00\x80\x00\x00"
        b"\x01\x00"
    )
    assert data2


def test_range_descriptor_to_bytes():
    rd = RangeDescriptor(
        restricting_object=selective_access.CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(0, 0, 1, 0, 0, 255),
                attribute=2,
            ),
            data_index=0,
        ),
        from_value=parser.parse("2020-01-01T00:03:00+02:00"),
        to_value=parser.parse("2020-01-06T00:03:00+01:00"),
    )
    data = b"\x01\x02\x04\x02\x04\x12\x00\x08\t\x06\x00\x00\x01\x00\x00\xff\x0f\x02\x12\x00\x00\t\x0c\x07\xe4\x01\x01\xff\x00\x03\x00\x00\xff\x88\xff\t\x0c\x07\xe4\x01\x06\xff\x00\x03\x00\x00\xff\xc4\xff\x01\x00"
    assert rd.to_bytes() == data


def test_range_descriptor_to_bytes_with_selected_values():
    rd = RangeDescriptor(
        restricting_object=selective_access.CaptureObject(
            cosem_attribute=cosem.CosemAttribute(
                interface=enumerations.CosemInterface.CLOCK,
                instance=cosem.Obis(0, 0, 1, 0, 0, 255),
                attribute=2,
            ),
            data_index=0,
        ),
        from_value=parser.parse("2020-01-01T00:03:00+02:00"),
        to_value=parser.parse("2020-01-06T00:03:00+01:00"),
        selected_values=[
            CaptureObject(
                cosem_attribute=CosemAttribute(
                    interface=1,
                    instance=Obis(a=0, b=0, c=96, d=17, e=4, f=255),
                    attribute=2,
                ),
                data_index=0,
            ),
            CaptureObject(
                cosem_attribute=CosemAttribute(
                    interface=1,
                    instance=Obis(a=0, b=0, c=96, d=11, e=0, f=255),
                    attribute=2,
                ),
                data_index=0,
            ),
        ],
    )

    # the same as test_range_descriptor_to_bytes but removing 2 trailing bytes
    data = b"\x01\x02\x04\x02\x04\x12\x00\x08\t\x06\x00\x00\x01\x00\x00\xff\x0f\x02\x12\x00\x00\t\x0c\x07\xe4\x01\x01\xff\x00\x03\x00\x00\xff\x88\xff\t\x0c\x07\xe4\x01\x06\xff\x00\x03\x00\x00\xff\xc4\xff"

    data+=bytes.fromhex(
        "0102" +
        "0204 120001 09060000601104FF 0F02 120000" +
        "0204 120001 09060000600B00FF 0F02 120000"
    )
    assert rd.to_bytes() == data


def test_parse_range_descriptor():

    """
    Profile: 1 (15 minutes profile)
    From: 01.10.2017 00:00
    To: 01.10.2017 01:00

    """

    data = b"\xc0\x01\xc1\x00\x07\x01\x00c\x01\x00\xff\x02\x01\x01\x02\x04\x02\x04\x12\x00\x08\t\x06\x00\x00\x01\x00\x00\xff\x0f\x02\x12\x00\x00\t\x0c\x07\xe1\n\x01\x07\x00\x00\x00\x00\xff\xc4\x80\t\x0c\x07\xe1\n\x01\x07\x01\x00\x00\x00\xff\xc4\x80\x01\x00"
    g = GetRequestFactory.from_bytes(data)

    access = (
        b"\x01"  # Optional value used
        b"\x01"  # Access selector
        b"\x02\x04"  # Structure of 4 elements
        b"\x02\x04"  # structure of 4 elements
        b"\x12\x00\x08"  # Clock interface class (unsigned long int)
        b"\t\x06\x00\x00\x01\x00\x00\xff"  # Clock instance octet string of 0.0.1.0.0.255
        b"\x0f\x02"  # attribute index  = 2 (integer)
        b"\x12\x00\x00"  # data index  = 0 (long unsigned)
        b"\t\x0c\x07\xe1\n\x01\x07\x00\x00\x00\x00\xff\xc4\x80"  # from date
        b"\t\x0c\x07\xe1\n\x01\x07\x01\x00\x00\x00\xff\xc4\x80"  # to date
        b"\x01\x00"  # selected_values empty array.
    )
    assert access

    access_selection = g.access_selection

    assert isinstance(access_selection, RangeDescriptor)
    assert access_selection.selected_values is None
    assert (
        access_selection.restricting_object.cosem_attribute.instance.to_string()
        == "0-0:1.0.0.255"
    )

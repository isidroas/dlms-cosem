from datetime import datetime
from typing import *

import attr

from dlms_cosem import cosem, dlms_data, enumerations, time, utils
from dlms_cosem.cosem.capture_object import CaptureObject


@attr.s(auto_attribs=True)
class RangeDescriptor:
    """
    The range descriptor can be used to read buffers of Profile Generic.
    Only buffer element that corresponds to the descriptor shall be returned in a get
    request.


    """

    ACCESS_DESCRIPTOR: ClassVar[int] = 1

    restricting_object: CaptureObject = attr.ib(
        validator=attr.validators.instance_of(CaptureObject)
    )
    from_value: datetime | dlms_data.AbstractDlmsData = attr.ib(
        validator=attr.validators.instance_of((datetime, dlms_data.AbstractDlmsData))
    )
    to_value: datetime | dlms_data.AbstractDlmsData = attr.ib(
        validator=attr.validators.instance_of((datetime, dlms_data.AbstractDlmsData))
    )
    selected_values: Optional[List[CaptureObject]] = attr.ib(default=None)

    @classmethod
    def from_bytes(cls, source_bytes: bytes) -> "RangeDescriptor":
        data = bytearray(source_bytes)
        access_descriptor = data.pop(0)
        if access_descriptor is not cls.ACCESS_DESCRIPTOR:
            raise ValueError(
                f"Access descriptor {access_descriptor} is not valid for "
                f"RangeDescriptor. It should be {cls.ACCESS_DESCRIPTOR}"
            )
        parsed_data = utils.parse_as_dlms_data(data)

        restricting_object_data = parsed_data[0]
        from_value_data = parsed_data[1]
        to_value_data = parsed_data[2]
        selected_values_data = parsed_data[3]

        restricting_cosem_attribute = cosem.CosemAttribute(
            interface=enumerations.CosemInterface(restricting_object_data[0]),
            instance=cosem.Obis.from_bytes(restricting_object_data[1]),
            attribute=restricting_object_data[2],
        )
        restricting_object = CaptureObject(
            cosem_attribute=restricting_cosem_attribute,
            data_index=restricting_object_data[3],
        )
        from_dt, clock_status = time.datetime_from_bytes(from_value_data)
        to_dt, clock_status = time.datetime_from_bytes(to_value_data)
        if selected_values_data:
            raise NotImplementedError()
        else:
            selected_values = None

        return cls(
            restricting_object=restricting_object,
            from_value=from_dt,
            to_value=to_dt,
            selected_values=selected_values,
        )

    def to_bytes(self) -> bytes:
        out = bytearray()
        out.append(self.ACCESS_DESCRIPTOR)
        out.extend(b"\x02\x04")  # structure of 4 elements
        out.extend(self.restricting_object.to_bytes())
        from_value = self.from_value
        if isinstance(self.from_value, datetime):
            from_value= dlms_data.OctetStringData(
                time.datetime_to_bytes(self.from_value)
            )
        out.extend(from_value.to_bytes())
        to_value = self.to_value
        if isinstance(self.to_value, datetime):
            to_value= dlms_data.OctetStringData(
                time.datetime_to_bytes(self.to_value)
            )
        out.extend(to_value.to_bytes())
        if not self.selected_values:
            out.extend(b"\x01\x00")  # empty array for selected values means all columns
        else:
            array = dlms_data.DataArray(self.selected_values)
            out.extend(array.to_bytes())

        return bytes(out)


def validate_unsigned_double_long_int(instance, attribute, value):
    if 0 >= value >= 0xFFFFFFFF:
        raise ValueError(
            f"{value} is not withing the limits of a unsigned double long integer"
        )


def validate_unsigned_long_int(instance, attribute, value):
    if 0 >= value >= 0xFFFF:
        raise ValueError(
            f"{value} is not withing the limits of a unsigned long integer"
        )


@attr.s(auto_attribs=True)
class EntryDescriptor:
    """
    The entry descriptor limits response data by entries.
    It is possible to limit the entries and also the columns returned.
    The from/to_selected_value limits the columns returned from/to_entry limits the
    entries.

    Numbering of selected values and entries start from 1.
    Setting to_entry=0 or to_selected_value=0 requests the highest possible value.
    """

    ACCESS_DESCRIPTOR: ClassVar[int] = 2

    from_entry: int = attr.ib(
        validator=[validate_unsigned_double_long_int, attr.validators.instance_of(int)]
    )
    to_entry: int = attr.ib(
        validator=[validate_unsigned_double_long_int, attr.validators.instance_of(int)],
        default=0,
    )
    from_selected_value: int = attr.ib(
        validator=[validate_unsigned_long_int, attr.validators.instance_of(int)],
        default=1,
    )
    to_selected_value: int = attr.ib(
        validator=[validate_unsigned_long_int, attr.validators.instance_of(int)],
        default=0,
    )

    @classmethod
    def from_bytes(cls, source_bytes) -> "EntryDescriptor":
        raise NotImplementedError()

    def to_bytes(self) -> bytes:
        """
        entry_descriptor ::= structure
        {
            from_entry:              double-long-unsigned -- first entry to retrieve,
            to_entry:                double-long-unsigned -- last entry to retrieve /*(if to_entry == 0: highest possible entry)*/
            from_selected_value:     long-unsigned               -- index of first value to retrieve,
            to_selected_value:       long-unsigned               -- index of last value to retrieve
                                                                    /*(if to_selected_value == 0: highest
                                                                    possible selected_value)*/
        }
        NOTE 1    from_entry and to_entry identify the lines, from_selected_value to_selected_value identify the columns of
                the buffer to be retrieved.

        NOTE 2    Numbering of entries and selected values starts from 1.
        """
        out = bytearray()
        out.append(self.ACCESS_DESCRIPTOR)
        out.extend(b"\x02\x04")  # structure of 4 elements
        out.extend(dlms_data.DoubleLongUnsignedData(self.from_entry).to_bytes())
        out.extend(dlms_data.DoubleLongUnsignedData(self.to_entry).to_bytes())
        out.extend(dlms_data.UnsignedLongData(self.from_selected_value).to_bytes())
        out.extend(dlms_data.UnsignedLongData(self.to_selected_value).to_bytes())

        return bytes(out)


@attr.s(auto_attribs=True)
class AccessDescriptorFactory:

    """
    Handles the selection of parsing the first byte to find what kind of access
    descriptor it is and returns the object.
    """

    @staticmethod
    def from_bytes(source_bytes: bytes) -> Union[RangeDescriptor, EntryDescriptor]:

        access_descriptor = source_bytes[0]
        if access_descriptor == 1:
            return RangeDescriptor.from_bytes(source_bytes)
        elif access_descriptor == 2:
            return EntryDescriptor.from_bytes(source_bytes)
        else:
            raise ValueError(f"{access_descriptor} is not a valid access descriptor")

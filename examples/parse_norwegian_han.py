from dlms_cosem.cosem import Obis
from dlms_cosem.hdlc import frames
from dlms_cosem.protocol import xdlms
from dlms_cosem.time import datetime_from_bytes
from dlms_cosem.utils import parse_as_dlms_data

# 3-phase
hdlc_data_hex = (
    "7ea2434108831385ebe6e7000f4000000000011b020209060000010000ff090c07e30c1001073b28ff"
    "8000ff020309060100010700ff060000046202020f00161b020309060100020700ff06000000000202"
    "0f00161b020309060100030700ff06000005e302020f00161d020309060100040700ff060000000002"
    "020f00161d0203090601001f0700ff10000002020fff1621020309060100330700ff10004b02020fff"
    "1621020309060100470700ff10000002020fff1621020309060100200700ff12090302020fff162302"
    "0309060100340700ff1209c302020fff1623020309060100480700ff12090402020fff162302030906"
    "0100150700ff060000000002020f00161b020309060100160700ff060000000002020f00161b020309"
    "060100170700ff060000000002020f00161d020309060100180700ff060000000002020f00161d0203"
    "09060100290700ff060000046202020f00161b0203090601002a0700ff060000000002020f00161b02"
    "03090601002b0700ff06000005e202020f00161d0203090601002c0700ff060000000002020f00161d"
    "0203090601003d0700ff060000000002020f00161b0203090601003e0700ff060000000002020f0016"
    "1b0203090601003f0700ff060000000002020f00161d020309060100400700ff060000000002020f00"
    "161d020309060100010800ff060099598602020f00161e020309060100020800ff060000000802020f"
    "00161e020309060100030800ff060064ed4b02020f001620020309060100040800ff06000000050202"
    "0f001620be407e"
)

ui = frames.UnnumberedInformationFrame.from_bytes(bytes.fromhex(hdlc_data_hex))
dn = xdlms.DataNotification.from_bytes(
    ui.payload[3:]
)  # The first 3 bytes should be ignored.
result = parse_as_dlms_data(dn.body)

# First is date
date_row = result.pop(0)
clock_obis = Obis.from_bytes(date_row[0])
clock, stats = datetime_from_bytes(date_row[1])
print(f"Clock object: {clock_obis.to_string()}, datetime={clock}")

# rest is data
for item in result:
    obis = Obis.from_bytes(item[0])
    value = item[1]
    print(f"{obis.to_string()}={value}")

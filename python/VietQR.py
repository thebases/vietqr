import copy
import qrcode
import logging

_logger = logging.getLogger(__name__)

BANK_CODE = {
    "ABB": "970425",
    "ACB": "970416",
    "AGRI": "970405",
    "BAB": "970409",
    "BIDV": "970488",
    "BVB": "970438",
    "COOP": "970446",
    "DAB": "970406",
    "EIB": "970431",
    "GPB": "970408",
    "HDB": "970437",
    "HLB": "970442",
    "IVB": "970434",
    "KLB": "970452",
    "LVB": "970449",
    "MB": "970422",
    "MSB": "970426",
    "NAB": "970428",
    "NCB": "970419",
    "OCB": "970448",
    "PGB": "970430",
    "PVC": "970412",
    "SCB": "970429",
    "SEA": "970440",
    "SGB": "970400",
    "SHINHAN": "970424",
    "SHB": "970443",
    "STB": "970403",
    "TCB": "970407",
    "TPB": "970423",
    "UOB": "970458",
    "VAB": "970427",
    "VC": "970460",
    "VCB": "970436",
    "VCCB": "970454",
    "VIB": "970441",
    "VPB": "970432",
    "VRB": "970421",
    "VTB": "970415",
    "WRB": "970457"
}


class TLV:
    tag = ""
    name = ""
    length = ""
    value = ""

    def __init__(self, tag: str, name: str, length: str, value: any, is_fixed_length=True,
                 present_type="O"):
        self.tag = tag or ""
        self.name = name or ""
        if is_fixed_length:
            self.length = f"0{length}" if int(length) < 10 else str(length)
        else:
            self.get_value_length()
        self.present_type = present_type
        self.value = value

    def get_value(self):
        return self.value

    def get_value_length(self):
        if type(self.get_value()) is str:
            self.length = f"0{len(self.value)}" if len(self.value) < 10 else str(len(self.value))
        if type(self.get_value()) is TlvList:
            self.length = len(self.value.to_string())
        return self.length

    def set_value(self, value):
        self.value = value

    def to_string(self):
        return f"{self.tag}{self.length}{self.value}"


class TlvList:
    def __init__(self, tlv_array: list[TLV]):
        self.tlv_array = tlv_array

    def __getitem__(self, item):
        return self.tlv_array[item]

    def get_tlv(self, tag: str) -> TLV:
        for index, element in enumerate(self):
            if element.tag == tag:
                return element

    def get_tlv_index(self, tag: str) -> TLV:
        for index, element in enumerate(self):
            if element.tag == tag:
                return index

    def get_subtag_value(self, tag: str, sub_tag: str) -> str:
        tag_tlv = self.get_tlv(tag)
        _logger.debug(type(tag_tlv.value))
        if type(tag_tlv.value) is TlvList:
            return tag_tlv.value.get_tlv(sub_tag).value
        else:
            return False

    def set_subtag_value(self, tag: str, sub_tag: str, value: str | list[TLV]) -> str:
        tag_tlv = self.get_tlv(tag)
        _logger.debug(type(tag_tlv.value))
        if type(tag_tlv.value) is TlvList:
            tag_tlv.value.get_tlv(sub_tag).value = value

    def to_string(self) -> str:
        build_str = ""
        for tlv in self.tlv_array:
            # _logger.debug(f"Condition 1: {len(tlv.value) >0} - Condition 2: {tlv.tag == '63'}")
            if int(tlv.get_value_length()) > 0:
                build_str = f"{build_str}{tlv.to_string()}"
        return build_str


def _crc16(data: bytes, last4char=True):
    """
    CRC-16 (CCITT) implemented with a precomputed lookup table
    """
    table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7, 0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C,
        0xD1AD, 0xE1CE, 0xF1EF,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6, 0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD,
        0xC39C, 0xF3FF, 0xE3DE,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485, 0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE,
        0xF5CF, 0xC5AC, 0xD58D,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4, 0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF,
        0xE7FE, 0xD79D, 0xC7BC,
        0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823, 0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948,
        0x9969, 0xA90A, 0xB92B,
        0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12, 0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79,
        0x8B58, 0xBB3B, 0xAB1A,
        0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41, 0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A,
        0xBD0B, 0x8D68, 0x9D49,
        0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70, 0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B,
        0xAF3A, 0x9F59, 0x8F78,
        0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F, 0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004,
        0x4025, 0x7046, 0x6067,
        0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E, 0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235,
        0x5214, 0x6277, 0x7256,
        0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D, 0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466,
        0x6447, 0x5424, 0x4405,
        0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C, 0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657,
        0x7676, 0x4615, 0x5634,
        0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB, 0x5844, 0x4865, 0x7806, 0x6827, 0x18C0,
        0x08E1, 0x3882, 0x28A3,
        0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A, 0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1,
        0x1AD0, 0x2AB3, 0x3A92,
        0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9, 0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2,
        0x2C83, 0x1CE0, 0x0CC1,
        0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8, 0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93,
        0x3EB2, 0x0ED1, 0x1EF0
    ]

    crc = 0xFFFF
    for byte in data:
        crc = (crc << 8) ^ table[(crc >> 8) ^ byte]
        crc &= 0xFFFF  # important, crc must stay 16bits all the way through
    if last4char:
        return f"{crc:04X}"  # 4 hex chars, upper-case, zero padded
    else:
        return hex(crc)


_ACCENT_MAP = {ord(c): to for chars, to in (
    ("àáạảãâầấậẩẫăằắặẳẵ", "a"), ("èéẹẻẽêềếệểễ", "e"), ("ìíịỉĩ", "i"),
    ("òóọỏõôồốộổỗơờớợởỡ", "o"), ("ùúụủũưừứựửữ", "u"), ("ỳýỵỷỹ", "y"), ("đ", "d"),
    ("/", "-"),
) for c in chars}
# combining marks: grave, acute, tilde, hook, dot below, circumflex, breve, horn
_ACCENT_MAP.update({ord(c): None for c in "\u0300\u0301\u0303\u0309\u0323\u02C6\u0306\u031B"})


def _non_accent(text: str) -> str:
    """Any text -> upper-case pure ASCII (same rule as vietqr.js nonAccentVietnamese)."""
    ascii_text = text.lower().translate(_ACCENT_MAP).encode("ascii", "ignore").decode("ascii")  # other non-ASCII dropped
    return ascii_text.upper().strip()


def _tlv(tag: str, *values: str) -> str:
    """Build one TLV; an empty value emits nothing."""
    value = _non_accent("".join(values))  # every generated value is upper-case ASCII
    return f"{tag}{len(value):02d}{value}" if value else ""


def get_crc16(data="", last4char=True) -> str:
    string_byte = bytes(data, "UTF-8")
    return _crc16(data=string_byte, last4char=last4char)


def get_bincode(bank="") -> str:
    return BANK_CODE[bank]


def genQRString(is_dynamic_qr: bool = True, merchant_category="", merchant_name="",
                merchant_city="",
                postal_code="", currency="704", country_code="VN", amount="0",
                acq="970403", merchant_id="", service_code="QRIBFTTA",
                bill_number="", mobile_number="", store_label="", loyalty_number="",
                ref_label="", customer_label="", terminal_label="", purpose_txn="", additional_data="",
                lang_ref="", local_merchant_name="", local_merchant_city="", uuid="",
                ipn_url="", app_package_name="", custom_data="") -> str:
    """Generate VietQR Data String

    Keyword arguments: argument -- description
        @is_dynamic_qr        -- The Type of QR: "True" is Dynamic QR, "False" is Static QR
        @merchant_category  -- For Tag 52: Merchant Category \n
        @merchant_name      -- For Tag 59: Merchant Name \n
        @merchant_city      -- For Tag 60: Merchant City \n
        @postal_code        -- For Tag 61: Postal Code \n
        @currency           -- For Tag 53: Currency Code \n
        @country_code       -- For Tag 58: Country Code \n
        @amount             -- For Tag 54: Amount \n
        @acq                -- For Tag 38: Acquirer Bank \n
        @merchant_id        -- For Tag 38: when use QRPUSH -> input Merchant_ID, when use QRIBFTTA 
                                -> merchant bank account, when use QRIBFTTC -> merchant card account \n
        @service_code       -- For Tag 38: QRPUSH: payment service, QRCASH: ATM service, QRIBFTTA: 
                                Napas 24/7 transfer to Bank Account,QRIBFTTC: Napas 24/7 transfer to ATM Card \n
        @bill_number        -- For Tag 62:  Bill number \n
        @mobile_number      -- For Tag 62: Mobile number \n
        @store_label        -- For Tag 62: Store label \n
        @loyalty_number     -- For Tag 62: Loyalty number \n
        @ref_label          -- For Tag 62: Reference label \n
        @customer_label     -- For Tag 62: Customer label \n
        @terminal_label     -- For Tag 62: Terminal label \n
        @purpose_txn        -- For Tag 62: Purpose of Transaction \n
        @additional_data    -- For Tag 62: Additional Data \n
        @lang_ref           -- For Tag 64: Local language to show Merchant Name \n
        @local_merchant_name-- For Tag 64: Local Merchant name \n
        @local_merchant_city-- For Tag 64: Local Merchant City \n
        @uuid               -- For Tag 80 (optional, special use): UUID \n
        @ipn_url            -- Reserved, not encoded (kept for compatibility) \n
        @app_package_name   -- Reserved, not encoded (kept for compatibility) \n
        @custom_data        -- For Tag 80 (optional, special use): custom data \n

    Return: return_description
        @result -- The VietQR Data String
    """
    dynamic = bool(is_dynamic_qr)
    semi_vietqr = "".join([
        _tlv("00", "01"),
        _tlv("01", "12" if dynamic else "11"),
        _tlv("38", _tlv("00", "A000000727"), _tlv("01", _tlv("00", acq), _tlv("01", merchant_id)),
             _tlv("02", service_code)),
        _tlv("52", merchant_category),
        _tlv("53", currency),
        _tlv("54", amount if dynamic else ""),
        _tlv("58", country_code),
        _tlv("59", merchant_name),
        _tlv("60", merchant_city),
        _tlv("61", postal_code),
        _tlv("62", _tlv("01", bill_number), _tlv("02", mobile_number), _tlv("03", store_label),
             _tlv("04", loyalty_number), _tlv("05", ref_label), _tlv("06", customer_label),
             _tlv("07", terminal_label), _tlv("08", purpose_txn),
             _tlv("09", additional_data)),
        _tlv("64", _tlv("00", lang_ref), _tlv("01", local_merchant_name),
             _tlv("02", local_merchant_city)),
        # Tag 80 is optional (special use case): only emitted when uuid/custom_data is set
        _tlv("80", _tlv("00", uuid), _tlv("01", custom_data)),
        "6304",
    ])
    return f"{semi_vietqr}{get_crc16(data=semi_vietqr)}"


VIETQR_FORM = TlvList([
    TLV("00", "Payload Format Indicator", '2', present_type="M", value="01"),
    # present_type can be "M", "O", "C"
    TLV("01", "Point of Initiation Method", '2', present_type="O", value="12"),
    # “11” = Static QR ; “12” = Dynamic QR
    # tag 2 to 51 is used for payment service, tag [38] is used for QR code service on NAPAS system
    TLV("38", "VietQR service", '99', is_fixed_length=False, present_type="M",
        value=TlvList([
            TLV("00", "Global Unique Identifier - GUID", '32', is_fixed_length=False,
                present_type="M", value="A000000727"),
            TLV("01", "Payment network specific (Member banks, Payment Intermediaries) ", '99',
                is_fixed_length=False, present_type="M", value=TlvList([
                    TLV("00", "Acquier ID/BNB ID ", '06', is_fixed_length=False,
                        present_type="M", value=""),
                    TLV("01", "Merchant ID/Consumer ID  ", '19', is_fixed_length=False,
                        present_type="M", value=""),
                ])),
            TLV("02", "Service Code ", '10', is_fixed_length=False,
                present_type="C", value="QRIBFTTA"),

        ])),
    TLV("52", "Merchant Category Code", '4', present_type="M", value=""),
    TLV("53", "Transaction Currency", '3', present_type="M", value=""),
    TLV("54", "Transaction Amount", '13', is_fixed_length=False, present_type="C", value=""),

    # avalable value for tag 55:
    #     "01": txn have TIP, the application will show TIP input
    #     "02" txn have fixed Convenience Fee and have to use tag 56
    #     "03" txn have fixed Convenience Fee and have to use tag 57
    TLV("55", "Tip or Convenience Indicator", '2', present_type="O", value=""),
    TLV("56", "Value of Convenience Fee Fixed", '13', is_fixed_length=False, present_type="C", value=""),
    # only accept number [0..9] and "."
    TLV("57", "Value of Convenience Fee Percentage", '5', is_fixed_length=False, present_type="C", value=""),
    # only values between  “00.01” and “99.99” shall be used.
    TLV("58", "Country Code", '2', present_type="M", value=""),
    TLV("59", "Merchant Name", '25', is_fixed_length=False, present_type="M", value=""),
    TLV("60", "Merchant City", '15', is_fixed_length=False, present_type="M", value=""),
    TLV("61", "Postal Code", '10', is_fixed_length=False, present_type="O", value=""),
    TLV("62", "Additional Data Field Template", '99', is_fixed_length=False, present_type="O",
        value=TlvList([
            TLV("01", "Bill Number", '25', is_fixed_length=False, present_type="C", value=""),
            TLV("02", "Mobile Number ", '25', is_fixed_length=False, present_type="O", value=""),
            TLV("03", "Store Label ", '25', is_fixed_length=False, present_type="C", value=""),
            TLV("04", "Loyalty Number ", '25', is_fixed_length=False, present_type="O", value=""),
            TLV("05", "Reference Label", '25', is_fixed_length=False, present_type="C", value=""),
            TLV("06", "Customer Label", '25', is_fixed_length=False, present_type="O", value=""),
            TLV("07", "Terminal Label", '25', is_fixed_length=False, present_type="C", value=""),
            TLV("08", "Purpose of Transaction ", '25', is_fixed_length=False, present_type="C",
                value=""),
            TLV("09", "Additional Consumer Data Request ", '03', is_fixed_length=False,
                present_type="O", value=""),
        ])),
    TLV("64", "Merchant Information - Language Template", '99', is_fixed_length=False, present_type="O",
        value=TlvList([TLV("00", "Language Preference", '02', is_fixed_length=True, present_type="M", value=""),
               TLV("01", "Merchant Name - Alternate Language", '25', is_fixed_length=False, present_type="O", value=""),
               TLV("02", "Merchant City - Alternate Language", '25', is_fixed_length=False, present_type="C",
                   value=""), ])),
    TLV("63", "CRC", '4', is_fixed_length=True, present_type="M", value="")
])


def _decode_into(template: TlvList, text: str) -> None:
    """Parse TLV text into template, recursing into templates such as tags 38, 62 and 64."""
    while len(text) >= 4:
        tag, length = text[:2], int(text[2:4])
        value = text[4:4 + length]
        text = text[4 + length:]
        element = template.get_tlv(tag)
        if element is None:  # tag not in the form (e.g. tag 80): ignore
            continue
        element.length = text_length = f"{length:02d}"
        if type(element.value) is TlvList:
            _decode_into(element.value, value)
        else:
            element.value = value
        _logger.debug(f"TLV: {tag} - {text_length} - {value}")


def decode(
        vietqr_string: str = "00020101021238620010A00000072701320006970454011899AT00668RCWXA98XQ0208"
                             "QRIBFTTA53037045405500005802VN62150811Chuyen tien63040CBA") -> TlvList:
    """Decode a VietQR string into a fresh TlvList (the module template is not modified)."""
    data = copy.deepcopy(VIETQR_FORM)
    _decode_into(data, vietqr_string)
    return data


def genVietQR(is_dynamic_qr: bool = True, merchant_category="", merchant_name="",
              merchant_city="",
              postal_code="", currency="704", country_code="VN", amount="0",
              acq="970403", merchant_id="", service_code="QRIBFTTA",
              bill_number="", mobile_number="", store_label="", loyalty_number="",
              ref_label="", customer_label="", terminal_label="", purpose_txn="", additional_data="",
              lang_ref="", local_merchant_name="", local_merchant_city="", uuid="",
              ipn_url="", app_package_name="", custom_data=""):
    vietQRstr = genQRString(is_dynamic_qr=is_dynamic_qr, merchant_category=merchant_category,
                            merchant_name=merchant_name,
                            merchant_city=merchant_city,
                            postal_code=postal_code, currency=currency, country_code=country_code, amount=amount,
                            acq=acq, merchant_id=merchant_id, service_code=service_code,
                            bill_number=bill_number, mobile_number=mobile_number, store_label=store_label,
                            loyalty_number=loyalty_number,
                            ref_label=ref_label, customer_label=customer_label, terminal_label=terminal_label,
                            purpose_txn=purpose_txn, additional_data=additional_data,
                            lang_ref=lang_ref, local_merchant_name=local_merchant_name,
                            local_merchant_city=local_merchant_city, uuid=uuid,
                            ipn_url=ipn_url, app_package_name=app_package_name,
                            custom_data=custom_data)
    qr = qrcode.main.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vietQRstr)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


decode()
VIETQR_FORM.get_subtag_value("38", "00")

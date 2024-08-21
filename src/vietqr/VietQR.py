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
        return hex(crc)[-4:].upper()  # Get 4 last char and uppercase
    else:
        return hex(crc)


def _build_tag62(bill_number="", mobile_number="", store_label="", loyalty_number="",
                 ref_label="", customer_label="", terminal_label="", purpose_txn="", additional_data=""):
    return TlvList([
        TLV("01", "Bill Number", '25', is_fixed_length=False, present_type="C", value=bill_number),
        TLV("02", "Mobile Number", '25', is_fixed_length=False, present_type="O", value=mobile_number),
        TLV("03", "Store Label", '25', is_fixed_length=False, present_type="C", value=store_label),
        TLV("04", "Loyalty Number", '25', is_fixed_length=False, present_type="O", value=loyalty_number),
        TLV("05", "Reference Label", '25', is_fixed_length=False, present_type="C", value=ref_label),
        TLV("06", "Customer Label", '25', is_fixed_length=False, present_type="O", value=customer_label),
        TLV("07", "Terminal Label ", '25', is_fixed_length=False, present_type="C", value=terminal_label),
        TLV("08", "Purpose of Transaction", '25', is_fixed_length=False, present_type="C", value=purpose_txn),
        TLV("09", "Additional Consumer Data Request", '3', is_fixed_length=False, present_type="O",
            value=additional_data)
    ]).to_string()


def _build_tag64(lang_ref="", local_merchant_name="", local_merchant_city=""):
    return TlvList([
        TLV("00", "Language Preference", '2', present_type="M", value=lang_ref),
        TLV("01", "Merchant Name - Alternate Language", '25', is_fixed_length=False, present_type="M",
            value=local_merchant_name),
        TLV("03", "Merchant City - Alternate Language", '15', is_fixed_length=False, present_type="O",
            value=local_merchant_city),
    ]).to_string()


def _build_tag3801(acq="", mid=""):
    return TlvList([
        TLV("00", "Acquirer ID/BNB ID", '6', present_type="M", value=acq),
        TLV("01", "Merchant ID/Consumer ID", '19', is_fixed_length=False, present_type="M", value=mid),
    ]).to_string()


def _build_tag38(acq="", mid="", service_code="QRPUSH"):
    # - QRPUSH: Product payment service by QR
    # - QRCASH: Cash withdrawal service at ATM by QR
    # - QRIBFTTC: Inter-Bank Fund Transfer 24/7 to Card service by QR
    # - QRIBFTTA: Inter-Bank Fund Transfer 24/7 to Account service by QR
    return TlvList([
        TLV("00", "Global Unique Identifier - GUID", '32', is_fixed_length=False, present_type="M", value="A000000727"),
        TLV("01", "Payment network specific (Member banks, Payment Intermediaries)", '32', is_fixed_length=False,
            present_type="M", value=_build_tag3801(acq, mid)),
        TLV("02", "Service Code", '10', is_fixed_length=False, present_type="C", value=service_code),
    ]).to_string()


def get_crc16(data="", last4char=True) -> str:
    string_byte = bytes(data, "UTF-8")
    return _crc16(data=string_byte, last4char=last4char)


def get_bincode(bank="") -> str:
    return BANK_CODE[bank]


def genQRString(is_dynamic_qr: bool = False, merchant_category="5812", merchant_name="_",
                merchant_city="HO CHI MINH",
                postal_code="", currency="704", country_code="VN", amount="0",
                acq="", merchant_id="04719238105", service_code="QRPUSH",
                bill_number="", mobile_number="", store_label="", loyalty_number="",
                ref_label="", customer_label="", terminal_label="", purpose_txn="", additional_data="",
                lang_ref="", local_merchant_name="", local_merchant_city="", uuid="",
                ipn_url="", app_package_name="") -> str:
    """Generate VietQR Data String

    Keyword arguments: argument -- description
        @is_dynamic_qr        -- The Type of QR: "True" is Dynamic QR, "False" is Static QR
        @merchant_category  -- For Tag 52: Merchant Category \n
        @merchant_name      -- For Tag 59: Merchant Name \n
        @merchant_city      -- For Tag 60: Merchant City \n
        @postal_code        -- For Tag 61: Postal Code \n
        @currency           -- For Tag 53: Currency Code \n
        @country_code       -- For Tag 38: Country Code \n
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
        @uuid               -- For Tag 99: UUID \n
        @ipn_url            -- For Tag 99: Ipn url use for result calling back \n
        @app_package_name   -- For Tag 99: app package name \n

    Return: return_description
        @result -- The VietQR Data String
    """
    qr_type = "12" if is_dynamic_qr else "11"
    data = TlvList([
        TLV("00", "Payload Format Indicator", '2', present_type="M", value="01"),
        # present_type can be "M", "O", "C"
        TLV("01", "Point of Initiation Method", '2', present_type="O", value=qr_type),
        # “11” = Static QR ; “12” = Dynamic QR
        # tag 2 to 51 is used for payment service, tag [38] is used for QR code service on NAPAS system
        TLV("38", "VietQR service", '99', is_fixed_length=False, present_type="M",
            value=_build_tag38(acq, merchant_id, service_code)),
        TLV("52", "Merchant Category Code", '4', present_type="M", value=merchant_category),
        TLV("53", "Transaction Currency", '3', present_type="M", value=currency),
        TLV("54", "Transaction Amount", '13', is_fixed_length=False, present_type="C", value=amount),

        # avalable value for tag 55:
        #     "01": txn have TIP, the application will show TIP input
        #     "02" txn have fixed Convenience Fee and have to use tag 56
        #     "03" txn have fixed Convenience Fee and have to use tag 57
        TLV("55", "Tip or Convenience Indicator", '2', present_type="O", value=""),
        TLV("56", "Value of Convenience Fee Fixed", '13', is_fixed_length=False, present_type="C", value=""),
        # only accept number [0..9] and "."
        TLV("57", "Value of Convenience Fee Percentage", '5', is_fixed_length=False, present_type="C", value=""),
        # only values between  “00.01” and “99.99” shall be used.
        TLV("58", "Country Code", '2', present_type="M", value=country_code),
        TLV("59", "Merchant Name", '25', is_fixed_length=False, present_type="M", value=merchant_name),
        TLV("60", "Merchant City", '15', is_fixed_length=False, present_type="M", value=merchant_city),
        TLV("61", "Postal Code", '10', is_fixed_length=False, present_type="O", value=postal_code),
        TLV("62", "Additional Data Field Template", '99', is_fixed_length=False, present_type="O",
            value=_build_tag62(bill_number, mobile_number, store_label, loyalty_number, ref_label,
                               customer_label,
                               terminal_label, purpose_txn, additional_data)),
        TLV("64", "Merchant Information - Language Template", '99', is_fixed_length=False, present_type="O",
            value=_build_tag64(lang_ref=lang_ref, local_merchant_city=local_merchant_city,
                               local_merchant_name=local_merchant_name))
    ])

    # TODO: Testing area for ATOM POS connection
    tag_99 = TlvList([
        TLV("00", "Globally Unique Identifier- GUID", '32', is_fixed_length=False, present_type="M",
            value="A000000727")
    ])
    if len(uuid) > 0:
        tag_99.tlv_array.append(TLV("01", "UUID", '32', is_fixed_length=False, present_type="O", value=uuid))
    if len(ipn_url) > 0:
        tag_99.tlv_array.append(TLV("02", "IPN URl", '32', is_fixed_length=False, present_type="O", value=ipn_url))
    if len(app_package_name) > 0:
        tag_99.tlv_array.append(
            TLV("03", "App Package Name", '32', is_fixed_length=False, present_type="O", value=app_package_name))

    _logger.debug(f"count:{len(tag_99.tlv_array)}")
    if len(tag_99.tlv_array) >= 2:
        data.tlv_array.append(
            TLV("99", "ATOM Data", '99', is_fixed_length=False, present_type="O", value=tag_99.to_string()))

    # As VietQR Specs, tag 63 is always the last element
    semi_vietqr = data.to_string()
    crc_value = get_crc16(data=f"{semi_vietqr}6304")
    return f"{semi_vietqr}6304{crc_value}"


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
                    TLV("00", "Merchant ID/Consumer ID  ", '19', is_fixed_length=False,
                        present_type="M", value=""),
                ])),
            TLV("00", "Service Code ", '10', is_fixed_length=False,
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
        value=[TLV("00", "Language Preference", '02', is_fixed_length=True, present_type="M", value=""),
               TLV("01", "Merchant Name - Alternate Language", '25', is_fixed_length=False, present_type="O", value=""),
               TLV("02", "Merchant City - Alternate Language", '25', is_fixed_length=False, present_type="C",
                   value=""), ]),
    TLV("63", "CRC", '4', is_fixed_length=True, present_type="M", value="")
])


def decode(
        vietqr_string: str = "00020101021238620010A00000072701270006970454011899AT00668RCWXA98XQ0208"
                             "QRIBFTTA53037045405500005802VN62150811Chuyen tien630434A7") -> TlvList:
    data = VIETQR_FORM
    i = 0
    while i > (-1):
        tag = vietqr_string[:2]
        length = vietqr_string[2:4]
        value = vietqr_string[4:int(length) + 4]
        _logger.debug(f"TLV: {tag} - {length} - {value}")
        _logger.debug("tag:", data[i].tag)
        _logger.debug(f"vietqr_string: {vietqr_string}")
        data.get_tlv(tag).length = int(length)
        data.get_tlv(tag).value = value
        vietqr_string = vietqr_string[int(length) + 4:len(vietqr_string)]
        _logger.debug(f"vietqr_string after: {vietqr_string}")
        if tag != '63':
            i = i + 1
        else:
            i = -1

    _logger.debug(f"data: {data.to_string()}")
    _logger.debug(f"{data.get_subtag_value('38', '00')}")
    return data


def genVietQR(is_dynamic_qr: bool = False, merchant_category="5812", merchant_name="_",
              merchant_city="HO CHI MINH",
              postal_code="", currency="704", country_code="VN", amount="0",
              acq="", merchant_id="04719238105", service_code="QRPUSH",
              bill_number="", mobile_number="", store_label="", loyalty_number="",
              ref_label="", customer_label="", terminal_label="", purpose_txn="", additional_data="",
              lang_ref="", local_merchant_name="", local_merchant_city="", uuid="",
              ipn_url="", app_package_name=""):
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
                            ipn_url=ipn_url, app_package_name=app_package_name)
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

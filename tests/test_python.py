import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
try:
    import qrcode  # noqa: F401
except ImportError:  # qrcode is only used for image rendering, not for the payload string
    from unittest import mock
    sys.modules["qrcode"] = mock.MagicMock()
import VietQR  # noqa: E402

with open(os.path.join(HERE, "vectors.json"), encoding="utf-8") as fh:
    VECTORS = json.load(fh)


class SharedVectors(unittest.TestCase):
    def test_vectors(self):
        for v in VECTORS:
            with self.subTest(v["name"]):
                self.assertEqual(VietQR.genQRString(**v["fields"]), v["expected"])


class Helpers(unittest.TestCase):
    def test_crc16_check_value(self):
        self.assertEqual(VietQR.get_crc16("123456789"), "29B1")

    def test_bincode(self):
        self.assertEqual(VietQR.get_bincode("VCB"), "970436")
        self.assertEqual(VietQR.get_bincode("MB"), "970422")

    def test_crc_is_last_four_chars_and_valid(self):
        out = VietQR.genQRString(merchant_id="1")
        self.assertEqual(out[-4:], VietQR.get_crc16(out[:-4]))

    def test_decode_roundtrip(self):
        out = VietQR.genQRString(merchant_category="5812", merchant_name="TEST", merchant_city="HCM",
                                 amount="50000", merchant_id="123456789")
        tlv = VietQR.decode(out)
        self.assertEqual(tlv.get_tlv("54").value, "50000")
        self.assertEqual(tlv.get_tlv("59").value, "TEST")
        self.assertEqual(tlv.get_subtag_value("38", "00"), "A000000727")
        self.assertEqual(tlv.get_subtag_value("38", "02"), "QRIBFTTA")
        self.assertEqual(tlv.get_tlv("38").value.get_tlv("01").value.get_tlv("01").value, "123456789")

    def test_decode_ignores_unknown_tag_and_keeps_template_clean(self):
        VietQR.decode(VietQR.genQRString(merchant_id="1", uuid="U"))
        self.assertEqual(VietQR.VIETQR_FORM.get_tlv("54").value, "")


if __name__ == "__main__":
    unittest.main()

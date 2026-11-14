// Java library based on your TypeScript code

// Package declaration (adjust based on your project's structure)
package com.thebase.vietqr;

import java.util.ArrayList;
import java.util.List;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

public class VietQRLibrary {

    // Constants
    public static class ServiceCode {
        public static final String PAYMENT = "QRPUSH";
        public static final String TO_CARD = "QRIBFTTC";
        public static final String TO_ACCOUNT = "QRIBFTTA";
    }

    public static final String NAPAS_GUID = "A000000727";

    // Bank short name -> Napas BIN (use as Fields.acq)
    public static final java.util.Map<String, String> BANK_CODE;
    static {
        java.util.Map<String, String> m = new java.util.LinkedHashMap<>();
        m.put("ABB", "970425");
        m.put("ACB", "970416");
        m.put("AGRI", "970405");
        m.put("BAB", "970409");
        m.put("BIDV", "970488");
        m.put("BVB", "970438");
        m.put("COOP", "970446");
        m.put("DAB", "970406");
        m.put("EIB", "970431");
        m.put("GPB", "970408");
        m.put("HDB", "970437");
        m.put("HLB", "970442");
        m.put("IVB", "970434");
        m.put("KLB", "970452");
        m.put("LVB", "970449");
        m.put("MB", "970422");
        m.put("MSB", "970426");
        m.put("NAB", "970428");
        m.put("NCB", "970419");
        m.put("OCB", "970448");
        m.put("PGB", "970430");
        m.put("PVC", "970412");
        m.put("SCB", "970429");
        m.put("SEA", "970440");
        m.put("SGB", "970400");
        m.put("SHINHAN", "970424");
        m.put("SHB", "970443");
        m.put("STB", "970403");
        m.put("TCB", "970407");
        m.put("TPB", "970423");
        m.put("UOB", "970458");
        m.put("VAB", "970427");
        m.put("VC", "970460");
        m.put("VCB", "970436");
        m.put("VCCB", "970454");
        m.put("VIB", "970441");
        m.put("VPB", "970432");
        m.put("VRB", "970421");
        m.put("VTB", "970415");
        m.put("WRB", "970457");
        BANK_CODE = java.util.Collections.unmodifiableMap(m);
    }

    /** Returns the BIN for a bank short name, or null if unknown. */
    public static String getBinCode(String bank) {
        return BANK_CODE.get(bank);
    }

    public static class Currency {
        public static final String VND = "704";
        public static final String USD = "840";
    }

    // Fields Interface translated to Java class
    public static class Fields {
        public boolean isDynamicQR;
        public String merchantCategory;
        public String merchantName;
        public String merchantCity;
        public String postalCode;
        public String currency;
        public String countryCode;
        public String amount;
        public String acquirer;
        public String merchantId;
        public String serviceCode;
        public String billNumber;
        public String mobileNumber;
        public String storeLabel;
        public String loyaltyNumber;
        public String refLabel;
        public String customerLabel;
        public String terminalLabel;
        public String purposeTxn;
        public String additionalData;
        public String langRef;
        public String localMerchantName;
        public String localMerchantCity;
        public String uuid;
        public String ipnUrl;
        public String appPackageName;
        public String customData;

        public Fields() {
            this.isDynamicQR = true;
            this.merchantCategory = "";
            this.merchantName = "";
            this.merchantCity = "";
            this.postalCode = "";
            this.currency = Currency.VND;
            this.countryCode = "VN";
            this.amount = "0";
            this.acquirer = "970403";
            this.merchantId = "";
            this.serviceCode = ServiceCode.TO_ACCOUNT;
            this.billNumber = "";
            this.mobileNumber = "";
            this.storeLabel = "";
            this.loyaltyNumber = "";
            this.refLabel = "";
            this.customerLabel = "";
            this.terminalLabel = "";
            this.purposeTxn = "";
            this.additionalData = "";
            this.langRef = "";
            this.localMerchantName = "";
            this.localMerchantCity = "";
            this.uuid = "";
            this.ipnUrl = "";
            this.appPackageName = "";
            this.customData = "";
        }
    }

    // CRC Utility class
    public static class CRC {

        public static byte[] stringToUtf8ByteArray(String str) {
            return str.getBytes(StandardCharsets.UTF_8);
        }

        public static String getCrc16(String str, int offset) {
            byte[] data = stringToUtf8ByteArray(str);
            if (data.length == 0 || offset < 0 || offset > data.length - 1) {
                return "0";
            }

            int crc = 0xFFFF;
            for (int i = 0; i < str.length(); i++) {
                crc ^= (data[offset + i] << 8);
                for (int j = 0; j < 8; j++) {
                    crc = (crc & 0x8000) != 0 ? (crc << 1) ^ 0x1021 : crc << 1;
                }
            }

            return String.format("%04X", crc & 0xFFFF);
        }

        public static String getCrc16Array(String[][] text, boolean hexOutput) {
            int polynomial = 0x1021;
            List<String> result = new ArrayList<>();

            for (String[] row : text) {
                for (String string : row) {
                    if (string.isEmpty()) {
                        result.add(null);
                        continue;
                    }

                    byte[] bytes = string.getBytes(StandardCharsets.UTF_8);
                    int crc = 0xFFFF;

                    for (byte b : bytes) {
                        for (int i = 0; i < 8; i++) {
                            boolean bit = ((b >> (7 - i)) & 1) == 1;
                            boolean c15 = ((crc >> 15) & 1) == 1;
                            crc <<= 1;
                            if (c15 != bit) crc ^= polynomial;
                        }
                    }

                    crc &= 0xFFFF;
                    result.add(hexOutput ? String.format("%04X", crc) : String.valueOf(crc));
                }
            }

            return result.stream().collect(Collectors.joining());
        }

        public static String nonAccentVietnamese(String str) {
            return str.toLowerCase()
                    .replaceAll("/", "-")
                    .replaceAll("[àáạảãâầấậẩẫăằắặẳẵ]", "a")
                    .replaceAll("[èéẹẻẽêềếệểễ]", "e")
                    .replaceAll("[ìíịỉĩ]", "i")
                    .replaceAll("[òóọỏõôồốộổỗơờớợởỡ]", "o")
                    .replaceAll("[ùúụủũưừứựửữ]", "u")
                    .replaceAll("[ỳýỵỷỹ]", "y")
                    .replaceAll("đ", "d")
                    .replaceAll("[\\u0300\\u0301\\u0303\\u0309\\u0323]", "")
                    .replaceAll("[\\u02C6\\u0306\\u031B]", "")
                    .replaceAll("[^\\x00-\\x7F]", "") // any other non-ASCII character is dropped
                    .toUpperCase()
                    .trim();
        }
    }

    // TLV Class
    public static class TLV {
        int tagId;
        String tagName;
        int tagLength;
        Object tagValue;
        String presence;

        public TLV(int id, String name, int length, boolean isFixed, String presence, Object value) {
            this.tagId = id;
            this.tagName = name;
            this.tagLength = isFixed ? length : name.length();
            this.tagValue = value;
            this.presence = presence;
        }

        @Override
        public String toString() {
            String value = (tagValue instanceof List)
                    ? ((List<?>) tagValue).stream().map(Object::toString).collect(Collectors.joining())
                    : (tagValue == null ? "" : CRC.nonAccentVietnamese((String) tagValue)); // upper-case ASCII

            if (value.isEmpty()) {
                return "";
            } else {
                this.tagLength = value.length();
                return String.format("%02d%02d%s", this.tagId, this.tagLength, value);
            }
        }
    }

    // VIETQR Class
    public static class VietQR {
        List<TLV> data;
        Fields fields;

        public VietQR() {
            this.data = new ArrayList<>();
            this.fields = new Fields();
        }

        @Override
        public String toString() {
            String str = data.stream().map(TLV::toString).collect(Collectors.joining());
            String semiVietQR = str + "6304";
            String crcValue = CRC.getCrc16Array(new String[][]{{semiVietQR}}, true);
            return semiVietQR + crcValue;
        }

        public String builder() {
            data.clear();
            boolean dynamic = fields.isDynamicQR;
            data.add(new TLV(0, "Payload Format Indicator", 2, true, "M", "01"));
            data.add(new TLV(1, "QR Type", 2, true, "M", dynamic ? "12" : "11"));
            data.add(new TLV(38, "QR code service on NAPAS system", 99, false, "M", List.of(
                    new TLV(0, "Global Unique Identifier - GUID", 10, true, "M", NAPAS_GUID),
                    new TLV(1, "Payment network specific", 32, false, "M", List.of(
                            new TLV(0, "Acquier ID/BNB ID", 6, true, "M", fields.acquirer),
                            new TLV(1, "Merchant ID/Consumer ID", 19, false, "M", fields.merchantId)
                    )),
                    new TLV(2, "Service Code", 10, false, "C", fields.serviceCode)
            )));
            data.add(new TLV(52, "Merchant Category Code", 4, true, "O", fields.merchantCategory));
            data.add(new TLV(53, "Transaction Currency", 3, true, "M", fields.currency));
            data.add(new TLV(54, "Transaction Amount", 13, false, "C", dynamic ? fields.amount : ""));
            data.add(new TLV(58, "Country Code", 2, true, "M", fields.countryCode));
            data.add(new TLV(59, "Merchant Name", 25, false, "O", fields.merchantName));
            data.add(new TLV(60, "Merchant City", 15, false, "O", fields.merchantCity));
            data.add(new TLV(61, "Postal Code", 10, false, "O", fields.postalCode));
            data.add(new TLV(62, "Additional Data Field Template", 99, true, "O", List.of(
                    new TLV(1, "Bill Number", 25, false, "C", fields.billNumber),
                    new TLV(2, "Mobile Number", 25, false, "C", fields.mobileNumber),
                    new TLV(3, "Store Label", 25, false, "O", fields.storeLabel),
                    new TLV(4, "Loyalty Number", 25, false, "O", fields.loyaltyNumber),
                    new TLV(5, "Reference Label", 25, false, "C", fields.refLabel),
                    new TLV(6, "Customer Label", 25, false, "C", fields.customerLabel),
                    new TLV(7, "Terminal Label", 25, false, "O", fields.terminalLabel),
                    new TLV(8, "Purpose of Transaction", 25, false, "C",
                            fields.purposeTxn),
                    new TLV(9, "Additional Consumer Data Request", 3, false, "O", fields.additionalData)
            )));
            data.add(new TLV(64, "Merchant Information - Language Template", 2, true, "O", List.of(
                    new TLV(0, "Language Preference", 2, true, "M", fields.langRef),
                    new TLV(1, "Merchant Name - Alternate Language", 25, false, "M", fields.localMerchantName),
                    new TLV(2, "Merchant City - Alternate Language", 15, false, "O", fields.localMerchantCity)
            )));
            // Tag 80 is optional (special use case): only emitted when uuid/customData is set
            data.add(new TLV(80, "The Base data", 99, false, "O", List.of(
                    new TLV(0, "uuid", 16, false, "O", fields.uuid),
                    new TLV(1, "custom data", 83, false, "O", fields.customData)
            )));
            return toString();
        }
    }
}

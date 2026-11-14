import 'dart:convert';
import 'package:qr_flutter/qr_flutter.dart';

/// Bank short name -> Napas BIN (use as `acq`).
const Map<String, String> bankCode = {
  'ABB': '970425',
  'ACB': '970416',
  'AGRI': '970405',
  'BAB': '970409',
  'BIDV': '970488',
  'BVB': '970438',
  'COOP': '970446',
  'DAB': '970406',
  'EIB': '970431',
  'GPB': '970408',
  'HDB': '970437',
  'HLB': '970442',
  'IVB': '970434',
  'KLB': '970452',
  'LVB': '970449',
  'MB': '970422',
  'MSB': '970426',
  'NAB': '970428',
  'NCB': '970419',
  'OCB': '970448',
  'PGB': '970430',
  'PVC': '970412',
  'SCB': '970429',
  'SEA': '970440',
  'SGB': '970400',
  'SHINHAN': '970424',
  'SHB': '970443',
  'STB': '970403',
  'TCB': '970407',
  'TPB': '970423',
  'UOB': '970458',
  'VAB': '970427',
  'VC': '970460',
  'VCB': '970436',
  'VCCB': '970454',
  'VIB': '970441',
  'VPB': '970432',
  'VRB': '970421',
  'VTB': '970415',
  'WRB': '970457',
};

/// Returns the BIN for a bank short name, or null if unknown.
String? getBinCode(String bank) => bankCode[bank];

/// Fields of a VietQR payload. Same names and defaults as Javascript/vietqr.js.
/// Tag 80 (uuid, customData) is optional and only for special use cases.
class VietQrFields {
  bool isDynamicQr;
  String merchantCategory;
  String merchantName;
  String merchantCity;
  String postalCode;
  String currency;
  String countryCode;
  String amount;
  String acq;
  String merchantId;
  String serviceCode;
  String billNumber;
  String mobileNumber;
  String storeLabel;
  String loyaltyNumber;
  String refLabel;
  String customerLabel;
  String terminalLabel;
  String purposeTxn;
  String additionalData;
  String langRef;
  String localMerchantName;
  String localMerchantCity;
  String uuid;
  String customData;

  VietQrFields({
    this.isDynamicQr = true,
    this.merchantCategory = '',
    this.merchantName = '',
    this.merchantCity = '',
    this.postalCode = '',
    this.currency = '704',
    this.countryCode = 'VN',
    this.amount = '0',
    this.acq = '970403',
    this.merchantId = '',
    this.serviceCode = 'QRIBFTTA',
    this.billNumber = '',
    this.mobileNumber = '',
    this.storeLabel = '',
    this.loyaltyNumber = '',
    this.refLabel = '',
    this.customerLabel = '',
    this.terminalLabel = '',
    this.purposeTxn = '',
    this.additionalData = '',
    this.langRef = '',
    this.localMerchantName = '',
    this.localMerchantCity = '',
    this.uuid = '',
    this.customData = '',
  });
}

class EmvQrDto {
  String bincode;
  String serviceCode;
  String merchantId;
  String merchantName;
  String currency;
  String amount;
  String qrCode;

  EmvQrDto({
    required this.bincode,
    required this.serviceCode,
    required this.merchantId,
    required this.merchantName,
    required this.currency,
    required this.amount,
    this.qrCode = '',
  });
}

int crc16(List<int> data) {
  int crc = 0xFFFF;
  for (var byte in data) {
    crc ^= (byte << 8);
    for (int i = 0; i < 8; i++) {
      if ((crc & 0x8000) != 0) {
        crc = (crc << 1) ^ 0x1021;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc & 0xFFFF;
}

const _accentGroups = {
  'a': 'àáạảãâầấậẩẫăằắặẳẵ',
  'e': 'èéẹẻẽêềếệểễ',
  'i': 'ìíịỉĩ',
  'o': 'òóọỏõôồốộổỗơờớợởỡ',
  'u': 'ùúụủũưừứựửữ',
  'y': 'ỳýỵỷỹ',
  'd': 'đ',
};

// combining marks: grave, acute, tilde, hook, dot below, circumflex, breve, horn
const _combiningMarks = {0x300, 0x301, 0x303, 0x309, 0x323, 0x2C6, 0x306, 0x31B};

final Map<int, String> _accentMap = {
  for (final e in _accentGroups.entries)
    for (final r in e.value.runes) r: e.key,
};

/// Any text -> upper-case pure ASCII (same rule as vietqr.js nonAccentVietnamese).
String nonAccentVietnamese(String text) {
  final buf = StringBuffer();
  for (final r in text.toLowerCase().runes) {
    if (_combiningMarks.contains(r)) continue;
    if (r == 0x2F) {
      buf.write('-');
    } else if (r < 0x80) {
      buf.write(String.fromCharCode(r));
    } else {
      buf.write(_accentMap[r] ?? ''); // any other non-ASCII character is dropped
    }
  }
  return buf.toString().toUpperCase().trim();
}

/// Build one TLV; an empty value emits nothing.
/// Every generated value is upper-case ASCII.
String _tlv(String tag, String raw) {
  final value = nonAccentVietnamese(raw);
  return value.isEmpty ? '' : '$tag${value.length.toString().padLeft(2, '0')}$value';
}

String generateVietQr(VietQrFields f) {
  final semiVietQr = [
    _tlv('00', '01'),
    _tlv('01', f.isDynamicQr ? '12' : '11'),
    _tlv(
        '38',
        [
          _tlv('00', 'A000000727'),
          _tlv('01', _tlv('00', f.acq) + _tlv('01', f.merchantId)),
          _tlv('02', f.serviceCode),
        ].join()),
    _tlv('52', f.merchantCategory),
    _tlv('53', f.currency),
    _tlv('54', f.isDynamicQr ? f.amount : ''),
    _tlv('58', f.countryCode),
    _tlv('59', f.merchantName),
    _tlv('60', f.merchantCity),
    _tlv('61', f.postalCode),
    _tlv(
        '62',
        [
          _tlv('01', f.billNumber),
          _tlv('02', f.mobileNumber),
          _tlv('03', f.storeLabel),
          _tlv('04', f.loyaltyNumber),
          _tlv('05', f.refLabel),
          _tlv('06', f.customerLabel),
          _tlv('07', f.terminalLabel),
          _tlv('08', f.purposeTxn),
          _tlv('09', f.additionalData),
        ].join()),
    _tlv(
        '64',
        [
          _tlv('00', f.langRef),
          _tlv('01', f.localMerchantName),
          _tlv('02', f.localMerchantCity),
        ].join()),
    // Tag 80 is optional (special use case): only emitted when uuid/customData is set
    _tlv('80', _tlv('00', f.uuid) + _tlv('01', f.customData)),
    '6304',
  ].join();

  final crc = crc16(utf8.encode(semiVietQr));
  return '$semiVietQr${crc.toRadixString(16).toUpperCase().padLeft(4, '0')}';
}

/// Legacy entry point; prefer [generateVietQr].
String generateEmvQr(EmvQrDto dto) => generateVietQr(VietQrFields(
      acq: dto.bincode,
      serviceCode: dto.serviceCode,
      merchantId: dto.merchantId,
      merchantName: dto.merchantName,
      currency: dto.currency,
      amount: dto.amount,
    ));

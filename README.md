# VietQR

Generate **VietQR** payload strings (the Napas EMV QR standard used by Vietnamese banks) in six languages: Go, Python, JavaScript, Java, Dart (Flutter) and C.

The library produces the **VietQR data string**: EMVCo TLV fields plus a CRC16 checksum. You then render that string as a QR image with any QR library. (`Javascript/qrcode.js` is included for JavaScript rendering.)

Each language folder is self-contained. Copy the one you need; there are no cross-language dependencies.

| Folder | Language | Entry points |
| --- | --- | --- |
| [`go/`](go) | Go 1.22+ (stdlib only) | `Generate`, `DefaultFields`, `GetBinCode`, `CRC16`, `NonAccent` |
| [`python/`](python) | Python 3.10+ | `genQRString`, `genVietQR`, `decode`, `get_bincode`, `get_crc16` |
| [`Javascript/`](Javascript) | JavaScript | `vietqr.js`, `qrcode.js` (QR rendering) |
| [`java/`](java) | Java | `VietQR.java` (`Fields`, `ServiceCode`, `Currency`, `CRC`, `TLV`, `VietQR`) |
| [`Flutter/`](Flutter) | Dart | `vietqr.dart` (`VietQrFields`, `generateVietQr`) |
| [`C/`](C) | C | `vietqr.h` / `vietqr.c` (`VietQr_InitFields`, `VietQr_Generate`) |

## Quick start

### Go

```go
f := vietqr.DefaultFields()
f.Acq = "970436"                 // or look up with vietqr.GetBinCode("VCB")
f.MerchantID = "0011001234567"   // account number
f.Amount = "50000"
f.MerchantName = "CONG TY ABC"
f.MerchantCity = "HA NOI"

qr, err := vietqr.Generate(f)    // error if any value exceeds 99 characters
```

### Python

```python
from VietQR import genQRString, get_bincode

qr = genQRString(
    merchant_id="660704060000129",
    acq=get_bincode("VIB"),
    amount="50000",
    service_code="QRIBFTTA",
)
```

Other languages follow the same field names and defaults. See each folder's source for the exact call.

## Fields

| Field | Meaning |
| --- | --- |
| `is_dynamic_qr` | `true` = dynamic QR (carries an amount); `false` = static QR |
| `acq` | Acquirer bank BIN assigned by the State Bank of Vietnam (e.g. `970403`) |
| `merchant_id` | Account number (`QRIBFTTA`), card number (`QRIBFTTC`) or merchant ID from the acquirer (`QRPUSH`) |
| `service_code` | `QRPUSH` payment, `QRIBFTTC` interbank transfer to card, `QRIBFTTA` interbank transfer to account |
| `amount` | Total amount; only encoded for dynamic QR |
| `currency` / `country_code` | ISO 4217 / ISO 3166-1 alpha-2. Defaults: `704` (VND) / `VN` |
| `merchant_category`, `merchant_name`, `merchant_city`, `postal_code` | Merchant details |
| `bill_number`, `mobile_number`, `store_label`, `loyalty_number`, `ref_label`, `customer_label`, `terminal_label`, `purpose_txn`, `additional_data` | Optional additional data (tag 62) |
| `lang_ref`, `local_merchant_name`, `local_merchant_city` | Optional alternative-language merchant info (tag 64) |
| `uuid`, `custom_data` | Optional special-use data (tag 80) |

Defaults: dynamic QR, currency `704`, country `VN`, amount `0`, acquirer `970403`, service `QRIBFTTA`. Empty values are omitted from the output.

## How the string is built

1. Fields are emitted as TLV (tag, 2-digit length, value) in fixed order: `00`, `01`, `38` (Napas GUID `A000000727`, acquirer, account, service code), `52`, `53`, `54`, `58`, `59`, `60`, `61`, `62`, `64`, `80`.
2. Every text value is normalized first: lower-cased, Vietnamese accents removed, `/` replaced by `-`, other non-ASCII dropped, then upper-cased and trimmed.
3. `6304` plus a CRC16-CCITT-FALSE checksum (4 upper-case hex digits) is appended.

Example output (dynamic transfer to account):

```
00020101021238530010A0000007270123000697040301091234567890208QRIBFTTA5204581253037045405500005802VN5904TEST6003HCM6304B2E5
```

## Testing and consistency

All implementations must produce byte-identical output for the same input. [`tests/vectors.json`](tests/vectors.json) holds the shared input/expected-output cases, and each language has a test that checks it:

| Test | Covers |
| --- | --- |
| [`tests/test_python.py`](tests/test_python.py) | Python (`unittest`) |
| [`tests/test_javascript.js`](tests/test_javascript.js) | JavaScript (`node --test`) |
| [`tests/test_c.c`](tests/test_c.c) | C (built with `gcc`; vectors are inlined) |
| [`go/vietqr_test.go`](go/vietqr_test.go) | Go (`go test`) |

Run them all with:

```sh
bash tests/run_all.sh
```

Java and Dart have no test harness yet, so `run_all.sh` skips them and those ports have not been compiled or run against the shared vectors. A tag push (`v*`) runs the tests in the [release workflow](.github/workflows/release.yml).

## Author and maintainer

Authored and maintained by **The Base** ([github.com/thebases/vietqr](https://github.com/thebases/vietqr)).

## Notes

- The standard follows the VietQR specification published by Napas.
- Do not commit real account numbers or customer data in examples or tests.
- License: `[VERIFY]` the previous root `LICENSE` (GPL-3.0) was removed while the repo was restructured, and `Javascript/qrcode.js` carries an MIT header. Confirm and restore the intended license before publishing.

/* Reads tests/vectors.json is not practical in plain C, so the vectors are inlined (same as vectors.json). */
#include <stdio.h>
#include <string.h>
#include "../C/vietqr.h"

static int fails = 0;
#define CHECK(name, cond) do { if (!(cond)) { printf("FAIL %s\n", name); fails++; } else printf("ok   %s\n", name); } while (0)

static void expect(const char *name, const VietQrFields *f, const char *want) {
    char out[1024];
    int rc = VietQr_Generate(f, out, sizeof out);
    if (rc != 0 || strcmp(out, want) != 0) printf("  got  %s\n  want %s\n", rc ? "(error)" : out, want);
    CHECK(name, rc == 0 && strcmp(out, want) == 0);
}

int main(void) {
    VietQrFields f;

    VietQr_InitFields(&f);
    f.merchant_category = "5812"; f.merchant_name = "TEST"; f.merchant_city = "HCM";
    f.amount = "50000"; f.acq = "970403"; f.merchant_id = "123456789"; f.service_code = "QRIBFTTA";
    expect("vector dynamic", &f,
        "00020101021238530010A0000007270123000697040301091234567890208QRIBFTTA5204581253037045405500005802VN5904TEST6003HCM6304B2E5");

    VietQr_InitFields(&f);
    f.is_dynamic_qr = 0; f.merchant_category = "5812"; f.merchant_name = "TEST"; f.merchant_city = "HCM";
    f.acq = "970436"; f.merchant_id = "0011001234567"; f.service_code = "QRPUSH";
    expect("vector static", &f,
        "00020101021138550010A00000072701270006970436011300110012345670206QRPUSH5204581253037045802VN5904TEST6003HCM630492F2");

    VietQr_InitFields(&f);
    f.merchant_name = "Cong Ty"; f.merchant_city = "HA NOI"; f.postal_code = "100000"; f.amount = "1000";
    f.merchant_id = "1"; f.bill_number = "INV01"; f.mobile_number = "0900000000"; f.store_label = "S1";
    f.loyalty_number = "L1"; f.ref_label = "R1"; f.customer_label = "C1"; f.terminal_label = "T1";
    f.purpose_txn = "Chuy\xE1\xBB\x83n ti\xE1\xBB\x81n/\xC4\x90\xC3\x80 N\xE1\xBA\xB5ng \xE1\xBB\xA2"; /* Chuyển tiền/ĐÀ Nẵng Ợ */
    f.additional_data = "CME";
    expect("vector tag62", &f,
        "00020101021238450010A00000072701150006970403010110208QRIBFTTA5303704540410005802VN5907CONG TY6006HA NOI610610000062850105INV01021009000000000302S10402L10502R10602C10702T10821CHUYEN TIEN-DA NANG O0903CME6304EDAF");

    CHECK("bincode VCB", VietQr_GetBinCode("VCB") && strcmp(VietQr_GetBinCode("VCB"), "970436") == 0);
    CHECK("bincode unknown", VietQr_GetBinCode("NOPE") == NULL);

    {
        char small[10];
        VietQr_InitFields(&f);
        CHECK("small buffer rejected", VietQr_Generate(&f, small, sizeof small) == -1);
        CHECK("null args rejected", VietQr_Generate(NULL, small, sizeof small) == -1);
    }

    printf(fails ? "%d FAILED\n" : "all passed\n", fails);
    return fails != 0;
}

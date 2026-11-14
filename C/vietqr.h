#ifndef _vietqr_h_
#define _vietqr_h_

#include <stddef.h>

#define MAX_WORDS 20  // Maximum number of words
#define MAX_LENGTH 50 // Maximum length of each word

typedef struct EmvQrDto
{
    char bincode[20];
    char serviceCode[10];
    char merchantId[20];
    char merchantName[50];
    char currency[3];
    char amount[20];
    char qrCode[512];
} EmvQrDto;

/* Fields of a VietQR payload; NULL or "" means "not set". Same names/defaults as Javascript/vietqr.js.
   Tag 80 (uuid, custom_data) is optional and only for special use cases. */
typedef struct VietQrFields
{
    int is_dynamic_qr;
    const char *merchant_category, *merchant_name, *merchant_city, *postal_code;
    const char *currency, *country_code, *amount;
    const char *acq, *merchant_id, *service_code;
    const char *bill_number, *mobile_number, *store_label, *loyalty_number;
    const char *ref_label, *customer_label, *terminal_label, *purpose_txn, *additional_data;
    const char *lang_ref, *local_merchant_name, *local_merchant_city;
    const char *uuid, *custom_data;
} VietQrFields;

/* Set the defaults (dynamic, VND, VN, amount "0", acq 970403, QRIBFTTA). */
void VietQr_InitFields(VietQrFields *f);
/* Returns the BIN for a bank short name (e.g. "VCB"), or NULL if unknown. */
const char *VietQr_GetBinCode(const char *bank);
/* Build the VietQR string into output. Returns 0 on success, -1 on bad args or if it does not fit. */
int VietQr_Generate(const VietQrFields *f, char *output, size_t output_size);

EmvQrDto *GetEmvQrDto();
void GenerateEmvQr(char *output, const char *bincode, const char *serviceCode,
                   const char *merchantID, const char *merchantName, const char *currency, const char *amount);
void Convert_number_to_vietnamese(const char *number, char *result);
void Split_string(const char *input, char result[MAX_WORDS][MAX_LENGTH], int *size);

#endif
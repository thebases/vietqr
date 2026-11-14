#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "vietqr.h"

static const struct { const char *bank, *bin; } BANK_CODE[] = {
    {"ABB", "970425"},
    {"ACB", "970416"},
    {"AGRI", "970405"},
    {"BAB", "970409"},
    {"BIDV", "970488"},
    {"BVB", "970438"},
    {"COOP", "970446"},
    {"DAB", "970406"},
    {"EIB", "970431"},
    {"GPB", "970408"},
    {"HDB", "970437"},
    {"HLB", "970442"},
    {"IVB", "970434"},
    {"KLB", "970452"},
    {"LVB", "970449"},
    {"MB", "970422"},
    {"MSB", "970426"},
    {"NAB", "970428"},
    {"NCB", "970419"},
    {"OCB", "970448"},
    {"PGB", "970430"},
    {"PVC", "970412"},
    {"SCB", "970429"},
    {"SEA", "970440"},
    {"SGB", "970400"},
    {"SHINHAN", "970424"},
    {"SHB", "970443"},
    {"STB", "970403"},
    {"TCB", "970407"},
    {"TPB", "970423"},
    {"UOB", "970458"},
    {"VAB", "970427"},
    {"VC", "970460"},
    {"VCB", "970436"},
    {"VCCB", "970454"},
    {"VIB", "970441"},
    {"VPB", "970432"},
    {"VRB", "970421"},
    {"VTB", "970415"},
    {"WRB", "970457"},
};

const char *VietQr_GetBinCode(const char *bank)
{
    if (!bank)
        return NULL;
    for (size_t i = 0; i < sizeof(BANK_CODE) / sizeof(BANK_CODE[0]); i++)
        if (strcmp(BANK_CODE[i].bank, bank) == 0)
            return BANK_CODE[i].bin;
    return NULL;
}

EmvQrDto g_emvQrDto = {0};

// Getters and Setters for EmvQrDto
EmvQrDto *GetEmvQrDto()
{
    return &g_emvQrDto;
}

/* The `crc16` function is calculating the CRC16-CCITT (XMODEM) checksum for a given
data array. It iterates over each byte in the data array, performs bitwise XOR
operations and bit shifting to calculate the checksum value, and finally returns the
calculated CRC value as an unsigned short integer. */

unsigned short crc16(const unsigned char *data, size_t len)
{
    unsigned short crc = 0xFFFF;
    for (size_t i = 0; i < len; i++)
    {
        crc ^= (unsigned short)data[i] << 8;
        for (int j = 0; j < 8; j++)
        {
            if (crc & 0x8000)
            {
                crc = (crc << 1) ^ 0x1021;
            }
            else
            {
                crc <<= 1;
            }
        }
    }
    return crc;
}


/* ===== VietQR generator (same rules as Javascript/vietqr.js) ===== */

#define VQ_MAX 1024

typedef struct
{
    char *p;
    size_t cap;
    size_t len;
    int err;
} VqBuf;

static void vq_init(VqBuf *b, char *mem, size_t cap)
{
    b->p = mem;
    b->cap = cap;
    b->len = 0;
    b->err = 0;
    if (cap > 0)
        mem[0] = '\0';
}

static void vq_put(VqBuf *b, const char *s)
{
    size_t n = strlen(s);
    if (b->err || b->len + n + 1 > b->cap)
    {
        b->err = 1;
        return;
    }
    memcpy(b->p + b->len, s, n + 1);
    b->len += n;
}

static int vq_non_accent(const char *in, char *out, size_t out_size);

/* Append one TLV; a NULL/empty value emits nothing. The value is normalized to upper-case ASCII. */
static void vq_tlv(VqBuf *b, const char *tag, const char *raw)
{
    char hdr[16], value[VQ_MAX];
    if (b->err)
        return;
    if (vq_non_accent(raw, value, sizeof(value)) != 0)
    {
        b->err = 1;
        return;
    }
    if (value[0] == '\0')
        return;
    snprintf(hdr, sizeof(hdr), "%s%02u", tag, (unsigned)strlen(value));
    vq_put(b, hdr);
    vq_put(b, value);
}

/* Append a nested TLV built in `inner`; propagates inner overflow. */
static void vq_tlv_nested(VqBuf *b, const char *tag, const VqBuf *inner)
{
    if (inner->err)
        b->err = 1;
    else
        vq_tlv(b, tag, inner->p);
}

static unsigned vq_utf8_next(const unsigned char **pp)
{
    const unsigned char *p = *pp;
    unsigned cp = *p;
    int extra = 0;
    if (cp >= 0xF0 && cp < 0xF8) { cp &= 0x07; extra = 3; }
    else if (cp >= 0xE0) { cp &= 0x0F; extra = 2; }
    else if (cp >= 0xC0) { cp &= 0x1F; extra = 1; }
    p++;
    while (extra-- > 0 && (*p & 0xC0) == 0x80)
        cp = (cp << 6) | (*p++ & 0x3F);
    *pp = p;
    return cp;
}

static const struct
{
    const char *chars;
    char to;
} VQ_ACCENT[] = {
    {"àáạảãâầấậẩẫăằắặẳẵ", 'A'}, {"èéẹẻẽêềếệểễ", 'E'}, {"ìíịỉĩ", 'I'},
    {"òóọỏõôồốộổỗơờớợởỡ", 'O'}, {"ùúụủũưừứựửữ", 'U'}, {"ỳýỵỷỹ", 'Y'}, {"đ", 'D'},
};

static char vq_accent_to_ascii(unsigned cp)
{
    size_t g;
    for (g = 0; g < sizeof(VQ_ACCENT) / sizeof(VQ_ACCENT[0]); g++)
    {
        const unsigned char *p = (const unsigned char *)VQ_ACCENT[g].chars;
        while (*p)
        {
            unsigned lc = vq_utf8_next(&p);
            unsigned uc = lc < 0x100 ? lc - 0x20 : lc - 1;
            if (cp == lc || cp == uc)
                return VQ_ACCENT[g].to;
        }
    }
    return 0;
}

/* Vietnamese text -> upper-case ASCII ('/' -> '-', combining marks dropped, trimmed).
   Any other non-ASCII character is dropped. Returns 0 on success, -1 if out is too small. */
static int vq_non_accent(const char *in, char *out, size_t out_size)
{
    const unsigned char *p = (const unsigned char *)(in ? in : "");
    size_t n = 0, start = 0;
    while (*p)
    {
        unsigned cp = vq_utf8_next(&p);
        char c = 0;
        if (cp == 0x300 || cp == 0x301 || cp == 0x303 || cp == 0x309 || cp == 0x323 ||
            cp == 0x2C6 || cp == 0x306 || cp == 0x31B)
            continue;
        if (cp < 0x80)
            c = cp == '/' ? '-' : (cp >= 'a' && cp <= 'z') ? (char)(cp - 'a' + 'A') : (char)cp;
        else
            c = vq_accent_to_ascii(cp);
        if (c)
        {
            if (n + 2 > out_size)
                return -1;
            out[n++] = c;
        }
        /* any other non-ASCII character is dropped: the VietQR string must be pure ASCII */
    }
    if (out_size == 0)
        return -1;
    out[n] = '\0';
    while (n > 0 && (out[n - 1] == ' ' || out[n - 1] == '\t' || out[n - 1] == '\n' || out[n - 1] == '\r'))
        out[--n] = '\0';
    while (out[start] == ' ' || out[start] == '\t' || out[start] == '\n' || out[start] == '\r')
        start++;
    if (start > 0)
        memmove(out, out + start, n - start + 1);
    return 0;
}

void VietQr_InitFields(VietQrFields *f)
{
    memset(f, 0, sizeof(*f));
    f->is_dynamic_qr = 1;
    f->currency = "704";
    f->country_code = "VN";
    f->amount = "0";
    f->acq = "970403";
    f->service_code = "QRIBFTTA";
}

int VietQr_Generate(const VietQrFields *f, char *output, size_t output_size)
{
    char m_acq[VQ_MAX], m_38[VQ_MAX], m_62[VQ_MAX], m_64[VQ_MAX], m_80[VQ_MAX], m_body[VQ_MAX];
    char crc_hex[8];
    VqBuf acq, n38, n62, n64, n80, body;
    unsigned short crc;

    if (f == NULL || output == NULL || output_size == 0)
        return -1;

    vq_init(&acq, m_acq, sizeof(m_acq));
    vq_tlv(&acq, "00", f->acq);
    vq_tlv(&acq, "01", f->merchant_id);

    vq_init(&n38, m_38, sizeof(m_38));
    vq_tlv(&n38, "00", "A000000727");
    vq_tlv_nested(&n38, "01", &acq);
    vq_tlv(&n38, "02", f->service_code);

    vq_init(&n62, m_62, sizeof(m_62));
    vq_tlv(&n62, "01", f->bill_number);
    vq_tlv(&n62, "02", f->mobile_number);
    vq_tlv(&n62, "03", f->store_label);
    vq_tlv(&n62, "04", f->loyalty_number);
    vq_tlv(&n62, "05", f->ref_label);
    vq_tlv(&n62, "06", f->customer_label);
    vq_tlv(&n62, "07", f->terminal_label);
    vq_tlv(&n62, "08", f->purpose_txn);
    vq_tlv(&n62, "09", f->additional_data);

    vq_init(&n64, m_64, sizeof(m_64));
    vq_tlv(&n64, "00", f->lang_ref);
    vq_tlv(&n64, "01", f->local_merchant_name);
    vq_tlv(&n64, "02", f->local_merchant_city);

    /* Tag 80 is optional (special use case): only emitted when uuid/custom_data is set */
    vq_init(&n80, m_80, sizeof(m_80));
    vq_tlv(&n80, "00", f->uuid);
    vq_tlv(&n80, "01", f->custom_data);

    vq_init(&body, m_body, sizeof(m_body));
    vq_tlv(&body, "00", "01");
    vq_tlv(&body, "01", f->is_dynamic_qr ? "12" : "11");
    vq_tlv_nested(&body, "38", &n38);
    vq_tlv(&body, "52", f->merchant_category);
    vq_tlv(&body, "53", f->currency);
    vq_tlv(&body, "54", f->is_dynamic_qr ? f->amount : NULL);
    vq_tlv(&body, "58", f->country_code);
    vq_tlv(&body, "59", f->merchant_name);
    vq_tlv(&body, "60", f->merchant_city);
    vq_tlv(&body, "61", f->postal_code);
    vq_tlv_nested(&body, "62", &n62);
    vq_tlv_nested(&body, "64", &n64);
    vq_tlv_nested(&body, "80", &n80);
    vq_put(&body, "6304");
    if (body.err)
        return -1;

    crc = crc16((const unsigned char *)body.p, body.len);
    snprintf(crc_hex, sizeof(crc_hex), "%04X", (unsigned)crc);
    if (body.len + 4 + 1 > output_size)
        return -1;
    memcpy(output, body.p, body.len);
    memcpy(output + body.len, crc_hex, 5);
    return 0;
}

/* Legacy wrapper: `output` must hold at least 512 bytes (EmvQrDto.qrCode size).
   Empty/NULL arguments fall back to the VietQr_InitFields defaults. On failure output is "". */
void GenerateEmvQr(char *output, const char *bincode, const char *serviceCode, const char *merchantID,
                   const char *merchantName, const char *currency, const char *amount)
{
    VietQrFields f;
    VietQr_InitFields(&f);
    if (bincode && *bincode)
        f.acq = bincode;
    if (serviceCode && *serviceCode)
        f.service_code = serviceCode;
    if (currency && *currency)
        f.currency = currency;
    if (amount && *amount)
        f.amount = amount;
    f.merchant_id = merchantID;
    f.merchant_name = merchantName;
    if (VietQr_Generate(&f, output, 512) != 0)
        output[0] = '\0';
}


/* ===========================================*/

void Split_string(const char *input, char result[MAX_WORDS][MAX_LENGTH], int *size) {
    char temp[256]; // Temporary buffer to avoid modifying the original string
    strcpy(temp, input);

    char *token = strtok(temp, " "); // First split
    *size = 0;

    while (token != NULL && *size < MAX_WORDS) {
        strcpy(result[*size], token);
        (*size)++;
        token = strtok(NULL, " "); // Get next token
    }
}   


// Vietnamese number names without accents
const char *vietnamese_numbers[] = {
    "", "mot", "hai", "ba", "bon", "nam", "sau", "bay", "tam", "chin"
};

// Function to convert a number to Vietnamese text 
// TODO: Need to review this function because it's not working correctly
void Convert_number_to_vietnamese(const char *number, char *result) {
    int length = strlen(number);
    int *num = (int *)malloc(length * sizeof(int));
    if (!num) {
        strcpy(result, "Memory allocation failed");
        return;
    }

    // Convert char digits to integer array
    for (int i = 0; i < length; i++) {
        num[i] = number[i] - '0';
    }

    char buffer[512] = "";
    int first_nonzero = -1;

    // Find first non-zero digit to avoid leading zeros
    for (int i = 0; i < length; i++) {
        if (num[i] != 0) {
            first_nonzero = i;
            break;
        }
    }

    if (first_nonzero == -1) { // If all are zeros
        strcpy(result, "khong");
        free(num);
        return;
    }

    int has_previous_nonzero = 0;
    int last_unit_position = -1;

    for (int i = first_nonzero; i < length; i++) {
        int digit = num[i];
        int position = length - i;
        int mod3 = position % 3;
        int group_index = position / 3;

        if (digit == 0) {
            // Handle "không trăm" when hundreds place is missing
            if (mod3 == 0 && (i + 2 < length) && (num[i + 1] != 0 || num[i + 2] != 0)) {
                strcat(buffer, " khong tram");
            }
            // Handle "linh" when zero appears in the tens place
            else if (mod3 == 2 && num[i - 1] != 0) {
                strcat(buffer, " linh");
            }
            continue;
        }

        // Handle "mười" case
        if (mod3 == 2 && digit == 1) {  
            strcat(buffer, has_previous_nonzero ? " muoi" : "muoi");
        } else if (mod3 == 1 && digit == 5 && has_previous_nonzero) {  
            strcat(buffer, " lam");
        } else { 
            strcat(buffer, has_previous_nonzero ? " " : "");  
            strcat(buffer, vietnamese_numbers[digit]);
        }

        has_previous_nonzero = 1;

        // Append unit names
        if (mod3 == 2 && digit != 1) {
            strcat(buffer, " muoi");
        } else if (mod3 == 0) {
            strcat(buffer, " tram");
        }

        // Append "nghin", "trieu", "ty" only if needed
        if (mod3 == 1 && group_index > 0) {
            int next_three_digits_zero = 1;

            // Check if the next three digits are all zero
            for (int j = i; j < i + 3 && j < length; j++) {
                if (num[j] != 0) {
                    next_three_digits_zero = 0;
                    break;
                }
            }

            // Add unit only if this is a nonzero group or if it's needed at the end
            if (!next_three_digits_zero || (length - i) > 3) {
                if (group_index == 1 && last_unit_position != 1) {
                    strcat(buffer, " nghin");
                    last_unit_position = 1;
                } else if (group_index == 2 && last_unit_position != 2) {
                    strcat(buffer, " trieu");
                    last_unit_position = 2;
                } else if (group_index == 3 && last_unit_position != 3) {
                    strcat(buffer, " ty");
                    last_unit_position = 3;
                }
            }
        }
    }

    // **Fix: Remove trailing "linh" if it's incorrectly placed**
    int buffer_length = strlen(buffer);
    if (buffer_length > 5 && strcmp(&buffer[buffer_length - 5], " linh") == 0) {
        buffer[buffer_length - 5] = '\0';  // Trim " linh"
    }

    // Copy final result
    strcpy(result, buffer);
    free(num);
} 
// Package vietqr builds VietQR (Napas EMV QR) payload strings.
//
// It follows the same rules as the other libraries in this repository
// (Javascript/vietqr.js is the reference): the same tag order, defaults,
// text normalization and CRC, so the same input gives the same string.
package vietqr

import (
	"errors"
	"fmt"
	"strings"
	"unicode"
)

// Service codes (tag 38.02) and currencies (tag 53).
const (
	ServicePayment   = "QRPUSH"
	ServiceToCard    = "QRIBFTTC"
	ServiceToAccount = "QRIBFTTA"

	CurrencyVND = "704"
	CurrencyUSD = "840"

	napasGUID = "A000000727"
)

// BankCode maps a bank short name to its Napas BIN (use as Fields.Acq).
var BankCode = map[string]string{
	"ABB":     "970425",
	"ACB":     "970416",
	"AGRI":    "970405",
	"BAB":     "970409",
	"BIDV":    "970488",
	"BVB":     "970438",
	"COOP":    "970446",
	"DAB":     "970406",
	"EIB":     "970431",
	"GPB":     "970408",
	"HDB":     "970437",
	"HLB":     "970442",
	"IVB":     "970434",
	"KLB":     "970452",
	"LVB":     "970449",
	"MB":      "970422",
	"MSB":     "970426",
	"NAB":     "970428",
	"NCB":     "970419",
	"OCB":     "970448",
	"PGB":     "970430",
	"PVC":     "970412",
	"SCB":     "970429",
	"SEA":     "970440",
	"SGB":     "970400",
	"SHINHAN": "970424",
	"SHB":     "970443",
	"STB":     "970403",
	"TCB":     "970407",
	"TPB":     "970423",
	"UOB":     "970458",
	"VAB":     "970427",
	"VC":      "970460",
	"VCB":     "970436",
	"VCCB":    "970454",
	"VIB":     "970441",
	"VPB":     "970432",
	"VRB":     "970421",
	"VTB":     "970415",
	"WRB":     "970457",
}

// GetBinCode returns the BIN for a bank short name; ok is false if unknown.
func GetBinCode(bank string) (bin string, ok bool) {
	bin, ok = BankCode[bank]
	return
}

// ErrValueTooLong is returned when a value does not fit the 2-digit TLV length.
var ErrValueTooLong = errors.New("vietqr: value longer than 99 characters")

// Fields are the inputs of a VietQR string. Empty strings are omitted from the
// output. Use DefaultFields to start from the library defaults.
type Fields struct {
	IsDynamicQR      bool   `json:"is_dynamic_qr"`
	MerchantCategory string `json:"merchant_category"`
	MerchantName     string `json:"merchant_name"`
	MerchantCity     string `json:"merchant_city"`
	PostalCode       string `json:"postal_code"`
	Currency         string `json:"currency"`
	CountryCode      string `json:"country_code"`
	Amount           string `json:"amount"` // only encoded for dynamic QR
	Acq              string `json:"acq"`    // acquirer BIN, e.g. 970403
	MerchantID       string `json:"merchant_id"`
	ServiceCode      string `json:"service_code"`

	BillNumber     string `json:"bill_number"`
	MobileNumber   string `json:"mobile_number"`
	StoreLabel     string `json:"store_label"`
	LoyaltyNumber  string `json:"loyalty_number"`
	RefLabel       string `json:"ref_label"`
	CustomerLabel  string `json:"customer_label"`
	TerminalLabel  string `json:"terminal_label"`
	PurposeTxn     string `json:"purpose_txn"`
	AdditionalData string `json:"additional_data"`

	LangRef           string `json:"lang_ref"`
	LocalMerchantName string `json:"local_merchant_name"`
	LocalMerchantCity string `json:"local_merchant_city"`

	// Tag 80 is optional and meant for special use cases: it is only emitted
	// when UUID or CustomData is set.
	UUID       string `json:"uuid"`
	CustomData string `json:"custom_data"`
}

// DefaultFields returns a dynamic VND transfer-to-account QR with acquirer 970403.
func DefaultFields() Fields {
	return Fields{
		IsDynamicQR: true,
		Currency:    CurrencyVND,
		CountryCode: "VN",
		Amount:      "0",
		Acq:         "970403",
		ServiceCode: ServiceToAccount,
	}
}

// Generate returns the VietQR data string (TLV payload + CRC16).
// Every text value is first normalized to upper-case ASCII (see NonAccent).
func Generate(f Fields) (string, error) {
	amount := ""
	if f.IsDynamicQR {
		amount = f.Amount
	}
	qrType := "11"
	if f.IsDynamicQR {
		qrType = "12"
	}

	b := &builder{}
	b.put(b.leaf("00", "01"))
	b.put(b.leaf("01", qrType))
	b.put(b.nested("38",
		b.leaf("00", napasGUID),
		b.nested("01", b.leaf("00", f.Acq), b.leaf("01", f.MerchantID)),
		b.leaf("02", f.ServiceCode)))
	b.put(b.leaf("52", f.MerchantCategory))
	b.put(b.leaf("53", f.Currency))
	b.put(b.leaf("54", amount))
	b.put(b.leaf("58", f.CountryCode))
	b.put(b.leaf("59", f.MerchantName))
	b.put(b.leaf("60", f.MerchantCity))
	b.put(b.leaf("61", f.PostalCode))
	b.put(b.nested("62",
		b.leaf("01", f.BillNumber), b.leaf("02", f.MobileNumber), b.leaf("03", f.StoreLabel),
		b.leaf("04", f.LoyaltyNumber), b.leaf("05", f.RefLabel), b.leaf("06", f.CustomerLabel),
		b.leaf("07", f.TerminalLabel), b.leaf("08", f.PurposeTxn), b.leaf("09", f.AdditionalData)))
	b.put(b.nested("64",
		b.leaf("00", f.LangRef), b.leaf("01", f.LocalMerchantName), b.leaf("02", f.LocalMerchantCity)))
	b.put(b.nested("80", b.leaf("00", f.UUID), b.leaf("01", f.CustomData)))
	if b.err != nil {
		return "", b.err
	}

	// The CRC covers everything up to and including the "6304" tag header.
	semi := b.sb.String() + "6304"
	return fmt.Sprintf("%s%04X", semi, CRC16([]byte(semi))), nil
}

// builder accumulates TLVs and remembers the first error, so the call site
// stays a flat list of tags.
type builder struct {
	sb  strings.Builder
	err error
}

// leaf encodes one TLV with a normalized value; an empty value gives "".
func (b *builder) leaf(tag, value string) string {
	return b.encode(tag, NonAccent(value))
}

// nested wraps already-encoded sub-TLVs into one TLV (a template tag).
func (b *builder) nested(tag string, tlvs ...string) string {
	return b.encode(tag, strings.Join(tlvs, ""))
}

// put appends an encoded TLV to the payload.
func (b *builder) put(tlv string) {
	b.sb.WriteString(tlv)
}

// encode builds tag + 2-digit length + value. Lengths are in characters, which
// equals bytes because values are ASCII after normalization.
func (b *builder) encode(tag, value string) string {
	if value == "" {
		return ""
	}
	if len(value) > 99 {
		if b.err == nil {
			b.err = fmt.Errorf("tag %s: %w", tag, ErrValueTooLong)
		}
		return ""
	}
	return fmt.Sprintf("%s%02d%s", tag, len(value), value)
}

// CRC16 is CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over data.
func CRC16(data []byte) uint16 {
	crc := uint16(0xFFFF)
	for _, c := range data {
		crc ^= uint16(c) << 8
		for range 8 {
			if crc&0x8000 != 0 {
				crc = crc<<1 ^ 0x1021
			} else {
				crc <<= 1
			}
		}
	}
	return crc
}

// accent maps lower-case Vietnamese letters to their plain ASCII form.
var accent = buildAccentMap()

func buildAccentMap() map[rune]rune {
	groups := map[rune]string{
		'A': "àáạảãâầấậẩẫăằắặẳẵ",
		'E': "èéẹẻẽêềếệểễ",
		'I': "ìíịỉĩ",
		'O': "òóọỏõôồốộổỗơờớợởỡ",
		'U': "ùúụủũưừứựửữ",
		'Y': "ỳýỵỷỹ",
		'D': "đ",
	}
	m := make(map[rune]rune)
	for to, chars := range groups {
		for _, r := range chars {
			m[r] = to
		}
	}
	return m
}

// NonAccent turns any text into upper-case pure ASCII: Vietnamese accents are
// removed, "/" becomes "-", every other non-ASCII character is dropped and the
// result is trimmed. The output must be ASCII because TLV lengths and the CRC
// are computed on it.
func NonAccent(s string) string {
	return strings.TrimSpace(strings.Map(toASCII, s))
}

func toASCII(r rune) rune {
	r = unicode.ToLower(r)
	switch {
	case r == '/':
		return '-'
	case r < unicode.MaxASCII+1:
		return unicode.ToUpper(r)
	}
	if to, ok := accent[r]; ok {
		return to
	}
	return -1
}

package vietqr

import (
	"encoding/json"
	"errors"
	"os"
	"strings"
	"testing"
)

// vectors.json is shared by every language in this repository; the expected
// strings come from Javascript/vietqr.js.
type vector struct {
	Name     string          `json:"name"`
	Fields   json.RawMessage `json:"fields"`
	Expected string          `json:"expected"`
}

func TestGenerateSharedVectors(t *testing.T) {
	raw, err := os.ReadFile("../tests/vectors.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors []vector
	if err := json.Unmarshal(raw, &vectors); err != nil {
		t.Fatal(err)
	}
	for _, v := range vectors {
		t.Run(v.Name, func(t *testing.T) {
			f := DefaultFields()
			if err := json.Unmarshal(v.Fields, &f); err != nil {
				t.Fatal(err)
			}
			got, err := Generate(f)
			if err != nil {
				t.Fatal(err)
			}
			if got != v.Expected {
				t.Errorf("got  %s\nwant %s", got, v.Expected)
			}
		})
	}
}

func TestCRC16(t *testing.T) {
	if got := CRC16([]byte("123456789")); got != 0x29B1 {
		t.Errorf("CRC16 = %04X, want 29B1", got)
	}
}

func TestGenerateValueTooLong(t *testing.T) {
	f := DefaultFields()
	f.MerchantName = strings.Repeat("A", 100)
	if _, err := Generate(f); !errors.Is(err, ErrValueTooLong) {
		t.Errorf("err = %v, want ErrValueTooLong", err)
	}
}

func TestNonAccent(t *testing.T) {
	if got := NonAccent("  Chuyển tiền/ĐÀ Nẵng 😀 ñ "); got != "CHUYEN TIEN-DA NANG" {
		t.Errorf("NonAccent = %q", got)
	}
}

func TestGetBinCode(t *testing.T) {
	if bin, ok := GetBinCode("VCB"); !ok || bin != "970436" {
		t.Errorf("GetBinCode(VCB) = %q, %v", bin, ok)
	}
	if _, ok := GetBinCode("NOPE"); ok {
		t.Error("unknown bank must report ok=false")
	}
}

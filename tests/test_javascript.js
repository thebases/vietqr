'use strict';
// vietqr.js has no module.exports (browser script): evaluate it in a vm context and read its top-level bindings.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const src = fs.readFileSync(path.join(__dirname, '..', 'Javascript', 'vietqr.js'), 'utf8');
const ctx = vm.createContext({});
vm.runInContext(src + '\n;this.api = { VIETQR, CRC, FIELDS, getBinCode };', ctx);
const { VIETQR, CRC, FIELDS, getBinCode } = ctx.api;
const vectors = JSON.parse(fs.readFileSync(path.join(__dirname, 'vectors.json'), 'utf8'));

function generate(fields) {
  const q = new VIETQR();
  q.fields = Object.assign({}, FIELDS, fields);
  return q.builder();
}

for (const v of vectors) {
  test(`vector ${v.name}`, () => assert.strictEqual(generate(v.fields), v.expected));
}

test('crc16 check value', () => assert.strictEqual(CRC.getCrc16_array('123456789'), '29B1'));
test('getCrc16 matches getCrc16_array', () => {
  assert.strictEqual(CRC.getCrc16('123456789'), '29B1');
  assert.strictEqual(CRC.getCrc16('Chuyển'), CRC.getCrc16_array('Chuyển'));
});
test('crc16 zero padded to 4 chars', () => assert.strictEqual(CRC.getCrc16_array('x').length, 4));
test('bin code', () => {
  assert.strictEqual(getBinCode('VCB'), '970436');
  assert.strictEqual(getBinCode('NOPE'), undefined);
});
test('nonAccentVietnamese', () => {
  assert.strictEqual(CRC.nonAccentVietnamese('  Chuyển tiền/ĐÀ Nẵng 😀 ñ '), 'CHUYEN TIEN-DA NANG');
});

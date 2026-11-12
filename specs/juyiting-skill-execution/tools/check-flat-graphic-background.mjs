// Read-only oracle for this two-solid-shape fixture. Derive foreground boxes from
// saturated expected colors, NOT from whiteness, before testing background bytes.
// Preserve an explicit 8px resampling-edge exclusion; not an all-semantic mask.
import fs from 'node:fs'
import crypto from 'node:crypto'
import assert from 'node:assert/strict'
import zlib from 'node:zlib'
const file = process.argv[2], bytes = fs.readFileSync(file)
// This oracle supports the tested fixture's 8-bit RGB/RGBA, noninterlaced PNG.
// Reject unsupported encodings instead of silently treating them as a pass.
assert.ok(bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])), 'PNG signature')
let offset = 8, width, height, channels, interlace, depth
const idat = []
while (offset < bytes.length) {
  const n = bytes.readUInt32BE(offset), type = bytes.toString('ascii', offset + 4, offset + 8)
  assert.ok(offset + n + 12 <= bytes.length, 'complete PNG chunk')
  const data = bytes.subarray(offset + 8, offset + 8 + n)
  if (type === 'IHDR') {
    width = data.readUInt32BE(0); height = data.readUInt32BE(4); depth = data[8]
    channels = ({ 2: 3, 6: 4 })[data[9]]; interlace = data[12]
    assert.equal(data[10], 0); assert.equal(data[11], 0)
  }
  if (type === 'IDAT') idat.push(data)
  offset += n + 12
  if (type === 'IEND') break
}
assert.equal(depth, 8); assert.equal(interlace, 0); assert.ok(channels)
assert.equal(width, 800); assert.equal(height, 600)
const raw = zlib.inflateSync(Buffer.concat(idat)), stride = width * channels
assert.equal(raw.length, height * (stride + 1))
const decoded = Buffer.alloc(height * stride)
let pos = 0
for (let y = 0; y < height; y++) {
  const filter = raw[pos++]; assert.ok(filter <= 4)
  for (let x = 0; x < stride; x++) {
    const i = y * stride + x, a = x >= channels ? decoded[i - channels] : 0
    const b = y ? decoded[i - stride] : 0, c = y && x >= channels ? decoded[i - stride - channels] : 0
    let predictor = 0
    if (filter === 1) predictor = a
    if (filter === 2) predictor = b
    if (filter === 3) predictor = Math.floor((a + b) / 2)
    if (filter === 4) {
      const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c)
      predictor = pa <= pb && pa <= pc ? a : pb <= pc ? b : c
    }
    decoded[i] = (raw[pos++] + predictor) & 255
  }
}
const rgba = new Uint8Array(width * height * 4)
for (let i = 0; i < width * height; i++) {
  rgba.set(decoded.subarray(i * channels, i * channels + 3), i * 4)
  rgba[i * 4 + 3] = channels === 4 ? decoded[i * channels + 3] : 255
}
const raster = { width, height, rgba }
function inspect({ width, height, rgba }) {
  const boxes = [null, null]
  let nonOpaque = 0
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const i = (y * width + x) * 4, [r, g, b, a] = rgba.subarray(i, i + 4)
    if (a !== 255) nonOpaque++
    const index = r >= 180 && g <= 100 && b <= 100 ? 0 : (b >= 180 && r <= 100 && g <= 150 || g >= 80 && g >= r + 50 && g >= b + 50 && r <= 100 && b <= 100) ? 1 : -1
    if (index < 0) continue
    if (!boxes[index]) boxes[index] = { left: x, top: y, right: x, bottom: y }
    const box = boxes[index]; box.left = Math.min(box.left, x); box.right = Math.max(box.right, x); box.top = Math.min(box.top, y); box.bottom = Math.max(box.bottom, y)
  }
  assert.equal(width, 800); assert.equal(height, 600)
  assert.ok(boxes.every(Boolean), 'expected two saturated foreground colors')
  assert.ok(boxes[0].right < boxes[1].left && boxes[0].left < width / 2 && boxes[1].right > width / 2, 'red left and blue/green right')
  const guardPixels = 8
  const excluded = boxes.map(b => ({ left: b.left - guardPixels, top: b.top - guardPixels, right: b.right + guardPixels, bottom: b.bottom + guardPixels }))
  let checked = 0, nonwhite = 0
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    if (excluded.some(b => x >= b.left && x <= b.right && y >= b.top && y <= b.bottom)) continue
    checked++; const i = (y * width + x) * 4
    if (rgba[i] !== 255 || rgba[i + 1] !== 255 || rgba[i + 2] !== 255 || rgba[i + 3] !== 255) nonwhite++
  }
  return { width, height, nonOpaque, foregroundBoxes: boxes, guardPixels, excluded, checked, nonwhite, pass: nonOpaque === 0 && nonwhite === 0 }
}
const actual = inspect(raster), negative = { ...raster, rgba: raster.rgba.slice() }
negative.rgba[0] = 254
const control = inspect(negative)
assert.equal(control.nonwhite, actual.nonwhite + 1, 'a real off-white background pixel must fail; never classify via whiteness')
assert.equal(control.pass, false)
const result = { file, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), ...actual, negativeControl: { at: [0, 0], rgb: [254, 255, 255], detected: true }, scope: 'All pixels outside expected saturated-foreground bounding rectangles plus 8px resampling-edge guards; not all semantic background. Old fixed x370..420 strip can intersect unconstrained shape edges; its raw 252/249 counts are retained, not relabeled zero.' }
fs.writeFileSync(file + '.strict-background.json', JSON.stringify(result, null, 2));console.log(JSON.stringify(result))

assert.equal(actual.pass, true, 'strict background/opacity failed')

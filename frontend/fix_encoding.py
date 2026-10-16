"""
Fix mojibake in HTML files.

Root cause: emoji bytes were saved as UTF-8 after being misread through Windows-1252.
  e.g. 🔍 (F0 9F 90 8D in UTF-8) was read as Windows-1252 → ðŸ\x90\x8d, then
  re-saved as UTF-8.  Bytes 0x81, 0x8D, 0x8F, 0x90, 0x9D are undefined in cp1252;
  Python maps them to C1 control chars U+0081 etc. when decoding, but won't encode
  them back.  We handle those 5 slots explicitly with their Latin-1 byte values.
"""
import glob

# The 5 cp1252 "undefined" code points — Python can't encode these back, so we do it manually
UNDEF = {'\x81': 0x81, '\x8d': 0x8d, '\x8f': 0x8f, '\x90': 0x90, '\x9d': 0x9d}


def to_original_bytes(text: str) -> bytes:
    buf = bytearray()
    for ch in text:
        if ch in UNDEF:
            buf.append(UNDEF[ch])          # C1 control: use Latin-1 byte value
        else:
            try:
                buf.extend(ch.encode('cp1252'))
            except UnicodeEncodeError:
                buf.extend(ch.encode('utf-8'))  # already correct — keep as-is
    return bytes(buf)


files = sorted(glob.glob("*.html"))
fixed = 0

for path in files:
    with open(path, 'rb') as f:
        raw = f.read()

    # Strip UTF-8 BOM (EF BB BF) — it blocks encoding
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]

    try:
        text = raw.decode('utf-8')
        recovered = to_original_bytes(text).decode('utf-8')
        if recovered != text:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(recovered)
            print(f"Fixed : {path}")
            fixed += 1
        else:
            print(f"OK    : {path}")
    except Exception as e:
        print(f"Error : {path} — {e}")

print(f"\nDone — {fixed} file(s) repaired.")

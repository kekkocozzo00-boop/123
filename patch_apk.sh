#!/bin/bash
# patch_apk.sh - Script di rifirma APK con keystore fresh + bump version
# Uso: bash patch_apk.sh <input.apk> <output_name.apk>
set -e

INPUT="${1:?Uso: $0 <input.apk> <output.apk>}"
OUTPUT="${2:?Uso: $0 <input.apk> <output.apk>}"

# Assicura strumenti
which java >/dev/null || apt install -y default-jdk-headless
which apksigner >/dev/null || apt install -y apksigner zipalign

# Scarica APKEditor se manca
[ -f /tmp/APKEditor.jar ] || curl -sL -o /tmp/APKEditor.jar \
  "https://github.com/REAndroid/APKEditor/releases/download/V1.4.3/APKEditor-1.4.3.jar"

WORK=/tmp/apk_patch_work
rm -rf "$WORK" /tmp/${OUTPUT%.apk}_*.apk

echo "==> Decompilo $INPUT..."
java -jar /tmp/APKEditor.jar d -i "$INPUT" -o "$WORK" 2>&1 | tail -2

# Bump version
echo "==> Bumpo version..."
python3 <<PYEOF
import re
with open('$WORK/AndroidManifest.xml') as f: s = f.read()
m = re.search(r'versionCode="(\d+)"', s)
old_code = int(m.group(1)); new_code = old_code + 1
s = s.replace(f'versionCode="{old_code}"', f'versionCode="{new_code}"', 1)
m = re.search(r'versionName="([0-9.]+)"', s)
old_name = m.group(1)
parts = old_name.split('.')
parts[-1] = str(int(parts[-1]) + 1)
new_name = '.'.join(parts)
s = s.replace(f'versionName="{old_name}"', f'versionName="{new_name}"', 1)
with open('$WORK/AndroidManifest.xml', 'w') as f: f.write(s)
print(f'versionCode {old_code} -> {new_code}, versionName {old_name} -> {new_name}')
PYEOF

# Fresh keystore
echo "==> Genero keystore fresh..."
KS=/tmp/apk_patch_$$.keystore
rm -f "$KS"
keytool -genkeypair -keystore "$KS" \
  -storepass android1 -keypass android1 -alias app \
  -keyalg RSA -keysize 2048 -validity 10950 \
  -dname "CN=App Release, O=Mobile, C=US" 2>&1 | tail -1

# Build
echo "==> Ricompilo..."
java -jar /tmp/APKEditor.jar b -i "$WORK" -o /tmp/apk_patch_unsigned.apk 2>&1 | tail -2

# Zipalign + sign
echo "==> Zipalign + firma..."
zipalign -p -f 4 /tmp/apk_patch_unsigned.apk /tmp/apk_patch_aligned.apk
apksigner sign \
  --ks "$KS" --ks-pass pass:android1 --key-pass pass:android1 \
  --v1-signing-enabled true --v2-signing-enabled true \
  --v3-signing-enabled false --v4-signing-enabled false \
  --out "/tmp/$OUTPUT" /tmp/apk_patch_aligned.apk

apksigner verify --print-certs "/tmp/$OUTPUT" | head -3

echo "==> Pronta: /tmp/$OUTPUT"
ls -lh "/tmp/$OUTPUT"

# Cleanup
rm -rf "$WORK" /tmp/apk_patch_unsigned.apk /tmp/apk_patch_aligned.apk "$KS"
echo "==> Cleanup completato"

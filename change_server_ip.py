#!/usr/bin/env python3
"""
change_server_ip.py - Cambia l'IP del server in un APK decompilato.

Le APK xxPay/Poste/PT hanno l'IP server offuscato con NPStringFog (XOR).
Questo script:
1. Trova la chiave XOR dentro NPStringFog.smali
2. Decodifica tutte le stringhe per trovare l'URL server
3. Lo sostituisce con il nuovo URL (stessa lunghezza richiesta)

Uso:
  python3 change_server_ip.py /tmp/work 185.169.252.172
"""
import os
import re
import sys

def find_key(smali_root):
    """Trova la chiave XOR in NPStringFog.smali"""
    target = os.path.join(smali_root, 'classes/obfuse/NPStringFog.smali')
    if not os.path.exists(target):
        # cerca in altre cartelle
        for root, dirs, files in os.walk(smali_root):
            if 'NPStringFog.smali' in files:
                target = os.path.join(root, 'NPStringFog.smali')
                break
    if not os.path.exists(target):
        return None
    with open(target) as f:
        content = f.read()
    # cerca dopo 'sput-object v0, Lobfuse/NPStringFog;->KEY:'
    m = re.search(r'const-string v0, "([a-z]+)"\s*\n\s*sput-object v0, Lobfuse/NPStringFog;->KEY', content)
    if m:
        return m.group(1).encode()
    # fallback: prima const-string
    m = re.search(r'const-string v0, "([a-z]+)"', content)
    if m:
        return m.group(1).encode()
    return None


def encode(s, key):
    b = s.encode('utf-8')
    return ''.join(f'{c ^ key[i % len(key)]:02X}' for i, c in enumerate(b))


def decode(hex_str, key):
    try:
        b = bytes.fromhex(hex_str)
    except:
        return None
    out = bytearray(len(b))
    for i, ch in enumerate(b):
        out[i] = ch ^ key[i % len(key)]
    return out.decode('utf-8', errors='replace')


def find_server_url(smali_root, key):
    """Cerca tutte le const-string che decodificano in URL ws/http"""
    urls = []
    for root, dirs, files in os.walk(smali_root):
        for fn in files:
            if not fn.endswith('.smali'):
                continue
            path = os.path.join(root, fn)
            with open(path, errors='ignore') as f:
                content = f.read()
            for m in re.finditer(r'"([0-9A-F]{16,80})"', content):
                hx = m.group(1)
                d = decode(hx, key)
                if d and ('ws://' in d or 'http://' in d):
                    urls.append((d, hx, path))
    return urls


def patch_url(smali_root, old_hex, new_hex):
    """Sostituisce la stringa hex in tutti i file smali"""
    count = 0
    for root, dirs, files in os.walk(smali_root):
        for fn in files:
            if not fn.endswith('.smali'):
                continue
            path = os.path.join(root, fn)
            with open(path) as f:
                content = f.read()
            if old_hex in content:
                content = content.replace(old_hex, new_hex)
                with open(path, 'w') as f:
                    f.write(content)
                count += 1
    return count


def patch_plain_urls(smali_root, old_ip, new_ip):
    """Sostituisce IP in chiaro (non offuscati) tipo /api/check_device.php"""
    count = 0
    for root, dirs, files in os.walk(smali_root):
        for fn in files:
            if not fn.endswith('.smali'):
                continue
            path = os.path.join(root, fn)
            with open(path) as f:
                content = f.read()
            if old_ip in content:
                content = content.replace(old_ip, new_ip)
                with open(path, 'w') as f:
                    f.write(content)
                count += 1
    return count


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    work = sys.argv[1].rstrip('/')
    new_ip = sys.argv[2]
    smali_root = os.path.join(work, 'smali')

    key = find_key(smali_root)
    if not key:
        print('ERRORE: chiave NPStringFog non trovata in', smali_root)
        sys.exit(1)
    print(f'Chiave XOR: {key.decode()!r}')

    urls = find_server_url(smali_root, key)
    if not urls:
        print('Nessun URL ws/http offuscato trovato.')
    for url, hx, path in urls:
        print(f'\nTrovato: {url!r}')
        print(f'  hex: {hx}')
        print(f'  file: {path}')

        # Estrai vecchio IP dal URL
        m = re.search(r'(\d+\.\d+\.\d+\.\d+)', url)
        if not m:
            continue
        old_ip = m.group(1)
        if old_ip == new_ip:
            print('  (gia\' al valore corretto, skip)')
            continue
        new_url = url.replace(old_ip, new_ip)
        if len(new_url) != len(url):
            print(f'  ERRORE: lunghezza URL cambia ({len(url)} -> {len(new_url)})')
            print(f'  Usa un IP della stessa lunghezza o aggiungi/togli "/" finali')
            continue
        new_hex = encode(new_url, key)
        c = patch_url(smali_root, hx, new_hex)
        print(f'  patched in {c} file -> {new_url!r}')

    # Cerca anche IP in chiaro
    print('\n--- Cerco IP in chiaro ---')
    for root, dirs, files in os.walk(smali_root):
        for fn in files:
            if not fn.endswith('.smali'):
                continue
            path = os.path.join(root, fn)
            with open(path, errors='ignore') as f:
                content = f.read()
            for m in re.finditer(r'http://(\d+\.\d+\.\d+\.\d+)[^"]*', content):
                old_ip = m.group(1)
                if old_ip != new_ip:
                    c = patch_plain_urls(smali_root, old_ip, new_ip)
                    if c:
                        print(f'  IP in chiaro {old_ip} -> {new_ip} ({c} file)')
                        break

    print('\nDone.')


if __name__ == '__main__':
    main()

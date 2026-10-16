"""Ajusta o projeto Android gerado pelo Capacitor: tela horizontal, modo TV Box e icone."""
import os, re, shutil
from PIL import Image

base = 'android/app/src/main'
mf = f'{base}/AndroidManifest.xml'
s = open(mf, encoding='utf-8').read()

if 'usesCleartextTraffic' not in s:
    s = s.replace('<application', '<application android:usesCleartextTraffic="true" android:banner="@drawable/banner"', 1)
if 'screenOrientation' not in s:
    s = s.replace('<activity', '<activity android:screenOrientation="sensorLandscape"', 1)
if 'LEANBACK_LAUNCHER' not in s:
    s = re.sub(r'(<category android:name="android.intent.category.LAUNCHER"\s*/>)',
               r'\1\n                <category android:name="android.intent.category.LEANBACK_LAUNCHER" />', s, count=1)
if 'android.software.leanback' not in s:
    s = s.replace('</manifest>',
        '    <uses-feature android:name="android.software.leanback" android:required="false" />\n'
        '    <uses-feature android:name="android.hardware.touchscreen" android:required="false" />\n</manifest>')
open(mf, 'w', encoding='utf-8').write(s)

res = f'{base}/res'
img = Image.open('icon.png').convert('RGBA')
shutil.rmtree(f'{res}/mipmap-anydpi-v26', ignore_errors=True)   # usa os PNG em vez do icone adaptativo
for d, sz in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
    p = f'{res}/mipmap-{d}'
    os.makedirs(p, exist_ok=True)
    r = img.resize((sz, sz), Image.LANCZOS)
    for n in ('ic_launcher.png', 'ic_launcher_round.png', 'ic_launcher_foreground.png'):
        r.save(f'{p}/{n}')

os.makedirs(f'{res}/drawable', exist_ok=True)           # banner da TV Box (320x180)
bn = Image.new('RGBA', (320, 180), (4, 10, 34, 255))
bn.paste(img.resize((160, 160), Image.LANCZOS), (80, 10))
bn.save(f'{res}/drawable/banner.png')
print('Android ajustado: orientacao, TV Box, icones e banner.')

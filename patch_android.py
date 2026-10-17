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

# Versao do app: codigo = numero do arquivo versao.txt * 1000 + numero da execucao (sempre sobe)
run = int(os.environ.get('GITHUB_RUN_NUMBER', '1')) % 1000
try:
    base = int(open('versao.txt', encoding='utf-8').read().split()[0])
except Exception:
    base = 1
code = base * 1000 + run
gp = 'android/app/build.gradle'
g = open(gp, encoding='utf-8').read()
g = re.sub(r'versionCode\s+\d+', f'versionCode {code}', g, count=1)
g = re.sub(r'versionName\s+"[^"]*"', f'versionName "1.1.{base}"', g, count=1)
open(gp, 'w', encoding='utf-8').write(g)
print('Versao do app: codigo', code, '/ nome 1.1.%d' % base)

# Volume e botao Voltar tratados pelo app (interface do decodificador)
import glob
for jp in glob.glob('android/app/src/main/java/**/MainActivity.java', recursive=True):
    j = open(jp, encoding='utf-8').read()
    if 'dispatchKeyEvent' not in j:
        body = '''public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(android.os.Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getBridge().getWebView().addJavascriptInterface(new Object() {
            @android.webkit.JavascriptInterface
            public String model() { return android.os.Build.MODEL == null ? "" : android.os.Build.MODEL; }
            @android.webkit.JavascriptInterface
            public String name() {
                try {
                    String n = android.provider.Settings.Global.getString(MainActivity.this.getContentResolver(), "device_name");
                    return n == null ? "" : n;
                } catch (Exception e) { return ""; }
            }
        }, "SatDev");
    }

    @Override
    public boolean dispatchKeyEvent(android.view.KeyEvent e) {
        int k = e.getKeyCode();
        boolean up = k == android.view.KeyEvent.KEYCODE_VOLUME_UP;
        boolean down = k == android.view.KeyEvent.KEYCODE_VOLUME_DOWN;
        boolean mute = k == android.view.KeyEvent.KEYCODE_VOLUME_MUTE;
        boolean back = k == android.view.KeyEvent.KEYCODE_BACK;
        if (up || down || mute || back) {
            if (e.getAction() == android.view.KeyEvent.ACTION_DOWN) {
                if (back) {
                    if (e.getRepeatCount() == 0) getBridge().getWebView().evaluateJavascript("window.nativeBack&&window.nativeBack()", null);
                } else {
                    android.media.AudioManager am = (android.media.AudioManager) getSystemService(android.content.Context.AUDIO_SERVICE);
                    if (am.isVolumeFixed() && !mute) {
                        getBridge().getWebView().evaluateJavascript("window.nativeVolStep&&window.nativeVolStep(" + (up ? 1 : -1) + ")", null);
                    } else {
                        int dir = up ? android.media.AudioManager.ADJUST_RAISE : (down ? android.media.AudioManager.ADJUST_LOWER : android.media.AudioManager.ADJUST_TOGGLE_MUTE);
                        am.adjustStreamVolume(android.media.AudioManager.STREAM_MUSIC, dir, 0);
                        int v = am.getStreamVolume(android.media.AudioManager.STREAM_MUSIC);
                        int m = am.getStreamMaxVolume(android.media.AudioManager.STREAM_MUSIC);
                        boolean mu = am.isStreamMute(android.media.AudioManager.STREAM_MUSIC);
                        getBridge().getWebView().evaluateJavascript("window.nativeVol&&window.nativeVol(" + v + "," + m + "," + mu + ")", null);
                    }
                }
            }
            return true;
        }
        return super.dispatchKeyEvent(e);
    }
}'''
        j2 = re.sub(r'public class MainActivity extends BridgeActivity\s*\{\s*\}', lambda m: body, j, count=1)
        open(jp, 'w', encoding='utf-8').write(j2)
        print('MainActivity ajustada:', jp, '(alterada)' if j2 != j else '(NAO alterada)')

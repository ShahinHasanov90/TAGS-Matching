import os
import sys
import shutil
from pathlib import Path
import PyInstaller.__main__
import json

def create_windows_build():
    """Windows için build klasörü oluştur"""
    print("Windows build hazırlanıyor...")
    
    # Build klasörünü temizle
    build_dir = Path('TAGS_Windows_Build')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    print("Build klasörü oluşturuldu")
    
    # Dosyaları kopyala
    files_to_copy = [
        'tarvel.py',
        'app_icon.svg',
        'temp_network.html',
        'convert_icon.py',
        'requirements.txt',
        'build.bat',
        'TAGS.spec',
        'file_version_info.txt'
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, build_dir / file)
            print(f"{file} kopyalandı")
        else:
            print(f"UYARI: {file} bulunamadı!")
    
    # Settings.json oluştur
    settings = {
        "theme": "Dark"
    }
    with open(build_dir / 'settings.json', 'w') as f:
        json.dump(settings, f)
    print("Settings.json oluşturuldu")
    
    # Zip dosyası oluştur
    shutil.make_archive('TAGS_Windows_Build', 'zip', build_dir)
    print("Zip dosyası oluşturuldu")

def create_macos_build():
    """macOS için build oluştur"""
    print("MacOS build işlemi başlatılıyor...")
    
    # SVG'yi ICNS'e çevir
    os.system("mkdir app.iconset")
    os.system("sips -s format png app_icon.svg --out app.iconset/icon_512x512@2x.png")
    for size in [16, 32, 64, 128, 256, 512]:
        os.system(f"sips -z {size} {size} app.iconset/icon_512x512@2x.png --out app.iconset/icon_{size}x{size}.png")
        if size <= 256:
            os.system(f"sips -z {size*2} {size*2} app.iconset/icon_512x512@2x.png --out app.iconset/icon_{size}x{size}@2x.png")
    os.system("iconutil -c icns app.iconset -o app_icon.icns")
    os.system("rm -rf app.iconset")
    print("Icon oluşturuldu")
    
    # Build klasörünü temizle
    build_dir = Path('dist')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Assets klasörünü kontrol et
    assets_dir = Path('assets')
    if not assets_dir.exists():
        assets_dir.mkdir()
    
    # Gerekli dosyaları assets'e kopyala
    files_to_copy = [
        'app_icon.svg',
        'temp_network.html',
        'lib/tom-select/tom-select.css',
        'lib/tom-select/tom-select.complete.min.js'
    ]
    
    # Pyvis template'ini doğrudan kopyala
    pyvis_template = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Network Visualization</title>
<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet" type="text/css">
</head>
<body>
<div id="mynetwork"></div>
<script type="text/javascript">
    var nodes = new vis.DataSet({{ nodes | safe }});
    var edges = new vis.DataSet({{ edges | safe }});
    var container = document.getElementById("mynetwork");
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {{ options | safe }};
    var network = new vis.Network(container, data, options);
</script>
</body>
</html>
    """
    
    # Template'i assets klasörüne kaydet
    templates_dir = assets_dir / 'templates'
    templates_dir.mkdir(exist_ok=True)
    with open(templates_dir / 'template.html', 'w') as f:
        f.write(pyvis_template)
    print("Pyvis template oluşturuldu")
    
    for file in files_to_copy:
        src = Path(file)
        dst = assets_dir / src.name
        if src.exists():
            # Eğer lib klasöründen geliyorsa, lib klasörünü de oluştur
            if 'lib' in str(src):
                lib_dir = assets_dir / 'lib' / 'tom-select'
                lib_dir.mkdir(parents=True, exist_ok=True)
                dst = lib_dir / src.name
            shutil.copy(src, dst)
            print(f"{file} kopyalandı")
        else:
            print(f"UYARI: {file} bulunamadı!")
    
    # Settings.json oluştur
    settings = {
        "theme": "Dark"
    }
    with open(assets_dir / 'settings.json', 'w') as f:
        json.dump(settings, f)
    print("Settings dosyası oluşturuldu")

    print("PyInstaller build başlatılıyor...")
    
    PyInstaller.__main__.run([
        'tarvel.py',
        '--name=TAGS Matching',
        '--windowed',
        '--onedir',
        '--noconfirm',
        '--clean',
        '--add-data=assets:assets',
        '--icon=app_icon.icns',
        '--hidden-import=customtkinter',
        '--hidden-import=CTkMessagebox',
        '--hidden-import=pyvis',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=networkx',
        '--hidden-import=matplotlib',
        '--hidden-import=numpy',
        '--hidden-import=pandas',
        '--hidden-import=webbrowser',
        '--hidden-import=jinja2',
        '--collect-data=customtkinter',
        '--collect-data=CTkMessagebox',
        '--collect-data=matplotlib',
        '--collect-data=pyvis',
        '--osx-bundle-identifier=com.shahin.tags'
    ])
    
    print("Build tamamlandı!")

if __name__ == "__main__":
    if not sys.platform.startswith('darwin'):
        print("Bu script sadece MacOS'ta çalışır!")
        sys.exit(1)
        
    create_macos_build()
    print("MacOS build paketi hazır!")
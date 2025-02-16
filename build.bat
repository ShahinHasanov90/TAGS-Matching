@echo off
:: 1. Sanal ortam oluştur
python -m venv venv
call venv\Scripts\activate

:: 2. Gerekli paketleri yükle
pip install --upgrade pip
pip install -r requirements.txt

:: 3. İkonu oluştur
python convert_icon.py

:: 4. Uygulamayı paketle
pyinstaller TAGS.spec --clean

echo Build tamamlandi! Sonuclar dist\ klasorunde.
pause 
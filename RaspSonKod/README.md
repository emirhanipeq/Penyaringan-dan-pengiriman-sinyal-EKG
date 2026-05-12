Kod Çalışma sistamatiği aşağıda verilmiştir.


ssh emirhan@IP ADRESİ
sudo systemctl restart vncserver-x11-serviced              (PC DE CMD EKRANINDA BU KOD İLE UZAKTAN ERİŞİM SAĞLAYABİLİYORUZ)


DOSYALARIMIZI RASP IN İÇİNE YĞKLEDİKDEN SONRA ŞU ADIMLARI UYGULUYORUZ)
projenin olduğu klasöre giriş
cd ~/ekg_projesi

 sanal ortamı aktif etme
source ekg_env/bin/activate

 GPIO ayarını yapma
export GPIOZERO_PIN_FACTORY=lgpio

kod çalıştırma
python rpi_ekg.py

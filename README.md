# Project Control Center

GitHub projelerini tek raporda toplayan, bakım önceliği çıkaran ve benzer isimli repoları işaretleyen yerel araç.

## İlk sürüm

- GitHub CLI oturumuyla salt okunur repo bilgisi toplar.
- Açıklama, dil, son kod güncellemesi ve açık issue sayısından açıklanabilir bakım puanı çıkarır.
- Olası isim tekrarlarını listeler. Bu liste otomatik silme/birleştirme önerisi değildir.
- Aranabilir, tek dosyalık HTML ve makinece okunabilir JSON üretir.
- Varsayılan olarak özel repoları rapordan dışlar. Raporlar ve snapshot dosyaları Git tarafından yok sayılır.
- Ağsız kullanım için JSON snapshot girişi destekler.

## Kurulum ve kullanım

Python 3.11+ ve [GitHub CLI](https://cli.github.com/) gerekir. `gh auth login` ile giriş yap.

```bash
python -m pip install -e .
pcc --owner KULLANICI_ADI
```

`reports/index.html` dosyasını tarayıcıda aç. Özel repoları da yalnızca yerel rapora almak için `--include-private` ekle. JSON snapshot ile ağsız çalıştırma: `pcc --input snapshot.json`.

Test: `python -m unittest discover -s tests -v`

## Yol haritası

1. README, test ve CI varlığı için repo içerik denetimi.
2. Açık issue ve başarısız workflow durumlarını önceliklendirme.
3. Elle onaylanan proje hedefleri ve haftalık eylem planı.
4. Zaman içindeki gelişim grafikleri.

Bu sürüm yalnızca metadata okur; GitHub üzerinde issue, PR veya repo değiştirmez.

## CI triage

Kendi hesabındaki **özel depoları** görebilmek için GitHub CLI ile kendi hesabında oturum açmış olman gerekir. Varsayılan rapor özel depoları **dışlar**; raporlar bulutta yayımlanmaz.

```bash
# Salt-okunur: özel depolar hariç, en güncel 20 aktif repo için Actions durumu
pcc --owner emirhankaya-AFK --check-ci

# Yalnızca güvenilen yerel bilgisayarda özel depolar dahil
pcc --owner emirhankaya-AFK --include-private --check-ci --ci-limit 30

# Ağsız snapshot, harici API sorgusu yok
pcc --input snapshot.json
```

- En son GitHub Actions iş akışı çalışmasının sonucunu görüntüler. Workflow çalışması bulunmadığında **Çalışma bulunamadı** yazar; bunun CI kurulmadığını kanıtlamadığını unutma.
- Başarısız CI bakım puanına 30 puana kadar etki eder ve log incelemesini bir sonraki eylem olarak önerir; puan yazılım kalitesi ölçümü değildir.
- Yetki, ağ veya API hatalarını **Doğrulanamadı**; sorgulanmamış depoları **Kontrol edilmedi** gösterir.
- Başarısız Actions çalışmasında job kaydı olsa da **runner adı ve çalıştırılmış adımlar yoksa** olayı **Başlatılamadı** sınıfında gösterir. Bu durum test hatası olarak sunulmaz; runner/kota/hesap durumu ayrıca incelenmelidir. Job ayrıntıları okunamazsa normal **Başarısız** durumu korunur ve testlerin çalıştığı varsayılmaz.
- Başarısız bir çalışmanın job ayrıntısı için en fazla bir ek salt-okunur istek yapılır. Hiçbirini başarılı kabul etmez.
- **--ci-limit** en fazla 100 sorguyla sınırlıdır (varsayılan 20); arşivli depolar sorgulanmaz.
- GitHub CLI'nin oturumunun Actions okuma yetkisi gerekir. Herhangi bir issue/PR/depo, workflow veya secret değiştirilmez; yalnızca yerel HTML/JSON raporları yazılır.
- GitHub Actions `GITHUB_TOKEN` gibi uygulama tokenları `/user` sorgusunu engelleyebilir; **public-only** tarama güvenle `/users/{owner}/repos` yoluna geçer. `--include-private` ise otomatik public'e düşmez: seçilen hesapla kimlik doğrulaması zorunludur, aksi halde açık hata üretir.
- Özel raporları internete yükleme: repo isimleri, durumları ve bağlantıları mahrem olabilir.

Test: `PYTHONPATH=src python -m unittest discover -s tests -v` (Windows PowerShell'de `$env:PYTHONPATH='src'`).

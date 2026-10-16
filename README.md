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

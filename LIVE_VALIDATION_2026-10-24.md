# Project Control Center — Canlı doğrulama (24 Ekim 2026)

## Gerçek GitHub doğrulamaları
- Bağlı GitHub hesabında sahibi olunan **71 depo** görüldü: **62 public, 9 private**.
- GitHub hesabı bağlantısının özel depo metadata erişimi ayrı ayrı **9/9 başarılı**; herhangi bir özel depo adı, verisi, tokenı veya raporu bu public GitHub deposuna eklenmedi.
- Yukarıdaki bağlı hesap sorgusu, yerel `gh auth` oturumunun doğrulandığı anlamına gelmez.

## Gerçek GitHub CLI / Actions smoke
- CI, `GH_TOKEN` olarak yalnız ilgili iş akışının otomatik GitHub tokenını kullanır. Bu token bir kullanıcı PAT'i veya tüm özel depoları okuma izni değildir.
- `pcc --owner emirhankaya-AFK --check-ci --ci-limit 3 --output reports/live-public` komutu gerçek GitHub API bağlantısıyla **62 public depo** için çalıştı. Gerçek JSON ve HTML çıktıları doğrulandı.
- GitHub Actions uygulama tokenı `/user` kimlik sorgusuna erişemiyorsa public-only taramada `/users/{owner}/repos` API'sine geçilir; `--include-private` seçeneğinde kimlik doğrulaması başarısızsa işlem gizlice public taramaya düşürülmez.
- Kimlik kontrolü ve public fallback için üç ek regresyon testi yazıldı. Toplam **16 test** yeşil.

## Güvenlik ve sınırlar
- Yerel kullanıcı bilgisayarında `gh auth login` ile özel depoları kapsayan `pcc --owner ... --include-private --check-ci` komutu çalıştırılmadı; bu *özel CLI yolunun* canlı uçtan uca kabulü ayrı kaldı.
- Bağlı GitHub uygulaması üzerinden **gerçek özel depo okuma izni** doğrulandı, ancak bu bağlantı yetkisi `gh` CLI oturumuna aktarılamaz.
- CI raporları runner üzerindedir, public depo içine yüklenmez; `reports/` klasörü Git tarafından yok sayılır. Gerçek özel depo raporları yalnızca kullanıcının yetkili, yerel ortamında tutulmalıdır.

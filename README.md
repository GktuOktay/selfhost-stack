# selfhost-stack

Kendi makinelerinde çalışan BookStack, Penpot ve Plane kurulumlarının tek merkezi. Depo araçları ve belgeleri taşır. Veri, parola ve token taşımaz.

## Şu an depoda ne var

| Klasör | İçerik | Durum |
|---|---|---|
| `dashboard/` | BookStack ana sayfa paneli (Seni bekliyor, Devam eden, Son değişiklikler, Projeler) | Çalışıyor |
| `docs/` | Spec 0001 (üç uygulamanın ortak kurulumu), spec 0002 (panel), incelemeler, mimari notlar | Belge |
| `stacks/bookstack/theme/`, `tests/` | BookStack theme dilimi ve statik testleri | Kullanılmıyor, ileride için duruyor |

Henüz yok: BookStack, Penpot ve Plane'in Docker Compose kurulumu ve `./stack` komutu. Spec 0001 bunu tarif ediyor ama kodlanmadı. Bu üç uygulamayı başka makinede kurmak için şimdilik kendi kurulumlarını (her birinin resmi Docker kurulum belgesi) elle yapman gerekir.

## Gereksinimler

- Docker ve Docker Compose (v2.24.4 ya da üstü, spec 0001'e göre)
- BookStack, Penpot ve Plane'in çalışır durumda olması
- BookStack'te yönetici hesabı

## Kurulum: başka bir bilgisayara paneli taşımak

1. Depoyu indir:

   ```bash
   git clone https://github.com/GktuOktay/selfhost-stack
   cd selfhost-stack
   ```

2. BookStack'e yönetici olarak giriş yap. "Panel" adlı bir kitap aç, içinde "Panel" adlı bir sayfa oluştur.
3. Sayfayı HTML (WYSIWYG) düzenleyicide aç, kaynak koduna `dashboard/panel-page.html` içeriğini yapıştır ve kaydet.
4. Settings, Customization, "Özel HTML başlık içeriği" alanının sonuna `dashboard/panel-head.html` içeriğini ekle (`selfhost-panel-start` ve `selfhost-panel-end` işaretleri dahil). Alandaki mevcut içeriği silme.
5. Aynı ekranda "Ana sayfa içeriği" ayarını "Spesifik Sayfa" yap ve "Panel" sayfasını seç. Kaydet.
6. Ana sayfayı yenile. Dört panel dolmalı.

Ayrıntı ve geri alma adımları: [`dashboard/README.md`](dashboard/README.md).

## Makineye göre değiştirmen gerekenler

- `dashboard/panel-page.html` içindeki Plane (`localhost:8090`) ve Penpot (`localhost:9001`) adresleri.
- Panelin veri kaynakları BookStack'teki sayfa adlarına dayanır: her projenin "Sorular" ve "Beklenenler" sayfaları ve "İş Planı" kitapları. Farklı adlar kullanıyorsan `panel-head.html` içindeki betiği düzenle.

## Sorun giderme

- **Paneller "Yüklenemedi" diyor:** BookStack API sınırı dakikada 180 istektir. Bir dakika bekle ve sayfayı yenile. Sonuçlar tarayıcıda 2 dakika önbelleğe alınır.
- **Sayfa dar görünüyor, yan paneller duruyor:** Özel başlık içeriği kaydedilmemiş ya da `selfhost-panel-start` bloğu eksik. 4. adımı tekrarla.
- **Paneli kaldırmak:** "Ana sayfa içeriği"ni "Varsayılan"a çevir. Özel başlık alanında `selfhost-panel-start` ile `selfhost-panel-end` arasını sil.

## Güvenlik notları

- Depo özeldir. Parola, token ve `.env` dosyalarını depoya ekleme. `.gitignore` bunları dışarıda tutar.
- Panel tarayıcıda, açık oturumun yetkisiyle BookStack API'sini okur. Ayrı bir token kullanmaz.

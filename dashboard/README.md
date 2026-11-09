# BookStack Panel (ana sayfa dashboard'u)

Tek merkez: bu klasör panelin tek kaynağı. Başka bir bilgisayarda aynısını kurmak için:

1. BookStack'te "Panel" adlı bir kitap aç, içinde "Panel" adlı bir sayfa oluştur. Sayfayı HTML (WYSIWYG) düzenleyicide aç, kaynak koduna `panel-page.html` içeriğini yapıştır, kaydet.
2. Settings, Customization, "Özel HTML başlık içeriği" alanının SONUNA `panel-head.html` içeriğini ekle (`selfhost-panel-start` ve `selfhost-panel-end` işaretleri dahil). Alandaki mevcut içeriği silme.
3. Aynı ekranda "Ana sayfa içeriği" ayarını "Spesifik Sayfa" yap ve "Panel" sayfasını seç. Kaydet.

Geri almak: Ana sayfa ayarını "Varsayılan"a çevir, özel başlık alanında `selfhost-panel-start` ile `selfhost-panel-end` arasını sil.

## Veri nereden gelir

Betik tarayıcıda, oturum açmış kullanıcıyla BookStack API'sini çağırır. Token ya da gizli bilgi yoktur.

- Seni bekliyor: her projenin "Sorular" ve "Beklenenler" sayfalarındaki Durum = Açık satırları. Proje adı kitabın bağlı olduğu raftan gelir.
- Devam eden: "İş Planı" kitaplarındaki sayfalar.
- Son değişiklikler: son güncellenen sayfalar.
- Projeler: raflar.

BookStack API sınırı dakikada 180 istektir. Sonuçlar tarayıcıda 2 dakika önbelleğe alınır.

## Bilinen sınırlar

- BookStack sayfa içindeki `display` ayarlarını kaydederken siler. Bu yüzden düzen sayfada değil `panel-head.html` içindeki stilde.
- Plane verisi yok (token gerektirir). Plane ve Penpot adresleri `panel-page.html` içinde sabit: `localhost:8090` ve `localhost:9001`. Makineye göre değiştir.

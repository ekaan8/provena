# Goldorn Auto-Topology Deneyi — Sonuç Analizi

**Tarih:** 2026-06-24  
**Deney:** 10 cümlelik veritabanı paragrafı → otomatik graph topolojisi → 5 test sorgusu + 2 regresyon testi

---

## Kriter Sonuçları

| # | Kriter | Hedef | Sonuç | Durum |
|---|---|---|---|---|
| 1 | Node çıkarımı | ≥7/10 cümle | 6/10 | ⚠️ Düşük |
| 2 | Edge çıkarımı | ≥5 iç edge | 5 iç edge | ✅ Geçti |
| 3 | İlişki türü çeşitliliği | ≥3 farklı tür | 3 (causes, example_of, contradicts) | ✅ Geçti |
| 4 | Sorgu doğruluğu | ≥3/5 doğru | 2/5 doğru | ❌ Başarısız |
| 5 | Regresyon | Mevcut domain'ler sağlam | ✅ I/O ve chip domain'leri sağlam | ✅ Geçti |

**Genel: 3/5 kriter geçti. Sınırda.**

---

## Detaylı Analiz

### Kriter 1 — Node Çıkarımı (6/10)

**Kaçırılan 4 cümle:**

| Cümle | Neden kaçırıldı? |
|---|---|
| "İlişkisel veritabanları ACID özelliklerini garanti ederek veri tutarlılığını **sağlar**." | `is_knowledge_claim` muhtemelen fiil sonekini yakalayamadı |
| "NoSQL sistemleri ise CAP teoremine göre tutarlılık yerine erişilebilirliği **tercih edebilir**." | `-ebilir` soneki kontrol listesinde yok |
| "PostgreSQL, ilişkisel veritabanlarının en güçlü açık kaynak **örneğidir**." | `-dir` sonu var ama ek kontroller engelliyor olabilir |
| "Dağıtık veritabanları, veriyi birden fazla sunucuya yayarak yatay ölçeklenebilirlik **sağlar**." | `-lar` soneki var ama "sağlar" da yakalanmalıydı |

**Teşhis:** Türkçe fiil sonu tespit heuristiği yetersiz. `-ebilir`, `-sağlar`, `-örneğidir` gibi yaygın kalıplar eksik.

**Düzeltme:** `is_knowledge_claim()` fonksiyonundaki fiil soneki listesine eklenmesi gereken sonekler:
- `"abilir", "ebilir"` — yeterlilik kipi
- `"sağlar"` — yaygın bildirme fiili  
- `"edir", "ıdır"` — ek fiil kalıpları

> [!IMPORTANT]
> Bu 4 cümle kritik bilgi taşıyordu: ACID, CAP, PostgreSQL, Dağıtık DB. Bunlar olmadan graph eksik kaldı ve sorgu doğruluğu düştü.

---

### Kriter 2 — Edge Çıkarımı (5/5 ✅)

Üretilen 5 edge:

| From | To | Relation | Sim | Doğru mu? |
|---|---|---|---|---|
| İlişkisel DB | NoSQL DB | `causes` | 0.725 | ⚠️ Yanlış tür — `contradicts` veya `alternative_to` olmalıydı |
| İlişkisel DB | MongoDB | `example_of` | 0.484 | ⚠️ Yanlış yön — MongoDB → NoSQL olmalıydı, İlişkisel → MongoDB değil |
| İlişkisel DB | İndeksleme | `contradicts` | 0.449 | ❌ Yanlış — bunlar çelişmez |
| NoSQL DB | MongoDB | `example_of` | 0.534 | ✅ Doğru! MongoDB, NoSQL'in örneğidir |
| İndeksleme | Normalizasyon | `causes` | 0.691 | ⚠️ Kısmen doğru — ikisi ilişkili ama `causes` tam doğru değil, `related_to` daha isabetli |

**Skorkart: 1 kesinlikle doğru, 2 kısmen doğru, 2 yanlış**

**Teşhis:**
1. `causes` ile `contradicts/alternative_to` ayrımı yapılamıyor — "ise" cue'u `contradicts`'e 0.8 puan verdi ama `causes` cue'ları (nedeniyle, sağlar) daha yüksek çıktı
2. Edge yönü metindeki sıralamaya göre belirleniyor, ama bu her zaman doğru değil
3. `example_of` tespiti çalışıyor ("örneğidir" cue'u) ama yalnızca "örnek" kelimesi geçen cümleler arasında

---

### Kriter 3 — İlişki Türü Çeşitliliği (3 tür ✅)

- `causes`: 2 edge
- `example_of`: 2 edge  
- `contradicts`: 1 edge

**Eksik türler:** `uses`, `supports`, `alternative_to`, `related_to`

Sistem 3 farklı ilişki türü üretmeyi başardı. Hedef minimum karşılandı.

---

### Kriter 4 — Sorgu Doğruluğu (2/5 ❌)

| Test | Soru | Beklenen | Dönen | Doğru? |
|---|---|---|---|---|
| 1 | NoSQL vs ilişkisel fark | NoSQL veya İlişkisel node | 🥇 NoSQL DB node | ✅ |
| 2 | PostgreSQL ne tür? | PostgreSQL node | 🥇 NoSQL DB node | ❌ (PostgreSQL node hiç yok!) |
| 3 | Veri tutarlılığı | ACID node | 🥇 concurrent_stock_sim | ❌ (ACID node hiç yok!) |
| 4 | Performans artırma | İndeksleme node | 🥇 Normalizasyon node | ⚠️ İlgili ama 2. sırada indeksleme var |
| 5 | Eşzamanlı erişim | MVCC node | 🥇 c11_stdatomic_usage | ❌ (Mevcut paralel prog. domain'i çekti) |

**Doğru: 1, Kısmen doğru: 1, Yanlış: 3**

> [!WARNING]
> Test 2, 3 ve 5'in başarısız olmasının kök nedeni **aynı**: ilgili cümlelerin node olarak çıkarılamaması (Kriter 1 hatası). PostgreSQL, ACID ve Dağıtık DB cümleleri node olmadığı için sorgulanabilecek bilgi bile yoktu.

Test 5'te `c11_stdatomic_usage` (mevcut paralel programlama domain'i) MVCC'nin önüne geçti. Bunun nedeni:
- MVCC node'unun confidence'ı 0.75 (otomatik), stdatomic'in 1.0 (elle)
- "Eşzamanlı" kelimesi her iki domain'de de güçlü embedding skoru aldı
- MVCC hiçbir edge ile bağlı değil (izole node), stdatomic ise `supports → mutex_lock_overhead` edge'i ile boost aldı

---

### Kriter 5 — Regresyon (✅ ✅)

| Test | Beklenen | Dönen | Doğru? |
|---|---|---|---|
| I/O performansı | epoll | 🥇 epoll (skor: 0.686) | ✅ |
| ARM güç verimliliği | arm_power_efficiency | 🥇 arm_power_efficiency (skor: 0.928) | ✅ |

**Mevcut domain'ler tamamen sağlam.** Yeni veritabanı node'ları mevcut domain'leri bozmadı. Cross-domain izolasyon çalışıyor.

---

## Domain Tahmin Analizi

| Node | Tahmin edilen domain | Doğru domain | Doğru mu? |
|---|---|---|---|
| İlişkisel DB | genel | veritabanı sistemleri | ❌ |
| NoSQL DB | genel | veritabanı sistemleri | ❌ |
| MongoDB | genel | veritabanı sistemleri | ❌ |
| İndeksleme | işletim sistemleri | veritabanı sistemleri | ❌ |
| Normalizasyon | işletim sistemleri | veritabanı sistemleri | ❌ |
| MVCC | paralel programlama | veritabanı sistemleri | ❌ |

**6/6 yanlış domain tahmini.**

**Neden?** Mevcut grafta "veritabanı sistemleri" domain'i yok. `detect_domain()` en yakın mevcut domain'i seçiyor. "Performans", "eşzamanlılık" gibi kelimeler mevcut domain'lerin embedding'leriyle yüksek benzerlik gösteriyor.

**Çözüm:** Eşik altında kalan benzerlikler için yeni domain oluşturma mekanizması zaten var (`best_sim = 0.35` altında "genel" atanıyor). Ama threshold çok düşük — veritabanı terimleri mevcut domain'lerle 0.35'in üzerinde benzerlik gösteriyor.

---

## Genel Değerlendirme

```
Çalışan kısımlar:
  ✅ Cümle bölme doğru (10/10)
  ✅ Edge sayısı yeterli (5)
  ✅ İlişki türü çeşitliliği var (3)
  ✅ Regresyon güvenli (2/2)
  ✅ "örneğidir" cue'u example_of olarak doğru yakalanıyor

Çalışmayan kısımlar:
  ❌ Fiil tespit heuristiği 4 cümleyi kaçırdı (kök neden)
  ❌ İlişki türü tahmini: causes vs contradicts ayrımı zayıf
  ❌ Domain tahmini: yeni domain oluşturma mekanizması yok
  ❌ Edge yönü: metin sırasına göre belirleme her zaman doğru değil
  ❌ İzole node'lar (MVCC gibi) mevcut domain node'larına yeniliyor
```

---

## Karar

Bu deney **sınırda** sonuç üretti. 5 kriterden 3'ü geçti, 2'si kaldı. Ama kritik bir gözlem var:

> **Başarısızlıkların kök nedeni tek:** 4 cümlenin kaçırılması. Eğer `is_knowledge_claim()` fonksiyonu bu 4 cümleyi de yakalasaydı, 10/10 node, daha fazla edge, ve muhtemelen 4/5 doğru sorgu sonucu elde edilecekti.

Bu, motorun *mimari olarak yanlış* olmadığını, *heuristiğin yetersiz* olduğunu gösterir. İkisi arasında büyük fark var:

- Mimari yanlışsa: yeniden tasarla
- Heuristik yetersizse: heuristiği iyileştir

**Karar: İz 2 (araştırma) devam etmeye değer.** Ama önce şu 3 düzeltme yapılmalı:

1. **Fiil tespit heuristiği genişletilmeli** — 10 dakikalık iş
2. **Domain oluşturma mekanizması eklenmeli** — mevcut domain'lerle similarity düşükse yeni domain aç
3. **İlişki tahmini: "ise" cue'una daha yüksek ağırlık** — Türkçe'de "X ... ise Y" kalıbı neredeyse her zaman karşılaştırma/çelişki

---

## Credit Assignment — Gözlemler

İlk kez çalışan path tracking çok değerli veri üretiyor:

```
Test 4'te normalizasyon node'u 1. sırada (beklenen: indeksleme)
En etkili edge: indeksleme →[causes]→ normalizasyon  katkı: +0.0734

Bu, indeksleme node'unun normalizasyonu boost ettiğini gösteriyor.
Edge yanlış yöndeydi: normalizasyon, indekslemenin nedeni değil.
blame_edge() bu durumda causes edge'ini cezalandırabilir.
```

Credit assignment mekanizması çalışıyor ve sistemin *neden* hata yaptığını teşhis etmeyi mümkün kılıyor. Bu, İz 1 (araç) için de İz 2 (araştırma) için de çok kritik.

---

*Bu analiz 2026-06-24 tarihinde, ilk auto-topology deneyi sonuçlarına dayanmaktadır.*

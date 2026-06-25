# Provena — Master Plan
**Güncelleme Tarihi:** 2026-06-25
**Karar:** Araştırma + Açık Kaynak + Makale Serisi
**Süre:** 4 hafta yoğun çalışma
**Hedef Çıktı:** Temiz GitHub repo + 4 makaleden oluşan yayın serisi

---

## Bölüm 0 — Mevcut Durum Özeti

### Kod Tabanı Envanteri

| Dosya | Durum | Açıklama |
|---|---|---|
| `knowledge_graph.py` | ✅ Çekirdek — stabil | 1039 satır, tam özellikli |
| `auto_topology.py` | ⚠️ Çalışıyor ama zayıf | 500 satır, heuristik sorunları var |
| `gateway.py` | ✅ Stabil | Dağıtık mimari, 424 satır |
| `domain_server.py` | ✅ Stabil | HTTP API, 188 satır |
| `provena.py` | ✅ Stabil | CLI, 247 satır |
| `ingest_data.py` | ⚠️ Temel seviye | Dosya okuma, geliştirilmeli |
| `knowledge_graph_copy.py` | ❌ Temizle | Eski versiyon — sil |
| `test_v03_features.py` | ❌ Temizle | Eski test — arşivle |
| `test_v05_features.py` | ❌ Temizle | Eski test — arşivle |
| `test_v06_features.py` | ❌ Temizle | Eski test — arşivle |
| `test_v07_features.py` | ❌ Temizle | Eski test — arşivle |
| `test_v08_features.py` | ✅ Aktif test | Mevcut entegrasyon testi |
| `test_auto_features.py` | ✅ Aktif test | auto_topology testi |
| `experiment_auto_topology.py` | ✅ Araştırma | Deney scripti |
| `add_chip_domain.py` | ⚠️ Temizle | One-off seed script |
| `add_v02_nodes.py` | ⚠️ Temizle | One-off seed script |
| `migrate_edges.py` | ⚠️ Temizle | Migrasyon scripti |
| `seed.py` | ✅ Koru | Örnek veri oluşturucu |

### Mevcut Dokümantasyon Envanteri

| Dosya | İçerik | Karar |
|---|---|---|
| `goldorn_progress_v1.md` | v0.2'den v0.8'e kadar tüm geliştirme log'u | ✅ Arşiv — README'de referans ver |
| `goldorn_roadmap_v2.md` | Stratejik yol haritası v2 | ✅ Arşiv — bu plan onun yerini alır |
| `experiment_analysis.md` | auto_topology deney analizi | ✅ Makale 3 için ham veri |
| `search_reports_analysis.md` | Arama raporu analizi | ✅ Makale 3 için ek veri |
| `distributed_cognitive_network_vision.md` | Vizyon belgesi | ✅ Arşiv — Makale 4 için referans |
| `dagitik_ogrenilmis_temsil_fikri.md` | Türkçe teorik yazı | ✅ Makale 1 için ham malzeme |
| `ogrenilebilir_acik_temsil_sistemi_spec_v0_1.md` | Teknik spec | ✅ Arşiv |
| `xanadu_benzeri_ai.txt` | Xanadu bağlantısı | ✅ Makale 1 ve 2 için referans |

### Kanıtlanmış Çalışan Özellikler (v0.8 itibarıyla)

```
✅ FAISS semantik arama (cosine similarity + node confidence)
✅ Multi-hop graf aktivasyonu (2-hop yayılım, domain izolasyonu)
✅ İlişki türüne göre boost/penalty mekanizması
✅ Çelişki çözümleme (confidence → recency → feedback)
✅ Hebbian ağırlık güncellemesi
✅ Credit assignment — blame_edge() ile hatalı edge tespiti
✅ Örtük geri bildirim analizi
✅ Dağıtık mimari: domain_server.py + gateway.py
✅ Semantik yönlendirme (semantic routing)
✅ auto_topology.py — metinden otomatik node/edge çıkarımı
✅ Edge geçmişi ve provenance kaydı
```

### Bilinen Zayıflıklar (Düzeltilecek)

```
❌ auto_topology Türkçe fiil tespiti yetersiz (-ebilir, -sağlar eksik)
❌ Domain tahmini 6/6 yanlış (yeni domain oluşturma mekanizması yok)
❌ İlişki yönü tahmini metindeki sıraya dayalı — her zaman doğru değil
❌ knowledge_graph_copy.py ve eski test dosyaları repoda
❌ README yok
❌ Benchmark / ölçüm scripti yok
❌ requirements.txt yok
```

---

## Bölüm 1 — Karar ve Strateji

### Neden Araştırma + Makale Yolu?

- Ürün yolu için gereken: web UI, auth, %70+ doğruluk, 10K+ node test → 4-8 ay
- Makale + açık kaynak yolu için gereken: kod temizliği + ölçüm + yazı → 4 hafta
- Web sitenize yayınlanan makaleler + GitHub repo → güvenilirlik + trafik + portföy

### Çıktı Hedefleri

```
1. Temiz GitHub reposu (README, requirements.txt, örnek kullanım)
2. Benchmark scripti (Precision@3 ölçümü, before/after karşılaştırma)
3. 4 makale (TR + EN paralel yayın imkânı)
4. Makalelerden repoya, repodan makalelere çapraz bağlantılar
```

---

## Bölüm 2 — 4 Haftalık Plan

### Hafta 1 — Temizlik + GitHub Hazırlığı

**Hedef:** Temiz repo, çalışan kurulum talimatı, profesyonel README

#### 2.1.1 — Repo Temizliği

```
[ ] knowledge_graph_copy.py → SİL
[ ] add_chip_domain.py → docs/archive/ klasörüne taşı
[ ] add_v02_nodes.py → docs/archive/ klasörüne taşı
[ ] migrate_edges.py → docs/archive/ klasörüne taşı
[ ] test_v03, v05, v06, v07 → tests/archive/ klasörüne taşı
[ ] goldorn_progress_v1.md → docs/history/ klasörüne taşı
[ ] goldorn_roadmap_v2.md → docs/history/ klasörüne taşı
[ ] distributed_cognitive_network_vision.md → docs/vision/ klasörüne taşı
[ ] dagitik_ogrenilmis_temsil_fikri.md → docs/vision/ klasörüne taşı
[ ] xanadu_benzeri_ai.txt → docs/references/ klasörüne taşı
```

#### 2.1.2 — Hedef Klasör Yapısı

```
provena/
├── knowledge_graph.py       ← çekirdek motor
├── auto_topology.py         ← otomatik topoloji
├── gateway.py               ← dağıtık yönlendirme
├── domain_server.py         ← HTTP API sunucusu
├── provena.py               ← CLI giriş noktası
├── ingest_data.py           ← veri yükleme yardımcısı
├── seed.py                  ← örnek veri
├── requirements.txt         ← [YENİ]
├── README.md                ← [YENİ]
├── .gitignore               ← [YENİ]
├── GOLDORN_MASTER_PLAN.md   ← bu dosya
├── tests/
│   ├── test_v08_features.py
│   ├── test_auto_features.py
│   └── archive/             ← eski test versiyonları
├── benchmarks/
│   └── benchmark_retrieval.py  ← [YENİ — Hafta 2]
├── docs/
│   ├── architecture.md      ← [YENİ]
│   ├── history/             ← eski roadmap ve progress log'lar
│   ├── vision/              ← vizyon belgeleri
│   └── references/          ← Xanadu, Cyc, NELL notları
└── data/
    └── sample_texts/        ← benchmark için örnek metinler [YENİ]
```

#### 2.1.3 — Yeni Dosyalar

**`requirements.txt`**
```
numpy>=1.24
faiss-cpu>=1.7
sentence-transformers>=2.2
```

**`README.md`** — şu bölümleri içermeli:
- Provena nedir? (3 cümle — net ve çarpıcı)
- Temel formül: `Y = f(X, W)` vs `Y = f(X, Graph)`
- Hızlı kurulum (pip + örnek komut)
- CLI kullanımı (ask, add, import, feedback)
- Mimari diyagramı (ASCII veya Mermaid)
- Makale serisi bağlantıları
- Katkıda bulunma kılavuzu

**`.gitignore`**
```
knowledge.db
*.index
venv/
__pycache__/
*.pyc
.DS_Store
test_db_*.db
```

#### 2.1.4 — auto_topology Heuristik Düzeltmeleri (Hafta 1 teknik işi)

**Görev A: Türkçe fiil tespiti — `is_knowledge_claim()`**

Mevcut kod sadece İngilizce fiil soneklerine bakıyor. Eklenecekler:
```python
turkish_verb_endings = (
    'abilir', 'ebilir',           # yeterlilik kipi ("tercih edebilir")
    'sağlar', 'sağlıyor',         # yaygın bildirme ("veri tutarlılığını sağlar")
    'edir', 'ıdır', 'idir',       # ek fiil ("en güçlü örneğidir")
    'eder', 'ediyor',             # etmek fiili
    'dır', 'dir', 'dur', 'dür',  # bildirme kipi
)
turkish_common_verbs = {
    'sağlar', 'kullanır', 'içerir', 'oluşur',
    'gerektir', 'sunar', 'verir', 'gösterir'
}
```

**Görev B: Domain oluşturma eşiği — `detect_domain()`**

Mevcut eşik 0.35 çok düşük; eski domain'ler her şeyi çekiyor. Düzeltme:
```python
DOMAIN_CREATION_THRESHOLD = 0.45  # 0.35'ten artırıldı

def _infer_domain_name(text):
    """İçerikten domain adı çıkar — anahtar kelime tabanlı."""
    domain_keywords = {
        'database': ['sql', 'nosql', 'mongodb', 'acid', 'index', 'query', 'transaction'],
        'machine_learning': ['neural', 'gradient', 'model', 'training', 'overfitting', 'loss'],
        'networking': ['tcp', 'http', 'protocol', 'packet', 'latency', 'routing'],
        'security': ['encryption', 'authentication', 'vulnerability', 'firewall', 'token'],
        'distributed': ['consensus', 'replication', 'partition', 'fault', 'eventual'],
    }
    text_lower = text.lower()
    for domain, keywords in domain_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return domain
    return 'general'
```

**Hafta 1 Çıktısı:** Temiz repo + çalışan README + düzeltilmiş heuristikler

---

### Hafta 2 — Kanıt Üretme (En Kritik Hafta)

> **Bu hafta olmadan makale yazılamaz.** "Graf öğreniyor" iddiasını sayısal olarak kanıtlayan veriler burada üretiliyor.

#### Deney 1: Graf vs. Saf Embedding

**Araştırma Sorusu:** Graf aktivasyonu retrieval kalitesini iyileştiriyor mu?

```
Koşul A (Baseline):  Sadece FAISS cosine similarity — graf yok
Koşul B (Tam sistem): FAISS + multi-hop aktivasyon + boost/penalty

Metrik: Precision@3
Veri: 3 domain × 50 cümle, her domain için 5 test sorusu = 15 soru toplam
Her iki koşulda da aynı sorular çalıştırılır.
```

Beklenen çıktı tablosu:
```
| Yöntem           | P@3  |
|------------------|------|
| Sadece Embedding | X%   |
| Embedding + Graf | Y%   |
| Fark             | +Z%  |
```

**Benchmark Script:** `benchmarks/benchmark_retrieval.py`
```python
"""
Provena Retrieval Benchmark — Graf vs. Embedding Only
Metrik: Precision@3
İki koşul: (A) sadece embedding, (B) tam sistem
"""
import knowledge_graph

def run_baseline(question, top_k=3):
    """FAISS embedding skoru döndür, graf aktivasyonu uygulamadan."""
    # _base_scores() fonksiyonunu doğrudan çağır
    ...

def run_full_system(question, top_k=3):
    """Tam sistem: FAISS + multi-hop + boost/penalty."""
    hits, paths = knowledge_graph.query(question, top_k=top_k)
    return hits

def precision_at_k(results, expected_keyword, k=3):
    """İlk K sonuç içinde beklenen keyword var mı?"""
    return any(expected_keyword.lower() in r[1].lower() for r in results[:k])
```

#### Deney 2: Feedback ile Öğrenme

**Araştırma Sorusu:** Explicit feedback sonrası retrieval değişiyor mu?

```
Aşama 1: 10 sorgu → sonuçları + aktif edge ağırlıklarını kaydet (baseline)
Aşama 2: Her sorguya explicit feedback ver (reward veya blame)
Aşama 3: Aynı 10 sorguyu tekrar çalıştır
Aşama 4: Edge ağırlık değişimlerini kaydet
Aşama 5: Retrieval sıralaması değişti mi? Karşılaştır.
```

Beklenen çıktı:
```
| Sorgu | Önce (ağırlık) | Feedback | Sonra (ağırlık) | Değişim |
|-------|----------------|----------|-----------------|---------|
| Q1    | 0.50           | reward   | 0.73            | +0.23   |
| Q2    | 0.85           | blame    | 0.62            | -0.23   |
```

#### Deney 3: auto_topology Precision (Güncellenmiş Heuristikle)

Hafta 1'de düzeltilen `is_knowledge_claim()` ile tekrar çalıştır:
```
Domain 1: Operating Systems (50 cümle İngilizce)
Domain 2: Machine Learning (50 cümle İngilizce)
Domain 3: Databases (50 cümle Türkçe + İngilizce karışık)

Ölçüm:
- Node çıkarımı: P@10 (10 cümlede kaç doğru?)
- Edge doğruluğu: Üretilen edge'lerin kaçı mantıklı?
- Domain tahmini: Kaç node doğru domain?
- Sorgu doğruluğu: P@3
```

**Hafta 2 Çıktısı:** 3 deneyin sayısal sonuçları, tablo ve grafik formatında

---

### Hafta 3 — Makale Yazımı

**Hedef:** 4 makalenin taslağını tamamla

---

#### Makale 1 — Felsefi Giriş

**TR:** *Yapay Zeka Neden Unutuyor? Ağırlık Matrisleri ile Açık Temsil Arasındaki Fark*
**EN:** *Why AI Forgets: The Case for Explicit Knowledge Over Weight Matrices*

**Hedef okuyucu:** Teknik olmayan ama meraklı okuyucu. 8-12 dakika okuma.

**Taslak:**
```
1. Giriş — "Neden ChatGPT ne zaman eğitildiğini bilmiyor?"
2. LLM'ler bilgiyi nasıl saklar?
   - Ağırlık matrisleri: sıkıştırılmış, opak, donmuş
   - Güncelleme neden zor (fine-tuning ≠ bilgi ekleme)
   - Hallüsinasyon kaçınılmaz mı?
3. Alternatif: Açık temsil
   - Node + edge + weight = şeffaf, güncellenebilir, izlenebilir
   - "Bu bilgi nereden geldi?" sorusu her zaman yanıtlanabilir
   - Tek fact değişimi tüm sistemi bozmaz
4. Provena — Bu fikrin prototipi
   - Y = f(X, W) vs Y = f(X, Graph)
   - Tek cümle: "Provena bilgiyi grafta tutar ve geri bildirimden öğrenir"
5. Sonraki makale: Bu fikri önceden deneyenler ne yaptı?
```

**Ham Malzeme:** `dagitik_ogrenilmis_temsil_fikri.md` + `xanadu_benzeri_ai.txt`
**Uzunluk:** 1200-1800 kelime

---

#### Makale 2 — Tarihten Ders

**TR:** *Cyc ve NELL Neden Başarısız Oldu — ve Biz Ne Öğrendik*
**EN:** *Why Cyc and NELL Failed — And What We Learned From Them*

**Hedef okuyucu:** AI/CS geçmişi olan okuyucu. 10-15 dakika okuma.

**Taslak:**
```
1. Giriş — "1984'te Doug Lenat binlerce insan-yıl harcayacağını söyledi"
2. Cyc: İnsan bilgisini elle kodlama
   - Başlangıç noktası (Lisp Machines'in çöküşü)
   - Büyüklük (600K+ kural, 30+ yıl)
   - Neden tamamlanamadı (common sense bottleneck, long tail problem)
3. NELL: İnternetten öğrenen sistem
   - Sürekli öğrenme iddiası (2010-2018)
   - Gürültü problemi: Kalitesiz veri büyük graph'ı mahvetti
   - Neden durdu
4. Ortak hata: Ölçek ≠ Anlayış
   - Daha fazla kural / daha fazla web verisi çözüm değildi
   - Öğrenme kalitesi, miktarından önemli
5. Provena ne farklı yapıyor?
   - Elle değil, auto_topology ile otomatik
   - Öğrenme: confidence × feedback — sadece kullanılan bilgi güncellenir
   - Küçük ama doğrulanmış
6. Sonraki makale: Deneyin sayısal sonuçları
```

**Ham Malzeme:** `goldorn_progress_v1.md §4 Theoretical Background` + Cyc/NELL web kaynakları
**Uzunluk:** 1500-2000 kelime

---

#### Makale 3 — Teknik Deney

**TR:** *Hebbian Öğrenme Bir Bilgi Grafiğinde Çalışır mı? Provena ile Bir Deney*
**EN:** *Does Hebbian Learning Work in a Knowledge Graph? An Experiment with Provena*

**Hedef okuyucu:** Teknik okuyucu, ML/AI geçmişi. 15-20 dakika okuma.

**Taslak:**
```
1. Giriş — Araştırma sorusu: "Graf semantiği retrieval'ı gerçekten iyileştiriyor mu?"
2. Sistem Mimarisinin Özeti
   - FAISS + SQLite + multi-hop aktivasyon
   - Hebbian kuralı: Δw = η × feedback × confidence − (decay × günler)
   - blame_edge: "Hangi kenar bu hatadan sorumlu?"
3. Deney Tasarımı
   - Deney 1: Graf vs Embedding (metodoloji)
   - Deney 2: Feedback ile öğrenme (metodoloji)
   - Deney 3: auto_topology doğruluk ölçümü
4. Bulgular (Hafta 2 sayıları)
   - Tablo 1: Graf vs Embedding Precision@3
   - Tablo 2: Edge ağırlık değişimleri (before/after)
   - Tablo 3: auto_topology node/edge doğruluğu
5. Yorum
   - Ne çalıştı: Multi-hop boost tutarlı iyileştirme gösterdi
   - Ne çalışmadı: Domain tahmini (6/6 yanlış) — neden ve nasıl düzeldi
   - Sınırlamalar: 25 node, tek makine, Türkçe heuristik eksikleri
6. Repo ve Kod
7. Sonraki makale: Bu şeffaflık neden önemli?
```

**Ham Malzeme:** `experiment_analysis.md` + Hafta 2 benchmark çıktıları
**Uzunluk:** 2000-2500 kelime

---

#### Makale 4 — Tasarım Felsefesi

**TR:** *Kara Kutu Olmayan Yapay Zeka: İzlenebilir Bilginin Tasarımı*
**EN:** *AI Without Black Boxes: Designing for Traceable Knowledge*

**Hedef okuyucu:** Kurumsal okuyucu + XAI ilgisi olan. 10-15 dakika okuma.

**Taslak:**
```
1. Giriş — "Yapay zekaya neden bunu söylediğini soramazsın"
2. Şeffaflık Sorunu
   - GDPR: Otomatik karar açıklanabilir olmak zorunda
   - Mevcut XAI araçları: LIME/SHAP post-hoc, gerçek şeffaflık değil
3. Provena'nun 3 Şeffaflık Mekanizması
   a. Provenance: source + created_at + confidence her node'da
   b. blame_edge(): Yanlış sonucun sorumlu kenarını bulur
   c. resolve_contradictions(): Winner/loser kararı izlenebilir log bırakır
4. Somut Örnek: Bir sorgunun tam izi
   - Sorgu → FAISS → 30 aday → 2-hop subgraph → boost/penalty → çelişki → karar
   - Her adım SQLite'da kayıtlı
5. Neden Önemli?
   - Hukuk: hangi içtihatın hangi karara yol açtığı izlenebilir
   - İlaç: hangi bulgunun hangi hipotezi desteklediği takip edilebilir
   - Kurumsal KB: politika değişikliği history'si korunuyor
6. Açık Sorular ve Sınırlamalar
7. Sonuç: "Şeffaflık özellik değil, tasarım kararıdır"
```

**Ham Malzeme:** `distributed_cognitive_network_vision.md` + `knowledge_graph.py` blame/contradiction fonksiyonları
**Uzunluk:** 1500-2000 kelime

---

### Hafta 4 — Yayın + Bağlantılar

**Hedef:** Her şeyi dışarı aç, birbirine bağla

#### 2.4.1 — GitHub Release

```
[ ] README son halini al — kurulum talimatı test et
[ ] requirements.txt temiz ortamda test edildi
[ ] Tüm testler yeşil (test_v08_features.py, test_auto_features.py)
[ ] knowledge.db .gitignore'da
[ ] İlk tag: v0.8.0
[ ] Release notes: "Research release — 4 makale ile birlikte"
```

#### 2.4.2 — Website Yayını

```
[ ] Makale 1 → website yayını
[ ] Makale 2 → website yayını
[ ] Makale 3 → website yayını (GitHub bağlantısı dahil)
[ ] Makale 4 → website yayını
[ ] Seri navigasyonu: "Önceki / Sonraki" bağlantıları
[ ] Her makalede "Kaynak kodu: GitHub" bağlantısı
[ ] README'de "Yazı serisi" bölümü
```

#### 2.4.3 — Opsiyonel Duyuru

```
[ ] Hacker News: "Show HN: Provena — explicit knowledge graph with Hebbian learning"
[ ] Twitter/X: Makale per makale kısa thread
[ ] LinkedIn: Araştırma özeti
```

---

## Bölüm 3 — Makale Yazım Prensipleri

### Her Makale İçin Kontrol Listesi

```
[ ] Başlık: Soru veya güçlü iddia — merak uyandırsın ama clickbait olmasın
[ ] İlk paragraf: "Bu neden önemli?" 30 saniyede yanıtlansın
[ ] Teknik terimler: İlk kullanımda açıkla
[ ] Her iddia için sayı: P@3, edge ağırlık değişimi, doğru/yanlış sayısı
[ ] Sınırlamalar: Açıkça yaz — "25 node, 10.000'de ne olur bilinmiyor"
[ ] Minimal kod örneği: Her teknik makalede en az 1 snippet
[ ] Bağlantılar: GitHub + diğer makaleler + kaynaklar
[ ] Uzunluk: 1200-2500 kelime (1 oturumda okunabilir)
[ ] Son paragraf: Okuyucuyu bir sonraki makaleye yönlendir
```

### Ton ve Üslup

- **Dürüst:** "Bu sistem 25 node ile test edildi"
- **Birinci şahıs:** "Yaptım, gördüm, şunu anladım"
- **Teknik ama erişilebilir:** Formül ver, sonra düz dille açıkla
- **Kaçın:** "Revolutionary", "state-of-the-art", "game-changer"

---

## Bölüm 4 — Başarı Kriterleri

### Hafta 1 Sonunda
```
[ ] python provena.py ask "test" temiz çalışıyor
[ ] pip install -r requirements.txt && python provena.py graph çalışıyor
[ ] README 5 dakikada sistemi anlatıyor
[ ] Repo temiz — eski dosyalar arşivde
[ ] auto_topology Türkçe 7+/10 cümleyi yakalıyor (eski: 6/10)
```

### Hafta 2 Sonunda
```
[ ] benchmark_retrieval.py P@3 tablosu üretiyor
[ ] Graf vs Embedding farkı sayısal olarak ölçüldü
[ ] Feedback etkisi 10 sorgu üzerinde belgelendi
[ ] Makale 3 için tablolar hazır
```

### Hafta 3 Sonunda
```
[ ] 4 makale taslağı tamamlandı (her biri 1000+ kelime)
[ ] Tüm iddialar sayısal destekle
[ ] EN versiyonlar hazır veya çeviri notları tamamlandı
```

### Hafta 4 Sonunda
```
[ ] GitHub repo public ve çalışıyor
[ ] En az 2 makale website'de yayınlandı
[ ] README → website, website → GitHub bağlantıları aktif
[ ] Tüm testler yeşil
```

---

## Bölüm 5 — Risk Analizi

| Risk | Olasılık | Etki | Çözüm |
|---|---|---|---|
| auto_topology düzeltmeleri Hafta 1'i aşar | Orta | Yüksek | Sadece Türkçe desteği öncelikli; domain tahmini Hafta 2'ye bırak |
| Benchmark sayıları beklenmedik çıkar (grafın etkisi ölçülemez?) | Düşük | Yüksek | "Beklenmedik sonuç" da bir bulgudur — dürüstçe raporla |
| Makale yazımı 3. haftayı aşar | Yüksek | Orta | 4 makale yerine 2 yayınla, 2'yi hazır tut |
| Ollama bağımlılığı test ortamını karmaşıklaştırır | Orta | Düşük | Testlerde Ollama bölümünü `@skipIf(not ollama_available)` ile işaretle |

---

## Bölüm 6 — Gelecek Aşama (1 Ay Sonrası)

Bu plan tamamlandıktan sonra bulgulara göre karar verilir:

**Seçenek A — Makale Serisi Devam**
- Makale 5: "Distributed Knowledge Graphs — Bir Vizyon"
- arXiv preprint
- Akademik topluluklarla temasa geç

**Seçenek B — Araç Yoluna Geç**
- Ciddi ilgi geldiyse temel web UI ekle
- Belirli bir kullanım alanı seç
- 5-10 pilot kullanıcıya ver

**Seçenek C — Organik Büyüme**
- Repo + makaleler hazır, aktif pazarlama yok
- İlgi gelirse yön ver

---

## Bölüm 7 — Hızlı Referans

### Mimari Akış

```
Ham Metin / Kullanıcı Girdisi
        |
   auto_topology.py
   (cümle bölme → knowledge claim filtresi → embedding → node/edge çıkarımı)
        |
   knowledge_graph.py
   (SQLite node/edge + FAISS embedding index)
        |
  Sorgu: FAISS → candidate nodes → load_active_subgraph()
        |
  Multi-hop aktivasyon + boost/penalty + domain izolasyonu
        |
  resolve_contradictions() → winner/loser tespiti
        |
  blame_edge() → credit assignment
        |
  update_weight() → Hebbian öğrenme
        |
  Çıktı: (node_id, content, confidence, score) listesi
        |
  [Opsiyonel] Ollama NL üretimi
        |
  [Dağıtık] domain_server.py → gateway.py → semantic routing
```

### Temel Formüller

```
Hebbian güncelleme:
  new_weight = clamp(old_weight + (feedback × confidence) − (0.01 × decay_days), 0.0, 1.0)

Boost katkısı:
  contribution = source_score × edge_weight × relation_coef × domain_coef × attention

Contradiction çözüm sırası:
  1. confidence (yüksek kazanır)
  2. created_at (yeni kazanır)
  3. positive feedback count (fazla kazanır)
  Kaybeden: score × 0.10

Precision@K:
  P@K = (ilk K sonuç içinde doğru keyword geçen sonuç sayısı) / K
```

### Temel Kavramlar

| Terim | Provena Karşılığı |
|---|---|
| Node | Tek bir bilgi birimi (cümle/paragraf) |
| Edge | İki node arasındaki typed, weighted ilişki |
| Hop | Bir edge'i takip etme — grafta bir adım |
| Boost | İlişki türüne göre skor artışı |
| Blame | Yanlış sonucun sorumlu edge'ini bulma |
| Episode | Bir sorgu kaydı (query + top_node + feedback) |
| Domain | Node'ların konusal grubu |
| Confidence | Node güvenilirlik skoru (0.0–1.0) |

---

*Bu belge 4 haftalık araştırma-yayın sprint'i için master referanstır.*
*Her haftanın başında ilgili bölüm okunur, görevler tamamlandıkça işaretlenir.*

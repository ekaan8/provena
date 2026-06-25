# Goldorn — Stratejik Yol Haritası v2.0

**Tarih:** 2026-06-24  
**Hazırlayan:** Antigravity (Goldorn kod tabanı, tüm belgeler ve kaynak kodun tam analizi sonrası)  
**Kapsam:** v0.2'den v1.0'a — stratejik yön, teknik öncelikler, kaçınılması gerekenler

---

## 0. Durum Değerlendirmesi — Neredeyiz?

### Kanıtlanmış Olanlar ✅

| Yetenek | Kanıt |
|---|---|
| Embedding tabanlı anlamsal arama | Cosine similarity ile çalışıyor |
| Graf yapısı skor'a etki ediyor | `supersedes` edge, epoll'ü select'in üzerine çıkarttı |
| Penalty mekanizması çalışıyor | select skoru 0.574 → 0.478 |
| Multi-hop propagation | 2-hop zincirler üzerinden aktivasyon yayılıyor |
| Cross-domain izolasyon | I/O ve chip domain'leri birbirini bozmuyor |
| Hebbian öğrenme (basit) | Edge weight 0.85 → 1.00 feedback ile |
| Episode logging | Sorgu geçmişi kaydediliyor |

### Kanıtlanmamış Olanlar ⚠️

| Yetenek | Durum |
|---|---|
| Otomatik node üretimi | Yok — her node elle yazılıyor |
| Credit assignment | Yok — hangi edge'in hatadan sorumlu olduğu bilinmiyor |
| İmplicit feedback | Yok — sadece explicit +1/0/-1 |
| Doğal dil üretimi | Yok — ham node content döndürülüyor |
| Ölçek | 17 node — 10.000'de ne olacağı bilinmiyor |
| Dağıtık mimari | Tamamen yerel, tek SQLite dosyası |
| Çelişki çözümleme | İki çelişen node aktif olunca karar mekanizması yok |

### Kritik Gözlem

**v0.2 bir proof-of-concept'tir, bir ürün değildir.** Kanıtladığı şey önemlidir: *graf semantiği, ham embedding benzerliğini override edebilir.* Bu, projenin temel tezinin geçerli olduğunu gösterir. Ama bu, projenin tezini kanıtladığı anlamına da gelmez — sadece *çelişmediğini* gösterir.

---

## 1. Kritik Karar Noktası — Çatal

Şu an projenin önünde iki yol var. **Yanlış seçim, projeyi öldürür.**

### Yol A: "Hızla büyüyelim" (YANLIŞ)
- Web sitelerine dağıtalım
- Binlerce node ekleyelim
- Dağıtık sistem kuralım

**Bu neden yanlış:** Temel motor 17 node'da bile semantik hata yapabiliyor (bkz: `arm_risc_architecture`'ın `apple_silicon_transition` yerine gelmesi). Zayıf bir motoru ölçeklemek, zayıflığı büyütmek demektir.

### Yol B: "Motoru sağlamlaştıralım" (DOĞRU)
- Öğrenme mekanizmasını derinleştirelim
- Otomatik node üretimi kuralım
- Credit assignment problemi çözelim
- Doğal dil üretim katmanı ekleyelim
- Sonra ölçekleyelim

**Kararım: Yol B.**

Gerekçe: Ted Nelson'ın Xanadu'su *tam olarak bu hatayı yaptı* — vizyonu büyüktü ama çalışan bir temel inşa etmeden ölçeklemeye çalıştı ve 60 yıl boyunca hiç bitmedi. Goldorn aynı hatayı yapmamalı.

---

## 2. Yedi Aşamalı Plan

```
v0.3  Motor Sağlamlaştırma          ← ŞİMDİ
v0.4  Otomatik Bilgi Çıkarımı       ← 2-3 hafta
v0.5  Dil Üretim Katmanı            ← 1-2 hafta
v0.6  Ölçek Altyapısı               ← 2-3 hafta
v0.7  CLI + Günlük Kullanım         ← 1-2 hafta
v0.8  Dağıtık Mimari Temelleri      ← 3-4 hafta
v1.0  Kişisel Bilgi İşletim Sistemi ← Hedef
```

---

## 3. v0.3 — Motor Sağlamlaştırma (ŞİMDİ YAPILACAK)

Bu aşama, mevcut kodun üzerine inşa eder. Yeni mimari değil, mevcut mimarinin derinleştirilmesi.

### 3.1 Credit Assignment — Hatalı Edge'i Bul

**Problem:** Sorgu A→B→C yolunu izliyor, sonuç yanlış. Hangi edge suçlu?

**Çözüm: Path Recording**

```python
# Her query'de aktif olan yolları kaydet
def query(question, top_k=3, hops=2):
    ...
    paths = []  # [(from, to, relation, contribution)]
    
    for from_node, to_node, weight, relation in edges:
        contribution = boosted[source] * weight * effective_coef
        if abs(contribution) > 0.01:
            paths.append((from_node, to_node, relation, contribution))
    
    return results, paths  # artık yolu da döndür
```

Negative feedback gelince, path üzerindeki *en büyük katkıyı yapan edge*'in weight'ini düşür:

```python
def blame_edge(paths, feedback):
    """Credit assignment: en yüksek katkılı edge'i bul ve cezalandır."""
    if feedback < 0 and paths:
        worst = max(paths, key=lambda p: abs(p[3]))
        update_weight(worst[0], worst[1], feedback=-1, confidence=0.5)
```

### 3.2 Implicit Feedback — Kullanımdan Öğren

Explicit feedback (+1/-1) yetersiz. Şu sinyalleri otomatik üret:

| Sinyal | Anlamı | Feedback Değeri |
|---|---|---|
| Aynı soru tekrar soruldu | İlk cevap yetersizdi | -0.3 |
| Top-1 node tekrar sorgulandı | Kullanıcı derinleşiyor, cevap doğruydu | +0.5 |
| Sorgu sonrası hiç etkileşim yok | Nötr veya yetersiz | 0 |
| Aynı domain'de ardışık 3+ sorgu | Domain ilgisi yüksek | Domain edge'lerine +0.2 |

Bu, `episodes` tablosunu analiz ederek yapılır:

```python
def analyze_implicit_feedback():
    """Episode geçmişinden implicit sinyaller çıkar."""
    conn = sqlite3.connect(DB_PATH)
    episodes = conn.execute(
        "SELECT query, top_node, created_at FROM episodes ORDER BY id"
    ).fetchall()
    # Tekrarlanan sorgular → negative signal
    # Derinleşen sorgular → positive signal
    ...
```

### 3.3 Çelişki Çözümleme

İki node `contradicts` ilişkisiyle bağlıysa ve ikisi de aktif oluyorsa:

```
Karar kuralı:
1. confidence yüksek olan kazanır
2. Eşitse, created_at yeni olan kazanır (daha güncel bilgi)
3. O da eşitse, daha çok positive feedback almış olan kazanır
```

Bu, `query()` fonksiyonuna eklenir — penalty mekanizmasının üzerine inşa edilir.

### 3.4 Edge Versioning

Her edge güncellemesini kaydet:

```sql
CREATE TABLE IF NOT EXISTS edge_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node   TEXT NOT NULL,
    to_node     TEXT NOT NULL,
    old_weight  REAL,
    new_weight  REAL,
    reason      TEXT,  -- 'feedback', 'decay', 'implicit', 'blame'
    created_at  TEXT
);
```

Bu, sistemin *nasıl öğrendiğini* izlemeyi sağlar. Xanadu'nun "her versiyonu koru" prensibi.

---

## 4. v0.4 — Otomatik Bilgi Çıkarımı

Bu aşama, sistemi "elle node yazma" köleliğinden kurtarır.

### 4.1 Metin → Node Pipeline

```
Ham metin (paragraf, not, makale özeti)
    ↓
Cümlelere böl (spaCy veya basit regex)
    ↓
Her cümle bir bilgi iddiası mı? (filtre)
    ↓
Node ID üret (içerikten hash veya slug)
    ↓
Domain tahmin et (mevcut domain'lerle embedding benzerliği)
    ↓
Edge öner (yeni node vs. mevcut node'lar arası benzerlik)
    ↓
add_node() + add_edge()
```

### 4.2 Neden LLM API Kullanılmamalı (Şimdilik)

Claude veya GPT API ile "bu metni parse et" demek kolay ama:
- Maliyet ölçeklenmez
- Dış bağımlılık yaratır
- Goldorn'un kendi kendine yetme felsefesiyle çelişir

**Tercih: Yerel kurallar + embedding benzerliği.**

Bir cümlenin bilgi iddiası olup olmadığını anlamak için:
- Fiil içeriyor mu?
- Özne-nesne ilişkisi var mı?
- Uzunluk > 8 kelime mi?
- Soru cümlesi değil mi?

Bu basit filtre, %70-80 doğrulukla çalışır ve yeterlidir.

### 4.3 Otomatik Edge Önerme

Yeni node eklendiğinde mevcut tüm node'larla cosine similarity hesapla. Threshold üstündeki çiftler için:

```python
def suggest_edges(new_node_id, threshold=0.65):
    """Yeni node için olası edge'leri öner."""
    new_emb = get_embedding(new_node_id)
    candidates = []
    for existing_id, existing_emb in all_embeddings():
        sim = cosine(new_emb, existing_emb)
        if sim > threshold:
            # İlişki türünü tahmin et
            relation = guess_relation(new_node_id, existing_id, sim)
            candidates.append((existing_id, relation, sim))
    return candidates
```

İlişki türü tahmini için basit kurallar:
- Çok yüksek benzerlik (>0.85) → `related_to` veya `supports`
- Aynı domain + orta benzerlik → `part_of` veya `example_of`
- Farklı domain + yüksek benzerlik → `related_to`

---

## 5. v0.5 — Dil Üretim Katmanı

### Neden Şart?

Şu an sistem şunu döndürüyor:
```
🥇 [io_multiplexing_epoll]  güven:1.0  skor:0.553
   epoll_wait() sistem çağrısı, yalnızca olay gerçekleşen...
```

Bu, bir veritabanı sonucudur. İnsanın beklediği:
```
Yüksek bağlantı sayısında en uygun I/O yöntemi epoll'dür. 
epoll_wait() yalnızca aktif olan file descriptor'ları döndürdüğü 
için O(1) ölçeklenebilirlik sağlar. Klasik select() ise O(N) 
tarama yaptığından yüksek FD sayılarında performans kaybı yaşar.
```

### Nasıl?

**Katmanlı yaklaşım — model boyutunu kademeli artır:**

1. **Şablon tabanlı (ilk adım, model gerektirmez):**
```python
TEMPLATES = {
    "supersedes": "{from_content}. Bu, {to_content} yaklaşımının yerini almıştır.",
    "contradicts": "{from_content}. Ancak {to_content} ile çelişir.",
    "supports": "{from_content}. Bu iddia, {to_content} tarafından desteklenmektedir.",
}
```

2. **Küçük yerel model (Ollama + Phi-3 Mini veya Gemma 2B):**
```python
def generate_answer(top_nodes, question):
    context = "\n".join([
        f"- {node.content} (kaynak: {node.source}, güven: {node.confidence})"
        for node in top_nodes
    ])
    prompt = f"""Aşağıdaki bilgilere dayanarak soruyu yanıtla.
    
Soru: {question}

Bilgi:
{context}

Yanıt:"""
    return ollama.generate(model="phi3:mini", prompt=prompt)
```

3. **Hibrit (uzun vadeli):**
   - Graf çıkarımı → top-K node ve ilişkiler
   - Küçük model → akıcı dil üretimi
   - Kaynak gösterimi → her cümlede [kaynak: X] etiketi

> [!IMPORTANT]
> Burada kritik karar: İlk aşamada şablon tabanlı üretim yeterlidir. Ollama entegrasyonu v0.5'in **ikinci yarısında** gelir. Şablon sistemi tek başına büyük bir UX iyileştirmesi sağlar ve dış bağımlılık getirmez.

---

## 6. v0.6 — Ölçek Altyapısı

### 6.1 FAISS Entegrasyonu

17 node'da her sorgu tüm embedding'leri yüklüyor. 10.000 node'da bu çalışmaz.

```python
import faiss

class EmbeddingIndex:
    def __init__(self, dimension=384):
        self.index = faiss.IndexFlatIP(dimension)  # inner product
        self.id_map = []  # index position → node_id
    
    def add(self, node_id, embedding):
        self.index.add(np.array([embedding], dtype='float32'))
        self.id_map.append(node_id)
    
    def search(self, query_embedding, top_k=20):
        scores, indices = self.index.search(
            np.array([query_embedding], dtype='float32'), top_k
        )
        return [(self.id_map[i], scores[0][j]) 
                for j, i in enumerate(indices[0]) if i >= 0]
```

### 6.2 Lazy Graph Loading

Tüm edge'leri yüklemek yerine, FAISS'ten gelen top-20 node'un komşularını yükle:

```python
def _get_relevant_edges(node_ids):
    placeholders = ','.join(['?'] * len(node_ids))
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f'''
        SELECT from_node, to_node, weight, relation FROM edges
        WHERE from_node IN ({placeholders}) OR to_node IN ({placeholders})
    ''', node_ids + node_ids).fetchall()
    conn.close()
    return rows
```

### 6.3 Benchmark Hedefleri

| Node Sayısı | Hedef Latency (query) |
|---|---|
| 100 | < 50ms |
| 1.000 | < 200ms |
| 10.000 | < 500ms |
| 100.000 | < 1s |

---

## 7. v0.7 — CLI + Günlük Kullanım

Sistem günlük hayatta kullanılmazsa ölür. Bu aşama, Goldorn'u bir araç haline getirir.

### 7.1 Komut Satırı Arayüzü

```bash
goldorn ask "ARM neden güç verimli?"
goldorn add "Python GIL, gerçek paralelliği engeller" --domain "programlama" --source "Python Docs"
goldorn import notes.md              # Markdown → otomatik node'lar
goldorn feedback --last positive     # Son sorguya pozitif feedback
goldorn graph show                   # Mevcut graf'ın özeti
goldorn history                      # Son sorgular
goldorn domains                      # Domain listesi ve node sayıları
```

### 7.2 Kişisel Veri İthalatı

- Markdown notlar → otomatik node çıkarımı (v0.4'ten)
- Yer imleri / kaydedilen makaleler → kaynak referanslı node'lar
- Kitap notları → domain etiketli yapılandırılmış bilgi

---

## 8. v0.8 — Dağıtık Mimari Temelleri

> [!WARNING]
> Bu aşama, v0.3-v0.7 tamamlanmadan **BAŞLAMAZ**. Erken dağıtık mimari, projeyi öldürür.

### 8.1 Vizyonun Netleştirilmesi

Senin orijinal vizyonun: *"Binlerce, belki milyonlarca web sitesinde LLM işlemlerini yaparak fiziksel GPU'ya mahkum kalmadan kişisel LLM üretmek."*

Bu vizyonun teknik karşılığı şu değildir:
- ❌ Her web sitesine bir model parçası yerleştirmek
- ❌ Matrix çarpımını HTTP üzerinden dağıtmak

Bu vizyonun teknik karşılığı şudur:
- ✅ Bilgi temsilini dağıtık node sunucularına yaymak
- ✅ Her "alan" (domain) kendi bilgi kümesiyle kendi sunucusunda yaşar
- ✅ Sorgular, ilgili domain sunucularına yönlendirilir
- ✅ Sonuçlar merkezi bir çıkarım katmanında birleştirilir

### 8.2 Dağıtık Mimari Taslağı

```
                    ┌─────────────────────┐
                    │   Goldorn Gateway    │
                    │  (Query Router)      │
                    └─────────┬───────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
         ┌──────▼──────┐ ┌───▼──────┐ ┌────▼─────┐
         │  Domain A   │ │ Domain B │ │ Domain C │
         │  (OS/IO)    │ │ (Chip)   │ │ (ML)     │
         │             │ │          │ │          │
         │ nodes+edges │ │ nodes+   │ │ nodes+   │
         │ FAISS index │ │ edges    │ │ edges    │
         │ local model │ │ FAISS    │ │ FAISS    │
         └─────────────┘ └──────────┘ └──────────┘
                │             │             │
                └─────────────┼─────────────┘
                              │
                    ┌─────────▼───────────┐
                    │  Merge & Generate   │
                    │  (küçük yerel LLM)  │
                    └─────────────────────┘
```

### 8.3 Domain Sunucusu Protokolü

Her domain sunucusu aynı API'yi konuşur:

```
POST /query
{
  "question": "...",
  "question_embedding": [...],
  "top_k": 5,
  "hops": 2
}

Response:
{
  "domain": "bilgisayar mimarisi",
  "results": [
    {"node_id": "...", "content": "...", "score": 0.85, "paths": [...]}
  ]
}
```

### 8.4 Bu Neden Web Sitesi Değil, Ama Web Tabanlı

"Milyonlarca web sitesi" fikri şu forma dönüşür:
- Her domain bir **mikro-servis**
- Her mikro-servis bir **bilgi alanı**
- HTTP üzerinden iletişim (web protokolü)
- Ama "web sitesi" değil — **bilgi sunucusu**

Bu, Xanadu'nun transclusion vizyonuna çok yakın:
- Bilgi referansla çağrılır, kopyalanmaz
- Her bilgi parçasının sahibi bellidir
- Güncellemeler kaynağında yapılır, tüm referanslar güncellenir

---

## 9. v1.0 — Kişisel Bilgi İşletim Sistemi

Bu, uzun vadeli hedeftir. v0.8 tamamlandığında şu olur:

- Kişisel notlar, araştırmalar, öğrenme kayıtları → otomatik node'lar
- Soru sor → graf çıkarımı + dil üretimi → kaynaklı cevap
- Her kullanım sistemi güçlendirir
- Domain'ler bağımsız büyür ama gerektiğinde çapraz çıkarım yapar
- "Bu bilgi nereden geldi?" her zaman cevaplanabilir

---

## 10. YAPILMAYACAKLAR (Anti-Pattern Listesi)

> [!CAUTION]
> Aşağıdakiler projeyi öldürecek kararlardır:

| Yapma | Neden |
|---|---|
| Web arayüzü inşa etme (şimdi) | Motor olgunlaşmadan UI yapmak, boş bir binayı boyamak |
| Dağıtık sisteme geçme (şimdi) | 17 node'da çalışan bir şeyi dağıtmak anlamsız |
| Büyük LLM entegre etme | Goldorn'un tezi "büyük modele ihtiyaç yok" — büyük model eklemek teziyle çelişir |
| Cloud deploy etme (şimdi) | Yerel olgunlaşmadan cloud'a çıkmak, debug'u imkansızlaştırır |
| Genel amaçlı AI hedefleme | Goldorn dar-ve-derin olmalı, geniş-ve-sığ değil |
| Kendi embedding modelini eğitme | `paraphrase-multilingual-MiniLM` şimdilik yeterli |
| Framework/kütüphane savaşına girme | SQLite + NetworkX + numpy yeterli, Postgres/Neo4j gereksiz |

---

## 11. Hemen Şimdi Yapılacaklar — İlk Oturum Planı

### Öncelik 1: Credit Assignment (tahmini 1-2 saat)
1. `query()` fonksiyonunu `paths` döndürecek şekilde genişlet
2. `blame_edge()` fonksiyonunu yaz
3. `edge_history` tablosunu oluştur
4. Test: Yanlış sonuç → feedback → doğru edge cezalanıyor mu?

### Öncelik 2: Implicit Feedback (tahmini 1-2 saat)
1. `analyze_implicit_feedback()` fonksiyonunu yaz
2. Episode geçmişinden pattern çıkar
3. Otomatik weight güncelleme

### Öncelik 3: Çelişki Çözümleme (tahmini 30 dk)
1. `contradicts` edge'leri olan node çiftlerini bul
2. Her ikisi de aktifse, confidence + recency + feedback ile karar ver
3. Kaybedenin skorunu penalty'nin ötesinde bastır

### Öncelik 4: 3. Domain Ekleme — Test (tahmini 1 saat)
1. Yeni bir domain ekle (örn: "programlama dilleri" veya "makine öğrenmesi")
2. 5-8 node, 6-10 edge
3. Cross-domain izolasyonun 3 domain'de de çalıştığını doğrula
4. Bu, motorun sağlamlığının asıl testi

---

## 12. Başarı Metrikleri — Ne Zaman Bir Aşamayı "Tamamlandı" Sayacağız?

| Aşama | Metrik |
|---|---|
| v0.3 | 3 domain, 50+ node, credit assignment çalışıyor, implicit feedback var |
| v0.4 | Bir markdown dosyası otomatik olarak node'lara dönüşüyor |
| v0.5 | Sorulara ham node yerine cümle biçiminde yanıt üretiliyor |
| v0.6 | 1.000 node'da query < 200ms |
| v0.7 | `goldorn ask "..."` komutu terminal'den çalışıyor |
| v0.8 | 2 domain sunucusu HTTP üzerinden birleşik sorgu cevaplayabiliyor |
| v1.0 | Kişisel notlar sisteme aktarılmış, günlük kullanıma hazır |

---

## 13. Felsefi Pusula — Kaybolduğunda Buraya Dön

1. **Goldorn bir arama motoru değildir.** Bilgiyi *bulmuyor*, bilgi üzerinden *çıkarım yapıyor*.

2. **Goldorn bir LLM kopyası değildir.** Ağırlık matrislerinin yaptığını farklı bir formda yapmayı araştırıyor.

3. **"Y = f(X, Graph)"** formülü projenin omurgasıdır. Her karar bu formülü güçlendirmeli.

4. **Ted Nelson'ın dersi:** Büyük vizyon, küçük adımlarla inşa edilir. Xanadu 60 yıldır bitmedi çünkü her şeyi bir anda yapmaya çalıştı.

5. **Dağıtık mimari bir *sonuçtur*, başlangıç noktası değil.** Motor olgunlaşınca dağıtık mimari doğal olarak gelir.

6. **17 node'dan 17.000'e geçmek, kod değil *mimari* problemidir.** Kod yazmadan önce veri yapısını düşün.

7. **Xanadu'nun AI yorumu:** Bilgi kopyalanmaz, referans edilir. Her bilginin sahibi, tarihi ve güveni vardır. Bu, projenin DNA'sıdır.

---

*Belge oluşturma tarihi: 2026-06-24*  
*Referans: goldorn_progress_v1.md, dagitik_ogrenilmis_temsil_fikri.md, xanadu_benzeri_ai.txt, ogrenilebilir_acik_temsil_sistemi_spec_v0_1.md*  
*Kaynak kod analizi: knowledge_graph.py (259 satır), seed.py, add_chip_domain.py, add_v02_nodes.py, migrate_edges.py*

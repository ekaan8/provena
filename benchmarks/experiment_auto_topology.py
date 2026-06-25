"""
Provena Auto-Topology Deneyi
=============================
Araştırma sorusu: Provena kendi graph topolojisini veriyi okuyarak öğrenebilir mi?

Bu deney:
1. Sisteme 10 cümlelik bir paragraf verir (veritabanı sistemleri konusu)
2. Sistem node ve edge'leri İNSAN MÜDAHALESİ OLMADAN üretir
3. Üretilen topolojiyi analiz eder
4. Aynı domain'den 5 soru sorar
5. Mevcut domain'lerin bozulup bozulmadığını test eder
6. Sonuçları raporlar

Beklenen topoloji (insan olarak bildiğimiz):
  - İlişkisel DB ↔ NoSQL: contradicts / alternative_to
  - PostgreSQL → İlişkisel DB: example_of
  - MongoDB → NoSQL: example_of
  - ACID → İlişkisel DB: supports
  - İndeksleme: internal trade-off (artırır ama yavaşlatır)
  - Normalizasyon: internal trade-off (azaltır ama kayba neden olur)
  - MVCC → eşzamanlılık: uses
"""

from auto_topology import ingest
from knowledge_graph import ask, init_db

# ═══════════════════════════════════════════════════════════
# 1. TEST VERİSİ — Veritabanı Sistemleri (10 cümle)
# ═══════════════════════════════════════════════════════════

TEST_PARAGRAPH = """
İlişkisel veritabanları, verileri tablolar halinde organize eder ve SQL sorgu dili ile erişim sağlar.
NoSQL veritabanları ise şema esnekliği sunarak yapılandırılmamış verileri depolamak için tasarlanmıştır.
İlişkisel veritabanları ACID özelliklerini garanti ederek veri tutarlılığını sağlar.
NoSQL sistemleri ise CAP teoremine göre tutarlılık yerine erişilebilirliği tercih edebilir.
PostgreSQL, ilişkisel veritabanlarının en güçlü açık kaynak örneğidir.
MongoDB, belge tabanlı NoSQL veritabanlarının yaygın bir örneğidir ve JSON benzeri dökümanlar kullanır.
İndeksleme, veritabanı sorgularının performansını dramatik biçimde artırır ancak yazma işlemlerini yavaşlatabilir.
Dağıtık veritabanları, veriyi birden fazla sunucuya yayarak yatay ölçeklenebilirlik sağlar.
Veritabanı normalizasyonu, veri tekrarını azaltır ancak karmaşık sorgularda performans kaybına neden olabilir.
MVCC mekanizması, eşzamanlı okuma ve yazma işlemlerini kilitlemeden yönetmek için kullanılır.
"""

# ═══════════════════════════════════════════════════════════
# 2. TEST SORULARI — Beklenen cevaplarla birlikte
# ═══════════════════════════════════════════════════════════

TEST_QUERIES = [
    {
        "question": "NoSQL ve ilişkisel veritabanı arasındaki fark nedir?",
        "expected": "İlişkisel/NoSQL karşılaştırma node'ları (contradicts ilişkisi)",
    },
    {
        "question": "PostgreSQL ne tür bir veritabanıdır?",
        "expected": "PostgreSQL → ilişkisel DB (example_of ilişkisi)",
    },
    {
        "question": "Veritabanında veri tutarlılığı nasıl sağlanır?",
        "expected": "ACID ile ilgili node",
    },
    {
        "question": "Veritabanı performansını artırmak için ne yapılır?",
        "expected": "İndeksleme ile ilgili node",
    },
    {
        "question": "Eşzamanlı veritabanı erişiminde veri bütünlüğü nasıl korunur?",
        "expected": "MVCC ile ilgili node",
    },
]


# ═══════════════════════════════════════════════════════════
# 3. DENEYİ ÇALIŞTIR
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()

    print("=" * 70)
    print("  PROVENA AUTO-TOPOLOGY DENEYİ")
    print("  Araştırma sorusu: Sistem kendi graph topolojisini üretebilir mi?")
    print("=" * 70)

    # ── ADIM 1: Otomatik topoloji üretimi ──
    print("\n" + "=" * 70)
    print("  ADIM 1: Otomatik Node ve Edge Üretimi")
    print("  (İnsan müdahalesi yok — sistem kendi karar veriyor)")
    print("=" * 70)

    result = ingest(
        TEST_PARAGRAPH,
        source="Auto-Topology Deneyi — Veritabanı Sistemleri",
        domain_hint=None,   # Domain'i de sistem tahmin etsin
        confidence=0.75,
    )

    # ── Topoloji analizi ──
    stats = result["stats"]
    edges = result["edges"]

    print("\n📐 Topoloji Kalite Analizi:")
    print("─" * 50)

    # İlişki türü dağılımı
    relation_counts = {}
    for e in edges:
        r = e["relation"]
        relation_counts[r] = relation_counts.get(r, 0) + 1
    print("  İlişki türü dağılımı:")
    for rel, count in sorted(relation_counts.items(), key=lambda x: -x[1]):
        print(f"    {rel}: {count}")

    # Beklenen kritik edge'ler
    print("\n  Beklenen kritik ilişkiler:")
    critical_checks = [
        ("contradicts veya alternative_to", "ilişkisel ↔ NoSQL"),
        ("example_of", "PostgreSQL veya MongoDB → üst kategori"),
        ("supports veya causes", "ACID → veri tutarlılığı"),
        ("uses", "MVCC → eşzamanlılık yönetimi"),
    ]
    for expected_rel, description in critical_checks:
        found = any(
            e["relation"] in expected_rel.split(" veya ")
            for e in edges if not e.get("cross_domain")
        )
        status = "✅" if found else "❌"
        print(f"    {status} {description} ({expected_rel})")

    # ── ADIM 2: Test sorguları ──
    print("\n" + "=" * 70)
    print("  ADIM 2: Test Sorguları")
    print("  (Otomatik üretilen topoloji üzerinden sorgu)")
    print("=" * 70)

    for i, test in enumerate(TEST_QUERIES, 1):
        print(f"\n{'─' * 70}")
        print(f"  Test {i}/5 — Beklenti: {test['expected']}")
        ask(test["question"])

    # ── ADIM 3: Çapraz domain regresyon testi ──
    print("\n" + "=" * 70)
    print("  ADIM 3: Regresyon Testi")
    print("  (Mevcut domain'ler yeni domain'den etkilenmemeli)")
    print("=" * 70)

    print("\n  I/O domain testi:")
    ask("yüksek bağlantı sayısında I/O performansı")

    print("\n  Chip domain testi:")
    ask("ARM neden güç verimli?")

    # ── SONUÇ ──
    print("\n" + "=" * 70)
    print("  DENEY SONUCU — DEĞERLENDİRME KRİTERLERİ")
    print("=" * 70)
    print(f"""
  Kriter 1: Node çıkarımı
    Bulunan bilgi iddiaları: {stats['claims_extracted']}/{stats['sentences_found']}
    Hedef: %70+ cümle bilgi iddiası olarak tanınmalı (≥7/10)
    Sonuç: {'✅ BAŞARILI' if stats['claims_extracted'] >= 7 else '⚠️  DÜŞÜK'}

  Kriter 2: Edge çıkarımı
    Üretilen iç edge: {stats['internal_edges']}
    Hedef: En az 5 anlamlı iç edge
    Sonuç: {'✅ BAŞARILI' if stats['internal_edges'] >= 5 else '⚠️  DÜŞÜK'}

  Kriter 3: İlişki türü çeşitliliği
    Farklı ilişki türü sayısı: {len(relation_counts)}
    Hedef: En az 3 farklı ilişki türü
    Sonuç: {'✅ BAŞARILI' if len(relation_counts) >= 3 else '⚠️  DÜŞÜK'}

  Kriter 4: Sorgu doğruluğu
    Manuel değerlendirme gerektirir — yukarıdaki sonuçları incele.
    Hedef: 5 sorudan en az 3'ü doğru node'u döndürmeli.

  Kriter 5: Regresyon
    Mevcut domain'ler (I/O, chip) etkilenmemeli.
    Manuel değerlendirme gerektirir.

  ────────────────────────────────────────────
  Eğer 5 kriterden 4'ü geçerse:
    → Araştırma yönünde ilerlemeye devam. Provena kendi topolojisini öğrenebiliyor.

  Eğer 3 veya daha az geçerse:
    → Öğrenme mekanizması yeniden tasarlanmalı. Spesifik başarısızlık noktalarını analiz et.
""")

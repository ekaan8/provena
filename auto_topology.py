"""
Provena Auto-Topology Engine — Araştırma Modülü
================================================
Araştırma Sorusu: Provena kendi graph topolojisini veriyi okuyarak öğrenebilir mi?

Bu modül ham metinden, insan müdahalesi olmadan:
1. Bilgi düğümleri (node) çıkarır
2. Node'lar arası ilişki türünü tahmin eder
3. Edge ağırlıklarını belirler
4. Mevcut graf ile bağlantı kurar

Tüm kararlar dilsel ipuçları + embedding benzerliği ile yapılır.
Hiçbir dış LLM API kullanılmaz.
"""

import re
import json
import hashlib
import numpy as np
from collections import defaultdict
from knowledge_graph import (
    add_node, add_edge, _cosine, _get_all_nodes,
    USE_EMBEDDINGS, _model, DB_PATH, VALID_RELATIONS, init_db
)
import sqlite3


# ═══════════════════════════════════════════════════════════
# 1. DİLSEL İPUÇLARI — İlişki türü tahmini için
# ═══════════════════════════════════════════════════════════

RELATION_CUES = {
    "causes": [
        "because", "causes", "leads to", "results in", "therefore",
        "triggers", "creates", "produces", "consequently", "resulting in"
    ],
    "contradicts": [
        "however", "but", "although", "despite", "contrary to",
        "whereas", "unlike", "instead of", "contradicts", "conflicts with",
        "on the other hand", "rather than", "opposes"
    ],
    "supports": [
        "supports", "confirms", "furthermore", "moreover", "proves",
        "evidence", "validates", "justifies", "additionally", "also"
    ],
    "supersedes": [
        "replaces", "supersedes", "upgraded", "obsolete", "newer version of",
        "succeeds", "deprecated", "replaced by"
    ],
    "example_of": [
        "is an example", "such as", "instance of", "is a type of",
        "like", "exemplified by", "for example"
    ],
    "part_of": [
        "part of", "component of", "included in", "division of",
        "member of", "segment of", "constitutes"
    ],
    "depends_on": [
        "depends on", "requires", "prerequisite", "relies on",
        "conditional upon", "necessary for"
    ],
    "uses": [
        "uses", "using", "utilizes", "based on", "employs",
        "applies"
    ],
    "alternative_to": [
        "alternative", "option", "instead", "substitute for",
        "replacement for"
    ]
}


# ═══════════════════════════════════════════════════════════
# 2. CÜMLE İŞLEME
# ═══════════════════════════════════════════════════════════

def split_sentences(text):
    """Metni cümlelere böl."""
    # Nokta, noktalı virgül, ünlem ve soru işaretinden böl
    # Ama kısaltmalarda (Dr., vb.) bölme
    sentences = re.split(r'(?<=[.!?;])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def is_knowledge_claim(sentence):
    """Bu cümle bir bilgi iddiası mı? Heuristik filtre (Türkçe + English)."""
    s = sentence.lower()

    # Question sentence check (English)
    if s.rstrip('.').endswith('?') or s.startswith(('what ', 'how ', 'why ', 'who ', 'when ', 'where ')):
        return False

    # Question sentence check (Turkish)
    if s.rstrip('.').endswith('?') or s.startswith(('neden ', 'nasıl ', 'kim ', 'ne zaman ', 'nerede ', 'hangi ')):
        return False

    # Command sentence check (English)
    if s.startswith(('please ', 'do ', 'use ', 'note:', 'warning:', "don't ")):
        return False

    # Command sentence check (Turkish)
    if s.startswith(('lütfen ', 'dikkat:', 'uyarı:', 'not:')):
        return False

    # En az 5 kelime
    words = s.split()
    if len(words) < 5:
        return False

    # Kelimeleri noktalama temizleyerek normalleştir (Türkçe son kelimelerde "sağlar." gibi durumlar)
    clean_words = [w.rstrip('.,;:!?') for w in words]

    # --- English: Common verbs and verb suffixes ---
    common_verbs_en = {
        'is', 'are', 'has', 'have', 'was', 'were', 'can', 'will',
        'does', 'do', 'should', 'would', 'could', 'may', 'might'
    }
    verb_endings_en = ('s', 'ed', 'ing', 'ize', 'fy', 'tion', 'ment')

    has_verb_en = any(
        w in common_verbs_en or w.endswith(verb_endings_en)
        for w in clean_words
    )

    # --- Turkish: Yaygın fiil sonekleri ---
    # Türkçe fiil çekimi örnekleri: "sağlar", "kullanır", "tercih edebilir",
    # "örneğidir", "garanti eder", "oluşur"
    turkish_common_verbs = {
        'sağlar', 'sağlıyor', 'kullanır', 'kullanıyor', 'içerir', 'içeriyor',
        'oluşur', 'oluşuyor', 'sunar', 'sunuyor', 'verir', 'veriyor',
        'gösterir', 'gösteriyor', 'gerektirir', 'gerektiriyor', 'destekler',
        'destekliyor', 'artırır', 'artırıyor', 'azaltır', 'azaltıyor',
        'sağlamak', 'kullanmak', 'içermek', 'oluşturmak', 'sunmak'
    }
    # Türkçe fiil sonekleri (kelime sonlarına bakılır)
    turkish_verb_endings = (
        'abilir', 'ebilir', 'ıbilir', 'ubilir',  # yeterlilik kipi: "tercih edebilir"
        'sağlar', 'sağlıyor',                       # yaygın bildirme fiili
        'edir', 'ıdır', 'idir', 'udur', 'üdür',   # ek fiil: "örneğidir"
        'eder', 'ediyor', 'etmek',                  # etmek fiili
        'ındır', 'indir', 'undur', 'ündür',        # vurgu ek fiili
        'dır', 'dir', 'dur', 'dür',                # bildirme kipi: "veritabanıdır"
        'lıdır', 'lidir', 'ludur', 'lüdür',        # niteleme ek fiili
        'maktadır', 'mektedir',                     # geniş zaman resmi
    )

    has_verb_tr = any(w in turkish_common_verbs for w in clean_words) or \
                  any(w.endswith(turkish_verb_endings) for w in clean_words)

    return has_verb_en or has_verb_tr


def generate_node_id(content, prefix="auto"):
    """İçerikten benzersiz node ID üret (English)."""
    # Anlamlı kelimeleri çıkar
    words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

    stop_words = {
        'the', 'is', 'are', 'and', 'for', 'with', 'from', 'that',
        'this', 'has', 'have', 'been', 'was', 'were', 'not', 'but',
        'about', 'in', 'on', 'at', 'to', 'of', 'a', 'an'
    }
    meaningful = [w for w in words if w not in stop_words][:4]

    if meaningful:
        slug = "_".join(meaningful)
    else:
        slug = hashlib.md5(content.encode()).hexdigest()[:10]

    return f"{prefix}_{slug}"


def check_contradiction(content_new, content_exist):
    """Yeni bilgi ile veritabanındaki bilgi arasında çelişki olup olmadığını denetler (Validation Gate)."""
    n = content_new.lower()
    e = content_exist.lower()
    
    # Kelimeleri ayıkla
    words_n = set(re.findall(r'\b\w+\b', n))
    words_e = set(re.findall(r'\b\w+\b', e))
    
    # Kelime çakışması oranını hesapla (overlap)
    shared = words_n & words_e
    all_words = words_n | words_e
    overlap = len(shared) / len(all_words) if all_words else 0
    
    # Eğer benzer konulardan bahsediyorlarsa (overlap > 0.35)
    if overlap > 0.35:
        # 1. Negasyon (olumsuzluk) farkı kontrolü
        negations = {"not", "no", "never", "cannot", "doesn't", "don't", "fails", "isn't", "aren't", "wasn't", "weren't"}
        has_neg_n = any(neg in words_n for neg in negations)
        has_neg_e = any(neg in words_e for neg in negations)
        
        if has_neg_n != has_neg_e:
            return True
            
        # 2. Zıt anlamlı kelime çiftleri kontrolü
        antonyms = [
            ("increase", "decrease"), ("fast", "slow"), ("efficient", "inefficient"),
            ("high", "low"), ("performance", "overhead"), ("contradict", "support"),
            ("valid", "invalid"), ("true", "false"), ("enable", "disable"),
            ("advantage", "disadvantage"), ("better", "worse")
        ]
        for a, b in antonyms:
            if (a in words_n and b in words_e) or (b in words_n and a in words_e):
                return True
                
    return False


# ═══════════════════════════════════════════════════════════
# 3. DOMAIN TAHMİNİ
# ═══════════════════════════════════════════════════════════

# Minimum similarity threshold for matching an existing domain.
# Eşiği 0.35'ten 0.45'e çıkardık — eski domain'lerin yeni konuları yanlış
# yakalaması bu sayede engelleniyor. Eşik altında kalan node'lar için
# _infer_domain_from_text() ile içerikten domain adı çıkarılıyor.
_DOMAIN_MATCH_THRESHOLD = 0.45


def _infer_domain_from_text(text):
    """İçerik metninden domain adı çıkar — anahtar kelime tabanlı.

    Yeni bir konu tespit edildiğinde (mevcut domain'lerle benzerlik düşükse)
    bu fonksiyon çağrılır ve içeriğe en uygun domain adını döndürür.
    """
    # Her domain için temsili anahtar kelimeler (Türkçe + İngilizce)
    domain_keywords = {
        'database': [
            'sql', 'nosql', 'mongodb', 'acid', 'index', 'query', 'transaction',
            'veritabanı', 'tablo', 'ilişkisel', 'normalizasyon', 'indeksleme',
            'postgresql', 'mysql', 'sqlite', 'schema', 'join', 'aggregation'
        ],
        'machine_learning': [
            'neural', 'gradient', 'model', 'training', 'overfitting', 'loss',
            'sinir', 'öğrenme', 'eğitim', 'regresyon', 'sınıflandırma',
            'embedding', 'transformer', 'attention', 'backpropagation', 'epoch'
        ],
        'networking': [
            'tcp', 'http', 'protocol', 'packet', 'latency', 'routing',
            'ağ', 'protokol', 'paket', 'gecikme', 'yönlendirme', 'bandwidth',
            'socket', 'dns', 'ip', 'firewall', 'proxy', 'cdn'
        ],
        'security': [
            'encryption', 'authentication', 'vulnerability', 'firewall', 'token',
            'şifreleme', 'kimlik', 'güvenlik', 'saldırı', 'açık', 'exploit',
            'ssl', 'tls', 'hash', 'salt', 'certificate', 'oauth'
        ],
        'distributed_systems': [
            'consensus', 'replication', 'partition', 'fault', 'eventual',
            'dağıtık', 'ölçek', 'shard', 'cluster', 'leader', 'raft', 'paxos',
            'cap', 'consistency', 'availability', 'microservice'
        ],
        'operating_systems': [
            'kernel', 'process', 'thread', 'syscall', 'memory', 'scheduler',
            'çekirdek', 'süreç', 'iş parçacığı', 'bellek', 'zamanlayıcı',
            'epoll', 'select', 'mutex', 'semaphore', 'deadlock', 'paging'
        ],
        'programming': [
            'function', 'class', 'object', 'interface', 'algorithm', 'complexity',
            'fonksiyon', 'sınıf', 'nesne', 'arayüz', 'algoritma', 'karmaşıklık',
            'recursion', 'iteration', 'pointer', 'garbage', 'compilation'
        ],
    }
    text_lower = text.lower()
    scores = {domain: 0 for domain in domain_keywords}
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return 'general'


def detect_domain(new_embedding, domain_hint=None, content_text=None):
    """
    Yeni node'un domain'ini tahmin et.

    Strateji:
    1. domain_hint verilmişse onu kullan (en güvenilir)
    2. Mevcut domain'lerin ortalama embedding'leriyle karşılaştır
    3. Benzerlik _DOMAIN_MATCH_THRESHOLD altındaysa:
       a. content_text varsa _infer_domain_from_text() ile anahtar kelimeden tahmin et
       b. Yoksa "general" domain'i ata

    Not: Eşik 0.35'ten 0.45'e çıkarıldı (2025-06-25 düzeltmesi).
    Eski eşik, mevcut domain'lerin yeni konuları yanlış yakalamasına yol açıyordu.
    """
    if domain_hint:
        return domain_hint

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT domain, embedding FROM nodes WHERE embedding IS NOT NULL"
    ).fetchall()
    conn.close()

    if not rows:
        # Hiç node yok — içerikten tahmin et veya "general" döndür
        return _infer_domain_from_text(content_text) if content_text else "general"

    # Domain başına embedding'leri topla
    domain_embeddings = defaultdict(list)
    for domain, emb_json in rows:
        if emb_json:
            domain_embeddings[domain].append(np.array(json.loads(emb_json)))

    if not domain_embeddings:
        return _infer_domain_from_text(content_text) if content_text else "general"

    best_domain = None
    best_sim = _DOMAIN_MATCH_THRESHOLD  # Minimum eşik (artırıldı: 0.35 → 0.45)

    for domain, embeddings in domain_embeddings.items():
        avg_emb = np.mean(embeddings, axis=0)
        sim = float(np.dot(new_embedding, avg_emb) /
                    (np.linalg.norm(new_embedding) * np.linalg.norm(avg_emb) + 1e-9))
        if sim > best_sim:
            best_sim = sim
            best_domain = domain

    if best_domain is None:
        # Eşik altında kaldı — içerikten domain adı çıkar
        return _infer_domain_from_text(content_text) if content_text else "general"

    return best_domain


# ═══════════════════════════════════════════════════════════
# 4. İLİŞKİ TAHMİNİ
# ═══════════════════════════════════════════════════════════

def infer_relation_type(sent_a, sent_b, similarity):
    """
    İki cümle arasındaki ilişki türünü tahmin et.

    Strateji:
    1. Dilsel ipuçlarına bak (en güvenilir)
    2. İpucu yoksa benzerlik skoruna göre karar ver
    """
    combined = (sent_a + " " + sent_b).lower()

    # Her relation type için cue sayısını hesapla
    cue_scores = defaultdict(float)
    for relation, cues in RELATION_CUES.items():
        for cue in cues:
            if cue in combined:
                cue_scores[relation] += 1.0

    # Özel pattern: "X ise Y" — Türkçe'de karşılaştırma/çelişki belirteci
    if re.search(r'\bise\b', combined):
        cue_scores["contradicts"] += 0.8

    # Özel pattern: "X örneğidir" veya "en güçlü/yaygın örneği"
    if re.search(r'(örneği\w*|tipik\s+örneği)', combined):
        cue_scores["example_of"] += 1.5

    # Özel pattern: "X ... ancak Y" veya "X artırır ancak Y yavaşlatır"
    if re.search(r'ancak|fakat', combined):
        # Aynı cümle içi çelişki mi, iki cümle arası mı?
        if 'ancak' in sent_a.lower() or 'fakat' in sent_a.lower():
            pass  # İç çelişki — bu cümle kendi başına bir trade-off anlatıyor
        else:
            cue_scores["contradicts"] += 0.5

    # En yüksek cue skoru olan relation'ı seç
    if cue_scores:
        best_relation = max(cue_scores, key=cue_scores.get)
        if cue_scores[best_relation] >= 0.5:
            return best_relation

    # Cue yoksa benzerlik skoruna göre
    if similarity > 0.80:
        return "related_to"
    elif similarity > 0.65:
        return "supports"
    else:
        return "related_to"


def calculate_edge_weight(similarity, has_linguistic_cue):
    """Edge ağırlığını benzerlik ve dilsel ipucu varlığına göre hesapla."""
    base_weight = similarity * 0.7
    cue_bonus = 0.15 if has_linguistic_cue else 0.0
    return min(0.90, max(0.30, base_weight + cue_bonus))


# ═══════════════════════════════════════════════════════════
# 5. ANA GİRİŞ NOKTASI — INGEST
# ═══════════════════════════════════════════════════════════

def ingest(text, source="auto-ingest", domain_hint=None, confidence=0.75):
    """
    Ham metinden otomatik graph topolojisi üret.

    İnsan müdahalesi gerektirmez. Tüm kararlar:
    - Heuristik filtreler (bilgi iddiası tespiti)
    - Embedding benzerliği (domain tahmini, edge ağırlığı)
    - Dilsel ipuçları (ilişki türü tahmini)
    ile yapılır.

    Args:
        text: İşlenecek ham metin
        source: Bilginin kaynağı
        domain_hint: Opsiyonel domain ipucu (None ise otomatik tahmin)
        confidence: Otomatik node'ların başlangıç güveni (< 1.0)

    Returns:
        dict: Üretilen node'lar, edge'ler ve istatistikler
    """
    if not USE_EMBEDDINGS:
        raise RuntimeError(
            "Auto-topology requires sentence-transformers. "
            "Install: pip install sentence-transformers"
        )

    init_db()

    # ── 1. Cümlelere böl ──
    sentences = split_sentences(text)
    print(f"\n📝 Metin {len(sentences)} cümleye bölündü.")

    # ── 2. Bilgi iddialarını filtrele ──
    claims = [(i, s) for i, s in enumerate(sentences) if is_knowledge_claim(s)]
    print(f"🔍 {len(claims)} bilgi iddiası tespit edildi.")

    if not claims:
        print("⚠️  Hiçbir bilgi iddiası bulunamadı.")
        return {"nodes": [], "edges": [], "stats": {}}

    # ── 3. Embedding'leri toplu hesapla ──
    claim_texts = [s for _, s in claims]
    embeddings = _model.encode(claim_texts)

    # ── 4. Node'ları oluştur ──
    created_nodes = []
    for (orig_idx, sentence), emb in zip(claims, embeddings):
        node_id = generate_node_id(sentence)

        # Duplicate kontrolü
        conn = sqlite3.connect(DB_PATH)
        existing = conn.execute("SELECT id FROM nodes WHERE id=?", (node_id,)).fetchone()
        conn.close()
        if existing:
            node_id = f"{node_id}_{orig_idx}"

        # Domain tahmini (content_text ile birlikte — yeni domain oluşturma mekanizması)
        domain = detect_domain(emb, domain_hint, content_text=sentence)

        # Çelişki kontrolü (Validation Gate)
        is_contradicted = False
        contradicting_node_id = None
        
        conn = sqlite3.connect(DB_PATH)
        existing_rows = conn.execute("SELECT id, content, confidence, embedding FROM nodes").fetchall()
        conn.close()
        
        node_confidence = confidence
        for ex_id, ex_content, ex_conf, ex_emb_json in existing_rows:
            if ex_emb_json:
                ex_emb = np.array(json.loads(ex_emb_json))
                sim = float(np.dot(emb, ex_emb) / (np.linalg.norm(emb) * np.linalg.norm(ex_emb) + 1e-9))
                if sim > 0.60:
                    if check_contradiction(sentence, ex_content):
                        is_contradicted = True
                        contradicting_node_id = ex_id
                        node_confidence = 0.40  # Güven skoru düşürülür
                        print(f"  ⚠️  Çelişki Tespit Edildi: '{sentence[:40]}...' ile '{ex_content[:40]}...' (ID: {ex_id}) çelişiyor.")
                        break

        # Node ekle
        add_node(node_id, sentence, source, node_confidence, domain)
        if is_contradicted and contradicting_node_id:
            add_edge(node_id, contradicting_node_id, "contradicts", weight=0.80)
            print(f"  ⚖️  Çelişki Kenarı Otomatik Oluşturuldu: {node_id} ↔ {contradicting_node_id}")

        created_nodes.append({
            "id": node_id,
            "content": sentence,
            "domain": domain,
            "embedding": emb,
            "original_index": orig_idx,
        })
        print(f"  ✓ node: {node_id} (güven: {node_confidence})")
        print(f"    domain: {domain}")
        print(f"    içerik: {sentence[:80]}...")

    # ── 5. Edge'leri çıkar ──
    created_edges = []

    # 5a. Yeni node'lar kendi aralarında
    n = len(created_nodes)
    print(f"\n🔗 {n} node arasında ilişki analizi...")

    for i in range(n):
        for j in range(i + 1, n):
            a = created_nodes[i]
            b = created_nodes[j]

            sim = float(np.dot(a["embedding"], b["embedding"]) /
                        (np.linalg.norm(a["embedding"]) * np.linalg.norm(b["embedding"]) + 1e-9))

            # Eşik: yeni node'lar arası daha düşük eşik — daha fazla bağlantı keşfet
            if sim < 0.40:
                continue

            # İlişki türünü tahmin et
            relation = infer_relation_type(a["content"], b["content"], sim)
            has_cue = relation not in ("related_to", "supports")
            weight = calculate_edge_weight(sim, has_cue)

            # Yönü belirle: metinde önce gelen → kaynak
            if a["original_index"] < b["original_index"]:
                from_id, to_id = a["id"], b["id"]
            else:
                from_id, to_id = b["id"], a["id"]

            conn = sqlite3.connect(DB_PATH)
            exists = conn.execute("SELECT 1 FROM edges WHERE (from_node=? AND to_node=?) OR (from_node=? AND to_node=?)", 
                                  (from_id, to_id, to_id, from_id)).fetchone()
            conn.close()
            if exists:
                continue

            try:
                add_edge(from_id, to_id, relation, weight)
                created_edges.append({
                    "from": from_id, "to": to_id,
                    "relation": relation, "weight": round(weight, 2),
                    "similarity": round(sim, 3),
                    "cross_domain": False,
                })
                print(f"  ✓ edge: {from_id} →[{relation}]→ {to_id}  "
                      f"(w:{weight:.2f}, sim:{sim:.3f})")
            except Exception as e:
                print(f"  ⚠ edge skip: {from_id} → {to_id}: {e}")

    # 5b. Yeni node'lar ↔ mevcut node'lar (çapraz bağlantı)
    existing_nodes = _get_all_nodes()
    new_ids = {n["id"] for n in created_nodes}
    cross_edges = 0

    print(f"\n🌐 Mevcut {len(existing_nodes)} node ile çapraz ilişki analizi...")

    for new_node in created_nodes:
        for ex_id, ex_content, ex_conf, ex_emb_json in existing_nodes:
            if not ex_emb_json or ex_id in new_ids:
                continue
            ex_emb = np.array(json.loads(ex_emb_json))
            sim = float(np.dot(new_node["embedding"], ex_emb) /
                        (np.linalg.norm(new_node["embedding"]) * np.linalg.norm(ex_emb) + 1e-9))

            # Mevcut node'larla daha yüksek eşik
            if sim < 0.55:
                continue

            relation = infer_relation_type(new_node["content"], ex_content, sim)
            has_cue = relation not in ("related_to", "supports")
            weight = calculate_edge_weight(sim, has_cue)

            conn = sqlite3.connect(DB_PATH)
            exists = conn.execute("SELECT 1 FROM edges WHERE (from_node=? AND to_node=?) OR (from_node=? AND to_node=?)", 
                                  (new_node["id"], ex_id, ex_id, new_node["id"])).fetchone()
            conn.close()
            if exists:
                continue

            try:
                add_edge(new_node["id"], ex_id, relation, weight)
                created_edges.append({
                    "from": new_node["id"], "to": ex_id,
                    "relation": relation, "weight": round(weight, 2),
                    "similarity": round(sim, 3),
                    "cross_domain": True,
                })
                cross_edges += 1
                print(f"  🔗 cross: {new_node['id']} →[{relation}]→ {ex_id}  "
                      f"(w:{weight:.2f}, sim:{sim:.3f})")
            except Exception:
                pass  # Duplicate edge — skip

    # ── 6. Rapor ──
    internal_edges = len(created_edges) - cross_edges
    stats = {
        "sentences_found": len(sentences),
        "claims_extracted": len(claims),
        "nodes_created": len(created_nodes),
        "internal_edges": internal_edges,
        "cross_edges": cross_edges,
        "total_edges": len(created_edges),
    }

    print(f"\n{'═' * 60}")
    print(f"📊 Otomatik Topoloji Raporu")
    print(f"{'═' * 60}")
    print(f"  Bulunan cümleler:     {stats['sentences_found']}")
    print(f"  Bilgi iddiaları:      {stats['claims_extracted']}")
    print(f"  Oluşturulan node'lar: {stats['nodes_created']}")
    print(f"  İç edge'ler:          {stats['internal_edges']}")
    print(f"  Çapraz edge'ler:      {stats['cross_edges']}")
    print(f"  Toplam edge:          {stats['total_edges']}")
    print(f"{'═' * 60}")

    return {
        "nodes": [{k: v for k, v in n.items() if k != "embedding"}
                  for n in created_nodes],
        "edges": created_edges,
        "stats": stats,
    }

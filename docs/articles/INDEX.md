# Provena Makale Serisi — Okuma Rehberi

Bu sayfa Provena araştırma serisinin 4 makalesini bir arada sunar.
Sırayla okunması tavsiye edilir; her makale bir sonraki için zemin hazırlar.

---

## Makale 1 — Yapay Zeka Neden Unutuyor?

**[→ İngilizce](article_01_why_ai_forgets.md)**

**Özet:**  
Büyük dil modelleri bilgiyi ağırlık matrislerinde sıkıştırıyor. Bu sıkıştırma hızlı
ve güçlü — ama opak, güncellenemeyen ve kaynaksız. `Y = f(X, W)` yerine
`Y = f(X, Graph)` formülasyonunu öneriyoruz: bilginin ağırlıklar yerine açık,
izlenebilir, güncellenebilir bir grafta tutulması.

**Hedef okuyucu:** Teknik olmayan meraklı okuyucu  
**Okuma süresi:** ~8 dakika

---

## Makale 2 — Cyc ve NELL Neden Başarısız Oldu?

**[→ İngilizce](article_02_cyc_nell_lessons.md)**

**Özet:**  
1984'te başlayan Cyc projesi 40 yıl boyunca 25 milyon kuralı elle kodladı ve
tamamlanamadı. NELL 8 yıl boyunca internetten bilgi çekti ve gürültü sorunundan
çöktü. Her ikisi de aynı hatayı yaptı: bilgiyi biriktirmek için bir mekanizma
kurdu ama zayıf bilgiyi ayıklamak için kurmadı. Provena'un mimari yanıtı nedir?

**Hedef okuyucu:** AI/CS geçmişi olan okuyucu  
**Okuma süresi:** ~12 dakika

---

## Makale 3 — Bilgi Grafiğinde Hebbian Öğrenme Çalışır mı?

**[→ İngilizce](article_03_hebbian_experiment.md)**

**Özet:**  
Üç deney, üç gerçek iddia. Graf aktivasyonu embedding'den her zaman iyi değil —
Databases domain'inde beklenmedik şekilde kötü sonuç verdi. Hebbian öğrenme
edge ağırlıklarını anlamlı biçimde değiştiriyor (ortalama |Δw|=0.39) ama tek
döngüde sıralamayı değiştirmiyor. `blame_edge` kontrollü koşullarda %100 doğru.
Beklenmedik sonuç dahil tüm sayılar burada.

**Hedef okuyucu:** Teknik okuyucu, ML/AI geçmişi  
**Okuma süresi:** ~18 dakika

---

## Makale 4 — Kara Kutu Olmayan Yapay Zeka

**[→ İngilizce](article_04_traceable_knowledge.md)**

**Özet:**  
"Bu sonuç neden döndü?" sorusu LLM'ler için gerçek bir yanıt almıyor. Provena'da
her sonucun kaynağı, her hatanın sorumlu edge'i, her çelişki kararının gerekçesi
kayıtlı. Açıklanabilirlik bir özellik değil mimari bir karar. GDPR'dan Xanadu'ya,
izlenebilir bilginin neden önemli olduğu ve gerçek maliyeti.

**Hedef okuyucu:** Kurumsal okuyucu + XAI ilgisi olan  
**Okuma süresi:** ~14 dakika

---

## GitHub

Tüm kaynak kod, benchmark scripti ve veri setleri açık kaynak:  
[github.com/ekaan8/provena](https://github.com)

Deneyler tekrarlanabilir:
```bash
git clone https://github.com/ekaan8/provena
cd provena
pip install -r requirements.txt
python benchmarks/benchmark_retrieval.py
```

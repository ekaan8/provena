# Öğrenilebilir Açık Temsil Zekâ Sistemi

## Specification Document v0.1

## 1. Amaç

Bu doküman, LLM modellerinde parametreler içine sıkıştırılan bilgi
temsilini alternatif bir mimariyle araştıran deneysel sistem tasarımını
tanımlar.

Ana soru:

> Bilgi; yalnızca ağırlık matrislerinde saklanmak yerine açık,
> izlenebilir, güncellenebilir ve öğrenebilir bir yapı içinde
> tutulabilir mi?

Amaç mevcut LLM'leri kopyalamak değildir. Amaç, bilgi temsilinin,
öğrenmenin ve çıkarımın farklı bir mimariyle incelenmesidir.

------------------------------------------------------------------------

# 2. Temel prensipler

## Açık temsil

Bilgi parçaları:

-   kimlik
-   içerik
-   kaynak
-   zaman
-   güven seviyesi
-   ilişkiler

ile tutulur.

## Öğrenebilirlik

Sistem yeni verilerle:

-   yeni düğüm ekler,
-   bağlantıları güçlendirir,
-   bağlantıları zayıflatır,
-   ilişkileri günceller.

## İzlenebilir çıkarım

Her cevap:

-   hangi bilgileri kullandığını,
-   hangi ilişkiler üzerinden ilerlediğini

gösterebilir.

------------------------------------------------------------------------

# 3. Mimari

    Input
     ↓
    Query Analysis
     ↓
    Semantic Retrieval
     ↓
    Knowledge Graph
     ↓
    Activation Engine
     ↓
    Reasoning Layer
     ↓
    Output

------------------------------------------------------------------------

# 4. Node tasarımı

Node temel bilgi birimidir.

Örnek alanlar:

``` json
{
"id": "",
"content": "",
"embedding": [],
"source": "",
"timestamp": "",
"confidence": 0.0,
"domain": ""
}
```

Alanlar:

-   id: benzersiz kimlik
-   content: bilgi içeriği
-   embedding: anlamsal temsil
-   source: kaynak
-   timestamp: zaman
-   confidence: güven seviyesi
-   domain: alan

------------------------------------------------------------------------

# 5. Edge tasarımı

Edge iki bilgi arasındaki ilişkidir.

``` json
{
"from": "",
"to": "",
"relation_type": "",
"weight": 0.0,
"last_active": ""
}
```

Örnek ilişki türleri:

-   supports
-   contradicts
-   causes
-   part_of
-   example_of
-   related_to

------------------------------------------------------------------------

# 6. Öğrenme kuralı

Sistemin ana problemi öğrenme mekanizmasıdır.

Basit model:

    new_weight =
    old_weight
    +
    feedback * activation * confidence
    -
    decay

Amaç:

Kullanılan ve doğrulanan ilişkilerin güçlenmesi, kullanılmayan veya
hatalı ilişkilerin zayıflamasıdır.

------------------------------------------------------------------------

# 7. Aktivasyon

Sistem bütün grafı aynı anda çalıştırmaz.

Sorguya göre ilgili alt yapı aktive edilir.

Örnek:

    Apple Silicon
     |
    ARM
     |
    Energy Efficiency
     |
    Architecture

------------------------------------------------------------------------

# 8. Geri bildirim

Öğrenme sinyalleri:

-   kullanıcı onayı
-   görev başarısı
-   tekrar kullanım
-   hata bildirimi

ile üretilebilir.

------------------------------------------------------------------------

# 9. Zaman ve hafıza

Bilgi statik değildir.

Sistem:

-   eski ilişkileri zayıflatabilir,
-   yeni ilişkileri güçlendirebilir,
-   bilgi geçmişini saklayabilir.

------------------------------------------------------------------------

# 10. İlk teknoloji yığını

-   Python
-   NetworkX
-   SQLite
-   Sentence Transformers
-   Opsiyonel küçük lokal dil modeli

------------------------------------------------------------------------

# 11. İlk prototip hedefi

Veri:

20-30 kaliteli bilgi parçası.

Kaynak:

-   kişisel notlar
-   teknik araştırmalar
-   öğrenme kayıtları

Test:

-   doğru bilgi bulunuyor mu?
-   doğru ilişkiler aktifleşiyor mu?
-   sistem zaman içinde gelişiyor mu?

------------------------------------------------------------------------

# 12. Başarı kriteri

İlk prototip:

-   yeni bilgi ekleyebilmeli
-   bağlantıları güncelleyebilmeli
-   çıkarım yapabilmeli
-   kullandığı kaynakları gösterebilmeli

------------------------------------------------------------------------

# 13. Kapsam dışı

İlk hedef değildir:

-   GPT alternatifi yapmak
-   genel yapay zekâ yapmak
-   insan beynini birebir taklit etmek

------------------------------------------------------------------------

# 14. Ana araştırma sorusu

> Parametrelerde sıkıştırılmış bilgi yerine açık, ilişkisel ve
> öğrenebilir bir yapı kullanarak daha şeffaf ve sürekli gelişen yapay
> zekâ sistemleri oluşturabilir miyiz?

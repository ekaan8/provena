from knowledge_graph import init_db, add_node, add_edge

init_db()

nodes = [
    ("io_multiplexing_select",
     "select() sistem çağrısı, dosya tanımlayıcı setlerini doğrusal olarak (O(N)) taradığı için yüksek bağlantı sayılarında performans kaybı yaşar.",
     "Unix Network Programming Notları", 1.0, "işletim sistemleri"),

    ("io_multiplexing_epoll",
     "epoll_wait() sistem çağrısı, yalnızca olay gerçekleşen dosya tanımlayıcılarını döndürerek O(1) zaman karmaşıklığı ile ölçeklenebilirlik sağlar.",
     "Linux Man Sayfaları", 1.0, "işletim sistemleri"),

    ("concurrent_stock_sim",
     "Tek iş parçacıklı ve select() tabanlı bir eşzamanlı borsa simülatörü, aktif bağlantı sayısı kısıtlı senaryolarda düşük bellek ayak iziyle kararlı çalışır.",
     "Eşzamanlı Sistem Tasarımları", 0.95, "yazılım mimarisi"),

    ("c11_stdatomic_usage",
     "C11 standart kütüphanesindeki stdatomic.h, veri yarışlarını (data race) engellemek için kilit gerektirmeyen (lock-free) atomik operasyonlar sağlar.",
     "C11 Dil Standartları Dokümantasyonu", 1.0, "paralel programlama"),

    ("mutex_lock_overhead",
     "Yoğun thread rekabetinin olduğu sistemlerde geleneksel mutex kilitleri, context switch maliyeti nedeniyle kilit gerektirmeyen (lock-free) yapılara göre performansı düşürür.",
     "Modern İşletim Sistemleri", 0.9, "işletim sistemleri"),
]

edges = [
    ("io_multiplexing_epoll", "io_multiplexing_select", "supersedes", 0.85),
    ("io_multiplexing_select", "concurrent_stock_sim",  "part_of",    0.90),
    ("c11_stdatomic_usage",   "mutex_lock_overhead",    "supports",   0.80),
]

for args in nodes:
    add_node(*args)
    print(f"✓ node: {args[0]}")

for args in edges:
    add_edge(*args)
    print(f"✓ edge: {args[0]} → {args[1]}")

print("\nVeritabanı hazır.")

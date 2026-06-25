from knowledge_graph import add_node, add_edge

# ── NODES ──────────────────────────────────────────────────

add_node(
    "arm_risc_architecture",
    "ARM, Reduced Instruction Set Computing (RISC) mimarisini benimser; az sayıda basit komut seti ile yüksek saat hızı ve düşük güç tüketimi sağlar.",
    "Computer Architecture: A Quantitative Approach", 1.0, "bilgisayar mimarisi"
)

add_node(
    "x86_cisc_architecture",
    "x86, Complex Instruction Set Computing (CISC) mimarisini kullanır; donanım düzeyinde karmaşık komutlar içerir ve geriye dönük uyumluluk katmanları taşır.",
    "Intel 64 and IA-32 Architectures Software Developer Manual", 1.0, "bilgisayar mimarisi"
)

add_node(
    "apple_silicon_m1",
    "Apple M1, ARM tabanlı ilk Apple Silicon çipidir; 2020'de piyasaya çıkmış, unified memory mimarisi ile CPU ve GPU'nun aynı bellek havuzunu paylaşmasını sağlamıştır.",
    "Apple WWDC 2020 Keynote", 1.0, "bilgisayar mimarisi"
)

add_node(
    "unified_memory_architecture",
    "Unified Memory Architecture (UMA), CPU ve GPU'nun ayrı bellek yerine tek bir yüksek bant genişlikli havuzu paylaşmasıdır; veri kopyalama gecikmesini ortadan kaldırır.",
    "Apple Silicon Technical Overview", 0.95, "bilgisayar mimarisi"
)

add_node(
    "moores_law",
    "Moore Yasası, entegre devredeki transistör sayısının yaklaşık her iki yılda bir iki katına çıkacağını öngörür; Gordon Moore tarafından 1965'te gözlemlenmiştir.",
    "Gordon Moore, Electronics Magazine 1965", 1.0, "chip tarihi"
)

add_node(
    "moores_law_slowdown",
    "2010'ların ortasından itibaren transistör küçültmenin fiziksel limitlere (kuantum tünelleme, ısı yoğunluğu) yaklaşması nedeniyle Moore Yasası'nın sürekliliği tartışmalıdır.",
    "IEEE Spectrum - The End of Moore's Law", 0.95, "chip tarihi"
)

add_node(
    "arm_power_efficiency",
    "ARM mimarisi, daha az transistörle aynı hesaplama işini yapabildiğinden x86'ya kıyasla watt başına daha yüksek performans (performance-per-watt) sunar.",
    "Anandtech Apple M1 Review", 1.0, "bilgisayar mimarisi"
)

add_node(
    "apple_silicon_transition",
    "Apple, 2020-2022 arasında Mac ürün serisini Intel x86'dan kendi tasarımı ARM tabanlı Apple Silicon çiplerine geçirdi; geçiş Rosetta 2 çeviri katmanıyla desteklendi.",
    "Apple Silicon Transition Guide", 1.0, "chip tarihi"
)

add_node(
    "chiplet_design",
    "Chiplet mimarisi, tek bir monolitik çip yerine birden fazla küçük çip parçasını (chiplet) bir arada paketler; AMD ve Intel bu yaklaşımı Moore Yasası yavaşlamasına karşı kullanmaktadır.",
    "IEEE Hot Chips 2022", 0.90, "bilgisayar mimarisi"
)

add_node(
    "tsmc_3nm_process",
    "TSMC'nin 3nm üretim süreci, Apple M3 serisi ve diğer modern çipler için kullanılmaktadır; daha küçük transistörler daha düşük güç tüketimi ve daha yüksek yoğunluk sağlar.",
    "TSMC Technology Symposium 2023", 0.90, "chip tarihi"
)

# ── EDGES ─────────────────────────────────────────────────

add_edge("arm_risc_architecture",   "x86_cisc_architecture",    "contradicts",    0.75)
add_edge("arm_risc_architecture",   "arm_power_efficiency",     "causes",         0.90)
add_edge("apple_silicon_m1",        "arm_risc_architecture",    "example_of",     0.95)
add_edge("apple_silicon_m1",        "unified_memory_architecture","example_of",   0.90)
add_edge("apple_silicon_transition","x86_cisc_architecture",    "supersedes",     0.80)
add_edge("apple_silicon_transition","apple_silicon_m1",         "part_of",        0.85)
add_edge("moores_law_slowdown",     "moores_law",               "contradicts",    0.85)
add_edge("moores_law_slowdown",     "chiplet_design",           "causes",         0.75)
add_edge("moores_law_slowdown",     "arm_power_efficiency",     "supports",       0.70)
add_edge("tsmc_3nm_process",        "apple_silicon_m1",         "supports",       0.80)
add_edge("chiplet_design",          "moores_law",               "alternative_to", 0.70)

print("Chip domain node ve edge'leri eklendi.")
print("Toplam yeni: 10 node, 11 edge")

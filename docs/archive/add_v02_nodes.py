from knowledge_graph import add_node, add_edge

add_node(
    "select_low_conn_advantage",
    "select() düşük bağlantı sayısında (<100 FD) basitliği ve taşınabilirliği nedeniyle epoll'e göre tercih edilebilir.",
    "Unix Network Programming", 0.85, "işletim sistemleri"
)

add_node(
    "epoll_linux_only",
    "epoll Linux çekirdeğine özgüdür; BSD, macOS veya Windows sistemlerde kullanılamaz, taşınabilir kod için alternatif gerekir.",
    "POSIX Standartları", 0.95, "işletim sistemleri"
)

# select'in avantajlı olduğu bağlam
add_edge("select_low_conn_advantage", "io_multiplexing_select", "supports",      0.75)
add_edge("select_low_conn_advantage", "io_multiplexing_epoll",  "contradicts",   0.60)

# epoll'ün sınırı
add_edge("epoll_linux_only",          "io_multiplexing_epoll",  "valid_when",    0.80)
add_edge("select_low_conn_advantage", "epoll_linux_only",       "alternative_to",0.65)

print("v0.2 node ve edge'ler eklendi.")
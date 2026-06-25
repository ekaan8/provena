import sqlite3
from datetime import date

conn = sqlite3.connect("knowledge.db")

# Yanlış edge'i sil
conn.execute("""
    DELETE FROM edges 
    WHERE from_node='io_multiplexing_select' 
    AND to_node='concurrent_stock_sim'
""")

# Doğru edge: stock_sim, select'i KULLANIYOR
conn.execute("""
    INSERT OR REPLACE INTO edges 
    (from_node, to_node, relation, weight, last_active)
    VALUES (?,?,?,?,?)
""", ("concurrent_stock_sim", "io_multiplexing_select", "uses", 0.70, date.today().isoformat()))

conn.commit()
conn.close()
print("Migration tamamlandı.")

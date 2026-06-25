import os
import sys
import argparse
import auto_topology

def extract_txt(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def extract_pdf(file_path):
    try:
        import pypdf
    except ImportError:
        print("\n❌ PDF dosyalarını okuyabilmek için 'pypdf' kütüphanesi yüklü olmalıdır.")
        print("Lütfen şu komutla yükleyin ve tekrar deneyin:")
        print("  ./venv/bin/pip install pypdf")
        sys.exit(1)
        
    reader = pypdf.PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)

def process_file(file_path, domain_hint, confidence):
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    
    print(f"\nProcessing file: {filename}...")
    
    if ext == ".txt":
        text = extract_txt(file_path)
    elif ext == ".pdf":
        text = extract_pdf(file_path)
    else:
        print(f"⚠️  Desteklenmeyen dosya formatı (sadece .txt ve .pdf): {filename}")
        return
        
    if not text.strip():
        print(f"⚠️  Dosya içeriği boş veya metin çıkarılamadı: {filename}")
        return
        
    result = auto_topology.ingest(
        text=text,
        source=filename,
        domain_hint=domain_hint,
        confidence=confidence
    )
    
    stats = result.get("stats", {})
    if stats:
        print(f"  ✓ Ingestion Completed: {stats.get('nodes_created', 0)} nodes and {stats.get('total_edges', 0)} edges created.")

def main():
    parser = argparse.ArgumentParser(description="Provena Veri Giriş (Ingest) Aracı")
    parser.add_argument("path", help="TXT/PDF dosyasının yolu veya bu dosyaları içeren klasörün yolu")
    parser.add_argument("--domain", default=None, help="Verinin ait olduğu domain (varsayılan: otomatik tahmin)")
    parser.add_argument("--confidence", type=float, default=0.75, help="Oluşturulan düğümlerin güven skoru (0.0-1.0)")
    
    args = parser.parse_args()
    
    target_path = args.path
    if not os.path.exists(target_path):
        print(f"❌ Belirtilen yol bulunamadı: {target_path}")
        sys.exit(1)
        
    if os.path.isfile(target_path):
        process_file(target_path, args.domain, args.confidence)
    elif os.path.isdir(target_path):
        files = [os.path.join(target_path, f) for f in os.listdir(target_path) 
                 if os.path.isfile(os.path.join(target_path, f))]
        
        # Sadece PDF ve TXT dosyalarını bul
        valid_files = [f for f in files if os.path.splitext(f)[1].lower() in (".txt", ".pdf")]
        
        if not valid_files:
            print(f"⚠️  Klasörde işlenebilecek .txt veya .pdf dosyası bulunamadı: {target_path}")
            sys.exit(0)
            
        print(f"📂 Klasörde {len(valid_files)} adet dosya bulundu.")
        for f in valid_files:
            process_file(f, args.domain, args.confidence)
            
    print("\n🎉 Tüm veri girişi işlemleri tamamlandı!")

if __name__ == "__main__":
    main()

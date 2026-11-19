import docx

doc = docx.Document(r"c:\Users\tmoun\Downloads\IEEE FORMATE RESEARCH PAPER (1).docx")
print("Paragraphs count:", len(doc.paragraphs))
print("Tables count:", len(doc.tables))

with open("doc_structure.txt", "w", encoding="utf-8") as f:
    f.write(f"Paragraphs count: {len(doc.paragraphs)}\n")
    f.write(f"Tables count: {len(doc.tables)}\n\n")
    
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text:
            f.write(f"P{i} [style={p.style.name}]: {text}\n")
            
    f.write("\n" + "="*50 + "\nTABLES\n" + "="*50 + "\n")
    for ti, t in enumerate(doc.tables):
        f.write(f"\n=== TABLE {ti} ({len(t.rows)} rows, {len(t.columns)} cols) ===\n")
        for ri, r in enumerate(t.rows):
            cells = [c.text.strip().replace("\n", " ") for c in r.cells]
            f.write(f"  R{ri}: {cells}\n")

print("Saved doc_structure.txt")

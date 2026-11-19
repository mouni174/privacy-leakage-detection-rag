import zipfile
import xml.etree.ElementTree as ET
import os

def dump_docx_summary(path):
    print(f"\n=======================================================")
    print(f"FILE: {path}")
    print(f"=======================================================")
    if not os.path.exists(path):
        print("File does not exist.")
        return
    with zipfile.ZipFile(path) as z:
        tree = ET.fromstring(z.read('word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paras = []
        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
            if texts:
                paras.append(''.join(texts))
        print(f"Total paragraphs: {len(paras)}")
        for i, p in enumerate(paras[:40]):
            print(f"[{i}] {p}")
        print("...")
        for i, p in enumerate(paras[40:100]):
            if any(heading in p for heading in ["Abstract", "Introduction", "Related", "Method", "Evaluation", "Result", "Discussion", "Conclusion", "Table", "Figure"]):
                print(f"[{i+40}] {p[:120]}")

dump_docx_summary(r"c:\Users\tmoun\Downloads\IEEE FORMATE RESEARCH PAPER (1).docx")
dump_docx_summary(r"c:\Users\tmoun\Downloads\Privacy_RAG_IEEE_Paper_v2_Real_Results.docx")

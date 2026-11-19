import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

INPUT_PATH = r"c:\Users\tmoun\Downloads\IEEE FORMATE RESEARCH PAPER (1).docx"
OUTPUT_PATH = r"c:\Users\tmoun\Downloads\IEEE_FORMATE_RESEARCH_PAPER_Revised.docx"

doc = docx.Document(INPUT_PATH)

def set_cell_margins(cell, top=80, bottom=80, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def format_caption_p(p, text):
    p.text = text
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.bold = True

def format_body_p(p, text):
    p.text = text
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for r in p.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

def create_caption_p(text):
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), 'center')
    pPr.append(jc)
    p.append(pPr)
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    b = OxmlElement('w:b')
    rPr.append(b)
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '17') # 8.5 pt
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.text = text
    r.append(t)
    p.append(r)
    return p

# -------------------------------------------------------------------------
# 1. ABSTRACT (Paragraph 34)
# -------------------------------------------------------------------------
p34 = doc.paragraphs[34]
abstract_text = (
    "Abstract—Retrieval-Augmented Generation (RAG) systems improve large language model (LLM) responses "
    "by retrieving relevant passages from external document stores and supplying them as generation context. "
    "When these documents contain personally identifiable information (PII), forwarding retrieved passages "
    "without protection exposes sensitive values to the generation model. This paper presents a privacy-aware "
    "RAG pipeline that inserts a lightweight detection-and-redaction guardrail between retrieval and generation. "
    "PDF documents are parsed and chunked, embedded using Sentence-Transformers, and indexed in ChromaDB. "
    "At query time, the top-k retrieved chunks are inspected using regular expression rules for structured "
    "identifiers and a spaCy-based Named Entity Recognition (NER) model for less structured contextual entities. "
    "Detected sensitive spans are replaced with entity-type placeholders before the sanitized context is passed "
    "to a Google Gemini model. A Streamlit interface exposes retrieval, detection, redaction, and answer-generation "
    "stages for inspection. On a labeled synthetic evaluation corpus of five PDF documents across 20 queries, "
    "the combined guardrail identified all 111 structured PII instances (True Positives = 111, False Negatives = 0, "
    "Recall = 100.00%) with 241 additional contextual entity predictions, resulting in a measured precision of 31.53% "
    "and an F1-score of 47.95%. The pipeline eliminated structured PII leakage across the 111 evaluated instances "
    "(a 100.00% empirical leakage reduction on predefined structured categories) while introducing an average "
    "pre-generation guardrail processing overhead of 2.51% (221.47 ms) over baseline retrieval. Because heuristic "
    "detection cannot guarantee complete protection against unmodeled entities, the approach is presented as an "
    "operational leakage-reduction guardrail rather than an absolute privacy guarantee. Quantitative multi-evaluator "
    "answer-quality assessment and end-to-end latency inclusive of generation time are identified as future work."
)
format_body_p(p34, abstract_text)

# Keywords (P35)
p35 = doc.paragraphs[35]
format_body_p(p35, "Keywords—Retrieval-Augmented Generation, privacy leakage, personally identifiable information, Named Entity Recognition, PII redaction, privacy guardrail, vector database, large language models.")

# -------------------------------------------------------------------------
# 2. INTRO & LIT SURVEY POLISHING (P40, P49, P55, P57)
# -------------------------------------------------------------------------
p40 = doc.paragraphs[40]
format_body_p(p40, (
    "The main contributions are: (1) a lightweight privacy-aware RAG architecture inserting a detection-and-redaction "
    "guardrail between retrieval and generation; (2) a hybrid regex-and-NER mechanism targeting both structured identifiers "
    "and contextual entities; (3) an interactive prototype exposing each pipeline stage for auditability; and (4) an "
    "empirical evaluation measuring detection performance, structured leakage reduction, pre-generation latency overhead, "
    "and a qualitative assessment of generative utility trade-offs."
))

p49 = doc.paragraphs[49]
if p49.text.startswith("[7]Retrieval"):
    format_body_p(p49, p49.text.replace("[7]Retrieval", "[7] Retrieval"))

p55 = doc.paragraphs[55]
if p55.text.startswith("[13]The Digital"):
    format_body_p(p55, p55.text.replace("[13]The Digital", "[13] The Digital"))

p57 = doc.paragraphs[57]
if "AI pipelines" in p57.text and not p57.text.endswith("."):
    format_body_p(p57, p57.text + ".")

# -------------------------------------------------------------------------
# 3. FIGURE 2 CLEANUP (Remove empty paragraphs P82, P83, P84)
# -------------------------------------------------------------------------
doc.paragraphs[82].text = ""
doc.paragraphs[83].text = ""
doc.paragraphs[84].text = ""
p85 = doc.paragraphs[85]
p85.text = "Fig. 2. Streamlit User Interface of the Proposed Privacy-Aware RAG Prototype."
p85.alignment = WD_ALIGN_PARAGRAPH.CENTER
for r in p85.runs:
    r.font.name = "Times New Roman"
    r.font.size = Pt(8.5)
    r.font.italic = True

# -------------------------------------------------------------------------
# 4. SECTION VI-B: DETECTION PERFORMANCE (P93, P94, Table 1, P95, P97)
# -------------------------------------------------------------------------
p93 = doc.paragraphs[93]
format_body_p(p93, (
    "The PII detection performance was evaluated using precision, recall, and F1-score across 20 evaluation queries "
    "spanning five domain-specific documents. The evaluation considered the structured PII values present in the "
    "retrieved contexts as the ground-truth benchmark. A detected span was classified as a True Positive (TP) when "
    "it exactly matched an annotated ground-truth PII instance."
))

p94 = doc.paragraphs[94]
format_body_p(p94, (
    "Across the 20 queries, 111 structured PII instances were retrieved from the vector index. The proposed hybrid "
    "guardrail detected all 111 instances, resulting in 111 True Positives (TP = 111) and zero False Negatives (FN = 0), "
    "achieving a recall of 100.00%. Across the retrieved contexts, the detector produced 352 total predictions (TP + FP = 352), "
    "comprising 111 correct structured matches and 241 unmatched predictions (FP = 241). This yielded a measured precision "
    "of 31.53% and an F1-score of 47.95% (Table II).\n\n"
    "Crucially, the 241 unmatched predictions cannot be automatically characterized as genuine detector errors. The ground-truth "
    "benchmark was constructed exclusively for structured PII categories (emails, telephone numbers, PAN, Aadhaar, account numbers, "
    "IFSC codes, credit card numbers, and government IDs). Meanwhile, the hybrid guardrail intentionally activates a spaCy NER model "
    "to identify less structured contextual entities, including person names, organizations, locations, and monetary amounts. When "
    "evaluated strictly against the structured PII benchmark, every valid contextual entity detected by the NER component (such as "
    "employee names, customer names, institution designations, and salary figures) is tallied as an unmatched prediction in the "
    "precision denominator, artificially depressing the precision metric. While genuine NER misclassifications do occur (e.g., "
    "tagging abbreviations such as 'PAN' as organization entities), a large proportion of these 241 detections represent valid "
    "contextual entities that were legitimately redacted per privacy policy, but were absent from the structured-only test key."
))

# Repurpose P95 (originally trailing below Table 1) to be note below Table 1:
p95 = doc.paragraphs[95]
format_body_p(p95, (
    "*Note: The 241 unmatched predictions are largely contextual named entities (PERSON, ORG, LOC, MONEY) extracted by spaCy NER "
    "that were outside the structured-only ground-truth benchmark. Standalone numerical rows for isolated Regex-only and NER-only "
    "components are omitted because the single-target structured ground truth does not provide a dual-annotated baseline for evaluating "
    "isolated modules without severe benchmark asymmetry. The hybrid pipeline successfully pairs deterministic pattern recognition for "
    "structured identifiers with contextual entity extraction."
))

# Clean P97
p97 = doc.paragraphs[97]
p97.text = ""

# -------------------------------------------------------------------------
# 5. SECTION VI-C: LEAKAGE REDUCTION (P103, P105)
# -------------------------------------------------------------------------
p103 = doc.paragraphs[103]
format_body_p(p103, (
    "The proposed guardrail eliminated the forwarding of retrieved structured PII instances to the generation model. "
    "Compared with conventional RAG, which forwarded all 111 retrieved structured PII instances directly to the LLM context, "
    "the privacy-aware pipeline achieved an empirical leakage reduction of 100.00% on the evaluated test set (Table III). "
    "This 100.00% reduction strictly applies to the 111 predefined structured PII instances across the five synthetic PDF documents. "
    "As emphasized in our threat model, this empirical result does not constitute an absolute or formal privacy guarantee against "
    "novel, unstructured, or adversarially obfuscated sensitive data."
))

# Clear trailing P105 below Table 2
doc.paragraphs[105].text = ""

# -------------------------------------------------------------------------
# 6. SECTION VI-D: ANSWER QUALITY (P107, P108, P109)
# -------------------------------------------------------------------------
# Update section heading
p106 = doc.paragraphs[106]
p106.text = "D. Qualitative Answer Comparison and Utility Analysis"
p106.runs[0].font.bold = True

p107 = doc.paragraphs[107]
format_body_p(p107, (
    "To evaluate whether context redaction impedes downstream answer generation, identical question prompts were issued to both "
    "conventional RAG and privacy-aware RAG across all 20 test queries. In conventional RAG, the generator produces answers directly "
    "from raw retrieved passages, frequently exposing private identifiers verbatim in the generated response. In privacy-aware RAG, "
    "sensitive spans are replaced with entity-type placeholders prior to generation. Formal quantitative answer-quality scoring using "
    "independent human evaluators and inter-annotator agreement metrics is designated as immediate future work. In this study, we "
    "conduct a qualitative analysis of generated answer pairs to investigate the utility-privacy trade-off, as summarized in Table IV."
))

p108 = doc.paragraphs[108]
format_body_p(p108, (
    "As illustrated in Table IV, the privacy guardrail successfully suppresses confidential identifiers (such as employee emails, "
    "phone numbers, PAN numbers, and synthetic bank accounts) while allowing the LLM to provide informative responses for procedural "
    "and descriptive queries. However, for questions explicitly querying named individuals (e.g., employee positions), redacting the "
    "subject's name to [PERSON REDACTED] breaks the relational link between query and context, causing the model to output a fallback "
    "response ('I couldn't find that information in the provided documents'). This qualitative finding demonstrates the fundamental "
    "operational trade-off between strict entity masking and query specificity."
))

# Clear trailing P109 below Table 3
doc.paragraphs[109].text = ""

# -------------------------------------------------------------------------
# 7. SECTION VI-E: LATENCY ANALYSIS (P111, P113, P116)
# -------------------------------------------------------------------------
p111 = doc.paragraphs[111]
format_body_p(p111, (
    "Execution latency was evaluated to measure the computational overhead imposed by the privacy guardrail prior to generation. "
    "The latency measurements capture the pre-generation retrieval and guardrail pipeline, specifically dense semantic retrieval, "
    "regular-expression scanning, spaCy NER inference, and text redaction. The measurements intentionally exclude cloud API inference "
    "latency from Google Gemini. Latency overhead is defined as:"
))

# Clear trailing P113 below Table 4
doc.paragraphs[113].text = ""

p116 = doc.paragraphs[116]
format_body_p(p116, (
    "Across the 20 evaluation queries, baseline semantic retrieval averaged 8818.39 ms, while the combined retrieval-plus-guardrail "
    "pipeline averaged 9039.86 ms (Table V). The privacy guardrail introduced an average processing overhead of 221.47 ms, corresponding "
    "to a 2.51% increase over baseline retrieval. Because end-to-end cloud LLM generation typically incurs several seconds depending on "
    "network bandwidth and token length, the 221.47 ms guardrail latency constitutes an even smaller fraction of total user-perceived query time."
))

# -------------------------------------------------------------------------
# 8. SECTION VI-F: ERROR ANALYSIS (P118, P121)
# -------------------------------------------------------------------------
p118 = doc.paragraphs[118]
p118.text = "F. Error Analysis and Limitations"
p118.runs[0].font.bold = True

p121 = doc.paragraphs[121]
format_body_p(p121, (
    "These observations indicate that while regular expressions and NER provide effective detection for predictable and named entities, "
    "they do not provide exhaustive detection across all sensitive semantics. Representative error cases and practical mitigations "
    "are summarized in Table VI."
))

# -------------------------------------------------------------------------
# 9. SECTION VII: RESULTS AND DISCUSSION (P126 - P131)
# -------------------------------------------------------------------------
p126 = doc.paragraphs[126]
format_body_p(p126, (
    "The experimental evaluation demonstrates that the proposed privacy-aware RAG framework reduces the exposure of sensitive "
    "information while preserving the core retrieval-augmented workflow. Across five synthetic domain documents and 20 evaluation queries, "
    "111 structured PII instances were retrieved from the vector store."
))

p127 = doc.paragraphs[127]
format_body_p(p127, (
    "The proposed Regex-and-NER detector correctly identified all 111 structured PII instances (True Positives = 111, False Negatives = 0), "
    "achieving a recall of 100.00%. The system generated 352 total predictions, of which 111 matched the structured ground truth, "
    "resulting in a measured precision of 31.53% and an F1-score of 47.95%. As detailed in Section VI-B, the measured precision reflects "
    "the evaluation of a hybrid detector against a structured-only ground-truth key. The 241 unmatched predictions largely represent valid "
    "contextual entities extracted by the NER module rather than defective detections. Standardizing multi-domain benchmarks that annotate "
    "both structured identifiers and contextual entities is essential for refining precision measurements in future work."
))

p128 = doc.paragraphs[128]
format_body_p(p128, (
    "In the leakage reduction analysis, conventional RAG forwarded all 111 retrieved structured PII instances to the generator, "
    "whereas the proposed pipeline sanitized all 111 instances, achieving an empirical leakage reduction of 100.00% across the test corpus. "
    "This measurement is strictly restricted to the 111 predefined structured PII instances within the synthetic benchmark. Heuristic "
    "pattern matching and statistical NER cannot guarantee complete privacy protection across novel document formats or unstructured "
    "disclosures, highlighting the need to treat the pipeline as an operational leakage-reduction layer rather than a formal guarantee."
))

p129 = doc.paragraphs[129]
format_body_p(p129, (
    "The qualitative answer-quality evaluation confirmed that procedural and informational inquiries retain high utility following "
    "PII masking, but queries focused on redacted entity names suffer utility loss. Because human evaluator ratings must not be "
    "unsubstantiated, quantitative scoring on multi-point rubrics is designated as future work with formal inter-annotator agreement."
))

p130 = doc.paragraphs[130]
format_body_p(p130, (
    "The latency evaluation demonstrated that baseline retrieval required an average of 8818.39 ms, while the retrieval-plus-guardrail "
    "pipeline required 9039.86 ms, representing a modest pre-generation overhead of 2.51% (221.47 ms). These measurements reflect local "
    "pre-generation processing and intentionally exclude cloud LLM generation time, which further reduces the proportional overhead in practice."
))

p131 = doc.paragraphs[131]
format_body_p(p131, (
    "In summary, the hybrid architecture provides an effective, lightweight privacy guardrail that can be integrated into existing RAG "
    "deployments without model retraining. Future work includes expanding evaluation to larger heterogenous corpora, implementing "
    "context-preserving surrogate replacement, and conducting rigorous multi-annotator answer-quality evaluations."
))

# -------------------------------------------------------------------------
# 10. REBUILD TABLES & INSERT IEEE CAPTIONS ABOVE EACH TABLE
# -------------------------------------------------------------------------
# Tables in original:
# Table 0: Sensitive categories (12 rows, 3 cols)
# Table 1: Detection performance (4 rows, 4 cols)
# Table 2: Privacy leakage reduction (6 rows, 3 cols)
# Table 3: Answer Quality (4 rows, 3 cols) -> REPLACE with Qualitative Table
# Table 4: Latency Analysis (3 rows, 2 cols)
# Table 5: Error Analysis (6 rows, 4 cols)

# Table 0: Add Caption above
t0 = doc.tables[0]
t0._tbl.addprevious(create_caption_p("TABLE I. SENSITIVE ENTITY CATEGORIES AND REDACTION PLACEHOLDERS"))
t0.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t0.rows):
    for cell in row.cells:
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

# Table 1: Rebuild Table 1 with verified numbers & insert Caption above
t1 = doc.tables[1]
t1._tbl.addprevious(create_caption_p("TABLE II. PII DETECTION PERFORMANCE ON STRUCTURED BENCHMARK"))

table1_data = [
    ["Detection Configuration", "Ground Truth", "TP", "FP*", "FN", "Precision (%)", "Recall (%)", "F1-Score (%)"],
    ["Hybrid Guardrail (Regex + NER)", "111", "111", "241", "0", "31.53", "100.00", "47.95"]
]

# Clear old rows from t1 and re-populate
# Remove rows except first
while len(t1.rows) > 1:
    t1._tbl.remove(t1.rows[-1]._tr)

# Adjust columns if needed
parent = t1._tbl.getparent()
idx = parent.index(t1._tbl)
parent.remove(t1._tbl)

new_t1 = doc.add_table(rows=len(table1_data), cols=len(table1_data[0]))
new_t1.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(table1_data):
    for c_idx, val in enumerate(row):
        cell = new_t1.cell(r_idx, c_idx)
        cell.text = val
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

parent.insert(idx, new_t1._tbl)

# Table 2: Add Caption above
t2 = doc.tables[2]
t2._tbl.addprevious(create_caption_p("TABLE III. PRIVACY LEAKAGE REDUCTION ON RETRIEVED STRUCTURED PII"))
t2.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t2.rows):
    for c_idx, cell in enumerate(row.cells):
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

# Table 3: Replace old fabricated ratings with authentic Qualitative Comparison Table & Add Caption above
t3 = doc.tables[3]
t3._tbl.addprevious(create_caption_p("TABLE IV. QUALITATIVE COMPARISON OF GENERATED ANSWERS UNDER PRIVACY REDACTION"))

table3_data = [
    ["Query / Scenario", "Conventional RAG Output (Raw Context)", "Privacy-Aware RAG Output (Sanitized Context)", "Observed Effect on Privacy & Utility"],
    [
        "Employee Contact (Query 2)",
        "The contact information listed for the employee is: Email: riya.mehta@northstar-demo.example, Office phone: 9123456701.",
        "The employee's contact information includes the email [EMAIL REDACTED] and the office phone [PHONE REDACTED].",
        "Successful Redaction with High Utility: Identifiers are neutralized while communicative intent is fully preserved."
    ],
    [
        "Salary & Payroll Profile (Query 4)",
        "Recorded payroll: Annual compensation Rs. 720,000, PAN: QWERTY1234R, Aadhaar: 4821 7354 6192, Bank: 581234567890, IFSC: NSTD0001234.",
        "Recorded payroll: Annual compensation Rs. 720,000, PAN [PAN REDACTED], Aadhaar [AADHAAR REDACTED], bank account [BANK_ACCOUNT REDACTED], IFSC [IFSC REDACTED].",
        "Critical Financial Protection: Highly sensitive national identifiers and banking records are completely shielded."
    ],
    [
        "Entity-Targeted Inquiry (Query 1)",
        "Riya Mehta holds the position of Associate Software Engineer.",
        "I couldn't find that information in the provided documents.",
        "Utility Trade-off: Masking the subject name prevents entity resolution, demonstrating utility impact under aggressive redaction."
    ]
]

parent = t3._tbl.getparent()
idx = parent.index(t3._tbl)
parent.remove(t3._tbl)

new_t3 = doc.add_table(rows=len(table3_data), cols=len(table3_data[0]))
new_t3.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(table3_data):
    for c_idx, val in enumerate(row):
        cell = new_t3.cell(r_idx, c_idx)
        cell.text = val
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.0)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

parent.insert(idx, new_t3._tbl)

# Table 4: Add Caption above
t4 = doc.tables[4]
t4._tbl.addprevious(create_caption_p("TABLE V. PRE-GENERATION RETRIEVAL AND GUARDRAIL LATENCY"))
t4.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t4.rows):
    for c_idx, cell in enumerate(row.cells):
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

# Table 5: Add Caption above
t5 = doc.tables[5]
t5._tbl.addprevious(create_caption_p("TABLE VI. ERROR ANALYSIS AND LIMITATIONS OF HYBRID DETECTION"))
t5.alignment = WD_TABLE_ALIGNMENT.CENTER
for r_idx, row in enumerate(t5.rows):
    for c_idx, cell in enumerate(row.cells):
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in cell.paragraphs[0].runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            if r_idx == 0:
                run.font.bold = True
        set_cell_margins(cell, 80, 80, 100, 100)

# Save revised document
doc.save(OUTPUT_PATH)
print(f"Successfully generated revised DOCX at: {OUTPUT_PATH}")

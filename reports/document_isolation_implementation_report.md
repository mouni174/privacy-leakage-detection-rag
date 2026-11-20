# Document Isolation and Safe Deletion Implementation Report

**Date:** 19 November 2026
**Scope:** UUID-based document identity, Chroma document isolation, deletion, session tracking, and regression coverage.

## Files inspected

- `src/vector_store.py`, `src/retriever.py`, `src/loader.py`, `src/session_init.py`
- `pages/1_Document_Management.py`, `pages/2_RAG_Query.py`, `pages/3_Privacy_Dashboard.py`, `pages/4_Privacy_Audit.py`
- `tests/test_privacy_evaluation.py` and its fixture files
- `evaluate.py`, `evaluate_ablation.py`, `evaluate_answer_quality.py`, and `scripts/evaluate_phase5.py`
- Search results for `source_doc`, vector store callers, session document state, processed uploads, retrieval, and Chroma collection operations
- Local LangChain Chroma method signatures and Streamlit session-state guidance

The installed Streamlit skill documentation was read from the project environment. Its discovery script could not use the configured Python 3.12 interpreter because that interpreter path is no longer available.

## Files modified

- `src/loader.py`
- `src/vector_store.py`
- `src/retriever.py`
- `src/session_init.py`
- `src/document_registry.py` (new)
- `src/document_ingest.py` (new)
- `pages/1_Document_Management.py`
- `pages/2_RAG_Query.py`
- `tests/test_privacy_evaluation.py`
- `evaluate.py`, `evaluate_ablation.py`, `evaluate_answer_quality.py` (preserve their previous one-document-at-a-time reset behavior after changing the vector-store default)

No files in `chroma_db/` were read or modified by the implementation or test attempts. No evaluation result files were changed.

## Problems discovered

1. The app previously used `source_doc`/filename as its only document identifier. Two different PDFs with the same filename were indistinguishable to retrieval and registry state.
2. The first document upload called `create_vector_store(..., reset=True)`, which removed the collection and therefore risked deleting vectors unrelated to the current upload.
3. The query page used filename filtering for selected-document retrieval. “All Documents” used no metadata filter, so orphaned or old records in the persistent collection could be returned.
4. The registry was session-scoped while Chroma is persistent, allowing registry and vector state to diverge.
5. There was no document-scoped vector deletion workflow.
6. Legacy records without a `document_id` cannot be safely identified when filenames collide. Deletion or UUID-level isolation cannot be reconstructed from `source_doc` alone.
7. Removing upload tracking immediately on deletion could let the still-selected uploader file re-index itself during Streamlit's rerun.

## Changes implemented

### Document ID design

- The upload page creates a UUID4 for each distinct PDF upload.
- `load_and_split_pdf(..., document_id=...)` places `document_id` on every chunk while preserving `source_doc` for display and backward-compatible filtering. Direct loader callers that omit the argument receive a UUID4 as well.
- The session registry is keyed by document ID. Each new entry stores `document_id`, `original_filename`, `chunks_count`, `status`, `sanitized_bytes`, and the upload content fingerprint.
- `src/document_registry.py` computes SHA-256 content fingerprints and returns each not-yet-processed upload once. This prevents Streamlit reruns and duplicate copies of the same bytes from repeatedly indexing them. Two different PDFs sharing a filename receive separate IDs.
- Chroma chunk IDs use the stable form `<document_id>:<chunk-index>`.
- PDF ingestion requires a non-empty ID, and vector insertion verifies that Chroma stored exactly the deterministic chunk IDs before it commits the registry record.

### ChromaDB operations

- `add_documents_to_vector_store()` appends chunks and rejects an already-present document ID. It never resets the collection.
- `create_vector_store()` now defaults to `reset=False`; explicit `reset=True` remains available for the research scripts, which now pass it explicitly to preserve their former behavior.
- `document_id_exists()` checks exact metadata matches.
- `delete_document_from_vector_store()` first checks matching chunk IDs, deletes with `where={"document_id": ...}`, verifies that no matching chunks remain, and returns the count found before deletion. Unknown IDs and an empty collection are safe no-ops. It never drops the collection.
- If a Chroma add raises after beginning, `add_documents_to_vector_store()` attempts rollback using the same document-ID metadata filter. `VectorStoreWriteError` retains any rollback error so the upload page can report a possible orphan. The page also attempts a scoped rollback if an error occurs after a successful vector write.
- Sanitization now occurs before indexing. Empty extraction results are rejected, and temporary PDF files are still removed in a `finally` block.

### Retrieval isolation

- `get_relevant_context()` accepts `document_id` for one-document retrieval and `document_ids` for the registry’s current set of documents. Multiple IDs use Chroma’s `$in` metadata filter.
- The prior `doc_filter` filename argument remains available for compatibility with older callers.
- The query page revalidates the selected scope against the current registry before retrieval.
- The query page passes UUIDs for selected documents and the list of registered UUIDs for “All Documents.” An empty UUID list returns no context instead of running an unscoped search.
- The existing distance cutoff and duplicate filtering are unchanged.
- Registry entries without stable IDs are excluded from the query options, with an explanatory warning to re-upload them. This avoids using a filename as an isolation boundary in the new UI.

### Document Management UI and session state

- Each UUID-backed registry entry shows its sanitized filename, shortened document ID, chunk count, status, and sanitized PDF download.
- Deletion requires an explicit confirmation checkbox followed by the document’s Delete button.
- The registry entry and upload fingerprint are removed only after Chroma deletion succeeds. The database-ready flag, selected scope, and latest result are updated when applicable.
- A `seen_uploads` tombstone suppresses the same still-selected bytes after deletion; it is cleared when those bytes leave the uploader, allowing a later deliberate re-upload.
- Legacy records remain visible, but safe deletion is unavailable for them because their Chroma chunks have no document ID.
- Session state now includes `processed_uploads` and `selected_document_id`; `processed_files` remains for compatibility and stores UUIDs for new entries.

### Tests added

Thirteen tests were added to `tests/test_privacy_evaluation.py` (34 test methods are present in the file after the focused review):

- Same-filename/different-content upload tracking and rerun duplicate suppression.
- Deleted upload remains suppressed until removed from uploader selection.
- Consistent caller-supplied and generated document IDs on all loader chunks.
- Upload pipeline propagation of IDs and registry metadata.
- Parse and sanitization failures before indexing, including temporary-file cleanup.
- Selected-document isolation for identical filenames and retrieval across an explicit ID set.
- Empty and invalid scope filters do not fall back to unscoped retrieval.
- Deleting one document while retaining another document’s chunks.
- Removing one matching document from registry and processed-upload state.
- Unknown-ID and empty-collection deletion behavior.
- Duplicate document-ID rejection.
- Rollback scoped to one document ID when a Chroma add or post-write verification fails, including reporting rollback failure.

The existing PII, redaction, blocking, generation, PDF, and retrieval tests were retained.

## Test and validation results

| Check | Result |
|---|---|
| `python -m unittest tests.test_privacy_evaluation -v` | **Could not run.** Available Python 3.14 failed during test import because `langchain_core` is not installed in that interpreter. No test methods executed. |
| `venv312\Scripts\python.exe -m unittest tests.test_privacy_evaluation -v` | **Could not start.** The virtual environment refers to a Python 3.12 executable that is unavailable at its configured path. |
| `venv312\Scripts\python.exe -m pip check` | **Could not start** for the same missing interpreter. |
| `python -m pip check` | Exited successfully with “No broken requirements found” under system Python 3.14. This checks that interpreter's installed packages, not the project's intended Python 3.12 environment. |
| Upload deletion/rerun helper smoke check | Passed for the fingerprint/tombstone helpers: selected bytes stayed suppressed after deletion, then became eligible after removal from the uploader. |
| AST parse of modified Python files | Passed. This verifies syntax parsing only; it does not execute imports or tests. |
| `git diff --check` | Passed with no whitespace errors. Git emitted line-ending normalization warnings for `src/session_init.py` and `src/vector_store.py`. |
| Live Gemini integration | Not run. |
| Real `chroma_db` operations | Not run. |

## Remaining limitations

- Existing Chroma records without `document_id` cannot be reliably mapped to UUIDs. They are not included in the new app’s UUID-scoped retrieval and cannot be safely deleted by the new UI. Re-upload is required to create isolated replacements. Existing records are not automatically migrated or deleted.
- `source_doc` filename filtering remains for legacy callers; callers that rely on it do not get collision-proof isolation.
- The collection is local persistent storage and is not encrypted by this change.
- The registry and processed-upload map remain session state. A server restart or new session does not reconstruct them from Chroma, and cross-session document management remains incomplete.
- Upload content fingerprints are held only in session state; they are not a persistent document catalog.
- A rollback failure is reported, but no transactional guarantee can be made if Chroma itself fails during deletion.
- The test suite remains unexecuted until a working Python 3.12 environment with the project dependencies is available.

## Manual verification steps

1. Activate or repair the project’s Python 3.12 environment and install the project dependencies.
2. Run the automated suite:

   ```powershell
   python -m unittest tests.test_privacy_evaluation -v
   python -m pip check
   ```

3. Start the UI:

   ```powershell
   streamlit run app.py
   ```

4. Upload two different PDFs with the same filename. Confirm both appear with distinct document IDs and that their chunks are not mixed when querying each selected document.
5. Select **All Documents** and verify retrieval is limited to documents listed in the current session registry.
6. Re-trigger a Streamlit rerun with the same upload selected. Confirm the chunk count does not increase.
7. Confirm a document’s delete checkbox, delete it, then verify that only its chunks and registry row disappear and that the other same-name document remains queryable.
8. Try deletion without checking the confirmation box and confirm no Chroma or registry change occurs.
9. Verify the sanitized PDF download still works and rerun the existing privacy guardrail tests after restoring a working environment.

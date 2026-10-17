# Assisted Resume Import

Authenticated users can submit PDF or DOCX (up to 5 MB) for server-side text extraction and on-screen review.

- LinkedIn profile exported as PDF is supported only if the file contains extractable text; the app does **not** access LinkedIn or scrape profiles.
- DOCX is parsed with mammoth; PDFs use pdf-parse. This phase extracts text only, without AI rewriting or field classification.
- No file storage or database writes occur on import. Users manually transfer reviewed text to resume fields.
- Signed-in-only server action; PDF/DOCX signatures and extension checked, size cap 5 MB, output capped at 60k characters.
- Limitations: PDF scans without text need a separate OCR workflow; multi-column layouts may lose ordering.
- Before production deployment, perform a dedicated security review of document parsers, dependency updates, runtime resource quotas and content retention controls.

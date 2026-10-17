# Resume Studio — secure ATS export

- Authorized users can download their own resume as accessible plain text or minimalist ATS HTML.
- The HTML can be opened locally and printed as PDF via the browser's Print → Save as PDF function.
- An approved tailored resume version can be downloaded as TXT; draft versions cannot be downloaded through its route.
- All export endpoints require a validated authenticated session and explicitly constrain each query to the current user's ID.
- Private/no-store cache headers, restricted HTML content security policy and output escaping are enabled.
- These are **not** native PDF/DOCX generators, upload parsers, LinkedIn imports or AI rewriting tools. No automated applications or email sends.
- Downloaded files are user-sensitive and must be handled privately.

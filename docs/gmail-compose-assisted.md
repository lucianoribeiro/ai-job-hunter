# Gmail assisted compose — no OAuth, attachment or send

This step supports a user-approved recruiter message with a verified recipient supplied by the applicant.

Flow: save opportunity → prepare recruiter email → approve content → open Gmail compose screen → manually attach CV → user manually sends.

- The compose URL carries the recipient, subject and message in its query string; opening it may expose that content to browser history, extensions and link processing. Do **not** put secrets, IDs, personal passwords, or unnecessary sensitive data in the message. A proper API-based Gmail draft flow will avoid this limitation.
- Gmail may choose a default account other than the applicant's; check sender account before sending.
- A human-approved resume version is downloadable as TXT. PDF or DOCX attachment must be created/selected by the user.
- A compose URL is **not** a saved Gmail draft. There is no Gmail OAuth, attachment or email sending in this implementation.
- Every compose page is protected by Supabase auth, user ownership and approved status.

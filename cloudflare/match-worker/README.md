# Cloudflare Workers AI · AI Job Hunter

The `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` GitHub Secrets are used **only to deploy** the Worker through GitHub Actions. The deployed Worker uses a Cloudflare Workers AI binding (`AI`), so no bearer token is exposed in the browser.

Run workflow **Deploy Cloudflare AI Match Worker** to deploy. The API token must have permission to deploy Workers, in addition to Workers AI permissions.

After deployment, copy the worker `https://...workers.dev` URL reported by Wrangler into the repository **Actions variable** named `AI_MATCH_API_URL` (not a secret). The GitHub Pages workflow injects that URL into the public HTML, but not any private credentials. Trigger **Publish AI Job Hunter Premium** again.

Only click "Analyze with Cloudflare AI" after explicitly consenting to transmission of your extracted CV and vacancy requirements to Cloudflare. The Worker does not persist resumes. Requests are restricted by origin, size and per-IP rate limiting; CORS is not authentication. Review Cloudflare usage and billing limits before enabling access for other people.

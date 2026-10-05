# opthemis-site

Public marketing site for OpThemis — currently just the `get-started` lead-capture
landing page (`index.html`), kept deliberately separate from the main `opthemis`
product repo so it can deploy cleanly on its own, with no login gate and no
dependency on the product app's branch state.

## Structure

```
index.html                  Standalone landing page (no build step — plain HTML/CSS/JS)
staticwebapp.config.json    Azure Static Web Apps routing/headers config
api/
  function_app.py           One Azure Function: lead_capture
  requirements.txt
  host.json
  local.settings.json.example   Copy to local.settings.json for local dev (never commit the real one)
```

## Lead capture

The form on `index.html` POSTs to `/api/lead_capture`, which emails the
submission to Saria via SMTP and drops bot submissions via a honeypot field.
See the comment block at the top of that function in `api/function_app.py`
for the full input/output contract.

**Required Azure Function App Settings** (set in the Azure portal once the
Static Web App exists — none of these are committed):

- `SMTP_HOST`
- `SMTP_PORT` (defaults to 587)
- `SMTP_USERNAME`
- `SMTP_PASSWORD` — an app password / API key, not your main account password
- `NOTIFY_TO_EMAIL` — defaults to `saria.sfeir@opthemis.ch` if unset

Until these are set, the endpoint returns a 500 and the form tells the visitor
to email Saria directly instead.

## Deploying

Not yet wired up — needs a new Azure Static Web App resource (the old one is
being retired) and its deployment token added as a GitHub secret
(`AZURE_STATIC_WEB_APPS_API_TOKEN`), referenced from
`.github/workflows/azure-static-web-apps.yml`. Custom domain: `opthemis.ch`,
registered at Infomaniak, DNS currently delegated to Azure DNS for the apex
record (required for Azure Static Web Apps custom apex domains).

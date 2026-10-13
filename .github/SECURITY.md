# Security Policy

## Supported versions

Only the latest commit on the `main` branch receives security fixes. If you are running an older version, please update.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

1. Go to the **Security** tab of the [BizLens repository](https://github.com/G10rga/BizLens/security).
2. Click **Report a vulnerability** to open a private advisory.
3. Include as much detail as possible:
   - Description of the vulnerability and potential impact
   - Steps to reproduce
   - Any proof-of-concept code (optional but helpful)

We will acknowledge your report within 7 days and aim to release a fix within 30 days for confirmed vulnerabilities. We will credit reporters in the release notes unless you prefer to remain anonymous.

## Scope

Items in scope:
- Authentication and JWT handling (`/api/auth`, `Flask-JWT-Extended` configuration)
- Business data isolation (one user must not be able to access another user's data)
- OCR file upload handling (path traversal, file-type validation)
- SQL injection or ORM misuse
- Secrets in environment variables leaking through API responses

Items out of scope:
- Issues in third-party dependencies that are not exploitable in the context of BizLens
- Theoretical vulnerabilities without a realistic attack scenario
- Social engineering or phishing attacks

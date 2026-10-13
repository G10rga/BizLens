# Privacy Policy

**Last updated: 2026-10-06**

This Privacy Policy describes how BizLens ("we", "us", or "our") collects, uses, stores, and protects information when you use the BizLens application ("the Service"). By using the Service you agree to the practices described here.

---

## 1. Information We Collect

### 1.1 Account information
When you register, we collect:
- Email address
- Password (stored as a cryptographic hash — never in plain text)
- Optional display name

### 1.2 Business profile
During onboarding and in Settings, you may provide:
- Business name, type, and city
- Cash on hand (baseline balance)
- Language preference

### 1.3 Sales data
Depending on which entry method you use:
- **POS**: product names, quantities, prices, payment method (cash/card), timestamp
- **Lens Mode**: uploaded receipt images, OCR-extracted text, parsed totals, payment method, timestamp. Images are stored locally on the server disk.
- **CSV import**: date and revenue rows from uploaded files, import audit metadata

All sales are normalized into daily revenue records used for forecasting.

### 1.4 Expenses and suppliers
- Fixed expense names, amounts, due days
- Supplier names, amounts, payment frequency, next due date

### 1.5 Usage and technical data
We may collect standard server logs including:
- IP address and request timestamps
- Browser / client type (User-Agent)
- HTTP status codes and endpoint paths

These logs are used to diagnose errors and maintain the Service. We do not build individual behavioral profiles from them.

---

## 2. How We Use Your Information

| Purpose | Data used |
|---------|-----------|
| Authenticate you and maintain your session | Email, hashed password, JWT tokens |
| Generate cash-flow forecasts and alerts | Sales history, expense schedule, cash on hand |
| Run OCR on receipt images | Uploaded images (processed locally by default) |
| Display the dashboard and alerts | All business and sales data |
| Improve and debug the Service | Server logs, error reports |
| Seed demo data | None — demo uses a fixed fictional dataset |

We do **not** use your data for advertising, and we do not sell or share your data with third parties except as described in Section 4.

---

## 3. Receipt Images (Lens Mode)

Receipt photos uploaded in Lens Mode are:
- Stored on the server's local disk under `instance/lens_uploads/`
- Processed by OCR to extract totals (locally by default using RapidOCR)
- Optionally sent to OpenAI Vision or OCR.space **only if** you or the server operator has configured those API keys
- Linked to the resulting sale record for audit purposes

**Important for self-hosted deployments:** If you run BizLens on your own server (Render ephemeral disk or Ubuntu VPS), images are stored on that server and are subject to its data-retention policies. On Render's free tier, images are lost on redeploy.

---

## 4. Data Sharing

We do not sell, rent, or trade your personal information. We may share data only in these limited circumstances:

- **Service providers**: Hosting infrastructure (e.g. Render) processes data as part of operating the Service. These providers have their own privacy commitments.
- **Optional third-party OCR**: If `OPENAI_API_KEY` or `OCR_SPACE_API_KEY` is configured, receipt images may be sent to those providers for text extraction. Review their privacy policies before enabling these keys.
- **Legal requirements**: We may disclose information if required by law, court order, or to protect the rights and safety of users or the public.

---

## 5. Data Retention

| Data type | Retention |
|-----------|-----------|
| Account and business profile | Until you delete your account |
| Sales records and daily revenue | Until you delete your account or explicitly clear history via CSV import |
| Receipt images | Until deleted from disk (automatic on Render redeploy; manual on VPS) |
| Server logs | Typically 30–90 days depending on hosting provider settings |
| Demo data | Reset on each server restart when `DEMO_SEED=true` |

---

## 6. Security

We take reasonable technical and organizational measures to protect your data, including:
- Passwords hashed with a strong algorithm (never stored in plain text)
- JWT tokens with expiration for session management
- HTTPS in production (enforced via Cloudflare or Render TLS)
- CORS restrictions limiting which origins can call the API

No method of transmission or storage is 100% secure. We cannot guarantee absolute security.

---

## 7. Your Rights

Depending on your location and applicable law, you may have the right to:
- **Access** the personal data we hold about you
- **Correct** inaccurate data
- **Delete** your account and associated data
- **Export** your sales data (downloadable via CSV export)
- **Withdraw consent** for optional features (e.g. cloud OCR keys)

To exercise these rights, open an issue in the [BizLens GitHub repository](https://github.com/G10rga/BizLens/issues) or contact the maintainers directly.

---

## 8. Children's Privacy

The Service is intended for business owners and is not directed at children under the age of 18. We do not knowingly collect personal information from children. If you believe a child has provided us with personal data, please contact us so we can delete it.

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. We will update the "Last updated" date at the top and, where practical, notify users via the application. Continued use of the Service after changes take effect constitutes acceptance of the updated policy.

---

## 10. Contact

For privacy-related questions or requests, open an issue in the [BizLens GitHub repository](https://github.com/G10rga/BizLens/issues) or reach out to the maintainers through the repository.

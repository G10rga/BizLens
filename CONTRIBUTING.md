# Contributing to BizLens

Thank you for your interest in BizLens! Contributions — bug reports, feature suggestions, translations, and code — are welcome.

---

## Before you start

- Read the [Wiki](docs/wiki-Home.md) to understand how the project works.
- Check the [open issues](https://github.com/G10rga/BizLens/issues) to avoid duplicating effort.
- For significant changes, open an issue first to discuss the approach before investing time in a pull request.

---

## Local development setup

Full instructions are in [Getting Started](docs/wiki-Getting-Started.md). The short version:

```bash
git clone https://github.com/G10rga/BizLens.git
cd BizLens
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd web && npm install && npm run build && cd ..
cp .env.example .env
cd backend && python run.py
```

For hot-reload development, run the Flask API and Vite dev server in separate terminals (see the Getting Started page).

---

## What to work on

### Good first issues

- Improving Georgian / English translations in `web/src/i18n/ka.js` and `en.js`
- Adding sample CSV files in `backend/sample_data/`
- Documentation improvements in `docs/`
- Bug fixes with a clear reproduction case

### Larger contributions

- New business types in `georgian_calendar.py` (with appropriate seasonality multipliers)
- Additional OCR engine integrations in `backend/app/services/ocr.py`
- Improved Prophet tuning or an alternative forecasting backend
- UI improvements to the dashboard, POS, or Lens screens

---

## Code style

### Python (backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/).
- Use descriptive variable names; avoid single-letter names except in very short loops.
- Keep service functions focused — one clear responsibility per function.
- Add a brief docstring to new public functions.
- Python **3.11** is the target version; do not use features only available in 3.12+.

### JavaScript / React (frontend)

- Functional components with hooks; no class components.
- Keep components reasonably small and composable.
- Use the existing `useLanguage` / i18n pattern for any user-visible strings — add entries to both `ka.js` and `en.js`.
- Use Chart.js for data visualizations to stay consistent with the existing dashboard.

### General

- Write clear commit messages (imperative, present tense: "Add Lens completeness indicator", not "Added…").
- One logical change per commit where possible.
- Do not commit `.env` files, credentials, or the `instance/` directory.

---

## Submitting a pull request

1. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/my-feature-name
   ```

2. Make your changes.

3. Test locally:
   - Start the Flask server and verify your changes work end-to-end.
   - For frontend changes, test in both Georgian and English.
   - For forecast changes, test with the demo account and with a CSV import.

4. Push your branch and open a pull request against `main`.

5. In the PR description:
   - Explain **what** the change does and **why**.
   - Link the related issue if one exists (`Closes #123`).
   - Include a screenshot or brief demo if the change is visual.

6. A maintainer will review the PR. Be prepared for feedback and revision requests.

---

## Translations

BizLens is primarily aimed at Georgian-speaking users. If you can improve the Georgian (`ka.js`) translations or add clarity to the English (`en.js`) ones, that is a high-value contribution. Please keep:
- Business terminology natural for a Georgian small-business owner.
- Alert messages concise — they appear in a compact UI element.
- Consistent tone across both language files.

---

## Reporting bugs

Open a [GitHub issue](https://github.com/G10rga/BizLens/issues) and include:
- A clear description of the problem.
- Steps to reproduce.
- Expected vs. actual behavior.
- Your environment (local / Render / Ubuntu, Python version, browser).
- Any relevant error messages or screenshots.

---

## Security issues

If you discover a security vulnerability, **please do not open a public issue**. Instead, contact the maintainers privately through GitHub (use the repository's Security tab or a direct message).

---

## Code of conduct

Be respectful and constructive. We welcome contributors of all experience levels. Harassment, discrimination, or hostile behavior will not be tolerated.

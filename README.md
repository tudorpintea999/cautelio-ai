# Clause — AI Contract Compliance

Highlights dangerous contract clauses in red, explains each in one sentence, and tells you what's negotiable. Freelancer mode flags anything that affects ownership of your work.

## How it works

1. Open any page with a contract (DocuSign, Google Docs, vendor agreements, etc.)
2. Click the Clause extension icon
3. Toggle Freelancer mode if needed
4. Press **Analyze Contract**
5. Dangerous clauses highlight red on the page — hover for explanations and negotiation tips

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your ANTHROPIC_API_KEY

uvicorn main:app --reload --port 8000
```

### 2. Extension

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension/` folder

The Clause icon appears in your toolbar.

---

## Risk levels

| Color | Meaning |
|-------|---------|
| Red | High risk — read this carefully |
| Amber | Medium risk — worth flagging |
| Teal | Low risk — noted but not alarming |

---

## Freelancer mode

Flags anything affecting ownership of work product: IP assignment, work-for-hire language, non-solicitation, portfolio rights. Essential before signing any client contract.

---

## Project structure

```
extension/        Chrome extension (Manifest V3, vanilla JS)
  content.js      Injects highlights and tooltips into the page
  popup.html/css/js  Extension popup UI
  background.js   Service worker, calls backend
  icons/          Run create_icons.py to generate icons

backend/
  main.py         FastAPI entry point
  services/
    analyze.py    Claude Sonnet — contract analysis
```

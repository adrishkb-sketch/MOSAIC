# MOSAIC | Universal Personal Browser Agent

> *"MOSAIC learns the web, not your identity."*

MOSAIC is a production-quality, privacy-preserving universal browser agent built for the browser-agent hackathon. It allows users to type natural-language requests into one single interface. MOSAIC breaks down the task, retrieves only relevant details from the user's private memory, controls a live browser session using **Webcmd**, prepares action plans, and waits for explicit human approval before completing consequential actions.

---

## Key Features

1. **Universal Conversational Agent**: Arbitrary natural-language queries (job searching, product comparing, hackathon registration) parsed dynamically rather than using hardcoded conditional trees.
2. **Private Scoped Memory**: Complete database isolation. The orchestrator determines task relevance and retrieves only the minimum required variables (e.g. skills for job search, shipping address for shopping), leaving the rest of the profile untouched.
3. **Data Usage Transparency Center ("My Memory")**: A dedicated screen listing every saved fact, its origin source (explicitly provided vs inferred), and an audit trail ("Why did MOSAIC use this?") explaining exactly where and when it was used.
4. **Webcmd Adaptive Browser Controller**: Integrated global browser automation. Utilizes stealth Chromium contexts to explore pages, execute Playwright scripts, and recover dynamically from website changes.
5. **Shared Web Knowledge**: Generic website layout configurations and reusable Webcmd commands are persisted globally to improve speed for all users. Private user data (emails, resumes, payment info) is sanitized out.
6. **Consequential Action Preview & Human-in-the-Loop**: Displays exactly what details will be sent and what actions will be clicked before executing forms.
7. **Strict Payment Safety Boundary**: The agent pauses automation and blocks whenever a checkout/payment page is reached, prompting the user: *"Manual payment required. Complete payment in the browser."* It does not request CVV, UPI PINs, bank passwords, or OTPs.

---

## Tech Stack

*   **Frontend**: Next.js 16 (App Router) with TypeScript, Tailwind CSS v4, and React hooks.
*   **Backend**: Python 3.13 with FastAPI, Pydantic v2 schemas, and SQLite database storage via SQLAlchemy.
*   **Browser Control**: Webcmd CLI (v0.7.2) using CloakBrowser stealth Chromium.
*   **Reasoning/AI**: Google Gemini API via the official `google-genai` Python SDK (runs `gemini-2.5-flash` or `gemini-2.5-pro`).

---

## Getting Started

### 1. Prerequisites
Ensure you have the following installed:
*   **Node.js**: v20+ (v25.2.1 installed)
*   **Python**: v3.11+ (v3.13.9 installed)
*   **Webcmd**: Installed globally and verified (`npm install -g @agentrhq/webcmd && webcmd doctor`)

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create `.env` from the template:
   ```bash
   cp .env.example .env
   ```
3. Configure your **`GEMINI_API_KEY`** in `.env` (obtain one from [Google AI Studio](https://aistudio.google.com/)).
4. Run the API server:
   ```bash
   .venv/bin/uvicorn app.main:app --reload
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Start the local development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

---

## Running Tests

To run the automated Python backend test suite (unit and integration tests checking memory isolation, tool routing, Webcmd lifecycle, and safety policies):
```bash
cd backend
.venv/bin/pytest tests/
```
*(All 18 tests are passing successfully.)*

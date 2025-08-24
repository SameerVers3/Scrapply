## 1. 🎯 Goals

* Provide a **minimalistic dashboard** to manage scraping jobs.
* Allow users to:

  * Create scraping requests
  * View and manage jobs (status, retry, delete)
  * Test and execute generated APIs
  * Control jobs via **chatbot interface**
* Keep UI clean, fast, and intuitive.

---

## 2. 👤 Target Users

* Developers, analysts, and builders who need quick **web → API conversion**.
* Users comfortable with APIs but prefer a **UI shortcut**.

---

## 3. 📐 Information Architecture

### Navigation

* **Sidebar** (icon-only):

  * Dashboard
  * Chatbot
  * Settings

### Views

1. **Dashboard**

   * Create Scraping Request (form)
   * Jobs List (cards)
   * Job actions: Test, Retry, Delete
   * Endpoint link (when ready)

2. **Chatbot Panel**

   * Conversational assistant to create/manage jobs

3. **Settings**

   * General preferences (placeholder, no auth)

---

## 4. 🧩 Core Flows

### 4.1 Create Scraping Request

* Form → `POST /api/v1/scraping/requests`
* Job immediately appears in the list (`pending`).
* Poll status until job becomes `ready`.

### 4.2 Manage Jobs

* Jobs list → `GET /api/v1/scraping/jobs`
* Job card shows: ID, URL, status, progress, actions.
* Retry/Delete mapped to API calls.

### 4.3 Test & Execute API

* Test endpoint → `POST /generated/{job_id}/test`
* Execute endpoint → `GET /generated/{job_id}`
* Results shown in modal/drawer.

### 4.4 Chatbot Commands

* Parse commands → map to API calls.
* Examples:

  * “Create scraper for [https://example.com”](https://example.com”) → new request
  * “List ready jobs” → filter jobs
  * “Delete job 123” → delete job

---

## 5. 🎨 Visual Design

### Layout

* **Sidebar:** left, icon-only navigation.
* **Main content:** form at top, job list below.
* **Chatbot:** right-hand panel, collapsible.

### Typography

* Sans-serif font, system default.
* Base size: 16px body, larger for headers.

---

## 6. 🧱 Components

1. **Sidebar Navigation** – icon buttons with tooltips.
2. **Scraping Request Form** – URL input + description + “Add” button.
3. **Job Card** – shows job details, progress, endpoint, and actions.
4. **Chatbot Panel** – messages list + input field.
5. **Result Modal** – JSON test results.

---

## 7. 📊 Job Status UI

| Status       | UI Treatment               |
| ------------ | -------------------------- |
| `pending`    | Text label + spinner       |
| `analyzing`  | Text label + progress bar  |
| `generating` | Text label + progress bar  |
| `testing`    | Text label + loader        |
| `ready`      | Text label + endpoint link |
| `failed`     | Text label + Retry button  |

---

## 8. 📁 Project Structure (Next.js 13+ with App Router)

```bash
nexus-frontend/
├── app/
│   ├── layout.tsx            # Root layout (sidebar + chatbot panel)
│   ├── page.tsx              # Dashboard (default view)
│   ├── chatbot/
│   │   └── page.tsx          # Chatbot standalone view
│   ├── settings/
│   │   └── page.tsx          # Settings page (basic)
│   └── api/                  # Next.js API routes (proxy helpers if needed)
│
├── components/
│   ├── Sidebar.tsx           # Navigation sidebar
│   ├── ScrapingForm.tsx      # URL + description form
│   ├── JobCard.tsx           # Job display card
│   ├── JobList.tsx           # Job list wrapper
│   ├── Chatbot.tsx           # Chat interface
│   ├── ResultModal.tsx       # JSON modal
│   └── ProgressBar.tsx       # Generic progress bar
│
├── lib/
│   ├── api.ts                # API helper functions (fetch jobs, create request, etc.)
│   └── chatbot.ts            # NL command → API mapping
│
├── styles/
│   └── globals.css           # TailwindCSS setup (minimal styling)
│
├── public/                   # Icons, assets if any
│
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

---

## 9. 🔌 API Integration Notes

* Use `fetch` (built-in in Next.js) or `SWR` for polling job status.
* No authentication needed → direct calls to backend.
* Chatbot uses a lightweight parser (regex/keywords → API calls).
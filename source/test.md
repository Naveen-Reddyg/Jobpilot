Act as a Senior Full-Stack Architect, AI Engineer, and Cybersecurity Expert. I want to build a web portal called "AgenticJobSync" that uses an autonomous AI Agent built on the open-source Strands Agents SDK to scrape LinkedIn, match jobs against a user's skills, and semi-automatically apply. 

Generate a complete production-grade blueprint, folder structure, database schema, and core implementation files using Next.js (App Router, TypeScript, Tailwind CSS), FastAPI (Python), and PostgreSQL.

### 1. CORE SYSTEM ARCHITECTURE & REQUIREMENTS

#### A. Multi-Step User Onboarding Flow (Frontend)
Create an interactive, multi-step onboarding wizard view:
- **Step 1: Profile & Target Skills:** A form to capture target job titles and an interactive multi-select tag input for "Target Skills" (e.g., Python, Docker, React).
- **Step 2: Resume Ingestion:** A clean drag-and-drop zone to upload a resume PDF.
- **Step 3: LinkedIn Authentication (Secure Session Injection):** Because LinkedIn has aggressive anti-bot protections, DO NOT ask for raw passwords. Create an educational UI explaining how users can export their session cookies/state via a browser extension (like EditThisCookie) and paste the JSON array into a secure textarea.

#### B. Database Schema (Prisma or SQL)
Define the relational schema containing:
- `Users` (Id, email, password_hash, created_at)
- `UserProfiles` (Target_job_titles, target_skills, resume_pdf_url, encrypted_linkedin_session)
- `ScrapedJobs` (Job_id, title, company, location, description, skill_match_score, status: 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED')
- `ApplicationLogs` (Id, job_id, applied_at, status: 'SUCCESS' | 'FAILED', error_message)

#### C. The Strands Agent & Automation Engine (FastAPI Backend)
Write a Python background script that initializes a `strands_agents.agent.Agent` loop with the following tools:
1. **Job Scraper Tool:** Uses Playwright to inject the user's `encrypted_linkedin_session` cookies, navigates to LinkedIn Job Search matching the user's criteria, and extracts job information.
2. **LLM Skill Evaluator Tool:** A prompt pattern where the agent compares the job description text against the user's `target_skills`. It must return a JSON response containing a `match_percentage` and a list of `missing_skills`.
3. **Execution Gate Tool:** An automated process that updates the `ScrapedJobs` table to `PENDING_REVIEW` if the skill match is greater than 80%. It must HALT and wait for user approval.
4. **Browser Submitter Tool:** Triggered only when the status changes to `APPROVED`. It handles clicking the "Easy Apply" flows via Playwright using the pre-authenticated session.

#### D. The Human-In-The-Loop Dashboard
Create a central UI dashboard displaying:
- High-level metric cards: Total Scraped, Highly Matched, and Automated Submissions.
- A "Review Queue" panel displaying the top skill-matched jobs. Show the match score badge (e.g., "94% Match") and prominent "Approve & Apply" (Green) and "Skip" (Red) buttons. Clicking Approve must trigger the backend application tool execution.

### 2. DELIVERY OUTPUT EXPECTED
1. **System Topology:** Briefly outline the file structure.
2. **Database Migrations:** Clean PostgreSQL definitions.
3. **Backend Engine:** Complete Python code showing the `strands_agents` implementation loop with custom `@tool` functions.
4. **Frontend Views:** Next.js React components using Tailwind CSS for the onboarding experience and the queue control panel.

Ensure all code handles credential storage with maximum security (AES-256 encryption at rest for the session strings). Write short, modular, and heavily commented code blocks.

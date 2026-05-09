# VIDEO SCRIPT — AI-Based Text Summarization Platform

**Format:** Technical walkthrough · Narrator voice-over · Screen recording  
**Runtime:** ~35–45 minutes  
**Audience:** Developers, technical recruiters, engineers

---

## [INTRO — 0:00–1:30]

**[Screen: Project landing page or GitHub repo homepage]**

> "Welcome. In this video, we're doing a full technical walkthrough of the AI-Based Text Summarization Platform — a production-grade, end-to-end web application built entirely from scratch.
>
> This is not a tutorial. This is an architectural deep-dive into how this system was designed, built, tested, and deployed.
>
> The platform allows users to register, log in, paste raw text or upload a PDF, and receive an AI-generated summary. Users can then chat with that summary conversationally, browse their history, extract keywords, and download the result as a formatted PDF.
>
> Under the hood, we have a FastAPI backend written in Python, a Next.js frontend in TypeScript, PostgreSQL as our database, and a dual-provider AI layer powered by OpenRouter and HuggingFace.
>
> Everything is containerized with Docker and deployed to Render and Vercel.
>
> Let's start with the codebase structure."

---

## [SECTION 1 — Monorepo Structure — 1:30–3:00]

**[Screen: VS Code Explorer showing root directory]**

> "The repository is a monorepo with clean separation at the top level.
>
> We have a `backend/` directory containing the entire FastAPI application, a `frontend/` directory with the Next.js app, a `docs/` folder with ten documentation files covering every aspect of the system, and a `render.yaml` at the root which is the Infrastructure-as-Code file for Render deployment.
>
> There is no cross-contamination between frontend and backend. They share nothing except the API contract defined in the documentation."

---

## [SECTION 2 — Backend Structure — 3:00–7:00]

**[Screen: Expanding `backend/` in VS Code]**

> "Inside `backend/`, the application source lives under `app/`. Let's walk through each subdirectory.
>
> `app/main.py` is the application factory. It creates the FastAPI instance, registers the CORS middleware, mounts all routers, and manages the database pool lifecycle via a FastAPI lifespan context manager. This is the entry point Uvicorn boots from.
>
> `app/core/` holds all cross-cutting concerns. `config.py` uses Pydantic Settings to load every environment variable from the `.env` file with full type validation. `security.py` implements bcrypt password hashing and JWT token creation and verification. `dependencies.py` contains FastAPI dependency functions — most importantly `get_current_user`, which every protected route depends on. `limiter.py` configures slowapi for rate limiting.
>
> `app/api/v1/` contains the route handlers. Each file maps directly to a URL prefix: `auth.py` for authentication, `summarize.py` for text and PDF summarization, `history.py` for querying past summaries, `chat.py` for conversational sessions, `users.py` for profile management, and `export.py` for PDF download.
>
> `app/services/` is the business logic layer. Nothing in the route handlers does computation — they delegate entirely to service classes. `summarizer.py` orchestrates the full summarization pipeline. `pdf_service.py` extracts text from uploaded PDFs using pdfplumber. `chat_service.py` manages conversational context and session persistence. `keyword_extractor.py` uses KeyBERT to identify the most semantically relevant keywords from a summary. `export_service.py` generates downloadable PDFs using reportlab.
>
> `app/ai/` is the AI client layer. `openai_client.py` wraps the OpenAI-compatible API — pointing to OpenRouter for free-tier model access. `huggingface_client.py` provides the fallback BART pipeline. `router.py` is the AI Router that transparently switches between providers. `prompts.py` holds all system and user prompt templates.
>
> `app/db/` contains the data layer. `session.py` manages the asyncpg connection pool. `models/` holds the SQLAlchemy ORM definitions for four tables. `repositories/` implements the Repository pattern — all SQL is isolated here, never leaking into services or routes.
>
> `app/schemas/` contains all Pydantic schemas — request bodies, response models, and error shapes.
>
> The `alembic/` directory contains the four migration files that build the database schema incrementally. The `docker/` directory holds the multi-stage Dockerfile and the `entrypoint.sh` startup script. The `tests/` directory contains both unit and integration test suites."

---

## [SECTION 3 — Frontend Structure — 7:00–9:30]

**[Screen: Expanding `frontend/src/` in VS Code]**

> "The frontend is a Next.js application using the App Router — the modern file-system-based routing introduced in Next.js 13.
>
> `src/app/` contains all pages. The route groups are organized with parentheses — `(auth)/` groups the login and register pages under a shared unauthenticated layout. `(dashboard)/` groups all authenticated pages: the summarize page, chat, history, and profile — under a layout that includes the sidebar, header, and footer.
>
> `src/app/api/` contains Next.js Route Handlers — these are server-side API routes running inside Next.js, not the FastAPI backend. They exist solely to handle the `httpOnly` refresh token cookie, which cannot be read by client-side JavaScript for security reasons. There are three: `set-cookie` stores the refresh token after login, `get-refresh-token` reads it for the token refresh flow, and `clear-cookie` removes it on logout.
>
> `src/components/` contains all UI components organized by feature. The `ui/` subdirectory holds primitive components from shadcn/ui — buttons, inputs, cards, dialogs, and so on. Feature components in `chat/`, `summarize/`, `history/`, and `layout/` compose those primitives into full UI sections.
>
> `src/lib/api/` is the API client layer. `client.ts` creates the Axios instance pointed at the backend URL. Each other file — `auth.ts`, `summarize.ts`, `chat.ts`, `history.ts`, `export.ts`, `users.ts` — wraps specific backend endpoints. The client includes an Axios response interceptor that automatically attempts a token refresh on any 401 response and retries the original request.
>
> `src/lib/store/` holds two Zustand stores — `auth-store.ts` manages the current user and access token in memory, and `summarize-store.ts` holds the current summarization result state."

---

## [SECTION 4 — The Documentation — 9:30–10:30]

**[Screen: `docs/` folder in VS Code Explorer]**

> "Before we go into the notebook, let's briefly cover the ten documentation files. These aren't afterthoughts — they were written as the architectural blueprint before and during implementation."

### Doc 01 — Environment Setup

> "The first document covers environment prerequisites — Python 3.10 or higher, Git, Docker Desktop, and the GitHub CLI. It walks through creating the virtual environment, installing dependencies, spinning up PostgreSQL and Adminer via Docker Compose, applying migrations with Alembic, and starting the FastAPI dev server. It also documents all environment variables and their expected values."

### Doc 02 — Architecture

> "The architecture document defines the three-tier async architecture. Client layer on top — the Next.js frontend, Swagger UI, and any external API clients. Below that, the FastAPI application layer containing routers, services, and the AI client layer. At the bottom, two external dependencies: PostgreSQL via asyncpg, and the AI providers. Every I/O operation in the request path is asynchronous — there are no blocking calls anywhere."

### Doc 03 — Project Structure

> "This document maps every file and directory in the monorepo to its purpose. It documents naming conventions — all files use snake_case, repository classes end with Repository, service classes end with Service. It's the reference a new developer reads first to understand where everything lives."

### Doc 04 — Database Schema

> "The schema document covers all four PostgreSQL tables. Users have UUID primary keys, email uniqueness constraints, and bcrypt-hashed passwords. Summaries store the original input hash for deduplication, the summary text, format, keywords as JSONB, and the model that generated it. Chat sessions link a user to an optional summary. Chat messages belong to a session with a role field distinguishing user from assistant messages. All tables use TIMESTAMP WITH TIME ZONE and cascade on delete."

### Doc 05 — API Design

> "Seventeen REST endpoints across six groups. Health endpoints with no authentication. Auth endpoints for register, login, and token refresh. Summarize endpoints for text and PDF. History endpoints for querying and deleting summaries. Chat endpoints for sessions and messages. Export for PDF download. Every error returns a consistent JSON contract with an error code, human message, details array, status code, and a request ID for tracing."

### Doc 06 — AI Integration

> "The AI integration document details the dual-provider design. OpenRouter is the primary provider using Meta's Llama 3.3 70B instruction model via a free tier. When the primary model returns a rate limit or error, the AI Router rotates through five verified fallback models automatically. HuggingFace BART is the last-resort fallback when all OpenRouter models are exhausted. The document also includes cost estimates per document size and summary length."

### Doc 07 — Advanced Features

> "This document covers the six features built on top of the core engine: JWT authentication with stateless access and refresh tokens, conversational chat against a summary using a sliding context window, full chat history persistence, keyword extraction using KeyBERT, multi-language detection using langdetect with language-specific prompting, and PDF export using reportlab. It also documents the password policy and the frontend token lifecycle — how the access token lives in Zustand memory while the refresh token lives in an httpOnly cookie."

### Doc 08 — Testing Strategy

> "The testing strategy targets 80% code coverage. Unit tests mock AI providers and the database to test business logic in isolation. Integration tests run the full request cycle using httpx's async ASGI client against a real test database. Each integration test wraps its database operations in a transaction that is rolled back after the test, guaranteeing clean state with no test pollution between runs."

### Doc 09 — Deployment

> "The deployment document covers the Render setup — a Docker Web Service for the backend and managed PostgreSQL for the database. The Dockerfile uses a two-stage build: the builder stage installs all Python dependencies, and the runtime stage copies only what is needed and runs as a non-root user. The entrypoint script runs Alembic migrations before starting Uvicorn, ensuring the database schema is always up to date on every deploy."

### Doc 10 — Security Checklist

> "The security checklist maps every OWASP Top 10 category to its specific mitigation in this codebase. Broken access control is addressed with JWT authentication and user ID enforcement in every repository query. Injection is prevented through asyncpg's parameterized queries — no raw SQL string interpolation anywhere. Cryptographic failures are mitigated with bcrypt at cost factor 12 and the `.env` file gitignored. Security misconfiguration is handled by locking CORS to specific allowed origins and setting DEBUG to false in production."

---

## [SECTION 5 — The General Summary Notebook — 10:30–35:00]

**[Screen: Open `docs/general-summary.ipynb` in Jupyter]**

> "Now let's walk through the general summary notebook. This notebook synthesizes all ten documentation files into a single living reference with visualizations. It serves as both documentation and a technical demonstration of the platform's architecture and quality metrics. Let's go cell by cell."

---

### Cell 1 — Title & Overview Table [Markdown]

**[Screen: Rendered markdown cell showing the title and documentation table]**

> "The notebook opens with a title block identifying the author, date, and purpose. Below that is a table mapping each of the ten documentation files to its topic — Environment Setup, Architecture, Project Structure, Database Schema, API Design, AI Integration, Advanced Features, Testing Strategy, Deployment, and Security Checklist. This table is a navigation guide — it tells you exactly what each doc covers before you open it."

---

### Cell 2 — Dependency Installation [Python]

**[Screen: Code cell with subprocess calls to install matplotlib, seaborn, networkx, pandas, numpy]**

> "Cell two installs all visualization dependencies at runtime using Python's subprocess module to call pip. This pattern ensures the notebook is self-contained — anyone who opens it doesn't need to manually pre-install anything. The five packages installed are matplotlib for base charting, seaborn for statistical heatmaps, networkx for graph-based architecture diagrams, pandas for data manipulation, and numpy for numerical array operations. The cell prints a confirmation message when all installs complete."

---

### Cell 3 — Global Style Configuration [Python]

**[Screen: Code cell setting plt.rcParams and defining color constants]**

> "Cell three configures the global visual theme. All chart backgrounds use GitHub's dark color palette — a very dark grey for figure backgrounds, a slightly lighter grey for axes, and a lighter blue-grey for text and labels. Five accent constants are defined: GitHub blue for primary elements, GitHub green for success states, yellow for warnings, red for danger states, a purple accent, and a teal for secondary success. This one-time configuration means every subsequent chart in the notebook inherits a consistent, professional dark-mode appearance without repeating style code."

---

### Cell 4 — Phase 1 Markdown: Environment Setup [Markdown]

**[Screen: Rendered markdown showing the prerequisites table and bash commands]**

> "This markdown cell is the Phase 1 section header. It presents the environment prerequisites in a structured table showing the tool, the specific technology, and the minimum version required. Below that are the five key commands a developer runs to get the backend operational from a fresh checkout: creating and activating the virtual environment, installing requirements, starting the Docker services, running Alembic migrations, and finally starting the FastAPI development server. This is the starting point of the developer experience."

---

### Cell 5 — Environment Setup Readiness Heatmap [Python]

**[Screen: Code cell producing a green heatmap]**

> "Cell five generates a 4-by-4 readiness heatmap for the setup phase. The rows represent the four stages of environment setup: Prerequisites, Virtual Environment, Docker Services, and Database. The columns are specific tasks within each stage. The values are readiness percentages — all ranging between 80 and 100 percent — displayed using a red-yellow-green colormap where green indicates high readiness. The chart uses seaborn's heatmap with annotated cell values, a thin separator between cells, and a colorbar labeled 'Readiness Percent'. The title is rendered in GitHub blue."

---

### Cell 6 — Phase 2 Markdown: System Architecture [Markdown]

**[Screen: Rendered architecture ASCII diagram]**

> "The Phase 2 markdown describes the three-tier async architecture using an ASCII art diagram. At the top sits the Client Layer — the Next.js frontend, Swagger UI, and any external API clients. In the middle is the FastAPI Application Layer, subdivided into Auth, Summarize, and Chat routers at the top, a Service Layer in the middle handling business logic, and an AI Client Layer at the bottom making external calls. At the base of the stack, two external services: PostgreSQL via asyncpg and the AI providers — OpenRouter as primary and HuggingFace BART as fallback. The four key design decisions documented here are: fully async I/O, the Repository pattern for SQL isolation, transparent AI provider switching, and structured JSON logging with request ID correlation on every request."

---

### Cell 7 — Architecture Component Graph [Python]

**[Screen: Code cell producing a directed network graph]**

> "Cell seven renders the architecture as a directed graph using networkx. Fourteen nodes are placed at fixed coordinates across the chart area — three in the client tier, three router nodes, three service nodes, the AI Router, two AI provider nodes, and two database nodes. Directed edges show the flow: client nodes connect to router nodes, routers connect to service nodes, services connect to the AI Router, which branches to both providers. Service nodes also connect to the asyncpg pool, which connects to PostgreSQL. Each tier is colored differently — purple for clients, GitHub blue for routers, teal for services, yellow for the AI Router, green for AI providers, and red for the data layer. A legend in the lower left identifies each color. This is one of the most information-dense cells in the notebook — it shows the entire application's flow in a single glance."

---

### Cell 8 — Phase 3 Markdown: Project Structure [Markdown]

**[Screen: Rendered directory tree]**

> "The Phase 3 markdown presents the monorepo structure as a directory tree with inline comments explaining each directory's purpose. It notes the `.github/` directory containing AI agent configuration files for autonomous phase execution, the `docs/` directory, and the full breakdown of `backend/app/` and `frontend/src/`. The naming conventions are documented: snake_case for all files, Repository suffix for data access classes, Service suffix for business logic classes."

---

### Cell 9 — Project Structure Heatmap [Python]

**[Screen: Code cell producing a viridis heatmap]**

> "Cell nine produces a heatmap measuring three dimensions across eight backend layers: the number of files in each layer, the average lines of code per file, and the code complexity score. The data is manually defined based on the actual codebase and normalized column-by-column for the color scale, while the raw values are displayed as annotations. The viridis colormap — a perceptually uniform purple-to-yellow gradient — is used here. This visualization lets you immediately spot which layers are the most complex — the API routes and services show the highest complexity scores, which is expected for a production application."

---

### Cell 10 — Phase 4 Markdown: Database Schema [Markdown]

**[Screen: ERD text diagram and schema table]**

> "The database markdown documents the entity relationships between the four tables: a user has many summaries and many chat sessions; a chat session belongs to one user and optionally one summary; a chat session has many messages. The key design choices table justifies each decision — UUIDs to prevent sequential ID enumeration attacks, an input hash column on summaries to deduplicate identical text submissions, keywords stored as JSONB to allow flexible querying with a GIN index, cascade deletes to prevent orphaned rows, and Alembic as the sole DDL mechanism so no schema change ever happens outside version control."

---

### Cell 11 — Database ERD Visualization [Python]

**[Screen: Code cell producing a dark-theme ERD diagram]**

> "Cell eleven draws a custom entity relationship diagram using matplotlib patches — not a library ERD tool, but hand-crafted boxes with precise positioning. Each table is drawn with a header block in its accent color and a body block listing the column names with color-coded annotations: GitHub blue for primary keys, yellow for foreign keys, and white for regular columns. Relationship arrows connect the tables with one-to-many labels. Four tables are laid out spatially to mirror the actual relationship topology — users on the left, summaries in the center, chat sessions upper right, and chat messages lower right. This is a fully custom visualization built with matplotlib primitives."

---

### Cell 12 — Phase 5 Markdown: API Design [Markdown]

**[Screen: Endpoint table]**

> "The API design markdown presents all 17 endpoints in a structured table showing method, path, authentication requirement, and description. It notes that the base URL is localhost port 8000 in development and the Render URL in production. It describes the authentication scheme — a Bearer JWT in the Authorization header, obtained from the login endpoint — and documents the consistent error contract that every error response follows: an error code string, a human readable message, a details array for validation errors, the HTTP status code, and a request ID for distributed tracing."

---

### Cell 13 — API Endpoint Heatmap + Request Lifecycle [Python]

**[Screen: Code cell producing a blue heatmap and a printed table]**

> "Cell thirteen has two outputs. The first is a heatmap showing the distribution of endpoint count across six groups and three HTTP methods — GET, POST, and DELETE. The Blues colormap shows where the API surface is densest. The second output is a printed request lifecycle table for the POST summarize-text endpoint, listing all nine steps in order: JWT validation, Pydantic body validation, text preprocessing, language detection, AI Router call to OpenRouter, fallback rotation if needed, keyword extraction, database persistence, and finally returning the summary response. This table is the clearest single view of what happens inside one API call."

---

### Cell 14 — Phase 6 Markdown: AI Integration [Markdown]

**[Screen: AI architecture flow diagram and fallback model list]**

> "The AI integration markdown shows the full call chain from SummarizerService or ChatService through the AI Router to the providers. It lists the five verified free-tier fallback models on OpenRouter in rotation order: Gemma 3 12B, NVIDIA Nemotron, Hermes Llama 405B, Llama 3.2 3B, and Gemma 3 4B. It also includes a cost estimate table for the GPT-4o-mini pricing reference, showing approximate cost per document size and summary length — ranging from fractions of a cent for short summaries to roughly two-thirds of a cent for 10,000 word documents with long output."

---

### Cell 15 — AI Fallback Decision Tree + Cost Heatmap [Python]

**[Screen: Code cell producing a flowchart and a cost heatmap]**

> "Cell fifteen generates two charts. The first is a decision tree flowchart — again hand-drawn using matplotlib FancyBboxPatch — showing every branch in the AI Router: request arrives, AI Router called, primary model attempted, on success returning an AI response, on error rotating through fallback models, and if all are exhausted either calling HuggingFace BART as a last resort or raising an AIServiceUnavailable exception. The second chart is a cost heatmap across five document sizes and three summary lengths, using the yellow-orange-red colormap to make cost escalation immediately visible."

---

### Cell 16 — Phase 7 Markdown: Advanced Features [Markdown]

**[Screen: Feature table and JWT lifecycle diagram]**

> "The advanced features markdown documents six capabilities in a feature table. The most detailed section covers the JWT token lifecycle: login returns both an access token — valid for 30 minutes — and a refresh token, valid for seven days. The frontend stores the access token in Zustand memory only, never in localStorage, and stores the refresh token in an httpOnly cookie via a Next.js server-side route handler. When the Axios interceptor receives a 401, it calls the refresh endpoint, gets new tokens, updates the Zustand store, and retries the original request — completely transparent to the user. The password policy requires a minimum of eight characters with at least one uppercase letter, one digit, and one special character."

---

### Cell 17 — Advanced Feature Radar Chart [Python]

**[Screen: Code cell producing a polar radar chart]**

> "Cell seventeen renders a radar chart — also called a spider chart — showing implementation completeness across the six advanced features. JWT Authentication scores 100 percent, Chat-with-Document and Chat History at 95, Keyword Extraction at 90, Multi-language at 85, and PDF Export at 80. The chart uses matplotlib's polar projection, with the filled area in GitHub blue at 25 percent opacity. The radar shape gives an immediate visual sense of which features are fully implemented and which have room for improvement."

---

### Cell 18 — Phase 8 Markdown: Testing Strategy [Markdown]

**[Screen: Test directory tree and pytest command]**

> "The testing markdown documents the directory structure: a shared `conftest.py` with database fixtures, a `unit/` directory with eight test modules each isolating one service or component with mocked dependencies, and an `integration/` directory with six test modules that test the full HTTP request cycle using an in-memory test client against a real PostgreSQL test database. The key technique is the transaction rollback pattern: each integration test opens a database transaction, runs the test, and rolls back — guaranteeing a clean slate for every test in O(1) time without truncating tables."

---

### Cell 19 — Test Coverage Heatmap [Python]

**[Screen: Wide heatmap with 18 modules across two test types]**

> "Cell nineteen is the widest chart in the notebook — an 18-column by 2-row heatmap showing estimated coverage percentages for every backend module across unit and integration tests. The red-yellow-green colormap makes coverage gaps immediately visible — the export service and keyword extractor show lower coverage in yellow-red, while security, dependencies, and database repositories show strong green coverage. This visualization makes a clear case for where testing effort should be focused in future phases."

---

### Cell 20 — Phase 9 Markdown: Deployment [Markdown]

**[Screen: Deployment pipeline description]**

> "The deployment markdown documents the production environment on Render. The Docker Web Service runs the FastAPI application. The managed PostgreSQL instance handles the database. The deployment pipeline starts with a git push to main, which triggers Render to detect the `render.yaml`, build the Docker image using the multi-stage Dockerfile, run the entrypoint script which applies Alembic migrations then starts Uvicorn, and finally pass the health check at `/health` before marking the deployment live. The multi-stage build strategy is highlighted: the builder stage installs all Python packages, the runtime stage copies only the installed packages and runs as non-root uid 1001 for container security."

---

### Cell 21 — Deployment Pipeline Chart [Python]

**[Screen: Horizontal pipeline flow boxes]**

> "Cell twenty-one renders the deployment pipeline as a horizontal sequence of boxes connected by arrows. Seven stages are shown left to right: git push, Render detects `render.yaml`, Docker multi-stage build, `alembic upgrade head`, uvicorn start, health check, and finally the live check mark. Each box uses a distinct accent color — blue for git, purple for Render detection, yellow for Docker build, green for migrations and server start, teal for health check, and green for live. The visual immediately communicates the linear, gated nature of the deploy pipeline."

---

### Cell 22 — Phase 10 Markdown: Security Checklist [Markdown]

**[Screen: OWASP table with 10 rows]**

> "The security markdown presents the full OWASP Top 10 mapping. Each row shows the OWASP category code, the category name, the specific mitigation implemented in this codebase, and the phase in which it was implemented. This table is both documentation and an audit record — it can be handed to a security reviewer to demonstrate coverage of the most common vulnerability categories."

---

### Cell 23 — OWASP Risk Heatmap [Python]

**[Screen: Three side-by-side heatmap columns]**

> "Cell twenty-three generates a three-panel OWASP risk assessment. The first column shows inherent risk on a zero-to-ten scale using the yellow-orange-red colormap — access control, injection, and authentication failures score highest at 9. The second column shows mitigation strength using the red-yellow-green colormap reversed — injection and access control score 10 and 9 respectively, showing strong mitigation. The third column shows residual risk after mitigation — computed as inherent risk minus mitigation strength plus a ten offset, displayed with a reversed green colormap so lower numbers appear greener, confirming that every OWASP category has been driven to a low residual risk. The three charts share the y-axis with the OWASP category names."

---

### Cell 24 — Business Logic Markdown: End-to-End User Journey [Markdown]

**[Screen: Full user journey tree diagram and business metrics table]**

> "This markdown cell steps back from technical implementation and describes the platform from a business logic perspective. It shows the complete user journey as a branching tree: register and log in to receive JWT tokens, upload a PDF or paste text to trigger summarization, view the AI-generated summary with keywords, chat with the summary in a conversational interface, browse history, and download the PDF export. Below the journey diagram is a business value metrics table with seven KPIs: summary latency target under 8 seconds at the 95th percentile, PDF extraction accuracy above 95 percent, AI fallback success rate above 99 percent, API availability at 99.9 percent uptime, token efficiency under 2000 tokens per summary, test coverage at or above 80 percent, and zero OWASP critical items."

---

### Cell 25 — Platform Quality Heatmap [Python]

**[Screen: 11-row by 6-column quality heatmap]**

> "Cell twenty-five is the platform-wide quality heatmap. Eleven rows represent every major platform layer from the frontend to the deployment infrastructure. Six columns represent quality dimensions: Reliability, Security, Performance, Scalability, Observability, and Test Coverage. The yellow-green-blue colormap makes the strongest layers immediately visible. The database layer scores highest across reliability, security, and performance. The export service and keyword extractor show lower scores in test coverage — consistent with the testing heatmap in cell nineteen. This single chart is the most complete summary of the platform's quality posture."

---

### Cell 26 — Phase Completion Gantt [Python]

**[Screen: Horizontal bar chart]**

> "Cell twenty-six renders the phase completion overview as a horizontal bar chart. Ten phases are shown: four backend phases, four frontend phases, and the deployment phase. Phases at 100 percent are colored green, phases between 75 and 99 percent are yellow, and anything below 75 is red. At the time this notebook was authored, phases 0 through 3 on both backend and frontend were fully complete. Phase 4 production hardening was at 75 percent. FE Phase 4 Chat and History UI was at 85 percent. Deployment was at 60 percent. The vertical dashed line at 100 percent serves as a visual goal marker. Below the chart, a pandas DataFrame prints the exact completion percentages alongside the overall average."

---

### Cell 27 — Summary Markdown [Markdown]

**[Screen: Final summary cell]**

> "The notebook closes with a summary markdown cell that distills the platform into four core pillars.
>
> Reliability — multi-model AI fallback with five OpenRouter models plus HuggingFace BART, asyncpg connection pooling, and structured error handling.
>
> Security — full OWASP Top 10 coverage, bcrypt at cost factor 12, parameterized SQL, CORS lockdown, and JWT token rotation.
>
> Observability — structured JSON logging with request ID correlation on every request, plus health and database liveness endpoints.
>
> Developer Experience — the monorepo structure, Alembic migrations, Docker Compose local development stack, pytest coverage targets, and AI agent configuration files for autonomous phase execution."

---

## [OUTRO — 34:00–35:30]

**[Screen: Live Render backend health endpoint returning JSON]**

> "That is the complete walkthrough of the AI-Based Text Summarization Platform.
>
> We covered the monorepo structure, the FastAPI backend with its layered architecture, the Next.js frontend with its App Router and API client layer, ten documentation files that served as both blueprint and record, and every cell of the architectural summary notebook.
>
> The backend is live on Render at the URL shown on screen. The frontend is deployed to Vercel. The database is running on Render's managed PostgreSQL.
>
> Every design decision in this codebase was deliberate — asynchronous I/O throughout, the repository pattern for clean data access, a dual-provider AI layer for resilience, JWT with httpOnly cookies for security, and a Docker-based deployment that guarantees environment parity from your laptop to production.
>
> If you have questions about any specific component, the ten documentation files in the `docs/` directory are the definitive reference.
>
> Thank you for watching."

---

**[END CARD: GitHub repo URL · Render live URL · Vercel frontend URL]**

---

*Script end — approximately 35–40 minutes at a measured professional narration pace.*

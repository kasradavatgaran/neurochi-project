# System Architecture & Specifications

## 1. Overall System Architecture

Nerochi follows a modern **Client-Server Architecture** utilizing a RESTful API pattern, enhanced with an AI Agent layer.

### High-Level Components

1.  **Presentation Layer (Frontend):**
    *   A Single Page Application (SPA) built with **Vue.js**.
    *   Responsible for UI rendering, audio recording, chart visualization, and state management.
    *   Communicates with the backend via **Axios** (HTTP JSON/FormData).

2.  **Application Layer (Backend):**
    *   Built with **FastAPI**.
    *   **API Gateway:** Handles routing, request validation (Pydantic), and CORS.
    *   **Controller Logic:** Orchestrates logic for Auth (OTP), Profile management, and Test sessions.
    *   **AI Orchestrator:** Manages `ChatSession` state for Gemini, handles RAG context injection, and processes STT (Speech-to-Text) and TTS (Text-to-Speech) requests.

3.  **Data Layer:**
    *   **Relational DB:** **SQLite** (via SQLAlchemy ORM) stores User data, Children profiles, Test results, Growth records, and Chat history.
    *   **Vector/Knowledge Base:** In-memory or local vector storage using `sentence-transformers` to retrieve relevant parenting documents (RAG).

### Interaction Flow (Example: Voice Chat)
1.  **User** holds microphone -> Frontend records audio.
2.  **Frontend** sends `.mp3` blob to `POST /transcribe-audio`.
3.  **Backend** saves temp file -> Sends to Gemini Flash for STT -> Gets Text.
4.  **Backend** performs RAG search (embeds text, queries docs) -> Retrieves Context.
5.  **Backend** retrieves/creates `ChatSession` -> Sends (Prompt + Context + History) to Gemini Pro.
6.  **Backend** saves interaction to DB -> Returns Text Response + Audio URL (TTS) to Frontend.

---

## 2. Infrastructure Requirements

To run the Kidora system efficiently, the following minimum specifications are required.

### Minimum Requirements (Development/Small Deployment)
*   **CPU:** 2 vCPUs (Intel/AMD) - Required for vector embedding and audio processing.
*   **RAM:** 4 GB (8 GB recommended if running local LLMs, but 4GB is sufficient for API-based LLMs).
*   **Storage:** 10 GB SSD (Database grows over time; audio files are temporary).
*   **Network:** Stable internet connection (Critical for Google Gemini API access).
*   **OS:** Ubuntu 20.04+, Windows 10/11, or macOS.

### Software Dependencies
*   **Python:** 3.10+
*   **Node.js:** 16+
*   **SQLite3**

---

## 3. AI Model Documentation

The system leverages a Multi-Modal approach using Google's Gemini ecosystem.

### Models Used
1.  **Chat & Analysis:** `gemini-2.5-flash`.
    *   *Usage:* General chat, Parenting advice, Final Analysis of tests.
    *   *Configuration:* Stateful `ChatSession` with System Instructions ("Persona: Kidora Expert").
2.  **Speech-to-Text (STT):** `gemini-2.5-flash`.
    *   *Usage:* Transcribing user audio inputs.
3.  **Text-to-Speech (TTS):** `gemini-2.5-flash-preview-tts` (or standard TTS endpoints).
    *   *Usage:* Converting bot text responses to audio.
4.  **Embeddings (RAG):** `Gemini-embedding` (Local execution).
    *   *Usage:* Vectorizing knowledge base documents for retrieval.

### Estimated TPS by Hardware Configuration

*Estimates assume Uvicorn running with workers matching CPU cores.*

| Hardware Configuration | Scenario A: Read-Heavy<br>(Get Profile, Get Games) | Scenario B: Write-Heavy<br>(Submit Answers, Auth) | Scenario C: AI Operations<br>(Chat, Analysis, Audio) | Bottleneck |
| :--- | :--- | :--- | :--- | :--- |
| **Minimum**<br>1 vCPU, 2GB RAM | ~150 - 200 TPS | ~30 - 50 TPS | ~2 - 5 TPS | CPU (Embeddings) & RAM |
| **Recommended**<br>2 vCPUs, 4GB RAM | ~400 - 600 TPS | ~80 - 100 TPS | ~10 - 20 TPS | SQLite Write Lock |
| **High Performance**<br>4 vCPUs, 8GB RAM | ~1,000+ TPS | ~150 TPS | ~40 - 50 TPS | External API Rate Limits

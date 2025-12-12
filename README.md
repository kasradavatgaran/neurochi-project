# Neurochi - Intelligent Parenting Assistant

Neurochi is a comprehensive, AI-powered application designed to assist parents in monitoring their child's growth, assessing developmental milestones (ASQ), and providing personalized game recommendations and analysis.

## 🛠 Technologies Used

### Frontend (Client-Side)
*   **Framework:** Vue.js 3
*   **State & Routing:** Vue Router
*   **HTTP Client:** Axios
*   **Visualization:** Chart.js, vue-chartjs
*   **Audio Processing:** mic-recorder-to-mp3
*   **Styling:** Custom CSS (Flexbox/Grid), Responsive Design

### Backend (Server-Side)
*   **Framework:** FastAPI (Python)
*   **Server:** Uvicorn (ASGI)
*   **Database ORM:** SQLAlchemy
*   **Validation:** Pydantic
*   **Audio Handling:** Standard Python `wave`, `shutil`

### AI & Data
*   **LLM Provider:** Google Gemini API (1.5 Flash & Pro models)
*   **RAG (Retrieval-Augmented Generation):** Custom implementation using `sentence-transformers` for embeddings.
*   **Database:** SQLite (Development/MVP)

---

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
*   **Python:** Version 3.9 or higher
*   **Node.js:** Version 16 or higher
*   **npm** or **yarn**
*   **Google Gemini API Key**

### 1. Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Ensure your `requirements.txt` includes: `fastapi`, `uvicorn`, `sqlalchemy`, `google-generativeai`, `python-multipart`, `sentence-transformers`, `chromadb` (if used), `pandas`, `openpyxl`)*

4.  Set up Environment Variables:
    Create a `.env` file or export your API key:
    ```bash
    export GOOGLE_API_KEY="your_actual_api_key_here"
    ```

5.  Initialize the Database:
    The database (`kidora.db`) will be automatically created and seeded with test data/games upon the first run.

6.  Start the Server:
    ```bash
    uvicorn main:app --reload
    ```
    The backend will run at `http://127.0.0.1:8000`.

### 2. Frontend Setup

1.  Navigate to the frontend directory (open a new terminal):
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the Development Server:
    ```bash
    npm run serve
    ```
    The application will typically run at `http://localhost:8080`.

---

## 📂 Project Structure

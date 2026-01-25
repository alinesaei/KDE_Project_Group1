# Semantic Pokédex - Setup & Running Instructions

This project uses a **Hybrid Setup**:
1.  **Database:** Runs in Docker (GraphDB).
2.  **Application:** Runs locally on Python (Streamlit).

---

## ✅ Prerequisites
* **Docker Desktop** (Installed and running).
* **Python 3.9+**.

---

## 🚀 Step 1: Start the Database (Docker)

1.  Open a terminal in the project root folder (where this README is located).
2.  Start the GraphDB container:
    ```bash
    docker-compose up -d
    ```
3.  Open the **GraphDB Workbench** in your browser: `http://localhost:7200`
4.  **⚠️ CRITICAL STEP (Data Import):**
    * Go to **Setup** -> **Repositories** -> **Create New Repository**.
    * **Repository ID:** `pokemon-repo` (Must match this exact name).
    * Click **Create**.
    * Go to **Import** -> **Upload RDF Files**.
    * Upload all files from the `data/rdf/` folder (Select both `.ttl` and `.nq` files).
    * Click **Import**.

---

## 💻 Step 2: Run the Application (Python)

1.  Open a **new** terminal window in the project root.
2.  Create and activate a virtual environment:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # Mac / Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the dashboard:
    ```bash
    streamlit run app/main.py
    ```

---

## 🌐 Access Points

| Service | URL |
| :--- | :--- |
| **User Interface** | `http://localhost:8501` |
| **Database Workbench** | `http://localhost:7200` |
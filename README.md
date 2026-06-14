# SplitEase - Expense Sharing App (Spreetail Assignment)

SplitEase is a full-stack web application designed to simplify group expense sharing. It features a robust CSV import engine capable of detecting and handling 18 different data anomalies, a transaction-minimizing algorithm ("Who Owes Whom"), and a sleek dark-themed UI.

## Tech Stack
- **Backend:** Python, FastAPI
- **Database:** SQLite, SQLAlchemy ORM
- **Frontend:** HTML, CSS, Jinja2 Templates (Server-Side Rendering)
- **Deployment:** Render.com

## How to Run Locally

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd spreetail-expenses
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Server**
   ```bash
   uvicorn main:app --reload
   ```
4. Open your browser and go to `http://127.0.0.1:8000`

## API Routes Overview

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/login`, `/signup`, `/logout` | User Authentication |
| GET/POST | `/groups` | Create and view groups |
| GET/POST | `/groups/{id}/expenses` | View and add manual expenses |
| GET | `/groups/{id}/balances` | View simplified debts ("Who owes whom") |
| GET/POST | `/groups/{id}/settlements` | Record debt payments |
| GET/POST | `/groups/{id}/import` | Upload and process CSV files |

## Core Features
1. **CSV Import Pipeline:** A 5-stage pipeline that normalizes data, detects duplicates, handles missing values, and flags out-of-bounds metrics (see `SCOPE.md` for details).
2. **Balance Engine:** Calculates exact net balances and uses a greedy algorithm to simplify debts to the minimum number of transactions.
3. **Audit Trail:** Every CSV import generates a detailed report of how many rows were imported, skipped, and flagged.

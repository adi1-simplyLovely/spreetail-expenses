# AI Usage Declaration

This project was built iteratively using an AI Coding Assistant. Below is a summary of how AI was leveraged to accelerate development and improve code quality.

## 3 Cases Where AI Produced Something Wrong (And How It Was Fixed)

**1. The "Excel BOM" CSV Parsing Failure**
*   **What went wrong:** The AI generated a CSV `DictReader` logic that expected the exact string `"Date"` as a header. However, CSV files exported from Excel often include a hidden Byte Order Mark (`\ufeff`). The AI's code read the header as `"\ufeffDate"`, failed the match, and skipped all 42 valid rows.
*   **How I caught it:** I uploaded the sample CSV and the system flagged every single row as "Missing or invalid date format."
*   **What I changed:** Instructed the AI to update the file decoding from `utf-8` to `utf-8-sig` to automatically strip the BOM character, and added a `.strip().lower()` normalization pass to all CSV header keys before processing.

**2. The Dynamic JWT Secret Key Crash**
*   **What went wrong:** The AI initially used `secrets.token_hex(32)` to generate a random JWT secret key every time the FastAPI server started. 
*   **How I caught it:** After deploying to Render's free tier, the application would occasionally spin down due to inactivity. When it spun back up, a new secret key was generated, invalidating all existing user session cookies and throwing a 401 Unauthorized "Could not validate credentials" error.
*   **What I changed:** I realized the issue and had the AI replace the dynamic generation with a static, hardcoded `SECRET_KEY` (or one loaded from environment variables) so sessions persist across server reboots.

**3. The Missing Import (NameError) during IDOR Security Patching**
*   **What went wrong:** While writing security checks to prevent users from importing data into groups they don't belong to, the AI added a `db.query(GroupMember)` database check inside `import_routes.py`, but forgot to add `from models import GroupMember` at the top of the file.
*   **How I caught it:** I clicked the "Import CSV" button and was immediately greeted with a 500 Internal Server Error. The server logs showed a `NameError: name 'GroupMember' is not defined`.
*   **What I changed:** Traced the error back to the missing import and added `GroupMember` to the SQLAlchemy models import list at the top of `import_routes.py`.

## Areas of AI Assistance
1. **Architecture Planning:** AI helped map out the core modules, ensuring all assignment requirements were met sequentially.
2. **Data Anomaly Strategy:** Used AI to brainstorm and catalog the 18 distinct anomalies hidden within the provided CSV dataset, and to construct the "Header Normalization" engine.
3. **Algorithm Generation:** The Greedy Algorithm used in `utils/balance_engine.py` for "Simplify Debts" was drafted with AI assistance and mathematically verified against test cases.
4. **Security Auditing:** Ran rigorous AI-assisted security scans and E2E tests, which successfully identified and patched 5 critical IDOR vulnerabilities related to group data access.
5. **UI Styling & UX:** AI generated the dark-themed CSS variables, responsive layout logic, and the rich "Dashboard" UI to present a premium user experience.

## Example Prompts Used
- *"Help me design a SQLite database schema for an expense sharing app that tracks users, groups, dynamic expense splits, and settlement payments."*
- *"Analyze this list of CSV anomalies and write a 5-stage Python parsing pipeline to handle them robustly (e.g., messy dates, 110% overflow, missing split types)."*
- *"Run a rigorous E2E security test on all my API endpoints to ensure users cannot add or delete expenses from groups they are not members of."*
- *"The CSV parser is throwing 'Missing date' errors for every row. What encoding issues (like Excel BOM) could be causing the DictReader to misread the headers?"*

## Time Saved
Leveraging AI for boilerplate generation, UI aesthetics, rigorous automated testing, and complex algorithm drafting reduced the development timeline significantly, allowing more focus on product stability, architectural integrity, and anomaly handling logic.

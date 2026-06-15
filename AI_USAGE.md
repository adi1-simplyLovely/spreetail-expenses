# AI Usage Declaration

This project was built iteratively using an AI Coding Assistant. Below is a summary of how AI was leveraged to accelerate development and improve code quality.

## Areas of AI Assistance
1. **Architecture Planning:** AI helped map out the core modules, ensuring all assignment requirements were met sequentially.
2. **Data Anomaly Strategy:** Used AI to brainstorm and catalog the 18 distinct anomalies hidden within the provided CSV dataset, and to construct the "Header Normalization" engine to strip Excel BOM markers.
3. **Algorithm Generation:** The Greedy Algorithm used in `utils/balance_engine.py` for "Simplify Debts" was drafted with AI assistance and mathematically verified against test cases.
4. **Security Auditing:** Ran rigorous AI-assisted security scans and E2E tests, which successfully identified and patched 5 critical IDOR vulnerabilities related to group data access, securing the API logic.
5. **UI Styling & UX:** AI generated the dark-themed CSS variables, responsive layout logic in `style.css`, and the rich "Dashboard" UI to present a premium user experience.
6. **Debugging:** Used AI to rapidly identify the cause of intermittent login crashes caused by Render's free-tier container restarts, shifting from dynamic to static JWT signing keys.

## Example Prompts Used
- *"Help me design a SQLite database schema for an expense sharing app that tracks users, groups, dynamic expense splits, and settlement payments."*
- *"Analyze this list of CSV anomalies and write a 5-stage Python parsing pipeline to handle them robustly (e.g., messy dates, 110% overflow, missing split types)."*
- *"Run a rigorous E2E security test on all my API endpoints to ensure users cannot add or delete expenses from groups they are not members of."*
- *"The CSV parser is throwing 'Missing date' errors for every row, but the date is present. What encoding issues (like Excel BOM) could be causing the DictReader to misread the headers?"*

## Time Saved
Leveraging AI for boilerplate generation, UI aesthetics, rigorous automated testing, and complex algorithm drafting reduced the development timeline from an estimated ~30 hours to under 6 hours, allowing more focus on product stability, architectural integrity, and anomaly handling logic.

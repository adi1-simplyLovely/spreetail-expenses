# AI Usage Declaration

This project was built iteratively using an AI Coding Assistant. Below is a summary of how AI was leveraged to accelerate development and improve code quality.

## Areas of AI Assistance
1. **Architecture Planning:** AI helped map out the 10-module master plan, ensuring all assignment requirements were met sequentially.
2. **Data Anomaly Strategy:** Used AI to brainstorm and catalog the 18 distinct anomalies hidden within the provided CSV dataset.
3. **Algorithm Generation:** The Greedy Algorithm used in `utils/balance_engine.py` for "Simplify Debts" was drafted with AI assistance and mathematically verified.
4. **UI Styling:** AI generated the dark-themed CSS variables and responsive layout logic in `style.css`.
5. **Debugging:** Used AI to quickly resolve a breaking change in the `TemplateResponse` signature caused by a newer FastAPI/Starlette version during deployment.

## Example Prompts Used
- *"Help me design a SQLite database schema for an expense sharing app that tracks users, groups, dynamic expense splits, and settlement payments."*
- *"Analyze this list of CSV anomalies and write a 5-stage Python parsing pipeline to handle them robustly (e.g., messy dates, 110% overflow, missing split types)."*
- *"Render.com is throwing a TypeError: unhashable type: 'dict' on TemplateResponse. Write a python script to regex replace the old syntax with the new kwargs syntax across my entire project."*

## Time Saved
Leveraging AI for boilerplate generation, CSS styling, and complex algorithm drafting reduced the development timeline from an estimated ~25 hours to under 4 hours, allowing more focus on product strategy and anomaly handling logic.

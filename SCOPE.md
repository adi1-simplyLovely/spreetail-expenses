# Project Scope & Anomaly Handling

## Database Schema (ER Diagram)

```mermaid
erDiagram
    USER {
        int id PK
        string name
        string email
        string password_hash
    }
    GROUP {
        int id PK
        string name
        string description
        date created_at
    }
    GROUP_MEMBER {
        int id PK
        int group_id FK
        int user_id FK
        date joined_at
        date left_at
    }
    EXPENSE {
        int id PK
        int group_id FK
        string description
        int paid_by FK
        float amount
        string currency
        float amount_inr
        string split_type
        date date
        boolean is_settlement
        boolean is_flagged
    }
    EXPENSE_SPLIT {
        int id PK
        int expense_id FK
        int user_id FK
        float amount_owed
    }
    SETTLEMENT {
        int id PK
        int group_id FK
        int from_user_id FK
        int to_user_id FK
        float amount
        date date
    }
    IMPORT_LOG {
        int id PK
        int group_id FK
        string filename
        int total_rows
        int imported
        int skipped
        int flagged
        string report_json
    }

    USER ||--o{ GROUP_MEMBER : "joins"
    GROUP ||--o{ GROUP_MEMBER : "has"
    GROUP ||--o{ EXPENSE : "contains"
    EXPENSE ||--o{ EXPENSE_SPLIT : "split into"
    USER ||--o{ EXPENSE_SPLIT : "owes"
    USER ||--o{ SETTLEMENT : "pays / receives"
    GROUP ||--o{ IMPORT_LOG : "audits"
```

## The 18 Anomalies Handled by the CSV Parser

Our `utils/csv_parser.py` implements a 5-stage pipeline to handle anomalies present in the raw spreadsheet:

1. **Duplicate Rows:** Checked using a composite hash of Date+Desc+Payer+Amount. Policy: First-row-wins, rest are Skipped.
2. **Missing Split Type:** Defaulted to "equal" split amongst all active group members at the time of the expense.
3. **Settlements Disguised as Expenses:** Descriptions containing "paid back" with an empty split type are automatically rerouted and saved as Settlements.
4. **Invalid Percentages (>100%):** Math overflow (e.g., 110%) is caught, the row is Flagged, and the fallback is an equal split assigned to the payer so money isn't lost.
5. **Messy Date Formats:** `python-dateutil` parses "Mar-14", "15/04", etc. Policy: DD-MM-YYYY is strictly enforced as the primary format.
6. **Membership Timeline Conflicts:** If a user is added to an expense *after* their `left_at` date, the row is Flagged for review.
7. **Explicit Rejections:** Rows with "wrong" or "ignore" in the Notes column are explicitly Skipped.
8. **Currency Conversion:** USD entries are dynamically converted to INR (Base conversion: 1 USD = 83.50 INR).
9. **Unknown Users:** Names not recognized in the system are automatically created and added to the Group to prevent import failure.
10. **Rounding Errors:** Handled using accounting standard `ROUND_HALF_UP` during split calculations to ensure cents don't leak.
*(...and 8 other structural edge cases regarding empty descriptions, zero amounts, and string stripping).*

## Out of Scope
The following features were intentionally excluded to focus on core requirements:
- Email/SMS notifications for debts.
- Live WebSockets for real-time updates.
- OAuth (Google/GitHub login).
- Multi-currency live exchange rate API (static conversion used instead).

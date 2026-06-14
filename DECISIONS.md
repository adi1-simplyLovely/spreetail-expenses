# Technical Decisions & Trade-offs

This document outlines the rationale behind the key technical decisions made during the development of SplitEase.

## 1. Why FastAPI?
**Decision:** Selected FastAPI over Django or Flask.
**Rationale:** FastAPI provides out-of-the-box asynchronous support, which is excellent for I/O bound operations like CSV processing. It also automatically generates Swagger documentation and performs data validation via Pydantic, significantly reducing boilerplate code.

## 2. Why SQLite?
**Decision:** Used SQLite as the primary database.
**Rationale:** SQLite is lightweight, file-based, and requires zero infrastructure setup. It perfectly satisfies the assignment requirements while keeping the project highly portable for the evaluator to test locally.

## 3. Deployment Strategy (Bypassing `render.yaml`)
**Decision:** Deployed manually as a Render "Web Service" instead of using the Infrastructure-as-Code `render.yaml` Blueprint.
**Rationale:** Render's recent policy update requires a credit card on file to use the Blueprint feature (specifically for provisioning persistent disks), even for free tier usage. To keep the deployment 100% free and accessible without payment barriers, the Blueprint was bypassed in favor of a stateless manual deployment. The trade-off is that SQLite data resets upon server restart on the free tier, which is acceptable for a showcase assignment.

## 4. Frontend Architecture (Jinja2 Templates)
**Decision:** Used Server-Side Rendering (SSR) via Jinja2 instead of a decoupled React/Next.js frontend.
**Rationale:** Building a decoupled frontend requires setting up CORS, managing JWT tokens in localStorage, and creating two separate deployment pipelines. For an assignment focused heavily on backend logic (CSV parsing and algorithms), SSR allows for rapid iteration, SEO friendliness, and a single cohesive codebase.

## 5. The Balance Engine Algorithm
**Decision:** Implemented a Greedy Algorithm for debt simplification.
**Rationale:** Instead of mapping a complex graph of every individual debt (A owes B, B owes C, C owes A), the engine calculates the net balance (+/-) for each user. It then iteratively matches the maximum debtor with the maximum creditor. This mathematically guarantees the minimum possible number of transactions to settle the entire group, heavily inspired by Splitwise's "Simplify Debts" feature.

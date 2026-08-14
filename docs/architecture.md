# Whitfield WMS Architecture

This is a full-stack web application:

- Frontend: Next.js + TypeScript
- Backend: FastAPI
- Database: SQLite for local/client-ready MVP

Core flow:

Seller / Marketplace order → Order created → Stock reserved → Picker task → Pick scan → Pack + invoice/label → Dispatch → Physical stock deducted → Seller tracking updated.

Inventory is protected by a movement ledger. Stock is never treated as one manually editable number.

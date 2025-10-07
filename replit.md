# Sensasiwangi.id - Indonesian Fragrance Marketplace

## Overview

Sensasiwangi.id is a digital platform dedicated to promoting local Indonesian fragrance products (perfumes, aromatherapy, home fragrances) by connecting them to the national market through rich Nusantara storytelling. The platform features a curated Marketplace, an editorial channel called Nusantarum for olfactory story curation, and User & Brand Profiles to build trust and manage preferences. The project aims to validate that storytelling drives product engagement, automation reduces operational effort, and curated profiles increase conversion.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI**: Asynchronous application using a modular monolith pattern.
- **SQLAlchemy 2.0**: ORM with AsyncSession and Pydantic v2 schemas.
- **Dependency Injection**: Utilized for service layer and database sessions.
- **Alembic**: Manages database migrations with versioning.

### Frontend Approach
- **Server-Side Rendering (SSR)**: Powered by Jinja2 templates.
- **HTMX**: For progressive enhancement, enabling partial updates and dynamic forms.
- **Glassmorphism**: UI theme inspired by glass perfume bottles.
- **Mobile-first**: Responsive design with fallback HTML.

### Authentication & Security
- **Supabase Auth**: Handles email and magic link authentication.
- **bcrypt**: Used for password hashing.
- **Rate Limiting**: Implemented on critical endpoints.
- **Session Middleware**: Encrypted 30-day cookies.
- **Audit Logging**: For authentication and order operations.

### Core Features

#### Product Catalog
- Supports marketplace and Sambatan (group-buy) modes with stock management.
- Features product variants, images, history tracking, and categorized listings.

#### Order Management
- Manages the full order lifecycle from draft to completion.
- Integrates with RajaOngkir API for shipping calculations.
- Tracks order status history and performs atomic stock reservations.

#### Shopping Cart
- Session-based cart storage with item management and quantity validation.

#### Sambatan (Group-Buy)
- Manages campaigns with slot-based participation, automated lifecycle states, and participant tracking.
- Uses APScheduler for background processing of deadlines and refunds/payouts.

#### BRI Wallet & Payment System
- **E-Wallet Infrastructure**: User wallets linked to BRI BaaS virtual accounts with real-time balance tracking and BRIVA integration for top-ups.
- **Escrow Workflow**: Buyer payments are held until delivery confirmation, with automatic release to sellers (minus platform fee) or refunds for cancellations.
- **Platform Fee System**: A 3% fee is automatically deducted from seller payouts.
- **BRI BaaS Integration**: API client with HMAC-SHA256 for virtual account creation, fund transfers, balance inquiry, and webhook handling for payment confirmation.

#### Brand Management
- Provides brand profiles, multi-member support, and a brand verification workflow.
- Displays product catalogs and certifications.

#### Nusantarum Editorial
- Curated content (Perfume, Brand, Perfumer) with verification status and optional linking to products/brands.

#### Platform Administration
- **Admin Settings Dashboard**: Platform-wide configuration management at `/dashboard/admin-settings`
- **Dynamic Platform Fee**: Configurable fee rate stored in database (default 3%)
- **Platform Bank Account**: Centralized bank account configuration for settlement payouts
- **Fail-Closed Security**: Admin access requires explicit environment variable configuration (ADMIN_USER_IDS or ADMIN_EMAILS)
- **Settings Service**: Atomic operations for reading/updating platform configuration
- **Integration**: Settlement service dynamically reads fee rate from settings with fallback

### Data Layer

#### Database (Supabase/PostgreSQL 15)
- **Schema**: 16+ active tables, views, and functions.
- **Row-Level Security (RLS)**: For access control.
- **Triggers and Functions**: For automation (e.g., progress calculation, wallet operations).
- **Atomic Operations**: Via stored procedures for critical processes like stock management and wallet transactions.
- **Wallet System Tables**: `user_wallets`, `wallet_transactions`, `wallet_topup_requests`, `order_settlements`.

### Background Processing
- **APScheduler**: Used for `SambatanScheduler` to manage campaign deadlines and process refunds/payouts.

### Deployment
- **Vercel**: Serverless deployment via Mangum ASGI adapter.
- **CI/CD**: Includes linting (Ruff, Black) and test coverage gates.

## External Dependencies

### Required Services
1.  **Supabase**: Managed PostgreSQL, Auth, and Storage. Used for the primary database, RLS, and file storage.
    -   Environment variables: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
2.  **RajaOngkir API**: For shipping cost calculation and address data.
    -   Environment variable: `RAJAONGKIR_API_KEY`.
3.  **BRI BaaS API**: For banking services, virtual accounts (BRIVA), fund transfers, and wallet management.
    -   Environment variables: `BRI_CLIENT_ID`, `BRI_CLIENT_SECRET`, `BRI_API_KEY`, `BRI_MERCHANT_ID`.

### Python Packages
-   **Core**: `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `aiofiles`, `httpx`.
-   **Data**: `supabase`, `pydantic-settings`, `email-validator`.
-   **Security**: `bcrypt`, `slowapi`.
-   **Scheduling**: `apscheduler`.
-   **Deployment**: `mangum`.

### Frontend Libraries
-   **HTMX**: For dynamic UI enhancements.
-   **Feather Icons** / **Phosphor Icons**: For UI elements.
-   **Google Fonts**: For typography.
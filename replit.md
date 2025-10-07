# Sensasiwangi.id - Indonesian Fragrance Marketplace

## Overview

Sensasiwangi.id is a digital platform elevating local Indonesian fragrance products (perfumes, aromatherapy, home fragrances) to the national market through Nusantara storytelling. The platform consists of three core components:

1. **Marketplace** - Curated product showcase for local fragrance brands with local identity, distinctive packaging, and stories behind each scent
2. **Nusantarum** - Editorial channel with articles, guides, and olfactory story curation that educates consumers while driving traffic to pilot brands
3. **User & Brand Profiles** - Trust-building space displaying artisan credentials, BPOM/halal certifications, and managing consumer aroma preferences

The MVP validates three key hypotheses:
- Nusantarum stories can drive visitors to product listings
- Order automation reduces operational effort by ≥30%
- Curated brand profiles increase inquiry conversion

**Tech Stack**: FastAPI (Python 3.11), Supabase (PostgreSQL 15), Server-Side Rendering (Jinja2 + HTMX), Glassmorphism UI theme

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

### October 2025 - UI/UX Audit & Security Fixes

**Security Improvements:**
- Fixed critical HTMX integrity error by upgrading to v2.0.7 with proper SRI hash protection (sha384-ZBXiYtYQ6hJ2Y0ZNoYuI+Nq5MqWBr+chMrS/RkXpNzQCApHEhOt2aY8EJgqwHLkJ)
- Using jsDelivr CDN with crossorigin attribute for secure resource loading

**Dashboard UX Enhancements:**
- **Brand Owner Dashboard**: Improved action button labels ("Kelola Produk", "Buat Kampanye", "Kelola Tim") with better navigation flow
- **Moderation Dashboard**: Added approve/reject/revision controls to brand verification workflow with informative status alerts
- All interactive elements now properly render with working HTMX integration

**Verified Functional Components:**
- Onboarding workflow (3-step wizard: register → verify → profile) fully operational
- Authentication pages (login, signup) working correctly
- Dashboard rendering and navigation functional

**Known Gaps Requiring Future Development:**
- Product creation forms and API integration (backend routes needed)
- Campaign creation forms and modal UIs (backend routes needed)
- Team member invitation workflow (modal/form implementation needed)
- Moderation API integration for approve/reject actions (backend endpoints needed)

## System Architecture

### Backend Framework
- **FastAPI** async application with modular monolith pattern
- **SQLAlchemy 2.0** AsyncSession ORM with Pydantic v2 schemas
- **Dependency injection** for service layer and database sessions
- **Alembic** for database migrations with versioning scripts

### Frontend Approach
- **Server-Side Rendering (SSR)** using Jinja2 templates
- **HTMX** for progressive enhancement (partial updates, form submissions, pagination)
- **Glassmorphism** design system inspired by glass perfume bottles
- **Mobile-first** responsive design with fallback HTML

### Authentication & Security
- **Supabase Auth** for email + magic link authentication
- **bcrypt** password hashing (cost factor 12) with SHA-256 fallback
- **Rate limiting** on critical endpoints (slowapi)
- **Session middleware** with 30-day encrypted cookies
- **Audit logging** for auth and order operations

### Core Features

#### Product Catalog
- Products table with marketplace and Sambatan (group-buy) modes
- Marketplace listings with stock management and inventory adjustments
- Product variants, images, and history tracking
- Four-category tabs (Perfume, Raw Materials, Tools, Other) with search and filtering

#### Order Management
- Complete order lifecycle (draft → paid → shipped → completed)
- Order items with channel differentiation (marketplace vs sambatan)
- Shipping address integration with RajaOngkir API
- Status history tracking and inventory reservation
- Atomic stock operations using database functions

#### Shopping Cart
- Session-based cart storage
- Add/remove/update items with quantity validation
- Cart total calculation
- Automatic clearing after checkout

#### Sambatan (Group-Buy)
- Campaign management with slot-based participation
- Automated lifecycle states (INACTIVE → ACTIVE → FULL → COMPLETED/FAILED)
- Participant tracking with payment status
- Deadline monitoring and automated refunds/payouts
- Background scheduler (APScheduler) for lifecycle management
- Audit logs and transaction history

#### Brand Management
- Brand profiles as store showcases
- Multi-member support (owner, admin, contributor)
- Brand verification workflow
- Product catalog and certification display
- Integration with Nusantarum content

#### Nusantarum Editorial
- Three-tab structure (Perfume, Brand, Perfumer)
- Content curation with verification status
- Optional linking to products/brands/perfumers
- Filter panels and text search per tab
- Hero highlights and article management

### Data Layer

#### Database (Supabase/PostgreSQL 15)
- **12 active tables** including products, orders, brands, Sambatan campaigns, Nusantarum content
- **Row-Level Security (RLS)** for access control
- **Triggers and functions** for automated updates (progress calculation, status transitions)
- **Atomic operations** via stored procedures (reserve_stock, release_stock, complete_sambatan_campaign)
- **Views** for performance (marketplace snapshots, directory aggregations)

#### Database Helper Functions
- `reserve_stock()` / `release_stock()` - Thread-safe inventory operations with SELECT FOR UPDATE
- `check_sambatan_deadlines()` - Batch deadline processing
- `trigger_update_sambatan_progress` - Auto-calculate campaign progress
- `complete_sambatan_campaign()` / `fail_sambatan_campaign()` - Lifecycle automation

#### Schema Patterns
- Enum types for statuses (order_status, sambatan_status, payment_status, etc.)
- Audit tables for tracking changes (order_status_history, sambatan_audit_logs)
- Relationship tables (brand_members, product_perfumers, user_follows)
- Address standardization following RajaOngkir fields (province_id, city_id, subdistrict_id)

### Background Processing
- **SambatanScheduler** running every 5 minutes via APScheduler
- Deadline checks and automatic campaign completion/failure
- Refund and payout processing
- Email reminders (logged, not sent in MVP)
- Graceful startup/shutdown with FastAPI lifespan events

### Testing Infrastructure
- **pytest** with async support and coverage reporting
- **FakeSupabaseClient** mock for testing without real database
- **FakeSupabaseTable/Result** mocks with RPC handler support
- 69 passing tests covering auth, onboarding, Sambatan, Nusantarum, profiles

### Deployment
- **Vercel** serverless deployment using Mangum ASGI adapter
- **Gunicorn + Uvicorn workers** as fallback for VM/container deployment
- **Blue-green strategy** with reversible Alembic migrations
- **CI/CD** with linting (Ruff, Black) and test coverage gates

## External Dependencies

### Required Services
1. **Supabase** (managed PostgreSQL + Auth + Storage)
   - Primary database (15+ tables, views, functions)
   - Row-level security and role-based access
   - File storage for product images and article assets (5MB limit per file)
   - Environment variables: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`

2. **RajaOngkir API** (shipping cost calculation)
   - Province, city, subdistrict data
   - Shipping cost estimates for checkout
   - Environment variable: `RAJAONGKIR_API_KEY`
   - Documentation: `docs/RajaOngkir-API-Integration-Deep-Dive.md`

### Optional Services
- **Email provider** (for verification emails, currently logged only)
- **APM/Sentry** (monitoring, planned post-MVP)
- **CDN** (Supabase Storage includes CDN for static assets)

### Python Packages
- **Core**: fastapi, uvicorn[standard], jinja2, python-multipart, aiofiles, httpx
- **Data**: supabase, pydantic-settings, email-validator
- **Security**: bcrypt, slowapi
- **Scheduling**: apscheduler
- **Deployment**: mangum (ASGI adapter for serverless)

### Frontend Libraries
- **HTMX** for progressive enhancement
- **Feather Icons** / **Phosphor Icons** for UI elements
- **Google Fonts** (Playfair Display + Inter) for typography
- No heavy JavaScript frameworks - focus on SSR with light enhancements

### Development Tools
- **Alembic** for database migrations
- **pytest** for testing with coverage
- **Ruff** and **Black** for linting and formatting
- **Supabase CLI** for migration management
- **Vercel CLI** for deployment
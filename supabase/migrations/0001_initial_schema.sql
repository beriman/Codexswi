-- Initial schema for Sensasiwangi.id MVP on Supabase
-- This migration covers core marketplace, Sambatan, onboarding, and content modules.

set check_function_bodies = off;
set search_path = public;

-- Ensure useful extensions are available
create extension if not exists "pgcrypto" with schema public;
create extension if not exists "citext" with schema public;

-- Enumerated types ---------------------------------------------------------

DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'onboarding_status') THEN
    CREATE TYPE onboarding_status AS ENUM ('registered', 'email_verified', 'profile_completed');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'brand_status') THEN
    CREATE TYPE brand_status AS ENUM ('draft', 'review', 'active', 'suspended');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'brand_member_role') THEN
    CREATE TYPE brand_member_role AS ENUM ('owner', 'admin', 'contributor');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_status') THEN
    CREATE TYPE product_status AS ENUM ('draft', 'active', 'inactive', 'archived');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status') THEN
    CREATE TYPE order_status AS ENUM (
    'draft',
    'awaiting_payment',
    'paid',
    'processing',
    'shipped',
    'delivered',
    'completed',
    'cancelled'
);
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
    CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'refunded', 'partial_refund', 'failed');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sambatan_status') THEN
    CREATE TYPE sambatan_status AS ENUM ('draft', 'scheduled', 'active', 'locked', 'fulfilled', 'expired', 'cancelled');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sambatan_participant_status') THEN
    CREATE TYPE sambatan_participant_status AS ENUM ('pending_payment', 'confirmed', 'cancelled', 'refunded', 'fulfilled');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sambatan_transaction_type') THEN
    CREATE TYPE sambatan_transaction_type AS ENUM ('payment', 'payout', 'refund', 'adjustment');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'article_status') THEN
    CREATE TYPE article_status AS ENUM ('draft', 'review', 'published', 'archived');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'article_category') THEN
    CREATE TYPE article_category AS ENUM ('parfum', 'brand', 'perfumer');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'marketplace_listing_status') THEN
    CREATE TYPE marketplace_listing_status AS ENUM ('draft', 'preview', 'published', 'paused', 'archived');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_channel') THEN
    CREATE TYPE order_channel AS ENUM ('marketplace', 'sambatan', 'mixed');
  END IF;
END $$;
DO $$ 
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inventory_adjustment_reason') THEN
    CREATE TYPE inventory_adjustment_reason AS ENUM (
    'manual',
    'order_reservation',
    'order_release',
    'restock',
    'correction'
);
  END IF;
END $$;

-- Utility function to maintain updated_at columns
create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

-- Core user tables ---------------------------------------------------------

create table if not exists user_profiles (
    id uuid primary key default gen_random_uuid(),
    auth_user_id uuid unique,
    email citext not null unique,
    full_name text not null,
    phone_number text,
    preferred_aroma text,
    onboarding_status onboarding_status not null default 'registered',
    marketing_opt_in boolean not null default false,
    avatar_url text,
    last_login_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_user_profiles
before update on user_profiles
for each row execute function set_updated_at();

create table if not exists auth_accounts (
    id uuid primary key default gen_random_uuid(),
    email citext not null unique,
    password_hash text not null,
    full_name text not null,
    status text not null default 'active',
    last_login_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_auth_accounts
before update on auth_accounts
for each row execute function set_updated_at();

create table if not exists auth_sessions (
    id uuid primary key default gen_random_uuid(),
    account_id uuid not null references auth_accounts(id) on delete cascade,
    session_token text not null unique,
    ip_address text,
    user_agent text,
    created_at timestamptz not null default timezone('utc', now()),
    expires_at timestamptz not null
);

create index if not exists idx_auth_sessions_account_expires
    on auth_sessions (account_id, expires_at desc);

create table if not exists onboarding_registrations (
    id uuid primary key default gen_random_uuid(),
    email citext not null unique,
    full_name text not null,
    password_hash text,
    status onboarding_status not null default 'registered',
    verification_token text,
    verification_sent_at timestamptz,
    verification_expires_at timestamptz,
    verification_attempts integer not null default 0,
    marketing_opt_in boolean not null default false,
    profile_snapshot jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_onboarding_registrations
before update on onboarding_registrations
for each row execute function set_updated_at();

create table if not exists onboarding_events (
    id bigint generated by default as identity primary key,
    onboarding_id uuid not null references onboarding_registrations(id) on delete cascade,
    event text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_onboarding_events_onboarding_id_created_at
    on onboarding_events (onboarding_id, created_at desc);

-- Brand and merchant domain ------------------------------------------------

create table if not exists brands (
    id uuid primary key default gen_random_uuid(),
    slug text not null,
    name text not null,
    tagline text,
    description text,
    story_highlights text,
    logo_path text,
    banner_path text,
    status brand_status not null default 'draft',
    is_featured boolean not null default false,
    created_by uuid references user_profiles(id),
    reviewed_by uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    published_at timestamptz,
    review_notes text,
    constraint brands_slug_key unique (slug)
);

create trigger set_updated_at_brands
before update on brands
for each row execute function set_updated_at();

create table if not exists brand_members (
    brand_id uuid not null references brands(id) on delete cascade,
    profile_id uuid not null references user_profiles(id) on delete cascade,
    role brand_member_role not null,
    invitation_status text not null default 'pending',
    invited_at timestamptz not null default timezone('utc', now()),
    joined_at timestamptz,
    removed_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    primary key (brand_id, profile_id)
);

create index if not exists idx_brand_members_profile_role on brand_members (profile_id, role);

create table if not exists brand_addresses (
    id uuid primary key default gen_random_uuid(),
    brand_id uuid not null references brands(id) on delete cascade,
    label text,
    contact_name text,
    contact_phone text,
    province_id text,
    province_name text,
    city_id text,
    city_name text,
    subdistrict_id text,
    subdistrict_name text,
    postal_code text,
    address_line text not null,
    additional_info text,
    is_primary boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_brand_addresses
before update on brand_addresses
for each row execute function set_updated_at();

-- Product catalog ----------------------------------------------------------

create table if not exists product_categories (
    id serial primary key,
    slug text not null unique,
    name text not null,
    description text,
    sort_order integer not null default 0,
    is_active boolean not null default true,
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    brand_id uuid not null references brands(id) on delete cascade,
    slug text not null,
    name text not null,
    short_description text,
    description text,
    highlight_aroma text,
    aroma_notes jsonb not null default '[]'::jsonb,
    tags text[],
    sku text,
    price_currency text not null default 'IDR',
    price_low numeric(12,2) not null default 0,
    price_high numeric(12,2),
    stock integer,
    status product_status not null default 'draft',
    is_active boolean not null default false,
    marketplace_enabled boolean not null default false,
    sambatan_enabled boolean not null default false,
    weight_grams integer,
    dimension_length_cm numeric(6,2),
    dimension_width_cm numeric(6,2),
    dimension_height_cm numeric(6,2),
    shipping_lead_time_days integer,
    metadata jsonb not null default '{}'::jsonb,
    views_count integer not null default 0,
    favorites_count integer not null default 0,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    published_at timestamptz,
    archived_at timestamptz,
    constraint products_brand_slug_key unique (brand_id, slug)
);

create trigger set_updated_at_products
before update on products
for each row execute function set_updated_at();

create index if not exists idx_products_brand_status on products (brand_id, status);
create index if not exists idx_products_marketplace_enabled on products (marketplace_enabled) where marketplace_enabled;
create index if not exists idx_products_sambatan_enabled on products (sambatan_enabled) where sambatan_enabled;

create table if not exists marketplace_listings (
    product_id uuid primary key references products(id) on delete cascade,
    status marketplace_listing_status not null default 'draft',
    list_price numeric(12,2) not null,
    compare_at_price numeric(12,2),
    stock_on_hand integer not null default 0,
    stock_reserved integer not null default 0,
    allow_backorder boolean not null default false,
    minimum_order_quantity integer not null default 1,
    maximum_order_quantity integer,
    purchase_limit_per_customer integer,
    shipping_profile jsonb not null default '{}'::jsonb,
    sales_channel text not null default 'online',
    published_at timestamptz,
    unpublished_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_marketplace_listings
before update on marketplace_listings
for each row execute function set_updated_at();

create index if not exists idx_marketplace_listings_status on marketplace_listings (status);
create index if not exists idx_marketplace_listings_channel on marketplace_listings (sales_channel);

create table if not exists product_category_links (
    product_id uuid not null references products(id) on delete cascade,
    category_id integer not null references product_categories(id) on delete cascade,
    primary key (product_id, category_id)
);

create table if not exists product_variants (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    name text not null,
    sku text,
    price numeric(12,2),
    stock integer,
    attributes jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_product_variants
before update on product_variants
for each row execute function set_updated_at();

create table if not exists product_images (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    file_path text not null,
    alt_text text,
    is_primary boolean not null default false,
    position integer not null default 0,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_product_images_product_position on product_images (product_id, position);

create table if not exists product_history (
    id bigint generated by default as identity primary key,
    product_id uuid not null references products(id) on delete cascade,
    status product_status,
    marketplace_status marketplace_listing_status,
    sambatan_status sambatan_status,
    marketplace_enabled boolean,
    sambatan_enabled boolean,
    note text,
    actor_id uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now())
);

-- User favourites ----------------------------------------------------------

create table if not exists user_product_favourites (
    profile_id uuid not null references user_profiles(id) on delete cascade,
    product_id uuid not null references products(id) on delete cascade,
    created_at timestamptz not null default timezone('utc', now()),
    primary key (profile_id, product_id)
);

-- Customer addresses -------------------------------------------------------

create table if not exists user_addresses (
    id uuid primary key default gen_random_uuid(),
    profile_id uuid not null references user_profiles(id) on delete cascade,
    label text,
    recipient_name text not null,
    phone_number text not null,
    province_id text,
    province_name text,
    city_id text,
    city_name text,
    subdistrict_id text,
    subdistrict_name text,
    postal_code text,
    address_line text not null,
    additional_info text,
    is_default boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_user_addresses
before update on user_addresses
for each row execute function set_updated_at();

create index if not exists idx_user_addresses_profile_default on user_addresses (profile_id, is_default);

-- Orders and fulfilment ----------------------------------------------------

create table if not exists orders (
    id uuid primary key default gen_random_uuid(),
    order_number text not null unique,
    customer_id uuid references user_profiles(id),
    channel order_channel not null default 'marketplace',
    status order_status not null default 'draft',
    payment_status payment_status not null default 'pending',
    subtotal_amount numeric(12,2) not null default 0,
    shipping_amount numeric(12,2) not null default 0,
    discount_amount numeric(12,2) not null default 0,
    total_amount numeric(12,2) not null default 0,
    notes text,
    metadata jsonb not null default '{}'::jsonb,
    placed_at timestamptz,
    paid_at timestamptz,
    fulfilled_at timestamptz,
    completed_at timestamptz,
    cancelled_at timestamptz,
    cancellation_reason text,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_orders
before update on orders
for each row execute function set_updated_at();

create index if not exists idx_orders_customer_status on orders (customer_id, status);
create index if not exists idx_orders_channel_status on orders (channel, status);
create index if not exists idx_orders_created_at on orders (created_at desc);

create table if not exists order_shipping_addresses (
    order_id uuid primary key references orders(id) on delete cascade,
    recipient_name text not null,
    phone_number text not null,
    province_id text,
    province_name text,
    city_id text,
    city_name text,
    subdistrict_id text,
    subdistrict_name text,
    postal_code text,
    address_line text not null,
    additional_info text,
    created_at timestamptz not null default timezone('utc', now())
);

-- Sambatan (group-buy) domain ----------------------------------------------

create table if not exists sambatan_campaigns (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    slug text,
    title text,
    status sambatan_status not null default 'draft',
    total_slots integer not null,
    filled_slots integer not null default 0,
    slot_price numeric(12,2) not null,
    minimum_slots integer,
    maximum_slots integer,
    deadline timestamptz,
    locked_at timestamptz,
    fulfilled_at timestamptz,
    cancelled_at timestamptz,
    progress numeric(5,2) default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint uq_sambatan_campaigns_product unique (product_id)
);

create trigger set_updated_at_sambatan_campaigns
before update on sambatan_campaigns
for each row execute function set_updated_at();

create index if not exists idx_sambatan_campaigns_status on sambatan_campaigns (status);
create index if not exists idx_sambatan_campaigns_deadline on sambatan_campaigns (deadline) where deadline is not null;

create table if not exists order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references orders(id) on delete cascade,
    product_id uuid references products(id),
    variant_id uuid references product_variants(id),
    campaign_id uuid references sambatan_campaigns(id),
    channel order_channel not null default 'marketplace',
    product_name text not null,
    brand_name text,
    sku text,
    unit_price numeric(12,2) not null,
    quantity integer not null default 1,
    sambatan_slot_count integer,
    sambatan_deadline_snapshot timestamptz,
    subtotal_amount numeric(12,2) not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now()),
    constraint chk_order_items_channel_campaign
        check (
            (channel = 'sambatan' and campaign_id is not null and sambatan_slot_count is not null)
            or (channel <> 'sambatan' and campaign_id is null)
        )
);

create index if not exists idx_order_items_order on order_items (order_id);
create index if not exists idx_order_items_campaign on order_items (campaign_id) where campaign_id is not null;

create table if not exists order_status_history (
    id bigint generated by default as identity primary key,
    order_id uuid not null references orders(id) on delete cascade,
    status order_status not null,
    payment_status payment_status,
    note text,
    actor_id uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_order_status_history_order_created on order_status_history (order_id, created_at desc);

create table if not exists marketplace_inventory_adjustments (
    id uuid primary key default gen_random_uuid(),
    product_id uuid not null references products(id) on delete cascade,
    variant_id uuid references product_variants(id) on delete set null,
    adjustment integer not null,
    reason inventory_adjustment_reason not null default 'manual',
    reference_order_id uuid references orders(id) on delete set null,
    actor_id uuid references user_profiles(id),
    note text,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_marketplace_inventory_product on marketplace_inventory_adjustments (product_id, created_at desc);

create table if not exists sambatan_participants (
    id uuid primary key default gen_random_uuid(),
    campaign_id uuid not null references sambatan_campaigns(id) on delete cascade,
    profile_id uuid references user_profiles(id),
    order_id uuid references orders(id),
    slot_count integer not null default 1,
    contribution_amount numeric(12,2) not null,
    status sambatan_participant_status not null default 'pending_payment',
    joined_at timestamptz not null default timezone('utc', now()),
    confirmed_at timestamptz,
    cancelled_at timestamptz,
    notes text
);

create index if not exists idx_sambatan_participants_campaign_status on sambatan_participants (campaign_id, status);
create index if not exists idx_sambatan_participants_profile on sambatan_participants (profile_id);

create table if not exists sambatan_transactions (
    id bigint generated by default as identity primary key,
    participant_id uuid not null references sambatan_participants(id) on delete cascade,
    transaction_type sambatan_transaction_type not null,
    amount numeric(12,2) not null,
    reference_id text,
    notes text,
    actor_id uuid references user_profiles(id),
    recorded_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_sambatan_transactions_participant on sambatan_transactions (participant_id, recorded_at desc);

create table if not exists sambatan_audit_logs (
    id bigint generated by default as identity primary key,
    campaign_id uuid not null references sambatan_campaigns(id) on delete cascade,
    event text not null,
    metadata jsonb not null default '{}'::jsonb,
    actor_id uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_sambatan_audit_logs_campaign on sambatan_audit_logs (campaign_id, created_at desc);

create table if not exists sambatan_lifecycle_states (
    id bigint generated by default as identity primary key,
    campaign_id uuid not null references sambatan_campaigns(id) on delete cascade,
    status sambatan_status not null,
    note text,
    actor_id uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_sambatan_lifecycle_campaign on sambatan_lifecycle_states (campaign_id, created_at desc);

-- Nusantarum curated content -----------------------------------------------

create table if not exists nusantarum_articles (
    id uuid primary key default gen_random_uuid(),
    slug text not null unique,
    title text not null,
    summary text,
    content text,
    category article_category not null,
    status article_status not null default 'draft',
    hero_image_path text,
    highlight_quote text,
    reading_duration_minutes integer,
    tags text[],
    brand_id uuid references brands(id),
    product_id uuid references products(id),
    curated_by uuid references user_profiles(id),
    perfumer_name text,
    published_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create trigger set_updated_at_nusantarum_articles
before update on nusantarum_articles
for each row execute function set_updated_at();

create index if not exists idx_nusantarum_articles_category_status on nusantarum_articles (category, status);
create index if not exists idx_nusantarum_articles_brand_product on nusantarum_articles (brand_id, product_id);

create table if not exists nusantarum_article_links (
    id uuid primary key default gen_random_uuid(),
    article_id uuid not null references nusantarum_articles(id) on delete cascade,
    related_brand_id uuid references brands(id) on delete cascade,
    related_product_id uuid references products(id) on delete cascade,
    relation_type text not null,
    created_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists uq_nusantarum_article_links_relation
    on nusantarum_article_links (article_id, relation_type, coalesce(related_brand_id::text, ''), coalesce(related_product_id::text, ''));

-- Seed baseline categories -------------------------------------------------
insert into product_categories (slug, name, sort_order)
values
    ('parfum', 'Parfum', 1),
    ('raw-material', 'Raw Material', 2),
    ('tools', 'Tools', 3),
    ('lainnya', 'Lainnya', 4)
on conflict (slug) do nothing;

-- Helpful materialized view for Sambatan dashboard ------------------------
create or replace view sambatan_dashboard_summary as
select
    c.id as campaign_id,
    c.product_id,
    p.name,
    p.brand_id,
    c.total_slots,
    c.filled_slots,
    c.deadline,
    c.status as sambatan_status,
    c.progress,
    coalesce(sum(sp.slot_count), 0) as slots_claimed,
    coalesce(sum(case when sp.status = 'confirmed' then sp.slot_count else 0 end), 0) as slots_confirmed,
    coalesce(sum(sp.contribution_amount), 0) as total_contribution,
    max(sp.joined_at) as last_joined_at
from sambatan_campaigns c
join products p on p.id = c.product_id
left join sambatan_participants sp on sp.campaign_id = c.id
group by c.id, p.id;


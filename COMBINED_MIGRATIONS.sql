-- Combined Migrations for Supabase
-- Generated automatically
-- Project: yguckgrnvzvbxtygbzke
--



-- ========================================
-- Migration: 0001_initial_schema.sql
-- ========================================

-- Initial schema for Sensasiwangi.id MVP on Supabase
-- This migration covers core marketplace, Sambatan, onboarding, and content modules.

set check_function_bodies = off;
set search_path = public;

-- Ensure useful extensions are available
create extension if not exists "pgcrypto" with schema public;
create extension if not exists "citext" with schema public;

-- Enumerated types ---------------------------------------------------------

create type if not exists onboarding_status as enum ('registered', 'email_verified', 'profile_completed');
create type if not exists brand_status as enum ('draft', 'review', 'active', 'suspended');
create type if not exists brand_member_role as enum ('owner', 'admin', 'contributor');
create type if not exists product_status as enum ('draft', 'active', 'inactive', 'archived');
create type if not exists order_status as enum (
    'draft',
    'awaiting_payment',
    'paid',
    'processing',
    'shipped',
    'delivered',
    'completed',
    'cancelled'
);
create type if not exists payment_status as enum ('pending', 'paid', 'refunded', 'partial_refund', 'failed');
create type if not exists sambatan_status as enum ('draft', 'scheduled', 'active', 'locked', 'fulfilled', 'expired', 'cancelled');
create type if not exists sambatan_participant_status as enum ('pending_payment', 'confirmed', 'cancelled', 'refunded', 'fulfilled');
create type if not exists sambatan_transaction_type as enum ('payment', 'payout', 'refund', 'adjustment');
create type if not exists article_status as enum ('draft', 'review', 'published', 'archived');
create type if not exists article_category as enum ('parfum', 'brand', 'perfumer');
create type if not exists marketplace_listing_status as enum ('draft', 'preview', 'published', 'paused', 'archived');
create type if not exists order_channel as enum ('marketplace', 'sambatan', 'mixed');
create type if not exists inventory_adjustment_reason as enum (
    'manual',
    'order_reservation',
    'order_release',
    'restock',
    'correction'
);

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




-- ========================================
-- Migration: 0002_profile_social_graph.sql
-- ========================================

-- Profile social graph, perfumer tagging, and brand summary expansion
-- Implements the schema additions required by docs/user-profile-feature-plan.md

set check_function_bodies = off;
set search_path = public;

-- ---------------------------------------------------------------------------
-- User follow relationships
-- ---------------------------------------------------------------------------

create table if not exists user_follows (
    follower_id uuid references user_profiles(id) on delete cascade,
    following_id uuid references user_profiles(id) on delete cascade,
    created_at timestamptz default timezone('utc', now()),
    constraint user_follows_pkey primary key (follower_id, following_id),
    constraint user_follows_no_self_follow check (follower_id <> following_id)
);

create index if not exists idx_user_follows_following on user_follows (following_id);
create index if not exists idx_user_follows_follower on user_follows (follower_id);

-- ---------------------------------------------------------------------------
-- Perfumer tagging for marketplace products
-- ---------------------------------------------------------------------------

create table if not exists product_perfumers (
    product_id uuid not null references products(id) on delete cascade,
    perfumer_profile_id uuid not null references user_profiles(id) on delete cascade,
    role text default 'lead',
    assigned_by uuid references user_profiles(id),
    assigned_at timestamptz default timezone('utc', now()),
    notes text,
    constraint product_perfumers_pkey primary key (product_id, perfumer_profile_id)
);

-- ---------------------------------------------------------------------------
-- Brand ownership summary view for quick profile lookups
-- ---------------------------------------------------------------------------

create or replace view profile_brand_summary as
select
    bm.profile_id,
    b.id as brand_id,
    b.name,
    b.slug,
    b.logo_path,
    bm.role,
    b.status,
    b.tagline
from brand_members bm
join brands b on b.id = bm.brand_id
where bm.role in ('owner', 'admin');

-- ---------------------------------------------------------------------------
-- Profile aggregated statistics to speed up SSR rendering
-- ---------------------------------------------------------------------------

create or replace view user_profile_stats as
select
    p.id as profile_id,
    count(distinct f.following_id) filter (where f.follower_id = p.id) as following_count,
    count(distinct f.follower_id) filter (where f.following_id = p.id) as follower_count,
    count(distinct pp.product_id) as perfumer_product_count,
    count(distinct case when bm.role = 'owner' then bm.brand_id end) as owned_brand_count
from user_profiles p
left join user_follows f on f.follower_id = p.id or f.following_id = p.id
left join product_perfumers pp on pp.perfumer_profile_id = p.id
left join brand_members bm on bm.profile_id = p.id
group by p.id;

-- End of migration ----------------------------------------------------------



-- ========================================
-- Migration: 0003_nusantarum_schema.sql
-- ========================================

-- Nusantarum data model, marketplace integration, and profile linkage
-- Implements docs/nusantarum-implementation-plan.md foundation

set check_function_bodies = off;
set search_path = public;

-- ---------------------------------------------------------------------------
-- Brand enrichment for Nusantarum directory
-- ---------------------------------------------------------------------------

alter table brands
    add column if not exists nusantarum_status text not null default 'draft',
    add column if not exists is_verified boolean not null default false,
    add column if not exists brand_profile_id uuid references user_profiles(id);

alter table user_profiles
    add column if not exists username citext unique;

-- ---------------------------------------------------------------------------
-- Core Nusantarum entities
-- ---------------------------------------------------------------------------

create table if not exists perfumers (
    id uuid primary key default gen_random_uuid(),
    slug text not null,
    display_name text not null,
    biography text,
    signature_scent text,
    website_url text,
    instagram_handle text,
    perfumer_profile_id uuid references user_profiles(id),
    is_featured boolean not null default false,
    is_verified boolean not null default false,
    is_linked_to_active_perfume boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint perfumers_slug_key unique (slug)
);

create trigger set_updated_at_perfumers
    before update on perfumers
    for each row execute function set_updated_at();

create table if not exists parfums (
    id uuid primary key default gen_random_uuid(),
    slug text not null,
    name text not null,
    description text,
    hero_note text,
    aroma_families text[] not null default '{}'::text[],
    accords jsonb not null default '[]'::jsonb,
    release_year integer,
    price_reference numeric(12,2),
    price_currency text not null default 'IDR',
    marketplace_rating numeric(4,2),
    base_image_url text,
    brand_id uuid not null references brands(id) on delete cascade,
    perfumer_id uuid references perfumers(id) on delete set null,
    marketplace_product_id uuid references products(id) on delete set null,
    is_active boolean not null default true,
    is_displayable boolean not null default false,
    sync_source text not null default 'manual',
    sync_status text default 'pending',
    synced_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint parfums_slug_key unique (slug)
);

create trigger set_updated_at_parfums
    before update on parfums
    for each row execute function set_updated_at();

create table if not exists perfume_notes (
    id bigserial primary key,
    parfum_id uuid not null references parfums(id) on delete cascade,
    note_type text not null check (note_type in ('top', 'middle', 'base')),
    note text not null,
    position integer not null default 0
);

create table if not exists perfume_assets (
    id uuid primary key default gen_random_uuid(),
    parfum_id uuid not null references parfums(id) on delete cascade,
    asset_type text not null default 'image',
    file_path text not null,
    alt_text text,
    metadata jsonb not null default '{}'::jsonb,
    position integer not null default 0,
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists parfum_audits (
    id bigserial primary key,
    parfum_id uuid,
    action text not null,
    payload jsonb not null,
    actor_id uuid references user_profiles(id),
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists nusantarum_sync_logs (
    id bigserial primary key,
    source text not null,
    status text not null,
    summary text,
    payload jsonb not null default '{}'::jsonb,
    run_by uuid references user_profiles(id),
    run_at timestamptz not null default timezone('utc', now())
);

-- ---------------------------------------------------------------------------
-- Helper functions and triggers
-- ---------------------------------------------------------------------------

create or replace function set_parfum_displayable()
returns trigger
language plpgsql
as $$
declare
    brand_verified boolean := false;
begin
    select coalesce(is_verified, false)
      into brand_verified
      from brands
     where id = new.brand_id;

    new.is_displayable := coalesce(new.is_active, false) and brand_verified;
    return new;
end;
$$;

create trigger parfums_displayable_guard
    before insert or update on parfums
    for each row execute function set_parfum_displayable();

create or replace function maintain_parfum_displayable_from_brand()
returns trigger
language plpgsql
as $$
begin
    update parfums
       set is_displayable = (new.is_verified and parfums.is_active)
     where brand_id = new.id;
    return new;
end;
$$;

create trigger parfums_brand_displayable
    after update of is_verified on brands
    for each row execute function maintain_parfum_displayable_from_brand();

create or replace function update_perfumer_link_flag(perfumer uuid)
returns void
language plpgsql
as $$
begin
    update perfumers p
       set is_linked_to_active_perfume = exists (
            select 1
              from parfums pf
              join brands b on b.id = pf.brand_id
             where pf.perfumer_id = p.id
               and pf.is_active
               and b.is_verified
        )
     where p.id = perfumer;
end;
$$;

create or replace function refresh_perfumer_link()
returns trigger
language plpgsql
as $$
begin
    if tg_op = 'DELETE' then
        if old.perfumer_id is not null then
            perform update_perfumer_link_flag(old.perfumer_id);
        end if;
        return old;
    end if;

    if new.perfumer_id is not null then
        perform update_perfumer_link_flag(new.perfumer_id);
    end if;

    if tg_op = 'UPDATE' and old.perfumer_id is distinct from new.perfumer_id and old.perfumer_id is not null then
        perform update_perfumer_link_flag(old.perfumer_id);
    end if;

    return new;
end;
$$;

create trigger parfums_perfumer_link_refresh
    after insert or update or delete on parfums
    for each row execute function refresh_perfumer_link();

create or replace function log_parfum_audit()
returns trigger
language plpgsql
as $$
declare
    actor uuid;
begin
    begin
        actor := nullif(current_setting('app.current_actor', true), '')::uuid;
    exception when others then
        actor := null;
    end;

    if tg_op = 'DELETE' then
        insert into parfum_audits(parfum_id, action, payload, actor_id)
        values (old.id, tg_op, to_jsonb(old), actor);
        return old;
    else
        insert into parfum_audits(parfum_id, action, payload, actor_id)
        values (new.id, tg_op, to_jsonb(new), actor);
        return new;
    end if;
end;
$$;

create trigger parfums_audit_log
    after insert or update or delete on parfums
    for each row execute function log_parfum_audit();

-- ---------------------------------------------------------------------------
-- Marketplace and profile driven views
-- ---------------------------------------------------------------------------

create or replace view marketplace_product_snapshot as
select
    p.id as product_id,
    p.brand_id,
    p.name,
    p.slug,
    p.highlight_aroma,
    p.price_currency,
    coalesce(ml.list_price, p.price_low) as list_price,
    ml.compare_at_price,
    ml.stock_on_hand,
    ml.stock_reserved,
    ml.status as marketplace_status,
    ml.updated_at as marketplace_updated_at,
    p.updated_at as product_updated_at
from products p
left join marketplace_listings ml on ml.product_id = p.id
where p.marketplace_enabled;

create or replace view perfumer_showcase as
select
    pr.id as perfumer_id,
    pr.slug as perfumer_slug,
    pr.display_name,
    pr.signature_scent,
    pr.is_linked_to_active_perfume,
    pf.id as parfum_id,
    pf.slug as parfum_slug,
    pf.name as parfum_name,
    b.slug as brand_slug,
    b.name as brand_name
from perfumers pr
left join parfums pf on pf.perfumer_id = pr.id and pf.is_active
left join brands b on b.id = pf.brand_id
where b.is_verified;

create or replace view nusantarum_perfume_directory as
select
    pf.id,
    pf.slug,
    pf.name,
    pf.hero_note,
    pf.aroma_families,
    pf.release_year,
    pf.price_reference,
    pf.price_currency,
    pf.marketplace_rating,
    pf.description,
    pf.base_image_url,
    pf.sync_source,
    pf.sync_status,
    pf.synced_at,
    pf.is_displayable,
    pf.is_active,
    pf.updated_at,
    b.id as brand_id,
    b.slug as brand_slug,
    b.name as brand_name,
    b.origin_city as brand_city,
    b.is_verified as brand_is_verified,
    b.nusantarum_status,
    mp.list_price as marketplace_price,
    mp.marketplace_status,
    mp.stock_on_hand,
    mp.marketplace_updated_at,
    pf.marketplace_product_id,
    pr.slug as perfumer_slug,
    pr.display_name as perfumer_name,
    pr.signature_scent,
    pr.is_verified as perfumer_verified,
    pr.is_linked_to_active_perfume,
    up.username as perfumer_profile_username,
    ub.username as brand_profile_username
from parfums pf
join brands b on b.id = pf.brand_id
left join marketplace_product_snapshot mp on mp.product_id = pf.marketplace_product_id
left join perfumers pr on pr.id = pf.perfumer_id
left join user_profiles up on up.id = pr.perfumer_profile_id
left join user_profiles ub on ub.id = b.brand_profile_id
where b.is_verified and pf.is_active;

create or replace view nusantarum_brand_directory as
select
    b.id,
    b.slug,
    b.name,
    b.origin_city,
    b.nusantarum_status,
    b.is_verified,
    b.brand_profile_id,
    ub.username as brand_profile_username,
    coalesce(stats.active_count, 0) as active_perfume_count,
    stats.last_perfume_synced_at
from brands b
left join (
    select
        brand_id,
        count(*) filter (where is_active) as active_count,
        max(synced_at) as last_perfume_synced_at
    from parfums
    where is_displayable
    group by brand_id
) stats on stats.brand_id = b.id
left join user_profiles ub on ub.id = b.brand_profile_id
where b.is_verified;

create or replace view nusantarum_perfumer_directory as
select
    pr.id,
    pr.slug,
    pr.display_name,
    pr.signature_scent,
    pr.is_verified,
    pr.is_linked_to_active_perfume,
    pr.perfumer_profile_id,
    up.username as perfumer_profile_username,
    coalesce(stats.active_perfume_count, 0) as active_perfume_count,
    stats.highlight_perfume,
    stats.highlight_brand,
    stats.last_synced_at
from perfumers pr
left join (
    select
        pf.perfumer_id,
        count(*) filter (where pf.is_active) as active_perfume_count,
        max(pf.synced_at) as last_synced_at,
        max(pf.name) filter (where pf.is_displayable) as highlight_perfume,
        max(b.name) filter (where pf.is_displayable) as highlight_brand
    from parfums pf
    join brands b on b.id = pf.brand_id
    where b.is_verified
    group by pf.perfumer_id
) stats on stats.perfumer_id = pr.id
left join user_profiles up on up.id = pr.perfumer_profile_id
where pr.is_linked_to_active_perfume;

-- ---------------------------------------------------------------------------
-- Row level security for public consumption
-- ---------------------------------------------------------------------------

alter table perfumers enable row level security;
alter table parfums enable row level security;
alter table perfume_notes enable row level security;
alter table perfume_assets enable row level security;
alter table parfum_audits enable row level security;
alter table nusantarum_sync_logs enable row level security;

create policy perfumers_public_read on perfumers for select using (true);
create policy parfums_public_read on parfums for select using (true);
create policy perfume_notes_public_read on perfume_notes for select using (true);
create policy perfume_assets_public_read on perfume_assets for select using (true);

create policy perfumers_curator_write on perfumers for all
    using ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'))
    with check ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'));

create policy parfums_curator_write on parfums for all
    using ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'))
    with check ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'));

create policy perfume_notes_curator_write on perfume_notes for all
    using ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'))
    with check ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'));

create policy perfume_assets_curator_write on perfume_assets for all
    using ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'))
    with check ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'));

create policy parfum_audits_admin_read on parfum_audits for select
    using ((auth.jwt() ->> 'role') in ('admin', 'brand_owner'));

create policy sync_logs_admin_all on nusantarum_sync_logs for all
    using ((auth.jwt() ->> 'role') in ('admin'))
    with check ((auth.jwt() ->> 'role') in ('admin'));

-- ---------------------------------------------------------------------------
-- Supabase helper functions for background workers
-- ---------------------------------------------------------------------------

create or replace function sync_marketplace_products()
returns void
language plpgsql
as $$
begin
    insert into nusantarum_sync_logs(source, status, summary)
    values ('marketplace', 'queued', 'Marketplace product sync triggered');
end;
$$;

create or replace function sync_nusantarum_profiles()
returns void
language plpgsql
as $$
begin
    insert into nusantarum_sync_logs(source, status, summary)
    values ('profiles', 'queued', 'Profile sync triggered');
end;
$$;



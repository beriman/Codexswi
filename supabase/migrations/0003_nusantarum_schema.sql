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


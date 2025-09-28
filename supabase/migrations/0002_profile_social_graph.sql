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

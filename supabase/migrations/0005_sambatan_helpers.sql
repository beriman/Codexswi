-- Helper functions for atomic Sambatan operations
-- Created: 2025-10-05

-- Function to atomically reserve slots in a campaign
CREATE OR REPLACE FUNCTION reserve_sambatan_slots(
    p_campaign_id uuid,
    p_slot_count integer
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_campaign sambatan_campaigns%ROWTYPE;
    v_available_slots integer;
BEGIN
    -- Lock the campaign row for update
    SELECT * INTO v_campaign
    FROM sambatan_campaigns
    WHERE id = p_campaign_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign not found: %', p_campaign_id;
    END IF;
    
    -- Check if campaign is active
    IF v_campaign.status NOT IN ('active', 'scheduled') THEN
        RAISE EXCEPTION 'Campaign is not active';
    END IF;
    
    -- Calculate available slots
    v_available_slots := v_campaign.total_slots - v_campaign.filled_slots;
    
    IF v_available_slots < p_slot_count THEN
        RAISE EXCEPTION 'Insufficient slots: available=%, requested=%', v_available_slots, p_slot_count;
    END IF;
    
    -- Update filled slots
    UPDATE sambatan_campaigns
    SET 
        filled_slots = filled_slots + p_slot_count,
        status = CASE 
            WHEN (filled_slots + p_slot_count) >= total_slots THEN 'locked'
            ELSE status
        END,
        progress = ROUND((filled_slots + p_slot_count)::numeric / total_slots * 100, 2)
    WHERE id = p_campaign_id;
    
    RETURN TRUE;
END;
$$;

-- Function to release slots (e.g., on cancellation)
CREATE OR REPLACE FUNCTION release_sambatan_slots(
    p_campaign_id uuid,
    p_slot_count integer
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE sambatan_campaigns
    SET 
        filled_slots = GREATEST(0, filled_slots - p_slot_count),
        status = CASE
            WHEN status = 'locked' AND (filled_slots - p_slot_count) < total_slots 
                THEN 'active'
            ELSE status
        END,
        progress = ROUND(GREATEST(0, filled_slots - p_slot_count)::numeric / total_slots * 100, 2)
    WHERE id = p_campaign_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign not found: %', p_campaign_id;
    END IF;
    
    RETURN TRUE;
END;
$$;

-- Function to complete a campaign
CREATE OR REPLACE FUNCTION complete_sambatan_campaign(
    p_campaign_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update campaign status
    UPDATE sambatan_campaigns
    SET 
        status = 'fulfilled',
        fulfilled_at = timezone('utc', now())
    WHERE id = p_campaign_id
      AND status IN ('active', 'locked');
    
    -- Confirm all pending participants
    UPDATE sambatan_participants
    SET 
        status = 'confirmed',
        confirmed_at = timezone('utc', now())
    WHERE campaign_id = p_campaign_id
      AND status = 'pending_payment';
    
    RETURN TRUE;
END;
$$;

-- Function to fail/expire a campaign
CREATE OR REPLACE FUNCTION fail_sambatan_campaign(
    p_campaign_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update campaign status
    UPDATE sambatan_campaigns
    SET 
        status = 'expired',
        cancelled_at = timezone('utc', now())
    WHERE id = p_campaign_id
      AND status IN ('active', 'locked');
    
    -- Refund all participants
    UPDATE sambatan_participants
    SET status = 'refunded'
    WHERE campaign_id = p_campaign_id
      AND status IN ('pending_payment', 'confirmed');
    
    RETURN TRUE;
END;
$$;

-- Function to get campaign progress summary
CREATE OR REPLACE FUNCTION get_sambatan_campaign_progress(
    p_campaign_id uuid
)
RETURNS TABLE (
    campaign_id uuid,
    total_slots integer,
    filled_slots integer,
    available_slots integer,
    progress numeric,
    participant_count bigint,
    total_contribution numeric,
    status sambatan_status
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        c.id,
        c.total_slots,
        c.filled_slots,
        c.total_slots - c.filled_slots as available_slots,
        c.progress,
        COUNT(DISTINCT p.id) as participant_count,
        COALESCE(SUM(p.contribution_amount), 0) as total_contribution,
        c.status
    FROM sambatan_campaigns c
    LEFT JOIN sambatan_participants p ON p.campaign_id = c.id
    WHERE c.id = p_campaign_id
    GROUP BY c.id;
$$;

-- Function to check and transition campaigns based on deadline
CREATE OR REPLACE FUNCTION check_sambatan_deadlines()
RETURNS TABLE (
    campaign_id uuid,
    action text,
    old_status sambatan_status,
    new_status sambatan_status
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH updated_campaigns AS (
        UPDATE sambatan_campaigns
        SET 
            status = CASE
                -- Complete if filled or deadline passed with enough slots
                WHEN status = 'locked' THEN 'fulfilled'
                WHEN status = 'active' AND deadline < timezone('utc', now()) 
                     AND filled_slots >= total_slots THEN 'fulfilled'
                -- Fail if deadline passed without enough slots
                WHEN status = 'active' AND deadline < timezone('utc', now()) 
                     AND filled_slots < total_slots THEN 'expired'
                ELSE status
            END,
            fulfilled_at = CASE
                WHEN (status = 'locked' OR 
                     (status = 'active' AND deadline < timezone('utc', now()) 
                      AND filled_slots >= total_slots))
                THEN timezone('utc', now())
                ELSE fulfilled_at
            END,
            cancelled_at = CASE
                WHEN status = 'active' AND deadline < timezone('utc', now()) 
                     AND filled_slots < total_slots
                THEN timezone('utc', now())
                ELSE cancelled_at
            END
        WHERE status IN ('active', 'locked')
          AND (status = 'locked' OR deadline < timezone('utc', now()))
        RETURNING 
            id,
            CASE
                WHEN status = 'fulfilled' THEN 'completed'
                WHEN status = 'expired' THEN 'failed'
                ELSE 'none'
            END as action,
            -- Store old status in metadata before update
            CASE
                WHEN status = 'fulfilled' THEN 'active'::sambatan_status
                WHEN status = 'expired' THEN 'active'::sambatan_status
                ELSE status
            END as old_status,
            status as new_status
    )
    SELECT * FROM updated_campaigns
    WHERE action != 'none';
    
    -- Update participants for failed campaigns
    UPDATE sambatan_participants
    SET status = 'refunded'
    WHERE campaign_id IN (
        SELECT id FROM sambatan_campaigns 
        WHERE status = 'expired'
    )
    AND status IN ('pending_payment', 'confirmed');
    
    -- Confirm participants for completed campaigns
    UPDATE sambatan_participants
    SET 
        status = 'confirmed',
        confirmed_at = timezone('utc', now())
    WHERE campaign_id IN (
        SELECT id FROM sambatan_campaigns 
        WHERE status = 'fulfilled'
    )
    AND status = 'pending_payment';
END;
$$;

-- Create index for deadline checks
CREATE INDEX IF NOT EXISTS idx_sambatan_campaigns_deadline_status
    ON sambatan_campaigns (deadline, status)
    WHERE status IN ('active', 'locked');

-- Add progress calculation trigger
CREATE OR REPLACE FUNCTION update_sambatan_progress()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.progress := CASE 
        WHEN NEW.total_slots > 0 
        THEN ROUND((NEW.filled_slots::numeric / NEW.total_slots) * 100, 2)
        ELSE 0
    END;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_update_sambatan_progress
    BEFORE INSERT OR UPDATE OF filled_slots, total_slots
    ON sambatan_campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_sambatan_progress();

-- Add comment documentation
COMMENT ON FUNCTION reserve_sambatan_slots IS 
    'Atomically reserves slots in a campaign, ensuring thread-safety';

COMMENT ON FUNCTION release_sambatan_slots IS 
    'Releases reserved slots back to the campaign pool';

COMMENT ON FUNCTION complete_sambatan_campaign IS 
    'Marks a campaign as fulfilled and confirms all participants';

COMMENT ON FUNCTION fail_sambatan_campaign IS 
    'Marks a campaign as expired/failed and refunds all participants';

COMMENT ON FUNCTION check_sambatan_deadlines IS 
    'Checks all active campaigns and transitions based on deadline and slot status';

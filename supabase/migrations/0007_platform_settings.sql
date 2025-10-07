-- Platform Settings Table
-- Stores configurable platform settings like bank account and fee rate
-- Single row table (enforced by check constraint)

CREATE TABLE IF NOT EXISTS platform_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Platform Bank Account for settlements
    bank_account_number VARCHAR(50) NOT NULL,
    bank_account_name VARCHAR(255) NOT NULL,
    bank_name VARCHAR(100) NOT NULL DEFAULT 'BRI',
    
    -- Platform Fee Configuration
    platform_fee_rate DECIMAL(5,2) NOT NULL DEFAULT 3.00 CHECK (platform_fee_rate >= 0 AND platform_fee_rate <= 100),
    
    -- Metadata
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),
    
    -- Ensure only one settings row exists
    CONSTRAINT single_row_check CHECK (id = '00000000-0000-0000-0000-000000000001'::UUID)
);

-- Insert default settings (using marketplace account from replit.md)
INSERT INTO platform_settings (
    id,
    bank_account_number,
    bank_account_name,
    bank_name,
    platform_fee_rate
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    '201101000546304',
    'SENSASI WANGI INDONE',
    'BRI',
    3.00
) ON CONFLICT (id) DO NOTHING;

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_platform_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_platform_settings_timestamp
    BEFORE UPDATE ON platform_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_platform_settings_timestamp();

-- Row Level Security
ALTER TABLE platform_settings ENABLE ROW LEVEL SECURITY;

-- Only authenticated users can read settings
CREATE POLICY "Anyone can read platform settings"
    ON platform_settings FOR SELECT
    TO authenticated
    USING (true);

-- Only admins can update settings (will be enforced in application layer)
CREATE POLICY "Service role can update platform settings"
    ON platform_settings FOR UPDATE
    TO service_role
    USING (true);

-- Create index for faster lookups
CREATE INDEX idx_platform_settings_id ON platform_settings(id);

-- Comment for documentation
COMMENT ON TABLE platform_settings IS 'Platform-wide settings including bank account and fee configuration. Single row table.';
COMMENT ON COLUMN platform_settings.platform_fee_rate IS 'Platform fee percentage (e.g., 3.00 for 3%). Range: 0-100';

-- Wallet System and BRI BaaS Integration
-- This migration adds tables and functions for digital wallet with BRI integration

set check_function_bodies = off;
set search_path = public;

-- ============================================================================
-- TABLES
-- ============================================================================

-- User wallets table (linked to BRI BaaS accounts)
CREATE TABLE IF NOT EXISTS user_wallets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES auth_accounts(id) ON DELETE CASCADE UNIQUE NOT NULL,
    
    -- BRI BaaS account info
    bri_account_number varchar(20) UNIQUE,
    bri_customer_id varchar(50),
    
    -- Balance
    balance decimal(15,2) DEFAULT 0 NOT NULL CHECK (balance >= 0),
    currency varchar(3) DEFAULT 'IDR' NOT NULL,
    
    -- Status
    status varchar(20) DEFAULT 'active' NOT NULL,
    kyc_status varchar(20) DEFAULT 'pending' NOT NULL,
    
    -- Timestamps
    created_at timestamptz DEFAULT timezone('utc', now()) NOT NULL,
    updated_at timestamptz DEFAULT timezone('utc', now()) NOT NULL
);

-- Wallet transactions table
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id uuid REFERENCES user_wallets(id) ON DELETE CASCADE NOT NULL,
    
    -- Transaction details
    transaction_type varchar(30) NOT NULL, -- 'topup', 'payment', 'refund', 'transfer_in', 'transfer_out', 'withdrawal', 'fee_revenue', 'payout'
    amount decimal(15,2) NOT NULL,
    balance_before decimal(15,2) NOT NULL,
    balance_after decimal(15,2) NOT NULL,
    
    -- Status
    status varchar(20) DEFAULT 'pending' NOT NULL, -- 'pending', 'completed', 'failed', 'cancelled'
    
    -- Reference to related entities
    reference_type varchar(50), -- 'order', 'sambatan', 'topup', 'transfer'
    reference_id varchar(100),
    
    -- BRI transaction references
    bri_reference varchar(100),
    bri_transaction_id varchar(100),
    
    -- Additional info
    description text,
    metadata jsonb DEFAULT '{}',
    
    -- Timestamps
    created_at timestamptz DEFAULT timezone('utc', now()) NOT NULL,
    updated_at timestamptz DEFAULT timezone('utc', now()) NOT NULL
);

-- Top-up requests table (BRIVA tracking)
CREATE TABLE IF NOT EXISTS wallet_topup_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id uuid REFERENCES user_wallets(id) ON DELETE CASCADE NOT NULL,
    
    -- Top-up details
    amount decimal(15,2) NOT NULL CHECK (amount > 0),
    virtual_account varchar(50) UNIQUE NOT NULL,
    
    -- Status
    status varchar(20) DEFAULT 'pending' NOT NULL, -- 'pending', 'paid', 'expired', 'cancelled'
    
    -- BRI BRIVA data
    bri_va_data jsonb,
    
    -- Timestamps
    expires_at timestamptz NOT NULL,
    paid_at timestamptz,
    created_at timestamptz DEFAULT timezone('utc', now()) NOT NULL
);

-- Order settlements table (platform fee tracking)
CREATE TABLE IF NOT EXISTS order_settlements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference
    order_id uuid REFERENCES orders(id) ON DELETE CASCADE,
    campaign_id uuid, -- for sambatan
    
    -- Settlement type
    settlement_type varchar(20) NOT NULL, -- 'order' or 'sambatan'
    
    -- Amounts
    gross_amount decimal(15,2) NOT NULL,
    platform_fee_rate decimal(5,2) DEFAULT 3.00 NOT NULL,
    platform_fee_amount decimal(15,2) NOT NULL,
    seller_payout_amount decimal(15,2) NOT NULL,
    
    -- Seller info
    seller_id uuid REFERENCES auth_accounts(id),
    seller_account_number varchar(50),
    seller_bank_code varchar(10),
    
    -- BRI transfer references
    bri_transfer_reference varchar(100),
    bri_transaction_id varchar(100),
    
    -- Status
    status varchar(20) DEFAULT 'pending' NOT NULL, -- 'pending', 'completed', 'failed'
    
    -- Timestamps
    settled_at timestamptz,
    created_at timestamptz DEFAULT timezone('utc', now()) NOT NULL,
    updated_at timestamptz DEFAULT timezone('utc', now()) NOT NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- User wallets indexes
CREATE INDEX IF NOT EXISTS idx_user_wallets_user_id ON user_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_user_wallets_bri_account ON user_wallets(bri_account_number);
CREATE INDEX IF NOT EXISTS idx_user_wallets_status ON user_wallets(status);

-- Wallet transactions indexes
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_type ON wallet_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_status ON wallet_transactions(status);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_reference ON wallet_transactions(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at DESC);

-- Top-up requests indexes
CREATE INDEX IF NOT EXISTS idx_wallet_topup_wallet_id ON wallet_topup_requests(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallet_topup_status ON wallet_topup_requests(status);
CREATE INDEX IF NOT EXISTS idx_wallet_topup_va ON wallet_topup_requests(virtual_account);

-- Order settlements indexes
CREATE INDEX IF NOT EXISTS idx_order_settlements_order_id ON order_settlements(order_id);
CREATE INDEX IF NOT EXISTS idx_order_settlements_campaign_id ON order_settlements(campaign_id);
CREATE INDEX IF NOT EXISTS idx_order_settlements_seller_id ON order_settlements(seller_id);
CREATE INDEX IF NOT EXISTS idx_order_settlements_status ON order_settlements(status);
CREATE INDEX IF NOT EXISTS idx_order_settlements_settled_at ON order_settlements(settled_at DESC);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to credit wallet balance atomically
CREATE OR REPLACE FUNCTION credit_wallet(p_wallet_id uuid, p_amount decimal, p_transaction_type varchar, p_reference_type varchar DEFAULT NULL, p_reference_id varchar DEFAULT NULL, p_description text DEFAULT NULL)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_balance_before decimal;
    v_balance_after decimal;
    v_transaction_id uuid;
BEGIN
    -- Lock wallet row
    SELECT balance INTO v_balance_before
    FROM user_wallets
    WHERE id = p_wallet_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Wallet not found: %', p_wallet_id;
    END IF;
    
    -- Calculate new balance
    v_balance_after := v_balance_before + p_amount;
    
    -- Update wallet balance
    UPDATE user_wallets
    SET balance = v_balance_after,
        updated_at = timezone('utc', now())
    WHERE id = p_wallet_id;
    
    -- Create transaction record
    INSERT INTO wallet_transactions (
        wallet_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        status,
        reference_type,
        reference_id,
        description
    ) VALUES (
        p_wallet_id,
        p_transaction_type,
        p_amount,
        v_balance_before,
        v_balance_after,
        'completed',
        p_reference_type,
        p_reference_id,
        p_description
    ) RETURNING id INTO v_transaction_id;
    
    RETURN v_transaction_id;
END;
$$;

-- Function to debit wallet balance atomically
CREATE OR REPLACE FUNCTION debit_wallet(p_wallet_id uuid, p_amount decimal, p_transaction_type varchar, p_reference_type varchar DEFAULT NULL, p_reference_id varchar DEFAULT NULL, p_description text DEFAULT NULL)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_balance_before decimal;
    v_balance_after decimal;
    v_transaction_id uuid;
BEGIN
    -- Lock wallet row
    SELECT balance INTO v_balance_before
    FROM user_wallets
    WHERE id = p_wallet_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Wallet not found: %', p_wallet_id;
    END IF;
    
    -- Check sufficient balance
    IF v_balance_before < p_amount THEN
        RAISE EXCEPTION 'Insufficient balance. Available: %, Required: %', v_balance_before, p_amount;
    END IF;
    
    -- Calculate new balance
    v_balance_after := v_balance_before - p_amount;
    
    -- Update wallet balance
    UPDATE user_wallets
    SET balance = v_balance_after,
        updated_at = timezone('utc', now())
    WHERE id = p_wallet_id;
    
    -- Create transaction record
    INSERT INTO wallet_transactions (
        wallet_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        status,
        reference_type,
        reference_id,
        description
    ) VALUES (
        p_wallet_id,
        p_transaction_type,
        -p_amount,  -- Negative for debit
        v_balance_before,
        v_balance_after,
        'completed',
        p_reference_type,
        p_reference_id,
        p_description
    ) RETURNING id INTO v_transaction_id;
    
    RETURN v_transaction_id;
END;
$$;

-- Function to get wallet balance
CREATE OR REPLACE FUNCTION get_wallet_balance(p_wallet_id uuid)
RETURNS decimal
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_balance decimal;
BEGIN
    SELECT balance INTO v_balance
    FROM user_wallets
    WHERE id = p_wallet_id;
    
    RETURN COALESCE(v_balance, 0);
END;
$$;

-- Function to calculate platform fee
CREATE OR REPLACE FUNCTION calculate_platform_fee(p_amount decimal, p_fee_rate decimal DEFAULT 3.00)
RETURNS decimal
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    RETURN ROUND(p_amount * (p_fee_rate / 100), 2);
END;
$$;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at on user_wallets
CREATE OR REPLACE FUNCTION update_wallet_timestamp()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$;

CREATE TRIGGER user_wallets_updated_at
    BEFORE UPDATE ON user_wallets
    FOR EACH ROW
    EXECUTE FUNCTION update_wallet_timestamp();

CREATE TRIGGER wallet_transactions_updated_at
    BEFORE UPDATE ON wallet_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_wallet_timestamp();

CREATE TRIGGER order_settlements_updated_at
    BEFORE UPDATE ON order_settlements
    FOR EACH ROW
    EXECUTE FUNCTION update_wallet_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE user_wallets IS 'User wallet accounts linked to BRI BaaS';
COMMENT ON TABLE wallet_transactions IS 'Wallet transaction history with balance tracking';
COMMENT ON TABLE wallet_topup_requests IS 'BRIVA top-up request tracking';
COMMENT ON TABLE order_settlements IS 'Order settlement with platform fee tracking';

COMMENT ON FUNCTION credit_wallet IS 'Atomically credit wallet balance and create transaction record';
COMMENT ON FUNCTION debit_wallet IS 'Atomically debit wallet balance with balance check and create transaction record';
COMMENT ON FUNCTION get_wallet_balance IS 'Get current wallet balance';
COMMENT ON FUNCTION calculate_platform_fee IS 'Calculate platform fee (default 3%)';

-- ============================================================================
-- ESCROW / HOLD FUNCTIONS
-- ============================================================================

-- Function to hold/escrow funds for order payment
CREATE OR REPLACE FUNCTION hold_wallet_funds(
    p_wallet_id uuid,
    p_amount decimal,
    p_reference_type varchar,
    p_reference_id varchar,
    p_description text DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_balance_before decimal;
    v_balance_after decimal;
    v_transaction_id uuid;
BEGIN
    -- Lock wallet and get current balance
    SELECT balance INTO v_balance_before
    FROM user_wallets
    WHERE id = p_wallet_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Wallet not found: %', p_wallet_id;
    END IF;
    
    -- Check sufficient balance
    IF v_balance_before < p_amount THEN
        RAISE EXCEPTION 'Insufficient balance for hold: available=%, required=%', v_balance_before, p_amount;
    END IF;
    
    -- Calculate new balance (deduct from available)
    v_balance_after := v_balance_before - p_amount;
    
    -- Update wallet balance
    UPDATE user_wallets
    SET balance = v_balance_after,
        updated_at = timezone('utc', now())
    WHERE id = p_wallet_id;
    
    -- Create transaction record with 'on_hold' status
    INSERT INTO wallet_transactions (
        wallet_id,
        transaction_type,
        amount,
        balance_before,
        balance_after,
        status,
        reference_type,
        reference_id,
        description
    ) VALUES (
        p_wallet_id,
        'payment_hold',
        -p_amount,
        v_balance_before,
        v_balance_after,
        'on_hold',
        p_reference_type,
        p_reference_id,
        COALESCE(p_description, 'Payment on hold')
    ) RETURNING id INTO v_transaction_id;
    
    RETURN v_transaction_id;
END;
$$;

-- Function to release held funds to seller with platform fee
CREATE OR REPLACE FUNCTION release_held_funds(
    p_hold_transaction_id uuid,
    p_seller_wallet_id uuid,
    p_platform_fee decimal
)
RETURNS TABLE (
    seller_transaction_id uuid,
    platform_fee_amount decimal
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_hold_tx wallet_transactions%ROWTYPE;
    v_gross_amount decimal;
    v_net_amount decimal;
    v_seller_tx_id uuid;
BEGIN
    -- Get and lock hold transaction
    SELECT * INTO v_hold_tx
    FROM wallet_transactions
    WHERE id = p_hold_transaction_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Hold transaction not found: %', p_hold_transaction_id;
    END IF;
    
    IF v_hold_tx.status != 'on_hold' THEN
        RAISE EXCEPTION 'Transaction is not on hold: status=%', v_hold_tx.status;
    END IF;
    
    -- Calculate amounts (hold amount is negative, make positive)
    v_gross_amount := ABS(v_hold_tx.amount);
    v_net_amount := v_gross_amount - p_platform_fee;
    
    -- Update hold transaction to released
    UPDATE wallet_transactions
    SET status = 'released',
        updated_at = timezone('utc', now())
    WHERE id = p_hold_transaction_id;
    
    -- Credit seller with net amount (after platform fee)
    v_seller_tx_id := credit_wallet(
        p_seller_wallet_id,
        v_net_amount,
        'payout',
        v_hold_tx.reference_type,
        v_hold_tx.reference_id,
        'Payout (after ' || ROUND(p_platform_fee / v_gross_amount * 100, 2) || '% platform fee)'
    );
    
    RETURN QUERY SELECT v_seller_tx_id, p_platform_fee;
END;
$$;

-- Function to refund held funds to buyer
CREATE OR REPLACE FUNCTION refund_held_funds(
    p_hold_transaction_id uuid,
    p_reason text DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_hold_tx wallet_transactions%ROWTYPE;
    v_refund_amount decimal;
    v_refund_tx_id uuid;
BEGIN
    -- Get and lock hold transaction
    SELECT * INTO v_hold_tx
    FROM wallet_transactions
    WHERE id = p_hold_transaction_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Hold transaction not found: %', p_hold_transaction_id;
    END IF;
    
    IF v_hold_tx.status != 'on_hold' THEN
        RAISE EXCEPTION 'Transaction is not on hold: status=%', v_hold_tx.status;
    END IF;
    
    -- Calculate refund amount (hold amount is negative)
    v_refund_amount := ABS(v_hold_tx.amount);
    
    -- Update hold transaction to refunded
    UPDATE wallet_transactions
    SET status = 'refunded',
        updated_at = timezone('utc', now())
    WHERE id = p_hold_transaction_id;
    
    -- Credit wallet (refund to buyer)
    v_refund_tx_id := credit_wallet(
        v_hold_tx.wallet_id,
        v_refund_amount,
        'refund',
        v_hold_tx.reference_type,
        v_hold_tx.reference_id,
        COALESCE(p_reason, 'Refund of held payment')
    );
    
    RETURN v_refund_tx_id;
END;
$$;

COMMENT ON FUNCTION hold_wallet_funds IS 'Hold/escrow funds for order payment until delivery confirmation';
COMMENT ON FUNCTION release_held_funds IS 'Release held funds to seller with platform fee deduction';
COMMENT ON FUNCTION refund_held_funds IS 'Refund held funds back to buyer wallet';

-- Helper functions for order management and inventory reservation
-- This migration adds functions to atomically reserve and release inventory for orders

set check_function_bodies = off;
set search_path = public;

-- Function to reserve stock atomically
-- This ensures we don't oversell products by checking availability before reserving
CREATE OR REPLACE FUNCTION reserve_stock(p_product_id uuid, p_quantity integer)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_available integer;
BEGIN
    -- Check if listing exists and has sufficient stock
    SELECT (stock_on_hand - stock_reserved) INTO v_available
    FROM marketplace_listings
    WHERE product_id = p_product_id
    FOR UPDATE;  -- Lock the row to prevent race conditions
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product listing not found for product_id: %', p_product_id;
    END IF;
    
    IF v_available < p_quantity THEN
        RAISE EXCEPTION 'Insufficient stock for product %. Available: %, Requested: %', 
            p_product_id, v_available, p_quantity;
    END IF;
    
    -- Reserve the stock
    UPDATE marketplace_listings
    SET stock_reserved = stock_reserved + p_quantity,
        updated_at = timezone('utc', now())
    WHERE product_id = p_product_id;
END;
$$;

-- Function to release stock atomically
-- This is used when an order is cancelled or payment fails
CREATE OR REPLACE FUNCTION release_stock(p_product_id uuid, p_quantity integer)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Release the reserved stock
    UPDATE marketplace_listings
    SET stock_reserved = GREATEST(0, stock_reserved - p_quantity),
        updated_at = timezone('utc', now())
    WHERE product_id = p_product_id;
    
    IF NOT FOUND THEN
        -- Log warning but don't fail - product might have been deleted
        RAISE WARNING 'Product listing not found for product_id: %', p_product_id;
    END IF;
END;
$$;

-- Function to commit reserved stock (convert reserved to sold)
-- This is used when an order is fulfilled
CREATE OR REPLACE FUNCTION commit_stock(p_product_id uuid, p_quantity integer)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Reduce both on-hand and reserved stock
    UPDATE marketplace_listings
    SET stock_on_hand = GREATEST(0, stock_on_hand - p_quantity),
        stock_reserved = GREATEST(0, stock_reserved - p_quantity),
        updated_at = timezone('utc', now())
    WHERE product_id = p_product_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product listing not found for product_id: %', p_product_id;
    END IF;
END;
$$;

-- Function to get available stock for a product
CREATE OR REPLACE FUNCTION get_available_stock(p_product_id uuid)
RETURNS integer
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_available integer;
BEGIN
    SELECT (stock_on_hand - stock_reserved) INTO v_available
    FROM marketplace_listings
    WHERE product_id = p_product_id;
    
    RETURN COALESCE(v_available, 0);
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION reserve_stock IS 'Atomically reserve inventory for an order. Raises exception if insufficient stock.';
COMMENT ON FUNCTION release_stock IS 'Release reserved inventory when order is cancelled or fails.';
COMMENT ON FUNCTION commit_stock IS 'Commit reserved inventory when order is fulfilled (reduces on-hand stock).';
COMMENT ON FUNCTION get_available_stock IS 'Get available stock (on_hand - reserved) for a product.';

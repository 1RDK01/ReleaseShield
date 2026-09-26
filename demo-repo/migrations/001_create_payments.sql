-- Migration 001: Create payments table
-- NOTE: amount column is INTEGER (storing cents)

CREATE TABLE IF NOT EXISTS payments (
    id          SERIAL PRIMARY KEY,
    order_id    VARCHAR(36)  NOT NULL,
    customer_id VARCHAR(36)  NOT NULL,
    currency    VARCHAR(3)   NOT NULL DEFAULT 'USD',
    amount      INTEGER      NOT NULL CHECK (amount > 0),  -- integer cents
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_customer_id ON payments(customer_id);
CREATE INDEX idx_payments_status ON payments(status);

COMMENT ON COLUMN payments.amount IS 'Payment amount in integer cents (e.g., 9999 = $99.99)';

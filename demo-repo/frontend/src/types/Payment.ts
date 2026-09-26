/**
 * Core Payment domain types.
 * NOTE: amount is number (integer cents) — BEFORE state.
 */

export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface Payment {
  id: number;
  order_id: string;
  customer_id: string;
  amount: number; // integer cents (e.g., 9999 = $99.99)
  currency: string;
  status: PaymentStatus;
  payment_method: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentSummary {
  id: number;
  order_id: string;
  amount: number; // integer cents
  currency: string;
  status: PaymentStatus;
  created_at: string;
}

export interface PaymentCreate {
  order_id: string;
  customer_id: string;
  amount: number; // must be positive integer cents
  currency: string;
  payment_method: string;
  description?: string;
}

export interface PaymentUpdate {
  status?: PaymentStatus;
  description?: string;
}

export interface ProcessingFeeResponse {
  payment_id: number;
  gross_amount: number; // integer cents
  processing_fee: number; // integer cents
  net_amount: number; // integer cents
  formatted: string;
}

/**
 * Format integer cents to display string.
 * @param cents - integer cent amount (e.g., 9999)
 * @returns formatted string (e.g., "$99.99")
 */
export function formatAmount(cents: number): string {
  const dollars = Math.floor(cents / 100);
  const remainder = cents % 100;
  return `$${dollars}.${remainder.toString().padStart(2, '0')}`;
}

/**
 * Validate that a payment amount is a valid integer cent value.
 * @param amount - value to validate
 * @returns true if valid
 */
export function isValidAmount(amount: number): boolean {
  return Number.isInteger(amount) && amount > 0;
}

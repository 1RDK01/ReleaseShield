/**
 * API client for payment service.
 * NOTE: expects integer cent amounts in all requests/responses.
 */

import type {
  Payment,
  PaymentCreate,
  PaymentUpdate,
  PaymentSummary,
  ProcessingFeeResponse,
} from '../types/Payment';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Create a new payment.
 * @param data - payment data with integer cent amount
 */
export async function createPayment(data: PaymentCreate): Promise<Payment> {
  if (!Number.isInteger(data.amount)) {
    throw new Error('Payment amount must be an integer (cents)');
  }
  return fetchJson<Payment>(`${BASE_URL}/payments/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * List all payments, optionally filtered by customer.
 */
export async function listPayments(customerId?: string): Promise<PaymentSummary[]> {
  const url = customerId
    ? `${BASE_URL}/payments/?customer_id=${encodeURIComponent(customerId)}`
    : `${BASE_URL}/payments/`;
  return fetchJson<PaymentSummary[]>(url);
}

/**
 * Get a single payment by ID.
 */
export async function getPayment(id: number): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`);
}

/**
 * Update a payment.
 */
export async function updatePayment(id: number, data: PaymentUpdate): Promise<Payment> {
  return fetchJson<Payment>(`${BASE_URL}/payments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Get processing fee for a payment.
 * Returns integer cent amounts for gross, fee, and net.
 */
export async function getProcessingFee(id: number): Promise<ProcessingFeeResponse> {
  return fetchJson<ProcessingFeeResponse>(`${BASE_URL}/payments/${id}/fee`);
}

/**
 * PaymentCard component.
 * NOTE: expects integer cent amounts — displays them formatted.
 * BEFORE state: uses integer arithmetic.
 */

import React from 'react';
import type { Payment } from '../types/Payment';
import { formatAmount } from '../types/Payment';

interface PaymentCardProps {
  payment: Payment;
  onSelect?: (id: number) => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-gray-100 text-gray-800',
};

export function PaymentCard({ payment, onSelect }: PaymentCardProps): JSX.Element {
  // amount is integer cents — use integer arithmetic throughout
  const amountDisplay = formatAmount(payment.amount);

  // Integer-based calculation: fee is 2.9% + 30 cents
  const feeEstimate = Math.floor(payment.amount * 0.029) + 30;
  const netEstimate = payment.amount - feeEstimate;

  // Validate amount is integer (matches backend contract)
  const isValidAmount = Number.isInteger(payment.amount);

  return (
    <div
      className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onSelect?.(payment.id)}
      data-testid={`payment-card-${payment.id}`}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-sm text-gray-500">Order #{payment.order_id}</p>
          <p className="text-lg font-semibold text-gray-900">{amountDisplay}</p>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[payment.status] || ''}`}
        >
          {payment.status}
        </span>
      </div>

      <div className="text-xs text-gray-500 space-y-1">
        <p>Customer: {payment.customer_id}</p>
        <p>Method: {payment.payment_method}</p>
        {payment.description && <p>Note: {payment.description}</p>}
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
        <p>Raw amount: {payment.amount} cents (integer)</p>
        <p>Est. fee: {feeEstimate} cents | Net: {netEstimate} cents</p>
        {!isValidAmount && (
          <p className="text-red-500 font-medium">⚠ Non-integer amount detected</p>
        )}
      </div>
    </div>
  );
}

export default PaymentCard;

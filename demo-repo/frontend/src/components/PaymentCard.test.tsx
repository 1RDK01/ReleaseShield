/**
 * Tests for PaymentCard component.
 * NOTE: Tests assume integer cent amounts — BEFORE state.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PaymentCard } from './PaymentCard';
import type { Payment } from '../types/Payment';

const mockPayment: Payment = {
  id: 1,
  order_id: 'ord-001',
  customer_id: 'cust-001',
  amount: 9999, // integer cents
  currency: 'USD',
  status: 'completed',
  payment_method: 'card',
  description: 'Test payment',
  created_at: '2024-01-15T10:30:00',
  updated_at: '2024-01-15T10:30:05',
};

describe('PaymentCard', () => {
  it('displays formatted amount from integer cents', () => {
    render(<PaymentCard payment={mockPayment} />);
    // 9999 cents should display as $99.99
    expect(screen.getByText('$99.99')).toBeInTheDocument();
  });

  it('displays raw integer cent amount', () => {
    render(<PaymentCard payment={mockPayment} />);
    expect(screen.getByText(/9999 cents \(integer\)/)).toBeInTheDocument();
  });

  it('shows payment status badge', () => {
    render(<PaymentCard payment={mockPayment} />);
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', async () => {
    const onSelect = jest.fn();
    render(<PaymentCard payment={mockPayment} onSelect={onSelect} />);
    await userEvent.click(screen.getByTestId('payment-card-1'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it('calculates integer fee estimate correctly', () => {
    render(<PaymentCard payment={mockPayment} />);
    // Fee = floor(9999 * 0.029) + 30 = floor(289.97) + 30 = 289 + 30 = 319
    expect(screen.getByText(/Est\. fee: 319 cents/)).toBeInTheDocument();
  });

  it('shows warning for non-integer amount', () => {
    const floatPayment = { ...mockPayment, amount: 99.99 as unknown as number };
    render(<PaymentCard payment={floatPayment} />);
    expect(screen.getByText(/Non-integer amount detected/)).toBeInTheDocument();
  });
});

import React, { useState } from 'react';
import { DollarSign, Clock, Package, Calendar, Shield, FileText, AlertCircle, X, Plus } from 'lucide-react';

interface AddQuoteModalProps {
  rfq?: any;
  requirementId?: string;
  suppliers: any[];
  token: string | null;
  isOpen: boolean;
  onClose: () => void;
  onQuoteAdded: () => void;
}

const API_BASE = '/api/v1';

export const AddQuoteModal: React.FC<AddQuoteModalProps> = ({
  rfq,
  requirementId,
  suppliers = [],
  token,
  isOpen,
  onClose,
  onQuoteAdded,
}) => {
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>('');
  const [quoteReference, setQuoteReference] = useState<string>('');
  const [unitPrice, setUnitPrice] = useState<string>('42');
  const [totalPrice, setTotalPrice] = useState<string>('21000');
  const [currency, setCurrency] = useState<string>('USD');
  const [leadTimeDays, setLeadTimeDays] = useState<string>('25');
  const [moq, setMoq] = useState<string>('100');
  const [paymentTerms, setPaymentTerms] = useState<string>('Net 30');
  const [validityPeriod, setValidityPeriod] = useState<string>('30 days');
  const [warranty, setWarranty] = useState<string>('3 years');
  const [notes, setNotes] = useState<string>('');
  const [status, setStatus] = useState<string>('received');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const reqId = rfq?.requirement_id || requirementId;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || (!reqId && !rfq?.id) || !selectedSupplierId) {
      setErrorMsg('Please select a supplier and requirement/RFQ.');
      return;
    }

    const uPrice = parseFloat(unitPrice);
    const tPrice = parseFloat(totalPrice);
    const lDays = parseInt(leadTimeDays, 10);

    // Numeric validation
    if (isNaN(uPrice) || uPrice <= 0) {
      setErrorMsg('Unit price must be a positive number greater than 0.');
      return;
    }
    if (isNaN(tPrice) || tPrice <= 0) {
      setErrorMsg('Total price must be a positive number greater than 0.');
      return;
    }
    if (isNaN(lDays) || lDays < 0) {
      setErrorMsg('Lead time in days cannot be negative.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    const payload = {
      requirement_id: reqId,
      rfq_id: rfq?.id || undefined,
      supplier_id: selectedSupplierId,
      quote_reference: quoteReference.trim() || undefined,
      unit_price: uPrice,
      total_price: tPrice,
      currency: currency.toUpperCase().trim(),
      moq: moq.trim() || '100',
      lead_time_days: lDays,
      warranty: warranty.trim() || '1 Year',
      payment_terms: paymentTerms.trim() || 'Net 30',
      validity_period: validityPeriod.trim() || '30 days',
      status: status,
      notes: notes.trim() || undefined,
    };

    try {
      const res = await fetch(`${API_BASE}/quotations/manual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        onQuoteAdded();
        onClose();
      } else {
        const errData = await res.json();
        setErrorMsg(errData.detail || 'Failed to record supplier quotation.');
      }
    } catch (err: any) {
      setErrorMsg(err?.message || 'Network error during quotation submission.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content" style={{ maxWidth: '650px', width: '90%', padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', color: '#f8fafc', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Plus size={20} color="#10b981" />
              Record Supplier Quotation
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '0.2rem', margin: 0 }}>
              Record a formal supplier quote response against this RFQ into the procurement database.
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px', padding: '0.75rem 1rem', color: '#ef4444', marginBottom: '1rem', fontSize: '0.85rem',
            display: 'flex', alignItems: 'center', gap: '0.4rem'
          }}>
            <AlertCircle size={16} /> {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {/* Supplier Select */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Supplier Name *
              </label>
              <select
                value={selectedSupplierId}
                onChange={e => setSelectedSupplierId(e.target.value)}
                required
                style={{
                  width: '100%', background: '#0b1120', border: '1px solid var(--border-color)',
                  borderRadius: '8px', color: '#f8fafc', padding: '0.5rem 0.75rem', fontSize: '0.85rem'
                }}
              >
                <option value="">-- Choose Supplier --</option>
                {suppliers.map(sup => (
                  <option key={sup.id} value={sup.id}>
                    {sup.company_name} ({sup.location_country || 'Global'})
                  </option>
                ))}
              </select>
            </div>

            {/* Quote Reference Number */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Quote / Reference Number
              </label>
              <input
                type="text"
                className="form-input"
                value={quoteReference}
                onChange={e => setQuoteReference(e.target.value)}
                placeholder="e.g. EC-QUOTE-2026-042"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Unit Price */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Unit Price *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                className="form-input"
                value={unitPrice}
                onChange={e => {
                  setUnitPrice(e.target.value);
                  const u = parseFloat(e.target.value);
                  if (!isNaN(u) && u > 0) {
                    setTotalPrice((u * 500).toString());
                  }
                }}
                placeholder="42.00"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Total Price & Currency */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Total Price & Currency *
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  className="form-input"
                  value={totalPrice}
                  onChange={e => setTotalPrice(e.target.value)}
                  placeholder="21000.00"
                  style={{ flex: 1, fontSize: '0.85rem' }}
                />
                <input
                  type="text"
                  className="form-input"
                  value={currency}
                  onChange={e => setCurrency(e.target.value)}
                  placeholder="USD"
                  style={{ width: '70px', textTransform: 'uppercase', fontSize: '0.85rem' }}
                />
              </div>
            </div>

            {/* Lead Time */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Guaranteed Lead Time (Days) *
              </label>
              <input
                type="number"
                min="0"
                required
                className="form-input"
                value={leadTimeDays}
                onChange={e => setLeadTimeDays(e.target.value)}
                placeholder="25"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* MOQ */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Minimum Order Quantity (MOQ)
              </label>
              <input
                type="text"
                className="form-input"
                value={moq}
                onChange={e => setMoq(e.target.value)}
                placeholder="100 units"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Payment Terms */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Payment Terms
              </label>
              <input
                type="text"
                className="form-input"
                value={paymentTerms}
                onChange={e => setPaymentTerms(e.target.value)}
                placeholder="Net 30"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Quote Validity */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Quote Validity / Expiry
              </label>
              <input
                type="text"
                className="form-input"
                value={validityPeriod}
                onChange={e => setValidityPeriod(e.target.value)}
                placeholder="30 days"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Warranty */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Warranty Terms
              </label>
              <input
                type="text"
                className="form-input"
                value={warranty}
                onChange={e => setWarranty(e.target.value)}
                placeholder="3 years"
                style={{ fontSize: '0.85rem' }}
              />
            </div>

            {/* Status */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                Quote Status
              </label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                style={{
                  width: '100%', background: '#0b1120', border: '1px solid var(--border-color)',
                  borderRadius: '8px', color: '#f8fafc', padding: '0.5rem 0.75rem', fontSize: '0.85rem'
                }}
              >
                <option value="received">Received</option>
                <option value="under_review">Under Review</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
              Notes & Special Instructions
            </label>
            <textarea
              className="form-textarea"
              rows={3}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g., Includes free shipping to India plant for orders above $20k."
              style={{ fontSize: '0.85rem' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || !selectedSupplierId}
            >
              {isSubmitting ? 'Persisting Quote…' : 'Record Supplier Quote'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

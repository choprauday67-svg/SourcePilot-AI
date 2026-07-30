import React from 'react';
import { Award, DollarSign, Clock, Package, CheckCircle2 } from 'lucide-react';

interface ComparisonTableProps {
  quotations: any[];
  recommendation: any;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ quotations, recommendation }) => {
  if (!quotations || quotations.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <p>No supplier quotations have been received or parsed yet.</p>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: '2rem', marginBottom: '2rem', overflowX: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
          <Award size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.3rem', color: '#f8fafc' }}>Side-by-Side Quotation Comparison Grid</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Structured data extracted by Quotation Extraction Agent from incoming supplier responses.
          </p>
        </div>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
            <th style={{ padding: '1rem' }}>Supplier Name</th>
            <th style={{ padding: '1rem' }}><DollarSign size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Unit Price</th>
            <th style={{ padding: '1rem' }}><DollarSign size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Total Quote</th>
            <th style={{ padding: '1rem' }}><Clock size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Lead Time</th>
            <th style={{ padding: '1rem' }}><Package size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> MOQ</th>
            <th style={{ padding: '1rem' }}>Payment Terms</th>
            <th style={{ padding: '1rem' }}>Extraction Confidence</th>
          </tr>
        </thead>
        <tbody>
          {quotations.map((q, idx) => {
            const data = q.extracted_data || {};
            const supplierName = q.supplier_name || q.supplier?.company_name || `Supplier ${idx + 1}`;
            const isTopChoice = recommendation?.recommended_supplier_id === q.supplier_id;

            return (
              <tr
                key={q.id || idx}
                style={{
                  borderBottom: '1px solid var(--border-color)',
                  background: isTopChoice ? 'rgba(16, 185, 129, 0.08)' : 'transparent',
                }}
              >
                <td style={{ padding: '1rem', fontWeight: '600', color: '#f8fafc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {isTopChoice && (
                      <span className="badge badge-quoted" style={{ background: '#10b981', color: '#040914' }}>
                        <CheckCircle2 size={12} style={{ marginRight: '3px' }} /> Recommended
                      </span>
                    )}
                    <span>{supplierName}</span>
                  </div>
                </td>
                <td style={{ padding: '1rem', color: '#38bdf8', fontWeight: '600' }}>
                  ${data.unit_price} {data.currency || 'USD'}
                </td>
                <td style={{ padding: '1rem', color: '#10b981', fontWeight: '700', fontSize: '1rem' }}>
                  ${data.total_price?.toLocaleString()} {data.currency || 'USD'}
                </td>
                <td style={{ padding: '1rem', color: '#e2e8f0' }}>
                  {data.lead_time_days || '14'} Days
                </td>
                <td style={{ padding: '1rem', color: '#e2e8f0' }}>
                  {data.moq || '100 units'}
                </td>
                <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>
                  {data.payment_terms || 'Net 30'}
                </td>
                <td style={{ padding: '1rem' }}>
                  <span style={{ color: '#10b981', fontWeight: '600' }}>
                    {Math.round((q.extraction_confidence || 1) * 100)}%
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

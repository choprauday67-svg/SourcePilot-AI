import React, { useState } from 'react';
import { Award, DollarSign, Clock, Package, CheckCircle2, Upload, FileText, AlertCircle, Plus } from 'lucide-react';
import { AddQuoteModal } from './AddQuoteModal';

interface ComparisonTableProps {
  quotations: any[];
  recommendation: any;
  requirementId?: string;
  suppliers?: any[];
  token?: string | null;
  rfq?: any;
  onQuotationUploaded?: () => void;
}

const API_BASE = '/api/v1';

export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  quotations,
  recommendation,
  requirementId,
  suppliers = [],
  token,
  rfq,
  onQuotationUploaded,
}) => {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isAddQuoteOpen, setIsAddQuoteOpen] = useState(false);
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccessMsg, setUploadSuccessMsg] = useState<string | null>(null);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !requirementId || !selectedSupplierId || !token) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccessMsg(null);

    const formData = new FormData();
    formData.append('requirement_id', requirementId);
    formData.append('supplier_id', selectedSupplierId);
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/quotations/upload-attachment`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadSuccessMsg(`Successfully extracted quotation for ${data.supplier_name || 'supplier'}.`);
        setFile(null);
        setIsUploadOpen(false);
        onQuotationUploaded?.();
      } else {
        const errData = await res.json();
        setUploadError(errData.detail || 'Failed to upload and extract quotation attachment.');
      }
    } catch (err: any) {
      setUploadError(err?.message || 'Network error during attachment upload.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* Upload Supplier Quote Header Card */}
      <div className="glass-card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
            <FileText size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', color: '#f8fafc', margin: 0 }}>Supplier Quotation Pipeline</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', margin: 0 }}>
              Process supplier quotes via inbox reply sync or direct PDF/XLSX attachment upload.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            className="btn btn-primary"
            style={{ fontSize: '0.85rem', padding: '0.45rem 0.85rem', background: 'linear-gradient(135deg, #10b981, #059669)', borderColor: '#10b981' }}
            onClick={() => setIsAddQuoteOpen(true)}
          >
            <Plus size={15} />
            Record Supplier Quote
          </button>

          {requirementId && (
            <button
              className="btn btn-secondary"
              style={{ fontSize: '0.85rem', padding: '0.45rem 0.85rem' }}
              onClick={() => setIsUploadOpen(!isUploadOpen)}
            >
              <Upload size={15} />
              {isUploadOpen ? 'Close Upload Form' : 'Upload Quote File (PDF/XLSX)'}
            </button>
          )}
        </div>
      </div>

      {/* Upload Attachment Form Modal / Panel */}
      {isUploadOpen && (
        <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem', border: '1px solid rgba(56, 189, 248, 0.3)', background: 'rgba(7, 10, 17, 0.85)' }}>
          <h4 style={{ fontSize: '1rem', color: '#f8fafc', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={18} color="#38bdf8" /> Upload & Parse Supplier Quotation File
          </h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '1rem' }}>
            Upload a PDF, XLSX, CSV, or TXT quote document. SourcePilot's Quotation Extraction Agent will parse unit prices, lead times, MOQ, payment terms, and warranty.
          </p>

          <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '220px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                  Select Associated Supplier:
                </label>
                <select
                  value={selectedSupplierId}
                  onChange={e => setSelectedSupplierId(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    background: '#0b1120',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    padding: '0.45rem 0.75rem',
                    fontSize: '0.85rem',
                  }}
                >
                  <option value="">-- Choose Supplier --</option>
                  {suppliers.map(sup => (
                    <option key={sup.id} value={sup.id}>
                      {sup.company_name}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ flex: 1, minWidth: '240px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.35rem' }}>
                  Quotation File (PDF, XLSX, CSV, TXT, max 10MB):
                </label>
                <input
                  type="file"
                  accept=".pdf,.xlsx,.csv,.xls,.doc,.docx,.txt,.json"
                  onChange={e => setFile(e.target.files?.[0] || null)}
                  required
                  style={{
                    width: '100%',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    padding: '0.35rem 0.5rem',
                    fontSize: '0.82rem',
                  }}
                />
              </div>
            </div>

            {uploadError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', padding: '0.5rem 0.75rem', color: '#ef4444', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <AlertCircle size={15} /> {uploadError}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setIsUploadOpen(false)}>
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isUploading || !file || !selectedSupplierId}
              >
                {isUploading ? 'Extracting Data…' : 'Process Attachment'}
              </button>
            </div>
          </form>
        </div>
      )}

      {uploadSuccessMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '8px', padding: '0.6rem 1rem', color: '#10b981', marginBottom: '1rem', fontSize: '0.85rem' }}>
          {uploadSuccessMsg}
        </div>
      )}

      {/* Comparison Grid */}
      {!quotations || quotations.length === 0 ? (
        <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <p>No supplier quotations have been received or uploaded yet.</p>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '2rem', overflowX: 'auto' }}>
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
                <th style={{ padding: '1rem' }}>Quote Ref</th>
                <th style={{ padding: '1rem' }}>Status</th>
                <th style={{ padding: '1rem' }}><DollarSign size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Unit Price</th>
                <th style={{ padding: '1rem' }}><DollarSign size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Total Quote</th>
                <th style={{ padding: '1rem' }}><Clock size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Lead Time</th>
                <th style={{ padding: '1rem' }}><Package size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> MOQ</th>
                <th style={{ padding: '1rem' }}>Payment Terms</th>
                <th style={{ padding: '1rem' }}>Warranty</th>
                <th style={{ padding: '1rem' }}>Validity</th>
                <th style={{ padding: '1rem' }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {quotations.map((q, idx) => {
                const data = q.extracted_data || {};
                const supplierName = q.supplier_name || q.supplier?.company_name || `Supplier ${idx + 1}`;
                const isTopChoice = recommendation?.recommended_supplier_id === q.supplier_id;
                const refNo = q.quote_reference || data.quote_reference || `N/A`;
                const quoteStatus = q.status || 'received';

                let statusBadgeStyle = { background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8' };
                if (quoteStatus === 'accepted') {
                  statusBadgeStyle = { background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' };
                } else if (quoteStatus === 'rejected') {
                  statusBadgeStyle = { background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' };
                } else if (quoteStatus === 'under_review') {
                  statusBadgeStyle = { background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b' };
                }

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
                    <td style={{ padding: '1rem', color: '#cbd5e1', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {refNo}
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <span style={{
                        padding: '0.2rem 0.55rem',
                        borderRadius: '6px',
                        fontSize: '0.78rem',
                        fontWeight: '700',
                        textTransform: 'uppercase',
                        ...statusBadgeStyle
                      }}>
                        {quoteStatus}
                      </span>
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
                    <td style={{ padding: '1rem', color: '#cbd5e1', fontSize: '0.85rem' }}>
                      {data.warranty || '1 Year'}
                    </td>
                    <td style={{ padding: '1rem', color: '#cbd5e1', fontSize: '0.85rem' }}>
                      {data.validity_period || '30 days'}
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
      )}

      {/* Add Supplier Quote Modal */}
      <AddQuoteModal
        rfq={rfq}
        requirementId={requirementId}
        suppliers={suppliers}
        token={token || null}
        isOpen={isAddQuoteOpen}
        onClose={() => setIsAddQuoteOpen(false)}
        onQuoteAdded={() => onQuotationUploaded?.()}
      />
    </div>
  );
};

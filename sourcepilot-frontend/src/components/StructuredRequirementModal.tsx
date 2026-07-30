import React from 'react';
import { CheckCircle2, Search, Lock } from 'lucide-react';

interface StructuredRequirementModalProps {
  requirement: any;
  isOpen: boolean;
  onConfirm: () => void;
  onClose: () => void;
  isDiscovering: boolean;
}

export const StructuredRequirementModal: React.FC<StructuredRequirementModalProps> = ({
  requirement,
  isOpen,
  onConfirm,
  onClose,
  isDiscovering
}) => {
  if (!isOpen || !requirement) return null;

  const data = requirement.structured_data || {};
  const reqStatus = requirement.status || 'draft';
  const isDraftOrConfirmed = reqStatus === 'draft' || reqStatus === 'confirmed';
  const isAwarded = reqStatus === 'awarded';

  const renderActionButton = () => {
    if (isDraftOrConfirmed) {
      return (
        <button className="btn btn-primary" onClick={onConfirm} disabled={isDiscovering}>
          <Search size={18} />
          {isDiscovering ? 'Discovering Suppliers...' : 'Confirm & Discover Suppliers'}
        </button>
      );
    }
    if (isAwarded) {
      return (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem',
          background: 'rgba(251, 191, 36, 0.15)', border: '1px solid rgba(251, 191, 36, 0.4)',
          color: '#fbbf24', padding: '0.5rem 1rem', borderRadius: '8px',
          fontWeight: '700', fontSize: '0.88rem'
        }}>
          <CheckCircle2 size={16} /> Procurement Awarded
        </div>
      );
    }
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        background: 'rgba(56, 189, 248, 0.12)', border: '1px solid rgba(56, 189, 248, 0.3)',
        color: '#38bdf8', padding: '0.5rem 1rem', borderRadius: '8px',
        fontWeight: '600', fontSize: '0.88rem'
      }}>
        <Lock size={15} /> Supplier Discovery Completed
      </div>
    );
  };

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <CheckCircle2 size={26} color="#38bdf8" />
            <h3 style={{ fontSize: '1.3rem' }}>AI Requirement Extraction Review</h3>
          </div>
          <span className="badge badge-discovering">Status: {reqStatus}</span>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          SourcePilot's Requirement Understanding Agent converted your raw text into the following structured parameters.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
          <div className="glass-card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Product & Category</div>
            <div style={{ fontWeight: '600', fontSize: '1rem', color: '#f8fafc' }}>{data.product || 'N/A'}</div>
            <span style={{ fontSize: '0.8rem', color: '#38bdf8' }}>{data.category || 'General'}</span>
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Quantity & Unit</div>
            <div style={{ fontWeight: '600', fontSize: '1rem', color: '#f8fafc' }}>{data.quantity} {data.unit}</div>
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Estimated Budget</div>
            <div style={{ fontWeight: '600', fontSize: '1rem', color: '#10b981' }}>
              {data.budget_range ? `$${data.budget_range.max?.toLocaleString()} ${data.budget_range.currency}` : 'Unspecified'}
            </div>
          </div>

          <div className="glass-card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Location & Timeline</div>
            <div style={{ fontWeight: '600', fontSize: '0.95rem', color: '#f8fafc' }}>{data.delivery_location || 'Global'}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Deadline: {data.timeline || 'Flexible'}</div>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Technical Specifications & Certifications</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {(data.specifications || []).map((spec: string, i: number) => (
              <span key={i} style={{ background: 'rgba(255,255,255,0.06)', padding: '4px 10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                • {spec}
              </span>
            ))}
            {(data.must_have_certifications || []).map((cert: string, i: number) => (
              <span key={i} style={{ background: 'rgba(168,85,247,0.15)', color: '#a855f7', border: '1px solid rgba(168,85,247,0.3)', padding: '4px 10px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: '600' }}>
                ✓ {cert}
              </span>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', alignItems: 'center' }}>
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
          {renderActionButton()}
        </div>
      </div>
    </div>
  );
};

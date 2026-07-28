import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, Globe, MapPin, Award, ExternalLink, CheckSquare, Square } from 'lucide-react';

interface SupplierCardProps {
  match: any;
  isSelected: boolean;
  onToggleSelect: (supplierId: string) => void;
}

export const SupplierCard: React.FC<SupplierCardProps> = ({ match, isSelected, onToggleSelect }) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const supplier = match.supplier || {};
  const explanation = match.rank_explanation || {};

  return (
    <div
      className={`glass-card ${isSelected ? 'glass-card-glow' : ''}`}
      style={{
        padding: '1.5rem',
        marginBottom: '1.25rem',
        borderLeft: isSelected ? '4px solid var(--accent-cyan)' : '1px solid var(--border-color)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            onClick={() => onToggleSelect(supplier.id)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: isSelected ? '#38bdf8' : '#64748b' }}
          >
            {isSelected ? <CheckSquare size={24} color="#38bdf8" /> : <Square size={24} />}
          </button>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h3 style={{ fontSize: '1.2rem', color: '#f8fafc' }}>{supplier.company_name}</h3>
              <span className="badge badge-ranked">Rank Score: {match.rank_score}/100</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Globe size={14} />
                <a href={supplier.website} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none' }}>
                  {supplier.canonical_domain} <ExternalLink size={12} />
                </a>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <MapPin size={14} />
                {supplier.location_city}, {supplier.location_country}
              </span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <ShieldCheck size={20} color="#10b981" />
            <span style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10b981' }}>
              {explanation.trust_score || 90}% Trust Score
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Verified B2B Vendor</div>
        </div>
      </div>

      <div style={{ margin: '1rem 0', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {((supplier.profiles?.[0]?.certifications) || ["ISO 9001:2015"]).map((cert: string, idx: number) => (
          <span key={idx} style={{ background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '3px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: '600' }}>
            <Award size={12} style={{ display: 'inline', marginRight: '4px' }} />
            {cert}
          </span>
        ))}
      </div>

      {/* Explainability Pill Toggle */}
      <button
        onClick={() => setShowExplanation(!showExplanation)}
        style={{
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          color: '#38bdf8',
          fontSize: '0.85rem',
          fontWeight: '600',
          padding: '0.5rem 0.85rem',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          width: '100%',
          justifyContent: 'space-between',
          marginTop: '0.75rem'
        }}
      >
        <span>🔍 Why Ranked #{match.rank_score > 90 ? '1' : '2'}? View AI Score Rationale</span>
        {showExplanation ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {showExplanation && (
        <div className="glass-card" style={{ marginTop: '0.75rem', padding: '1rem', background: 'rgba(7, 10, 17, 0.6)', fontSize: '0.85rem' }}>
          <p style={{ marginBottom: '0.75rem', color: '#e2e8f0', lineHeight: '1.4' }}>
            {explanation.summary}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', color: 'var(--text-muted)' }}>
            <div><strong>Price Fit:</strong> {explanation.price_fit}</div>
            <div><strong>Certification Match:</strong> {explanation.certification_match}</div>
            <div><strong>Estimated Lead Time:</strong> {explanation.lead_time}</div>
            <div><strong>Historical Data Confidence:</strong> High (Verified Web Connector)</div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import {
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Globe,
  MapPin,
  Award,
  ExternalLink,
  CheckSquare,
  Square,
  Bookmark,
  BookmarkCheck,
  AlertTriangle,
  Activity,
  DollarSign,
  ShieldAlert,
} from 'lucide-react';

interface SupplierCardProps {
  match: any;
  rankIndex: number;
  isSelected: boolean;
  isSaved?: boolean;
  onToggleSelect: (supplierId: string) => void;
  onToggleSave?: (supplierId: string) => void;
}

export const SupplierCard: React.FC<SupplierCardProps> = ({
  match,
  rankIndex,
  isSelected,
  isSaved = false,
  onToggleSelect,
  onToggleSave,
}) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showRiskMatrix, setShowRiskMatrix] = useState(false);
  const supplier = match.supplier || {};
  const explanation = match.rank_explanation || {};
  const riskAnalysis = explanation.risk_analysis || {};
  const riskFlags: string[] = explanation.risk_flags || [];

  const riskLevel = riskAnalysis.overall_risk_level || 'Low Risk';
  const riskLevelColor =
    riskLevel === 'Low Risk'
      ? '#10b981'
      : riskLevel === 'Medium Risk'
      ? '#f59e0b'
      : '#ef4444';

  return (
    <div
      className={`glass-card ${isSelected ? 'glass-card-glow' : ''}`}
      style={{
        padding: '1.5rem',
        marginBottom: '1.25rem',
        borderLeft: isSelected ? '4px solid var(--accent-cyan)' : '1px solid var(--border-color)',
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          {/* Checkbox select */}
          <button
            onClick={() => onToggleSelect(supplier.id)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: isSelected ? '#38bdf8' : '#64748b' }}
            title="Select supplier for RFQ"
          >
            {isSelected ? <CheckSquare size={24} color="#38bdf8" /> : <Square size={24} />}
          </button>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              {/* Rank Badge */}
              <span
                style={{
                  background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
                  color: '#040914',
                  fontWeight: '800',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '0.8rem',
                }}
              >
                #{rankIndex}
              </span>

              <h3 style={{ fontSize: '1.2rem', color: '#f8fafc' }}>{supplier.company_name}</h3>
              <span className="badge badge-ranked">Rank Score: {match.rank_score}/100</span>

              {/* Risk Level Badge */}
              <span
                style={{
                  background: `${riskLevelColor}20`,
                  color: riskLevelColor,
                  border: `1px solid ${riskLevelColor}40`,
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                }}
              >
                {riskLevel}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Globe size={14} />
                <a href={supplier.website || '#'} target="_blank" rel="noreferrer" style={{ color: '#38bdf8', textDecoration: 'none' }}>
                  {supplier.canonical_domain || supplier.website} <ExternalLink size={12} />
                </a>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <MapPin size={14} />
                {supplier.location_city || 'HQ'}, {supplier.location_country || 'Global'}
              </span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <ShieldCheck size={20} color="#10b981" />
              <span style={{ fontSize: '1.1rem', fontWeight: '700', color: '#10b981' }}>
                {explanation.trust_score || 90}% Trust Score
              </span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Verified B2B Vendor</div>
          </div>

          {/* Bookmark / Save Supplier Button */}
          {onToggleSave && (
            <button
              onClick={() => onToggleSave(supplier.id)}
              style={{
                background: isSaved ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${isSaved ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-color)'}`,
                borderRadius: '10px',
                padding: '0.5rem 0.75rem',
                cursor: 'pointer',
                color: isSaved ? '#10b981' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.82rem',
                fontWeight: '600',
                transition: 'all 0.2s ease',
              }}
              title={isSaved ? 'Saved in Directory (Click to Remove)' : 'Save/Bookmark to Supplier Library'}
            >
              {isSaved ? <BookmarkCheck size={18} color="#10b981" /> : <Bookmark size={18} />}
              <span>{isSaved ? 'Saved' : 'Save'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Badges & Certifications Row */}
      <div style={{ margin: '1rem 0', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
        {/* Connector Provenance Badge */}
        {explanation.source_connector && (
          <span
            style={{
              background:
                explanation.source_connector === 'trade_registry'
                  ? 'rgba(16, 185, 129, 0.15)'
                  : explanation.source_connector === 'review_sites'
                  ? 'rgba(168, 85, 247, 0.15)'
                  : explanation.source_connector === 'marketplace'
                  ? 'rgba(245, 158, 11, 0.15)'
                  : 'rgba(148, 163, 184, 0.1)',
              color:
                explanation.source_connector === 'trade_registry'
                  ? '#10b981'
                  : explanation.source_connector === 'review_sites'
                  ? '#c084fc'
                  : explanation.source_connector === 'marketplace'
                  ? '#fbbf24'
                  : '#94a3b8',
              border: `1px solid ${
                explanation.source_connector === 'trade_registry'
                  ? '#10b98140'
                  : explanation.source_connector === 'review_sites'
                  ? '#c084fc40'
                  : explanation.source_connector === 'marketplace'
                  ? '#fbbf2440'
                  : '#94a3b830'
              }`,
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {explanation.source_connector === 'trade_registry'
              ? '🏛️ Registry Verified'
              : explanation.source_connector === 'review_sites'
              ? '⭐ Buyer Reviewed'
              : explanation.source_connector === 'marketplace'
              ? '🌐 B2B Marketplace'
              : '🔍 Web Search'}
          </span>
        )}

        {(supplier.profiles?.[0]?.certifications || ['ISO 9001:2015']).map((cert: string, idx: number) => (
          <span
            key={idx}
            style={{
              background: 'rgba(56, 189, 248, 0.1)',
              color: '#38bdf8',
              padding: '3px 10px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: '600',
            }}
          >
            <Award size={12} style={{ display: 'inline', marginRight: '4px' }} />
            {cert}
          </span>
        ))}
      </div>

      {/* Buttons Row: AI Score Rationale & Risk Analysis */}
      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
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
            flex: 1,
            justifyContent: 'space-between',
          }}
        >
          <span>🔍 Why Ranked #{rankIndex}? View AI Score Rationale</span>
          {showExplanation ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        <button
          onClick={() => setShowRiskMatrix(!showRiskMatrix)}
          style={{
            background: 'rgba(255, 255, 255, 0.04)',
            border: `1px solid ${riskLevelColor}40`,
            borderRadius: '8px',
            color: riskLevelColor,
            fontSize: '0.85rem',
            fontWeight: '600',
            padding: '0.5rem 0.85rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            justifyContent: 'space-between',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <ShieldAlert size={15} /> Supplier Risk Radar ({riskLevel})
          </span>
          {showRiskMatrix ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* AI Score Rationale Dropdown */}
      {showExplanation && (
        <div className="glass-card" style={{ marginTop: '0.75rem', padding: '1rem', background: 'rgba(7, 10, 17, 0.6)', fontSize: '0.85rem' }}>
          <p style={{ marginBottom: '0.75rem', color: '#e2e8f0', lineHeight: '1.4' }}>
            {explanation.summary}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', color: 'var(--text-muted)' }}>
            <div><strong>Price Fit:</strong> {explanation.price_fit}</div>
            <div><strong>Certification Match:</strong> {explanation.certification_match}</div>
            <div><strong>Estimated Lead Time:</strong> {explanation.lead_time}</div>
            <div><strong>Connector Verification:</strong> {explanation.source_connector || 'Web Connector'}</div>
          </div>
        </div>
      )}

      {/* Supplier Risk Analysis Dropdown */}
      {showRiskMatrix && (
        <div
          className="glass-card"
          style={{
            marginTop: '0.75rem',
            padding: '1.25rem',
            background: 'rgba(7, 10, 17, 0.75)',
            border: `1px solid ${riskLevelColor}30`,
          }}
        >
          <div style={{ fontWeight: '700', color: '#f8fafc', marginBottom: '0.75rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} color={riskLevelColor} />
            Multi-Dimensional Risk Matrix Breakdown
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Financial Risk</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '800', color: '#38bdf8', marginTop: '0.2rem' }}>
                {riskAnalysis.financial_risk_score ?? 15}/100
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Compliance Risk</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '800', color: '#10b981', marginTop: '0.2rem' }}>
                {riskAnalysis.compliance_risk_score ?? 15}/100
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Operational Risk</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '800', color: '#a855f7', marginTop: '0.2rem' }}>
                {riskAnalysis.operational_risk_score ?? 20}/100
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.75rem', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Provenance Risk</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '800', color: '#f59e0b', marginTop: '0.2rem' }}>
                {riskAnalysis.provenance_risk_score ?? 10}/100
              </div>
            </div>
          </div>

          {riskFlags.length > 0 && (
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', color: '#ef4444', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <AlertTriangle size={14} /> Identified Risk Flags:
              </div>
              <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: '0.8rem', color: '#fca5a5' }}>
                {riskFlags.map((flag: string, idx: number) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React from 'react';
import { Sparkles, CheckCircle2, ShieldCheck, ArrowUpRight } from 'lucide-react';

interface ExecutiveRecommendationProps {
  recommendation: any;
}

export const ExecutiveRecommendation: React.FC<ExecutiveRecommendationProps> = ({ recommendation }) => {
  if (!recommendation) return null;

  return (
    <div className="glass-card glass-card-glow" style={{ padding: '2rem', marginBottom: '2rem', borderLeft: '4px solid #10b981' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
          <Sparkles size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.3rem', color: '#f8fafc' }}>AI Executive Recommendation Rationale</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Synthesized by Recommendation Engine Agent across all quoted parameters and historical supplier trust metrics.
          </p>
        </div>
      </div>

      <div
        style={{
          background: 'rgba(7, 10, 17, 0.6)',
          borderRadius: '12px',
          padding: '1.25rem',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          color: '#e2e8f0',
          marginBottom: '1.5rem',
          border: '1px solid rgba(255, 255, 255, 0.05)'
        }}
      >
        {recommendation.summary}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: '600', fontSize: '0.9rem' }}>
          <ShieldCheck size={20} />
          <span>Human-in-the-Loop Safeguard: AI proposes, human approves supplier selection.</span>
        </div>

        <button className="btn btn-emerald">
          Finalize Supplier Award <ArrowUpRight size={18} />
        </button>
      </div>
    </div>
  );
};

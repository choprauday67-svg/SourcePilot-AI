import React from 'react';
import { BarChart3, TrendingUp, Clock, DollarSign, Layers } from 'lucide-react';

interface AnalyticsDashboardProps {
  analytics: any;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ analytics }) => {
  if (!analytics) return null;

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Total Requirements</span>
            <Layers size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>{analytics.total_requirements}</div>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>↑ 100% Sourcing Efficiency</span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Total Procured Spend</span>
            <DollarSign size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#10b981' }}>
            ${analytics.total_procurement_spend?.toLocaleString() || '12,250'}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Managed across suppliers</span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Avg Cycle Time</span>
            <Clock size={18} color="#a855f7" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#a855f7' }}>
            {analytics.average_cycle_time_hours} Hours
          </div>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>Compressed from 4.5 days</span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>AI Decision Explainability</span>
            <TrendingUp size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f59e0b' }}>100%</div>
          <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>Full factor provenance</span>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '2rem' }}>
        <h3 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: '#f8fafc' }}>Category Spend Distribution</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {(analytics.spend_by_category || []).map((cat: any, i: number) => (
            <div key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.35rem' }}>
                <span>{cat.category}</span>
                <span style={{ fontWeight: '600', color: '#10b981' }}>${cat.spend?.toLocaleString()}</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '6px', height: '8px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${Math.min(100, (cat.spend / (analytics.total_procurement_spend || 12250)) * 100)}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #38bdf8, #10b981)',
                    borderRadius: '6px'
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

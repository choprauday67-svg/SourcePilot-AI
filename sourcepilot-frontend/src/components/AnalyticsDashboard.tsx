import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, DollarSign, Layers, Package, Activity } from 'lucide-react';

interface AnalyticsDashboardProps {
  analytics: any;
  token: string | null;
}

const API_BASE = '/api/v1';

const MiniBar: React.FC<{ value: number; max: number; color: string }> = ({ value, max, color }) => (
  <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '4px', height: '8px', overflow: 'hidden', flex: 1 }}>
    <div
      style={{
        width: `${Math.min(100, max > 0 ? (value / max) * 100 : 0)}%`,
        height: '100%',
        background: color,
        borderRadius: '4px',
        transition: 'width 0.6s ease',
      }}
    />
  </div>
);

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ analytics, token }) => {
  const [priceTrends, setPriceTrends] = useState<any>(null);
  const [loadingPrices, setLoadingPrices] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoadingPrices(true);
    fetch(`${API_BASE}/analytics/price-trends`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => setPriceTrends(data))
      .catch(() => {})
      .finally(() => setLoadingPrices(false));
  }, [token]);

  if (!analytics) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        <p>Loading procurement spend & analytics data…</p>
      </div>
    );
  }

  const categorySupplierMax = Math.max(
    ...(priceTrends?.supplier_performance || []).map((s: any) => s.total_spend || 0),
    1
  );
  const categoryMax = Math.max(
    ...(priceTrends?.category_summary || []).map((c: any) => c.avg_price || 0),
    1
  );

  const totalSpend = analytics.total_procurement_spend ?? 0;
  const cycleTime = analytics.average_cycle_time_hours ?? 0;

  return (
    <div>
      {/* ─── KPI Cards ─────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Total Requirements</span>
            <Layers size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f8fafc' }}>
            {analytics.total_requirements ?? 0}
          </div>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>
            {analytics.completed_requirements ?? 0} Completed / {analytics.active_sourcing ?? 0} Active
          </span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Total Procured Spend</span>
            <DollarSign size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#10b981' }}>
            ${totalSpend.toLocaleString()}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calculated from database quotations</span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>Avg Cycle Time</span>
            <Clock size={18} color="#a855f7" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#a855f7' }}>
            {cycleTime} Hrs
          </div>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>Automated AI Sourcing Workflow</span>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem' }}>AI Decision Explainability</span>
            <TrendingUp size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#f59e0b' }}>100%</div>
          <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>Full factor & score provenance</span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
        {/* ─── Category Spend ─────────────────────────── */}
        <div className="glass-card" style={{ padding: '2rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1.25rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Package size={16} color="#38bdf8" /> Category Spend Distribution
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {(analytics.spend_by_category || []).map((cat: any, i: number) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                  <span style={{ color: '#e2e8f0' }}>{cat.category}</span>
                  <span style={{ fontWeight: '600', color: '#10b981' }}>${cat.spend?.toLocaleString()}</span>
                </div>
                <MiniBar
                  value={cat.spend || 0}
                  max={totalSpend || 1}
                  color="linear-gradient(90deg, #38bdf8, #10b981)"
                />
              </div>
            ))}
            {(!analytics.spend_by_category || analytics.spend_by_category.length === 0) && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No category spend records found in the database.
              </p>
            )}
          </div>
        </div>

        {/* ─── Price Trends by Category ───────────────── */}
        <div className="glass-card" style={{ padding: '2rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1.25rem', color: '#f8fafc', display: 'center', gap: '0.5rem' }}>
            <BarChart3 size={16} color="#a855f7" /> Price Benchmarks by Category
          </h3>
          {loadingPrices ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading price trends…</p>
          ) : priceTrends && (priceTrends.category_summary || []).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {priceTrends.category_summary.map((cat: any, i: number) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem', marginBottom: '0.35rem', color: '#e2e8f0' }}>
                    <span>{cat.category}</span>
                    <span>
                      <span style={{ color: '#a855f7', fontWeight: '600' }}>${cat.avg_price}</span>
                      <span style={{ color: '#475569', marginLeft: '0.5rem', fontSize: '0.75rem' }}>
                        (${cat.min_price} – ${cat.max_price}, {cat.quote_count} quote{cat.quote_count !== 1 ? 's' : ''})
                      </span>
                    </span>
                  </div>
                  <MiniBar value={cat.avg_price} max={categoryMax} color="linear-gradient(90deg, #a855f7, #6366f1)" />
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No quotation records in database. Dispatch RFQs and receive quotes to display price benchmarks.
            </p>
          )}
        </div>
      </div>

      {/* ─── Supplier Performance Scorecards ─────────────── */}
      {priceTrends && (priceTrends.supplier_performance || []).length > 0 && (
        <div className="glass-card" style={{ padding: '2rem' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '1.25rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} color="#f59e0b" /> Supplier Performance Scorecards
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                  {['Supplier', 'Quotes Received', 'Total Spend', 'Avg Lead Time', 'Spend Share'].map(h => (
                    <th key={h} style={{ padding: '0.5rem 0.75rem', textAlign: 'left', color: '#64748b', fontWeight: '600' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {priceTrends.supplier_performance.map((sup: any, i: number) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#f8fafc', fontWeight: '600' }}>{sup.name}</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#94a3b8' }}>{sup.quote_count}</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#10b981', fontWeight: '600' }}>${sup.total_spend?.toLocaleString()}</td>
                    <td style={{ padding: '0.65rem 0.75rem', color: '#94a3b8' }}>{sup.avg_lead_time} days</td>
                    <td style={{ padding: '0.65rem 0.75rem', minWidth: '120px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <MiniBar value={sup.total_spend} max={categorySupplierMax} color="linear-gradient(90deg, #f59e0b, #ef4444)" />
                        <span style={{ color: '#64748b', fontSize: '0.78rem', whiteSpace: 'nowrap' }}>
                          {categorySupplierMax > 0 ? Math.round((sup.total_spend / categorySupplierMax) * 100) : 0}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

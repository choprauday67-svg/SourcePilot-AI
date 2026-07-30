import React, { useState } from 'react';
import { Brain, TrendingUp, AlertTriangle, Clock, Lightbulb, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';

interface MarketIntelligenceCardProps {
  requirementId: string;
  token: string | null;
}

const API_BASE = '/api/v1';

function markdownToHtml(md: string): string {
  if (!md) return '';
  return md
    .replace(/^### (.+)$/gm, '<h3 style="font-size:1rem;color:#a5b4fc;margin:0.5rem 0 0.2rem">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:1.05rem;color:#c4b5fd;margin:0.75rem 0 0.3rem">$1</h2>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#f8fafc">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:rgba(139,92,246,0.2);color:#c4b5fd;padding:0.1rem 0.3rem;border-radius:4px;font-size:0.88em">$1</code>');
}

export const MarketIntelligenceCard: React.FC<MarketIntelligenceCardProps> = ({ requirementId, token }) => {
  const [intelligence, setIntelligence] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState('');

  const fetchIntelligence = async () => {
    if (!token || loading) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/analytics/market-intelligence/${requirementId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setIntelligence(await res.json());
        setExpanded(true);
      } else {
        setError('Market Intelligence Agent returned an error. Ensure the requirement has been processed.');
      }
    } catch {
      setError('Failed to contact Market Intelligence Agent.');
    } finally {
      setLoading(false);
    }
  };

  const SENTIMENT_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
    bullish:  { color: '#10b981', bg: 'rgba(16,185,129,0.12)',  label: '📈 Bullish — Prices Rising' },
    bearish:  { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   label: '📉 Bearish — Prices Falling' },
    stable:   { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)',  label: '📊 Stable — Prices Steady' },
    volatile: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: '⚡ Volatile — Price Swings' },
  };

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      {/* Trigger Row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            padding: '0.5rem',
            borderRadius: '10px',
            background: 'rgba(168, 85, 247, 0.15)',
            color: '#a855f7',
          }}>
            <Brain size={22} />
          </div>
          <div>
            <div style={{ fontWeight: '700', color: '#f8fafc', fontSize: '1rem' }}>
              Market Intelligence Agent
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              AI-powered purchasing timing & market insights
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {intelligence && (
            <button
              onClick={() => setExpanded(e => !e)}
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: '#94a3b8',
                padding: '0.4rem 0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontSize: '0.82rem',
              }}
            >
              {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {expanded ? 'Collapse' : 'Expand'}
            </button>
          )}

          <button
            id="run-market-intelligence-btn"
            className="btn btn-primary"
            onClick={fetchIntelligence}
            disabled={loading}
            style={{ minWidth: '190px' }}
          >
            {loading ? (
              <>
                <Sparkles size={16} className="spin" />
                Analysing Market…
              </>
            ) : (
              <>
                <Brain size={16} />
                {intelligence ? 'Refresh Analysis' : 'Run Market Analysis'}
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          borderRadius: '8px',
          background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.25)',
          color: '#ef4444',
          fontSize: '0.85rem',
        }}>
          {error}
        </div>
      )}

      {/* Results */}
      {intelligence && expanded && (
        <div style={{ marginTop: '1.5rem' }}>
          {/* Sentiment Banner */}
          {intelligence.market_sentiment && (() => {
            const cfg = SENTIMENT_CONFIG[intelligence.market_sentiment] || SENTIMENT_CONFIG['stable'];
            return (
              <div style={{
                padding: '0.75rem 1.25rem',
                borderRadius: '10px',
                background: cfg.bg,
                border: `1px solid ${cfg.color}40`,
                color: cfg.color,
                fontWeight: '700',
                fontSize: '0.95rem',
                marginBottom: '1.25rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span>{cfg.label}</span>
                {intelligence.recommended_purchase_timing && (
                  <span style={{ fontSize: '0.82rem', fontWeight: '500', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Clock size={14} /> {intelligence.recommended_purchase_timing}
                  </span>
                )}
              </div>
            );
          })()}

          {/* Summary */}
          {intelligence.analysis_summary && (
            <div
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: '10px',
                padding: '1rem 1.25rem',
                marginBottom: '1.25rem',
                color: '#cbd5e1',
                fontSize: '0.9rem',
                lineHeight: '1.6',
              }}
              dangerouslySetInnerHTML={{ __html: markdownToHtml(intelligence.analysis_summary) }}
            />
          )}

          {/* Two-column: Risks + Opportunities */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* Supply Chain Risks */}
            {(intelligence.supply_chain_risks || []).length > 0 && (
              <div style={{
                background: 'rgba(239,68,68,0.06)',
                border: '1px solid rgba(239,68,68,0.18)',
                borderRadius: '10px',
                padding: '1rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#ef4444', fontWeight: '700', fontSize: '0.88rem' }}>
                  <AlertTriangle size={15} /> Supply Chain Risks
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {intelligence.supply_chain_risks.map((r: string, i: number) => (
                    <li key={i} style={{ fontSize: '0.83rem', color: '#fca5a5', display: 'flex', gap: '0.5rem', lineHeight: '1.4' }}>
                      <span style={{ color: '#ef4444', flexShrink: 0 }}>•</span>
                      <span dangerouslySetInnerHTML={{ __html: markdownToHtml(r) }} />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Key Opportunities */}
            {(intelligence.key_opportunities || []).length > 0 && (
              <div style={{
                background: 'rgba(16,185,129,0.06)',
                border: '1px solid rgba(16,185,129,0.18)',
                borderRadius: '10px',
                padding: '1rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#10b981', fontWeight: '700', fontSize: '0.88rem' }}>
                  <TrendingUp size={15} /> Key Opportunities
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {intelligence.key_opportunities.map((o: string, i: number) => (
                    <li key={i} style={{ fontSize: '0.83rem', color: '#6ee7b7', display: 'flex', gap: '0.5rem', lineHeight: '1.4' }}>
                      <span style={{ color: '#10b981', flexShrink: 0 }}>•</span>
                      <span dangerouslySetInnerHTML={{ __html: markdownToHtml(o) }} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Recommended Actions */}
          {(intelligence.recommended_actions || []).length > 0 && (
            <div style={{
              background: 'rgba(99,102,241,0.08)',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: '10px',
              padding: '1rem 1.25rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: '#818cf8', fontWeight: '700', fontSize: '0.88rem' }}>
                <Lightbulb size={15} /> Recommended Actions
              </div>
              <ol style={{ listStyle: 'decimal', paddingLeft: '1.2rem', margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {intelligence.recommended_actions.map((a: string, i: number) => (
                  <li key={i} style={{ fontSize: '0.85rem', color: '#c7d2fe', lineHeight: '1.5' }}>
                    <span dangerouslySetInnerHTML={{ __html: markdownToHtml(a) }} />
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Price Forecast */}
          {intelligence.price_forecast_90_days && (
            <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#64748b', fontSize: '0.82rem' }}>
              <TrendingUp size={14} color="#f59e0b" />
              <span>
                <strong style={{ color: '#f59e0b' }}>90-day price forecast:</strong>{' '}
                <span dangerouslySetInnerHTML={{ __html: markdownToHtml(intelligence.price_forecast_90_days) }} />
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

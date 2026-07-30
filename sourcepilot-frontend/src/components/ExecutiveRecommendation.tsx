import React, { useState, useMemo } from 'react';
import { Sparkles, ShieldCheck, Award, CheckCircle, Lock } from 'lucide-react';

interface ExecutiveRecommendationProps {
  recommendation: any;
  requirementId?: string;
  token?: string | null;
  onAward?: (supplierId: string, notes: string) => Promise<void>;
}

function markdownToHtml(md: string): string {
  if (!md) return '';
  return md
    .replace(/^### (.+)$/gm, '<h3 style="font-size:1rem;color:#a5b4fc;margin:0.75rem 0 0.3rem">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:1.1rem;color:#c4b5fd;margin:1rem 0 0.4rem">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:1.25rem;color:#f8fafc;margin:1.2rem 0 0.5rem">$1</h1>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#f8fafc">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:rgba(139,92,246,0.2);color:#c4b5fd;padding:0.1rem 0.4rem;border-radius:4px;font-size:0.88em">$1</code>')
    .replace(/\n{2,}/g, '<br/><br/>');
}

export const ExecutiveRecommendation: React.FC<ExecutiveRecommendationProps> = ({
  recommendation,
  requirementId,
  token,
  onAward,
}) => {
  const [isAwarding, setIsAwarding] = useState(false);
  const [awardError, setAwardError] = useState<string | null>(null);

  const summaryHtml = useMemo(() => {
    return recommendation?.summary ? markdownToHtml(recommendation.summary) : '';
  }, [recommendation?.summary]);

  if (!recommendation) return null;

  const isAlreadyAwarded = !!recommendation.awarded_supplier_id;
  const recommendedId = recommendation.recommended_supplier_id;

  const handleAward = async () => {
    if (!recommendedId || !onAward) return;
    setIsAwarding(true);
    setAwardError(null);
    try {
      await onAward(recommendedId, 'Confirmed via Executive Recommendation panel');
    } catch (e: any) {
      setAwardError(e?.message || 'Award failed');
    } finally {
      setIsAwarding(false);
    }
  };

  return (
    <div
      className="glass-card glass-card-glow"
      style={{
        padding: '2rem',
        marginBottom: '2rem',
        borderLeft: `4px solid ${isAlreadyAwarded ? '#fbbf24' : '#10b981'}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
          <Sparkles size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.3rem', color: '#f8fafc' }}>AI Executive Recommendation</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Synthesized by Recommendation Engine Agent across all received quotes, specifications, and trust signals.
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
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}
        dangerouslySetInnerHTML={{ __html: summaryHtml }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: '600', fontSize: '0.9rem' }}>
          <ShieldCheck size={20} />
          <span>Human-in-the-Loop: AI proposes; humans confirm final award.</span>
        </div>

        {isAlreadyAwarded ? (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.6rem',
            background: 'rgba(251, 191, 36, 0.12)',
            border: '1px solid rgba(251, 191, 36, 0.4)',
            padding: '0.6rem 1.2rem',
            borderRadius: '10px',
            color: '#fbbf24',
            fontWeight: '700',
            fontSize: '0.9rem',
          }}>
            <CheckCircle size={18} />
            Supplier Awarded
            {recommendation.awarded_supplier_name && (
              <span style={{ color: '#e2e8f0', fontWeight: '400', marginLeft: '0.25rem' }}>
                — {recommendation.awarded_supplier_name}
              </span>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
            {awardError && (
              <p style={{ color: '#f87171', fontSize: '0.8rem', margin: 0 }}>{awardError}</p>
            )}
            {recommendedId && onAward ? (
              <button
                className="btn btn-primary"
                onClick={handleAward}
                disabled={isAwarding}
                style={{
                  background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                  borderColor: '#fbbf24',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  fontWeight: '700',
                }}
              >
                <Award size={16} />
                {isAwarding ? 'Awarding…' : 'Confirm Final Award'}
              </button>
            ) : (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                color: '#10b981',
                fontWeight: '700',
                fontSize: '0.88rem',
              }}>
                <Lock size={14} />
                Final Award Decision Pending Human Sign-Off
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

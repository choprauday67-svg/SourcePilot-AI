import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, Clock3, Send, ShieldAlert, ChevronRight } from 'lucide-react';

interface ApprovalStep {
  id: string;
  step_number: number;
  role_required: string;
  status: 'pending' | 'approved' | 'rejected';
  comments?: string;
  decided_at?: string;
}

interface ApprovalWorkflowProps {
  rfq: any;
  token: string | null;
  onStatusChange: (newStatus: string) => void;
}

const API_BASE = '/api/v1';

const STEP_LABELS: Record<number, { title: string; description: string }> = {
  1: { title: 'Technical Review', description: 'Buyer verifies technical specifications, scope & supplier shortlist.' },
  2: { title: 'Director Approval', description: 'Director sign-off required prior to official email dispatch.' },
};

const ROLE_COLORS: Record<string, string> = {
  buyer: '#38bdf8',
  director: '#a855f7',
  admin: '#10b981',
};

export const ApprovalWorkflow: React.FC<ApprovalWorkflowProps> = ({ rfq, token, onStatusChange }) => {
  const rfqId = rfq?.id;
  const rfqStatus = rfq?.status;
  const [steps, setSteps] = useState<ApprovalStep[]>(rfq?.approvals || []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [comments, setComments] = useState<Record<number, string>>({});
  const [showCommentFor, setShowCommentFor] = useState<number | null>(null);

  // Fetch fresh approval steps from backend when status changes
  useEffect(() => {
    if (rfq?.approvals && rfq.approvals.length > 0) {
      setSteps(rfq.approvals);
      return;
    }
    if (!rfqId || !token || rfqStatus === 'draft' || rfqStatus === 'rfq_drafted') return;
    const hdrs = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
    fetch(`${API_BASE}/rfq/${rfqId}`, { headers: hdrs })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.approvals) setSteps(data.approvals); })
      .catch(() => {});
  }, [rfq?.approvals, rfqId, rfqStatus, token]);

  /** Returns true if the step is blocked by a prior incomplete step */
  const isStepBlocked = (stepNumber: number): boolean => {
    if (stepNumber <= 1) return false;
    const prev = steps.find(s => s.step_number === stepNumber - 1);
    return !prev || prev.status !== 'approved';
  };

  const headers = () => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  });

  const handleSubmitForApproval = async () => {
    if (!rfqId) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/submit-for-approval`, {
        method: 'POST',
        headers: headers(),
      });
      if (res.ok) {
        const data: ApprovalStep[] = await res.json();
        setSteps(data);
        onStatusChange('pending_approval');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveStep = async (stepNumber: number) => {
    if (!rfqId) return;
    setActionLoading(stepNumber);
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/approve-step`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ step_number: stepNumber, comments: comments[stepNumber] || '' }),
      });
      if (res.ok) {
        const updatedRfq = await res.json();
        setSteps(prev => prev.map(s => s.step_number === stepNumber ? { ...s, status: 'approved' } : s));
        onStatusChange(updatedRfq.status);
        setShowCommentFor(null);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectStep = async (stepNumber: number) => {
    if (!rfqId) return;
    if (!comments[stepNumber]) {
      setShowCommentFor(stepNumber);
      return;
    }
    setActionLoading(stepNumber);
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/reject-step`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ step_number: stepNumber, comments: comments[stepNumber] }),
      });
      if (res.ok) {
        const updatedRfq = await res.json();
        setSteps(prev => prev.map(s => s.step_number === stepNumber ? { ...s, status: 'rejected' } : s));
        onStatusChange(updatedRfq.status);
        setShowCommentFor(null);
      }
    } finally {
      setActionLoading(null);
    }
  };

  if (rfqStatus === 'sent') return null;

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <div style={{ padding: '0.5rem', borderRadius: '10px', background: 'rgba(245,158,11,0.15)', color: '#f59e0b' }}>
          <ShieldAlert size={22} />
        </div>
        <div>
          <div style={{ fontWeight: '700', color: '#f8fafc' }}>Multi-Approver Workflow</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            All approval steps must pass before this RFQ can be dispatched to suppliers.
          </div>
        </div>
      </div>

      {/* Submit for Approval CTA */}
      {(rfqStatus === 'draft' || steps.length === 0) && (
        <button
          id="submit-for-approval-btn"
          className="btn btn-secondary"
          style={{ width: '100%', justifyContent: 'center', gap: '0.5rem', marginBottom: steps.length > 0 ? '1rem' : '0' }}
          onClick={handleSubmitForApproval}
          disabled={isSubmitting}
        >
          <Send size={16} />
          {isSubmitting ? 'Submitting…' : 'Submit for Multi-Step Approval'}
        </button>
      )}

      {/* Approval Steps Pipeline */}
      {steps.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {steps.map((step, idx) => {
            const meta = STEP_LABELS[step.step_number] || { title: `Step ${step.step_number}`, description: '' };
            const roleColor = ROLE_COLORS[step.role_required] || '#94a3b8';
            const isLast = idx === steps.length - 1;

            return (
              <div key={step.id || idx}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '1rem',
                    background: 'rgba(255,255,255,0.03)',
                    border: `1px solid ${
                      step.status === 'approved'
                        ? 'rgba(16,185,129,0.35)'
                        : step.status === 'rejected'
                        ? 'rgba(239,68,68,0.35)'
                        : 'rgba(255,255,255,0.07)'
                    }`,
                    borderRadius: '10px',
                    padding: '1rem 1.25rem',
                  }}
                >
                  {/* Step Icon */}
                  <div style={{ flexShrink: 0, paddingTop: '2px' }}>
                    {step.status === 'approved' ? (
                      <CheckCircle2 size={22} color="#10b981" />
                    ) : step.status === 'rejected' ? (
                      <XCircle size={22} color="#ef4444" />
                    ) : (
                      <Clock3 size={22} color="#f59e0b" />
                    )}
                  </div>

                  {/* Step Info */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: '700', color: '#f8fafc', fontSize: '0.95rem' }}>
                        Step {step.step_number}: {meta.title}
                      </span>
                      <span
                        style={{
                          background: `${roleColor}20`,
                          color: roleColor,
                          border: `1px solid ${roleColor}40`,
                          padding: '1px 8px',
                          borderRadius: '8px',
                          fontSize: '0.72rem',
                          fontWeight: '700',
                          textTransform: 'uppercase',
                        }}
                      >
                        {step.role_required}
                      </span>
                      <span
                        style={{
                          marginLeft: 'auto',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          color: step.status === 'approved' ? '#10b981' : step.status === 'rejected' ? '#ef4444' : '#f59e0b',
                        }}
                      >
                        {step.status.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: step.status === 'pending' ? '0.75rem' : '0' }}>
                      {meta.description}
                    </div>

                    {/* Action Buttons for pending steps */}
                    {step.status === 'pending' && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {isStepBlocked(step.step_number) ? (
                          // Sequential lock — prior step not yet approved
                          <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            padding: '0.5rem 0.75rem',
                            background: 'rgba(100,116,139,0.1)',
                            border: '1px dashed rgba(100,116,139,0.3)',
                            borderRadius: '8px',
                            fontSize: '0.82rem',
                            color: '#64748b',
                          }}>
                            <Clock3 size={14} />
                            Locked — Step {step.step_number - 1} must be approved first.
                          </div>
                        ) : (
                          <>
                            {showCommentFor === step.step_number && (
                              <textarea
                                placeholder="Enter rejection reason (required for rejection)…"
                                value={comments[step.step_number] || ''}
                                onChange={e => setComments(prev => ({ ...prev, [step.step_number]: e.target.value }))}
                                className="form-textarea"
                                rows={2}
                                style={{ fontSize: '0.85rem', resize: 'vertical' }}
                              />
                            )}

                            <div style={{ display: 'flex', gap: '0.6rem' }}>
                              <button
                                id={`approve-step-${step.step_number}-btn`}
                                className="btn btn-emerald"
                                style={{ fontSize: '0.83rem', padding: '0.45rem 1rem' }}
                                onClick={() => handleApproveStep(step.step_number)}
                                disabled={actionLoading === step.step_number}
                              >
                                <CheckCircle2 size={14} />
                                {actionLoading === step.step_number ? 'Processing…' : 'Approve Step'}
                              </button>

                              <button
                                id={`reject-step-${step.step_number}-btn`}
                                className="btn btn-secondary"
                                style={{ fontSize: '0.83rem', padding: '0.45rem 1rem', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}
                                onClick={() => handleRejectStep(step.step_number)}
                                disabled={actionLoading === step.step_number}
                              >
                                <XCircle size={14} />
                                Reject Step
                              </button>

                              {showCommentFor !== step.step_number && (
                                <button
                                  style={{
                                    background: 'none',
                                    border: '1px solid var(--border-color)',
                                    borderRadius: '8px',
                                    color: '#64748b',
                                    padding: '0.45rem 0.75rem',
                                    cursor: 'pointer',
                                    fontSize: '0.8rem',
                                  }}
                                  onClick={() => setShowCommentFor(step.step_number)}
                                >
                                  + Add Note
                                </button>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    )}

                    {step.comments && (
                      <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>
                        "{step.comments}"
                      </div>
                    )}
                  </div>
                </div>

                {/* Pipeline Arrow */}
                {!isLast && (
                  <div style={{ display: 'flex', justifyContent: 'center', margin: '0.25rem 0' }}>
                    <ChevronRight size={16} color="#334155" style={{ transform: 'rotate(90deg)' }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

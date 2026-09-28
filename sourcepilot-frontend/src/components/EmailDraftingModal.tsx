import React, { useState, useEffect, useCallback } from 'react';
import { Send, Edit3, CheckCircle2, ShieldCheck, Mail, AlertTriangle, X } from 'lucide-react';

interface EmailDraftingModalProps {
  rfq: any;
  isOpen: boolean;
  token: string | null;
  onClose: () => void;
  onDispatchComplete?: () => void;
}

const API_BASE = '/api/v1';

function cleanEmailBody(text: string): string {
  if (!text) return '';
  return text
    .replace(/^\s*---\s*$/gm, '')
    .replace(/^###\s*\d*\.?\s*(.+)$/gm, '\n$1:')
    .replace(/^##\s*(.+)$/gm, '\n$1:')
    .replace(/^#\s*(.+)$/gm, '$1')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export const EmailDraftingModal: React.FC<EmailDraftingModalProps> = ({
  rfq,
  isOpen,
  token,
  onClose,
  onDispatchComplete,
}) => {
  const [drafts, setDrafts] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [sendingDraftId, setSendingDraftId] = useState<string | null>(null);
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const getHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  const fetchDraftsAndAccounts = useCallback(async () => {
    if (!token || !rfq?.id) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch connected accounts
      const accRes = await fetch(`${API_BASE}/connected-accounts/`, { headers: getHeaders() });
      if (accRes.ok) {
        const list = await accRes.json();
        setAccounts(list);
        if (list.length > 0) setSelectedAccountId(list[0].id);
      }

      // 2. Fetch or generate drafts
      let draftRes = await fetch(`${API_BASE}/email-drafts/rfq/${rfq.id}`, { headers: getHeaders() });
      if (draftRes.ok) {
        let draftList = await draftRes.json();
        if (draftList.length === 0) {
          // Generate draft proposals via AI Agent
          const genRes = await fetch(`${API_BASE}/email-drafts/generate/${rfq.id}`, {
            method: 'POST',
            headers: getHeaders(),
          });
          if (genRes.ok) draftList = await genRes.json();
        }
        setDrafts(draftList);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to load email drafts');
    } finally {
      setLoading(false);
    }
  }, [token, rfq?.id, getHeaders]);

  useEffect(() => {
    if (isOpen) {
      fetchDraftsAndAccounts();
    }
  }, [isOpen, fetchDraftsAndAccounts]);

  const handleStartEdit = (draft: any) => {
    setEditingDraftId(draft.id);
    setEditSubject(draft.subject);
    setEditBody(draft.body_markdown);
  };

  const handleSaveEdit = async (draftId: string) => {
    try {
      const res = await fetch(`${API_BASE}/email-drafts/${draftId}`, {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ subject: editSubject, body_markdown: editBody }),
      });
      if (res.ok) {
        const updated = await res.json();
        setDrafts(prev => prev.map(d => d.id === draftId ? updated : d));
        setEditingDraftId(null);
      }
    } catch (e: any) {
      setErrorMsg(e?.message || 'Failed to save revision');
    }
  };

  const handleApproveAndSend = async (draftId: string) => {
    setSendingDraftId(draftId);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/email-drafts/${draftId}/approve-and-send`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          connected_account_id: selectedAccountId || undefined,
          approval_notes: 'Explicit human approval via Email Drafting Modal',
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setDrafts(prev => prev.map(d => d.id === draftId ? updated : d));
        onDispatchComplete?.();
      } else {
        const errData = await res.json();
        setErrorMsg(errData.detail || 'Dispatch failed');
      }
    } catch (e: any) {
      setErrorMsg(e?.message || 'Dispatch error');
    } finally {
      setSendingDraftId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="glass-card modal-content" style={{ maxWidth: '850px', width: '90%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', margin: 0, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <ShieldCheck size={24} color="#10b981" />
              Human-in-the-Loop Email Review & Approval Panel
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.2rem', margin: 0 }}>
              AI agents propose supplier email drafts. Review, edit, select mailbox, and grant explicit human approval for each dispatch.
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px', padding: '0.75rem 1rem', color: '#ef4444', marginBottom: '1rem', fontSize: '0.85rem'
          }}>
            {errorMsg}
          </div>
        )}

        {/* Mailbox Selector */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.75rem',
          background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)',
          borderRadius: '10px', padding: '0.75rem 1rem', marginBottom: '1.25rem'
        }}>
          <Mail size={18} color="#38bdf8" />
          <span style={{ fontSize: '0.88rem', fontWeight: '600', color: '#f8fafc' }}>Send Outbound Emails From:</span>
          <select
            value={selectedAccountId}
            onChange={e => setSelectedAccountId(e.target.value)}
            style={{
              background: '#0b1120', border: '1px solid var(--border-color)',
              borderRadius: '8px', color: '#f8fafc', padding: '0.4rem 0.75rem',
              fontSize: '0.85rem', flex: 1
            }}
          >
            {accounts.length > 0 ? (
              accounts.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.provider.toUpperCase()}: {acc.email_address} (Connected Mailbox)
                </option>
              ))
            ) : (
              <option value="">SourcePilot Sandbox (Mailtrap SMTP Fallback)</option>
            )}
          </select>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
            Loading supplier email drafts…
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '60vh', overflowY: 'auto', paddingRight: '0.25rem' }}>
            {drafts.map(draft => {
              const isSent = draft.delivery_status === 'sent';
              const isSending = sendingDraftId === draft.id;

              return (
                <div
                  key={draft.id}
                  className="glass-card"
                  style={{
                    padding: '1.25rem',
                    borderLeft: isSent ? '4px solid #10b981' : '4px solid #f59e0b',
                    background: 'rgba(7, 10, 17, 0.75)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                        <h4 style={{ fontSize: '1.05rem', color: '#f8fafc', margin: 0 }}>
                          {draft.supplier_name || 'Supplier'}
                        </h4>
                        <span style={{
                          background: isSent ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                          color: isSent ? '#10b981' : '#f59e0b',
                          border: `1px solid ${isSent ? '#10b98140' : '#f59e0b40'}`,
                          padding: '2px 8px', borderRadius: '8px', fontSize: '0.73rem', fontWeight: '700', textTransform: 'uppercase'
                        }}>
                          {draft.delivery_status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                        To: {draft.recipient_email}
                      </div>
                    </div>

                    {!isSent && (
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '0.78rem', padding: '0.35rem 0.7rem' }}
                        onClick={() => editingDraftId === draft.id ? setEditingDraftId(null) : handleStartEdit(draft)}
                      >
                        <Edit3 size={13} /> {editingDraftId === draft.id ? 'Cancel Edit' : 'Edit Email Text'}
                      </button>
                    )}
                  </div>

                  {editingDraftId === draft.id ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.5rem' }}>
                      <input
                        className="form-input"
                        value={editSubject}
                        onChange={e => setEditSubject(e.target.value)}
                        placeholder="Subject line"
                        style={{ fontSize: '0.88rem' }}
                      />
                      <textarea
                        className="form-textarea"
                        rows={6}
                        value={editBody}
                        onChange={e => setEditBody(e.target.value)}
                        style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
                      />
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setEditingDraftId(null)}>Cancel</button>
                        <button className="btn btn-primary" onClick={() => handleSaveEdit(draft.id)}>Save Revision</button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: '600', color: '#e2e8f0', marginBottom: '0.5rem' }}>
                        Subject: {draft.subject}
                      </div>
                      <div style={{
                        background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '0.85rem',
                        fontSize: '0.83rem', color: '#cbd5e1', whiteSpace: 'pre-wrap', lineHeight: '1.5',
                        fontFamily: 'Inter, sans-serif'
                      }}>
                        {cleanEmailBody(draft.body_markdown)}
                      </div>
                    </div>
                  )}

                  {/* Dispatch Action */}
                  <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <ShieldCheck size={14} color="#10b981" />
                      {isSent ? `Human Approved & Dispatched at ${new Date(draft.sent_at).toLocaleTimeString()}` : 'Awaiting Explicit Human Approval'}
                    </div>

                    {!isSent && (
                      <button
                        className="btn btn-primary anim-pulse"
                        style={{ background: 'linear-gradient(135deg, #10b981, #059669)', borderColor: '#10b981' }}
                        onClick={() => handleApproveAndSend(draft.id)}
                        disabled={isSending}
                      >
                        <Send size={15} />
                        {isSending ? 'Sending via Mailbox…' : 'Approve & Send Email'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
};

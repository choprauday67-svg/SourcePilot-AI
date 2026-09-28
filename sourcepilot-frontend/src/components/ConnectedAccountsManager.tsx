import React, { useState, useEffect, useCallback } from 'react';
import { Mail, CheckCircle2, AlertCircle, Trash2, Plus, RefreshCw, ShieldCheck } from 'lucide-react';

interface ConnectedAccountsManagerProps {
  token: string | null;
  onAccountsChange?: () => void;
}

const API_BASE = '/api/v1';

export const ConnectedAccountsManager: React.FC<ConnectedAccountsManagerProps> = ({
  token,
  onAccountsChange,
}) => {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState<string | null>(null);

  const getHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  const fetchAccounts = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/connected-accounts/`, { headers: getHeaders() });
      if (res.ok) {
        const list = await res.json();
        setAccounts(list);
        onAccountsChange?.();
      }
    } catch (err) {
      console.error('Failed to fetch connected accounts:', err);
    } finally {
      setLoading(false);
    }
  }, [token, getHeaders, onAccountsChange]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const handleConnectProvider = async (provider: 'gmail' | 'outlook') => {
    if (!token) return;
    setAuthLoading(provider);
    try {
      const res = await fetch(`${API_BASE}/connected-accounts/oauth/authorize/${provider}`, {
        headers: getHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.authorization_url) {
          window.location.href = data.authorization_url;
        }
      }
    } catch (err) {
      console.error(`OAuth connect error for ${provider}:`, err);
    } finally {
      setAuthLoading(null);
    }
  };

  const handleDisconnect = async (accountId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/connected-accounts/${accountId}`, {
        method: 'DELETE',
        headers: getHeaders(),
      });
      if (res.ok || res.status === 204) {
        setAccounts(prev => prev.filter(a => a.id !== accountId));
        onAccountsChange?.();
      }
    } catch (err) {
      console.error('Disconnect error:', err);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.25rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{ padding: '0.4rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
            <Mail size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', margin: 0 }}>User-Scoped Connected Mailboxes</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
              Send approved RFQs and sync replies from your personal Gmail or Outlook account.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
            onClick={() => handleConnectProvider('gmail')}
            disabled={authLoading === 'gmail'}
          >
            <Plus size={14} />
            {authLoading === 'gmail' ? 'Connecting…' : 'Connect Gmail'}
          </button>

          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
            onClick={() => handleConnectProvider('outlook')}
            disabled={authLoading === 'outlook'}
          >
            <Plus size={14} />
            {authLoading === 'outlook' ? 'Connecting…' : 'Connect Outlook'}
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '0.5rem' }}>Loading connected accounts…</div>
      ) : accounts.length === 0 ? (
        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px dashed rgba(255,255,255,0.1)',
          borderRadius: '8px',
          padding: '0.85rem 1rem',
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={16} color="#f59e0b" />
          No connected mailboxes found for your user account. Outbound emails will default to Mailtrap Sandbox.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {accounts.map(acc => (
            <div
              key={acc.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(7, 10, 17, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '8px',
                padding: '0.6rem 0.85rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span style={{
                  background: acc.provider === 'gmail' ? 'rgba(239,68,68,0.15)' : 'rgba(56,189,248,0.15)',
                  color: acc.provider === 'gmail' ? '#ef4444' : '#38bdf8',
                  padding: '2px 8px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                }}>
                  {acc.provider}
                </span>
                <span style={{ fontWeight: '600', color: '#f8fafc', fontSize: '0.88rem' }}>
                  {acc.email_address}
                </span>
                <span style={{
                  display: 'flex', alignItems: 'center', gap: '0.25rem',
                  color: '#10b981', fontSize: '0.78rem', fontWeight: '600'
                }}>
                  <CheckCircle2 size={13} /> Active
                </span>
              </div>

              <button
                onClick={() => handleDisconnect(acc.id)}
                title="Revoke & Disconnect Mailbox"
                style={{
                  background: 'none',
                  border: '1px solid rgba(239,68,68,0.3)',
                  borderRadius: '6px',
                  color: '#ef4444',
                  padding: '0.3rem 0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.78rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <Trash2 size={13} /> Disconnect
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

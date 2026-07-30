import React, { useState, useEffect } from 'react';
import { Bookmark, BookmarkCheck, Globe, MapPin, Tag, Plus, Filter, Link2, Trash2, Award } from 'lucide-react';

interface SavedSupplierLibraryProps {
  token: string | null;
  requirementId?: string;
  onAttachSuppliers?: (count: number) => void;
  onRefreshLibrary?: () => void;
}

const API_BASE = '/api/v1';

const STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  preferred:   { bg: 'rgba(16, 185, 129, 0.15)',  color: '#10b981' },
  approved:    { bg: 'rgba(56, 189, 248, 0.15)',   color: '#38bdf8' },
  blacklisted: { bg: 'rgba(239, 68, 68, 0.15)',    color: '#ef4444' },
  under_review:{ bg: 'rgba(245, 158, 11, 0.15)',   color: '#f59e0b' },
};

export const SavedSupplierLibrary: React.FC<SavedSupplierLibraryProps> = ({
  token,
  requirementId,
  onAttachSuppliers,
}) => {
  const [library, setLibrary] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [isAttaching, setIsAttaching] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const headers = () => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  });

  const fetchLibrary = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const url = categoryFilter
        ? `${API_BASE}/saved-suppliers/?category=${encodeURIComponent(categoryFilter)}`
        : `${API_BASE}/saved-suppliers/`;
      const res = await fetch(url, { headers: headers() });
      if (res.ok) setLibrary(await res.json());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLibrary(); }, [token, categoryFilter]);

  const toggleSelect = (supplierId: string) => {
    setSelectedIds(prev =>
      prev.includes(supplierId) ? prev.filter(id => id !== supplierId) : [...prev, supplierId]
    );
  };

  const handleRemove = async (supplierId: string) => {
    await fetch(`${API_BASE}/saved-suppliers/${supplierId}`, {
      method: 'DELETE',
      headers: headers(),
    });
    setLibrary(prev => prev.filter(s => s.supplier_id !== supplierId));
    setSelectedIds(prev => prev.filter(id => id !== supplierId));
    onAttachSuppliers?.(0);
  };

  const handleAttach = async () => {
    if (!requirementId || selectedIds.length === 0) return;
    setIsAttaching(true);
    try {
      const res = await fetch(`${API_BASE}/saved-suppliers/attach-to-requirement/${requirementId}`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ supplier_ids: selectedIds }),
      });
      if (res.ok) {
        setSuccessMsg(`✅ Attached ${selectedIds.length} supplier(s) directly to current requirement.`);
        onAttachSuppliers?.(selectedIds.length);
        setTimeout(() => setSuccessMsg(''), 4000);
      }
    } finally {
      setIsAttaching(false);
    }
  };

  const categories = [...new Set(library.map(s => s.category).filter(Boolean))];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <BookmarkCheck size={22} color="#10b981" />
            Saved Supplier Library
            <span style={{ fontSize: '0.9rem', fontWeight: '400', color: '#64748b' }}>({library.length} saved)</span>
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Your organisation's pre-vetted supplier directory. Select and attach directly to any active requirement.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Category filter */}
          <div style={{ position: 'relative' }}>
            <Filter size={14} style={{ position: 'absolute', left: '0.65rem', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: '#e2e8f0',
                padding: '0.5rem 0.75rem 0.5rem 2rem',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              <option value="">All Categories</option>
              {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
            </select>
          </div>

          {requirementId && selectedIds.length > 0 && (
            <button
              className="btn btn-emerald"
              onClick={handleAttach}
              disabled={isAttaching}
              id="attach-saved-suppliers-btn"
            >
              <Link2 size={16} />
              {isAttaching ? 'Attaching…' : `Attach ${selectedIds.length} to Requirement`}
            </button>
          )}
        </div>
      </div>

      {successMsg && (
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          borderRadius: '10px',
          padding: '0.85rem 1.25rem',
          color: '#10b981',
          marginBottom: '1.25rem',
          fontWeight: '600',
          fontSize: '0.9rem',
        }}>
          {successMsg}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>⏳</div>
          Loading saved suppliers…
        </div>
      ) : library.length === 0 ? (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Bookmark size={40} style={{ marginBottom: '1rem', opacity: 0.4 }} />
          <p style={{ fontSize: '1rem' }}>No saved suppliers yet.</p>
          <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
            After discovering suppliers, use the bookmark icon on any supplier card to add them here.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {library.map(entry => {
            const sup = entry.supplier || {};
            const isSelected = selectedIds.includes(entry.supplier_id);
            const statusStyle = STATUS_COLORS[entry.status] || STATUS_COLORS['preferred'];

            return (
              <div
                key={entry.id}
                className="glass-card"
                style={{
                  padding: '1.25rem',
                  borderLeft: isSelected ? '3px solid #10b981' : '3px solid transparent',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer',
                  position: 'relative',
                }}
                onClick={() => toggleSelect(entry.supplier_id)}
              >
                {/* Select indicator */}
                <div style={{
                  position: 'absolute',
                  top: '1rem',
                  right: '1rem',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  border: `2px solid ${isSelected ? '#10b981' : 'rgba(255,255,255,0.2)'}`,
                  background: isSelected ? '#10b981' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                }}>
                  {isSelected && <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff' }} />}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', paddingRight: '2rem' }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(56,189,248,0.2), rgba(99,102,241,0.2))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '1.1rem', fontWeight: '700', color: '#38bdf8',
                  }}>
                    {(sup.company_name || 'S')[0]}
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', color: '#f8fafc', fontSize: '1rem' }}>{sup.company_name || '—'}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <MapPin size={11} /> {sup.location_city || '—'}, {sup.location_country || '—'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
                  <span style={{
                    ...statusStyle,
                    padding: '2px 10px',
                    borderRadius: '10px',
                    fontSize: '0.73rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}>
                    {entry.status || 'preferred'}
                  </span>
                  {entry.category && (
                    <span style={{
                      background: 'rgba(99, 102, 241, 0.12)',
                      color: '#818cf8',
                      padding: '2px 10px',
                      borderRadius: '10px',
                      fontSize: '0.73rem',
                      fontWeight: '600',
                    }}>
                      <Tag size={10} style={{ display: 'inline', marginRight: '3px' }} />
                      {entry.category}
                    </span>
                  )}
                  {(entry.tags || []).slice(0, 2).map((tag: string, i: number) => (
                    <span key={i} style={{
                      background: 'rgba(148,163,184,0.08)',
                      color: '#94a3b8',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontSize: '0.72rem',
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>

                {entry.notes && (
                  <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.75rem', lineHeight: '1.4' }}>
                    {entry.notes}
                  </p>
                )}

                {sup.canonical_domain && (
                  <div style={{ fontSize: '0.8rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Globe size={12} /> {sup.canonical_domain}
                  </div>
                )}

                {/* Remove button */}
                <button
                  onClick={e => { e.stopPropagation(); handleRemove(entry.supplier_id); }}
                  title="Remove from library"
                  style={{
                    position: 'absolute',
                    bottom: '1rem',
                    right: '1rem',
                    background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.2)',
                    borderRadius: '6px',
                    color: '#ef4444',
                    padding: '4px 6px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

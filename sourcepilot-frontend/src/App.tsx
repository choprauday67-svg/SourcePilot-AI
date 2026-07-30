import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { RequirementForm } from './components/RequirementForm';
import { StructuredRequirementModal } from './components/StructuredRequirementModal';
import { SupplierCard } from './components/SupplierCard';
import { RFQEditor } from './components/RFQEditor';
import { ComparisonTable } from './components/ComparisonTable';
import { ExecutiveRecommendation } from './components/ExecutiveRecommendation';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { CommentThread } from './components/CommentThread';
import { SavedSupplierLibrary } from './components/SavedSupplierLibrary';
import { MarketIntelligenceCard } from './components/MarketIntelligenceCard';
import { Folder } from 'lucide-react';

const API_BASE = '/api/v1';
const STORAGE_TOKEN_KEY = 'sourcepilot_token';
const STORAGE_TAB_KEY = 'sourcepilot_activeTab';
const STORAGE_REQ_KEY = 'sourcepilot_activeReqId';

export function App() {
  const [activeTab, setActiveTab] = useState<string>(
    () => localStorage.getItem(STORAGE_TAB_KEY) || 'requirements'
  );
  // Initialise token from localStorage so refresh doesn't lose auth
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(STORAGE_TOKEN_KEY)
  );

  const [requirementsList, setRequirementsList] = useState<any[]>([]);
  const [currentRequirement, setCurrentRequirement] = useState<any>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [rankedMatches, setRankedMatches] = useState<any[]>([]);
  const [selectedSupplierIds, setSelectedSupplierIds] = useState<string[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);

  const [rfq, setRfq] = useState<any>(null);
  const [isSendingRFQ, setIsSendingRFQ] = useState(false);

  const [quotations, setQuotations] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);

  const [savedSupplierIds, setSavedSupplierIds] = useState<string[]>([]);

  const handleSetActiveTab = (tab: string) => {
    setActiveTab(tab);
    localStorage.setItem(STORAGE_TAB_KEY, tab);
  };

  const persistToken = (t: string) => {
    setToken(t);
    localStorage.setItem(STORAGE_TOKEN_KEY, t);
  };

  const getHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  // ─── 1. Auth — register once, then login on subsequent loads ─
  useEffect(() => {
    // If we already have a stored token, validate it is still alive
    if (token) {
      fetch(`${API_BASE}/requirements`, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      }).then(r => {
        if (r.status === 401) {
          // Token expired — re-login
          localStorage.removeItem(STORAGE_TOKEN_KEY);
          setToken(null);
        }
      }).catch(() => {});
      return;
    }

    async function initAuth() {
      try {
        const regRes = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            org_name: 'Acme Procurement Corp',
            email: 'buyer@acmeprocure.com',
            password: 'Password123!',
            full_name: 'Alex Rivera',
          }),
        });
        if (regRes.ok) {
          persistToken((await regRes.json()).access_token);
          return;
        }
        const loginRes = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'buyer@acmeprocure.com', password: 'Password123!' }),
        });
        if (loginRes.ok) {
          persistToken((await loginRes.json()).access_token);
        }
      } catch (err) {
        console.error('Auth init error:', err);
      }
    }
    initAuth();
  }, [token]);

  // ─── 2. Fetch Saved Supplier IDs ───────────────────────────
  const fetchSavedSuppliers = useCallback(async (tok?: string) => {
    const t = tok ?? token;
    if (!t) return;
    try {
      const res = await fetch(`${API_BASE}/saved-suppliers/`, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
      });
      if (res.ok) {
        const list = await res.json();
        const ids = list.map((item: any) => item.supplier_id || item.supplier?.id).filter(Boolean);
        setSavedSupplierIds(ids);
      }
    } catch (err) {
      console.error('Saved suppliers fetch error:', err);
    }
  }, [token]);

  // ─── 3. Load All Data for Active Requirement ───────────────
  const loadRequirementState = useCallback(async (reqId: string, reqObj?: any) => {
    if (!token || !reqId) return;
    localStorage.setItem(STORAGE_REQ_KEY, reqId);

    // Fetch fresh requirement detail from API (not just the list snapshot)
    try {
      const rRes = await fetch(`${API_BASE}/requirements/${reqId}`, { headers: getHeaders() });
      if (rRes.ok) {
        const freshReq = await rRes.json();
        setCurrentRequirement(freshReq);
      } else if (reqObj) {
        setCurrentRequirement(reqObj);
      }
    } catch {
      if (reqObj) setCurrentRequirement(reqObj);
    }

    // Ranked suppliers
    try {
      const supRes = await fetch(`${API_BASE}/requirements/${reqId}/suppliers`, { headers: getHeaders() });
      if (supRes.ok) {
        const matches = await supRes.json();
        setRankedMatches(matches);
        const selected = matches.filter((m: any) => m.selected_by_user).map((m: any) => m.supplier?.id).filter(Boolean);
        setSelectedSupplierIds(selected.length > 0 ? selected : matches.map((m: any) => m.supplier?.id).filter(Boolean));
      } else {
        setRankedMatches([]);
      }
    } catch {
      setRankedMatches([]);
    }

    // RFQ & approvals
    try {
      const rfqRes = await fetch(`${API_BASE}/rfq/requirement/${reqId}`, { headers: getHeaders() });
      if (rfqRes.ok) {
        setRfq(await rfqRes.json());
      } else {
        setRfq(null);
      }
    } catch {
      setRfq(null);
    }

    // Quotations + recommendation
    try {
      const qRes = await fetch(`${API_BASE}/quotations/requirement/${reqId}`, { headers: getHeaders() });
      if (qRes.ok) {
        const qList = await qRes.json();
        setQuotations(qList);
        if (qList.length > 0) {
          try {
            const recRes = await fetch(`${API_BASE}/quotations/recommendation/${reqId}`, { headers: getHeaders() });
            if (recRes.ok) setRecommendation(await recRes.json());
            else setRecommendation(null);
          } catch { setRecommendation(null); }
        } else {
          setRecommendation(null);
        }
      } else {
        setQuotations([]);
        setRecommendation(null);
      }
    } catch {
      setQuotations([]);
      setRecommendation(null);
    }
  }, [token, getHeaders]);

  // ─── 4. Initial Hydration on Token Ready ───────────────────
  useEffect(() => {
    if (!token) return;

    async function hydrateState() {
      fetchSavedSuppliers(token!);

      try {
        const res = await fetch(`${API_BASE}/requirements`, { headers: getHeaders() });
        if (res.ok) {
          const reqs = await res.json();
          setRequirementsList(reqs);
          if (reqs.length > 0) {
            const savedReqId = localStorage.getItem(STORAGE_REQ_KEY);
            const target = reqs.find((r: any) => r.id === savedReqId) || reqs[0];
            loadRequirementState(target.id, target);
          }
        }
      } catch (err) {
        console.error('Hydration error:', err);
      }
    }

    hydrateState();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // ─── 5. Requirement Submission ──────────────────────────────
  const handleRequirementSubmit = async (rawText: string) => {
    if (!token) return;
    setIsExtracting(true);
    try {
      const res = await fetch(`${API_BASE}/requirements`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ raw_text: rawText }),
      });
      if (res.ok) {
        const newReq = await res.json();
        setCurrentRequirement(newReq);
        setRequirementsList(prev => [newReq, ...prev]);
        localStorage.setItem(STORAGE_REQ_KEY, newReq.id);
        // Reset downstream state for new requirement
        setRankedMatches([]);
        setRfq(null);
        setQuotations([]);
        setRecommendation(null);
        setIsModalOpen(true);
      }
    } catch (err) { console.error('Extraction error:', err); }
    finally { setIsExtracting(false); }
  };

  // ─── 6. Confirm Discovery ──────────────────────────────────
  const handleConfirmDiscovery = async () => {
    if (!currentRequirement || !token) return;
    setIsDiscovering(true);
    try {
      const res = await fetch(
        `${API_BASE}/requirements/${currentRequirement.id}/suppliers/discover`,
        { method: 'POST', headers: getHeaders() }
      );
      if (res.ok) {
        const matches = await res.json();
        setRankedMatches(matches);
        setIsModalOpen(false);
        handleSetActiveTab('suppliers');
        setSelectedSupplierIds(matches.map((m: any) => m.supplier?.id).filter(Boolean));
        setCurrentRequirement((prev: any) => ({ ...prev, status: 'ranked' }));
        setRequirementsList(prev =>
          prev.map(r => r.id === currentRequirement.id ? { ...r, status: 'ranked' } : r)
        );
      }
    } catch (err) { console.error('Discovery error:', err); }
    finally { setIsDiscovering(false); }
  };

  // ─── 7. Supplier Select & Save/Bookmark ────────────────────
  const handleToggleSupplierSelect = (supplierId: string) =>
    setSelectedSupplierIds(prev =>
      prev.includes(supplierId) ? prev.filter(id => id !== supplierId) : [...prev, supplierId]
    );

  const handleToggleSaveSupplier = async (supplierId: string) => {
    if (!token) return;
    const isSaved = savedSupplierIds.includes(supplierId);
    if (isSaved) {
      // Optimistic unsave
      setSavedSupplierIds(prev => prev.filter(id => id !== supplierId));
      try {
        const res = await fetch(`${API_BASE}/saved-suppliers/${supplierId}`, {
          method: 'DELETE',
          headers: getHeaders(),
        });
        if (res.ok || res.status === 204) {
          fetchSavedSuppliers();
        } else {
          // Revert optimistic change on failure
          setSavedSupplierIds(prev => [...prev, supplierId]);
        }
      } catch {
        setSavedSupplierIds(prev => [...prev, supplierId]);
      }
    } else {
      // Optimistic save
      setSavedSupplierIds(prev => [...prev, supplierId]);
      const cat = currentRequirement?.structured_data?.category
        || currentRequirement?.category
        || 'General';
      try {
        const res = await fetch(`${API_BASE}/saved-suppliers/`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({
            supplier_id: supplierId,
            category: cat,
            status: 'preferred',
            notes: `Saved from discovery shortlist for: ${currentRequirement?.title || 'requirement'}`,
          }),
        });
        if (res.ok || res.status === 201) {
          fetchSavedSuppliers();
        } else {
          // Revert optimistic change on failure
          setSavedSupplierIds(prev => prev.filter(id => id !== supplierId));
        }
      } catch {
        setSavedSupplierIds(prev => prev.filter(id => id !== supplierId));
      }
    }
  };

  // ─── 8. Generate / View RFQ (Lifecycle-Aware) ─────────────
  const handleGenerateRFQ = async () => {
    if (!currentRequirement || !token) return;
    // If an RFQ document already exists for this requirement, switch to RFQ tab directly
    if (rfq) {
      handleSetActiveTab('rfq');
      return;
    }
    const res = await fetch(`${API_BASE}/rfq/generate/${currentRequirement.id}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (res.ok) {
      const rfqData = await res.json();
      setRfq(rfqData);
      setCurrentRequirement((prev: any) => ({ ...prev, status: 'rfq_drafted' }));
      setRequirementsList(prev =>
        prev.map(r => r.id === currentRequirement.id ? { ...r, status: 'rfq_drafted' } : r)
      );
      handleSetActiveTab('rfq');
    }
  };

  const getRfqButtonLabel = () => {
    if (!rfq) {
      return `Draft RFQ for Selected (${selectedSupplierIds.length})`;
    }
    const st = rfq.status || currentRequirement?.status;
    if (st === 'sent' || st === 'rfq_sent') return 'View Dispatched RFQ Document';
    if (st === 'approved') return 'View Approved RFQ Document';
    if (st === 'pending_approval') return 'View Pending RFQ Approval';
    return 'View RFQ Draft';
  };

  // ─── 9. RFQ Status Change ──────────────────────────────────
  const handleRFQStatusChange = (newStatus: string) => {
    setRfq((prev: any) => prev ? { ...prev, status: newStatus } : prev);
    setCurrentRequirement((prev: any) => prev ? { ...prev, status: newStatus } : prev);
    setRequirementsList(prev =>
      prev.map(r => r.id === currentRequirement?.id ? { ...r, status: newStatus } : r)
    );
  };

  // ─── 10. Send RFQ ──────────────────────────────────────────
  const handleSendRFQ = async (rfqId: string) => {
    setIsSendingRFQ(true);
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/send`, {
        method: 'POST',
        headers: getHeaders(),
      });
      if (res.ok) {
        setRfq((prev: any) => ({ ...prev, status: 'sent' }));
        setCurrentRequirement((prev: any) => ({ ...prev, status: 'rfq_sent' }));

        // Create an initial quotation for the top-ranked supplier (demo flow)
        if (rankedMatches.length > 0 && currentRequirement) {
          const supId = rankedMatches[0].supplier?.id;
          if (supId) {
            await fetch(`${API_BASE}/quotations/manual`, {
              method: 'POST',
              headers: getHeaders(),
              body: JSON.stringify({
                requirement_id: currentRequirement.id,
                supplier_id: supId,
                unit_price: 24.50,
                total_price: 12250.0,
                currency: 'USD',
                moq: '100 units',
                lead_time_days: 14,
                warranty: '1 Year',
                payment_terms: 'Net 30',
              }),
            });
          }
          const qRes = await fetch(
            `${API_BASE}/quotations/requirement/${currentRequirement.id}`,
            { headers: getHeaders() }
          );
          if (qRes.ok) {
            const qList = await qRes.json();
            setQuotations(qList);
            if (qList.length > 0) {
              const recRes = await fetch(
                `${API_BASE}/quotations/recommendation/${currentRequirement.id}`,
                { headers: getHeaders() }
              );
              if (recRes.ok) setRecommendation(await recRes.json());
            }
          }
        }
        handleSetActiveTab('quotations');
      }
    } catch (err) { console.error('Send RFQ error:', err); }
    finally { setIsSendingRFQ(false); }
  };

  // ─── 11. Award Supplier ────────────────────────────────────
  const handleAwardSupplier = async (supplierId: string, notes: string) => {
    if (!currentRequirement || !token) return;
    const res = await fetch(`${API_BASE}/quotations/award/${currentRequirement.id}`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ supplier_id: supplierId, notes }),
    });
    if (res.ok) {
      const rec = await res.json();
      setRecommendation(rec);
      setCurrentRequirement((prev: any) => ({ ...prev, status: 'awarded' }));
      setRequirementsList(prev =>
        prev.map(r => r.id === currentRequirement.id ? { ...r, status: 'awarded' } : r)
      );
    }
  };

  // ─── 12. Analytics ─────────────────────────────────────────
  useEffect(() => {
    if (activeTab === 'analytics' && token) {
      fetch(`${API_BASE}/analytics/summary`, { headers: getHeaders() })
        .then(r => r.json())
        .then(data => setAnalytics(data))
        .catch(err => console.error('Analytics fetch error:', err));
    }
  }, [activeTab, token, getHeaders]);

  const TAB_TITLES: Record<string, string> = {
    requirements: 'Procurement Requirements',
    suppliers:    'Ranked Supplier Discovery',
    rfq:          'RFQ Document & Approval Workflow',
    quotations:   'Quotation Analysis & AI Recommendation',
    analytics:    'Procurement Spend & Price Analytics',
    library:      'Saved Supplier Library',
    intelligence: 'Market Intelligence',
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={handleSetActiveTab} />

      <main className="main-content">
        <header className="navbar">
          <div>
            <h1 style={{ fontSize: '1.6rem', color: '#f8fafc' }}>
              {TAB_TITLES[activeTab] || activeTab}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              SourcePilot AI Workspace · Category-Agnostic Sourcing Automation
            </p>
          </div>

          {requirementsList.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Folder size={15} color="#38bdf8" /> Active:
              </span>
              <select
                value={currentRequirement?.id || ''}
                onChange={e => loadRequirementState(e.target.value)}
                style={{
                  background: 'rgba(255, 255, 255, 0.06)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  color: '#f8fafc',
                  padding: '0.45rem 0.75rem',
                  fontSize: '0.85rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  maxWidth: '300px',
                }}
              >
                {requirementsList.map((r: any) => (
                  <option key={r.id} value={r.id} style={{ background: '#0b1120', color: '#f8fafc' }}>
                    {r.title} [{r.status}]
                  </option>
                ))}
              </select>
            </div>
          )}
        </header>

        {/* ── Tab: Requirements ── */}
        {activeTab === 'requirements' && (
          <div>
            <RequirementForm onSubmit={handleRequirementSubmit} isLoading={isExtracting} />
            {currentRequirement && (
              <>
                <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ fontSize: '1.1rem', color: '#f8fafc' }}>{currentRequirement.title}</h3>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                        "{currentRequirement.raw_text}"
                      </p>
                    </div>
                    <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
                      Review Extraction
                    </button>
                  </div>
                </div>
                <CommentThread requirementId={currentRequirement.id} token={token} />
              </>
            )}
          </div>
        )}

        {/* ── Tab: Supplier Discovery ── */}
        {activeTab === 'suppliers' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', color: '#f8fafc' }}>
                  Discovered & Ranked Suppliers ({rankedMatches.length})
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  Ranked by AI using explainable score factors and multi-dimensional risk radar.
                </p>
              </div>
              <button
                className="btn btn-primary"
                onClick={handleGenerateRFQ}
                disabled={rankedMatches.length === 0}
              >
                {getRfqButtonLabel()}
              </button>
            </div>

            {currentRequirement && (
              <MarketIntelligenceCard requirementId={currentRequirement.id} token={token} />
            )}

            {rankedMatches.map((m: any, idx: number) => (
              <SupplierCard
                key={m.match_id || idx}
                match={m}
                rankIndex={idx + 1}
                isSelected={selectedSupplierIds.includes(m.supplier?.id)}
                isSaved={savedSupplierIds.includes(m.supplier?.id)}
                onToggleSelect={handleToggleSupplierSelect}
                onToggleSave={handleToggleSaveSupplier}
              />
            ))}
          </div>
        )}

        {/* ── Tab: RFQ ── */}
        {activeTab === 'rfq' && (
          <div>
            {rfq ? (
              <RFQEditor
                rfq={rfq}
                token={token}
                onApprove={() => {}}
                onSend={handleSendRFQ}
                onUpdate={() => {}}
                onStatusChange={handleRFQStatusChange}
                isSending={isSendingRFQ}
              />
            ) : (
              <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>No RFQ draft yet. Discover suppliers first, then click "Draft RFQ for Selected".</p>
              </div>
            )}
          </div>
        )}

        {/* ── Tab: Quotations ── */}
        {activeTab === 'quotations' && (
          <div>
            <ExecutiveRecommendation
              recommendation={recommendation}
              requirementId={currentRequirement?.id}
              token={token}
              onAward={handleAwardSupplier}
            />
            <ComparisonTable quotations={quotations} recommendation={recommendation} />
          </div>
        )}

        {/* ── Tab: Analytics ── */}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard analytics={analytics} token={token} />
        )}

        {/* ── Tab: Saved Supplier Library ── */}
        {activeTab === 'library' && (
          <SavedSupplierLibrary
            token={token}
            requirementId={currentRequirement?.id}
            onAttachSuppliers={() => {
              fetchSavedSuppliers();
              if (currentRequirement?.id) {
                loadRequirementState(currentRequirement.id);
                handleSetActiveTab('suppliers');
              }
            }}
          />
        )}

        {/* ── Tab: Market Intelligence ── */}
        {activeTab === 'intelligence' && (
          <div>
            {currentRequirement ? (
              <MarketIntelligenceCard requirementId={currentRequirement.id} token={token} />
            ) : (
              <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>Submit a procurement requirement first to run Market Intelligence Analysis.</p>
              </div>
            )}
          </div>
        )}

        <StructuredRequirementModal
          requirement={currentRequirement}
          isOpen={isModalOpen}
          onConfirm={handleConfirmDiscovery}
          onClose={() => setIsModalOpen(false)}
          isDiscovering={isDiscovering}
        />
      </main>
    </div>
  );
}

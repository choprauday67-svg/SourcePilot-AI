import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { RequirementForm } from './components/RequirementForm';
import { StructuredRequirementModal } from './components/StructuredRequirementModal';
import { SupplierCard } from './components/SupplierCard';
import { RFQEditor } from './components/RFQEditor';
import { ComparisonTable } from './components/ComparisonTable';
import { ExecutiveRecommendation } from './components/ExecutiveRecommendation';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { Sparkles, FileText, Search, Send, Award, RefreshCw } from 'lucide-react';

const API_BASE = '/api/v1';

export function App() {
  const [activeTab, setActiveTab] = useState('requirements');
  const [token, setToken] = useState<string | null>(null);
  
  // Requirement state
  const [currentRequirement, setCurrentRequirement] = useState<any>(null);
  const [requirementsList, setRequirementsList] = useState<any[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Supplier & RFQ state
  const [rankedMatches, setRankedMatches] = useState<any[]>([]);
  const [selectedSupplierIds, setSelectedSupplierIds] = useState<string[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  
  const [rfq, setRfq] = useState<any>(null);
  const [isSendingRFQ, setIsSendingRFQ] = useState(false);

  // Quotation & Analytics state
  const [quotations, setQuotations] = useState<any[]>([]);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);

  // 1. Initial Auth setup (Auto register/login for local dev session)
  useEffect(() => {
    async function initAuth() {
      try {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            org_name: 'Acme Procurement Corp',
            email: 'buyer@acmeprocure.com',
            password: 'Password123!',
            full_name: 'Alex Rivera'
          })
        });
        if (res.ok) {
          const data = await res.json();
          setToken(data.access_token);
        } else {
          // Login if already registered
          const loginRes = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'buyer@acmeprocure.com', password: 'Password123!' })
          });
          const loginData = await loginRes.json();
          setToken(loginData.access_token);
        }
      } catch (err) {
        console.error("Auth init error:", err);
      }
    }
    initAuth();
  }, []);

  const getHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  });

  // Submit Requirement -> Extraction Agent
  const handleRequirementSubmit = async (rawText: string) => {
    if (!token) return;
    setIsExtracting(true);
    try {
      const res = await fetch(`${API_BASE}/requirements`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ raw_text: rawText })
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentRequirement(data);
        setIsModalOpen(true);
      }
    } catch (err) {
      console.error("Extraction error:", err);
    } finally {
      setIsExtracting(false);
    }
  };

  // Confirm -> Discover & Rank Suppliers
  const handleConfirmDiscovery = async () => {
    if (!currentRequirement || !token) return;
    setIsDiscovering(true);
    try {
      const res = await fetch(`${API_BASE}/requirements/${currentRequirement.id}/suppliers/discover`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (res.ok) {
        const matches = await res.json();
        setRankedMatches(matches);
        setIsModalOpen(false);
        setActiveTab('suppliers');

        // Automatically select top matches by default
        const defaultIds = matches.map((m: any) => m.supplier.id);
        setSelectedSupplierIds(defaultIds);

        // Update requirement status
        setCurrentRequirement((prev: any) => ({ ...prev, status: 'ranked' }));
      }
    } catch (err) {
      console.error("Discovery error:", err);
    } finally {
      setIsDiscovering(false);
    }
  };

  // Toggle Supplier Selection
  const handleToggleSupplierSelect = (supplierId: string) => {
    setSelectedSupplierIds(prev =>
      prev.includes(supplierId) ? prev.filter(id => id !== supplierId) : [...prev, supplierId]
    );
  };

  // Generate RFQ
  const handleGenerateRFQ = async () => {
    if (!currentRequirement || !token) return;
    try {
      const res = await fetch(`${API_BASE}/rfq/generate/${currentRequirement.id}`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (res.ok) {
        const rfqData = await res.json();
        setRfq(rfqData);
        setActiveTab('rfq');
      }
    } catch (err) {
      console.error("RFQ generation error:", err);
    }
  };

  // Approve RFQ
  const handleApproveRFQ = async (rfqId: string) => {
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/approve`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (res.ok) {
        const rfqData = await res.json();
        setRfq(rfqData);
      }
    } catch (err) {
      console.error("RFQ approval error:", err);
    }
  };

  // Dispatch RFQ via Email Agent / Mailtrap
  const handleSendRFQ = async (rfqId: string) => {
    setIsSendingRFQ(true);
    try {
      const res = await fetch(`${API_BASE}/rfq/${rfqId}/send`, {
        method: 'POST',
        headers: getHeaders()
      });
      if (res.ok) {
        setRfq((prev: any) => ({ ...prev, status: 'sent' }));
        setCurrentRequirement((prev: any) => ({ ...prev, status: 'rfq_sent' }));

        // Simulate receiving a quote & fetching recommendation
        if (rankedMatches.length > 0 && currentRequirement) {
          const supId = rankedMatches[0].supplier.id;
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
              payment_terms: 'Net 30'
            })
          });

          // Fetch quotes & recommendation
          const qRes = await fetch(`${API_BASE}/quotations/requirement/${currentRequirement.id}`, { headers: getHeaders() });
          if (qRes.ok) setQuotations(await qRes.json());

          const recRes = await fetch(`${API_BASE}/quotations/recommendation/${currentRequirement.id}`, { headers: getHeaders() });
          if (recRes.ok) setRecommendation(await recRes.json());
        }

        setActiveTab('quotations');
      }
    } catch (err) {
      console.error("Send RFQ error:", err);
    } finally {
      setIsSendingRFQ(false);
    }
  };

  // Fetch Analytics
  useEffect(() => {
    if (activeTab === 'analytics' && token) {
      fetch(`${API_BASE}/analytics/summary`, { headers: getHeaders() })
        .then(res => res.json())
        .then(data => setAnalytics(data))
        .catch(err => console.error("Analytics fetch error:", err));
    }
  }, [activeTab, token]);

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content">
        <header className="navbar">
          <div>
            <h1 style={{ fontSize: '1.6rem', color: '#f8fafc' }}>
              {activeTab === 'requirements' && 'Procurement Requirements'}
              {activeTab === 'suppliers' && 'Ranked Supplier Discovery'}
              {activeTab === 'rfq' && 'RFQ Document & Dispatch'}
              {activeTab === 'quotations' && 'Quotation Analysis & AI Recommendation'}
              {activeTab === 'analytics' && 'Procurement Spend & Cycle-time Analytics'}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              SourcePilot AI Workspace · Category-Agnostic Sourcing Automation
            </p>
          </div>

          {currentRequirement && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Active Requirement:</span>
              <span className={`badge badge-${currentRequirement.status}`}>
                {currentRequirement.title}
              </span>
            </div>
          )}
        </header>

        {/* Tab 1: Requirements Input */}
        {activeTab === 'requirements' && (
          <div>
            <RequirementForm onSubmit={handleRequirementSubmit} isLoading={isExtracting} />

            {currentRequirement && (
              <div className="glass-card" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ fontSize: '1.1rem', color: '#f8fafc' }}>{currentRequirement.title}</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                      "{currentRequirement.raw_text}"
                    </p>
                  </div>
                  <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
                    Review AI Extraction Modal
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Supplier Shortlist & Ranking */}
        {activeTab === 'suppliers' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', color: '#f8fafc' }}>Discovered & Ranked Suppliers ({rankedMatches.length})</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  Ranked by Supplier Ranking Agent using explainable score factors (Trust, Certifications, Price Signal, Lead Time).
                </p>
              </div>

              <button className="btn btn-primary" onClick={handleGenerateRFQ} disabled={rankedMatches.length === 0}>
                Draft RFQ Document for Selected ({selectedSupplierIds.length})
              </button>
            </div>

            {rankedMatches.map((m: any) => (
              <SupplierCard
                key={m.match_id}
                match={m}
                isSelected={selectedSupplierIds.includes(m.supplier.id)}
                onToggleSelect={handleToggleSupplierSelect}
              />
            ))}
          </div>
        )}

        {/* Tab 3: RFQ Document & Email Dispatch */}
        {activeTab === 'rfq' && (
          <div>
            {rfq ? (
              <RFQEditor
                rfq={rfq}
                onApprove={handleApproveRFQ}
                onSend={handleSendRFQ}
                onUpdate={() => {}}
                isSending={isSendingRFQ}
              />
            ) : (
              <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>No RFQ draft generated yet. Discover suppliers first and click "Draft RFQ Document".</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Quote Comparison & Recommendation */}
        {activeTab === 'quotations' && (
          <div>
            <ExecutiveRecommendation recommendation={recommendation} />
            <ComparisonTable quotations={quotations} recommendation={recommendation} />
          </div>
        )}

        {/* Tab 5: Spend & Cycle-time Analytics */}
        {activeTab === 'analytics' && (
          <AnalyticsDashboard analytics={analytics} />
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

import React from 'react';
import { Compass, FileText, Users, Award, BarChart3, Settings, ShieldCheck, Zap } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'requirements', label: 'Requirements', icon: FileText },
    { id: 'suppliers', label: 'Supplier Ranking', icon: Users },
    { id: 'rfq', label: 'RFQ Dispatch', icon: Compass },
    { id: 'quotations', label: 'Quote Comparison', icon: Award },
    { id: 'analytics', label: 'Spend Analytics', icon: BarChart3 },
  ];

  return (
    <aside className="sidebar">
      <div style={{ marginBottom: '2.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '36px', height: '36px', borderRadius: '10px',
          background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Zap size={22} color="#040914" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.2rem', lineHeight: '1.1' }}>SourcePilot</h2>
          <span className="brand-badge">AI Procurement</span>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className="btn"
              style={{
                justifyContent: 'flex-start',
                background: isActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                border: isActive ? '1px solid rgba(56, 189, 248, 0.3)' : '1px solid transparent',
                padding: '0.75rem 1rem'
              }}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
        <div className="glass-card" style={{ padding: '0.85rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <ShieldCheck size={20} color="#10b981" />
          <div>
            <div style={{ fontWeight: '600', color: '#f8fafc' }}>Acme Procurement</div>
            <div style={{ color: '#64748b' }}>Owner Role</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

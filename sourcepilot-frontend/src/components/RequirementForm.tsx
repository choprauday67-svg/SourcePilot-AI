import React, { useState } from 'react';
import { Sparkles, ArrowRight, Lightbulb } from 'lucide-react';

interface RequirementFormProps {
  onSubmit: (rawText: string) => void;
  isLoading: boolean;
}

export const RequirementForm: React.FC<RequirementFormProps> = ({ onSubmit, isLoading }) => {
  const [promptText, setPromptText] = useState('');

  const templates = [
    "Need 500 units of industrial-grade brushless DC motors, ISO 9001 certified, delivered to Austin, TX within 3 weeks, budget $15,000.",
    "Procure 2,000 meters of flame-retardant industrial cabling, CE & RoHS certified, required in Pune within 14 days, max budget ₹6L.",
    "Require 50 units of high-capacity stainless steel heat exchangers, ASME certified, fast turnaround to Chicago."
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (promptText.trim()) {
      onSubmit(promptText);
    }
  };

  return (
    <div className="glass-card glass-card-glow" style={{ padding: '2rem', marginBottom: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{
          padding: '0.5rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8'
        }}>
          <Sparkles size={22} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.4rem' }}>Submit Natural Language Procurement Need</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Describe your required product, quantity, delivery location, budget, and specs in plain language.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          className="form-textarea"
          rows={4}
          placeholder="e.g. Need 500 units of industrial-grade brushless DC motors, ISO 9001 certified, delivered to Austin, TX within 3 weeks, budget $15,000..."
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          style={{ marginBottom: '1.25rem' }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <Lightbulb size={16} color="#f59e0b" />
            <span>Click template shortcut:</span>
          </div>

          <button type="submit" className="btn btn-primary anim-pulse" disabled={isLoading || !promptText.trim()}>
            {isLoading ? 'AI Extracting Specs...' : 'Analyze Requirement'}
            <ArrowRight size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
          {templates.map((tpl, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setPromptText(tpl)}
              style={{
                textAlign: 'left', background: 'rgba(255, 255, 255, 0.03)', border: '1px dashed var(--border-color)',
                color: '#cbd5e1', padding: '0.5rem 0.85rem', borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer'
              }}
            >
              "{tpl}"
            </button>
          ))}
        </div>
      </form>
    </div>
  );
};

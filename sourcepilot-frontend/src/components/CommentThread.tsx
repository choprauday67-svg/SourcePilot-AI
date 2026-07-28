import React, { useState, useEffect } from 'react';
import { MessageSquare, Send, User, AtSign, CheckCircle2 } from 'lucide-react';

interface CommentThreadProps {
  requirementId: string;
  token: string | null;
}

export const CommentThread: React.FC<CommentThreadProps> = ({ requirementId, token }) => {
  const [comments, setComments] = useState<any[]>([]);
  const [body, setBody] = useState('');
  const [mentionUser, setMentionUser] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchComments = async () => {
    if (!requirementId || !token) return;
    try {
      const res = await fetch(`/api/v1/requirements/${requirementId}/comments/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setComments(await res.json());
      }
    } catch (err) {
      console.error("Error fetching comments:", err);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [requirementId, token]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim() || !token) return;

    setIsLoading(true);
    try {
      const mentions = mentionUser ? [mentionUser] : [];
      const formattedBody = mentionUser ? `@${mentionUser} ${body}` : body;

      const res = await fetch(`/api/v1/requirements/${requirementId}/comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ body: formattedBody, mentions })
      });

      if (res.ok) {
        setBody('');
        setMentionUser('');
        fetchComments();
      }
    } catch (err) {
      console.error("Error posting comment:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MessageSquare size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '1.05rem', color: '#f8fafc' }}>Team Collaboration & Discussion</h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <CheckCircle2 size={14} /> Webhook Ingestion Active
        </span>
      </div>

      {/* Existing Comments List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem', maxHeight: '220px', overflowY: 'auto' }}>
        {comments.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
            No comments yet. Start a discussion with your procurement team or mention a colleague.
          </p>
        ) : (
          comments.map((c: any) => (
            <div key={c.id} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.75rem 1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#38bdf8', fontWeight: '600' }}>
                  <User size={12} /> {c.author_id.substring(0, 8)}
                </span>
                <span>{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
              <p style={{ fontSize: '0.85rem', color: '#e2e8f0', margin: 0 }}>{c.body}</p>
            </div>
          ))
        )}
      </div>

      {/* Add Comment Form */}
      <form onSubmit={handleAddComment} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '0.4rem 0.6rem' }}>
            <AtSign size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder="Mention user..."
              value={mentionUser}
              onChange={(e) => setMentionUser(e.target.value)}
              style={{ background: 'none', border: 'none', color: '#f8fafc', fontSize: '0.8rem', width: '110px', outline: 'none' }}
            />
          </div>
          <input
            type="text"
            placeholder="Type your note or question..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            style={{ flex: 1, background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '0.5rem 0.85rem', color: '#f8fafc', fontSize: '0.85rem', outline: 'none' }}
          />
          <button type="submit" className="btn btn-primary" disabled={isLoading || !body.trim()} style={{ padding: '0.5rem 1rem' }}>
            <Send size={14} /> Post
          </button>
        </div>
      </form>
    </div>
  );
};

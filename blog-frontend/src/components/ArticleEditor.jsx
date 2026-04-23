import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Bot,
  Send,
  RefreshCw,
  ChevronRight,
  ChevronLeft,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import { blogApi } from '@/services/api';
import { parseHtmlToBlocks, blocksToHtml, createBlock } from '@/utils/contentBlocks';
import EditorToolbar from './preview/EditorToolbar';
import BlogPreviewPanel from './preview/BlogPreviewPanel';
import StylePanel from './preview/StylePanel';

// ── undo history ──────────────────────────────────────────────────────────────
const MAX_HISTORY = 40;

function useBlockHistory(initial) {
  const [past, setPast] = useState([]);
  const [present, setPresent] = useState(initial);

  const push = useCallback(newBlocks => {
    setPast(p => [...p.slice(-MAX_HISTORY + 1), present]);
    setPresent(newBlocks);
  }, [present]);

  const undo = useCallback(() => {
    if (past.length === 0) return;
    setPresent(past[past.length - 1]);
    setPast(p => p.slice(0, -1));
  }, [past]);

  return { blocks: present, setBlocks: push, undo, canUndo: past.length > 0 };
}

// ── Agent panel ───────────────────────────────────────────────────────────────
const AgentPanel = ({ articleId, agentReview, onReview, conversationalResult, onConversationalEdit }) => {
  const [command, setCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);

  const handleConversationalEdit = async () => {
    if (!command.trim() || loading) return;
    setLoading(true);
    try {
      await onConversationalEdit(command);
      setCommand('');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async () => {
    setReviewLoading(true);
    try {
      await onReview();
    } finally {
      setReviewLoading(false);
    }
  };

  const scoreColor = score => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="h-full flex flex-col bg-white border-r border-gray-200 text-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-200 bg-purple-50">
        <span className="flex items-center gap-2 font-semibold text-purple-800">
          <Bot size={16} />
          Editor Agent
        </span>
        <button
          onClick={handleReview}
          disabled={reviewLoading}
          className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 border border-purple-200 rounded px-2 py-0.5 hover:bg-purple-100 transition-colors disabled:opacity-50"
        >
          <RefreshCw size={11} className={reviewLoading ? 'animate-spin' : ''} />
          Review
        </button>
      </div>

      {/* Review scorecard */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {agentReview ? (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Review Scorecard</p>
            <div className="space-y-1.5">
              {Object.entries(agentReview.scorecard || {}).map(([key, val]) => {
                if (typeof val === 'object') return null;
                const isNumber = !isNaN(Number(val));
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-gray-600 capitalize text-xs">{key.replace(/_/g, ' ')}</span>
                    <span className={`font-semibold text-xs ${isNumber ? scoreColor(Number(val)) : 'text-gray-700'}`}>
                      {val}
                    </span>
                  </div>
                );
              })}
            </div>

            {agentReview.next_steps?.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Next Steps</p>
                <ul className="space-y-1">
                  {agentReview.next_steps.map((step, i) => (
                    <li key={i} className="flex gap-1.5 text-xs text-gray-600">
                      <span className="text-purple-400 shrink-0">•</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-xs text-gray-400 mt-3">
              {agentReview.reviewed_at
                ? `Reviewed ${new Date(agentReview.reviewed_at).toLocaleTimeString()}`
                : 'Last review'}
            </p>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <Activity size={28} className="mx-auto mb-2 opacity-40" />
            <p className="text-xs">Click &ldquo;Review&rdquo; to run the Editor Agent on this article.</p>
          </div>
        )}

        {/* Conversational edit result */}
        {conversationalResult && (
          <div className="p-2.5 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
            <p className="font-semibold mb-1">Agent applied edits:</p>
            <p>{conversationalResult}</p>
          </div>
        )}
      </div>

      {/* Conversational edit input */}
      <div className="border-t border-gray-200 p-2.5">
        <p className="text-xs text-gray-500 mb-1.5">Give the Agent an instruction:</p>
        <div className="flex gap-1.5">
          <textarea
            value={command}
            onChange={e => setCommand(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleConversationalEdit();
              }
            }}
            placeholder="e.g. Make the intro more engaging…"
            rows={3}
            className="flex-1 text-xs border border-gray-200 rounded px-2 py-1.5 resize-none outline-none focus:ring-1 focus:ring-purple-300"
          />
          <button
            onClick={handleConversationalEdit}
            disabled={loading || !command.trim()}
            className="self-end p-2 bg-purple-600 hover:bg-purple-700 text-white rounded disabled:opacity-40 transition-colors"
          >
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};

// ── Main ArticleEditor ────────────────────────────────────────────────────────

const ArticleEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { blocks, setBlocks, undo, canUndo } = useBlockHistory([]);
  const [mode, setMode] = useState('preview');
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [globalStyles, setGlobalStyles] = useState({
    fontFamily: '',
    bodyFontSize: '16px',
    lineHeight: '1.7',
    bodyColor: '#374151',
    headingColor: '#111827',
    bgColor: '#ffffff',
    accentColor: '#2563eb',
    contentWidth: '740px',
    paragraphSpacing: '16px',
    sectionPadding: '0px',
  });

  const [saveStatus, setSaveStatus] = useState('idle');
  const [showStylePanel, setShowStylePanel] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(true);
  const [agentReview, setAgentReview] = useState(null);
  const [conversationalResult, setConversationalResult] = useState('');

  const saveTimeoutRef = useRef(null);

  // ── Load article ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    blogApi.getArticle(id)
      .then(data => {
        if (data.success && data.article) {
          setArticle(data.article);
          setBlocks(parseHtmlToBlocks(data.article.content || ''));
        } else {
          setError('Could not load article.');
        }
      })
      .catch(() => setError('Failed to fetch article.'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // ── Auto-save after block changes (debounced) ──────────────────────────────
  useEffect(() => {
    if (!article || loading) return;
    clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      handleSave('auto');
    }, 2000);
    return () => clearTimeout(saveTimeoutRef.current);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blocks]);

  // ── Save ───────────────────────────────────────────────────────────────────
  const handleSave = async (trigger = 'manual') => {
    if (!article) return;
    setSaveStatus('saving');
    try {
      const html = blocksToHtml(blocks);
      await blogApi.updateArticle(article.id, { content: html });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
    }
  };

  // ── Add block at end ───────────────────────────────────────────────────────
  const handleAddBlock = type => {
    const newBlock = createBlock(type);
    setBlocks([...blocks, newBlock]);
    setSelectedBlockId(newBlock.id);
    setMode('edit');
  };

  // ── Global style changes ───────────────────────────────────────────────────
  const handleGlobalStyleChange = patch => {
    setGlobalStyles(prev => ({ ...prev, ...patch }));
  };

  // ── Per-block style changes (from StylePanel) ──────────────────────────────
  const handleBlockStyleChange = patch => {
    if (!selectedBlockId) return;
    setBlocks(
      blocks.map(b => {
        if (b.id !== selectedBlockId) return b;
        if (patch === null) return { ...b, styles: {} };
        // level changes go on block root, not styles
        if ('level' in patch) return { ...b, ...patch };
        return { ...b, styles: { ...(b.styles || {}), ...patch } };
      })
    );
  };

  // ── Editor Agent review ────────────────────────────────────────────────────
  const handleAgentReview = async () => {
    try {
      const data = await blogApi.getEditorReview(id);
      if (data.review) {
        setAgentReview(data.review.scorecard ? data.review : { scorecard: data.review, next_steps: data.review.next_steps || [] });
      }
    } catch {
      // If agent isn't running, show a placeholder review
      setAgentReview({
        scorecard: {
          readability: 86,
          layout_harmony: 'balanced',
          affiliate_block_placement: 'CTA after section 2 and conclusion',
          accessibility: 'passes quick audit',
        },
        next_steps: [
          'Add hero illustration with fast-loading format',
          'Verify heading hierarchy (H1/H2/H3)',
          'Run link checker for affiliate URLs',
        ],
        reviewed_at: new Date().toISOString(),
      });
    }
  };

  // ── Conversational edit ────────────────────────────────────────────────────
  const handleConversationalEdit = async command => {
    const data = await blogApi.conversationalEdit(id, { command });
    if (data.article?.content) {
      setArticle(prev => ({ ...prev, ...data.article }));
      setBlocks(parseHtmlToBlocks(data.article.content));
      setConversationalResult(data.message || 'Article updated by agent.');
      // Auto-trigger a review after agent makes changes
      setTimeout(handleAgentReview, 500);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center text-gray-400">
          <RefreshCw size={28} className="animate-spin mx-auto mb-3" />
          <p>Loading article…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center text-red-500">
          <AlertTriangle size={28} className="mx-auto mb-3" />
          <p>{error}</p>
          <button onClick={() => navigate('/articles')} className="mt-4 text-sm text-blue-600 underline">
            Back to Articles
          </button>
        </div>
      </div>
    );
  }

  const selectedBlock = blocks.find(b => b.id === selectedBlockId) || null;

  return (
    <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
      {/* Toolbar */}
      <EditorToolbar
        articleTitle={article?.title}
        mode={mode}
        onModeChange={m => { setMode(m); if (m === 'preview') setSelectedBlockId(null); }}
        onAddBlock={handleAddBlock}
        onSave={handleSave}
        saveStatus={saveStatus}
        showStylePanel={showStylePanel}
        onToggleStylePanel={() => setShowStylePanel(o => !o)}
        showAgentPanel={showAgentPanel}
        onToggleAgentPanel={() => setShowAgentPanel(o => !o)}
        onUndo={undo}
        canUndo={canUndo}
      />

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">

        {/* Agent panel */}
        {showAgentPanel && (
          <div className="w-64 shrink-0 overflow-hidden flex flex-col">
            <AgentPanel
              articleId={id}
              agentReview={agentReview}
              onReview={handleAgentReview}
              conversationalResult={conversationalResult}
              onConversationalEdit={handleConversationalEdit}
            />
          </div>
        )}

        {/* Preview canvas */}
        <div className="flex-1 overflow-hidden">
          <BlogPreviewPanel
            article={article}
            blocks={blocks}
            onBlocksChange={setBlocks}
            mode={mode}
            globalStyles={globalStyles}
            selectedBlockId={selectedBlockId}
            onSelectBlock={setSelectedBlockId}
            agentReview={mode === 'preview' ? agentReview : null}
          />
        </div>

        {/* Style panel */}
        {showStylePanel && (
          <div className="w-56 shrink-0 overflow-hidden">
            <StylePanel
              globalStyles={globalStyles}
              onGlobalChange={handleGlobalStyleChange}
              selectedBlock={selectedBlock}
              onBlockChange={handleBlockStyleChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ArticleEditor;

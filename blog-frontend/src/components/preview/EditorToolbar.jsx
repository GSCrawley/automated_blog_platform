import React, { useState } from 'react';
import {
  ArrowLeft,
  Eye,
  Pencil,
  Save,
  Plus,
  ChevronDown,
  PanelRight,
  PanelLeft,
  RotateCcw,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const BLOCK_TYPES = [
  { type: 'heading',   label: 'Heading',    shortcut: 'H' },
  { type: 'paragraph', label: 'Paragraph',  shortcut: 'P' },
  { type: 'image',     label: 'Image',      shortcut: 'I' },
  { type: 'list',      label: 'List',       shortcut: 'L' },
  { type: 'quote',     label: 'Blockquote', shortcut: 'Q' },
  { type: 'divider',   label: 'Divider',    shortcut: '—' },
  { type: 'ad',        label: 'Ad Block',   shortcut: 'A' },
  { type: 'cta',       label: 'CTA Button', shortcut: 'C' },
];

/**
 * Top toolbar for the ArticleEditor.
 *
 * Props:
 *   articleTitle      : string
 *   mode              : 'preview' | 'edit'
 *   onModeChange      : (mode) => void
 *   onAddBlock        : (type) => void
 *   onSave            : () => void
 *   saveStatus        : 'idle' | 'saving' | 'saved' | 'error'
 *   showStylePanel    : bool
 *   onToggleStylePanel: () => void
 *   showAgentPanel    : bool
 *   onToggleAgentPanel: () => void
 *   onUndo            : () => void
 *   canUndo           : bool
 */
const EditorToolbar = ({
  articleTitle = 'Untitled Article',
  mode,
  onModeChange,
  onAddBlock,
  onSave,
  saveStatus = 'idle',
  showStylePanel,
  onToggleStylePanel,
  showAgentPanel,
  onToggleAgentPanel,
  onUndo,
  canUndo,
}) => {
  const [addMenuOpen, setAddMenuOpen] = useState(false);

  const SaveIcon = () => {
    if (saveStatus === 'saving') return <Loader2 size={14} className="animate-spin" />;
    if (saveStatus === 'saved')  return <CheckCircle2 size={14} className="text-green-500" />;
    return <Save size={14} />;
  };

  const saveLabel = {
    idle:   'Save',
    saving: 'Saving…',
    saved:  'Saved',
    error:  'Retry',
  }[saveStatus] || 'Save';

  return (
    <div className="flex items-center h-11 bg-white border-b border-gray-200 px-3 gap-2 select-none z-20 sticky top-0 shadow-sm">
      {/* Back */}
      <Link
        to="/articles"
        className="flex items-center gap-1 text-gray-500 hover:text-gray-800 transition-colors px-2 py-1 rounded hover:bg-gray-100 text-sm"
      >
        <ArrowLeft size={14} />
        <span className="hidden sm:inline">Articles</span>
      </Link>

      <div className="h-4 w-px bg-gray-200" />

      {/* Title */}
      <span className="text-sm font-medium text-gray-700 truncate max-w-xs" title={articleTitle}>
        {articleTitle}
      </span>

      <div className="flex-1" />

      {/* Undo */}
      {mode === 'edit' && (
        <button
          onClick={onUndo}
          disabled={!canUndo}
          title="Undo"
          className={`p-1.5 rounded transition-colors ${
            canUndo ? 'text-gray-500 hover:bg-gray-100 hover:text-gray-800' : 'text-gray-300 cursor-not-allowed'
          }`}
        >
          <RotateCcw size={14} />
        </button>
      )}

      {/* Mode toggle */}
      <div className="flex items-center rounded-md border border-gray-200 overflow-hidden">
        <button
          onClick={() => onModeChange('preview')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === 'preview'
              ? 'bg-gray-900 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Eye size={13} />
          Preview
        </button>
        <button
          onClick={() => onModeChange('edit')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === 'edit'
              ? 'bg-gray-900 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Pencil size={13} />
          Edit
        </button>
      </div>

      {/* Add block (only in edit mode) */}
      {mode === 'edit' && (
        <div className="relative">
          <button
            onClick={() => setAddMenuOpen(o => !o)}
            className="flex items-center gap-1 text-xs border border-gray-200 rounded px-2.5 py-1.5 hover:bg-gray-50 text-gray-700 font-medium"
          >
            <Plus size={13} />
            Add Block
            <ChevronDown size={12} className="text-gray-400" />
          </button>
          {addMenuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setAddMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-44 bg-white border border-gray-200 rounded-md shadow-lg z-50 py-1">
                {BLOCK_TYPES.map(b => (
                  <button
                    key={b.type}
                    onClick={() => { onAddBlock(b.type); setAddMenuOpen(false); }}
                    className="flex items-center justify-between w-full px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
                  >
                    <span>{b.label}</span>
                    <kbd className="text-xs bg-gray-100 border border-gray-200 rounded px-1 text-gray-400">{b.shortcut}</kbd>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <div className="h-4 w-px bg-gray-200" />

      {/* Panel toggles */}
      <button
        onClick={onToggleAgentPanel}
        title="Toggle Editor Agent panel"
        className={`p-1.5 rounded transition-colors ${
          showAgentPanel ? 'bg-purple-100 text-purple-700' : 'text-gray-500 hover:bg-gray-100'
        }`}
      >
        <PanelLeft size={15} />
      </button>

      <button
        onClick={onToggleStylePanel}
        title="Toggle Style panel"
        className={`p-1.5 rounded transition-colors ${
          showStylePanel ? 'bg-blue-100 text-blue-700' : 'text-gray-500 hover:bg-gray-100'
        }`}
      >
        <PanelRight size={15} />
      </button>

      <div className="h-4 w-px bg-gray-200" />

      {/* Save */}
      <button
        onClick={onSave}
        disabled={saveStatus === 'saving'}
        className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded border transition-colors ${
          saveStatus === 'saved'
            ? 'border-green-300 bg-green-50 text-green-700'
            : saveStatus === 'error'
            ? 'border-red-300 bg-red-50 text-red-700'
            : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
        }`}
      >
        <SaveIcon />
        {saveLabel}
      </button>
    </div>
  );
};

export default EditorToolbar;

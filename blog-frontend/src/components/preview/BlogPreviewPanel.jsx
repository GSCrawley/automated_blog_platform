import React, { useRef, useState } from 'react';
import { Reorder, useDragControls } from 'framer-motion';
import { Plus } from 'lucide-react';
import PreviewBlock from './PreviewBlock';
import { createBlock } from '../../utils/contentBlocks';

/**
 * Wrapper that gives each Reorder.Item its own useDragControls instance.
 */
const SortableBlock = ({ block, isSelected, onSelect, onChange, onDelete, onAddAfter }) => {
  const dragControls = useDragControls();
  return (
    <Reorder.Item value={block} dragListener={false} dragControls={dragControls} className="relative">
      <PreviewBlock
        block={block}
        isEditing
        isSelected={isSelected}
        onSelect={onSelect}
        onChange={onChange}
        onDelete={onDelete}
        onAddAfter={onAddAfter}
        dragHandleProps={{
          onPointerDown: e => { e.preventDefault(); dragControls.start(e); },
        }}
      />
    </Reorder.Item>
  );
};

/**
 * BlogPreviewPanel — renders article content as a browser-like blog post.
 *
 * In 'edit' mode blocks are sortable (drag-to-reorder) and inline-editable.
 * In 'preview' mode it shows the clean rendered output.
 *
 * Props:
 *   article       : { title, meta_description, status, created_at, ... }
 *   blocks        : Block[]
 *   onBlocksChange: (newBlocks) => void
 *   mode          : 'preview' | 'edit'
 *   globalStyles  : { fontFamily, bodyFontSize, bodyColor, headingColor, bgColor, contentWidth, ... }
 *   selectedBlockId     : string | null
 *   onSelectBlock       : (id | null) => void
 *   agentReview   : { scorecard, next_steps } | null
 */
const BlogPreviewPanel = ({
  article = {},
  blocks = [],
  onBlocksChange,
  mode = 'preview',
  globalStyles = {},
  selectedBlockId,
  onSelectBlock,
  agentReview,
}) => {
  const containerRef = useRef(null);

  const isEditing = mode === 'edit';

  const updateBlock = (id, patch) => {
    if (patch === null) {
      // Reset styles
      onBlocksChange(blocks.map(b => b.id === id ? { ...b, styles: {} } : b));
    } else if ('level' in patch && typeof patch.level === 'number') {
      // heading level change comes from StylePanel — merge into block root, not styles
      onBlocksChange(blocks.map(b => b.id === id ? { ...b, ...patch } : b));
    } else {
      onBlocksChange(blocks.map(b => b.id === id ? { ...b, ...patch } : b));
    }
  };

  const deleteBlock = id => {
    onBlocksChange(blocks.filter(b => b.id !== id));
    if (selectedBlockId === id) onSelectBlock(null);
  };

  const addBlockAfter = (afterId, type = 'paragraph') => {
    const idx = blocks.findIndex(b => b.id === afterId);
    const newBlock = createBlock(type);
    const next = [...blocks];
    next.splice(idx + 1, 0, newBlock);
    onBlocksChange(next);
    // Select the new block
    setTimeout(() => onSelectBlock(newBlock.id), 50);
  };

  // ── Computed CSS vars ────────────────────────────────────────────────────
  const contentStyle = {
    fontFamily: globalStyles.fontFamily || undefined,
    fontSize: globalStyles.bodyFontSize || '16px',
    color: globalStyles.bodyColor || '#374151',
    backgroundColor: globalStyles.bgColor || '#ffffff',
    lineHeight: globalStyles.lineHeight || '1.7',
  };

  const articleMaxWidth = globalStyles.contentWidth || '740px';
  const headingColor = globalStyles.headingColor || '#111827';
  const accentColor = globalStyles.accentColor || '#2563eb';

  // ── Injected blog CSS (scoped to the preview) ────────────────────────────
  const blogCss = `
    .blog-preview-canvas h1,
    .blog-preview-canvas h2,
    .blog-preview-canvas h3,
    .blog-preview-canvas h4 {
      color: ${headingColor};
    }
    .blog-preview-canvas a {
      color: ${accentColor};
    }
    .blog-preview-canvas p + p {
      margin-top: ${globalStyles.paragraphSpacing || '16px'};
    }
  `;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto"
      style={contentStyle}
      onClick={() => isEditing && onSelectBlock(null)}
    >
      <style>{blogCss}</style>

      {/* ── Browser chrome ──────────────────────────────────────────────── */}
      <div className="sticky top-0 z-10 bg-gray-100 border-b border-gray-300 px-4 py-2 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <div className="w-3 h-3 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 bg-white border border-gray-300 rounded-full px-4 py-1 text-xs text-gray-500 truncate">
          https://yourblog.com/articles/{article.title ? article.title.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]/g, '') : 'draft'}
        </div>
      </div>

      {/* ── Simulated blog site header ───────────────────────────────────── */}
      <div
        className="border-b border-gray-200 px-8 py-3 flex items-center justify-between"
        style={{ backgroundColor: globalStyles.bgColor || '#ffffff' }}
      >
        <span className="font-bold text-lg" style={{ color: headingColor }}>
          YourBlog
        </span>
        <nav className="flex gap-4 text-sm" style={{ color: accentColor }}>
          <a href="#" className="hover:underline">Home</a>
          <a href="#" className="hover:underline">Reviews</a>
          <a href="#" className="hover:underline">Deals</a>
        </nav>
      </div>

      {/* ── Article container ────────────────────────────────────────────── */}
      <div
        className="mx-auto px-6 py-10 blog-preview-canvas"
        style={{ maxWidth: articleMaxWidth }}
      >
        {/* Article header */}
        <header className="mb-8">
          <h1
            className="text-4xl font-bold leading-tight mb-3"
            style={{ color: headingColor }}
          >
            {article.title || 'Untitled Article'}
          </h1>
          <div className="flex items-center gap-3 text-sm text-gray-500 mb-4">
            {article.created_at && (
              <span>{new Date(article.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
            )}
            {article.status && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                article.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {article.status}
              </span>
            )}
          </div>
          {article.meta_description && (
            <p className="text-lg text-gray-600 border-l-4 border-blue-200 pl-4 italic">
              {article.meta_description}
            </p>
          )}
        </header>

        {/* ── Blocks ────────────────────────────────────────────────────── */}
        {isEditing ? (
          <Reorder.Group
            axis="y"
            values={blocks}
            onReorder={onBlocksChange}
            className="space-y-4 pl-8"
          >
            {blocks.map(block => (
              <SortableBlock
                key={block.id}
                block={block}
                isSelected={selectedBlockId === block.id}
                onSelect={() => onSelectBlock(block.id)}
                onChange={patch => updateBlock(block.id, patch)}
                onDelete={() => deleteBlock(block.id)}
                onAddAfter={type => addBlockAfter(block.id, type)}
              />
            ))}
          </Reorder.Group>
        ) : (
          <div className="space-y-4">
            {blocks.map(block => (
              <PreviewBlock
                key={block.id}
                block={block}
                isEditing={false}
                isSelected={false}
              />
            ))}
          </div>
        )}

        {/* Add first block prompt */}
        {isEditing && blocks.length === 0 && (
          <div
            className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center cursor-pointer hover:border-blue-300 hover:bg-blue-50 transition-colors"
            onClick={() => {
              const b = createBlock('paragraph');
              onBlocksChange([b]);
              onSelectBlock(b.id);
            }}
          >
            <Plus size={24} className="mx-auto mb-2 text-gray-400" />
            <p className="text-gray-400 text-sm">Click to add your first block</p>
          </div>
        )}

        {/* ── Agent review overlay ───────────────────────────────────────── */}
        {agentReview && (
          <div className="mt-10 p-4 bg-purple-50 border border-purple-200 rounded-lg text-sm">
            <p className="font-semibold text-purple-800 mb-2 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-purple-500" />
              Editor Agent Review
            </p>
            <div className="grid grid-cols-2 gap-3 mb-3">
              {Object.entries(agentReview.scorecard || {}).map(([key, val]) => (
                typeof val !== 'object' && (
                  <div key={key} className="flex justify-between">
                    <span className="text-purple-600 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-purple-900">{val}</span>
                  </div>
                )
              ))}
            </div>
            {agentReview.next_steps?.length > 0 && (
              <>
                <p className="text-purple-700 font-medium mb-1">Next Steps:</p>
                <ul className="list-disc list-inside space-y-0.5 text-purple-600">
                  {agentReview.next_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}

        {/* ── Simulated blog footer ──────────────────────────────────────── */}
        <footer className="mt-16 pt-8 border-t border-gray-200 text-center text-sm text-gray-400">
          <p>© {new Date().getFullYear()} YourBlog · All rights reserved</p>
        </footer>
      </div>
    </div>
  );
};

export default BlogPreviewPanel;

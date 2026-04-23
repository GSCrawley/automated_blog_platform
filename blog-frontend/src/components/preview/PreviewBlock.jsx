import React, { useRef, useEffect, useState } from 'react';
import { GripVertical, Trash2, Plus, Image, ChevronUp, ChevronDown } from 'lucide-react';

/**
 * Renders a single content block.
 * In edit mode: shows drag handle, selection border, inline editing.
 */
const PreviewBlock = ({
  block,
  isEditing,
  isSelected,
  onSelect,
  onChange,
  onDelete,
  onAddAfter,
  dragHandleProps,
}) => {
  const editRef = useRef(null);
  const [imageError, setImageError] = useState(false);

  // Sync contenteditable when block changes externally
  useEffect(() => {
    if (!editRef.current) return;
    if (block.type === 'heading' && editRef.current.textContent !== block.text) {
      editRef.current.textContent = block.text;
    }
    if (block.type === 'paragraph' && editRef.current.innerHTML !== block.html) {
      editRef.current.innerHTML = block.html;
    }
  }, [block]);

  const blockStyle = block.styles || {};

  // ── wrapper classes ────────────────────────────────────────────────────────
  const wrapClass = [
    'group relative',
    isEditing ? 'cursor-pointer' : '',
    isEditing && isSelected
      ? 'ring-2 ring-blue-500 ring-offset-1 rounded'
      : isEditing
      ? 'hover:ring-1 hover:ring-blue-200 hover:ring-offset-1 rounded'
      : '',
  ]
    .filter(Boolean)
    .join(' ');

  // ── inline edit overlay (shown when block is selected in edit mode) ────────
  const EditOverlay = () =>
    isEditing && isSelected ? (
      <div className="absolute -top-7 right-0 flex items-center gap-1 bg-white border border-blue-300 rounded shadow-sm px-1 py-0.5 z-10">
        <button
          title="Add block after"
          onClick={e => { e.stopPropagation(); onAddAfter(); }}
          className="p-0.5 hover:bg-blue-50 rounded text-blue-600"
        >
          <Plus size={13} />
        </button>
        <button
          title="Delete block"
          onClick={e => { e.stopPropagation(); onDelete(); }}
          className="p-0.5 hover:bg-red-50 rounded text-red-500"
        >
          <Trash2 size={13} />
        </button>
      </div>
    ) : null;

  // ── drag handle ────────────────────────────────────────────────────────────
  const DragHandle = () =>
    isEditing ? (
      <div
        {...dragHandleProps}
        className="absolute -left-6 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-60 cursor-grab active:cursor-grabbing text-gray-400 transition-opacity"
        title="Drag to reorder"
      >
        <GripVertical size={16} />
      </div>
    ) : null;

  // ── content editable helpers ───────────────────────────────────────────────
  const handleHeadingInput = () => {
    if (editRef.current) {
      onChange({ text: editRef.current.textContent });
    }
  };

  const handleParaInput = () => {
    if (editRef.current) {
      onChange({ html: editRef.current.innerHTML });
    }
  };

  const handleKeyDown = e => {
    // Prevent Enter from creating a new block inside contenteditable heading
    if (block.type === 'heading' && e.key === 'Enter') {
      e.preventDefault();
      onAddAfter();
    }
  };

  // ── renderers by type ──────────────────────────────────────────────────────

  const renderHeading = () => {
    const Tag = `h${block.level}`;
    const sizeMap = { 1: 'text-4xl font-bold', 2: 'text-2xl font-bold', 3: 'text-xl font-semibold', 4: 'text-lg font-semibold' };
    const cls = sizeMap[block.level] || 'text-xl font-semibold';
    return (
      <Tag
        ref={editRef}
        contentEditable={isEditing}
        suppressContentEditableWarning
        onInput={handleHeadingInput}
        onKeyDown={handleKeyDown}
        className={`${cls} text-gray-900 leading-tight outline-none`}
        style={blockStyle}
        onFocus={() => onSelect && onSelect()}
      >
        {block.text}
      </Tag>
    );
  };

  const renderParagraph = () => (
    <p
      ref={editRef}
      contentEditable={isEditing}
      suppressContentEditableWarning
      onInput={handleParaInput}
      className="text-gray-700 leading-relaxed outline-none"
      style={blockStyle}
      onFocus={() => onSelect && onSelect()}
      dangerouslySetInnerHTML={isEditing ? undefined : { __html: block.html }}
    />
  );

  const renderImage = () => (
    <figure className="my-2" style={blockStyle}>
      {block.src && !imageError ? (
        <img
          src={block.src}
          alt={block.alt || ''}
          onError={() => setImageError(true)}
          className="w-full rounded-md object-cover max-h-96"
        />
      ) : (
        <div className="w-full h-48 bg-gray-100 border-2 border-dashed border-gray-300 rounded-md flex flex-col items-center justify-center text-gray-400">
          <Image size={32} className="mb-2" />
          <span className="text-sm">{block.src ? 'Image failed to load' : 'No image URL'}</span>
          {isEditing && (
            <input
              type="text"
              placeholder="Paste image URL..."
              defaultValue={block.src}
              onClick={e => e.stopPropagation()}
              onChange={e => onChange({ src: e.target.value, imageError: false })}
              onFocus={() => { setImageError(false); onSelect && onSelect(); }}
              className="mt-2 text-sm border rounded px-2 py-1 w-64 text-gray-700 outline-none focus:ring-1 focus:ring-blue-400"
            />
          )}
        </div>
      )}
      {(block.caption || isEditing) && (
        <figcaption
          contentEditable={isEditing}
          suppressContentEditableWarning
          onInput={e => onChange({ caption: e.currentTarget.textContent })}
          className="text-sm text-gray-500 text-center mt-1 outline-none"
        >
          {block.caption || (isEditing ? 'Add caption…' : '')}
        </figcaption>
      )}
    </figure>
  );

  const renderList = () => {
    const Tag = block.ordered ? 'ol' : 'ul';
    const listCls = block.ordered ? 'list-decimal' : 'list-disc';
    return (
      <Tag className={`${listCls} pl-6 text-gray-700 space-y-1`} style={blockStyle}>
        {(block.items || []).map((item, idx) => (
          <li
            key={idx}
            contentEditable={isEditing}
            suppressContentEditableWarning
            onInput={e => {
              const newItems = [...block.items];
              newItems[idx] = e.currentTarget.innerHTML;
              onChange({ items: newItems });
            }}
            onFocus={() => onSelect && onSelect()}
            className="outline-none"
            dangerouslySetInnerHTML={isEditing ? undefined : { __html: item }}
          />
        ))}
        {isEditing && (
          <li>
            <button
              onClick={e => { e.stopPropagation(); onChange({ items: [...(block.items || []), 'New item'] }); }}
              className="text-blue-500 text-sm hover:underline"
            >
              + Add item
            </button>
          </li>
        )}
      </Tag>
    );
  };

  const renderQuote = () => (
    <blockquote className="border-l-4 border-blue-400 pl-4 italic text-gray-600 my-4" style={blockStyle}>
      <p
        contentEditable={isEditing}
        suppressContentEditableWarning
        onInput={e => onChange({ text: e.currentTarget.innerHTML })}
        onFocus={() => onSelect && onSelect()}
        className="outline-none"
        dangerouslySetInnerHTML={isEditing ? undefined : { __html: block.text }}
      />
      {(block.cite || isEditing) && (
        <cite
          contentEditable={isEditing}
          suppressContentEditableWarning
          onInput={e => onChange({ cite: e.currentTarget.textContent })}
          className="not-italic text-sm text-gray-500 mt-1 block outline-none"
        >
          {block.cite || (isEditing ? '— Source' : '')}
        </cite>
      )}
    </blockquote>
  );

  const renderDivider = () => (
    <hr className="my-6 border-gray-200" style={blockStyle} />
  );

  const renderAd = () => (
    <div
      className="my-4 p-3 border-2 border-dashed border-amber-300 bg-amber-50 rounded-md text-center"
      style={blockStyle}
    >
      <span className="text-xs text-amber-600 font-medium uppercase tracking-wide block mb-1">
        Ad Placement · {block.adType || 'banner'}
      </span>
      {isEditing ? (
        <div className="flex gap-2 items-center justify-center mt-2">
          <select
            value={block.adType || 'banner'}
            onChange={e => onChange({ adType: e.target.value })}
            onClick={e => e.stopPropagation()}
            className="text-sm border rounded px-2 py-1 outline-none"
          >
            <option value="banner">Banner</option>
            <option value="sidebar">Sidebar</option>
            <option value="inline">Inline</option>
            <option value="sticky">Sticky</option>
          </select>
          <input
            type="text"
            defaultValue={block.label}
            onChange={e => onChange({ label: e.target.value })}
            onClick={e => e.stopPropagation()}
            placeholder="Ad label..."
            className="text-sm border rounded px-2 py-1 outline-none w-40"
          />
        </div>
      ) : (
        <span className="text-amber-700 text-sm">{block.label || 'Advertisement'}</span>
      )}
    </div>
  );

  const renderCta = () => (
    <div className="my-4 text-center" style={blockStyle}>
      <a
        href={isEditing ? undefined : (block.href || '#')}
        onClick={isEditing ? e => e.preventDefault() : undefined}
        className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg no-underline transition-colors"
      >
        {isEditing ? (
          <span
            contentEditable
            suppressContentEditableWarning
            onInput={e => onChange({ text: e.currentTarget.textContent })}
            onFocus={() => onSelect && onSelect()}
            className="outline-none"
          >
            {block.text}
          </span>
        ) : (
          block.text
        )}
      </a>
      {isEditing && (
        <input
          type="text"
          defaultValue={block.href}
          onChange={e => onChange({ href: e.target.value })}
          onClick={e => e.stopPropagation()}
          placeholder="https://..."
          className="mt-2 block mx-auto text-sm border rounded px-2 py-1 outline-none w-64 focus:ring-1 focus:ring-blue-400"
        />
      )}
    </div>
  );

  const renderContent = () => {
    switch (block.type) {
      case 'heading':   return renderHeading();
      case 'paragraph': return renderParagraph();
      case 'image':     return renderImage();
      case 'list':      return renderList();
      case 'quote':     return renderQuote();
      case 'divider':   return renderDivider();
      case 'ad':        return renderAd();
      case 'cta':       return renderCta();
      default:
        return <div dangerouslySetInnerHTML={{ __html: block.html || '' }} />;
    }
  };

  return (
    <div
      className={wrapClass}
      onClick={() => isEditing && onSelect && onSelect()}
    >
      <DragHandle />
      <EditOverlay />
      {renderContent()}
    </div>
  );
};

export default PreviewBlock;

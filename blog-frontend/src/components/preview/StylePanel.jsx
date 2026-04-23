import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Type, Palette, LayoutTemplate } from 'lucide-react';

const FONTS = [
  { label: 'System Default', value: '' },
  { label: 'Georgia (Serif)', value: 'Georgia, serif' },
  { label: 'Merriweather', value: "'Merriweather', Georgia, serif" },
  { label: 'Inter (Sans)', value: "'Inter', system-ui, sans-serif" },
  { label: 'Roboto', value: "'Roboto', Arial, sans-serif" },
  { label: 'Lato', value: "'Lato', Helvetica, sans-serif" },
  { label: 'Playfair Display', value: "'Playfair Display', Georgia, serif" },
  { label: 'Source Sans Pro', value: "'Source Sans Pro', sans-serif" },
  { label: 'Monospace', value: "Menlo, Consolas, monospace" },
];

const COLORS = [
  '#1a1a1a', '#374151', '#6b7280',
  '#1e40af', '#7c3aed', '#059669',
  '#dc2626', '#d97706', '#0891b2',
];

/**
 * Collapsible section within the style panel.
 */
const Section = ({ title, icon: Icon, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-gray-100 last:border-0">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <span className="flex items-center gap-2">
          {Icon && <Icon size={14} className="text-gray-400" />}
          {title}
        </span>
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
      </button>
      {open && <div className="px-3 pb-3 space-y-2.5">{children}</div>}
    </div>
  );
};

const Label = ({ children }) => (
  <label className="block text-xs text-gray-500 mb-1">{children}</label>
);

const NumberInput = ({ label, value, onChange, min = 0, max = 200, unit = 'px' }) => (
  <div>
    <Label>{label}</Label>
    <div className="flex items-center gap-2">
      <input
        type="range"
        min={min}
        max={max}
        value={parseInt(value) || 0}
        onChange={e => onChange(`${e.target.value}${unit}`)}
        className="flex-1 h-1.5 accent-blue-500"
      />
      <span className="text-xs text-gray-500 w-10 text-right">{value || `0${unit}`}</span>
    </div>
  </div>
);

/**
 * Style Panel — global blog styles + per-block overrides.
 *
 * Props:
 *   globalStyles    : { fontFamily, bodyFontSize, headingColor, bodyColor, bgColor }
 *   onGlobalChange  : (patch) => void
 *   selectedBlock   : block | null
 *   onBlockChange   : (stylePatch) => void
 */
const StylePanel = ({ globalStyles = {}, onGlobalChange, selectedBlock, onBlockChange }) => {
  return (
    <div className="h-full overflow-y-auto bg-white border-l border-gray-200 text-sm select-none">
      <div className="px-3 py-2.5 border-b border-gray-200 sticky top-0 bg-white z-10">
        <h3 className="font-semibold text-gray-800 text-sm">Styles</h3>
      </div>

      {/* ── Global Typography ──────────────────────────────────────────────── */}
      <Section title="Typography" icon={Type}>
        <div>
          <Label>Font Family</Label>
          <select
            value={globalStyles.fontFamily || ''}
            onChange={e => onGlobalChange({ fontFamily: e.target.value })}
            className="w-full text-xs border border-gray-200 rounded px-2 py-1.5 outline-none focus:ring-1 focus:ring-blue-400"
          >
            {FONTS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        <div>
          <Label>Body Font Size</Label>
          <div className="flex gap-1.5">
            {['14px', '16px', '18px', '20px'].map(s => (
              <button
                key={s}
                onClick={() => onGlobalChange({ bodyFontSize: s })}
                className={`flex-1 text-xs border rounded py-1 transition-colors ${
                  globalStyles.bodyFontSize === s
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-400'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div>
          <Label>Line Height</Label>
          <div className="flex gap-1.5">
            {['1.4', '1.6', '1.8', '2.0'].map(s => (
              <button
                key={s}
                onClick={() => onGlobalChange({ lineHeight: s })}
                className={`flex-1 text-xs border rounded py-1 transition-colors ${
                  globalStyles.lineHeight === s
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-400'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </Section>

      {/* ── Colors ──────────────────────────────────────────────────────────── */}
      <Section title="Colors" icon={Palette}>
        {[
          { key: 'headingColor', label: 'Heading Color' },
          { key: 'bodyColor', label: 'Body Text Color' },
          { key: 'bgColor', label: 'Background Color' },
          { key: 'accentColor', label: 'Accent / Link Color' },
        ].map(({ key, label }) => (
          <div key={key}>
            <Label>{label}</Label>
            <div className="flex items-center gap-2">
              <div className="flex flex-wrap gap-1.5">
                {COLORS.map(c => (
                  <button
                    key={c}
                    title={c}
                    onClick={() => onGlobalChange({ [key]: c })}
                    style={{ backgroundColor: c }}
                    className={`w-5 h-5 rounded-full border-2 transition-transform hover:scale-110 ${
                      globalStyles[key] === c ? 'border-blue-500 scale-110' : 'border-transparent'
                    }`}
                  />
                ))}
              </div>
              <input
                type="color"
                value={globalStyles[key] || '#1a1a1a'}
                onChange={e => onGlobalChange({ [key]: e.target.value })}
                className="w-6 h-6 rounded cursor-pointer border-0 bg-transparent"
                title="Custom color"
              />
            </div>
          </div>
        ))}
      </Section>

      {/* ── Layout / Spacing ────────────────────────────────────────────────── */}
      <Section title="Layout & Spacing" icon={LayoutTemplate}>
        <div>
          <Label>Content Width</Label>
          <div className="flex gap-1.5">
            {[
              { label: 'Narrow', value: '640px' },
              { label: 'Default', value: '740px' },
              { label: 'Wide', value: '900px' },
              { label: 'Full', value: '100%' },
            ].map(o => (
              <button
                key={o.value}
                onClick={() => onGlobalChange({ contentWidth: o.value })}
                className={`flex-1 text-xs border rounded py-1 transition-colors ${
                  globalStyles.contentWidth === o.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-400'
                }`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>

        <NumberInput
          label="Paragraph Spacing"
          value={globalStyles.paragraphSpacing}
          onChange={v => onGlobalChange({ paragraphSpacing: v })}
          min={0}
          max={48}
        />

        <NumberInput
          label="Section Padding (top/bottom)"
          value={globalStyles.sectionPadding}
          onChange={v => onGlobalChange({ sectionPadding: v })}
          min={0}
          max={80}
        />
      </Section>

      {/* ── Selected Block Overrides ─────────────────────────────────────────── */}
      {selectedBlock && (
        <Section title={`Block: ${selectedBlock.type}`} defaultOpen>
          <p className="text-xs text-gray-400 mb-2">Override styles for this block only.</p>

          <div>
            <Label>Text Align</Label>
            <div className="flex gap-1.5">
              {['left', 'center', 'right', 'justify'].map(a => (
                <button
                  key={a}
                  onClick={() => onBlockChange({ textAlign: a })}
                  className={`flex-1 text-xs border rounded py-1 capitalize ${
                    (selectedBlock.styles?.textAlign || 'left') === a
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-400'
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          {['heading', 'paragraph', 'list', 'quote'].includes(selectedBlock.type) && (
            <div>
              <Label>Font Size</Label>
              <div className="flex gap-1.5 flex-wrap">
                {['12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'].map(s => (
                  <button
                    key={s}
                    onClick={() => onBlockChange({ fontSize: s })}
                    className={`text-xs border rounded px-1.5 py-1 transition-colors ${
                      selectedBlock.styles?.fontSize === s
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedBlock.type === 'heading' && (
            <div>
              <Label>Heading Level</Label>
              <div className="flex gap-1.5">
                {[1, 2, 3, 4].map(l => (
                  <button
                    key={l}
                    onClick={() => onBlockChange({ level: l })}
                    className={`flex-1 text-xs border rounded py-1 ${
                      selectedBlock.level === l
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    H{l}
                  </button>
                ))}
              </div>
            </div>
          )}

          <NumberInput
            label="Margin Top"
            value={selectedBlock.styles?.marginTop}
            onChange={v => onBlockChange({ marginTop: v })}
            max={80}
          />
          <NumberInput
            label="Margin Bottom"
            value={selectedBlock.styles?.marginBottom}
            onChange={v => onBlockChange({ marginBottom: v })}
            max={80}
          />
          <NumberInput
            label="Padding"
            value={selectedBlock.styles?.padding}
            onChange={v => onBlockChange({ padding: v })}
            max={48}
          />

          <div>
            <Label>Text Color</Label>
            <div className="flex items-center gap-2">
              <div className="flex flex-wrap gap-1.5">
                {COLORS.map(c => (
                  <button
                    key={c}
                    onClick={() => onBlockChange({ color: c })}
                    style={{ backgroundColor: c }}
                    className={`w-5 h-5 rounded-full border-2 hover:scale-110 ${
                      selectedBlock.styles?.color === c ? 'border-blue-500 scale-110' : 'border-transparent'
                    }`}
                  />
                ))}
              </div>
              <input
                type="color"
                value={selectedBlock.styles?.color || '#1a1a1a'}
                onChange={e => onBlockChange({ color: e.target.value })}
                className="w-6 h-6 cursor-pointer border-0 bg-transparent"
              />
            </div>
          </div>

          <div>
            <Label>Background</Label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onBlockChange({ backgroundColor: 'transparent' })}
                className="text-xs border border-gray-200 rounded px-2 py-1 hover:border-gray-400"
              >
                None
              </button>
              {['#f9fafb', '#fffbeb', '#eff6ff', '#f0fdf4', '#fdf4ff'].map(c => (
                <button
                  key={c}
                  onClick={() => onBlockChange({ backgroundColor: c })}
                  style={{ backgroundColor: c }}
                  className={`w-5 h-5 rounded-full border-2 hover:scale-110 ${
                    selectedBlock.styles?.backgroundColor === c ? 'border-blue-500' : 'border-gray-200'
                  }`}
                />
              ))}
              <input
                type="color"
                value={selectedBlock.styles?.backgroundColor || '#ffffff'}
                onChange={e => onBlockChange({ backgroundColor: e.target.value })}
                className="w-6 h-6 cursor-pointer border-0 bg-transparent"
              />
            </div>
          </div>

          <button
            onClick={() => onBlockChange(null)}
            className="w-full text-xs text-red-500 border border-red-200 rounded py-1 hover:bg-red-50 mt-1"
          >
            Reset block styles
          </button>
        </Section>
      )}

      {!selectedBlock && (
        <div className="px-3 py-4 text-xs text-gray-400 text-center">
          Click a block to see its style options.
        </div>
      )}
    </div>
  );
};

export default StylePanel;

import React, { useState } from 'react';

function KeyboardShortcuts({ isOpen, onClose }) {
  if (!isOpen) return null;

  const shortcuts = [
    { keys: ['Ctrl', 'Z'], description: 'Undo last operation' },
    { keys: ['Ctrl', 'Y'], description: 'Redo last undone operation' },
    { keys: ['Ctrl', 'Shift', 'Z'], description: 'Redo (alternative)' },
    { keys: ['Ctrl', 'S'], description: 'Save session' },
    { keys: ['Esc'], description: 'Clear selection and highlights' },
    { keys: ['Ctrl', 'Click'], description: 'Multi-select nodes' },
    { keys: ['Click'], description: 'Select node / Center on node' },
    { keys: ['Scroll'], description: 'Zoom in/out' },
    { keys: ['Drag'], description: 'Pan graph' },
  ];

  return (
    <div className="shortcuts-modal-overlay" onClick={onClose}>
      <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="shortcuts-header">
          <h2>Keyboard Shortcuts</h2>
          <button onClick={onClose} className="btn-close" style={{ padding: '5px 10px' }}>
            ×
          </button>
        </div>
        <div className="shortcuts-content">
          {shortcuts.map((shortcut, idx) => (
            <div key={idx} className="shortcut-item">
              <div className="shortcut-keys">
                {shortcut.keys.map((key, keyIdx) => (
                  <React.Fragment key={keyIdx}>
                    <kbd>{key}</kbd>
                    {keyIdx < shortcut.keys.length - 1 && <span> + </span>}
                  </React.Fragment>
                ))}
              </div>
              <div className="shortcut-description">{shortcut.description}</div>
            </div>
          ))}
        </div>
        <div className="shortcuts-footer">
          <button onClick={onClose} className="btn-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default KeyboardShortcuts;


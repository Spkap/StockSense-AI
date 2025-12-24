import { useEffect, useCallback } from 'react';

type KeyboardShortcut = {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  callback: () => void;
  description?: string;
};

/**
 * Hook for handling keyboard shortcuts
 */
export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    const target = event.target as HTMLElement;
    const isInput = target.tagName === 'INPUT' || 
                    target.tagName === 'TEXTAREA' || 
                    target.isContentEditable;
    
    for (const shortcut of shortcuts) {
      const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();
      const ctrlMatch = shortcut.ctrlKey ? event.ctrlKey : !event.ctrlKey;
      const metaMatch = shortcut.metaKey ? event.metaKey : !event.metaKey;
      const shiftMatch = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;
      const altMatch = shortcut.altKey ? event.altKey : !event.altKey;
      
      // For Cmd/Ctrl+K style shortcuts, we want them to work even in inputs
      const isNavigationShortcut = shortcut.metaKey || shortcut.ctrlKey;
      
      if (keyMatch && ctrlMatch && metaMatch && shiftMatch && altMatch) {
        if (!isInput || isNavigationShortcut) {
          event.preventDefault();
          shortcut.callback();
          break;
        }
      }
    }
  }, [shortcuts]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Common keyboard shortcuts for the app
 */
export function useAppKeyboardShortcuts({
  onFocusSearch,
  onEscape,
}: {
  onFocusSearch?: () => void;
  onEscape?: () => void;
}) {
  const shortcuts: KeyboardShortcut[] = [];
  
  if (onFocusSearch) {
    // Cmd/Ctrl + K to focus search
    shortcuts.push({
      key: 'k',
      metaKey: true,
      callback: onFocusSearch,
      description: 'Focus search input',
    });
    shortcuts.push({
      key: 'k',
      ctrlKey: true,
      callback: onFocusSearch,
      description: 'Focus search input',
    });
    
    // Also add / as a search shortcut (common in many apps)
    shortcuts.push({
      key: '/',
      callback: onFocusSearch,
      description: 'Focus search input',
    });
  }
  
  if (onEscape) {
    shortcuts.push({
      key: 'Escape',
      callback: onEscape,
      description: 'Cancel/Close',
    });
  }
  
  useKeyboardShortcuts(shortcuts);
}

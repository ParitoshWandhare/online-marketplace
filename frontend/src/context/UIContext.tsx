import React, { createContext, useContext, useReducer, ReactNode } from 'react';

export type UIMode = 'customer' | 'seller';

interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

interface Modal {
  id: string;
  type: string;
  props?: Record<string, any>;
}

interface UIState {
  mode: UIMode;
  toasts: Toast[];
  modals: Modal[];
}

interface UIContextType extends UIState {
  setMode: (mode: UIMode) => void;
  pushToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  showModal: (modal: Omit<Modal, 'id'>) => void;
  hideModal: (id: string) => void;
  hideAllModals: () => void;
}

type UIAction =
  | { type: 'SET_MODE'; payload: UIMode }
  | { type: 'PUSH_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'SHOW_MODAL'; payload: Modal }
  | { type: 'HIDE_MODAL'; payload: string }
  | { type: 'HIDE_ALL_MODALS' };

const initialState: UIState = {
  mode: 'customer',
  toasts: [],
  modals: [],
};

const uiReducer = (state: UIState, action: UIAction): UIState => {
  switch (action.type) {
    case 'SET_MODE':
      return { ...state, mode: action.payload };
    case 'PUSH_TOAST':
      return { ...state, toasts: [...state.toasts, action.payload] };
    case 'REMOVE_TOAST':
      return { 
        ...state, 
        toasts: state.toasts.filter(toast => toast.id !== action.payload) 
      };
    case 'SHOW_MODAL':
      return { ...state, modals: [...state.modals, action.payload] };
    case 'HIDE_MODAL':
      return { 
        ...state, 
        modals: state.modals.filter(modal => modal.id !== action.payload) 
      };
    case 'HIDE_ALL_MODALS':
      return { ...state, modals: [] };
    default:
      return state;
  }
};

const UIContext = createContext<UIContextType | undefined>(undefined);

export const UIProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(uiReducer, initialState);

  const setMode = (mode: UIMode) => {
    dispatch({ type: 'SET_MODE', payload: mode });
  };

  const pushToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(7);
    dispatch({ type: 'PUSH_TOAST', payload: { ...toast, id } });
    
    // Auto-remove toast after 5 seconds
    setTimeout(() => {
      dispatch({ type: 'REMOVE_TOAST', payload: id });
    }, 5000);
  };

  const removeToast = (id: string) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
  };

  const showModal = (modal: Omit<Modal, 'id'>) => {
    const id = Math.random().toString(36).substring(7);
    dispatch({ type: 'SHOW_MODAL', payload: { ...modal, id } });
  };

  const hideModal = (id: string) => {
    dispatch({ type: 'HIDE_MODAL', payload: id });
  };

  const hideAllModals = () => {
    dispatch({ type: 'HIDE_ALL_MODALS' });
  };

  const value: UIContextType = {
    ...state,
    setMode,
    pushToast,
    removeToast,
    showModal,
    hideModal,
    hideAllModals,
  };

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>;
};

export const useUI = (): UIContextType => {
  const context = useContext(UIContext);
  if (context === undefined) {
    throw new Error('useUI must be used within a UIProvider');
  }
  return context;
};
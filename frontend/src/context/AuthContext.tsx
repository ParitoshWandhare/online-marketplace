import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { User, LoginCredentials, SignupPayload, authService } from '@/services/auth';
import { useToast } from '@/hooks/use-toast';

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  sendOtp: (email: string) => Promise<void>;
  logout: () => void;
  loadProfile: () => Promise<void>;
}

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_AUTH'; payload: { user: User; token: string } }
  | { type: 'SET_USER'; payload: User }
  | { type: 'LOGOUT' };

const initialState: AuthState = {
  user: null,
  token: null,
  loading: true,
};

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_AUTH':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        loading: false,
      };
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'LOGOUT':
      return { ...state, user: null, token: null, loading: false };
    default:
      return state;
  }
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const { toast } = useToast();

  // Load auth data from localStorage on mount
  useEffect(() => {
    const loadAuthData = () => {
      try {
        const token = localStorage.getItem('auth_token');
        const userString = localStorage.getItem('auth_user');
        
        if (token && userString) {
          const user = JSON.parse(userString);
          dispatch({ type: 'SET_AUTH', payload: { user, token } });
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        console.error('Error loading auth data:', error);
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    loadAuthData();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.login(credentials);
      
      // Handle MongoDB _id and convert to id for frontend consistency
      const user = {
        ...response.user,
        id: response.user._id || response.user.id,
      };
      
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      
      dispatch({ type: 'SET_AUTH', payload: { user, token: response.token } });
      
      toast({
        title: 'Welcome back!',
        description: 'You have been successfully logged in.',
      });
    } catch (error: any) {
      dispatch({ type: 'SET_LOADING', payload: false });
      toast({
        title: 'Login failed',
        description: error.response?.data?.message || 'Please check your credentials and try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const signup = async (payload: SignupPayload) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      await authService.signup(payload);
      
      dispatch({ type: 'SET_LOADING', payload: false });
      
      toast({
        title: 'Account created!',
        description: 'Please login with your credentials.',
      });
    } catch (error: any) {
      dispatch({ type: 'SET_LOADING', payload: false });
      toast({
        title: 'Signup failed',
        description: error.response?.data?.message || 'Failed to create account. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const sendOtp = async (email: string) => {
    try {
      await authService.sendOtp({ email });
      toast({
        title: 'OTP Sent',
        description: 'Please check your email for the verification code.',
      });
    } catch (error: any) {
      toast({
        title: 'Failed to send OTP',
        description: error.response?.data?.message || 'Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    dispatch({ type: 'LOGOUT' });
    toast({
      title: 'Logged out',
      description: 'You have been successfully logged out.',
    });
  };

  const loadProfile = async () => {
    try {
      const response = await authService.getProfile();
      const user = {
        ...response.user,
        id: response.user._id || response.user.id,
      };
      localStorage.setItem('auth_user', JSON.stringify(user));
      dispatch({ type: 'SET_USER', payload: user });
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    signup,
    sendOtp,
    logout,
    loadProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthService } from '@/services/auth';
import { User } from '@/types';

// Session state interface
interface SessionState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  sessionValid: boolean;
  lastActivity: string | null;
  error: string | null;
}

// Session action types
type SessionAction =
  | { type: 'SESSION_START_LOADING' }
  | { type: 'SESSION_STOP_LOADING' }
  | { type: 'SESSION_LOGIN_SUCCESS'; payload: { user: User } }
  | { type: 'SESSION_LOGOUT' }
  | { type: 'SESSION_UPDATE_USER'; payload: { user: User } }
  | { type: 'SESSION_SET_ERROR'; payload: { error: string } }
  | { type: 'SESSION_CLEAR_ERROR' }
  | { type: 'SESSION_SET_VALID'; payload: { isValid: boolean } }
  | { type: 'SESSION_UPDATE_ACTIVITY' };

// Initial state
const initialState: SessionState = {
  isAuthenticated: false,
  user: null,
  isLoading: true,
  sessionValid: false,
  lastActivity: null,
  error: null,
};

// Session reducer
const sessionReducer = (state: SessionState, action: SessionAction): SessionState => {
  switch (action.type) {
    case 'SESSION_START_LOADING':
      return { ...state, isLoading: true };
    
    case 'SESSION_STOP_LOADING':
      return { ...state, isLoading: false };
    
    case 'SESSION_LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        isLoading: false,
        sessionValid: true,
        lastActivity: new Date().toISOString(),
        error: null,
      };
    
    case 'SESSION_LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        sessionValid: false,
        lastActivity: null,
        error: null,
      };
    
    case 'SESSION_UPDATE_USER':
      return {
        ...state,
        user: action.payload.user,
        lastActivity: new Date().toISOString(),
      };
    
    case 'SESSION_SET_ERROR':
      return {
        ...state,
        error: action.payload.error,
        isLoading: false,
      };
    
    case 'SESSION_CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    
    case 'SESSION_SET_VALID':
      return {
        ...state,
        sessionValid: action.payload.isValid,
      };
    
    case 'SESSION_UPDATE_ACTIVITY':
      return {
        ...state,
        lastActivity: new Date().toISOString(),
      };
    
    default:
      return state;
  }
};

// Session context interface
interface SessionContextType {
  state: SessionState;
  login: () => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  updateUser: (user: User) => Promise<void>;
  refreshSession: () => Promise<boolean>;
  clearError: () => void;
  updateActivity: () => void;
}

// Create context
const SessionContext = createContext<SessionContextType | undefined>(undefined);

// Session provider component
interface SessionProviderProps {
  children: ReactNode;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(sessionReducer, initialState);

  // Initialize session on app start
  useEffect(() => {
    initializeSession();
    
    // Setup activity monitoring
    const activityInterval = setInterval(() => {
      updateActivity();
    }, 5 * 60 * 1000); // Every 5 minutes
    
    return () => clearInterval(activityInterval);
  }, []);

  // Initialize session
  const initializeSession = async () => {
    dispatch({ type: 'SESSION_START_LOADING' });
    
    try {
      // Attempt to restore existing session
      const sessionResult = await AuthService.restoreSession();
      
      if (sessionResult.success) {
        const userInfo = await AuthService.getStoredUserInfo();
        if (userInfo) {
          dispatch({ type: 'SESSION_LOGIN_SUCCESS', payload: { user: userInfo } });
          
          // Setup periodic token refresh
          await AuthService.setupPeriodicTokenRefresh();
          return;
        }
      }
      
      // No valid session, initialize auth service
      await AuthService.initializeAuth();
      
      // Check if auth is still valid after initialization
      const isAuthenticated = await AuthService.isAuthenticated();
      if (isAuthenticated) {
        const userInfo = await AuthService.getStoredUserInfo();
        if (userInfo) {
          dispatch({ type: 'SESSION_LOGIN_SUCCESS', payload: { user: userInfo } });
          return;
        }
      }
      
      // No valid session found
      dispatch({ type: 'SESSION_LOGOUT' });
      
    } catch (error) {
      console.error('Session initialization failed:', error);
      dispatch({ type: 'SESSION_SET_ERROR', payload: { error: 'Session initialization failed' } });
    } finally {
      dispatch({ type: 'SESSION_STOP_LOADING' });
    }
  };

  // Login function
  const login = async (): Promise<{ success: boolean; error?: string }> => {
    try {
      console.log('🔐 Starting login process...');
      dispatch({ type: 'SESSION_START_LOADING' });
      dispatch({ type: 'SESSION_CLEAR_ERROR' });
      
      // Retrieve stored user information
      console.log('📋 Retrieving stored user info...');
      const userInfo = await AuthService.getStoredUserInfo();
      console.log('👤 Retrieved user info:', userInfo);
      
      if (userInfo) {
        console.log('✅ User info found, validating session...');
        // Validate user session
        const isValid = await AuthService.isSessionValid();
        console.log('🔍 Session validity:', isValid);
        
        if (!isValid) {
          console.log('⚠️ Session invalid, attempting refresh...');
          // Try to refresh the session
          const refreshSuccess = await AuthService.refreshAccessToken();
          console.log('🔄 Refresh result:', refreshSuccess);
          
          if (!refreshSuccess) {
            const error = 'Session expired and refresh failed';
            console.error('❌ Session refresh failed');
            dispatch({ type: 'SESSION_SET_ERROR', payload: { error } });
            return { success: false, error };
          }
        }
        
        // Successfully logged in
        console.log('✅ Login successful, dispatching success...');
        dispatch({ type: 'SESSION_LOGIN_SUCCESS', payload: { user: userInfo } });
        await AuthService.persistSession();
        
        console.log(`🎉 User logged in successfully: ${userInfo.username} (${userInfo.subscription_level})`);
        return { success: true };
      } else {
        const error = 'No user information available';
        console.error('❌ No user info found');
        dispatch({ type: 'SESSION_SET_ERROR', payload: { error } });
        return { success: false, error };
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Login failed';
      console.error('❌ Login process error:', error);
      dispatch({ type: 'SESSION_SET_ERROR', payload: { error: errorMessage } });
      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      await AuthService.logoutUser(dispatch);
      dispatch({ type: 'SESSION_LOGOUT' });
    } catch (error) {
      console.error('Logout failed:', error);
      // Force logout even if API call fails
      dispatch({ type: 'SESSION_LOGOUT' });
    }
  };

  // Update user function
  const updateUser = async (user: User): Promise<void> => {
    try {
      await AuthService.storeUserInfo(user);
      dispatch({ type: 'SESSION_UPDATE_USER', payload: { user } });
    } catch (error) {
      console.error('Failed to update user:', error);
    }
  };

  // Refresh session function
  const refreshSession = async (): Promise<boolean> => {
    try {
      const isValid = await AuthService.isSessionValid();
      dispatch({ type: 'SESSION_SET_VALID', payload: { isValid } });
      
      if (!isValid) {
        await logout();
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('Session refresh failed:', error);
      await logout();
      return false;
    }
  };

  // Clear error function
  const clearError = (): void => {
    dispatch({ type: 'SESSION_CLEAR_ERROR' });
  };

  // Update activity function
  const updateActivity = async (): Promise<void> => {
    try {
      await AuthService.updateSessionActivity();
      dispatch({ type: 'SESSION_UPDATE_ACTIVITY' });
    } catch (error) {
      console.error('Failed to update activity:', error);
    }
  };

  const contextValue: SessionContextType = {
    state,
    login,
    logout,
    updateUser,
    refreshSession,
    clearError,
    updateActivity,
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

// Hook to use session context
export const useSession = (): SessionContextType => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

export default SessionContext;
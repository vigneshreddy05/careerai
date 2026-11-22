import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  updateUserProfile,
  deleteUserAccount,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('careerai_token'));
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Initialize and validate token on application load
  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      const storedToken = localStorage.getItem('careerai_token');
      if (!storedToken) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const data = await getCurrentUser();
        if (isMounted && data.success) {
          setUser(data.user);
        }
      } catch (err) {
        // Token invalid or expired
        console.warn('Session expired or invalidated. Resetting auth state.');
        localStorage.removeItem('careerai_token');
        if (isMounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    checkAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    setAuthError(null);
    try {
      const data = await loginUser({ email, password });
      if (data.token) {
        localStorage.setItem('careerai_token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data.user;
      }
      return null;
    } catch (err) {
      let message = 'Failed to authenticate.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setAuthError(message);
      throw new Error(message);
    }
  }, []);

  const register = useCallback(async (userData) => {
    setAuthError(null);
    try {
      const data = await registerUser(userData);
      if (data.token) {
        localStorage.setItem('careerai_token', data.token);
        setToken(data.token);
        setUser(data.user);
        return data.user;
      }
      return null;
    } catch (err) {
      let message = 'Failed to create account.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      setAuthError(message);
      throw new Error(message);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutUser();
    } catch (err) {
      console.warn('Logout API notification failed:', err);
    } finally {
      localStorage.removeItem('careerai_token');
      setToken(null);
      setUser(null);
      setAuthError(null);
    }
  }, []);

  const updateProfile = useCallback(async (updates) => {
    try {
      const data = await updateUserProfile(updates);
      if (data.success && data.user) {
        setUser(data.user);
        return data.user;
      }
      return null;
    } catch (err) {
      let message = 'Failed to update profile.';
      if (err.response && err.response.data && err.response.data.detail) {
        message = err.response.data.detail;
      } else if (err.message) {
        message = err.message;
      }
      throw new Error(message);
    }
  }, []);

  const deleteAccount = useCallback(async () => {
    try {
      await deleteUserAccount();
    } finally {
      localStorage.removeItem('careerai_token');
      setToken(null);
      setUser(null);
      setAuthError(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        authError,
        setAuthError,
        login,
        register,
        logout,
        updateProfile,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { authAPI } from '../services/api';

type User = {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
} | null;

type AuthContextType = {
  user: User;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  error: string | null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true); // Start with loading true
  const [error, setError] = useState<string | null>(null);
  const isInitialCheckDoneRef = useRef<boolean>(false);
  
  // Check if user is already logged in on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      if (isInitialCheckDoneRef.current) {
        return; // Skip if we've already done the initial check
      }
      
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        try {
          console.log('Found stored token and user data');
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          
          // Optional: validate token with backend
          // This is commented out for now to avoid making an extra request
          // await authAPI.getCurrentUser();
        } catch (err) {
          console.error('Error parsing stored user data:', err);
          // Clear invalid session data
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
        }
      }
      
      isInitialCheckDoneRef.current = true;
      setIsLoading(false);
    };
    
    checkAuthStatus();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Starting login process');
      const data = await authAPI.login(username, password);
      
      console.log('Storing token and user info');
      // Store token and user info
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      setUser(data.user);
      console.log('Login complete, user authenticated');
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Starting registration process');
      // Register the user
      await authAPI.register(username, email, password);
      
      console.log('Registration successful, logging in');
      // Automatically log the user in after registration
      await login(username, password);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : 'Registration failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  const logout = useCallback(() => {
    console.log('Logging out, clearing stored data');
    // Clear local storage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    
    // Dispatch a custom event that other contexts can listen for
    window.dispatchEvent(new CustomEvent('user-logout'));
  }, []);

  // Memoize the value to prevent unnecessary re-renders
  const value = React.useMemo(() => ({
    user,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    isLoading,
    error
  }), [user, login, register, logout, isLoading, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
// src/context/AgentContext.tsx
import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { agentAPI } from '../services/api';
import { useAuth } from './AuthContext';

export interface Agent {
  id: number;
  name: string;
  voice: string;
  knowledge: string | null;
  system_prompt: string;
  speed: number;
  min_silence: number;
  user_id: number;
  api_key?: string;
}

interface AgentContextType {
  agents: Agent[];
  addAgent: (agent: Omit<Agent, 'id' | 'user_id'>) => Promise<void>;
  updateAgent: (id: number, updates: Partial<Agent>) => Promise<void>;
  deleteAgent: (id: number) => Promise<void>;
  regenerateApiKey: (id: number) => Promise<void>;
  loading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export const AgentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, user } = useAuth();
  
  
  // Track if we're currently in a fetch operation to prevent duplicate calls
  const isFetchingRef = useRef<boolean>(false);
  // Track if initialization has happened
  const isInitializedRef = useRef<boolean>(false);
  // Store the last user ID to detect actual user changes
  const lastUserIdRef = useRef<number | null>(null);
  
  // Memoize the fetchAgents function to prevent recreation on renders
  const fetchAgents = useCallback(async () => {
    // Guard clauses to prevent duplicate or unnecessary fetches
    if (!isAuthenticated || !user) {
      console.log('Not authenticated or no user, skipping fetch');
      return;
    }
    
    if (isFetchingRef.current) {
      console.log('Already fetching agents, skipping duplicate fetch');
      return;
    }
    
    // Only fetch if user actually changed or we haven't fetched for this user yet
    if (lastUserIdRef.current === user.id && isInitializedRef.current) {
      console.log('User has not changed, skipping fetch');
      return;
    }
    
    // Set fetching flag to true to prevent duplicate calls
    isFetchingRef.current = true;
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching agents for user:', user.id);
      const data = await agentAPI.getAgents();
      console.log('Agents fetched successfully:', data.length || 'none');
      setAgents(data);
      
      // Update refs after successful fetch
      lastUserIdRef.current = user.id;
      isInitializedRef.current = true;
    } catch (err) {
      console.error('Error fetching agents:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, [isAuthenticated, user]);

  // Clear agents when user logs out
  useEffect(() => {
    const handleLogout = () => {
      console.log('Clearing agents on logout');
      setAgents([]);
      lastUserIdRef.current = null;
      isInitializedRef.current = false;
    };
    
    window.addEventListener('user-logout', handleLogout);
    
    return () => {
      window.removeEventListener('user-logout', handleLogout);
    };
  }, []);

  // Fetch agents when user authenticates
  useEffect(() => {
    // Only fetch if:
    // 1. User is authenticated and exists
    // 2. Either we haven't initialized yet OR the user has changed
    if (isAuthenticated && user && 
       (!isInitializedRef.current || lastUserIdRef.current !== user.id)) {
      fetchAgents();
    } else if (!isAuthenticated) {
      // Clear agents when not authenticated
      setAgents([]);
      lastUserIdRef.current = null;
      isInitializedRef.current = false;
    }
  }, [isAuthenticated, user, fetchAgents]);

  const addAgent = async (agentData: Omit<Agent, 'id' | 'user_id'>) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Adding new agent:', agentData.name);
      const newAgent = await agentAPI.createAgent(agentData);
      console.log('Agent added successfully:', newAgent);
      
      // Update the local state without fetching
      setAgents(prev => [...prev, newAgent.agent]);
      return newAgent;
    } catch (err) {
      console.error('Error adding agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to add agent');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateAgent = async (id: number, updates: Partial<Agent>) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Updating agent:', id);
      const updated = await agentAPI.updateAgent(id, updates);
      console.log('Agent updated successfully');
      
      // Update the local state without fetching
      setAgents(prev => prev.map(agent => 
        agent.id === id ? updated.agent : agent
      ));
      return updated;
    } catch (err) {
      console.error('Error updating agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to update agent');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (id: number) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Deleting agent:', id);
      await agentAPI.deleteAgent(id);
      console.log('Agent deleted successfully');
      
      // Update the local state
      setAgents(prev => prev.filter(agent => agent.id !== id));
    } catch (err) {
      console.error('Error deleting agent:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete agent');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const regenerateApiKey = async (id: number) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Regenerating API key for agent:', id);
      const response = await agentAPI.regenerateApiKey(id);
      console.log('API key regenerated successfully');
      
      // Update this specific agent in the local state
      setAgents(prev => prev.map(agent => 
        agent.id === id ? response.agent : agent
      ));
      return response;
    } catch (err) {
      console.error('Error regenerating API key:', err);
      setError(err instanceof Error ? err.message : 'Failed to regenerate API key');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Create a memoized context value to prevent unnecessary re-renders
  const contextValue = React.useMemo(() => ({
    agents, 
    addAgent, 
    updateAgent, 
    deleteAgent, 
    regenerateApiKey,
    loading, 
    error,
    fetchAgents
  }), [agents, loading, error, fetchAgents]);

  return (
    <AgentContext.Provider value={contextValue}>
      {children}
    </AgentContext.Provider>
  );
};

export const useAgents = () => {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgents must be used within an AgentProvider');
  }
  return context;
};
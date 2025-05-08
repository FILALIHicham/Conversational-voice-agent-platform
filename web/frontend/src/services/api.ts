// src/services/api.ts
const API_URL = 'http://localhost:5000';

// Get the stored JWT token
const getToken = () => localStorage.getItem('token');

// Helper for handling API responses
const handleResponse = async (response: Response) => {
  const data = await response.json();
  
  if (!response.ok) {
    console.error('API Error:', response.status, data);
    const error = data.message || response.statusText;
    throw new Error(error);
  }
  
  return data;
};

// Authentication API calls
export const authAPI = {
  // Log in a user
  login: async (username: string, password: string) => {
    console.log('Attempting login for:', username);
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    
    const data = await response.json();
    console.log('Login response status:', response.status);
    
    if (!response.ok) {
      throw new Error(data.message || 'Login failed');
    }
    
    console.log('Login successful, token received');
    return data;
  },
  
  // Register a new user
  register: async (username: string, email: string, password: string) => {
    console.log('Attempting registration for:', username);
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });
    
    const data = await response.json();
    console.log('Registration response status:', response.status);
    
    if (!response.ok) {
      throw new Error(data.message || 'Registration failed');
    }
    
    console.log('Registration successful');
    return data;
  },
  
  // Get current user profile
  getCurrentUser: async () => {
    const token = getToken();
    if (!token) return null;
    
    console.log('Checking current user with token');
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    if (!response.ok) {
      console.log('Invalid token or session');
      return null;
    }
    
    return handleResponse(response);
  },
};

// Agent API calls
export const agentAPI = {
  // Get all agents for the current user
  getAgents: async () => {
    const token = getToken();
    if (!token) {
      console.error('No token available');
      throw new Error('Not authenticated');
    }
    
    console.log('Fetching agents with token');
    try {
      const response = await fetch(`${API_URL}/agents`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      console.log('Agents response status:', response.status);
      const data = await response.json();
      
      if (!response.ok) {
        console.error('Error response:', data);
        throw new Error(data.message || 'Failed to fetch agents');
      }
      
      return data;
    } catch (error) {
      console.error('Error fetching agents:', error);
      throw error;
    }
  },
  
  // Get a specific agent
  getAgent: async (agentId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/agents/${agentId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Create a new agent
  createAgent: async (agentData: {
    name: string;
    voice: string;
    knowledge?: string;
    system_prompt: string;
    speed: number;
    min_silence: number;
  }) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/agents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(agentData),
    });
    
    return handleResponse(response);
  },
  
  // Update an agent
  updateAgent: async (agentId: number, agentData: Partial<{
    name: string;
    voice: string;
    knowledge: string;
    system_prompt: string;
    speed: number;
    min_silence: number;
  }>) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/agents/${agentId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(agentData),
    });
    
    return handleResponse(response);
  },
  
  // Delete an agent
  deleteAgent: async (agentId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/agents/${agentId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Regenerate an agent's API key
  regenerateApiKey: async (agentId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/agents/${agentId}/regenerate-key`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
};

// Customer API calls
export const customerAPI = {
  // Get customers for a specific agent
  getCustomersByAgent: async (agentId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/customers/agent/${agentId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Get a specific customer
  getCustomer: async (customerId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/customers/${customerId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Create a new customer for an agent
  createCustomer: async (agentId: number, customerData: {
    phone_number: string;
    name?: string;
    address?: string;
  }) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/customers/agent/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(customerData),
    });
    
    return handleResponse(response);
  },
  
  // Update a customer
  updateCustomer: async (customerId: number, customerData: Partial<{
    phone_number: string;
    name: string;
    address: string;
  }>) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/customers/${customerId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(customerData),
    });
    
    return handleResponse(response);
  },
  
  // Delete a customer
  deleteCustomer: async (customerId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/customers/${customerId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
};

// Order API calls
export const orderAPI = {
  // Get orders for a specific customer
  getOrdersByCustomer: async (customerId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/customer/${customerId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Get a specific order with its items
  getOrderDetails: async (orderId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/${orderId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Create a new order for a customer
  createOrder: async (customerId: number, orderData: {
    total_amount?: number;
    status?: string;
    items?: Array<{
      product_name: string;
      price: number;
      quantity: number;
    }>;
  }) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/customer/${customerId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(orderData),
    });
    
    return handleResponse(response);
  },
  
  // Update order status
  updateOrderStatus: async (orderId: number, status: string) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/${orderId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ status }),
    });
    
    return handleResponse(response);
  },
  
  // Add item to an order
  addOrderItem: async (orderId: number, itemData: {
    product_name: string;
    price: number;
    quantity?: number;
  }) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/${orderId}/items`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(itemData),
    });
    
    return handleResponse(response);
  },
  
  // Remove item from an order
  removeOrderItem: async (orderId: number, itemId: number) => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/orders/${orderId}/items/${itemId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
};

// Statistics API calls
export const statsAPI = {
  // Get order statistics
  getOrderStats: async () => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/stats/orders`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
  
  // Get popular items
  getPopularItems: async () => {
    const token = getToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_URL}/stats/popular-items`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    
    return handleResponse(response);
  },
};
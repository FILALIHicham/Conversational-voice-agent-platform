// src/pages/AgentDetails.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { agentAPI, orderAPI, customerAPI } from '../services/api';
import { 
  IconArrowLeft, 
  IconKey, 
  IconRobot, 
  IconSettings, 
  IconUser, 
  IconPhone, 
  IconShoppingCart, 
  IconBox,
  IconChevronDown,
  IconCalendar,
  IconCoins,
  IconClipboardCheck
} from '@tabler/icons-react';

interface Agent {
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

interface Customer {
  id: number;
  phone_number: string;
  name: string | null;
  address: string | null;
  agent_id: number;
  orders: Order[];
}

interface OrderItem {
  id: number;
  product_name: string;
  quantity: number;
  price: number;
  order_id: number;
  subtotal: number;
}

interface Order {
  id: number;
  total_amount: number;
  status: string;
  created_at: string;
  customer_id: number;
  items: OrderItem[];
}

const AgentDetails = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [customersWithOrders, setCustomersWithOrders] = useState<Customer[]>([]);
  const [showApiKey, setShowApiKey] = useState(false);
  const [regeneratingKey, setRegeneratingKey] = useState(false);
  const [expandedCustomer, setExpandedCustomer] = useState<number | null>(null);
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null);
  const [statusUpdating, setStatusUpdating] = useState<number | null>(null);

  // Fetch agent details
  useEffect(() => {
    const fetchAgentDetails = async () => {
      if (!id) return;
      
      try {
        setLoading(true);
        const agentData = await agentAPI.getAgent(parseInt(id));
        setAgent(agentData);
        
        // Fetch customers for this agent
        try {
          // Use the customerAPI service instead of direct fetch
          const customersData = await customerAPI.getCustomersByAgent(parseInt(id));
          
          // For each customer, fetch their orders
          const customersWithOrdersData = await Promise.all(
            customersData.map(async (customer: any) => {
              try {
                const orders = await orderAPI.getOrdersByCustomer(customer.id);
                return {
                  ...customer,
                  orders: orders || []
                };
              } catch (err) {
                console.error(`Error fetching orders for customer ${customer.id}:`, err);
                return {
                  ...customer,
                  orders: []
                };
              }
            })
          );
          
          setCustomersWithOrders(customersWithOrdersData);
        } catch (err) {
          console.error("Error fetching customers:", err);
          setCustomersWithOrders([]);
        }
        
      } catch (err) {
        console.error("Error fetching agent details:", err);
        setError("Failed to load agent details. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgentDetails();
  }, [id]);

  const handleRegenerateApiKey = async () => {
    if (!agent) return;
    
    if (window.confirm("Are you sure you want to regenerate the API key? This will invalidate the current key.")) {
      try {
        setRegeneratingKey(true);
        const response = await agentAPI.regenerateApiKey(agent.id);
        setAgent(response.agent);
      } catch (err) {
        console.error("Error regenerating API key:", err);
        alert("Failed to regenerate API key. Please try again.");
      } finally {
        setRegeneratingKey(false);
      }
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        alert("Copied to clipboard!");
      })
      .catch(err => {
        console.error("Failed to copy text: ", err);
      });
  };

  const toggleCustomerExpand = (customerId: number) => {
    if (expandedCustomer === customerId) {
      setExpandedCustomer(null);
    } else {
      setExpandedCustomer(customerId);
    }
    // Close any expanded order when toggling customers
    setExpandedOrder(null);
  };

  const toggleOrderExpand = (orderId: number) => {
    if (expandedOrder === orderId) {
      setExpandedOrder(null);
    } else {
      setExpandedOrder(orderId);
    }
  };

  const updateOrderStatus = async (orderId: number, newStatus: string) => {
    try {
      setStatusUpdating(orderId);
      await orderAPI.updateOrderStatus(orderId, newStatus);
      
      // Update the local state to reflect the change
      setCustomersWithOrders(prev => prev.map(customer => ({
        ...customer,
        orders: customer.orders.map(order => 
          order.id === orderId 
            ? { ...order, status: newStatus } 
            : order
        )
      })));
    } catch (err) {
      console.error("Error updating order status:", err);
      alert("Failed to update order status. Please try again.");
    } finally {
      setStatusUpdating(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-navy-200 border-t-navy-600 rounded-full animate-spin mb-4"></div>
          <p className="text-navy-600 font-medium">Loading agent details...</p>
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-md p-8 max-w-md w-full">
          <div className="text-red-500 text-center mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-2xl font-bold mt-4">Error Loading Agent</h2>
            <p className="mt-2">{error || "Agent not found"}</p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="w-full py-3 px-4 bg-navy-600 text-white font-medium rounded-lg transition-all duration-300 hover:bg-navy-700"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Calculate summary stats
  const totalCustomers = customersWithOrders.length;
  const totalOrders = customersWithOrders.reduce((sum, customer) => sum + customer.orders.length, 0);
  const completedOrders = customersWithOrders.reduce((sum, customer) => 
    sum + customer.orders.filter(order => order.status === 'Completed').length, 0);
  const totalRevenue = customersWithOrders.reduce((sum, customer) => 
    sum + customer.orders.reduce((orderSum, order) => orderSum + order.total_amount, 0), 0);

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-navy-600 hover:text-navy-800 transition-colors"
          >
            <IconArrowLeft size={18} className="mr-1" />
            Back to Dashboard
          </button>
        </div>
        
        <div className="bg-white rounded-xl shadow-md overflow-hidden border border-neutral-200">
          {/* Agent Header */}
          <div className="px-6 py-5 bg-gradient-to-r from-navy-600 to-navy-700 text-white">
            <div className="flex items-center">
              <div className="w-12 h-12 rounded-lg bg-white/20 flex items-center justify-center mr-4">
                <IconRobot size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{agent.name}</h1>
                <p className="text-navy-100 mt-1">Voice: {agent.voice} • Speed: {agent.speed}x</p>
              </div>
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="border-b border-neutral-200 bg-white">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-neutral-200">
              <div className="p-4 sm:p-6">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-lg bg-navy-100 text-navy-600 flex items-center justify-center mr-3">
                    <IconUser size={20} />
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Customers</p>
                    <p className="text-xl font-semibold text-neutral-900">{totalCustomers}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-4 sm:p-6">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-lg bg-navy-100 text-navy-600 flex items-center justify-center mr-3">
                    <IconShoppingCart size={20} />
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Total Orders</p>
                    <p className="text-xl font-semibold text-neutral-900">{totalOrders}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-4 sm:p-6">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-lg bg-green-100 text-green-600 flex items-center justify-center mr-3">
                    <IconClipboardCheck size={20} />
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Completed</p>
                    <p className="text-xl font-semibold text-neutral-900">{completedOrders}</p>
                  </div>
                </div>
              </div>
              
              <div className="p-4 sm:p-6">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-lg bg-accent-100 text-accent-600 flex items-center justify-center mr-3">
                    <IconCoins size={20} />
                  </div>
                  <div>
                    <p className="text-sm text-neutral-500">Revenue</p>
                    <p className="text-xl font-semibold text-neutral-900">${totalRevenue.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            {/* Updated grid with new column distribution: 40% left, 60% right */}
            <div className="grid grid-cols-1 md:grid-cols-10 gap-6">
              {/* Main Info Column - 40% width */}
              <div className="md:col-span-4 space-y-6">
                <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                  <h2 className="text-lg font-semibold text-neutral-900 mb-3">System Prompt</h2>
                  <p className="text-neutral-700 whitespace-pre-line">{agent.system_prompt}</p>
                </div>
                
                {agent.knowledge && (
                  <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                    <h2 className="text-lg font-semibold text-neutral-900 mb-3">Knowledge Base</h2>
                    <p className="text-neutral-700 whitespace-pre-line">{agent.knowledge}</p>
                  </div>
                )}
                
              </div>
              
              {/* Settings Column - 60% width */}
              <div className="md:col-span-6 space-y-6">
                <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                  <h2 className="text-lg font-semibold text-neutral-900 mb-3 flex items-center">
                    <IconSettings size={20} className="mr-2 text-navy-500" />
                    Settings
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-neutral-500 mb-1">
                        Voice Model
                      </label>
                      <div className="bg-white border border-neutral-300 rounded-lg p-3 text-neutral-700">
                        {agent.voice}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-neutral-500 mb-1">
                        Speech Speed
                      </label>
                      <div className="bg-white border border-neutral-300 rounded-lg p-3 text-neutral-700">
                        {agent.speed}x
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-neutral-500 mb-1">
                        Minimum Silence
                      </label>
                      <div className="bg-white border border-neutral-300 rounded-lg p-3 text-neutral-700">
                        {agent.min_silence} ms
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                  <h2 className="text-lg font-semibold text-neutral-900 mb-3">API Integration</h2>
                  <div className="mb-3">
                    <label className="block text-sm font-medium text-neutral-500 mb-1">
                      API Key
                    </label>
                    <div className="flex items-center">
                      <div className="flex-1 bg-white border border-neutral-300 rounded-lg p-3 font-mono text-sm overflow-hidden whitespace-nowrap overflow-ellipsis">
                        {showApiKey ? agent.api_key : '••••••••••••••••••••••••••••••••••••••'}
                      </div>
                      <button
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="ml-2 p-2 text-navy-600 hover:bg-navy-50 rounded-lg"
                      >
                        {showApiKey ? 'Hide' : 'Show'}
                      </button>
                      <button
                        onClick={() => agent.api_key && copyToClipboard(agent.api_key)}
                        className="ml-2 p-2 text-navy-600 hover:bg-navy-50 rounded-lg"
                        disabled={!showApiKey}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={handleRegenerateApiKey}
                    disabled={regeneratingKey}
                    className="flex items-center px-4 py-2 bg-navy-600 hover:bg-navy-700 text-white rounded-lg transition-all"
                  >
                    {regeneratingKey ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : (
                      <>
                        <IconKey size={18} className="mr-2" />
                        Regenerate API Key
                      </>
                    )}
                  </button>
                </div>
                {/* Customers Section */}
                <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                  <h2 className="text-lg font-semibold text-neutral-900 mb-3 flex items-center">
                    <IconUser size={20} className="mr-2 text-navy-500" />
                    Customers
                  </h2>
                  {customersWithOrders.length > 0 ? (
                    <div className="space-y-2">
                      {customersWithOrders.map((customer) => (
                        <div key={customer.id} className="border border-neutral-200 rounded-lg overflow-hidden">
                          <div 
                            className="bg-white p-3 flex items-center justify-between cursor-pointer hover:bg-neutral-50"
                            onClick={() => toggleCustomerExpand(customer.id)}
                          >
                            <div className="flex items-center">
                              <div className="w-8 h-8 rounded-full bg-navy-100 flex items-center justify-center mr-3">
                                <IconPhone size={14} className="text-navy-600" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-neutral-900 truncate">
                                  {customer.name || 'Unknown'}
                                </p>
                                <p className="text-xs text-neutral-500 truncate">
                                  {customer.phone_number}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center">
                              <span className="text-xs bg-navy-50 text-navy-700 rounded-full px-2 py-1">
                                {customer.orders.length} orders
                              </span>
                              <IconChevronDown
                                size={16}
                                className={`ml-2 text-neutral-500 transition-transform duration-300 ${expandedCustomer === customer.id ? 'transform rotate-180' : ''}`}
                              />
                            </div>
                          </div>
                          
                          {/* Orders for this customer - shown when expanded */}
                          <div 
                            className={`transition-all duration-300 overflow-hidden ${
                              expandedCustomer === customer.id 
                                ? 'max-h-[2000px] opacity-100' 
                                : 'max-h-0 opacity-0'
                            }`}
                          >
                            <div className="bg-neutral-50 p-3 border-t border-neutral-200">
                              <h4 className="text-sm font-medium text-neutral-700 mb-2">Orders</h4>
                              {customer.orders.length > 0 ? (
                                <div className="space-y-2">
                                  {customer.orders.map((order) => (
                                    <div key={order.id} className="border border-neutral-200 rounded-lg overflow-hidden">
                                      <div 
                                        className="bg-white p-3 flex items-center justify-between cursor-pointer hover:bg-neutral-50"
                                        onClick={() => toggleOrderExpand(order.id)}
                                      >
                                        <div className="flex items-center">
                                          <div className="w-7 h-7 rounded-full bg-accent-100 flex items-center justify-center mr-2">
                                            <IconShoppingCart size={12} className="text-accent-600" />
                                          </div>
                                          <div>
                                            <p className="text-sm font-medium text-neutral-900">
                                              Order #{order.id}
                                            </p>
                                            <p className="text-xs text-neutral-500">
                                              {new Date(order.created_at).toLocaleDateString()} • ${order.total_amount.toFixed(2)}
                                            </p>
                                          </div>
                                        </div>
                                        <div className="flex items-center">
                                          <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
                                            <span className={`text-xs rounded-full px-2 py-1 mr-2 ${
                                              order.status === 'Completed' 
                                                ? 'bg-green-100 text-green-800' 
                                                : order.status === 'Out for Delivery' 
                                                  ? 'bg-blue-100 text-blue-800'
                                                  : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                              {order.status}
                                            </span>
                                            <div className="relative">
                                              <select
                                                value={order.status}
                                                onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                                                className="appearance-none text-xs rounded-md border border-neutral-300 p-1.5 bg-white text-neutral-700 pr-7 pl-2 cursor-pointer focus:outline-none focus:ring-1 focus:ring-accent-500 focus:border-accent-500"
                                                disabled={statusUpdating === order.id}
                                              >
                                                <option value="Preparation">Preparation</option>
                                                <option value="Out for Delivery">Out for Delivery</option>
                                                <option value="Completed">Completed</option>
                                              </select>
                                              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-1.5 text-neutral-500">
                                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                                                </svg>
                                              </div>
                                            </div>
                                          </div>
                                          <button 
                                            className="ml-2 text-neutral-500 p-1 rounded-full hover:bg-neutral-100 transition-colors"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              toggleOrderExpand(order.id);
                                            }}
                                          >
                                            <IconChevronDown
                                              size={16}
                                              className={`transition-transform duration-300 ${expandedOrder === order.id ? 'transform rotate-180' : ''}`}
                                            />
                                          </button>
                                        </div>
                                      </div>
                                      
                                      {/* Order items - shown when order is expanded with animation */}
                                      <div 
                                        className={`transition-all duration-300 overflow-hidden ${
                                          expandedOrder === order.id 
                                            ? 'max-h-[1000px] opacity-100' 
                                            : 'max-h-0 opacity-0'
                                        }`}
                                      >
                                        <div className="content-container bg-neutral-100 p-3 border-t border-neutral-200">
                                          <h5 className="text-xs font-medium text-neutral-700 mb-2 flex items-center">
                                            <IconBox size={14} className="mr-1 text-accent-600" />
                                            Order Items
                                          </h5>
                                          <div className="bg-white rounded border border-neutral-200 overflow-x-auto order-panel">
                                            <table className="order-items-table w-full divide-y divide-neutral-200">
                                              <thead>
                                                <tr className="bg-neutral-50">
                                                  <th className="px-3 py-2 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider w-1/2">
                                                    Product
                                                  </th>
                                                  <th className="px-3 py-2 text-center text-xs font-medium text-neutral-500 uppercase tracking-wider w-1/6">
                                                    Quantity
                                                  </th>
                                                  <th className="px-3 py-2 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider w-1/6">
                                                    Price
                                                  </th>
                                                  <th className="px-3 py-2 text-right text-xs font-medium text-neutral-500 uppercase tracking-wider w-1/6">
                                                    Subtotal
                                                  </th>
                                                </tr>
                                              </thead>
                                              <tbody className="divide-y divide-neutral-200">
                                                {order.items && order.items.length > 0 ? (
                                                  order.items.map((item) => (
                                                    <tr key={item.id}>
                                                      <td className="px-3 py-2 text-sm text-neutral-800">
                                                        {item.product_name}
                                                      </td>
                                                      <td className="px-3 py-2 text-sm text-neutral-800 text-center">
                                                        {item.quantity}
                                                      </td>
                                                      <td className="px-3 py-2 text-sm text-neutral-800 text-right">
                                                        ${item.price.toFixed(2)}
                                                      </td>
                                                      <td className="px-3 py-2 text-sm font-medium text-neutral-800 text-right">
                                                        ${(item.price * item.quantity).toFixed(2)}
                                                      </td>
                                                    </tr>
                                                  ))
                                                ) : (
                                                  <tr>
                                                    <td colSpan={4} className="px-3 py-2 text-sm text-neutral-500 text-center">
                                                      No items found
                                                    </td>
                                                  </tr>
                                                )}
                                              </tbody>
                                              <tfoot className="bg-neutral-50">
                                                <tr>
                                                  <td colSpan={3} className="px-3 py-2 text-sm font-medium text-neutral-800 text-right">
                                                    Total
                                                  </td>
                                                  <td className="px-3 py-2 text-sm font-bold text-neutral-800 text-right">
                                                    ${order.total_amount.toFixed(2)}
                                                  </td>
                                                </tr>
                                              </tfoot>
                                            </table>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div className="bg-white border border-neutral-200 rounded-lg p-3 text-center text-neutral-500 text-sm">
                                  No orders yet
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-white border border-neutral-200 rounded-lg p-4 text-center text-neutral-500">
                      No customers yet
                    </div>
                  )}
                </div>
                
                {/* Recent Orders Section */}
                <div className="bg-neutral-50 rounded-lg p-5 border border-neutral-200">
                  <h2 className="text-lg font-semibold text-neutral-900 mb-3 flex items-center">
                    <IconShoppingCart size={20} className="mr-2 text-navy-500" />
                    Recent Orders
                  </h2>
                  
                  {customersWithOrders.flatMap(c => c.orders).length > 0 ? (
                    <div className="space-y-2">
                      {customersWithOrders
                        .flatMap(c => c.orders.map((o) => ({
                          ...o, 
                          customer: { 
                            id: c.id, 
                            name: c.name, 
                            phone_number: c.phone_number 
                          }
                        })))
                        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                        .slice(0, 3) // Show only 3 most recent
                        .map((order) => (
                          <div key={order.id} className="bg-white border border-neutral-200 rounded-lg p-3">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <span className="text-sm font-medium text-neutral-900">Order #{order.id}</span>
                                <div className="text-xs text-neutral-500">
                                  {new Date(order.created_at).toLocaleDateString()} • {order.customer.name || 'Unknown'}
                                </div>
                              </div>
                              <span className={`text-xs rounded-full px-2 py-1 ${
                                order.status === 'Completed' 
                                  ? 'bg-green-100 text-green-800' 
                                  : order.status === 'Out for Delivery' 
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {order.status}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <div className="text-xs text-neutral-500">
                                {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                              </div>
                              <div className="text-sm font-medium text-right text-neutral-900">
                                ${order.total_amount.toFixed(2)}
                              </div>
                            </div>
                          </div>
                        ))}
                      
                      {/* View all orders link */}
                      {customersWithOrders.flatMap(c => c.orders).length > 3 && (
                        <button className="w-full text-center py-2 border border-neutral-200 rounded-lg text-navy-600 hover:bg-navy-50 text-sm font-medium">
                          View all orders ({customersWithOrders.flatMap(c => c.orders).length})
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="bg-white border border-neutral-200 rounded-lg p-4 text-center text-neutral-500">
                      No recent orders
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDetails;
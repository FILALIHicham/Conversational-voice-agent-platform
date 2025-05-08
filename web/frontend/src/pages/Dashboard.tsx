// src/pages/Dashboard.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useAgents, Agent } from '../context/AgentContext';
import { IconPlus, IconDotsVertical, IconPencil, IconTrash, IconArrowRight, IconRobot, IconInfoCircle } from '@tabler/icons-react';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const { agents, addAgent, updateAgent, deleteAgent, fetchAgents, loading: agentsLoading, error: agentsError } = useAgents();
  const navigate = useNavigate();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [modalMode, setModalMode] = useState<'edit' | 'create'>('create');
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // Simple loading indicator with timeout
  useEffect(() => {
    if (!agents || agents.length === 0) {
      // Only show loading indicator if we don't have agents yet
      setIsLoadingInitial(true);
      
      // Fetch agents
      fetchAgents()
        .finally(() => {
          // Hide loading after fetch completes (success or error)
          setTimeout(() => {
            setIsLoadingInitial(false);
          }, 500);
        });
    } else {
      // If we already have agents, no need for loading indicator
      setIsLoadingInitial(false);
    }
  }, [fetchAgents]);

  const toggleMenu = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeMenu === id) {
      setActiveMenu(null);
    } else {
      setActiveMenu(id);
    }
  };

  const handleEdit = (agent: Agent, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedAgent(agent);
    setModalMode('edit');
    setShowModal(true);
    setActiveMenu(null);
  };

  const handleDelete = async (agent: Agent, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${agent.name}?`)) {
      try {
        await deleteAgent(agent.id);
      } catch (err) {
        console.error("Error deleting agent:", err);
        alert("Failed to delete agent. Please try again.");
      }
    }
    setActiveMenu(null);
  };

  const handleCreate = () => {
    setSelectedAgent(null);
    setModalMode('create');
    setShowModal(true);
  };

  const navigateToDetails = (agentId: number) => {
    navigate(`/agents/${agentId}`);
  };

  // Show loading spinner if either initial loading or data is loading
  if (isLoadingInitial || agentsLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-navy-200 border-t-navy-600 rounded-full animate-spin mb-4"></div>
          <p className="text-navy-600 font-medium">Loading your agents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 overflow-hidden">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white bg-opacity-80 backdrop-blur-md border-b border-neutral-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="w-8 h-8 rounded-md bg-gradient-to-r from-navy-600 to-navy-400 flex items-center justify-center mr-2">
                  <IconRobot size={20} className="text-white" />
                </div>
                <span className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-navy-700 to-navy-500">
                  AgentHub
                </span>
              </div>
            </div>
            <div className="flex items-center">
              <div className="ml-4 flex items-center md:ml-6 gap-4">
                <div className="relative group">
                  <div className="flex items-center px-3 py-1.5 rounded-full bg-navy-50 text-navy-700 text-sm font-medium transition-all duration-300 group-hover:bg-navy-100">
                    <span className="mr-1">{user?.username || 'User'}</span>
                  </div>
                </div>
                <button
                  onClick={() => logout()}
                  className="px-3 py-1.5 rounded-full bg-white text-neutral-600 text-sm font-medium border border-neutral-200 hover:bg-neutral-100 transition-all duration-300"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {agentsError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            Error: {agentsError}
          </div>
        )}
      
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 mb-1">My Agents</h1>
            <p className="text-neutral-500">Manage your AI agents and their configurations</p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2.5 bg-navy-600 hover:bg-navy-700 text-white rounded-lg inline-flex items-center transition-all duration-300 shadow-sm hover:shadow transform hover:-translate-y-0.5"
          >
            <IconPlus size={18} className="mr-1.5" />
            New Agent
          </button>
        </div>

        {/* Agents grid */}
        {agents && agents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="bg-white rounded-xl border border-neutral-200 overflow-hidden hover:shadow-lg transition-all duration-300"
                onClick={() => navigateToDetails(agent.id)}
              >
                <div className="px-6 py-5">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center mb-3">
                      <div className="w-10 h-10 rounded-lg bg-navy-100 text-navy-600 flex items-center justify-center mr-3">
                        <IconRobot size={20} />
                      </div>
                      <h2 className="text-lg font-semibold text-neutral-900 truncate">
                        {agent.name}
                      </h2>
                    </div>
                    <div className="relative">
                      <button
                        type="button"
                        onClick={(e) => toggleMenu(String(agent.id), e)}
                        className="p-2 rounded-full text-neutral-500 hover:bg-neutral-100 transition-colors"
                      >
                        <IconDotsVertical size={18} />
                      </button>
                      {activeMenu === String(agent.id) && (
                        <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-neutral-200 z-10 overflow-hidden">
                          <button
                            type="button"
                            onClick={(e) => handleEdit(agent, e)}
                            className="flex items-center px-4 py-3 text-sm text-neutral-700 hover:bg-navy-50 w-full text-left transition-colors"
                          >
                            <IconPencil size={16} className="mr-2 text-navy-500" />
                            Edit Agent
                          </button>
                          <button
                            type="button"
                            onClick={(e) => handleDelete(agent, e)}
                            className="flex items-center px-4 py-3 text-sm text-red-600 hover:bg-red-50 w-full text-left transition-colors"
                          >
                            <IconTrash size={16} className="mr-2" />
                            Delete Agent
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-neutral-50 rounded-lg p-3 mb-4">
                    <p className="text-neutral-600 text-sm line-clamp-2">
                      {agent.system_prompt}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-navy-50 p-3 rounded-lg">
                      <span className="text-xs text-navy-500 font-medium block">Voice</span>
                      <span className="text-sm font-medium text-navy-800">
                        {agent.voice}
                      </span>
                    </div>
                    <div className="bg-navy-50 p-3 rounded-lg">
                      <span className="text-xs text-navy-500 font-medium block">Speed</span>
                      <span className="text-sm font-medium text-navy-800">
                        {agent.speed}x
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center text-neutral-500">
                      <IconInfoCircle size={14} className="mr-1" />
                      <span>Silence: {agent.min_silence}ms</span>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      agent.knowledge ? "bg-green-100 text-green-800" : "bg-neutral-100 text-neutral-800"
                    }`}>
                      {agent.knowledge ? "Knowledge Base" : "No Knowledge Base"}
                    </div>
                  </div>
                </div>
                <div className="border-t border-neutral-200 px-6 py-3 bg-gradient-to-r from-white to-neutral-50">
                  <button
                    type="button"
                    className="text-navy-600 hover:text-navy-800 text-sm font-medium inline-flex items-center"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/agents/${agent.id}`);
                    }}
                  >
                    View details
                    <IconArrowRight size={16} className="ml-1" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-xl border border-neutral-200 shadow-sm">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-navy-50 mb-6">
              <IconRobot size={40} className="text-navy-400" />
            </div>
            <h3 className="text-xl font-medium text-neutral-900 mb-2">No agents found</h3>
            <p className="text-neutral-500 mb-6 max-w-md mx-auto">
              Get started by creating your first AI agent to automate conversations with your customers
            </p>
            <button
              onClick={handleCreate}
              className="px-5 py-2.5 bg-navy-600 hover:bg-navy-700 text-white rounded-lg inline-flex items-center"
            >
              <IconPlus size={18} className="mr-1.5" />
              Create Your First Agent
            </button>
          </div>
        )}
      </main>

      {/* Modal */}
      {showModal && (
        <AgentModal
          mode={modalMode}
          agent={selectedAgent}
          onClose={() => setShowModal(false)}
          onSave={async (formData) => {
            try {
              if (modalMode === 'create') {
                await addAgent(formData);
              } else if (selectedAgent) {
                await updateAgent(selectedAgent.id, formData);
              }
              setShowModal(false);
            } catch (err) {
              console.error("Error saving agent:", err);
            }
          }}
        />
      )}
    </div>
  );
};

interface AgentModalProps {
  mode: 'create' | 'edit';
  agent: Agent | null;
  onClose: () => void;
  onSave: (formData: Omit<Agent, 'id' | 'user_id'>) => Promise<void>;
}

const AgentModal = ({ mode, agent, onClose, onSave }: AgentModalProps) => {
  const [formData, setFormData] = useState({
    name: agent?.name || '',
    voice: agent?.voice || 'af_heart',
    knowledge: agent?.knowledge || '',
    system_prompt: agent?.system_prompt || '',
    speed: agent?.speed || 1.0,
    min_silence: agent?.min_silence || 500
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    
    // Convert numeric values
    if (name === 'speed') {
      setFormData(prev => ({ ...prev, [name]: parseFloat(value) }));
    } else if (name === 'min_silence') {
      setFormData(prev => ({ ...prev, [name]: parseInt(value, 10) }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await onSave(formData);
    } catch (err) {
      console.error("Error in form submission:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 overflow-auto bg-neutral-900/30 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-xl max-w-md w-full"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-neutral-200 flex justify-between items-center">
          <h3 className="text-lg font-medium text-neutral-900">
            {mode === 'create' ? 'Create New Agent' : 'Edit Agent'}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-700"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-1">
                Agent Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
                required
              />
            </div>
            
            <div>
              <label htmlFor="system_prompt" className="block text-sm font-medium text-neutral-700 mb-1">
                System Prompt
              </label>
              <textarea
                id="system_prompt"
                name="system_prompt"
                value={formData.system_prompt}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
                required
              />
            </div>
            
            <div>
              <label htmlFor="voice" className="block text-sm font-medium text-neutral-700 mb-1">
                Voice
              </label>
              <select
                id="voice"
                name="voice"
                value={formData.voice}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
                required
              >
                <option value="af_heart">AF Heart</option>
                <option value="echo">Echo</option>
                <option value="alloy">Alloy</option>
                <option value="shimmer">Shimmer</option>
                <option value="nova">Nova</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="knowledge" className="block text-sm font-medium text-neutral-700 mb-1">
                Knowledge Base (Optional)
              </label>
              <textarea
                id="knowledge"
                name="knowledge"
                value={formData.knowledge || ''}
                onChange={handleChange}
                rows={2}
                className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="speed" className="block text-sm font-medium text-neutral-700 mb-1">
                  Speed
                </label>
                <input
                  type="number"
                  id="speed"
                  name="speed"
                  value={formData.speed}
                  onChange={handleChange}
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="min_silence" className="block text-sm font-medium text-neutral-700 mb-1">
                  Min Silence (ms)
                </label>
                <input
                  type="number"
                  id="min_silence"
                  name="min_silence"
                  value={formData.min_silence}
                  onChange={handleChange}
                  min="100"
                  max="2000"
                  step="100"
                  className="w-full px-4 py-2.5 border border-neutral-300 rounded-lg"
                  required
                />
              </div>
            </div>
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2.5 bg-navy-600 text-white rounded-lg hover:bg-navy-700"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : (mode === 'create' ? 'Create Agent' : 'Save Changes')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Dashboard;
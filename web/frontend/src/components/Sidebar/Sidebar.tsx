import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { IconHome2, IconSettings, IconMessage, IconUsers, IconLogout, IconChartBar } from '@tabler/icons-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  hidden?: boolean;
}

const navItems = [
  { icon: <IconHome2 size={20} />, label: 'Dashboard', path: '/' },
  { icon: <IconUsers size={20} />, label: 'Users', path: '/users' },
  { icon: <IconMessage size={20} />, label: 'Messages', path: '/messages' },
  { icon: <IconChartBar size={20} />, label: 'Analytics', path: '/analytics' },
  { icon: <IconSettings size={20} />, label: 'Settings', path: '/settings' },
];

const Sidebar: React.FC<SidebarProps> = ({ hidden = false }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  if (hidden) return null;

  return (
    <div className="h-screen w-64 bg-dark-900/80 backdrop-blur-xl border-r border-dark-700/50 flex flex-col">
      {/* Logo */}
      <div className="p-6">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500"></div>
          <h1 className="ml-3 text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-400 to-secondary-400">
            NexaUI
          </h1>
        </div>
      </div>
      
      {/* Navigation */}
      <div className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => (
          <button 
            key={item.label}
            className={`w-full sidebar-item relative ${isActive(item.path) ? 'sidebar-item-active' : ''}`}
            onClick={() => navigate(item.path)}
            onMouseEnter={() => setHoveredItem(item.label)}
            onMouseLeave={() => setHoveredItem(null)}
          >
            {/* Glow effect on hover */}
            {(hoveredItem === item.label || isActive(item.path)) && (
              <div className="absolute inset-0 bg-primary-500/10 rounded-lg -z-10"></div>
            )}
            
            <div className={`${isActive(item.path) ? 'text-primary-500' : 'text-dark-300'}`}>
              {item.icon}
            </div>
            <span className={`${isActive(item.path) ? 'font-medium' : ''}`}>{item.label}</span>
          </button>
        ))}
      </div>
      
      {/* User Profile */}
      <div className="p-4 border-t border-dark-700/50">
        <div className="flex items-center p-3">
          <div className="h-10 w-10 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500 flex items-center justify-center text-white font-medium">
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-white">{user?.name || 'User'}</p>
            <p className="text-xs text-dark-400">{user?.email || 'user@example.com'}</p>
          </div>
        </div>
        
        <button 
          className="w-full mt-3 sidebar-item text-red-400 hover:text-red-300 hover:bg-red-500/10"
          onClick={handleLogout}
        >
          <IconLogout size={20} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
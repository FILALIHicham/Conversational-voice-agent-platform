import { useState, useEffect } from 'react';
import { IconMenu2, IconX, IconSearch, IconBell } from '@tabler/icons-react';
import Sidebar from '../Sidebar/Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    
    return () => {
      clearInterval(timer);
    };
  }, []);

  const formattedDate = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }).format(currentTime);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar - desktop */}
      {!isMobile && <Sidebar />}
      
      {/* Sidebar - mobile */}
      {isMobile && sidebarOpen && (
        <div className="fixed inset-0 z-40">
          <div className="absolute inset-0 bg-dark-900/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)}></div>
          <div className="relative z-50 h-full w-64">
            <Sidebar />
          </div>
        </div>
      )}
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-dark-900/60 backdrop-blur-md border-b border-dark-700/50 h-16 flex items-center px-4 lg:px-6">
          <div className="flex-1 flex items-center">
            {isMobile && (
              <button 
                className="p-2 rounded-lg text-dark-300 hover:text-white hover:bg-dark-700/50 transition-colors"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? <IconX size={20} /> : <IconMenu2 size={20} />}
              </button>
            )}
            
            <div className="relative ml-4 flex-1 max-w-xs">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <IconSearch size={16} className="text-dark-400" />
              </div>
              <input 
                type="text" 
                placeholder="Search..." 
                className="w-full bg-dark-800/50 border border-dark-700/50 rounded-lg py-1.5 pl-10 pr-4 text-sm text-white placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500/50"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="hidden md:block text-right">
              <p className="text-sm text-dark-300">{formattedDate}</p>
            </div>
            
            <button className="relative p-2 rounded-lg text-dark-300 hover:text-white hover:bg-dark-700/50 transition-colors">
              <IconBell size={20} />
              <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-primary-500"></span>
            </button>
          </div>
        </header>
        
        {/* Main content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
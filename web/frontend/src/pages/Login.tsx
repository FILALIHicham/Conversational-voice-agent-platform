// src/pages/Login.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { IconMail, IconLock, IconUser, IconBrandGoogle, IconBrandGithub, IconRobot } from '@tabler/icons-react';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isAuthenticated, isLoading, error } = useAuth();
  const navigate = useNavigate();
  const [isPageLoaded, setIsPageLoaded] = useState(false);
  const [formInView, setFormInView] = useState(false);

  // Animation on initial load
  useEffect(() => {
    setIsPageLoaded(true);
    const timer = setTimeout(() => {
      setFormInView(true);
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  // Redirect if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(username, password);
      // Upon successful login, the useEffect above will handle redirection
    } catch (err) {
      // Error handled by auth context
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-navy-900 to-navy-800 p-4">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-navy-800/50 to-transparent"></div>
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-navy-500 opacity-10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-navy-500 opacity-10 rounded-full blur-3xl"></div>
        
        {/* Animated floating elements */}
        <div className="absolute top-1/4 right-1/4 w-6 h-6 rounded bg-navy-400/20 animate-float1"></div>
        <div className="absolute bottom-1/3 left-1/3 w-8 h-8 rounded bg-navy-400/20 animate-float2"></div>
        <div className="absolute top-2/3 right-1/3 w-4 h-4 rounded bg-navy-400/20 animate-float3"></div>
      </div>
      
      <div 
        className={`relative w-full max-w-md transition-all duration-700 transform ${
          isPageLoaded ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
        }`}
      >
        {/* Logo and title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-navy-500/20 backdrop-blur-sm border border-navy-500/30 mb-4 transition-all duration-700">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-navy-400 to-navy-600 flex items-center justify-center">
              <IconRobot size={18} className="text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome Back
          </h1>
          <p className="text-navy-200">
            Sign in to manage your agents
          </p>
        </div>
        
        {/* Login card */}
        <div 
          className={`bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 shadow-xl overflow-hidden transition-all duration-500 transform ${
            formInView ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
          }`}
        >
          <div className="p-8">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-navy-100 mb-1">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <IconUser size={18} className="text-navy-300" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="pl-10 w-full px-4 py-3 bg-navy-800/50 border border-navy-700 text-white rounded-lg focus:ring-2 focus:ring-navy-400 focus:border-navy-500 outline-none transition-all placeholder-navy-400"
                    placeholder="Enter your username"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-navy-100 mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <IconLock size={18} className="text-navy-300" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="pl-10 w-full px-4 py-3 bg-navy-800/50 border border-navy-700 text-white rounded-lg focus:ring-2 focus:ring-navy-400 focus:border-navy-500 outline-none transition-all placeholder-navy-400"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {error && (
                <div className="bg-red-400/10 border border-red-400/30 rounded-lg p-3 text-sm text-red-300 animate-shake">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-navy-500 to-navy-600 hover:from-navy-600 hover:to-navy-700 text-white font-medium rounded-lg transition-all duration-300 transform hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-navy-500 focus:ring-offset-navy-800"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </span>
                ) : (
                  'Sign In'
                )}
              </button>
              
              <div className="text-center">
                <a href="#" className="text-sm text-navy-300 hover:text-white transition-colors">
                  Forgot your password?
                </a>
              </div>
            </form>
          </div>
          
          <div className="px-8 py-4 bg-navy-800/50 border-t border-navy-700">
            <button
              type="button"
              onClick={() => navigate('/register')}
              className="w-full text-center text-navy-300 hover:text-white text-sm transition-colors"
            >
              Don't have an account? Sign up
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
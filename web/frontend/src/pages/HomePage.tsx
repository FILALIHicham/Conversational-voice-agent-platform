// src/pages/HomePage.tsx
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { IconChevronRight, IconRobot, IconUsers, IconShoppingCart, IconMessage, IconBrandTwitter, IconBrandInstagram, IconBrandLinkedin } from '@tabler/icons-react';

// Mock data for statistics (in a real app, these would come from an API)
const stats = {
  users: 5800,
  agents: 12500,
  completedOrders: 352000,
  conversations: 1250000
};

// Testimonials data
const testimonials = [
  {
    name: "Sarah Johnson",
    role: "E-commerce Manager",
    company: "StyleHub",
    content: "Our conversion rate increased by 35% after implementing these AI agents. They handle customer inquiries 24/7 and provide personalized recommendations that really drive sales.",
    avatar: "/api/placeholder/40/40"
  },
  {
    name: "Michael Chen",
    role: "Restaurant Owner",
    company: "Fusion Kitchen",
    content: "Taking orders used to be a huge bottleneck. Now our AI agent handles all incoming calls, accurately captures orders, and even suggests popular add-ons. It's like having another full-time staff member!",
    avatar: "/api/placeholder/40/40"
  },
  {
    name: "Rebecca Williams",
    role: "Customer Service Lead",
    company: "TechSupport Pro",
    content: "We've been able to scale our support operations while maintaining quality. Our agents handle tier-1 issues automatically, freeing up our human team to focus on complex cases.",
    avatar: "/api/placeholder/40/40"
  }
];

const HomePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [isVisible, setIsVisible] = useState(false);
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [countedStats, setCountedStats] = useState({
    users: 0,
    agents: 0,
    completedOrders: 0,
    conversations: 0
  });
  
  const statsRef = useRef<HTMLDivElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const featureRef = useRef<HTMLDivElement>(null);
  
  // Handle counting animation for stats
  useEffect(() => {
    setIsVisible(true);
    
    // Intersection Observer for stats section
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        // Start counting animation when stats section is visible
        const duration = 2000; // Duration in milliseconds
        const frameDuration = 1000 / 60; // 60fps
        const totalFrames = Math.round(duration / frameDuration);
        
        let frame = 0;
        const countUp = setInterval(() => {
          frame++;
          const progress = frame / totalFrames; // Progress from 0 to 1
          
          setCountedStats({
            users: Math.floor(stats.users * Math.min(progress, 1)),
            agents: Math.floor(stats.agents * Math.min(progress, 1)),
            completedOrders: Math.floor(stats.completedOrders * Math.min(progress, 1)),
            conversations: Math.floor(stats.conversations * Math.min(progress, 1))
          });
          
          if (frame === totalFrames) {
            clearInterval(countUp);
          }
        }, frameDuration);
        
        // Once animation starts, we don't need to observe anymore
        if (statsRef.current) {
          observer.unobserve(statsRef.current);
        }
      }
    }, { threshold: 0.3 });
    
    if (statsRef.current) {
      observer.observe(statsRef.current);
    }
    
    return () => {
      if (statsRef.current) {
        observer.unobserve(statsRef.current);
      }
    };
  }, []);
  
  // Rotate testimonials
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveTestimonial(current => (current + 1) % testimonials.length);
    }, 8000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/register');
    }
  };

  return (
    <div className="min-h-screen bg-white overflow-hidden">
      {/* Header for navigation */}
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
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 bg-navy-600 hover:bg-navy-700 text-white rounded-lg font-medium transition-all duration-300"
                >
                  Dashboard
                </button>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/login')}
                    className="px-4 py-2 border border-navy-200 hover:bg-navy-50 text-navy-700 rounded-lg font-medium transition-all duration-300"
                  >
                    Login
                  </button>
                  <button
                    onClick={() => navigate('/register')}
                    className="px-4 py-2 bg-navy-600 hover:bg-navy-700 text-white rounded-lg font-medium transition-all duration-300"
                  >
                    Register
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div
        ref={heroRef}
        className={`relative bg-gradient-to-r from-navy-800 to-navy-900 text-white transition-all duration-1000 ease-out ${
          isVisible ? 'opacity-100' : 'opacity-0 transform translate-y-10'
        }`}
      >
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 right-10 w-64 h-64 bg-navy-500 opacity-10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 left-10 w-96 h-96 bg-navy-500 opacity-10 rounded-full blur-3xl"></div>
          
          {/* Animated grid pattern */}
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.08) 1px, transparent 0)',
            backgroundSize: '40px 40px',
            zIndex: 0
          }}></div>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32 relative z-10">
          <div className="flex flex-col items-center text-center">
            <div className="space-y-8 max-w-3xl mx-auto">
              <div className="space-y-5">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-accent-300 to-white">AI Voice Agents</span>
                  <span className="block">For Your Business</span>
                </h1>
                <p className="text-lg md:text-xl text-navy-100 max-w-2xl mx-auto">
                  Create custom AI voice agents to handle customer calls, take orders, and provide information 24/7.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={handleGetStarted}
                  className="px-6 py-3 bg-accent-500 hover:bg-accent-600 text-white rounded-lg font-medium flex items-center justify-center transition-all duration-300 transform hover:translate-y-[-2px] hover:shadow-lg group"
                >
                  Create Your Agent
                  <IconChevronRight size={20} className="ml-2 transition-transform group-hover:translate-x-1" />
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="px-6 py-3 bg-transparent border border-white/30 hover:bg-white/10 text-white rounded-lg font-medium flex items-center justify-center transition-all duration-300"
                >
                  Sign In
                </button>
              </div>
              
            </div>
          </div>
        </div>
      </div>
      
      {/* Stats Section */}
      <div 
        ref={statsRef}
        className="py-16 bg-white"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-navy-900">How It Works</h2>
            <p className="mt-4 text-lg text-neutral-600 max-w-2xl mx-auto">
              Create and deploy your custom AI voice agent in minutes with three simple steps.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-16 left-1/2 w-full h-0.5 bg-navy-200"></div>
              
              <div className="relative z-10 flex flex-col items-center p-6">
                <div className="w-16 h-16 rounded-full bg-navy-600 text-white flex items-center justify-center text-xl font-bold mb-4">
                  1
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-3 text-center">Create Your Agent</h3>
                <p className="text-neutral-600 text-center">
                  Define your agent's voice, personality, and knowledge base using our intuitive interface.
                </p>
              </div>
            </div>
            
            <div className="relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-16 left-0 w-full h-0.5 bg-navy-200"></div>
              
              <div className="relative z-10 flex flex-col items-center p-6">
                <div className="w-16 h-16 rounded-full bg-navy-600 text-white flex items-center justify-center text-xl font-bold mb-4">
                  2
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-3 text-center">Customize & Train</h3>
                <p className="text-neutral-600 text-center">
                  Tailor responses, add product information, and train your agent on your specific business needs.
                </p>
              </div>
            </div>
            
            <div className="relative">
              <div className="relative z-10 flex flex-col items-center p-6">
                <div className="w-16 h-16 rounded-full bg-navy-600 text-white flex items-center justify-center text-xl font-bold mb-4">
                  3
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-3 text-center">Deploy & Scale</h3>
                <p className="text-neutral-600 text-center">
                  Connect your agent to your phone system, website, or app and start handling customer interactions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Features Section */}
        <div 
          ref={featureRef}
          className="py-20 bg-navy-50"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-navy-900">Everything You Need</h2>
              <p className="mt-4 text-lg text-neutral-600 max-w-2xl mx-auto">
                Create and deploy AI voice agents with powerful features and an intuitive interface.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M12 4C12.9889 4 13.9556 4.29324 14.7779 4.84265C15.6001 5.39206 16.241 6.17295 16.6194 7.08658C16.9978 8.00021 17.0969 9.00555 16.9039 9.97545C16.711 10.9454 16.2348 11.8363 15.5355 12.5355C14.8363 13.2348 13.9454 13.711 12.9755 13.9039C12.0055 14.0969 11.0002 13.9978 10.0866 13.6194C9.17295 13.241 8.39206 12.6001 7.84265 11.7779C7.29324 10.9556 7 9.98891 7 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M8.5 18.5L7 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M15.5 18.5L17 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M12 16V20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Natural Voice Interactions</h3>
                <p className="text-neutral-600">
                  Create agents with natural-sounding voices that understand context and provide human-like responses.
                </p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 10H4V20H8V10Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M14 4H10V20H14V4Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M20 14H16V20H20V14Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M4 20H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Advanced Analytics</h3>
                <p className="text-neutral-600">
                  Track performance metrics, conversation outcomes, and customer satisfaction to optimize your agents.
                </p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 7H4C2.89543 7 2 7.89543 2 9V19C2 20.1046 2.89543 21 4 21H20C21.1046 21 22 20.1046 22 19V9C22 7.89543 21.1046 7 20 7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M16 21V5C16 4.46957 15.7893 3.96086 15.4142 3.58579C15.0391 3.21071 14.5304 3 14 3H10C9.46957 3 8.96086 3.21071 8.58579 3.58579C8.21071 3.96086 8 4.46957 8 5V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Knowledge Base Integration</h3>
                <p className="text-neutral-600">
                  Equip your agents with custom knowledge bases to provide accurate information specific to your business.
                </p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 13C10 13.5304 10.2107 14.0391 10.5858 14.4142C10.9609 14.7893 11.4696 15 12 15C12.5304 15 13.0391 14.7893 13.4142 14.4142C13.7893 14.0391 14 13.5304 14 13C14 12.4696 13.7893 11.9609 13.4142 11.5858C13.0391 11.2107 12.5304 11 12 11C11.4696 11 10.9609 11.2107 10.5858 11.5858C10.2107 11.9609 10 12.4696 10 13Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M10.9 7.24998C10.9 7.24998 12.4 6.5 11.9 5C11.9 5 13.5 5.5 13.5 3.5C13.5 3.5 15 4.5 15.5 3.5C16 2.5 18 3 18 5C18 5.5 18.5 6.5 19.5 6.5C20.5 6.5 21 7.5 21 8.5C21 9.5 20.7 10 20 10.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M5.60001 11.5C5.00001 11 4.90001 10.5 4.90001 9.5C4.90001 8.5 5.30001 7.5 6.20001 7.5C7.10001 7.5 7.60001 6.5 7.60001 6C7.60001 4 9.50001 3.5 10.1 4.5C10.7 5.5 12.2 4.5 12.2 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M18.2 14C18.6 13.5 19.6 12.5 19.8 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M5.7 13.7C5.7 13.7 6.80001 15.3 7.20001 15.8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M14.5 19.5C14 19.5 13.3 19.6 12 19.6C10.7 19.6 10 19.5 9.5 19.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Customizable Personas</h3>
                <p className="text-neutral-600">
                  Design agents with distinct personalities, voices, and conversation styles to match your brand identity.
                </p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 15C15.866 15 19 11.866 19 8C19 4.13401 15.866 1 12 1C8.13401 1 5 4.13401 5 8C5 11.866 8.13401 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M8.21 13.89L7 23L12 20L17 23L15.79 13.88" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Order Processing</h3>
                <p className="text-neutral-600">
                  Handle product orders, reservations, and bookings with built-in order management and integration capabilities.
                </p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-soft border border-neutral-200 transform transition duration-500 hover:shadow-medium hover:-translate-y-1">
                <div className="w-12 h-12 bg-navy-100 text-navy-600 rounded-lg flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 11L12 14L22 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-navy-900 mb-2">Seamless Handoff</h3>
                <p className="text-neutral-600">
                  Automatically transfer complex conversations to human agents when needed, with complete context preservation.
                </p>
              </div>
            </div>
          </div>
        </div>
      {/* Testimonials Section */}
        <div className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-navy-900">What Our Users Say</h2>
              <p className="mt-4 text-lg text-neutral-600 max-w-2xl mx-auto">
                Discover how businesses are transforming their operations with our AI voice agents.
              </p>
            </div>
            
            <div className="relative overflow-hidden h-96 rounded-2xl shadow-lg border border-neutral-200">
              {testimonials.map((testimonial, index) => (
                <div 
                  key={index}
                  className={`absolute inset-0 transition-all duration-700 ease-in-out ${
                    index === activeTestimonial 
                      ? 'opacity-100 translate-x-0' 
                      : 'opacity-0 translate-x-full'
                  }`}
                >
                  <div className="h-full bg-gradient-to-r from-navy-700 to-navy-900 text-white p-8 flex flex-col justify-center">
                    <div className="absolute top-1/2 left-0 transform -translate-y-1/2 translate-x-[-50%] w-64 h-64 bg-accent-500 opacity-10 rounded-full blur-3xl"></div>
                    <div className="relative z-10 max-w-3xl mx-auto text-center">
                      <div className="text-5xl font-serif text-accent-300 mb-6">"</div>
                      <p className="text-xl italic mb-8">{testimonial.content}</p>
                      <div className="flex items-center justify-center">
                        <img 
                          src={testimonial.avatar} 
                          alt={testimonial.name} 
                          className="w-12 h-12 rounded-full border-2 border-accent-300"
                        />
                        <div className="ml-4 text-left">
                          <p className="font-semibold">{testimonial.name}</p>
                          <p className="text-sm text-navy-200">{testimonial.role}, {testimonial.company}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Testimonial pagination indicators */}
              <div className="absolute bottom-6 left-0 right-0 flex justify-center space-x-2">
                {testimonials.map((_, index) => (
                  <button 
                    key={index}
                    onClick={() => setActiveTestimonial(index)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      index === activeTestimonial 
                        ? 'bg-white w-6' 
                        : 'bg-white/50'
                    }`}
                    aria-label={`View testimonial ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      {/* CTA Section */}
      <div className="py-20 bg-gradient-to-r from-navy-800 to-navy-900 text-white relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent-500 opacity-10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-navy-500 opacity-10 rounded-full blur-3xl"></div>
        </div>
        
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Transform Your Business?</h2>
            <p className="text-lg text-navy-100 mb-8 max-w-2xl mx-auto">
              Join thousands of businesses already using our AI voice agents to enhance customer experience and boost efficiency.
            </p>
            <button
              onClick={handleGetStarted}
              className="px-8 py-4 bg-accent-500 hover:bg-accent-600 text-white rounded-lg font-medium text-lg transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg"
            >
              Create Your AI Agent Now
            </button>
            <p className="mt-4 text-navy-200">No credit card required to get started</p>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="bg-navy-900 text-navy-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-1">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-navy-600 to-navy-400 flex items-center justify-center mr-3">
                  <IconRobot size={20} className="text-white" />
                </div>
                <span className="text-xl font-bold text-white">
                  AgentHub
                </span>
              </div>
              <p className="mb-6">
                AI-powered voice agents for businesses of all sizes. Transform customer interactions and streamline operations.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-navy-300 hover:text-white transition-colors">
                  <IconBrandTwitter size={20} />
                </a>
                <a href="#" className="text-navy-300 hover:text-white transition-colors">
                  <IconBrandLinkedin size={20} />
                </a>
                <a href="#" className="text-navy-300 hover:text-white transition-colors">
                  <IconBrandInstagram size={20} />
                </a>
              </div>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Product</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Case Studies</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Documentation</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Company</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">About Us</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-white font-semibold mb-4">Legal</h3>
              <ul className="space-y-3">
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Terms of Service</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">Cookie Policy</a></li>
                <li><a href="#" className="text-navy-300 hover:text-white transition-colors">GDPR</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-navy-800 mt-12 pt-8 text-center text-sm">
            <p>© {new Date().getFullYear()} AgentHub. All rights reserved.</p>
          </div>
        </div>
      </footer>
      </div>
  );
};

export default HomePage;
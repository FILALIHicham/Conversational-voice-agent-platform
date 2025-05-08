/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          navy: {
            50: '#E7EAFF',
            100: '#C7D0F6',
            200: '#A5B3E9',
            300: '#8295DD',
            400: '#5F77D0',
            500: '#3D59C4',
            600: '#2D479D',
            700: '#1F3576',
            800: '#12234F',
            900: '#091228',
          },
          accent: {
            50: '#F2F8FD',
            100: '#E3F1FA',
            200: '#C7E3F5',
            300: '#A1D0EC',
            400: '#64B2DF',
            500: '#3996D2',
            600: '#2678B0',
            700: '#1A608D',
            800: '#134B71',
            900: '#0D395C',
          },
          neutral: {
            50: '#F8FAFC',
            100: '#F1F5F9',
            200: '#E2E8F0',
            300: '#CBD5E1',
            400: '#94A3B8',
            500: '#64748B',
            600: '#475569',
            700: '#334155',
            800: '#1E293B',
            900: '#0F172A',
          }
        },
        fontFamily: {
          sans: ['Inter', 'sans-serif'],
        },
        boxShadow: {
          'soft': '0 2px 15px rgba(30, 41, 59, 0.05)',
          'medium': '0 4px 20px rgba(30, 41, 59, 0.08)',
        },
      },
    },
    plugins: [],
  }
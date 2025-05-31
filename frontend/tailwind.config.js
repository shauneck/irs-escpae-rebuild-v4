/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0A192F',
          800: '#112240',
          700: '#1A365D',
          600: '#2A4365',
        },
        emerald: {
          500: '#10B981',
          600: '#059669',
        },
      },
    },
  },
  plugins: [],
};
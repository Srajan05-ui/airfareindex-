/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          navy: '#0F172A',
          blue: '#1E3A8A',
          gold: '#F59E0B',
          teal: '#0D9488',
          red: '#DC2626',
          green: '#16A34A',
          slate: '#334155'
        }
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Source Serif 4"', '"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', '"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        'bg-base': '#F3EBDC',
        'bg-sunken': '#EBE1CE',
        'bg-surface': '#FBF7EE',
        'border-default': '#D3C6AB',
        'border-strong': '#A89774',
        ink: {
          900: '#14110C',
          700: '#2E2820',
          500: '#4F4637',
        },
        brand: {
          DEFAULT: '#0B2A5B',
          hover: '#08204A',
          soft: '#E6EDF8',
        },
        accent: {
          DEFAULT: '#C2570C',
          hover: '#A34607',
          soft: '#F6D9B0',
        },
        success: {
          DEFAULT: '#14622B',
          hover: '#0F4D21',
          soft: '#D5EBD3',
        },
        warning: {
          DEFAULT: '#8A4B00',
          hover: '#703D00',
          soft: '#F8E2A8',
        },
        danger: {
          DEFAULT: '#A61B1B',
          hover: '#871414',
          soft: '#F5D2CC',
        },
        info: {
          DEFAULT: '#1E4A9E',
          hover: '#16387A',
          soft: '#D6E2F6',
        },
      },
      boxShadow: {
        'warm-sm': '0 1px 2px rgba(60, 45, 20, 0.06)',
        'warm': '0 1px 2px rgba(60, 45, 20, 0.08), 0 8px 24px rgba(60, 45, 20, 0.06)',
        'warm-md': '0 4px 12px rgba(60, 45, 20, 0.08), 0 12px 32px rgba(60, 45, 20, 0.08)',
        'warm-lg': '0 8px 24px rgba(60, 45, 20, 0.12), 0 20px 48px rgba(60, 45, 20, 0.1)',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dock: {
          bg: '#071827',
          surface: '#0D2233',
          card: '#102A3E',
          hover: '#16364E',
          border: '#1E3E58',
          text: '#E6F1F5',
          muted: '#78909C',
          primary: '#22D3EE',
          'primary-hover': '#06B6D4',
          secondary: '#159FB5',
          danger: '#F87171',
          warning: '#FBBF24',
          success: '#34D399',
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'ui-monospace',
          'monospace',
        ],
      },
    },
  },
  plugins: [],
}

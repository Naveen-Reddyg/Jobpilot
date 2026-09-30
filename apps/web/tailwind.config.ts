import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}', './lib/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        primary: '#147b4e',
        accent: '#C74B3C',
        surface: '#F4F7F4',
        text: '#182522',
        muted: '#63706B',
        border: '#D6DED8',
      },
      boxShadow: {
        soft: '0 12px 30px rgba(24, 37, 34, 0.08)',
      },
      fontFamily: {
        heading: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        body: ['IBM Plex Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;

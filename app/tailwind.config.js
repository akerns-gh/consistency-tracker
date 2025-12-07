/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'rgb(150, 200, 85)',
          dark: 'rgb(120, 160, 68)',
          light: 'rgb(180, 220, 102)',
        },
      },
    },
  },
  plugins: [],
}


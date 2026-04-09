/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#06131f",
        brass: "#c08a2e",
        lagoon: "#4ecdc4",
        paper: "#f8f5ef"
      },
      boxShadow: {
        soft: "0 20px 60px rgba(6, 19, 31, 0.24)"
      }
    },
  },
  plugins: [],
};


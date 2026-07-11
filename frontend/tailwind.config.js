/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Vazirmatn", "sans-serif"] },
      colors: {
        teal: {
          50: "#E1F5EE", 100: "#9FE1CB", 200: "#5DCAA5",
          400: "#1D9E75", 600: "#0F6E56", 800: "#085041", 900: "#04342C",
        },
        gold: { DEFAULT: "#B8972E", light: "#F5EDD5" },
      },
    },
  },
  plugins: [],
};

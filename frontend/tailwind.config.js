/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        vault: {
          900: "#090d16",
          800: "#111827",
          700: "#1f2937",
          600: "#374151",
          gold: "#f59e0b",
          emerald: "#10b981",
          crimson: "#ef4444",
        }
      }
    },
  },
  plugins: [],
};

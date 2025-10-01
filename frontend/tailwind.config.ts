import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'turkey-red': '#a81007',
        'oxford-blue': '#0d082d',
        'fulvous': '#dc8300',
        'cornsilk': '#f9edcc',
        'ghost-white': '#f8f4f9',
      },
    },
  },
  plugins: [],
};
export default config;
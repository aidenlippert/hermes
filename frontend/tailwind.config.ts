import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "#e5e7eb",
        input: "#f3f4f6",
        ring: "#3b82f6",
        background: "#ffffff",
        foreground: "#111827",
        primary: {
          DEFAULT: "#f20d33",
          foreground: "#ffffff",
        },
        "background-light": "#f8f5f6",
        "background-dark": "#181112",
        "text-light": "#E0E0E0",
        "text-dark": "#EAEAEA",
        "text-muted-dark": "#888888",
        "text-muted-light": "#6b7280",
        "surface-dark": "#1E1E1E",
        "surface-light": "#ffffff",
        "border-dark": "#333333",
        "border-light": "#e5e7eb",
        secondary: {
          DEFAULT: "#f3f4f6",
          foreground: "#111827",
        },
        muted: {
          DEFAULT: "#f9fafb",
          foreground: "#6b7280",
        },
        accent: {
          DEFAULT: "#eef2ff",
          foreground: "#3730a3",
          secondary: "#00F6FF"
        },
        node: {
          DEFAULT: "#EAEAEA",
          text: "#121212",
          header: "#D1D1D1",
        },
        "border-color": "rgba(255, 255, 255, 0.1)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
        mono: ["Roboto Mono", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

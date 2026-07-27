/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#002b5c",
        "primary-dark": "#001a35",
        "primary-light": "#003d82",
        "primary-fixed": "#e3f2fd",
        "primary-fixed-dim": "#bbdefb",
        surface: "#f8fafc",
        "surface-container": "#eceef0",
        "surface-container-low": "#f1f5f9",
        "surface-container-high": "#e2e8f0",
        "on-surface": "#0f172a",
        "on-surface-variant": "#45464d",
        "outline-variant": "#cbd5e1",
        secondary: "#475569",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        console: "#0b1c30",
      },
      fontFamily: {
        sans: ["Geist", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "monospace"],
      },
      boxShadow: {
        institutional: "2px 2px 0px 0px rgba(13, 71, 161, 0.08)",
        "institutional-lg": "4px 4px 0px 0px rgba(13, 71, 161, 0.12)",
      },
      maxWidth: {
        content: "1440px",
      },
    },
  },
  plugins: [],
};

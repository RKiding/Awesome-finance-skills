/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0d1117",
          secondary: "#161b22",
          tertiary: "#1c2128",
          border: "#30363d",
        },
        accent: {
          green: "#3fb950",
          red: "#f85149",
          blue: "#58a6ff",
          yellow: "#d29922",
          purple: "#bc8cff",
          cyan: "#39d353",
        },
        text: {
          primary: "#e6edf3",
          secondary: "#8b949e",
          muted: "#484f58",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};

import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#152722",
        paper: "#f7f4ee",
        surface: "#fffdf9",
        sand: "#ece6da",
        accent: "#a94728",
        moss: "#315b4f",
        muted: "#5d6965",
        line: "#dcd8cf",
        danger: "#a63f3b",
        warning: "#8b5b16",
        success: "#2f684f",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        serif: ["Iowan Old Style", "Palatino Linotype", "Book Antiqua", "Georgia", "serif"],
      },
      boxShadow: {
        soft: "0 16px 45px rgba(21, 39, 34, 0.08)",
        lift: "0 24px 65px rgba(21, 39, 34, 0.13)",
        admin: "0 10px 30px rgba(21, 39, 34, 0.07)",
      },
    },
  },
  plugins: [],
};

export default config;

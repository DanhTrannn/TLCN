import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13231f",
        paper: "#f4f1e8",
        accent: "#c95f36",
        moss: "#42665a"
      }
    }
  },
  plugins: []
};

export default config;


import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",        // src/を削除
    "./components/**/*.{js,ts,jsx,tsx,mdx}", // src/を削除
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",        // src/を削除
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

export default config
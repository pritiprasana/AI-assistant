/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#6366f1',
                secondary: '#fbbf24',
                dark: '#1a1a2e',
                'dark-lighter': '#2a2a3e',
                'dark-code': '#16161f',
            },
        },
    },
    plugins: [],
}

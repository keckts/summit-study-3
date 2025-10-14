/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './myapp/templates/myapp/**/*.html',       // all your Django templates
    './static/src/**/*.js',        // any JS using Tailwind classes
    './node_modules/flowbite/**/*.js', // Flowbite components
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('flowbite/plugin'),
  ],
}

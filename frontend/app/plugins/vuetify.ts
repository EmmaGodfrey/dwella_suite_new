import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

export default defineNuxtPlugin({
  name: 'vuetify',
  enforce: 'pre',
  setup(nuxtApp) {
    const vuetify = createVuetify({
      components,
      directives,
      ssr: false,
      theme: {
        defaultTheme: 'light',
        themes: {
          light: {
            colors: {
              primary: '#7366ff',
              secondary: '#f73164',
            },
          },
        },
      },
    })

    nuxtApp.vueApp.use(vuetify)
  }
})

import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const rootEnvPath = resolve(process.cwd(), '..', '.env');

if (existsSync(rootEnvPath)) {
  for (const rawLine of readFileSync(rootEnvPath, 'utf8').split(/\r?\n/)) {
    const line = rawLine.trim();

    if (!line || line.startsWith('#') || !line.includes('=')) {
      continue;
    }

    const [key, ...valueParts] = line.split('=');
    process.env[key] ??= valueParts.join('=').replace(/^["']|["']$/g, '');
  }
}

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  
  runtimeConfig: {
    public: {
      apiBaseUrl:
        process.env.NUXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
    },
  },
  
  vue: {
    compilerOptions: {
      isCustomElement: tag => ['clippath'].includes(tag),
    },
  },
  
  app: {
    head: {
      link: [
        {
          href: 'https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&amp;display=swap.',
          rel: 'stylesheet',
        },
        { href: 'https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&amp;display=swap', rel: 'stylesheet' },
        { href: 'https://fonts.googleapis.com/css2?family=Rubik:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,300;1,400;1,500;1,600;1,700;1,800;1,900&amp;display=swap', rel: 'stylesheet' },
      ],
    },
  },
  
  css: ['bootstrap/dist/css/bootstrap.min.css', '@/assets/scss/app.scss'],

  modules: ['@pinia/nuxt', '@nuxt/icon'],

  pinia: {
    storesDirs: ['./store/**', './custom-folder/store/**'],
  },

  plugins: [
    { src: '~/plugins/plugins.ts', ssr: false, mode: 'client' },
    '~/plugins/api.ts',
    { src: '~/plugins/vuetify.ts', ssr: false, mode: 'client' },
    '~/plugins/vue-query.ts',
    '~/plugins/toast.ts',
  ],
  
  build: {
    transpile: ['vuetify'],
  },

  compatibilityDate: '2025-03-04',
});

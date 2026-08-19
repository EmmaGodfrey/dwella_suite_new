// eslint.config.js
import vue from 'eslint-plugin-vue';
import nuxt from 'eslint-plugin-nuxt';
import tseslint from '@typescript-eslint/eslint-plugin';
import parserTs from '@typescript-eslint/parser';
import prettier from 'eslint-plugin-prettier';
import importPlugin from 'eslint-plugin-import';
import vueParser from 'vue-eslint-parser';
import globals from 'globals';
import eslintConfigPrettier from 'eslint-config-prettier';

const safeGlobals = {
  ...Object.fromEntries(Object.entries(globals.browser ?? {}).filter(([key]) => key.trim() === key)),
  ...Object.fromEntries(Object.entries(globals.node ?? {}).filter(([key]) => key.trim() === key)),
  ...Object.fromEntries(Object.entries(globals.es2021 ?? {}).filter(([key]) => key.trim() === key)),
};

export default [
  {
    ignores: ['node_modules/**', '.output/**', 'dist/**', 'build/**', '.nuxt/**'],
  },
  {
    files: ['**/*.ts', '**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: parserTs,
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: false },
        extraFileExtensions: ['.vue'],
      },
      globals: {
        ...safeGlobals,
        useRoute: 'readonly',
        useRouter: 'readonly',
        defineNuxtPlugin: 'readonly',
        defineNuxtRouteMiddleware: 'readonly',
        definePageMeta: 'readonly',
        useHead: 'readonly',
        useI18n: 'readonly',
        defineStore: 'readonly',
        storeToRefs: 'readonly',
      },
    },
    plugins: {
      vue,
      nuxt,
      '@typescript-eslint': tseslint,
      import: importPlugin,
      prettier,
    },
    settings: {
      'import/resolver': {
        typescript: {
          project: './tsconfig.json',
        },
        alias: {
          map: [
            ['~', './'],
            ['@', './'],
            ['#app', './.nuxt'],
            ['#imports', './.nuxt'],
            ['#components', './.nuxt/components'],
          ],
          extensions: ['.ts', '.js', '.vue', '.json'],
        },
      },
    },
    rules: {
      // ✅ Nuxt Recommended Rules
      ...nuxt.configs.recommended.rules,

      // ✅ Prettier
      'prettier/prettier': 'warn',
      quotes: ['warn', 'single'],
      semi: ['warn', 'always'],
      indent: 'off',

      // ✅ Vue
      'vue/html-indent': ['warn', 2],
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'off',
      'vue/require-default-prop': 'off',
      'vue/attribute-hyphenation': 'off',

      // ✅ TypeScript
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],

      // ✅ Imports
      'import/order': [
        'warn',
        {
          groups: ['builtin', 'external', 'internal', ['parent', 'sibling', 'index'], 'object', 'type'],
          pathGroups: [
            {
              pattern: 'vue',
              group: 'external',
              position: 'before',
            },
            {
              pattern: '@/**',
              group: 'internal',
            },
          ],
          pathGroupsExcludedImportTypes: [],
          'newlines-between': 'always',
          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
        },
      ],
      'import/no-unresolved': 'error',
      'import/no-duplicates': 'error',
      'import/first': 'error',
      'import/newline-after-import': ['warn', { count: 1 }],
    },
  },
  eslintConfigPrettier,
];

import { createI18n } from 'vue-i18n';

import لعربية from '~/locales/ae.json';
import Arabic from '~/locales/ar.json';
import 简体中文 from '~/locales/cn.json';
import Deutsch from '~/locales/de.json';
import English from '~/locales/en.json';
import Español from '~/locales/es.json';
import Français from '~/locales/fr.json';
import German from '~/locales/ge.json';
import Português from '~/locales/pt.json';
import Russian from '~/locales/ru.json';

export default defineNuxtPlugin(({ vueApp }) => {
  const i18n = createI18n({
    legacy: false,
    globalInjection: true,
    locale: '',
    messages: {
      English: English,
      German: German,
      Russian: Russian,
      Arabic: Arabic,
      Español: Español,
      Deutsch: Deutsch,
      Français: Français,
      Português: Português,
      简体中文: 简体中文,
      لعربية: لعربية,
    },
  });
  vueApp.use(i18n);
});

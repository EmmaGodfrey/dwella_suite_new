import { defineStore } from 'pinia';

import Layout from '~/data/layout.json';

import type { Color, AppConfig, LayoutOption, SidebarOption } from '~/types/layout';

export const uselayoutStore = defineStore('layout', () => {
  const layout = ref(Layout);
  const boxlayout = ref<boolean>(true);
  const sidebar = ref<string>('default');
  const primaryColor = ref<string>('#24695c');
  const secondaryColor = ref<string>('#f73164');

  function setLayout(val: LayoutOption) {
    if ((document.body.className == 'rtl' || document.body.className == 'dark-only' || document.body.className == 'light-only rtl') && val.class == 'dark-only') {
      document.body.className = val.class + ' rtl';
    } else if (val.class == 'light-only' && document.body.getAttribute('main-theme-layout') == 'rtl') {
      document.body.className = 'rtl';
    } else if (val.class == 'light-only' && document.body.getAttribute('main-theme-layout') == 'ltr') {
      document.body.className = 'ltr';
    } else if (val.class == 'light-only' && document.body.getAttribute('main-theme-layout') == 'box-layout') {
      document.body.className = 'box-layout';
    } else if (document.body.className == 'box-layout' || document.body.className == 'dark-only' || document.body.className == 'light-only box-layout' || document.body.className == 'light-only') {
      document.body.className = val.class + ' box-layout';
    } else {
      document.body.className = val.class;
    }
  }
  if (import.meta.client) {
    document.body.setAttribute('main-theme-layout', layout.value.settings.layout_type);
    document.getElementsByTagName('html')[0]?.setAttribute('dir', layout.value.settings.layout_type);

    var primarycolor: string = useCookie('primary_color').value || layout.value.color.primary_color;
    var secondarycolor: string = useCookie('secondary_color').value || layout.value.color.secondary_color;

    var layoutVersion = localStorage.getItem('layoutVersion') || layout.value.color.layout_version;

    if (primarycolor || secondarycolor) {
      addStyle(primarycolor, secondarycolor);
      if (layoutVersion) document.body.className = layoutVersion;
    }
  }
  function addStyle(primary: string, secondary: string) {
    document.documentElement.style.setProperty('--theme-default', primary);
    document.documentElement.style.setProperty('--theme-secondary', secondary);
  }
  function setLayoutType(layout: AppConfig, val: string) {
    document.body.classList.remove('rtl');
    document.body.classList.remove('ltr');
    document.body.classList.remove('boxed');
    document.documentElement.removeAttribute('dir');
    document.body.setAttribute('class', val);
    document.body.setAttribute('main-theme-layout', val);

    document.getElementsByTagName('html')[0]?.setAttribute('dir', val);
  }
  function setColorScheme(color: Color) {
    setColor(color);

    primarycolor = color.primary;
    secondarycolor = color.secondary;
    layout.value.color.layout_version = 'light';
    localStorage.setItem('layoutVersion', layout.value.color.layout_version);
  }
  function setColor(color: Color) {
    addStyle(color.primary, color.secondary);
    let primary = useCookie('primary_color');
    let secondary = useCookie('secondary_color');
    primary.value = color.primary;
    secondary.value = color.secondary;

    window.location.reload();
  }
  function setCustomizeSidebarType(val: SidebarOption) {
    sidebar.value = val.type;
    if (import.meta.client) {
      localStorage.setItem('SidebarType', val.type);
    }
  }
  return {
    layout,
    setLayout,
    primaryColor,
    secondaryColor,
    setColorScheme,
    setLayoutType,
    setCustomizeSidebarType,
    boxlayout,
    sidebar,
  };
});

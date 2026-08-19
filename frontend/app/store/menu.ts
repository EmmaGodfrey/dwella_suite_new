import { defineStore } from 'pinia';

import Menu from '~/data/menu.json';

import type { menuItems } from '~/types/menu';

interface searchdatas {
  icon?: string;
  path?: string;
  title?: string;
}
interface search {
  icon: string;
  path: string;
  title: string;
  bookmark: string;
}
interface MenuItem {
  active: boolean;
  children?: MenuItem[];
}
export const useMenuStore = defineStore('menu', () => {
  const data = ref<menuItems[]>(Menu?.data as menuItems[]);
  const togglesidebar = ref<boolean>(true);
  const activeoverlay = ref<boolean>(true);
  const customizer = ref<string>('');
  const searchData = ref<menuItems[]>([]);
  const searchDatas = ref<menuItems[]>([]);
  const searchOpen = ref<boolean>(false);
  const hideRightArrowRTL = ref<boolean>(false);
  const hideLeftArrowRTL = ref<boolean>(true);
  const hideRightArrow = ref<boolean>(true);
  const hideLeftArrow = ref<boolean>(true);
  const width = ref<number>(0);
  const height = ref<number>(0);
  const margin = ref<number>(0);
  const menuWidth = ref<number>(0);
  const searchKey = ref('');
  let perentName = ref<string | undefined>('');
  let subName = ref<string>('');
  let childName = ref<string | undefined>('');
  
  // Initialize sidebar state based on screen size
  function initializeSidebar() {
    if (import.meta.client) {
      if (screen.availWidth < 991) {
        togglesidebar.value = false;
      } else {
        togglesidebar.value = true;
      }
      
      window.addEventListener('resize', function () {
        if (screen.availWidth < 991) {
          togglesidebar.value = false;
        } else {
          togglesidebar.value = true;
        }
      });
    }
  }
  
  function setPerentActive(title: string) {
    perentName.value = title == perentName.value ? '' : title;
  }
  function setSubActive(title: string) {
    subName.value = title == subName.value ? '' : title;
  }
  function toggleSidebar() {
    togglesidebar.value = !togglesidebar.value;
    if (window.innerWidth < 991) {
      activeoverlay.value = true;
    } else {
      activeoverlay.value = false;
    }
    activeoverlay.value = false;
  }
  function searchTerm(term: string) {
    const items: menuItems[] = [];

    const searchval = term.toLowerCase();
    data.value.filter((menuItems: menuItems) => {
      if (menuItems.title) {
        if (menuItems.title.toLowerCase().includes(searchval) && menuItems.type === 'link') {
          items.push(menuItems);
        }
        if (!menuItems.children) return false;
        menuItems.children.filter(subItems => {
          if (subItems.title?.toLowerCase().includes(searchval) && subItems.type === 'link') {
            subItems.icon = menuItems.icon;
            items.push(subItems);
          }
          if (!subItems.children) return false;
          subItems.children.filter(suSubItems => {
            if (suSubItems.title?.toLowerCase().includes(searchval)) {
              suSubItems.icon = menuItems.icon;
              items.push(suSubItems);
            }
          });
        });
        searchData.value = items;
      }
    });
  }
  function searchTerms(term: string) {
    const items: menuItems[] = [];

    const searchval = term.toLowerCase();
    data.value.filter((menuItems: menuItems) => {
      if (menuItems.title) {
        if (menuItems.title.toLowerCase().includes(searchval) && menuItems.type === 'link') {
          items.push(menuItems);
        }
        if (!menuItems.children) return false;
        menuItems.children.filter(subItems => {
          if (subItems.title?.toLowerCase().includes(searchval) && subItems.type === 'link') {
            subItems.icon = menuItems.icon;
            items.push(subItems);
          }
          if (!subItems.children) return false;
          subItems.children.filter(suSubItems => {
            if (suSubItems.title?.toLowerCase().includes(searchval)) {
              suSubItems.icon = menuItems.icon;
              items.push(suSubItems);
            }
          });
        });
        searchDatas.value = items;
      }
    });
  }
  function setNavActive(item: menuItems) {
    if (!item.active) {
      data.value.forEach(a => {
        if (data.value.includes(item)) a.active = false;
        if (!a.children) return false;
        a.children.forEach(b => {
          if (a.children?.includes(item)) {
            b.active = false;
          }
        });
      });
    }
    item.active = !item.active;
  }
  
  // Initialize active menu based on current route
  function initializeActiveMenu(currentPath: string) {
    data.value.filter((menuItem: menuItems) => {
      if (menuItem.path) {
        if (menuItem.path == currentPath) {
          perentName.value = menuItem.title;
        }
      } else {
        if (menuItem.children) {
          menuItem.children?.filter(subItem => {
            if (subItem.path) {
              if (subItem.path == currentPath) {
                perentName.value = menuItem.title;
                childName.value = subItem.title;
              }
            }

            if (subItem.children) {
              subItem.children?.filter(childItem => {
                if (childItem.path) {
                  if (childItem.path == currentPath) {
                    perentName.value = menuItem.title;
                    childName.value = childItem.title;
                  }
                }
              });
            }
          });
        }
      }
    });
  }
  
  function setActiveRoute(item: MenuItem) {}
  return {
    data,
    perentName,
    subName,
    setPerentActive,
    togglesidebar,
    setSubActive,
    activeoverlay,
    toggleSidebar,
    customizer,
    setNavActive,
    searchData,
    searchDatas,
    searchTerm,
    searchTerms,
    searchOpen,
    setActiveRoute,
    hideRightArrowRTL,
    hideLeftArrowRTL,
    hideRightArrow,
    hideLeftArrow,
    width,
    height,
    margin,
    menuWidth,
    initializeSidebar,
    initializeActiveMenu,
  };
});

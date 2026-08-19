import { defineStore } from 'pinia';

import Products from '~/data/products.json';
import type { product } from '~/types/products';

interface box {
  for: string;
  title: string;
}

type AnyObj = Record<string, unknown>;
export const useProductsStore = defineStore('products', () => {
  const block = ref<box[]>(Products.block);
  const products = ref<product[]>(Products.data);
  const col2 = ref<boolean>(false);
  const col3 = ref<boolean>(false);
  const col4 = ref<boolean>(true);
  const col6 = ref<boolean>(false);
  const listViewEnable = ref<boolean>(false);
  const list = ref<boolean>(false);
  const cartItems = ref<product[]>([]);
  const cart = ref(cartItems);

  const tagItems = ref<string[]>([]);
  const filteredProduct = ref(products);

  function grid2(item: boolean) {
    col2.value = item;
    col3.value = false;
    col4.value = false;
    col6.value = false;
    listViewEnable.value = false;
  }

  function grid3() {
    col2.value = false;
    col3.value = true;
    col4.value = false;
    col6.value = false;
    listViewEnable.value = false;
  }
  function grid4() {
    col2.value = false;
    col3.value = false;
    col4.value = true;
    col6.value = false;
    listViewEnable.value = false;
  }
  function grid6() {
    col2.value = false;
    col3.value = false;
    col4.value = false;
    col6.value = true;
    listViewEnable.value = false;
  }
  function listView() {
    listViewEnable.value = true;
    list.value = true;
    col2.value = false;
    col3.value = false;
    col4.value = false;
    col6.value = false;
  }
  function gridView() {
    listViewEnable.value = false;
    col4.value = true;
  }
  const filterProducts = computed(() => {
    return filteredProduct.value.filter(product => {
      if (!tagItems.value.length) return true;
      const Tags = tagItems.value.some(prev => {
        if (product.tags) {
          if (product.tags.includes(prev)) {
            return prev;
          }
        }
      });

      return Tags;
    });
  });
  function addToCart(product: product) {
    const hasItems = cart.value.find((items: product) => {
      if (items.sku === product.sku) {
        items.quantity = items.quantity ? items.quantity : 1;
        return true;
      }
      return false;
    });
    if (!hasItems) {
      cart.value.push(product);
    }

    let carts = useCookie('cartItem');
    carts.value = JSON.stringify(cart.value);
  }
  function updateCartQuantity(product: product) {
    cartItems.value.find((item: product, index: number) => {
      if (item.sku == product.sku && cartItems.value[index]) {
        cartItems.value[index].quantity = product.quantity;
      }
      localStorage.setItem('cartItem', JSON.stringify(cartItems.value));
    });
  }
  function setTags(item: string[]) {
    tagItems.value = item;
  }
  const getColors = computed(() => {
    const uniqueColors: string[] = [];
    const itemColor = [];
    products.value.map(product => {
      if (product.colors) {
        product.colors.map(color => {
          const index = uniqueColors.indexOf(color);
          if (index === -1) uniqueColors.push(color);
        });
      }
    });
    for (let i = 0; i < uniqueColors.length; i++) {
      itemColor.push({ color: uniqueColors[i] });
    }
    return itemColor;
  });
  const getBrands = computed(() => {
    const brands = [...new Set(products.value.map(product => product.brand))];
    return brands;
  });

  const getTotalAmount = computed(() => {
    return cart.value.reduce((prev: number, curr: AnyObj) => {
      return prev + (curr.price as number) * (curr.quantity as number);
    }, 0);
  });

  const getCategory = computed(() => {
    const uniqueCategory: string[] = [];
    const itemCat = [];
    products.value.map(product => {
      if (product.category) {
        product.category.map(category => {
          const index = uniqueCategory.indexOf(category);
          if (index === -1) uniqueCategory.push(category);
        });
      }
    });
    for (let i = 0; i < uniqueCategory.length; i++) {
      itemCat.push({ category: uniqueCategory[i] });
    }
    return itemCat;
  });
  function intialUpload(items: product[]) {
    cart.value = items;
  }
  function removeProduct(item: product) {
    const index = cart.value.indexOf(item);
    cart.value.splice(index, 1);
    if (import.meta.client) {
      let carts = useCookie('cartItem');
      carts.value = JSON.stringify(cart.value);
    }
  }
  function sortProducts(item: string) {
    if (item === 'Featured') {
      filteredProduct.value.sort(function (a, b) {
        if (a.name < b.name) {
          return -1;
        } else if (a.name > b.name) {
          return 1;
        }
        return 0;
      });
    } else if (item === 'z-a') {
      filteredProduct.value.sort(function (a, b) {
        if (a.name > b.name) {
          return -1;
        } else if (a.name < b.name) {
          return 1;
        }
        return 0;
      });
    } else if (item === 'Lowest') {
      filteredProduct.value.sort(function (a, b) {
        if (a.price < b.price) {
          return -1;
        } else if (a.price > b.price) {
          return 1;
        }
        return 0;
      });
    } else if (item === 'Highest') {
      filteredProduct.value.sort(function (a, b) {
        if (a.price > b.price) {
          return -1;
        } else if (a.price < b.price) {
          return 1;
        }
        return 0;
      });
    }
  }

  return {
    products,
    col2,
    col3,
    col4,
    col6,
    listViewEnable,
    list,
    grid2,
    grid3,
    grid4,
    grid6,
    listView,
    gridView,
    filterProducts,
    setTags,
    getBrands,
    addToCart,
    updateCartQuantity,
    getTotalAmount,
    cart,
    getCategory,
    removeProduct,
    sortProducts,
    getColors,
    intialUpload,
    block,
  };
});

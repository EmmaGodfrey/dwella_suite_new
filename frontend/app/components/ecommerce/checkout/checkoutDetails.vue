<template>
  <div class="col-xl-6 col-sm-12">
    <div class="checkout-details">
      <div class="order-box">
        <div class="title-box">
          <div class="checkbox-title">
            <h4 class="mb-0">Product</h4>
            <span>Total</span>
          </div>
        </div>
        <ul class="qty" v-if="cart.length">
          <li v-for="(item, index) in cart" :key="index">
            {{ item.name }} × {{ item.quantity }}
            <span>${{ item.price * item.quantity }}</span>
          </li>
        </ul>
        <ul class="qty" v-if="!cart.length">
          <li v-if="!cart.length">There are no products in cart</li>
        </ul>
        <ul class="sub-total">
          <li>
            Subtotal <span class="count">${{ getAmount() }}</span>
          </li>
          <li class="shipping-class">
            Shipping
            <div class="shopping-checkout-option">
              <label class="d-block" for="chk-ani"> <input class="checkbox_animated" id="chk-ani" type="checkbox" checked />Option 2 </label>
              <label class="d-block" for="chk-ani1"> <input class="checkbox_animated" id="chk-ani1" type="checkbox" />Option 3 </label>
            </div>
          </li>
        </ul>
        <ul class="sub-total total">
          <li>
            Total <span class="count">${{ getAmount() }}</span>
          </li>
        </ul>
        <div class="animate-chk" v-if="cart.length">
          <div class="row">
            <div class="col">
              <label> <input class="radio_animated" id="edo-ani" v-model="payment" :value="false" type="radio" name="rdo-ani" checked data-original-title title="" />Stripe </label>
              <label class="d-block" for="edo-ani2">
                <input class="radio_animated" id="edo-ani2" v-model="payment" type="radio" :value="true" name="rdo-ani" data-original-title="" title="" />PayPal
                <img class="img-paypal" src="/images/checkout/paypal.png" />
              </label>
            </div>
          </div>
        </div>
        <div class="order-place" v-if="cart.length && !payment"><a class="btn btn-primary" @click="payWithStripe()">Place Order </a></div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

const store = useProductsStore();
const { cart, getTotalAmount } = storeToRefs(store);
const totalAmount = ref();
const payment = ref<boolean>(false);

function getAmount() {
  return (totalAmount.value = getTotalAmount.value);
}
function payWithStripe() {
  payment.value = false;
}
</script>

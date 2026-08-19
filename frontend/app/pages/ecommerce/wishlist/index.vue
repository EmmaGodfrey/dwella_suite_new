<template>
  <TheBreadcrumbs main="Ecommerce" title="Wishlist" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-12">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Wishlist</h5>
          </div>
          <div class="card-body whishlist-main">
            <div class="row">
              <EcommerceWhishlistWishList />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Wish List | Cion - Premium Nuxt Admin Template',
});
</script>

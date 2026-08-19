<template>
  <TheBreadcrumbs main="Ecommerce" title="Invoice" />
  <div class="container-fluid">
    <div class="container invoice">
      <div class="row">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body">
              <div>
                <EcommerceInvoiceHeader />
                <EcommerceInvoiceProfile />
                <EcommerceInvoiceTable />
              </div>
              <div class="col-sm-12 text-center mt-3">
                <button class="btn btn btn-primary me-2" type="button" @click="printWindow()">Print</button>
                <button class="btn btn-secondary" type="button">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Invoice  | Cion - Premium Nuxt Admin Template',
});
function printWindow() {
  window.print();
}
</script>

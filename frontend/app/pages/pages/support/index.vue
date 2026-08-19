<template>
  <TheBreadcrumbs main="Apps" title="Support Ticket" />
  <div class="container-fluid support-ticket">
    <div class="row">
      <div class="col-sm-12">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Ticket List</h5>
            <span>List of ticket opend by customers</span>
          </div>
          <div class="card-body">
            <SupportTicket />
            <SupportTable />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Support | Cion - Premium Vue Admin Template',
});
</script>

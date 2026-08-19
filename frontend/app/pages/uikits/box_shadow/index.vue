<template>
  <TheBreadcrumbs main="UI Kits" title="box shadow" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-sm-12">
        <div class="card box-shadow-title">
          <div class="card-header pb-0">
            <h5>Examples</h5>
            <span
              >While shadows on components are disabled by default in Bootstrap and can be enabled via <code>$enable-shadows</code>, you can also quickly add or remove a shadow with our
              <code>box-shadow</code> utility classes. Includes support for <code>.shadow-none</code> and three default sizes (which have associated variables to match).</span
            >
          </div>
          <div class="card-body row">
            <UikitsShadowExamples />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Uikits Shadow | Cion - Premium Nuxt Admin Template',
});
</script>

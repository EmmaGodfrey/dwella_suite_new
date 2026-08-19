<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Basic Examples</h5>
        <span>Different Types Of Events Popover</span>
      </div>
      <div class="card-body btn-showcase">
        <client-only>
          <Popper placement="right" arrow>
            <button class="btn btn-primary example-popover">Click to toggle popover</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <h3 class="popover-header">Popover title</h3>
                <div class="popover-body">And here's some amazing content. It's very engaging. Right?</div>
              </div>
            </template>
          </Popper>
          <Popper arrow placement="right">
            <button class="btn btn-primary example-popover">Dismissible popover</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <h3 class="popover-header">Popover title</h3>
                <div class="popover-body">And here's some amazing content. It's very engaging. Right?</div>
              </div>
            </template>
          </Popper>
          <Popper arrow hover placement="bottom">
            <button class="btn btn-primary example-popover">On Hover Tooltip</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <h3 class="popover-header">Popover title</h3>
                <div class="popover-body">Vivamus sagittis lacus vel augue laoreet rutrum faucibus.</div>
              </div>
            </template>
          </Popper>
        </client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import Popper from 'vue3-popper';
</script>

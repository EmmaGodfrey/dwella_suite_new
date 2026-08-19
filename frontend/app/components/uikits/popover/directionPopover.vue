<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Direction</h5>
        <span>Popover With Directions.</span>
      </div>
      <div class="card-body btn-showcase">
        <client-only>
          <Popper class="pop" arrow placement="top">
            <button class="btn btn-primary example-popover">Popover on top</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <h3 class="popover-header">Popover title</h3>
                <div class="popover-body">Vivamus sagittis lacus vel augue laoreet rutrum faucibus.</div>
              </div>
            </template>
          </Popper>
          <Popper arrow placement="right">
            <button class="btn btn-primary example-popover">Popover on right</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <div class="popover-body">Vivamus sagittis lacus vel augue laoreet rutrum faucibus.</div>
              </div>
            </template>
          </Popper>
          <Popper arrow placement="bottom">
            <button class="btn btn-primary example-popover">Popover on bottom</button>
            <template #content>
              <div class="popover bs-popover-auto">
                <div class="popover-body">Vivamus sagittis lacus vel augue laoreet rutrum faucibus.</div>
              </div>
            </template>
          </Popper>
          <Popper arrow placement="left">
            <button class="btn btn-primary example-popover">Popover on left</button>
            <template #content>
              <div class="popover bs-popover-auto">
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

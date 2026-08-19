<template>
  <div class="col-sm-12 listing">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Listing Typography</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">Unorder list</h6>
            <ul>
              <li v-for="i in 10" :key="i">{{ Lorem }}</li>
            </ul>
          </div>
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">Order list</h6>
            <ol>
              <li>{{ Lorem }}</li>
              <li>{{ Lorem }}</li>
              <li>{{ Lorem }}</li>
              <li>
                <ol>
                  <li>{{ Lorem }}</li>
                  <li>{{ Lorem }}</li>
                  <li>{{ Lorem }}</li>
                  <li>{{ Lorem }}</li>
                  <li>{{ Lorem }}</li>
                </ol>
              </li>
              <li>{{ Lorem }}</li>
              <li>{{ Lorem }}</li>
            </ol>
          </div>
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">Order list</h6>
            <dl>
              <dt>{{ Lorem }}</dt>
              <dd>- ipsum dolor sit amet</dd>
              <dt>{{ Lorem }}</dt>
              <dd>- ipsum dolor sit amet</dd>
              <dt>{{ Lorem }}</dt>
              <dd>- ipsum dolor sit amet</dd>
              <dt>{{ Lorem }}</dt>
              <dd>- ipsum dolor sit amet</dd>
              <dt>{{ Lorem }}</dt>
              <dd>- ipsum dolor sit amet</dd>
            </dl>
          </div>
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">Fontawesome list</h6>
            <ul>
              <li v-for="i in 8" :key="i"><i class="fa fa-angle-double-right txt-primary m-r-10"></i>{{ Lorem }}</li>
            </ul>
          </div>
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">ICO Icon list</h6>
            <ul>
              <li v-for="i in 8" :key="i"><i class="fa fa-caret-right txt-secondary m-r-10"></i>{{ Lorem }}</li>
            </ul>
          </div>
          <div class="col-sm-12 col-xl-4">
            <h6 class="sub-title">Themfy list</h6>
            <ul>
              <li v-for="i in 8" :key="i"><i class="icofont icofont-ui-rate-add txt-success m-r-10"></i>{{ Lorem }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const Lorem = ref<string>('Lorem ipsum dolor sit amet');
</script>

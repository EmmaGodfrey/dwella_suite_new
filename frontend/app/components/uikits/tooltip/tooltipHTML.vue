<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>HTML elements</h5>
      </div>
      <div class="card-body btn-showcase">
        <button
          class="btn btn-primary"
          v-tooltip.top="{
            content: '<em>Tooltip</em> <u>with</u> <b>HTML</b>',
            theme: 'dropdown',
            html: true,
          }"
        >
          Click me
        </button>
        <button
          class="btn btn-primary"
          v-tooltip.right="{
            content: '<em>Tooltip</em> <u>with</u> <b>HTML</b>',
            theme: 'dropdown',
            html: true,
          }"
        >
          Click me
        </button>
        <button
          class="btn btn-primary"
          v-tooltip.bottom="{
            content: '<em>Tooltip</em> <u>with</u> <b>HTML</b>',
            theme: 'dropdown',
            html: true,
          }"
        >
          Click me
        </button>
        <button
          class="btn btn-primary"
          v-tooltip.left="{
            content: '<em>Tooltip</em> <u>with</u> <b>HTML</b>',
            theme: 'dropdown',
            html: true,
          }"
        >
          Click me
        </button>
      </div>
    </div>
  </div>
</template>

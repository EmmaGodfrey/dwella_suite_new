<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Single File Upload</h5>
      </div>
      <div class="card-body">
        <client-only> <DropZone :maxFileSize="Number(60000000)" url="http://localhost:3000" :uploadOnDrop="true" :maxFiles="1"> </DropZone></client-only>
      </div>
    </div>
  </div>
</template>

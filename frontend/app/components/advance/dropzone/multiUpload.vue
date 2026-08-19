<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Multi File Upload</h5>
      </div>
      <div class="card-body">
        <client-only> <DropZone :maxFileSize="Number(7000000)" url="http://localhost:3000" :uploadOnDrop="true" :multipleUpload="true" :parallelUpload="2" /></client-only>
      </div>
    </div>
  </div>
</template>

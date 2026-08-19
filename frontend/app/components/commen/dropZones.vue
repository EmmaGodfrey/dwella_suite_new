<template>
  <form class="dropzone digits" id="singleFileUpload" action="/upload.php">
    <div class="m-0 dz-message needsclick">
      <client-only>
        <DropZone :maxFileSize="Number(60000000)" url="http://localhost:3000" :uploadOnDrop="true" :maxFiles="1"> </DropZone>
      </client-only>
    </div>
  </form>
</template>

<template>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Material color tab</h5>
        <span>Add <code>.nav-primary</code> class with nav class</span>
      </div>
      <div class="card-body">
        <ul class="nav nav-tabs border-tab nav-primary" id="info-tab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="info-home-tab" data-bs-toggle="tab" href="#info-home" role="tab" aria-controls="info-home" aria-selected="true"
              ><i class="icofont icofont-ui-home"></i>Home</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="profile-info-tab" data-bs-toggle="tab" href="#info-profile" role="tab" aria-controls="info-profile" aria-selected="false"
              ><i class="icofont icofont-man-in-glasses"></i>Profile</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="contact-info-tab" data-bs-toggle="tab" href="#info-contact" role="tab" aria-controls="info-contact" aria-selected="false"
              ><i class="icofont icofont-contacts"></i>Contact</a
            >
          </li>
        </ul>
        <div class="tab-content" id="info-tabContent">
          <div class="tab-pane fade show active" id="info-home" role="tabpanel" aria-labelledby="info-home-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="info-profile" role="tabpanel" aria-labelledby="profile-info-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="info-contact" role="tabpanel" aria-labelledby="contact-info-tab">
            <p>{{ desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Material color tab</h5>
        <span>Add <code>.nav-secondary</code> class with nav class</span>
      </div>
      <div class="card-body">
        <ul class="nav nav-tabs border-tab nav-secondary nav-left" id="danger-tab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="danger-home-tab" data-bs-toggle="tab" href="#danger-home" role="tab" aria-controls="danger-home" aria-selected="true"
              ><i class="icofont icofont-ui-home"></i>Home</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="profile-danger-tab" data-bs-toggle="tab" href="#danger-profile" role="tab" aria-controls="danger-profile" aria-selected="false"
              ><i class="icofont icofont-man-in-glasses"></i>Profile</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="contact-danger-tab" data-bs-toggle="tab" href="#danger-contact" role="tab" aria-controls="danger-contact" aria-selected="false"
              ><i class="icofont icofont-contacts"></i>Contact</a
            >
          </li>
        </ul>
        <div class="tab-content" id="danger-tabContent">
          <div class="tab-pane fade show active" id="danger-home" role="tabpanel" aria-labelledby="danger-home-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="danger-profile" role="tabpanel" aria-labelledby="profile-danger-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="danger-contact" role="tabpanel" aria-labelledby="contact-danger-tab">
            <p>{{ desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const desc = ref<string>(
  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
);
</script>

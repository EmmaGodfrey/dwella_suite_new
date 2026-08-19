<template>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Simple Material style tab</h5>
        <span>Add <code>.border-tab</code> class with nav class</span>
      </div>
      <div class="card-body">
        <ul class="nav nav-tabs border-tab" id="top-tab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="top-home-tab" data-bs-toggle="tab" href="#top-home" role="tab" aria-controls="top-home" aria-selected="true"><i class="icofont icofont-ui-home"></i>Home</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" id="profile-top-tab" data-bs-toggle="tab" href="#top-profile" role="tab" aria-controls="top-profile" aria-selected="false"
              ><i class="icofont icofont-man-in-glasses"></i>Profile</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="contact-top-tab" data-bs-toggle="tab" href="#top-contact" role="tab" aria-controls="top-contact" aria-selected="false"
              ><i class="icofont icofont-contacts"></i>Contact</a
            >
          </li>
        </ul>
        <div class="tab-content" id="top-tabContent">
          <div class="tab-pane fade show active" id="top-home" role="tabpanel" aria-labelledby="top-home-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="top-profile" role="tabpanel" aria-labelledby="profile-top-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="top-contact" role="tabpanel" aria-labelledby="contact-top-tab">
            <p>{{ desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Material style bottom tab</h5>
        <span>Add <code>.border-tab</code> class with nav class</span>
      </div>
      <div class="card-body">
        <div class="tab-content" id="bottom-tabContent">
          <div class="tab-pane fade show active" id="bottom-home" role="tabpanel" aria-labelledby="bottom-home-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="bottom-profile" role="tabpanel" aria-labelledby="profile-bottom-tab">
            <p>{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="bottom-contact" role="tabpanel" aria-labelledby="contact-bottom-tab">
            <p>{{ desc }}</p>
          </div>
        </div>
        <ul class="nav nav-tabs border-tab" id="bottom-tab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="bottom-home-tab" data-bs-toggle="tab" href="#bottom-home" role="tab" aria-controls="bottom-home" aria-selected="true"
              ><i class="icofont icofont-ui-home"></i>Home</a
            >
            <div class="material-border"></div>
          </li>
          <li class="nav-item">
            <a class="nav-link" id="profile-bottom-tab" data-bs-toggle="tab" href="#bottom-profile" role="tab" aria-controls="bottom-profile" aria-selected="false"
              ><i class="icofont icofont-man-in-glasses"></i>Profile</a
            >
            <div class="material-border"></div>
          </li>
          <li class="nav-item">
            <a class="nav-link" id="contact-bottom-tab" data-bs-toggle="tab" href="#bottom-contact" role="tab" aria-controls="bottom-contact" aria-selected="false"
              ><i class="icofont icofont-contacts"></i>Contact</a
            >
          </li>
        </ul>
      </div>
    </div>
  </div>
  <UikitsTabsLineMaterialClass />
</template>
<script lang="ts" setup>
const desc = ref<string>(
  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
);
</script>

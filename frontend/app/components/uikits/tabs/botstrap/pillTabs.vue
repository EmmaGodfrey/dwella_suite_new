<template>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Pill Tabs</h5>
      </div>
      <div class="card-body">
        <ul class="nav nav-pills nav-primary" id="pills-tab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="pills-home-tab" data-bs-toggle="pill" href="#pills-home" role="tab" aria-controls="pills-home" aria-selected="true"
              >Home
              <div class="d-flex"></div>
            </a>
          </li>
          <li class="nav-item"><a class="nav-link" id="pills-profile-tab" data-bs-toggle="pill" href="#pills-profile" role="tab" aria-controls="pills-profile" aria-selected="false">Profile</a></li>
          <li class="nav-item"><a class="nav-link" id="pills-contact-tab" data-bs-toggle="pill" href="#pills-contact" role="tab" aria-controls="pills-contact" aria-selected="false">Contact</a></li>
        </ul>
        <div class="tab-content" id="pills-tabContent">
          <div class="tab-pane fade show active" id="pills-home" role="tabpanel" aria-labelledby="pills-home-tab">
            <p class="mb-0 m-t-30">
              Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a
              galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It
              was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages
            </p>
          </div>
          <div class="tab-pane fade" id="pills-profile" role="tabpanel" aria-labelledby="pills-profile-tab">
            <p class="mb-0 m-t-30">{{ desc }}</p>
          </div>
          <div class="tab-pane fade" id="pills-contact" role="tabpanel" aria-labelledby="pills-contact-tab">
            <p class="mb-0 m-t-30">{{ desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6 xl-50">
    <div class="card height-equal">
      <div class="card-header pb-0">
        <h5>Pill Tabs With Icon</h5>
      </div>
      <div class="card-body">
        <ul class="nav nav-pills nav-primary" id="pills-icontab" role="tablist">
          <li class="nav-item">
            <a class="nav-link active" id="pills-iconhome-tab" data-bs-toggle="pill" href="#pills-iconhome" role="tab" aria-controls="pills-iconhome" aria-selected="true"
              ><i class="icofont icofont-ui-home"></i>Home</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="pills-iconprofile-tab" data-bs-toggle="pill" href="#pills-iconprofile" role="tab" aria-controls="pills-iconprofile" aria-selected="false"
              ><i class="icofont icofont-man-in-glasses"></i>Profile</a
            >
          </li>
          <li class="nav-item">
            <a class="nav-link" id="pills-iconcontact-tab" data-bs-toggle="pill" href="#pills-iconcontact" role="tab" aria-controls="pills-iconcontact" aria-selected="false"
              ><i class="icofont icofont-contacts"></i>Contact</a
            >
          </li>
        </ul>
        <div class="tab-content" id="pills-icontabContent">
          <div class="tab-pane fade show active" id="pills-iconhome" role="tabpanel" aria-labelledby="pills-iconhome-tab">
            <p class="mb-0 m-t-30">
              Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a
              galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It
              was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including
              versions of Lorem Ipsum.It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus
              PageMaker including versions of Lorem IpsumIt was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publish It
              was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more
            </p>
          </div>
          <div class="tab-pane fade" id="pills-iconprofile" role="tabpanel" aria-labelledby="pills-iconprofile-tab">
            <p class="mb-0 m-t-30">{{ desc1 }}</p>
          </div>
          <div class="tab-pane fade" id="pills-iconcontact" role="tabpanel" aria-labelledby="pills-iconcontact-tab">
            <p class="mb-0 m-t-30">{{ desc1 }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <UikitsTabsBotstrapPillDark />
</template>
<script lang="ts" setup>
const desc = ref<string>(
  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum",
);
const desc1 = ref<string>(
  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem IpsumIt was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently",
);
</script>

<template>
  <div class="col-md-12 project-list">
    <div class="card">
      <div class="row">
        <div class="col-md-6 p-0">
          <ul class="nav nav-tabs border-tab" id="top-tab" role="tablist">
            <li class="nav-item">
              <a class="nav-link active" id="top-home-tab" data-bs-toggle="tab" href="#top-home" role="tab" aria-controls="top-home" aria-selected="true">
                <Icon name="material-symbols:target" class="" size="20" />All
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link" id="profile-top-tab" data-bs-toggle="tab" href="#top-profile" role="tab" aria-controls="top-profile" aria-selected="false">
                <Icon name="material-symbols:info-outline" class="" size="20" />Doing
              </a>
            </li>
            <li class="nav-item">
              <a class="nav-link" id="contact-top-tab" data-bs-toggle="tab" href="#top-contact" role="tab" aria-controls="top-contact" aria-selected="false">
                <Icon name="lucide:check-circle" class="" size="20" />Done
              </a>
            </li>
          </ul>
        </div>
        <div class="col-md-6 p-0">
          <div class="form-group mb-0 me-0"></div>
          <client-only>
            <nuxt-link to="/project/project_create">
              <a class="btn btn-primary" href="">
                <Icon name="ci:add-plus-square" class="" size="20" />
                Create New Project
              </a></nuxt-link
            >
          </client-only>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-body">
        <div class="tab-content" id="top-tabContent">
          <div class="tab-pane fade show active" id="top-home" role="tabpanel" aria-labelledby="top-home-tab">
            <ProjectListAllProjects />
          </div>
          <div class="tab-pane fade" id="top-profile" role="tabpanel" aria-labelledby="profile-top-tab">
            <ProjectListDoingProject />
          </div>
          <div class="tab-pane fade" id="top-contact" role="tabpanel" aria-labelledby="contact-top-tab">
            <ProjectListDoneProject />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

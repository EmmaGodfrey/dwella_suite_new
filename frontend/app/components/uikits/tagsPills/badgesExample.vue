<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card height-equal">
      <div class="card-header pb-0">
        <h4>Badges Example</h4>
      </div>
      <div class="card-body">
        <h1>heading <span class="badge badge-primary">New</span></h1>
        <h2>heading <span class="badge badge-primary">New</span></h2>
        <h3>heading <span class="badge badge-primary">New</span></h3>
        <h4>heading <span class="badge badge-primary">New</span></h4>
        <h5>heading <span class="badge badge-primary">New</span></h5>
        <h6>heading <span class="badge badge-primary">New</span></h6>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6">
    <div class="card height-equal">
      <div class="card-header pb-0">
        <h4>Badges as part buttons</h4>
      </div>
      <div class="card-body">
        <div class="mb-3">
          <button class="btn btn-primary" type="button">
            Messages
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="mdi:email-outline" class="" size="40" />
            </span>
          </button>
        </div>
        <div class="mb-3">
          <button class="btn btn-secondary" type="button">
            notifications
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="mdi:bell-outline" class="" size="40" />
            </span>
          </button>
        </div>
        <div class="mb-3">
          <button class="btn btn-success" type="button">
            Update available
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="material-symbols:settings-outline" class="" size="40" />
            </span>
          </button>
        </div>
        <div class="mb-3">
          <button class="btn btn-info" type="button">
            Playing Now
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="lucide:music" class="" size="40" />
            </span>
          </button>
        </div>
        <div class="mb-3">
          <button class="btn btn-warning text-dark" type="button">
            1.2 GB Used
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="lucide:alert-triangle" class="" size="40" />
            </span>
          </button>
        </div>
        <div>
          <button class="btn btn-danger" type="button">
            Alert
            <span class="badge rounded-pill badge-light text-dark">
              <Icon name="lucide:alert-circle" class="" size="40" />
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

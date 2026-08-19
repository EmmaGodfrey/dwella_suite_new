<template>
  <div class="xl-70 box-col-8 col-md-12 col-xl-9">
    <div class="email-right-aside">
      <div class="email-body card">
        <div class="email-profile">
          <div class="email-body">
            <div class="email-compose">
              <div class="email-top compose-border">
                <div class="compose-header">
                  <h4 class="mb-0">New Message</h4>
                  <button class="btn btn-secondary"><i class="fa fa-file me-2"></i> save</button>
                </div>
              </div>
              <div class="email-wrapper">
                <form class="theme-form">
                  <div class="form-group"><label class="col-form-label pt-0 form-label">To</label><input id="exampleInputEmail1" type="email" class="form-control form-control" /></div>
                  <div class="form-group"><label class="col-form-label pt-0 form-label">Subject</label><input id="exampleInputPassword1" type="text" class="form-control form-control" /></div>
                  <div class="form-group">
                    <label class="col-form-label pt-0 form-label">Messages</label>
                    <div class=""></div>
                  </div>
                  <div class="form-group">
                    <client-only>
                      <CommenDropZones />
                    </client-only>
                  </div>
                </form>
                <div class="action-wrapper">
                  <ul class="actions">
                    <li>
                      <nuxt-link class="btn btn-secondary" to="/email/read"><i class="fa fa-paper-plane me-2"></i>send </nuxt-link>
                    </li>
                    <li>
                      <nuxt-link class="btn btn-danger" to="/"> <i class="fa fa-times me-2"></i>cancel</nuxt-link>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

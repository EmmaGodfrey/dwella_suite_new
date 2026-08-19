<template>
  <div class="xl-70 col-md-12 col-xl-9">
    <div class="email-right-aside">
      <div class="email-body card">
        <div class="email-profile">
          <div class="email-right-aside">
            <div class="email-body">
              <div class="email-content">
                <div class="email-top">
                  <div class="row">
                    <div class="col-xl-12">
                      <div class="media">
                        <img class="me-3 rounded-circle" :src="getImages('user/user.png')" alt="" />
                        <div class="media-body">
                          <h6 class="d-block">John Deo</h6>
                          <p>Mattis luctus.Donec nisi diam text.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="email-wrapper">
                  <div class="emailread-group">
                    <div class="read-group">
                      <p>Hello</p>
                      <p>Dear Sir Good Morning,</p>
                    </div>
                    <div class="read-group">
                      <h5>Inquiry about our theme pages design.</h5>
                      <p>
                        Viho Admin is a full featured, multipurpose, premium bootstrap admin template built with Bootstrap 5 Framework, HTML5, CSS and JQuery.It has a huge collection of reusable UI
                        components and integrated with latest jQuery plugins.
                      </p>
                      <p class="m-t-10">
                        It can be used for all type of Web applications like custom admin panel, app backend, CMS or CRM. UI components and integrated with latest jQuery plugins. Viho Admin is a full
                        featured, multipurpose, premium bootstrap admin template built with Bootstrap 5 Framework.
                      </p>
                    </div>
                  </div>
                  <div class="emailread-group">
                    <h6 class="text-muted mb-0"><i class="icofont icofont-clip"></i> ATTACHMENTS</h6>
                    <a class="text-muted text-end right-download font-primary f-w-600" href="#javascripts"><i class="fa fa-long-arrow-down me-2"></i>Download All</a>
                    <div class="clearfix"></div>
                    <div class="attachment">
                      <ul class="simple-list d-flex flex-row list-group">
                        <li><img class="img-fluid" :src="getImages('email/1.jpg')" alt="" /></li>
                        <li><img class="img-fluid" :src="getImages('email/2.jpg')" alt="" /></li>
                        <li><img class="img-fluid" :src="getImages('email/3.jpg')" alt="" /></li>
                      </ul>
                    </div>
                  </div>
                  <div class="emailread-group">
                    <textarea class="form-control" rows="4" cols="50" placeholder="write about your nots"></textarea>
                    <div class="action-wrapper">
                      <ul class="actions">
                        <li>
                          <a class="btn btn-primary" href="javascript:void(0)"><i class="fa fa-reply me-2"></i>Reply</a>
                        </li>
                        <li>
                          <a class="btn btn-secondary" href="javascript:void(0)"><i class="fa fa-reply-all me-2"></i>Reply All</a>
                        </li>
                        <li>
                          <a class="btn btn-danger" href="javascript:void(0)"><i class="fa fa-share me-2"></i>Forward</a>
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
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>

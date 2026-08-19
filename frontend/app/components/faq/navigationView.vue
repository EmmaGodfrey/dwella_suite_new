<template>
  <div class="col-xl-4 xl-40 col-lg-6 col-md-5 box-col-40">
    <div class="row">
      <div class="col-lg-12">
        <div class="card card-mb-faq xs-mt-search">
          <div class="card-header faq-header d-flex justify-content-between">
            <h5 class="ps-0">Search Articles</h5>
            <Icon name="mdi:help-circle-outline" class="" size="20" />
          </div>
          <div class="card-body faq-body">
            <div class="faq-form">
              <input class="form-control" type="text" placeholder="Search.." />
              <Icon name="ph:magnifying-glass-bold" class="search-icon" size="20" />
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-12">
        <div class="card card-mb-faq">
          <div class="card-header faq-header d-flex justify-content-between">
            <h5 class="ps-0">Navigation</h5>
            <Icon name="material-symbols:settings-outline-rounded" class="" size="30" />
          </div>
          <div class="card-body faq-body">
            <div class="navigation-btn">
              <a class="btn btn-primary" href="javascript:void(0)"><Icon class="m-r-10" name="lucide:message-square"></Icon>Ask Question</a>
            </div>
            <div class="navigation-option">
              <ul>
                <li>
                  <a href="javascript:void(0)"> <Icon name="lucide:pen-square" class="" size="15" />Tutorials </a>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="ph:globe-simple" class="" size="15" />Help center </a>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="ci:book-open" class="" size="15" />Knowledgebase </a>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="lucide:file-text" class="" size="15" />Articles </a><span class="badge badge-primary badge-pill pull-right">42</span>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="tdesign:logo-youtube" class="" size="15" />Video Tutorials </a><span class="badge badge-primary badge-pill pull-right">648</span>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="ci:message-circle" class="" size="15" />Ask our community </a>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="lucide:mail" class="" size="15" />Contact us </a>
                </li>
              </ul>
              <ul>
                <li>
                  <a href="javascript:void(0)"> <Icon name="ci:message-circle" class="" size="15" />Ask our community </a>
                </li>
                <li>
                  <a href="javascript:void(0)"> <Icon name="lucide:mail" class="" size="15" />Contact us </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-12">
        <div class="card">
          <div class="card-header faq-header">
            <h5 class="d-inline-block ps-0">Latest Updates</h5>
            <span class="pull-right d-inline-block">See All</span>
          </div>
          <div class="card-body faq-body">
            <div class="media updates-faq-main">
              <div class="updates-faq">
                <Icon name="lucide:rotate-cw" class="font-primary" size="20" />
              </div>
              <div class="media-body updates-bottom-time">
                <p><a href="javascript:void(0)">David Linner </a>requested money back for a double debit card charge</p>
                <p>10 minutes ago</p>
              </div>
            </div>
            <div class="media updates-faq-main">
              <div class="updates-faq">
                <Icon name="lucide:dollar-sign" class="font-primary" size="20" />
              </div>
              <div class="media-body updates-bottom-time">
                <p>All sellers have received monthly payouts</p>
                <p>2 hours ago</p>
              </div>
            </div>
            <div class="media updates-faq-main">
              <div class="updates-faq">
                <Icon name="humbleicons:link" class="font-primary" size="20" />
              </div>
              <div class="media-body updates-bottom-time">
                <p>User Christopher <a href="javascript:void(0)">Wallace</a> is on hold and awaiting for staff reply</p>
                <p>45 minutes ago</p>
              </div>
            </div>
            <div class="media updates-faq-main">
              <div class="updates-faq">
                <Icon name="lucide:check" class="font-primary" size="20" />
              </div>
              <div class="media-body updates-bottom-time">
                <p>Ticket #43683 has been closed by <a href="javascript:void(0)">Victoria Wilson</a></p>
                <p>Dec 7, 11:48</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

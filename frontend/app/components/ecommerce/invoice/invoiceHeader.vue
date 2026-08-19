<template>
  <div>
    <div class="row invo-header">
      <div class="col-sm-6">
        <div class="media">
          <div class="media-left">
            <nuxt-link to="/"><img class="media-object img-60" src="/images/logo/logo-1.png" alt="" /></nuxt-link>
          </div>
          <div class="media-body m-l-20">
            <h4 class="media-heading f-w-600">Viho</h4>
            <p>hello@viho.in<br /><span class="digits">289-335-6503</span></p>
          </div>
        </div>
      </div>
      <div class="col-sm-6">
        <div class="text-md-end text-xs-center">
          <h3>
            Invoice #<span class="digits counter">
              <commen-number-animations data="1069" />
            </span>
          </h3>
          <p>Issued: May<span class="digits"> 27, 2023</span><br />Payment Due: June <span class="digits">27, 2023</span></p>
        </div>
      </div>
    </div>
  </div>
</template>

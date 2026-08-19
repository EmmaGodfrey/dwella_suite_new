<template>
  <div class="user-profile">
    <div class="image">
      <div class="avatar text-center"><img alt="" src="/images/user/2.png" /></div>
      <div class="icon-wrapper">
        <nuxt-link to=""> <i class="icofont icofont-pencil-alt-5"></i></nuxt-link>
      </div>
    </div>
    <div class="user-content text-center">
      <nuxt-link to="/users/profile">
        <h5 class="text-uppercase">mark jecno</h5>
      </nuxt-link>
      <div class="social-list">
        <ul>
          <li>
            <a href="https://www.facebook.com" target="_blank"><i class="fa fa-facebook"></i></a>
          </li>
          <li>
            <a href="https://www.google.com" target="_blank"><i class="fa fa-google-plus"></i></a>
          </li>
          <li>
            <a href="https://www.twitter.com" target="_blank"><i class="fa fa-twitter"></i></a>
          </li>
          <li>
            <a href="https://www.instagram.com" target="_blank"><i class="fa fa-instagram"></i></a>
          </li>
          <li>
            <a href="https://www.rss.com" target="_blank"><i class="fa fa-rss"> </i></a>
          </li>
        </ul>
      </div>
      <div class="follow text-center">
        <div class="row">
          <div class="col border-right">
            <span>Following</span>
            <div class="follow-num">236k</div>
          </div>
          <div class="col">
            <span>Follower</span>
            <div class="follow-num">3691k</div>
          </div>
        </div>
      </div>
      <div class="text-center digits">
        <p>Mark.jecno23@gmail.com</p>
        <p>+91 365 - 658 - 1236</p>
        <p>Fax: 123-4560</p>
      </div>
    </div>
  </div>
</template>

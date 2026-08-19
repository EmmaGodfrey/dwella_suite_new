<template>
  <div class="col-xl-4 col-md-6 box-col-4">
    <div class="card custom-card">
      <div class="card-header pb-0"><img class="img-fluid" src="/images/user-card/3.jpg" alt="" /></div>
      <div class="card-profile"><img class="rounded-circle" src="/images/avtar/3.jpg" alt="" /></div>
      <ul class="card-social">
        <li>
          <a href="https://www.facebook.com"><i class="fa fa-facebook"></i></a>
        </li>
        <li>
          <a href="https://accounts.google.com"><i class="fa fa-google-plus"></i></a>
        </li>
        <li>
          <a href="https://twitter.com"><i class="fa fa-twitter"></i></a>
        </li>
        <li>
          <a href="https://www.instagram.com"><i class="fa fa-instagram"></i></a>
        </li>
        <li>
          <a href="https://dashboard.rss.com/auth/sign-in"><i class="fa fa-rss"></i></a>
        </li>
      </ul>
      <div class="text-center profile-details">
        <h4><router-link to="/pages/social_app" alt="">Scarlett john</router-link></h4>
        <h6>Manager</h6>
      </div>
      <div class="card-footer row">
        <div class="col-4 col-sm-4 pb-0">
          <h6>Follower</h6>
          <h3 class="counter">
            <CommenNumberAnimations data="9564" />
          </h3>
        </div>
        <div class="col-4 col-sm-4 pb-0">
          <h6>Following</h6>
          <h3>
            <span class="counter"> <CommenNumberAnimations data="49" /> </span>K
          </h3>
        </div>
        <div class="col-4 col-sm-4 pb-0">
          <h6>Total Post</h6>
          <h3>
            <span class="counter"> <CommenNumberAnimations data="96" /> </span>M
          </h3>
        </div>
      </div>
    </div>
  </div>
</template>

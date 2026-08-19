<template>
  <div class="container-fluid">
    <div class="row">
      <div class="col-xl-5 b-center bg-size" :style="{ backgroundImage: 'url(' + '/images/login/3.jpg' + ')' }">
        <img class="bg-img-cover bg-center" src="/images/login/3.jpg" alt="looginpage" style="display: none" />
      </div>
      <div class="col-xl-7 p-0">
        <div class="login-card">
          <form class="theme-form login-form">
            <h4>Login</h4>
            <h6>Welcome back! Log in to your account.</h6>
            <div class="form-group">
              <label>Email Address</label>
              <div class="input-group">
                <span class="input-group-text"><i class="icon-email"></i></span>
                <input class="form-control" type="email" placeholder="Test@gmail.com" />
              </div>
            </div>
            <div class="form-group">
              <label>Password</label>
              <div class="input-group">
                <span class="input-group-text"><i class="icon-lock"></i></span>
                <input class="form-control" type="password" name="login[password]" placeholder="*********" />
                <div class="show-hide"><span class="show"></span></div>
              </div>
            </div>
            <div class="form-group">
              <div class="checkbox">
                <input id="checkbox1" type="checkbox" />
                <label class="text-muted" for="checkbox1">Remember password</label>
              </div>
              <a class="link" href="/authentication/forget_password">Forgot password?</a>
            </div>
            <div class="form-group"><a class="btn btn-primary btn-block" href="/" type="submit">Sign in</a></div>
            <div class="login-social-title">
              <h5>Sign in with</h5>
            </div>
            <div class="form-group">
              <ul class="login-social">
                <li>
                  <a href="https://www.linkedin.com/login" target="_blank"
                    ><i data-feather="linkedin"> <Icon name="lucide:linkedin" class="" size="20" /> </i
                  ></a>
                </li>
                <li>
                  <a href="https://www.linkedin.com/login" target="_blank"
                    ><i data-feather="twitter"> <Icon name="tdesign:logo-twitter" class="" size="20" /> </i
                  ></a>
                </li>
                <li>
                  <a href="https://www.linkedin.com/login" target="_blank"
                    ><i data-feather="facebook"> <Icon name="basil:facebook-outline" class="" size="20" /> </i
                  ></a>
                </li>
                <li>
                  <a href="https://www.instagram.com/login" target="_blank"
                    ><i data-feather="instagram"> <Icon name="uil:instagram" class="" size="20" /> </i
                  ></a>
                </li>
              </ul>
            </div>
            <p>
              Don't have account?<a class="ms-2" href=""><nuxt-link to="/auth/register">Account</nuxt-link></a>
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({
  layout: 'custom',
});
useHead({
  title: 'Login Image Two | Cion - Premium Vue Admin Template',
});
</script>

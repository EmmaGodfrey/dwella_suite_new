<template>
  <div>
    <div class="container-fluid p-0">
      <div class="row m-0">
        <div class="col-xl-5 b-center bg-size p-0" :style="{ backgroundImage: 'url(' + '/images/login/1.jpg' + ')' }">
          <img class="bg-img-cover bg-center" src="/images/login/1.jpg" alt="looginpage" style="display: none" />
        </div>
        <div class="col-xl-7 p-0">
          <div class="login-card">
            <div class="theme-form login-form">
              <form class="">
                <h4>Create your account</h4>
                <h6>Enter your personal details to create account</h6>
                <div class="form-group">
                  <label>Your Name</label>
                  <div class="small-group">
                    <div class="input-group">
                      <span class="input-group-text"><i class="icon-user"></i></span>
                      <input class="form-control" type="email" placeholder="First Name" />
                    </div>
                    <div class="input-group">
                      <span class="input-group-text"><i class="icon-user"></i></span>
                      <input class="form-control" type="email" placeholder="Last Name" />
                    </div>
                  </div>
                </div>
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
                    <label class="text-muted" for="checkbox1">Agree with <span>Privacy Policy</span></label>
                  </div>
                </div>
                <div class="form-group">
                  <button class="btn btn-primary btn-block" type="submit">Create Account</button>
                </div>
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
                <p class="mt-4 mb-0">
                  Already have an account?
                  <nuxt-link class="ms-2" tag="a" to="/auth/login"> Login </nuxt-link>
                </p>
              </form>
            </div>
          </div>
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
  title: 'Register Image Two | Cion - Premium Vue Admin Template',
});
</script>

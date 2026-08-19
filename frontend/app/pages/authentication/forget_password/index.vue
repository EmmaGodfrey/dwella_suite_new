<template>
  <div class="page-wrapper">
    <div class="container-fluid p-0">
      <div class="row">
        <div class="col-12">
          <div class="login-card">
            <div class="login-main">
              <form class="theme-form login-form">
                <h4 class="mb-3">Reset Your Password</h4>
                <div class="form-group">
                  <label>Enter Your Mobile Number</label>
                  <div class="row">
                    <div class="col-4 col-sm-3">
                      <input class="form-control" type="text" value="+ 91" />
                    </div>
                    <div class="col-8 col-sm-9">
                      <input class="form-control" type="tel" value="000-000-0000" />
                    </div>
                  </div>
                </div>
                <div class="form-group">
                  <button class="btn btn-primary btn-block" type="submit">Send</button>
                </div>
                <div class="form-group">
                  <span class="reset-password-link">If don't receive OTP?  <a class="btn-link text-danger" href="javascript:void(0)">Resend</a></span>
                </div>
                <div class="form-group">
                  <label>Enter OTP</label>
                  <div class="row">
                    <div class="col">
                      <input class="form-control text-center opt-text" type="text" value="00" maxlength="2" />
                    </div>
                    <div class="col">
                      <input class="form-control text-center opt-text" type="text" value="00" maxlength="2" />
                    </div>
                    <div class="col">
                      <input class="form-control text-center opt-text" type="text" value="00" maxlength="2" />
                    </div>
                  </div>
                </div>
                <h6>Create Your Password</h6>
                <div class="form-group">
                  <label>New Password</label>
                  <div class="input-group">
                    <span class="input-group-text"><i class="icon-lock"></i></span>
                    <input class="form-control" type="password" name="login[password]" placeholder="*********" />
                    <div class="show-hide"><span class="show"></span></div>
                  </div>
                </div>
                <div class="form-group">
                  <label>Retype Password</label>
                  <div class="input-group">
                    <span class="input-group-text"><i class="icon-lock"></i></span>
                    <input class="form-control" type="password" name="login[password]" placeholder="*********" />
                  </div>
                </div>
                <div class="form-group">
                  <div class="checkbox">
                    <input id="checkbox1" type="checkbox" />
                    <label class="text-muted" for="checkbox1">Remember password</label>
                  </div>
                </div>
                <div class="form-group">
                  <button class="btn btn-primary btn-block" type="submit">Done</button>
                </div>
                <p>Already have an password?<router-link class="ms-2" to="/auth/login">Sign in</router-link></p>
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
  title: 'Forget Password | Cion - Premium Vue Admin Template',
});
</script>

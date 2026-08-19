<template>
  <div class="col-sm-12 col-lg-6 col-xl-8 xl-50 col-md-12 box-col-6">
    <div class="card height-equal">
      <div class="card-header pb-0 d-flex justify-content-between align-items-center">
        <h5>Contact Us</h5>
      </div>
      <div class="contact-form card-body">
        <form class="theme-form">
          <div class="form-icon"><i class="icofont icofont-envelope-open"></i></div>
          <div class="mb-3">
            <label for="exampleInputName">Your Name</label>
            <input class="form-control" id="exampleInputName" type="text" placeholder="John Dio" />
          </div>
          <div class="mb-3">
            <label class="col-form-label" for="exampleInputEmail1">Email</label>
            <input class="form-control" id="exampleInputEmail1" type="email" placeholder="Demo@gmail.com" />
          </div>
          <div class="mb-3">
            <label class="col-form-label" for="exampleInputEmail1">Message</label>
            <textarea class="form-control textarea" rows="3" cols="50" placeholder="Your Message"></textarea>
          </div>
          <div>
            <button class="btn btn-primary">SEND IT</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

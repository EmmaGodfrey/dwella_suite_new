<template>
  <div class="col-sm-12 col-md-6">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Dropdown With Divider</h5>
        <span>Use a class </span>
      </div>
      <div class="card-body dropdown-basic">
        <div class="dropdown">
          <button class="dropbtn btn-primary" type="button">
            Dropdown Button <span><i class="icofont icofont-arrow-down"></i></span>
          </button>
          <div class="dropdown-content">
            <a href="#">Link 1</a>
            <a href="#">Link 2</a>
            <a href="#">Link 3</a>
            <a href="#">Another Link</a>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-md-6">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Dropdown With Header</h5>
        <span>Use a class <code>.dropdown-header</code></span>
      </div>
      <div class="card-body dropdown-basic">
        <div class="dropdown">
          <button class="dropbtn btn-primary" type="button">
            Dropdown Button <span><i class="icofont icofont-arrow-down"></i></span>
          </button>
          <div class="dropdown-content">
            <h5 class="dropdown-header">Dropdown header</h5>
            <a href="#">Link 1</a><a href="#">Link 2</a>
            <h5 class="dropdown-header">Dropdown header</h5>
            <a href="#">Another Link</a>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-md-6">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Dropdown With Disable</h5>
        <span>Use a class <code>.dropdown-disabled</code></span>
      </div>
      <div class="card-body dropdown-basic">
        <div class="dropdown">
          <button class="dropbtn btn-primary" type="button">
            Dropdown Button <span><i class="icofont icofont-arrow-up"></i></span>
          </button>
          <div class="dropdown-content">
            <a href="#">Normal</a>
            <a class="active" href="#">Active</a>
            <a class="disabled" href="#">Disabled</a>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-md-6">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Dropdown With DropUp</h5>
        <span>Use a class <code>.drop-up</code></span>
      </div>
      <div class="card-body dropdown-basic">
        <div class="dropdown">
          <button class="dropbtn btn-primary" type="button">
            Dropdown Button <span><i class="icofont icofont-arrow-up"></i></span>
          </button>
          <div class="dropup-content dropdown-content"><a href="#">Link 1</a><a href="#">Link 2</a></div>
        </div>
      </div>
    </div>
  </div>
</template>

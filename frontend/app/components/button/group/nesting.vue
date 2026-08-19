<template>
  <div class="col-lg-6">
    <div class="card height-equal">
      <div class="card-header">
        <h5>Nesting</h5>
        <span>Make nesting buttons</span>
      </div>
      <div class="card-body btn-group-wrapper">
        <div class="m-b-30">
          <div class="btn-group" role="group" aria-label="Button group with nested dropdown">
            <button class="btn btn-primary"><i class="fa fa-bold"></i></button>
            <button class="btn btn-secondary"><i class="fa fa fa-italic"></i></button>
            <div class="btn-group" role="group">
              <button class="btn btn-light dropdown-toggle" id="btnGroupDrop1" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</button>
              <div class="dropdown-menu" aria-labelledby="btnGroupDrop1">
                <a class="dropdown-item" href="#">Dropdown link</a><a class="dropdown-item" href="#">Dropdown link</a><a class="dropdown-item" href="#">Dropdown link</a
                ><a class="dropdown-item" href="#">Dropdown link</a>
              </div>
            </div>
          </div>
        </div>
        <div class="m-b-30">
          <div class="btn-group">
            <button class="btn btn-primary"><i class="fa fa-bold"></i></button>
            <button class="btn btn-secondary"><i class="fa fa fa-italic"></i></button>
            <button class="btn btn-success"><i class="fa fa-file-image-o"></i></button>
            <button class="btn btn-info"><i class="fa fa-paperclip"></i></button>
          </div>
        </div>
        <div class="m-b-30">
          <div class="btn-group">
            <button class="btn btn-primary btn-lg"><i class="fa fa-bold"></i></button>
            <button class="btn btn-secondary btn-lg"><i class="fa fa fa-italic"></i></button>
            <button class="btn btn-success btn-lg"><i class="fa fa-file-image-o"></i></button>
            <button class="btn btn-info btn-lg"><i class="fa fa-paperclip"></i></button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-lg-6">
    <div class="card height-equal">
      <div class="card-header">
        <h5>Vertical</h5>
        <span>Make vertical buttons</span>
      </div>
      <div class="card-body btn-group-wrapper">
        <div class="btn-group-vertical" role="group" aria-label="Vertical button group">
          <button class="btn btn-primary" type="button">Button</button>
          <button class="btn btn-secondary" type="button">Button</button>
          <div class="btn-group" role="group">
            <button class="btn btn-success dropdown-toggle" id="btnGroupVerticalDrop1" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</button>
            <div class="dropdown-menu" aria-labelledby="btnGroupVerticalDrop1"><a class="dropdown-item" href="#">Dropdown link</a><a class="dropdown-item" href="#">Dropdown link</a></div>
          </div>
          <button class="btn btn-info" type="button">Button</button>
          <button class="btn btn-warning" type="button">Button</button>
          <div class="btn-group" role="group">
            <button class="btn btn-danger dropdown-toggle" id="btnGroupVerticalDrop2" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</button>
            <div class="dropdown-menu" aria-labelledby="btnGroupVerticalDrop2"><a class="dropdown-item" href="#">Dropdown link</a><a class="dropdown-item" href="#">Dropdown link</a></div>
          </div>
          <div class="btn-group" role="group">
            <button class="btn btn-light dropdown-toggle" id="btnGroupVerticalDrop3" type="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">Dropdown</button>
            <div class="dropdown-menu" aria-labelledby="btnGroupVerticalDrop3"><a class="dropdown-item" href="#">Dropdown link</a><a class="dropdown-item" href="#">Dropdown link</a></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

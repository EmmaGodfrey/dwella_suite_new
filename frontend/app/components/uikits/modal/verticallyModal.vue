<template>
  <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-bs-target="#exampleModalCenter">Vertically centered</button>
  <div class="modal fade" id="exampleModalCenter" tabindex="-1" role="dialog" aria-labelledby="exampleModalCenter" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Modal title</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>Cras mattis consectetur purus sit amet fermentum. Cras justo odio, dapibus ac facilisis in, egestas eget quam. Morbi leo risus, porta ac consectetur ac, vestibulum at eros.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Close</button>
          <button class="btn btn-primary" type="button">Save changes</button>
        </div>
      </div>
    </div>
  </div>
  <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-bs-target="#tooltipmodal">Tooltips and popovers</button>
  <div class="modal fade" id="tooltipmodal" tabindex="-1" role="dialog" aria-labelledby="tooltipmodal" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Modal title</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <h5>Popover in a modal</h5>
          <p>
            This
            <a
              class="btn btn-primary popover-test"
              href="javascript:void(0)"
              role="button"
              title=""
              data-content="Popover body content is set in this attribute."
              data-container="#exampleModalPopovers"
              data-original-title="Popover title"
              >button</a
            >
            triggers a popover on click.
          </p>
          <hr />
          <h5>Tooltips in a modal</h5>
          <p>
            <a class="tooltip-test" href="javascript:void(0)" title="" data-container="#exampleModalPopovers" data-original-title="Tooltip">This link</a> and
            <a class="tooltip-test" href="javascript:void(0)" title="" data-container="#exampleModalPopovers" data-original-title="Tooltip">that link</a> have tooltips on hover.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Close</button>
          <button class="btn btn-primary" type="button">Save changes</button>
        </div>
      </div>
    </div>
  </div>
  <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-bs-target="#grid-modal">Using the grid</button>
  <div class="modal fade" id="grid-modal" tabindex="-1" role="dialog" aria-labelledby="grid-modal" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Modal title</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body grid-showcase">
          <div class="container-fluid bd-example-row">
            <div class="row">
              <div class="col-md-4"><span>.col-md-4</span></div>
              <div class="col-md-4 ml-auto"><span>.col-md-4 .ml-auto</span></div>
            </div>
            <div class="row">
              <div class="col-md-3 ml-auto"><span>.col-md-3 .ml-auto</span></div>
              <div class="col-md-2 ml-auto"><span>.col-md-2 .ml-auto</span></div>
            </div>
            <div class="row">
              <div class="col-md-6 ml-auto"><span>.col-md-6 .ml-auto</span></div>
            </div>
            <div class="row">
              <div class="col-sm-9">
                <span>Level 1: .col-sm-9</span>
                <div class="row">
                  <div class="col-8 col-sm-6"><span>Level 2: .col-8 .col-sm-6</span></div>
                  <div class="col-4 col-sm-6"><span>Level 2: .col-4 .col-sm-6</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Close</button>
          <button class="btn btn-primary" type="button">Save changes</button>
        </div>
      </div>
    </div>
  </div>
</template>

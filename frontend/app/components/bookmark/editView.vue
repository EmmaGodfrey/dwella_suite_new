<template>
  <div class="modal fade modal-bookmark" id="edit-bookmark" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Edit Bookmark</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form class="form-bookmark needs-validation" novalidate>
            <div class="form-row">
              <div class="form-group col-md-12">
                <label>Web Url</label>
                <input class="form-control" id="editurl" type="text" required autocomplete="off" value="http://admin.pixelstrap.com/endless/ltr/landing-page.html" />
              </div>
              <div class="form-group col-md-12">
                <label>Title</label>
                <input class="form-control" id="edittitle" type="text" required autocomplete="off" value="Admin Template" />
              </div>
              <div class="form-group col-md-12">
                <label>Description</label>
                <textarea class="form-control" id="editdesc" required autocomplete="off">
Endless is beautifully crafted, clean and modern designed admin theme with 6 different demos and light - dark versions.</textarea
                >
              </div>
              <div class="row">
                <div class="form-group col mb-0">
                  <label>Group</label>
                  <select class="js-example-basic-single">
                    <option value="AL">My Bookmarks</option>
                  </select>
                </div>
                <div class="form-group col mb-0">
                  <label>Collection</label>
                  <select class="js-example-disabled-results">
                    <option value="general">General</option>
                    <option value="fs">fs</option>
                  </select>
                </div>
              </div>
            </div>
            <button class="btn btn-secondary" type="button">Save</button>
            <button class="btn btn-primary ms-1" type="button" data-bs-dismiss="modal">Cancel</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

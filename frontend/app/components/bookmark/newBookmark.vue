<template>
  <div class="modal fade modal-bookmark" id="bookmarkmodal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="exampleModalLabel">Add Bookmark</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close" @click="emit('close')"></button>
        </div>
        <div class="modal-body">
          <form class="form-bookmark needs-validation" id="bookmark-form" novalidate>
            <div class="form-row">
              <div class="form-group col-md-12">
                <label for="bm-weburl">Web Url</label>
                <input class="form-control" id="bm-weburl" type="text" v-model="web" required autocomplete="off" />
              </div>
              <div class="form-group col-md-12">
                <label for="bm-title">Title</label>
                <input class="form-control" id="bm-title" type="text" v-model="title" required autocomplete="off" />
              </div>
              <div class="form-group col-md-12">
                <label>Description</label>
                <textarea class="form-control" id="bm-desc" v-model="description" required autocomplete="off"></textarea>
              </div>
              <div class="row">
                <div class="form-group col mb-0">
                  <label>Group</label>
                  <select class="js-example-basic-single form-control" id="bm-group">
                    <option value="bookmark">My Bookmarks</option>
                  </select>
                </div>
                <div class="form-group col mb-0">
                  <label>Collection</label>
                  <select class="js-example-disabled-results form-control" id="bm-collection">
                    <option value="general">General</option>
                    <option value="fs">fs</option>
                  </select>
                </div>
              </div>
            </div>
            <input id="index_var" type="hidden" value="6" />
            <button class="btn btn-secondary" type="button" @click="submitBookmark()" data-bs-dismiss="modal">Save</button>
            <button class="btn btn-primary ms-1" type="button" data-bs-dismiss="modal" @click="emit('close')">Cancel</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const web = ref<string>('');
const title = ref<string>('');
const description = ref<string>('');
const formSubmitted = ref<boolean>(false);
const titleError = ref<boolean>(false);
const descError = ref<boolean>(false);
const errors = ref<string | number[]>([]);
const store = useProjectStore();
const { bookmark } = storeToRefs(store);
const emit = defineEmits(['close']);
function submitBookmark() {
  formSubmitted.value = true;
  errors.value = [];
  if (title.value.length < 5 || description.value.length < 5) {
    titleError.value = true;
    descError.value = true;
    errors.value.push();
  } else {
    titleError.value = false;
    descError.value = false;
    errors.value.push();
    const arr = {
      id: 1,
      fillstar: false,
      website_url: web.value,
      title: title.value,
      desc: description.value,
      image: 'lightgallry/05.jpg',
      collection: 'General',
      active: false,
    };
    bookmark.value.push(arr);
  }
}
</script>

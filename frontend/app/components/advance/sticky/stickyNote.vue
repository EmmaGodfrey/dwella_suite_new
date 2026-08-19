<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Sticky Note <a class="btn btn-primary pull-right m-l-10" id="add_new" href="javascript:;" v-on:click="addNewSticky">Add New Note</a></h5>
      </div>
      <div class="card-body">
        <div class="sticky-note" id="board">
          <div class="note" style="" v-for="(n, index) in stickyNotes" :key="index">
            <a v-on:click="removeSticky(index)" class="button remove">X</a>
            <div class="note_cnt">
              <textarea class="title" placeholder="Enter note title" style="height: 64px" v-text="n.title"></textarea>
              <textarea class="cnt" placeholder="Enter note description here" style="height: 200px" v-text="n.description"></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
interface sticky {
  id: string;
  title: string;
  description: string;
}
const stickyNotes = ref<sticky[]>([]);
onMounted(() => {
  stickyNotes.value.push({ id: '', title: '', description: '' });
});
function addNewSticky() {
  stickyNotes.value.push({ id: '', title: '', description: '' });
}
function removeSticky(index: number) {
  stickyNotes.value.splice(index, 1);
}
</script>

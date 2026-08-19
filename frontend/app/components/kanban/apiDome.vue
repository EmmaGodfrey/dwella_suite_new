<template>
  <div class="col-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>API</h5>
        <p class="mb-0">add item, add board, delete board:</p>
      </div>
      <div class="card-body">
        <div id="demo2">
          <div class="kanban-container">
            <div
              data-id="_todo"
              v-for="(board, index) in dropZones"
              :key="index"
              data-order="1"
              @drop="onDrop($event, index)"
              @dragover.prevent
              @dragenter.prevent
              class="kanban-board"
              style="width: 400px; margin-left: 15px; margin-right: 15px"
            >
              <header class="kanban-board-header" :class="board.bg">
                <div class="kanban-title-board">{{ board.title }}</div>
              </header>
              <main class="kanban-drag">
                <div class="kanban-item is-moving" v-for="item in list(index)" :key="item.title" draggable="true" @dragstart="startDrag($event, item)">
                  <a class="kanban-box" href="#" draggable="false"
                    ><span class="date">{{ item.date }}</span
                    ><span class="badge f-right" :class="item.badge">{{ item.priority }}</span>
                    <img class="mt-2 img-fluid" v-if="item.img" :src="getImgUrl(item.img)" alt="" data-original-title="" title="" />
                    <h6>{{ item.title }}</h6>
                    <div class="media">
                      <img class="img-20 me-1 rounded-circle" :src="'/images/user/3.jpg'" alt="" data-original-title="" title="" />
                      <div class="media-body">
                        <p>{{ item.place }}</p>
                      </div>
                    </div>
                    <div class="d-flex mt-3">
                      <ul class="list">
                        <li><i class="fa fa-comments-o"></i>2</li>
                        <li><i class="fa fa-paperclip"></i>2</li>
                        <li><i class="fa fa-eye"></i></li>
                      </ul>
                      <div class="customers">
                        <ul>
                          <li class="d-inline-block me-3">
                            <p class="f-12">+5</p>
                          </li>
                          <li class="d-inline-block">
                            <img class="img-20 rounded-circle" :src="'/images/user/3.jpg'" alt="" data-original-title="" title="" />
                          </li>
                          <li class="d-inline-block">
                            <img class="img-20 rounded-circle" :src="'/images/user/1.jpg'" alt="" data-original-title="" title="" />
                          </li>
                          <li class="d-inline-block">
                            <img class="img-20 rounded-circle" :src="'/images/user/5.png'" alt="" data-original-title="" title="" />
                          </li>
                        </ul>
                      </div>
                    </div>
                  </a>
                </div>
              </main>
              <footer></footer>
            </div>
          </div>
        </div>
        <div class="kanban-btn-list">
          <button class="btn btn-primary kanban-btn" @click.prevent="addDefaultBoard">Add "Default" board</button>
          <button class="btn btn-secondary ms-2 kanban-btn" id="addToDo" @click.prevent="addTodoBoard">Add element in "To Do" Board</button>
          <button class="btn btn-danger mb-0 ms-2 kanban-btn" @click.prevent="removeDone">Remove "Done" Board</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useKanbanStore } from '~/store/kanban';

import type { KanbanItem } from '~/types/common';

interface DropZone {
  title: string;
  id: number;
  bg?: string;
}
const dropZones = ref<DropZone[]>([
  { title: 'Todo (2)', id: 0 },
  { title: 'Doing (2)', id: 1 },
  { title: 'Done (2)', id: 3 },
]);
const store = useKanbanStore();
const { api } = storeToRefs(store);
const kanbanlist = api.value;

function removeDone() {
  for (var i = kanbanlist.length - 1; i >= 0; i--) kanbanlist[i]!.list === 2 && kanbanlist.splice(i, 1);
}
function addDefaultBoard() {
  let objToAdd = {
    title: 'New deafult board',
    list: 0,
    place: 'Pixelstrap, New york',
    image: '/images/user/3.jpg',
    priority: 'Low',
    img: 'other-images/calender-bg.png',
    badge: 'badge-success',
    id: 7,
    date: '24/7/20',
    more: '',
  };
  kanbanlist.push(objToAdd);
}
function addTodoBoard() {
  let objToAdd = {
    title: 'Test Sidebar',
    list: 0,
    place: 'Themeforest, australia',
    image: '/images/user/3.jpg',
    badge: 'badge-danger',
    id: 8,
    more: '+5',
    priority: 'Argent',
    date: '24/7/20',
  };
  kanbanlist.push(objToAdd);
}
function list(index: number) {
  return kanbanlist.filter((kanbanlist: KanbanItem) => kanbanlist.list === index);
}
function startDrag(evt: DragEvent, item: KanbanItem) {
  if (!evt.dataTransfer) return;
  evt.dataTransfer.dropEffect = 'move';
  evt.dataTransfer.effectAllowed = 'move';
  evt.dataTransfer.setData('itemID', item.id.toString());
}
function onDrop(evt: DragEvent, list: number) {
  if (!evt.dataTransfer) return;
  const itemID = evt.dataTransfer.getData('itemID');
  const item = kanbanlist.find((kanbanlist: KanbanItem) => kanbanlist.id == Number(itemID));
  if (item) {
    item.list = list;
  }
}
function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>

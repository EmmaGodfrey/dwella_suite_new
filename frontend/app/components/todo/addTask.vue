<template>
  <div class="col-xl-9">
    <div class="card">
      <div class="card-header b-bottom">
        <div class="todo-list-header">
          <div class="new-task-wrapper input-group">
            <input class="form-control" id="new-task" placeholder="Enter new task here. . ." v-on:keyup.enter="addnewtask" v-model="task" /><span
              class="btn btn-primary d-flex input-group-text add-new-task-btn"
              id="add-task"
              @click="addnewtask()"
              >Add Task</span
            >
          </div>
        </div>
      </div>
      <div class="card-body">
        <div class="todo">
          <div class="todo-list-wrapper custom-scrollbar">
            <div class="todo-list-container">
              <div class="todo-list-body">
                <ul id="todo-list">
                  <li v-for="(todo, index) in todolist" :key="index" class="task" :class="{ completed: todo.status == 'complete' }">
                    <div class="task-container">
                      <h4 class="task-label">{{ todo.title }}</h4>
                      <div class="d-flex align-items-center gap-3">
                        <div>
                          <span class="badge" :class="todo.badgeClass">{{ todo.priority }}</span>
                        </div>
                        <h5 class="assign-name m-0" @click="taskComplete(todo.id, todo.status)">
                          {{ todo.date }}
                        </h5>
                        <span class="task-action-btn">
                          <span class="action-box large delete-btn" title="Delete Task" @click="remove(index)"
                            ><i class="icon"><i class="icon-trash"></i></i
                          ></span>
                        </span>
                      </div>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { toast } from 'vue3-toastify';

import { useTodoStore } from '~/store/todo';

const markallread = ref<boolean>(true);
const task = ref<string>('');
const addtask = ref<boolean>(false);
const store = useTodoStore();
const { data } = storeToRefs(store);
const { addtodo, taskcomplete, tododelete } = store;
const todolist = data.value;
function addnewtask() {
  if (task.value !== '') {
    addtodo(task.value);
    task.value = '';
    addtask.value = false;
    toast.success(' Task list is updated.', {
      hideProgressBar: true,
      autoClose: 2000,
      theme: 'colored',
      position: 'top-right',
    });
  }
}
function taskComplete(id: number, status: string) {
  taskcomplete(id);
  if (status !== '')
    toast.success(' tasks marked as complete. ', {
      hideProgressBar: true,
      autoClose: 2000,
      theme: 'colored',
      position: 'top-right',
    });
  else
    toast.error(' tasks marked as incomplete.', {
      hideProgressBar: true,
      autoClose: 2000,
      theme: 'colored',
      position: 'top-right',
    });
}
function remove(index: number) {
  tododelete(index);
  toast.success(' Task has been deleted.', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
</script>

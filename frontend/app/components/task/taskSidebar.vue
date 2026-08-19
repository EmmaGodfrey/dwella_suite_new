<template>
  <div class="col-xl-3 box-col-4 xl-30">
    <div class="email-sidebar">
      <a class="btn btn-primary email-aside-toggle" href="javascript:void(0)" @click="collapseFilter()">bookmark filter</a>
      <div class="email-left-aside" :class="filtered ? 'open' : ''">
        <div class="card">
          <div class="card-body">
            <div class="email-app-sidebar left-bookmark">
              <div class="media">
                <div class="media-size-email"><img class="me-3 rounded-circle" src="/images/user/user.png" alt="" /></div>
                <div class="media-body">
                  <nuxt-link to="/users/profile">
                    <h6 class="f-w-600">MARK JENCO</h6>
                  </nuxt-link>
                  <p>Markjecno@gmail.com</p>
                </div>
              </div>
              <ul class="nav main-menu custom-scrollbar" role="tablist">
                <li class="nav-item">
                  <button class="badge-light badge-light btn-block btn-mail" type="button" data-bs-toggle="modal" data-bs-target="#taskmodel">
                    <Icon name="lucide:check-circle" class="me-2" size="20" />New Task
                  </button>
                  <TaskNewTask />
                </li>
                <li class="nav-item"><span class="main-title"> Views</span></li>
                <li>
                  <a id="pills-created-tab" data-bs-toggle="pill" href="#pills-created" role="tab" aria-controls="pills-created" aria-selected="true"
                    ><span class="title" v-on:click="says('pills_created')"> Created by me</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-todaytask-tab" data-bs-toggle="pill" href="#pills-todaytask" role="tab" aria-controls="pills-todaytask" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-todaytask')"> Today's Tasks</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-delayed-tab" data-bs-toggle="pill" href="#pills-delayed" role="tab" aria-controls="pills-delayed" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-delayed')"> Delayed Tasks</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-upcoming-tab" data-bs-toggle="pill" href="#pills-upcoming" role="tab" aria-controls="pills-upcoming" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-upcoming')">Upcoming Tasks</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-weekly-tab" data-bs-toggle="pill" href="#pills-weekly" role="tab" aria-controls="pills-weekly" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-weekly')">This week tasks</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-monthly-tab" data-bs-toggle="pill" href="#pills-monthly" role="tab" aria-controls="pills-monthly" aria-selected="false"
                    ><span class="title" v-on:click="says('ppills-monthly')">This month tasks</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-assigned-tab" data-bs-toggle="pill" href="#pills-assigned" role="tab" aria-controls="pills-assigned" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-assigned')">Assigned to me</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-tasks-tab" data-bs-toggle="pill" href="#pills-tasks" role="tab" aria-controls="pills-tasks" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-tasks')">My tasks</span></a
                  >
                </li>
                <li>
                  <hr />
                </li>
                <li>
                  <span class="main-title">
                    Tags<span class="pull-right"
                      ><a href="javascript:void(0)" data-bs-toggle="modal" data-bs-target="#createtag"> <Icon name="iconamoon:sign-plus-circle-light" class=" " size="20" /> </a></span
                  ></span>
                </li>
                <li>
                  <a class="show" id="pills-notification-tab" data-bs-toggle="pill" href="#pills-notification" role="tab" aria-controls="pills-notification" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-notification')"> Notification</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-newsletter-tab" data-bs-toggle="pill" href="#pills-newsletter" role="tab" aria-controls="pills-newsletter" aria-selected="false"
                    ><span class="title" v-on:click="says('pills-newsletter')"> Newsletter</span></a
                  >
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-xl-9 col-md-12 box-col-8 xl-70">
    <div class="email-right-aside bookmark-tabcontent">
      <div class="card email-body radius-left">
        <div class="ps-0">
          <div class="tab-content">
            <TaskCreatedView />
            <TaskTodayTask />
            <TaskDelayedTasks />
            <TaskUpcomingTasks />
            <TaskWeekTasks />
            <TaskMonthTasks />
            <TaskAssignedView />
            <TaskMyTasks />
            <TaskNotificationView />
            <TaskNewsLetter />
            <TaskCareateTag />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const filtered = ref<boolean>(false);
const store = useProjectStore();
const { say } = store;

function says(message: string) {
  say(message);
}
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>

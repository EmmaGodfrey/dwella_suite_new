<template>
  <div class="col-xl-6 xl-100 box-col-12">
    <div class="card employee-status">
      <div class="card-header pb-0 d-flex justify-content-between align-items-center">
        <h5>EMPLOYEE STATUS</h5>
      </div>
      <div class="card-body">
        <div class="user-status table-responsive">
          <table class="table table-bordernone">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Designation</th>
                <th scope="col">Skill Level</th>
                <th scope="col">Experience</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in data" :key="index">
                <td class="bd-t-none u-s-tb">
                  <div class="align-middle image-sm-size">
                    <img class="img-radius align-top m-r-15 rounded-circle" :src="item.img" alt="" />
                    <div class="d-inline-block">
                      <h6>
                        {{ item.name }}<span class="text-muted">({{ item.online }}+ Online)</span>
                      </h6>
                    </div>
                  </div>
                </td>
                <td>{{ item.designation }}</td>
                <td>
                  <div class="progress-showcase">
                    <div class="progress" style="height: 8px">
                      <div class="progress-bar" :class="item.class" role="progressbar" style="width: 30%" aria-valuenow="50" :style="{ width: item.skill }" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                  </div>
                </td>
                <td>{{ item.experience }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useWidgetsStore } from '~/store/widgets';

const store = useWidgetsStore();
const { employe } = storeToRefs(store);
const data = employe.value;
</script>

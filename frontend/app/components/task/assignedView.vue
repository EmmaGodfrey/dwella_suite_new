<template>
  <div class="fade tab-pane" id="pills-assigned" v-bind:class="store1.activeclass === 'pills-assigned' ? 'active show' : ''" role="tabpanel" aria-labelledby="pills-assigned-tab">
    <div class="card mb-0">
      <div class="card-header d-flex">
        <h6 class="mb-0">Assigned to me</h6>
        <a href="javascript:void(0)" @click="printWindow()"> <Icon name="clarity:printer-line" class="me-2" size="20" />Print </a>
      </div>
      <div class="card-body p-0">
        <div class="taskadd">
          <div class="table-responsive">
            <table class="table">
              <tbody>
                <tr v-for="(row, index) in task" :key="index">
                  <td>
                    <h6 class="task_title_0">{{ row.title }}</h6>
                    <p class="project_name_0">General</p>
                  </td>
                  <td>
                    <p class="task_desc_0">{{ row.desc }}</p>
                  </td>
                  <td>
                    <a class="me-2" href="javascript:void(0)"> <Icon name="ph:link-bold" class="" size="20" /> </a
                    ><a href="javascript:void(0)">
                      <Icon name="ion:android-more-horizontal" class="" size="20" />
                    </a>
                  </td>
                  <td>
                    <a href="javascript:void(0)">
                      <Icon name="lucide:trash-2" class="" size="20" @click="removeTask(index)" />
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

import { useProjectStore } from '~/store/project';
import { useTaskStore } from '~/store/task';

const store1 = useProjectStore();
const store = useTaskStore();
const { items } = storeToRefs(store);
const task = items.value;

function printWindow() {
  window.print();
}
function removeTask(index: number) {
  swal
    .fire({
      icon: 'warning',
      title: 'Are you sure?',
      text: 'This Task will be deleted from your Personal task ',
      showCancelButton: true,
      cancelButtonText: 'Cancel',
      confirmButtonText: 'Ok',
      confirmButtonColor: 'var(--theme-default)',
    })
    .then(result => {
      if (result) {
        task.splice(index, 1);
        swal.fire({
          icon: 'success',
          text: 'Poof! Your imaginary file has been deleted!',
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({
          text: 'Your contact is safe!',
          confirmButtonColor: 'var(--theme-default)',
        });
      }
    });
}
</script>

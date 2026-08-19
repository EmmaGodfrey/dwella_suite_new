<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Advanced State</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-success sweet-12" type="button" v-on:click="advancedSuccessAlert">Success</button>
        <button class="btn btn-danger sweet-11" type="button" v-on:click="advancedDangerAlert">Danger</button>
        <button class="btn btn-info sweet-13" type="button" v-on:click="advancedInfoAlert">Information</button>
        <button class="btn btn-warning sweet-10" type="button" v-on:click="advancedWarningAlert">Warning</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

function advancedSuccessAlert() {
  swal
    .fire({
      text: 'A wild Pikachu appeared! What do you want to do?',
      showCancelButton: true,

      confirmButtonText: 'Throw Pokéball!',
      confirmButtonColor: 'var(--theme-default)',
      cancelButtonText: 'Defeat',
      cancelButtonColor: 'var(--theme-default)',
    })
    .then(result => {
      if (result.value) {
        swal.fire({
          icon: 'success',
          title: 'Gotcha!',
          text: 'Pikachu was caught!',
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({
          text: 'Pikachu fainted! You gained 500 XP!',
          confirmButtonColor: 'var(--theme-default)',
        });
      }
    });
}
function advancedDangerAlert() {
  swal.fire({
    text: 'Are you sure you want to do this?',
    showCancelButton: true,
    confirmButtonText: 'Aww yiss!',
    confirmButtonColor: 'var(--theme-default)',
    cancelButtonText: 'Oh noez!',
    cancelButtonColor: '#efefef',
    reverseButtons: true,
  });
}
function advancedInfoAlert() {
  swal
    .fire({
      text: 'Write something here:',
      input: 'text',
      confirmButtonColor: 'var(--theme-default)',
    })
    .then(result => {
      if (result.value) {
        swal.fire({
          text: 'You typed:' + result.value,
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({
          text: 'You typed:' + result.value,
          confirmButtonColor: 'var(--theme-default)',
        });
      }
    });
}
function advancedWarningAlert() {
  swal.fire({
    text: 'Are you sure you want to do this?',
    showCancelButton: true,
    confirmButtonText: 'Aww yiss!',
    confirmButtonColor: 'var(--theme-default)',
    cancelButtonText: 'Oh noez!',
    cancelButtonColor: '#efefef',
    reverseButtons: true,
  });
}
</script>

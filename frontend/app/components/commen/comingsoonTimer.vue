<template>
  <ul>
    <li><span class="time digits" v-text="days"></span><span class="title">days</span></li>
    <li><span class="time digits" v-text="hours"></span><span class="title">Hours</span></li>
    <li><span class="time digits" v-text="minutes"></span><span class="title">Minutes</span></li>
    <li><span class="time digits" v-text="seconds"></span><span class="title">Seconds</span></li>
  </ul>
</template>
<script lang="ts" setup>
const td = ref<number>(0);
const days = ref<number>(0);
const hours = ref<number>(0);
const minutes = ref<number>(0);
const seconds = ref<number>(0);
const startTime = ref<string | number>('');
const endTime = ref<string | number>('');
onMounted(() => {
  timer();
});
function timer() {
  setInterval(() => {
    endTime.value = new Date().getTime();
    ((startTime.value = new Date('Sep 1, 2023 00:00:00').getTime()), (td.value = endTime.value - startTime.value));
    if (td.value >= 0) {
      seconds.value = Math.floor((td.value / 1000) % 60);
      minutes.value = Math.floor((td.value / 1000 / 60) % 60);
      hours.value = Math.floor((td.value / (1000 * 60 * 60)) % 24);
      days.value = Math.floor(td.value / (1000 * 60 * 60 * 24));
    } else {
      seconds.value = minutes.value = hours.value = days.value = 0;
    }
  });
}
</script>

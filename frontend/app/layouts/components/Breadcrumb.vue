<template>
  <div class="container-fluid">
    <div class="page-header">
      <div class="row">
        <div class="col-lg-6 main-header">
          <h2>{{ title }}</h2>
          <h6 class="mb-0">{{ parent }}</h6>
        </div>
        <div class="col-lg-6 breadcrumb-right">
          <ol class="breadcrumb">
            <li
              v-for="(item, index) in breadcrumbs"
              :key="index"
              class="breadcrumb-item"
              :class="{ active: item.active }"
            >
              <nuxt-link v-if="item.url && !item.active" :to="item.url">
                {{ item.title }}
              </nuxt-link>
              <span v-else>{{ item.title }}</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  parent: string
}

defineProps<Props>()

const { breadcrumbs } = useBreadcrumbs()
</script>

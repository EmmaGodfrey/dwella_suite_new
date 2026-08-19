<template>
  <div class="d-flex align-items-center gap-2 flex-wrap">
    <VTextField
      v-model="localFilters.search"
      placeholder="Search by name or email"
      prepend-inner-icon="mdi-magnify"
      clearable
      density="compact"
      hide-details
      style="min-width: 250px;"
      @update:model-value="handleSearchChange"
    />
    <VSelect
      v-model="localFilters.role"
      :items="roleOptions"
      placeholder="Filter by role"
      clearable
      density="compact"
      hide-details
      style="min-width: 150px;"
      @update:model-value="applyFilters"
    />
  </div>
</template>

<script setup lang="ts">
import type { UsersListParams } from '~/types/user'

interface Props {
  filters: UsersListParams
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:filters': [filters: UsersListParams]
}>()

const localFilters = ref<UsersListParams>({ ...props.filters })
let searchTimeout: NodeJS.Timeout | null = null

const roleOptions = [
  { title: 'Admin', value: 'admin' },
  { title: 'User', value: 'user' },
  { title: 'Manager', value: 'manager' },
]

const handleSearchChange = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 500)
}

const applyFilters = () => {
  emit('update:filters', { ...localFilters.value })
}

watch(() => props.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
}, { deep: true })
</script>

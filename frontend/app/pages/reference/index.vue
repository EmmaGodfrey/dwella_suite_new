<template>
  <div>
    <BreadCrumbs title="Reference Data" main="Admin" />

    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-12">
          <div class="card">
            <div class="card-body">
              <!-- Tabs -->
              <ul class="nav nav-tabs border-tab mb-4" role="tablist">
                <li class="nav-item" v-for="tab in tabs" :key="tab.key">
                  <a
                    class="nav-link"
                    :class="{ active: activeTab === tab.key }"
                    @click.prevent="activeTab = tab.key"
                    href="#"
                  >
                    <i :class="tab.icon" class="me-2"></i>{{ tab.label }}
                  </a>
                </li>
              </ul>

              <!-- Property Types -->
              <div v-show="activeTab === 'property-types'">
                <DataTable
                  title="Property Types"
                  :headers="ptHeaders"
                  :items="referenceStore.propertyTypes"
                  :loading="ptLoading"
                  :searchable="false"
                >
                  <template #header-actions>
                    <button class="btn btn-primary" @click="openPtCreate">
                      <i class="fa fa-plus me-1"></i>Add Property Type
                    </button>
                  </template>
                  <template #cell-actions="{ row }">
                    <div class="d-flex gap-2 justify-content-center">
                      <button class="btn btn-sm btn-outline-primary" @click="openPtEdit(row.original)">
                        <i class="fa fa-pencil"></i>
                      </button>
                      <button class="btn btn-sm btn-outline-danger" @click="handlePtDelete(row.original)">
                        <i class="fa fa-trash"></i>
                      </button>
                    </div>
                  </template>
                </DataTable>
              </div>

              <!-- Provinces -->
              <div v-show="activeTab === 'provinces'">
                <DataTable
                  title="Provinces"
                  :headers="provinceHeaders"
                  :items="referenceStore.provinces"
                  :loading="provLoading"
                  :searchable="false"
                >
                  <template #header-actions>
                    <button class="btn btn-primary" @click="openProvCreate">
                      <i class="fa fa-plus me-1"></i>Add Province
                    </button>
                  </template>
                  <template #cell-actions="{ row }">
                    <div class="d-flex gap-2 justify-content-center">
                      <button class="btn btn-sm btn-outline-primary" @click="openProvEdit(row.original)">
                        <i class="fa fa-pencil"></i>
                      </button>
                      <button class="btn btn-sm btn-outline-danger" @click="handleProvDelete(row.original)">
                        <i class="fa fa-trash"></i>
                      </button>
                    </div>
                  </template>
                </DataTable>
              </div>

              <!-- Districts -->
              <div v-show="activeTab === 'districts'">
                <DataTable
                  title="Districts"
                  :headers="districtHeaders"
                  :items="referenceStore.districts"
                  :loading="distLoading"
                  :searchable="false"
                >
                  <template #header-actions>
                    <button class="btn btn-primary" @click="openDistCreate">
                      <i class="fa fa-plus me-1"></i>Add District
                    </button>
                  </template>
                  <template #cell-province="{ row }">
                    {{ getProvinceName(row.original.province_id) }}
                  </template>
                  <template #cell-actions="{ row }">
                    <div class="d-flex gap-2 justify-content-center">
                      <button class="btn btn-sm btn-outline-primary" @click="openDistEdit(row.original)">
                        <i class="fa fa-pencil"></i>
                      </button>
                      <button class="btn btn-sm btn-outline-danger" @click="handleDistDelete(row.original)">
                        <i class="fa fa-trash"></i>
                      </button>
                    </div>
                  </template>
                </DataTable>
              </div>

              <!-- Constituencies -->
              <div v-show="activeTab === 'constituencies'">
                <DataTable
                  title="Constituencies"
                  :headers="constHeaders"
                  :items="referenceStore.constituencies"
                  :loading="constLoading"
                  :searchable="false"
                >
                  <template #header-actions>
                    <button class="btn btn-primary" @click="openConstCreate">
                      <i class="fa fa-plus me-1"></i>Add Constituency
                    </button>
                  </template>
                  <template #cell-district="{ row }">
                    {{ getDistrictName(row.original.district_id) }}
                  </template>
                  <template #cell-actions="{ row }">
                    <div class="d-flex gap-2 justify-content-center">
                      <button class="btn btn-sm btn-outline-primary" @click="openConstEdit(row.original)">
                        <i class="fa fa-pencil"></i>
                      </button>
                      <button class="btn btn-sm btn-outline-danger" @click="handleConstDelete(row.original)">
                        <i class="fa fa-trash"></i>
                      </button>
                    </div>
                  </template>
                </DataTable>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Property Type Modal -->
    <div class="modal fade" id="ptModal" tabindex="-1" ref="ptModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ ptForm.id ? 'Edit' : 'Add' }} Property Type</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handlePtSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="ptForm.name"
                  :class="ptMutation.getFieldError('name') ? 'is-invalid' : ''" required />
                <div class="invalid-feedback" v-if="ptMutation.getFieldError('name')">
                  {{ ptMutation.getFieldError('name') }}
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea class="form-control" v-model="ptForm.description" rows="3"></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="ptMutation.isPending.value">
                <span v-if="ptMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ ptForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Province Modal -->
    <div class="modal fade" id="provModal" tabindex="-1" ref="provModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ provForm.id ? 'Edit' : 'Add' }} Province</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleProvSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="provForm.name"
                  :class="provMutation.getFieldError('name') ? 'is-invalid' : ''" required />
                <div class="invalid-feedback" v-if="provMutation.getFieldError('name')">
                  {{ provMutation.getFieldError('name') }}
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="provMutation.isPending.value">
                <span v-if="provMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ provForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- District Modal -->
    <div class="modal fade" id="distModal" tabindex="-1" ref="distModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ distForm.id ? 'Edit' : 'Add' }} District</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleDistSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Province <span class="text-danger">*</span></label>
                <select class="form-select" v-model="distForm.province_id" required>
                  <option :value="undefined">Select Province</option>
                  <option v-for="p in referenceStore.provinces" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="distForm.name"
                  :class="distMutation.getFieldError('name') ? 'is-invalid' : ''" required />
                <div class="invalid-feedback" v-if="distMutation.getFieldError('name')">
                  {{ distMutation.getFieldError('name') }}
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="distMutation.isPending.value">
                <span v-if="distMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ distForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Constituency Modal -->
    <div class="modal fade" id="constModal" tabindex="-1" ref="constModalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ constForm.id ? 'Edit' : 'Add' }} Constituency</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="handleConstSave">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">District <span class="text-danger">*</span></label>
                <select class="form-select" v-model="constForm.district_id" required>
                  <option :value="undefined">Select District</option>
                  <option v-for="d in referenceStore.districts" :key="d.id" :value="d.id">{{ d.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="constForm.name"
                  :class="constMutation.getFieldError('name') ? 'is-invalid' : ''" required />
                <div class="invalid-feedback" v-if="constMutation.getFieldError('name')">
                  {{ constMutation.getFieldError('name') }}
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="constMutation.isPending.value">
                <span v-if="constMutation.isPending.value" class="spinner-border spinner-border-sm me-2"></span>
                {{ constForm.id ? 'Update' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BreadCrumbs from '~/components/breadCrumbs.vue'
import DataTable from '~/components/tables/DataTable.vue'
import { Modal } from 'bootstrap'

definePageMeta({
  name: 'reference-data',
  path: '/reference/property-types',
  layout: 'default',
  middleware: 'auth',
  requiresAuth: true,
  public: false,
})

const { setBreadcrumbs } = useBreadcrumbs()
setBreadcrumbs([
  { title: 'Home', url: '/dashboard' },
  { title: 'Reference Data', active: true },
])

const referenceStore = useReferenceStore()
const {
  useFetchPropertyTypesQuery, useCreatePropertyTypeMutation, useUpdatePropertyTypeMutation, useDeletePropertyTypeMutation,
  useFetchProvincesQuery, useCreateProvinceMutation, useUpdateProvinceMutation, useDeleteProvinceMutation,
  useFetchDistrictsQuery, useCreateDistrictMutation, useUpdateDistrictMutation, useDeleteDistrictMutation,
  useFetchConstituenciesQuery, useCreateConstituencyMutation, useUpdateConstituencyMutation, useDeleteConstituencyMutation,
} = useReference()

const tabs = [
  { key: 'property-types', label: 'Property Types', icon: 'fa fa-building-o' },
  { key: 'provinces', label: 'Provinces', icon: 'fa fa-map' },
  { key: 'districts', label: 'Districts', icon: 'fa fa-map-marker' },
  { key: 'constituencies', label: 'Constituencies', icon: 'fa fa-location-arrow' },
]
const activeTab = ref('property-types')

// Fetch all on mount
const { isLoading: ptLoading } = useFetchPropertyTypesQuery()
const { isLoading: provLoading } = useFetchProvincesQuery()
const { isLoading: distLoading } = useFetchDistrictsQuery()
const { isLoading: constLoading } = useFetchConstituenciesQuery()

// Table headers
const ptHeaders = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'name', title: 'Name' },
  { key: 'slug', title: 'Slug' },
  { key: 'actions', title: 'Actions', align: 'center', width: 100 },
]
const provinceHeaders = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'name', title: 'Name' },
  { key: 'actions', title: 'Actions', align: 'center', width: 100 },
]
const districtHeaders = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'name', title: 'Name' },
  { key: 'province', title: 'Province' },
  { key: 'actions', title: 'Actions', align: 'center', width: 100 },
]
const constHeaders = [
  { key: 'id', title: 'ID', width: 60 },
  { key: 'name', title: 'Name' },
  { key: 'district', title: 'District' },
  { key: 'actions', title: 'Actions', align: 'center', width: 100 },
]

// Helper lookups
const getProvinceName = (id: number) => referenceStore.provinces.find(p => p.id === id)?.name ?? '—'
const getDistrictName = (id: number) => referenceStore.districts.find(d => d.id === id)?.name ?? '—'

// ─── Property Types ────────────────────────────────────────────────────────

const ptModalEl = ref<HTMLElement | null>(null)
let ptModalInstance: Modal | null = null
const ptForm = ref<any>({ id: null, name: '', description: '' })

const createPtMutation = useCreatePropertyTypeMutation()
const updatePtMutation = useUpdatePropertyTypeMutation()
const ptMutation = computed(() => ptForm.value.id ? updatePtMutation : createPtMutation)

const openPtCreate = () => { ptForm.value = { id: null, name: '', description: '' }; createPtMutation.reset(); ptModalInstance?.show() }
const openPtEdit = (row: any) => { ptForm.value = { id: row.id, name: row.name, description: row.description || '' }; updatePtMutation.reset(); ptModalInstance?.show() }
const handlePtSave = async () => {
  try {
    const { id, ...data } = ptForm.value
    if (id) await updatePtMutation.mutateAsync({ id, data })
    else await createPtMutation.mutateAsync(data)
    ptModalInstance?.hide()
  } catch { /* mutation handles errors */ }
}
const handlePtDelete = async (row: any) => {
  if (confirm(`Delete property type "${row.name}"?`)) await useDeletePropertyTypeMutation().mutateAsync(row.id)
}

// ─── Provinces ─────────────────────────────────────────────────────────────

const provModalEl = ref<HTMLElement | null>(null)
let provModalInstance: Modal | null = null
const provForm = ref<any>({ id: null, name: '' })

const createProvMutation = useCreateProvinceMutation()
const updateProvMutation = useUpdateProvinceMutation()
const provMutation = computed(() => provForm.value.id ? updateProvMutation : createProvMutation)

const openProvCreate = () => { provForm.value = { id: null, name: '' }; createProvMutation.reset(); provModalInstance?.show() }
const openProvEdit = (row: any) => { provForm.value = { id: row.id, name: row.name }; updateProvMutation.reset(); provModalInstance?.show() }
const handleProvSave = async () => {
  try {
    const { id, ...data } = provForm.value
    if (id) await updateProvMutation.mutateAsync({ id, data })
    else await createProvMutation.mutateAsync(data)
    provModalInstance?.hide()
  } catch { /* mutation handles errors */ }
}
const handleProvDelete = async (row: any) => {
  if (confirm(`Delete province "${row.name}"?`)) await useDeleteProvinceMutation().mutateAsync(row.id)
}

// ─── Districts ─────────────────────────────────────────────────────────────

const distModalEl = ref<HTMLElement | null>(null)
let distModalInstance: Modal | null = null
const distForm = ref<any>({ id: null, name: '', province_id: undefined })

const createDistMutation = useCreateDistrictMutation()
const updateDistMutation = useUpdateDistrictMutation()
const distMutation = computed(() => distForm.value.id ? updateDistMutation : createDistMutation)

const openDistCreate = () => { distForm.value = { id: null, name: '', province_id: undefined }; createDistMutation.reset(); distModalInstance?.show() }
const openDistEdit = (row: any) => { distForm.value = { id: row.id, name: row.name, province_id: row.province_id }; updateDistMutation.reset(); distModalInstance?.show() }
const handleDistSave = async () => {
  try {
    const { id, ...data } = distForm.value
    if (id) await updateDistMutation.mutateAsync({ id, data })
    else await createDistMutation.mutateAsync(data)
    distModalInstance?.hide()
  } catch { /* mutation handles errors */ }
}
const handleDistDelete = async (row: any) => {
  if (confirm(`Delete district "${row.name}"?`)) await useDeleteDistrictMutation().mutateAsync(row.id)
}

// ─── Constituencies ────────────────────────────────────────────────────────

const constModalEl = ref<HTMLElement | null>(null)
let constModalInstance: Modal | null = null
const constForm = ref<any>({ id: null, name: '', district_id: undefined })

const createConstMutation = useCreateConstituencyMutation()
const updateConstMutation = useUpdateConstituencyMutation()
const constMutation = computed(() => constForm.value.id ? updateConstMutation : createConstMutation)

const openConstCreate = () => { constForm.value = { id: null, name: '', district_id: undefined }; createConstMutation.reset(); constModalInstance?.show() }
const openConstEdit = (row: any) => { constForm.value = { id: row.id, name: row.name, district_id: row.district_id }; updateConstMutation.reset(); constModalInstance?.show() }
const handleConstSave = async () => {
  try {
    const { id, ...data } = constForm.value
    if (id) await updateConstMutation.mutateAsync({ id, data })
    else await createConstMutation.mutateAsync(data)
    constModalInstance?.hide()
  } catch { /* mutation handles errors */ }
}
const handleConstDelete = async (row: any) => {
  if (confirm(`Delete constituency "${row.name}"?`)) await useDeleteConstituencyMutation().mutateAsync(row.id)
}

// ─── Mount modals ─────────────────────────────────────────────────────────

onMounted(() => {
  if (ptModalEl.value) ptModalInstance = new Modal(ptModalEl.value)
  if (provModalEl.value) provModalInstance = new Modal(provModalEl.value)
  if (distModalEl.value) distModalInstance = new Modal(distModalEl.value)
  if (constModalEl.value) constModalInstance = new Modal(constModalEl.value)
})

onBeforeUnmount(() => {
  ptModalInstance?.dispose()
  provModalInstance?.dispose()
  distModalInstance?.dispose()
  constModalInstance?.dispose()
})
</script>

<style scoped>
.nav-tabs .nav-link { cursor: pointer; }
</style>

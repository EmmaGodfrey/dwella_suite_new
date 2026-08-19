export interface BreadcrumbItem {
  title: string
  url?: string
  active?: boolean
}

const breadcrumbs = ref<BreadcrumbItem[]>([])

export const useBreadcrumbs = () => {
  const setBreadcrumbs = (items: BreadcrumbItem[]) => {
    breadcrumbs.value = items
  }

  return {
    breadcrumbs: readonly(breadcrumbs),
    setBreadcrumbs,
  }
}

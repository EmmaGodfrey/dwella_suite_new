import { defineStore, acceptHMRUpdate } from 'pinia'

// ─── Types matching /auth/me response ───────────────────────────────────────

export interface SystemPermissions {
  admin_access: boolean
  admin_user_read: boolean
  admin_user_create: boolean
  admin_user_update: boolean
  admin_user_delete: boolean
  admin_listing_read: boolean
  admin_listing_approve: boolean
  admin_listing_reject: boolean
  admin_listing_publish: boolean
  admin_listing_archive: boolean
  admin_listing_delete: boolean
  admin_organization_read: boolean
  admin_organization_create: boolean
  admin_organization_update: boolean
  admin_organization_verify: boolean
  admin_organization_suspend: boolean
  admin_organization_activate: boolean
  admin_organization_delete: boolean
  admin_application_read: boolean
  admin_verification_read: boolean
  admin_verification_approve: boolean
  admin_verification_reject: boolean
  admin_verification_revoke: boolean
  admin_verification_plan_read: boolean
  admin_verification_plan_create: boolean
  admin_verification_plan_update: boolean
  admin_verification_plan_delete: boolean
  admin_subscription_read: boolean
  admin_subscription_cancel: boolean
  admin_subscription_reactivate: boolean
  admin_subscription_plan_read: boolean
  admin_subscription_plan_create: boolean
  admin_subscription_plan_update: boolean
  admin_subscription_plan_delete: boolean
  admin_payment_read: boolean
  admin_ref_data_read: boolean
  admin_ref_data_create: boolean
  admin_ref_data_update: boolean
  admin_ref_data_delete: boolean
  admin_amenity_read: boolean
  admin_amenity_create: boolean
  admin_amenity_update: boolean
  admin_amenity_delete: boolean
  admin_setting_read: boolean
  admin_setting_update: boolean
  admin_notification_read: boolean
  admin_notification_send: boolean
  [key: string]: boolean
}

export interface OrgPermissions {
  listing_read: boolean
  listing_create: boolean
  listing_update: boolean
  listing_submit: boolean
  listing_delete: boolean
  listing_publish: boolean
  listing_archive: boolean
  application_read: boolean
  application_update_status: boolean
  lease_read: boolean
  lease_create: boolean
  lease_update: boolean
  lease_renew: boolean
  lease_terminate: boolean
  maintenance_read: boolean
  maintenance_create: boolean
  maintenance_update: boolean
  team_read: boolean
  team_create: boolean
  team_update: boolean
  team_delete: boolean
  subscription_read: boolean
  subscription_create: boolean
  subscription_upgrade: boolean
  subscription_cancel: boolean
  organization_read: boolean
  organization_update: boolean
  organization_delete: boolean
  [key: string]: boolean
}

export interface Organization {
  id: number
  name: string
  type: 'agency' | 'landlord'
  is_verified: boolean
  org_role: 'owner' | 'manager' | 'member'
  status: 'active' | 'invited' | 'removed'
  has_subscription: boolean
  permissions: OrgPermissions
}

export interface AuthUser {
  id: number
  full_name: string
  email: string
  phone: string
  is_admin: boolean
  is_lister: boolean
  system_roles: string[]
  permissions: SystemPermissions
  organizations: Organization[]
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useAuthStore = defineStore('auth', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const user = ref<AuthUser | null>(null)
  const token = ref<string | null>(null)
  const activeOrg = ref<Organization | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const isLister = computed(() => user.value?.is_lister ?? false)
  const orgs = computed(() => user.value?.organizations ?? [])

  // ─── Persist / hydrate ────────────────────────────────────────────────────

  function _persist() {
    if (!process.client) return
    sessionStorage.setItem('authToken', token.value ?? '')
    sessionStorage.setItem('authUser', JSON.stringify(user.value))
    sessionStorage.setItem('authActiveOrg', JSON.stringify(activeOrg.value))
  }

  function initAuth() {
    if (!process.client) return
    const storedToken = sessionStorage.getItem('authToken')
    const storedUser = sessionStorage.getItem('authUser')
    const storedOrg = sessionStorage.getItem('authActiveOrg')

    if (storedToken) token.value = storedToken

    if (storedUser) {
      try { user.value = JSON.parse(storedUser) } catch { /* ignore */ }
    }

    if (storedOrg) {
      try { activeOrg.value = JSON.parse(storedOrg) } catch { /* ignore */ }
    }
  }

  // ─── fetchMe ──────────────────────────────────────────────────────────────

  async function fetchMe() {
    const response = await $api.get('/auth/me')
    if (response.success && response.data) {
      user.value = response.data
      // Auto-set active org if none selected and user has orgs
      if (!activeOrg.value && response.data.organizations?.length) {
        activeOrg.value = response.data.organizations[0]
      }
      _persist()
    }
    return response
  }

  // ─── Login ────────────────────────────────────────────────────────────────

  async function login(credentials: { email: string; password: string }) {
    const response = await $api.post('/auth/login', credentials)

    if (response.success && response.data?.token) {
      token.value = response.data.token
      if (process.client) {
        sessionStorage.setItem('authToken', response.data.token)
      }
      await fetchMe()
    }

    return response
  }

  // ─── Logout ───────────────────────────────────────────────────────────────

  async function logout() {
    try {
      await $api.post('/auth/logout')
    } catch { /* ignore */ }
    finally {
      user.value = null
      token.value = null
      activeOrg.value = null
      if (process.client) {
        sessionStorage.removeItem('authToken')
        sessionStorage.removeItem('authUser')
        sessionStorage.removeItem('authActiveOrg')
        sessionStorage.removeItem('authPermissions')
      }
      await navigateTo('/login', { replace: true })
    }
  }

  // ─── Org ──────────────────────────────────────────────────────────────────

  function setActiveOrg(org: Organization) {
    activeOrg.value = org
    _persist()
  }

  // ─── Permission check ─────────────────────────────────────────────────────

  function can(key: string): boolean {
    const sysPerm = user.value?.permissions?.[key]
    const orgPerm = activeOrg.value?.permissions?.[key]
    // org-scoped first, then system-level
    return orgPerm ?? sysPerm ?? false
  }

  // Keep old hasPermission for backward compatibility
  function hasPermission(key: string): boolean {
    return can(key)
  }

  // ─── Init on store creation ───────────────────────────────────────────────
  initAuth()

  return {
    user,
    token,
    activeOrg,
    orgs,
    isAuthenticated,
    isAdmin,
    isLister,
    login,
    logout,
    fetchMe,
    setActiveOrg,
    can,
    hasPermission,
    initAuth,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}

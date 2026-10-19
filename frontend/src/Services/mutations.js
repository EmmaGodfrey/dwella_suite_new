import { useMutation } from "@tanstack/react-query";

import {
  confirmPasswordReset,
  disableTwoFactor,
  login,
  requestPasswordReset,
  startTwoFactorSetup,
  submitIdentityVerification,
  updateProfile,
  uploadAvatar,
  verifyTwoFactorLogin,
  verifyTwoFactorSetup,
} from "./auth";
import { api } from "./apiClient";
import { queryClient } from "./queryClient";
import { queryKeys } from "./queryKeys";

export function useLoginMutation(options = {}) {
  return useMutation({
    mutationFn: login,
    onSuccess: (data, variables, context) => {
      if (data.user && data.token) {
        queryClient.setQueryData(queryKeys.currentUser, data.user);
      }
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useTwoFactorLoginMutation(options = {}) {
  return useMutation({
    mutationFn: verifyTwoFactorLogin,
    onSuccess: (data, variables, context) => {
      queryClient.setQueryData(queryKeys.currentUser, data.user);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function usePasswordResetRequestMutation(options = {}) {
  return useMutation({
    mutationFn: requestPasswordReset,
    onSuccess: options.onSuccess,
    onError: options.onError,
  });
}

export function usePasswordResetConfirmMutation(options = {}) {
  return useMutation({
    mutationFn: confirmPasswordReset,
    onSuccess: options.onSuccess,
    onError: options.onError,
  });
}

export function useTwoFactorSetupMutation(options = {}) {
  return useMutation({
    mutationFn: startTwoFactorSetup,
    onSuccess: options.onSuccess,
    onError: options.onError,
  });
}

export function useTwoFactorSetupVerifyMutation(options = {}) {
  return useMutation({
    mutationFn: verifyTwoFactorSetup,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useTwoFactorDisableMutation(options = {}) {
  return useMutation({
    mutationFn: disableTwoFactor,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useProfileUpdateMutation(options = {}) {
  return useMutation({
    mutationFn: updateProfile,
    onSuccess: (data, variables, context) => {
      queryClient.setQueryData(queryKeys.currentUser, data);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useAvatarUploadMutation(options = {}) {
  return useMutation({
    mutationFn: uploadAvatar,
    onSuccess: (data, variables, context) => {
      queryClient.setQueryData(queryKeys.currentUser, data);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useIdentityVerificationMutation(options = {}) {
  return useMutation({
    mutationFn: submitIdentityVerification,
    onSuccess: (data, variables, context) => {
      queryClient.setQueryData(queryKeys.currentUser, data);
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useSavePropertyMutation(options = {}) {
  return useMutation({
    mutationKey: ["saveProperty"],
    mutationFn: ({ id, payload }) => id ? api.patch(`/properties/${id}/`, payload) : api.post("/properties/", payload),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useSaveUnitMutation(options = {}) {
  return useMutation({
    mutationKey: ["saveUnit"],
    mutationFn: ({ id, payload }) => id
      ? api.patch(`/properties/units/${id}/`, payload)
      : api.post("/properties/units/", payload),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

// A lease touches the unit's occupancy and the tenant's status, so every lease
// or tenant write refreshes all three lists plus the dashboard figures.
const invalidateTenancy = () => {
  queryClient.invalidateQueries({ queryKey: ["tenants"] });
  queryClient.invalidateQueries({ queryKey: ["leases"] });
  queryClient.invalidateQueries({ queryKey: ["properties"] });
  queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
};

export function useSaveTenantMutation(options = {}) {
  return useMutation({
    mutationKey: ["saveTenant"],
    mutationFn: ({ id, payload }) => id ? api.patch(`/tenants/${id}/`, payload) : api.post("/tenants/", payload),
    onSuccess: (data, variables, context) => {
      invalidateTenancy();
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useSaveLeaseMutation(options = {}) {
  return useMutation({
    mutationKey: ["saveLease"],
    mutationFn: ({ id, payload }) => id ? api.patch(`/leases/${id}/`, payload) : api.post("/leases/", payload),
    onSuccess: (data, variables, context) => {
      invalidateTenancy();
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

export function useLeaseActionMutation(options = {}) {
  return useMutation({
    mutationKey: ["leaseAction"],
    mutationFn: ({ id, action }) => api.post(`/leases/${id}/${action}/`),
    onSuccess: (data, variables, context) => {
      invalidateTenancy();
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

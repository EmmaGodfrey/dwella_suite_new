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

export function useCreatePropertyMutation(options = {}) {
  return useMutation({
    mutationFn: (payload) => api.post("/properties/", payload),
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboardSummary });
      options.onSuccess?.(data, variables, context);
    },
    onError: options.onError,
  });
}

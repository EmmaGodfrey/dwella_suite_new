import { api, setAuthToken } from "./apiClient";

export async function login({ email, password }) {
  const response = await api.post("/accounts/login/", { email, password });
  if (response.two_factor_required) {
    return response;
  }

  setAuthToken(response.token);
  localStorage.setItem("dwella_user", JSON.stringify(response.user));
  return response;
}

export async function verifyTwoFactorLogin({ challengeToken, code }) {
  const response = await api.post("/accounts/login/2fa/", {
    challenge_token: challengeToken,
    code,
  });
  setAuthToken(response.token);
  localStorage.setItem("dwella_user", JSON.stringify(response.user));
  return response;
}

export async function requestPasswordReset({ email }) {
  return api.post("/accounts/password-reset/", { email });
}

export async function confirmPasswordReset({ uid, token, password }) {
  return api.post("/accounts/password-reset/confirm/", { uid, token, password });
}

export async function startTwoFactorSetup() {
  return api.post("/accounts/2fa/setup/", {});
}

export async function verifyTwoFactorSetup({ code }) {
  return api.post("/accounts/2fa/verify/", { code });
}

export async function disableTwoFactor() {
  return api.post("/accounts/2fa/disable/", {});
}

export async function updateProfile(payload) {
  const user = await api.patch("/accounts/me/", payload);
  localStorage.setItem("dwella_user", JSON.stringify(user));
  return user;
}

export async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append("avatar", file);
  const user = await api.post("/accounts/me/avatar/", formData);
  localStorage.setItem("dwella_user", JSON.stringify(user));
  return user;
}

export async function submitIdentityVerification(payload) {
  const formData = new FormData();
  formData.append("legal_name", payload.legalName);
  formData.append("document_type", payload.documentType);
  formData.append("document_number", payload.documentNumber);
  formData.append("document_image", payload.documentImage);
  const user = await api.post("/accounts/me/verification/", formData);
  localStorage.setItem("dwella_user", JSON.stringify(user));
  return user;
}

export function logout() {
  setAuthToken(null);
  localStorage.removeItem("dwella_user");
}

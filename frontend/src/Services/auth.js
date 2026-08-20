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

export function logout() {
  setAuthToken(null);
  localStorage.removeItem("dwella_user");
}

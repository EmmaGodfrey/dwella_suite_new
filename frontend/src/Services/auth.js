import { api, setAuthToken } from "./apiClient";

export async function login({ email, password }) {
  const response = await api.post("/accounts/login/", { email, password });
  setAuthToken(response.token);
  localStorage.setItem("dwella_user", JSON.stringify(response.user));
  return response;
}

export function logout() {
  setAuthToken(null);
  localStorage.removeItem("dwella_user");
}

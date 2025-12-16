import baseAPI from "./baseAPI";

export const loginAPI = (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email || credentials.username);
  formData.append('password', credentials.password);

  return baseAPI.post("/auth/login", formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });
};

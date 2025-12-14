import baseAPI from "./baseAPI";

export const loginAPI = (credentials) => {
  return baseAPI.post("/auth/login", credentials);
};

import axios from "axios";
import Cookies from "js-cookie";
import {
  mockLogin,
  mockCertificates,
  mockHourlyData,
  mockUserMe,
  mockAccounts,
  mockDevices,
  mockStorageRecords,
  mockTransferCertificate,
  mockCancelCertificate,
  mockCreateCertificate
} from "./completeMockAPI";

// Enable demo mode when backend is unavailable
const DEMO_MODE = false;

const AUTH_LIST = ["/auth/login"];
const CSRF_EXEMPT = ["/csrf-token"];

const baseAPI = axios.create({
  baseURL: "https://my-granular-certificate-registry-production.up.railway.app",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

const fetchCSRFToken = async () => {
  // CSRF disabled for Railway deployment
  return null;
};

// Override axios for demo mode
if (DEMO_MODE) {
  baseAPI.interceptors.request.use((config) => {
    // Block all real API calls in demo mode
    return Promise.reject({
      code: 'DEMO_MODE',
      config: config,
      message: 'Demo mode - using mock data'
    });
  });
}

baseAPI.interceptors.request.use(
  async (config) => {
    const isAuthRoute = AUTH_LIST.some((route) => config.url?.includes(route));
    const isCSRFExempt = CSRF_EXEMPT.some((route) =>
      config.url?.includes(route)
    );

    if (!isAuthRoute) {
      let token = Cookies.get("access_token");
      if (!token) {
        token = localStorage.getItem("access_token");
      }
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }

    // CSRF disabled for Railway deployment
    // if (!isCSRFExempt && config.method !== "get") {
    //   const csrfToken = await fetchCSRFToken();
    //   if (csrfToken) {
    //     config.headers["X-CSRF-Token"] = csrfToken;
    //   }
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// Check for demo mode in localStorage or environment
const isDemoEnabled = () => {
  return localStorage.getItem('demo_mode') === 'true' || DEMO_MODE;
};

baseAPI.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error(error);
    const url = error.config?.url;
    const isDemo = isDemoEnabled();

    // Demo mode fallback for network errors only
    if (isDemo && error.code === "ERR_NETWORK") {
      console.log(`Demo Mode: Intercepted ${error.response?.status || 'Network'} error for ${url}. Returning mock data.`);

      if (url?.includes("/auth/login")) return mockLogin();
      if (url?.includes("/certificate")) return mockCertificates();
      if (url?.includes("/hourly")) return mockHourlyData();
      if (url?.includes("/user/me")) return mockUserMe();
      if (url?.includes("/account")) return mockAccounts();
      if (url?.includes("/device")) return mockDevices();
      if (url?.includes("/storage")) return mockStorageRecords();
      if (url?.includes("/transfer")) return mockTransferCertificate();
      if (url?.includes("/create")) return mockCreateCertificate();
    }

    // Standard redirect logic (only if not in demo mode)
    if (!isDemo) {
      if ((error.code === "ERR_NETWORK" || !error.response || error.response?.status === 401) && window.location.pathname !== "/login") {
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    const status = error.response?.status || 500;
    const message = error.response?.data?.detail || "An unexpected error occurred.";
    return Promise.reject({ status, message });
  }
);

// CSRF disabled for Railway deployment
// fetchCSRFToken().catch(console.error);

export default baseAPI;

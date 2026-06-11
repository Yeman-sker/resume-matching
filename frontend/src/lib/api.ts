import axios from "axios"

const apiBaseURL =
  import.meta.env.VITE_API_BASE_URL ??
  window.location.protocol + "//" + window.location.hostname + ":8002"

const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.message)
    return Promise.reject(error)
  }
)

export default api

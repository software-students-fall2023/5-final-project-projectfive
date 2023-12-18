import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: '/api',
    timeout: 5000, // 设置请求超时时间（单位毫秒）
});

// 请求拦截器
axiosInstance.interceptors.request.use(
    function (config) {
        // 在发送请求之前做些什么
        const token = localStorage.getItem('token'); // 假设你从localStorage中获取用户token
        if (token) {
            config.headers.Authorization = `Bearer ${token}`; // 在请求头中添加授权信息
        }
        return config;
    },
    function (error) {
        // 对请求错误做些什么
        return Promise.reject(error);
    }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
    function (response) {
        // 对响应数据做些什么
        return response;
    },
    function (error) {
        // 对响应错误做些什么
        if (error.response.status === 401) {
            // 处理未登录的情况，跳转至登录页
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default axiosInstance;
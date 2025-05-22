import axios from 'axios';
import {useUserStore} from "@/stores/user"
import {ElMessage} from "element-plus";
import {router} from "@/router";
const baseURL = 'http://localhost:5173';
const instance = axios.create({
  baseURL,
  timeout: 10000,
})

instance.interceptors.request.use(
    (config) => {
        const userStore = useUserStore();
        if (userStore.token) {
            config.headers.Authorization = `Bearer ${userStore.token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
)

instance.interceptors.response.use(
    (response) => {

        return response;
    },
    (error) => {
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    ElMessage.error('请先登录');
                    router.push('/login');
                    break;
                case 403:
                    ElMessage.error('没有权限');
                    break;
                case 404:
                    ElMessage.error('请求的资源不存在');
                    break;
                case 500:
                    ElMessage.error('服务器内部错误');
                    break;
                default:
                    ElMessage.error(error.response.data.message);
                    break;
            }
        }
        ElMessage.error(error.message);
        return Promise.reject(error);
    }
)

export default instance;
export { baseURL };

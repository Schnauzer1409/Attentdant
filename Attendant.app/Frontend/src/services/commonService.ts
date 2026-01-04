import { localService } from "./localService"

export const commonService = {
    isLogin(): boolean {
        const username = localService.get('username')
        const token = localService.get('token')

        if (username && token) return true;

        return false;
    },

    logout() {
        localService.remove('username')
        localService.remove('token')
        localService.remove('role')
    }
}
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const originalFetch = window.fetch.bind(window)
let refreshPromise = null

function clearAuthStorage() {
	localStorage.removeItem('token')
	localStorage.removeItem('role')
	localStorage.removeItem('user_name')
}

async function refreshAccessToken() {
	// Refresh token is sent automatically via HttpOnly cookie
	const response = await originalFetch('/api/auth/refresh', {
		method: 'POST',
		credentials: 'same-origin',
		headers: {
			'Content-Type': 'application/json'
		}
	})

	if (!response.ok) {
		clearAuthStorage()
		return null
	}

	const data = await response.json()
	if (data.access_token) {
		localStorage.setItem('token', data.access_token)
	}
	return data.access_token || null
}

window.fetch = async (input, init = {}) => {
	const options = { ...init }
	const requestUrl = typeof input === 'string' ? input : input.url
	const isAuthRefresh = requestUrl.includes('/api/auth/refresh')

	const headers = new Headers(options.headers || {})
	const accessToken = localStorage.getItem('token')
	if (accessToken && !headers.has('Authorization') && !isAuthRefresh) {
		headers.set('Authorization', `Bearer ${accessToken}`)
	}
	options.headers = headers

	let response = await originalFetch(input, options)

	if (response.status !== 401 || isAuthRefresh || options.__isRetry) {
		return response
	}

	if (!refreshPromise) {
		refreshPromise = refreshAccessToken().finally(() => {
			refreshPromise = null
		})
	}

	const newAccessToken = await refreshPromise
	if (!newAccessToken) {
		return response
	}

	const retryHeaders = new Headers(options.headers || {})
	retryHeaders.set('Authorization', `Bearer ${newAccessToken}`)

	return originalFetch(input, {
		...options,
		headers: retryHeaders,
		__isRetry: true
	})
}

createApp(App).use(router).mount('#app')

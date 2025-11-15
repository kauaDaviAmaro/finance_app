/**
 * Serviço para gerenciar push notifications usando Web Push API
 */

import { apiClient } from './api/apiClient'

let VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY || ''

/**
 * Busca a chave VAPID pública do backend
 */
export async function fetchVapidPublicKey(): Promise<string> {
  if (VAPID_PUBLIC_KEY) {
    return VAPID_PUBLIC_KEY
  }

  try {
    const response = await apiClient.get<{ public_key: string }>('/notifications/vapid-public-key')
    VAPID_PUBLIC_KEY = response.data.public_key
    return VAPID_PUBLIC_KEY
  } catch (error) {
    console.error('Erro ao buscar chave VAPID:', error)
    throw new Error('Não foi possível obter a chave VAPID pública')
  }
}

export interface PushSubscriptionData {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

/**
 * Solicita permissão para notificações
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.warn('Este navegador não suporta notificações')
    return 'denied'
  }

  if (Notification.permission === 'granted') {
    return 'granted'
  }

  if (Notification.permission === 'denied') {
    return 'denied'
  }

  const permission = await Notification.requestPermission()
  return permission
}

/**
 * Registra o service worker
 */
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('Service Workers não são suportados neste navegador')
    return null
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    })
    console.log('Service Worker registrado:', registration)
    return registration
  } catch (error) {
    console.error('Erro ao registrar Service Worker:', error)
    return null
  }
}

/**
 * Converte a chave VAPID de base64 para Uint8Array
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

/**
 * Obtém a subscription de push do usuário
 */
export async function getPushSubscription(
  registration: ServiceWorkerRegistration
): Promise<PushSubscription | null> {
  try {
    const subscription = await registration.pushManager.getSubscription()
    return subscription
  } catch (error) {
    console.error('Erro ao obter subscription:', error)
    return null
  }
}

/**
 * Cria uma nova subscription de push
 */
export async function createPushSubscription(
  registration: ServiceWorkerRegistration
): Promise<PushSubscription | null> {
  // Buscar chave VAPID se não estiver configurada
  if (!VAPID_PUBLIC_KEY) {
    try {
      await fetchVapidPublicKey()
    } catch (error) {
      console.error('Erro ao buscar chave VAPID:', error)
      return null
    }
  }

  if (!VAPID_PUBLIC_KEY) {
    console.error('VAPID_PUBLIC_KEY não configurada')
    return null
  }

  try {
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
    })
    console.log('Push subscription criada:', subscription)
    return subscription
  } catch (error) {
    console.error('Erro ao criar push subscription:', error)
    return null
  }
}

/**
 * Converte PushSubscription para formato enviado ao backend
 */
export function subscriptionToJSON(subscription: PushSubscription): PushSubscriptionData | null {
  if (!subscription) {
    return null
  }

  const key = subscription.getKey('p256dh')
  const auth = subscription.getKey('auth')

  if (!key || !auth) {
    return null
  }

  return {
    endpoint: subscription.endpoint,
    keys: {
      p256dh: btoa(String.fromCharCode(...new Uint8Array(key))),
      auth: btoa(String.fromCharCode(...new Uint8Array(auth)))
    }
  }
}

/**
 * Inicializa push notifications (registra SW e solicita permissão)
 */
export async function initializePushNotifications(): Promise<PushSubscriptionData | null> {
  // 1. Buscar chave VAPID primeiro
  try {
    await fetchVapidPublicKey()
  } catch (error) {
    console.warn('Não foi possível obter chave VAPID. Push notifications podem não funcionar.')
  }

  // 2. Solicitar permissão
  const permission = await requestNotificationPermission()
  if (permission !== 'granted') {
    console.warn('Permissão de notificações negada')
    return null
  }

  // 3. Registrar service worker
  const registration = await registerServiceWorker()
  if (!registration) {
    console.error('Falha ao registrar service worker')
    return null
  }

  // 4. Obter ou criar subscription
  let subscription = await getPushSubscription(registration)
  if (!subscription) {
    subscription = await createPushSubscription(registration)
  }

  if (!subscription) {
    console.error('Falha ao obter/criar subscription')
    return null
  }

  // 5. Converter para formato JSON
  return subscriptionToJSON(subscription)
}

/**
 * Cancela a subscription de push
 */
export async function unsubscribePush(): Promise<boolean> {
  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    
    if (subscription) {
      await subscription.unsubscribe()
      console.log('Push subscription cancelada')
      return true
    }
    return false
  } catch (error) {
    console.error('Erro ao cancelar subscription:', error)
    return false
  }
}


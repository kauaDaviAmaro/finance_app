/**
 * Utilitário para validação de JWT tokens no frontend
 */

interface JWTPayload {
  sub: string
  exp: number
  [key: string]: unknown
}

/**
 * Decodifica um JWT token sem verificar a assinatura
 * (apenas para ler o payload e verificar expiração)
 */
function decodeJWT(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3 || !parts[1]) {
      return null
    }

    // Decodifica o payload (segunda parte do JWT)
    const payload = parts[1]
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(decoded) as JWTPayload
  } catch (error) {
    console.error('Erro ao decodificar JWT:', error)
    return null
  }
}

/**
 * Verifica se um token JWT está expirado
 */
export function isTokenExpired(token: string | null): boolean {
  if (!token) {
    return true
  }

  const payload = decodeJWT(token)
  if (!payload?.exp) {
    return true
  }

  // exp está em segundos Unix timestamp
  const expirationTime = payload.exp * 1000 // Converte para milissegundos
  const currentTime = Date.now()

  // Considera expirado se faltar menos de 1 minuto para expirar
  // (para evitar problemas de timing)
  return currentTime >= expirationTime - 60000
}

/**
 * Verifica se um token JWT é válido (não expirado e formato correto)
 */
export function isTokenValid(token: string | null): boolean {
  if (!token) {
    return false
  }

  const payload = decodeJWT(token)
  if (!payload?.exp) {
    return false
  }

  return !isTokenExpired(token)
}

/**
 * Obtém o tempo restante até a expiração do token em milissegundos
 */
export function getTokenTimeToExpiry(token: string | null): number {
  if (!token) {
    return 0
  }

  const payload = decodeJWT(token)
  if (!payload?.exp) {
    return 0
  }

  const expirationTime = payload.exp * 1000
  const currentTime = Date.now()
  return Math.max(0, expirationTime - currentTime)
}


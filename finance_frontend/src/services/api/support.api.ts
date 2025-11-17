import { apiClient, ApiError } from './apiClient'

export interface SupportMessageCreate {
  email: string
  category: 'general' | 'technical' | 'billing' | 'feature'
  subject: string
  message: string
}

export interface SupportMessage {
  id: number
  user_id?: number | null
  email: string
  category: string
  subject: string
  message: string
  status: string
  admin_response?: string | null
  responded_at?: string | null
  responded_by?: number | null
  created_at: string
  updated_at?: string | null
}

export async function sendSupportMessage(data: SupportMessageCreate): Promise<SupportMessage> {
  try {
    const response = await apiClient.post<SupportMessage>('/support', data)
    return response.data
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(0, 'Erro ao enviar mensagem de suporte')
  }
}





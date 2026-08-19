export interface Notification {
  id: number
  title: string
  message: string
  type?: string
  is_read?: boolean
  sent_at?: string
  created_at: string
  user?: { id: number; full_name: string; email: string }
}

export interface NotificationTemplate {
  id: number
  name: string
  title: string
  message: string
  type?: string
  created_at?: string
}

export interface BulkPushInput {
  title: string
  message: string
  user_ids?: number[]
  send_to_all: boolean
}

import api from './axios';

export async function bootstrapMessenger() {
  const { data } = await api.get('/messenger/bootstrap');
  return data;
}

export async function fetchMessengerDirectory() {
  const { data } = await api.get('/messenger/directory');
  return data;
}

export async function fetchMessengerUnreadCount() {
  const { data } = await api.get('/messenger/unread-count');
  return data;
}

export async function fetchMessengerConversations() {
  const { data } = await api.get('/messenger/conversations');
  return data;
}

export async function fetchMessengerMessages(conversationId) {
  const { data } = await api.get(`/messenger/conversations/${conversationId}/messages`);
  return data;
}

export async function createDirectConversation(recipientId) {
  const { data } = await api.post('/messenger/conversations/direct', {
    recipient_id: recipientId,
  });
  return data;
}

export async function createCustomConversation(title, memberIds) {
  const { data } = await api.post('/messenger/conversations/custom', {
    title,
    member_ids: memberIds,
  });
  return data;
}

export async function sendMessengerMessage(conversationId, content) {
  const { data } = await api.post(`/messenger/conversations/${conversationId}/messages`, {
    content,
  });
  return data;
}

export async function markMessengerConversationRead(conversationId) {
  const { data } = await api.post(`/messenger/conversations/${conversationId}/read`);
  return data;
}

export async function uploadMessengerAttachment(conversationId, file, caption = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (caption) {
    formData.append('caption', caption);
  }
  const { data } = await api.post(
    `/messenger/conversations/${conversationId}/attachments`,
    formData
  );
  return data;
}


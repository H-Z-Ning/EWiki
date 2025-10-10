import axios from 'axios'

const instance = axios.create({ baseURL: '/api' })

export const listProjects = () => instance.get<string[]>('/projects').then(r => r.data)

// 只在这里添加 language 参数
export const importProject = (path: string, language: string = 'zh') =>
  instance.post('/import', { path, language }).then(r => r.data)

// 添加上传接口，支持语言参数
export const uploadProject = (file: File, language: string = 'zh') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('language', language)

  return instance.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(r => r.data)
}

// 其他 API 保持不变
export const getProjectReadme = (project: string) =>
  instance.get<{ content: string }>(`/${project}/project`).then(r => r.data.content)

export const listModules = (project: string) =>
  instance.get<string[]>(`/${project}/modules`).then(r => r.data)

export const getModule = (project: string, name: string) =>
  instance.get<{ content: string }>(`/${project}/modules/${name}`).then(r => r.data.content)

export const chat = (project: string, question: string, history: any[] = []) =>
  instance.post(`/${project}/chat`, { question, history }).then(r => r.data.answer)

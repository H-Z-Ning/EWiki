import axios from 'axios'

const instance = axios.create({ baseURL: '/api' })

export const listProjects = () => instance.get<string[]>('/projects').then(r => r.data)
export const importProject = (path: string) =>
  instance.post('/import', { path }).then(r => r.data)

export const getProjectReadme = (project: string) =>
  instance.get<{ content: string }>(`/${project}/project`).then(r => r.data.content)

export const listModules = (project: string) =>
  instance.get<string[]>(`/${project}/modules`).then(r => r.data)

export const getModule = (project: string, name: string) =>
  instance.get<{ content: string }>(`/${project}/modules/${name}`).then(r => r.data.content)

export const chat = (project: string, question: string, history: any[] = []) =>
  instance.post(`/${project}/chat`, { question, history }).then(r => r.data.answer)
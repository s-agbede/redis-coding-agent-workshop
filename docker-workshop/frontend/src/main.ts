import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { loadWorkshopConfig } from './utils/workshopConfig'
import { initLanguageStore } from './store/language'

// Bootstrap language store from config before mounting
loadWorkshopConfig().then(config => {
  const { languages, defaultLanguage } = config.backend || {}
  initLanguageStore(languages, defaultLanguage)
}).catch(() => {
  initLanguageStore(['python'], 'python')
})

createApp(App)
  .use(router)
  .mount('#app')

// Synthetic mount boundary only. History uses unmodified production composable + HTTP.
import { createApp, reactive, nextTick } from 'vue'
import PersonalWorkspace from '/@fs/__WEB__/src/components/workspace/PersonalWorkspace.vue'
import { createApi } from '/@fs/__WEB__/src/composables/useHttp.js'
export const auth = reactive({ authorizationGeneration: 1, oauthClientId: 'client-a', token: async () => window.__historyTokens[window.__historyIdentity] })
export const globalStore = reactive({ user: { id: 'ownerA' } })
const transport = createApi('/agent')
window.__historyIdentity = 'ownerA'
window.__ancillary = []
window.__unexpected = []
export const api = { execute: async options => {
  if (options.url === '/personal-workspace/executions' && options.method === 'GET') return transport.execute({ ...options, authStore: auth, rum: false })
  // Explicitly outside this read-only history test: file list, roster, capabilities.
  const ancillary = {
    '/personal-workspace/files': { items: [], nextCursor: null },
    '/roster': [],
    '/personal-workspace/executions/capabilities': { allowedMimeTypes: [], inputMimeTypes: [], generationEnabled: false }
  }
  if (Object.hasOwn(ancillary, options.url)) { window.__ancillary.push(options.url); return ancillary[options.url] }
  window.__unexpected.push(options.url); throw new Error('Out-of-scope operation: ' + options.url)
} }
window.__switchHistoryIdentity = async identity => {
  window.__historyIdentity = identity
  globalStore.user = { id: identity }
  auth.authorizationGeneration++
  // Snapshot synchronous production cleanup BEFORE requesting the next identity.
  const cleared = window.__historyExecution.history.value.length === 0
  await nextTick()
  return cleared
}
createApp(PersonalWorkspace).mount('#app')

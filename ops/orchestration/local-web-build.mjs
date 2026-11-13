// Keep the exact source Vite configuration; only avoid duplicating public assets
// on this almost-full host. The packager includes every public file unchanged.
import { pathToFileURL } from 'node:url'
import { writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
const [source, output] = process.argv.slice(2)
const { build, loadEnv } = await import(pathToFileURL(`${source}/node_modules/vite/dist/node/index.js`))
// Deployment-specific public OAuth configuration must be supplied externally.
const runtimeConfig = loadEnv('production', source, 'VITE_')
for (const key of ['VITE_API_BASE_URL', 'VITE_OAUTH_CLIENT_ID']) {
  if (!runtimeConfig[key]?.trim()) throw new Error(`Missing production deployment configuration: ${key}`)
}
writeFileSync(join(dirname(output), 'runtime-config.json'), JSON.stringify(runtimeConfig, null, 2), { mode: 0o600 })
// Vite bundle loader writes node_modules/.vite-temp; runner keeps the shared set untouched.
await build({ configLoader: 'runner', root: source, cacheDir: `${output}-vite-cache`, build: { outDir: output, copyPublicDir: false, emptyOutDir: false } })

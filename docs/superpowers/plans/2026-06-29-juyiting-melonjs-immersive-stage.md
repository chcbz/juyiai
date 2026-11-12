# Juyi Hall melonJS Immersive Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make melonJS the primary Juyi Hall stage by loading Tiled map data, rendering spritesheet agents with animation states, and routing stage clicks/feedback through the melonJS canvas while keeping Vue business panels intact.

**Architecture:** Add a small TMX parser and scene config adapter under `web/src/game/`, use it from `JuyitingGame` and `HallScene`, and keep Vue as the business shell. `useHallScene` remains the source of business-derived agent/hotspot state, while melonJS owns canvas rendering, hit detection, sprite animation, and stage feedback.

**Tech Stack:** Vue 3.5, Vite 6, melonJS 15.7, Tiled TMX XML, JavaScript ES modules, Mocha + Chai frontend tests.

---

## File Structure

- Create `web/src/game/tiledMap.js`: parse the Juyi Hall TMX XML into normalized image layers, hotspots, obstacles, spawns, and coordinate-space metadata.
- Create `web/tests/juyiting-tiled-map.test.js`: focused unit tests for TMX parsing and coordinate normalization.
- Modify `web/src/game/resources.js`: include `hall.tmx`, expose fallback resources/hotspots, and remove static hotspots as the runtime source of truth.
- Modify `web/src/game/JuyitingGame.js`: wait for resource loading, parse the TMX map, start the PLAY state once ready, expose ready status, and accept hotspot sync.
- Modify `web/src/game/scenes/HallScene.js`: render image layers and hotspots from parsed Tiled data, register pointer events on canvas hit areas, sync scene hotspots, and preserve fallback behavior.
- Modify `web/src/game/entities/HallAgent.js`: implement spritesheet state animation, movement easing, pointer hit detection, state sync, bubbles, and selected/focused visuals.
- Modify `web/src/components/juyiting/HallStage.vue`: make melonJS the primary layer, hide DOM `AgentToken` when melonJS is ready, pass `sceneHotspots`, and keep DOM fallback.
- Modify `web/tests/juyiting-component-behavior.test.js`: assert `HallStage` syncs both agents and hotspots and uses the melonJS layer as active stage after ready.

## Task 1: TMX Parser

**Files:**
- Create: `web/src/game/tiledMap.js`
- Test: `web/tests/juyiting-tiled-map.test.js`

- [ ] **Step 1: Write parser tests**

Add `web/tests/juyiting-tiled-map.test.js`:

```js
import { expect } from 'chai'
import { readFileSync } from 'fs'

import { parseJuyiHallTmx, rectToPercent } from '../src/game/tiledMap.js'

describe('Juyi Hall Tiled map parser', () => {
  const xml = readFileSync(new URL('../public/juyiting/hall.tmx', import.meta.url), 'utf8')

  it('parses image layers, hotspots, obstacles, and spawn points from hall.tmx', () => {
    const map = parseJuyiHallTmx(xml)

    expect(map.width).to.equal(960)
    expect(map.height).to.equal(640)
    expect(map.coordinateWidth).to.equal(1672)
    expect(map.coordinateHeight).to.be.greaterThan(900)
    expect(map.imageLayers.background.source).to.equal('/juyiting/images/liangshan-hall-bg-v2.png')
    expect(map.imageLayers.foreground.source).to.equal('/juyiting/images/liangshan-hall-foreground-v1.png')
    expect(map.hotspots.map(item => item.id)).to.include.members([
      'mainSeat',
      'agentRoster',
      'bountyBoard',
      'personaCatalog',
      'libraryShelf'
    ])
    expect(map.hotspots.find(item => item.id === 'mainSeat')).to.include({
      panel: 'chat'
    })
    expect(map.obstacles.map(item => item.id)).to.include('main-seat')
    expect(map.spawns.songjiang).to.include.keys(['x', 'y'])
  })

  it('normalizes Tiled rectangles against image coordinate space', () => {
    const rect = rectToPercent({ x: 836, y: 470.5, width: 167.2, height: 94.1 }, { width: 1672, height: 941 })

    expect(rect.x).to.equal(50)
    expect(rect.y).to.equal(50)
    expect(rect.w).to.equal(10)
    expect(rect.h).to.equal(10)
  })
})
```

- [ ] **Step 2: Run the new parser test and verify it fails**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "Juyi Hall Tiled map parser"
```

Expected: FAIL with a module-not-found error for `../src/game/tiledMap.js`.

- [ ] **Step 3: Implement TMX parser**

Create `web/src/game/tiledMap.js`:

```js
const numberAttr = (node, name, fallback = 0) => {
  const value = Number(node?.getAttribute?.(name))
  return Number.isFinite(value) ? value : fallback
}

const textAttr = (node, name, fallback = '') => node?.getAttribute?.(name) || fallback

const absoluteJuyitingPath = (source = '') => {
  if (!source) return ''
  if (source.startsWith('/')) return source
  return `/juyiting/${source}`.replace(/\/+/g, '/')
}

const readProperties = (objectNode) => {
  const properties = {}
  objectNode.querySelectorAll('properties > property').forEach((property) => {
    properties[textAttr(property, 'name')] = textAttr(property, 'value')
  })
  return properties
}

const roundPercent = value => Math.round(value * 1000) / 1000

export const rectToPercent = (rect, space) => ({
  x: roundPercent(((rect.x + rect.width / 2) / space.width) * 100),
  y: roundPercent(((rect.y + rect.height / 2) / space.height) * 100),
  w: roundPercent((rect.width / space.width) * 100),
  h: roundPercent((rect.height / space.height) * 100)
})

const readObjectRect = objectNode => ({
  x: numberAttr(objectNode, 'x'),
  y: numberAttr(objectNode, 'y'),
  width: numberAttr(objectNode, 'width'),
  height: numberAttr(objectNode, 'height'),
  ellipse: Boolean(objectNode.querySelector('ellipse'))
})

const readObjectGroup = (doc, name) => {
  const group = [...doc.querySelectorAll('objectgroup')].find(item => textAttr(item, 'name') === name)
  if (!group) return []
  return [...group.querySelectorAll(':scope > object')]
}

const coordinateSpaceFor = (doc, mapWidth, mapHeight) => {
  const imageSizes = [...doc.querySelectorAll('imagelayer image')]
    .map(image => ({
      width: numberAttr(image, 'width'),
      height: numberAttr(image, 'height')
    }))
    .filter(size => size.width && size.height)

  const objectBounds = [...doc.querySelectorAll('object')].reduce((bounds, objectNode) => {
    const rect = readObjectRect(objectNode)
    return {
      width: Math.max(bounds.width, rect.x + rect.width),
      height: Math.max(bounds.height, rect.y + rect.height)
    }
  }, { width: mapWidth, height: mapHeight })

  return imageSizes.reduce((space, size) => ({
    width: Math.max(space.width, size.width),
    height: Math.max(space.height, size.height)
  }), objectBounds)
}

export const parseJuyiHallTmx = (xml) => {
  if (!xml || typeof DOMParser === 'undefined') {
    throw new Error('TMX XML parser unavailable')
  }

  const doc = new DOMParser().parseFromString(xml, 'application/xml')
  const parserError = doc.querySelector('parsererror')
  if (parserError) throw new Error('Invalid TMX XML')

  const mapNode = doc.querySelector('map')
  if (!mapNode) throw new Error('TMX map node missing')

  const width = numberAttr(mapNode, 'width') * numberAttr(mapNode, 'tilewidth')
  const height = numberAttr(mapNode, 'height') * numberAttr(mapNode, 'tileheight')
  const coordinateSpace = coordinateSpaceFor(doc, width, height)

  const imageLayers = {}
  doc.querySelectorAll('imagelayer').forEach((layer) => {
    const image = layer.querySelector('image')
    const name = textAttr(layer, 'name')
    imageLayers[name] = {
      id: name,
      source: absoluteJuyitingPath(textAttr(image, 'source')),
      width: numberAttr(image, 'width', coordinateSpace.width),
      height: numberAttr(image, 'height', coordinateSpace.height),
      offsetX: numberAttr(layer, 'offsetx'),
      offsetY: numberAttr(layer, 'offsety')
    }
  })

  const hotspots = readObjectGroup(doc, 'hotspots').map((objectNode) => {
    const rect = readObjectRect(objectNode)
    const props = readProperties(objectNode)
    return {
      id: textAttr(objectNode, 'name'),
      panel: props.panel || '',
      ...rectToPercent(rect, coordinateSpace),
      rect,
      properties: props
    }
  })

  const obstacles = readObjectGroup(doc, 'obstacles').map((objectNode) => {
    const rect = readObjectRect(objectNode)
    return {
      id: textAttr(objectNode, 'name'),
      ...rectToPercent(rect, coordinateSpace),
      rect
    }
  })

  const spawns = Object.fromEntries(readObjectGroup(doc, 'spawns').map((objectNode) => {
    const rawName = textAttr(objectNode, 'name')
    const name = rawName.replace(/^spawn_/, '')
    const rect = readObjectRect(objectNode)
    return [name, {
      id: name,
      rawName,
      x: roundPercent(((rect.x + rect.width / 2) / coordinateSpace.width) * 100),
      y: roundPercent(((rect.y + rect.height / 2) / coordinateSpace.height) * 100),
      rect
    }]
  }))

  return {
    width,
    height,
    coordinateWidth: coordinateSpace.width,
    coordinateHeight: coordinateSpace.height,
    imageLayers,
    hotspots,
    obstacles,
    spawns
  }
}
```

- [ ] **Step 4: Run parser test and verify it passes**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "Juyi Hall Tiled map parser"
```

Expected: PASS for both parser tests.

## Task 2: Resource Loading and Game Readiness

**Files:**
- Modify: `web/src/game/resources.js`
- Modify: `web/src/game/JuyitingGame.js`
- Test: `web/tests/juyiting-component-behavior.test.js`

- [ ] **Step 1: Add a component test expectation for hotspot sync**

In `web/tests/juyiting-component-behavior.test.js`, update the `syncs scene agents to the melonJS game layer when ready` test so the mock records hotspots too:

```js
const syncedAgents = []
const syncedHotspots = []
hallGameMock = {
  destroy: () => {},
  mount: async (_container, options = {}) => {
    options.onReady?.()
  },
  setSelectedAgent: () => {},
  start: () => {},
  syncAgents: agents => syncedAgents.push(agents),
  syncHotspots: hotspots => syncedHotspots.push(hotspots)
}
```

Pass `sceneHotspots` to `HallStage`:

```js
const sceneHotspots = [
  { id: 'bountyBoard', state: 'active', feedbackText: '荐单已出' }
]
```

Add it to props and assert:

```js
sceneHotspots,
```

```js
expect(syncedHotspots).to.deep.include(sceneHotspots)
```

- [ ] **Step 2: Run the updated component test and verify it fails**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "syncs scene agents"
```

Expected: FAIL because `HallStage` does not call `syncHotspots`.

- [ ] **Step 3: Update resources**

Change `web/src/game/resources.js` to include the TMX resource and fallback hotspots:

```js
export const HALL_MAP_RESOURCE = { name: 'juyiting-hall', type: 'tmx', src: '/juyiting/hall.tmx' }

export const HALL_RESOURCES = [
  HALL_MAP_RESOURCE,
  { name: 'liangshan-hall-bg', type: 'image', src: '/juyiting/images/liangshan-hall-bg-v2.png' },
  { name: 'liangshan-hall-fg', type: 'image', src: '/juyiting/images/liangshan-hall-foreground-v1.png' },
  { name: 'character-atlas', type: 'image', src: '/juyiting/liangshan-character-atlas-v2.png' }
]

export const FALLBACK_HALL_HOTSPOTS = [
  { id: 'mainSeat', panel: 'chat', x: 50, y: 36, w: 18, h: 11 },
  { id: 'agentRoster', panel: 'agents', x: 21, y: 35, w: 18, h: 15 },
  { id: 'bountyBoard', panel: 'tasks', x: 76, y: 47, w: 19, h: 18 },
  { id: 'personaCatalog', panel: 'catalog', x: 13, y: 77, w: 17, h: 15 },
  { id: 'libraryShelf', panel: 'library', x: 82, y: 76, w: 22, h: 18 }
]
```

- [ ] **Step 4: Update `JuyitingGame` to parse TMX and expose hotspot sync**

In `web/src/game/JuyitingGame.js`, import the parser and map resource:

```js
import { HALL_MAP_RESOURCE, HALL_RESOURCES } from './resources.js'
import { parseJuyiHallTmx } from './tiledMap.js'
```

Add fields in the constructor:

```js
this._mapData = null
this._pendingStart = false
```

After all resources load in `checkDone`, parse TMX before `_startGame(me)`:

```js
const tmx = me.loader.getTMX?.(HALL_MAP_RESOURCE.name)
try {
  this._mapData = tmx ? parseJuyiHallTmx(tmx) : null
} catch (error) {
  console.warn('[JuyitingGame] TMX parse failed:', error?.message || error)
  this._mapData = null
}
this._hallScene.setMapData(this._mapData)
this._startGame(me)
```

Change `start()` so it changes to PLAY only after resources are ready:

```js
start() {
  if (!this._me) return
  if (!this._initialized) {
    this._pendingStart = true
    return
  }
  this._me.state.change(this._me.state.PLAY, true)
}
```

At the end of `_startGame(me)`, honor pending start:

```js
if (this._pendingStart) {
  this._pendingStart = false
  me.state.change(me.state.PLAY, true)
}
```

Add:

```js
syncHotspots(list) {
  if (this._hallScene) this._hallScene.syncHotspots(list)
}
```

- [ ] **Step 5: Update `HallStage.vue` to sync hotspots**

In `web/src/components/juyiting/HallStage.vue`, inside `onReady` after `syncAgents`:

```js
juyitingGame.syncHotspots(props.sceneHotspots)
```

Add a watcher:

```js
watch(() => props.sceneHotspots, (hotspots) => {
  if (melonReady.value) juyitingGame.syncHotspots(hotspots || [])
}, { deep: true })
```

- [ ] **Step 6: Run the component test and verify it passes**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "syncs scene agents"
```

Expected: PASS.

## Task 3: melonJS Scene From Tiled Map

**Files:**
- Modify: `web/src/game/scenes/HallScene.js`
- Test: `web/tests/juyiting-component-behavior.test.js`

- [ ] **Step 1: Add a behavior assertion for melon layer readiness class**

In the HallStage sync test, after `await Vue.nextTick()`, assert:

```js
expect(wrapper.find('.hall-board').classes()).to.include('is-melon-ready')
```

Expected failure before implementation: `.hall-board` does not include `is-melon-ready`.

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "syncs scene agents"
```

Expected: FAIL because `is-melon-ready` is not rendered.

- [ ] **Step 3: Extend `HallScene` map rendering and hotspot state**

In `web/src/game/scenes/HallScene.js`, replace the `HALL_HOTSPOTS` import with:

```js
import { DEPTH_LAYERS } from '../config.js'
import { FALLBACK_HALL_HOTSPOTS } from '../resources.js'
```

Add constructor fields:

```js
this._mapData = null
this._hotspotState = new Map()
```

Add methods:

```js
setMapData(mapData) {
  this._mapData = mapData
}

syncHotspots(list = []) {
  this._hotspotState = new Map((list || []).map(item => [item.id, item]))
  this._hotspots.forEach(({ marker, label, data }) => {
    const state = this._hotspotState.get(data.id)
    marker.setFeedback?.(state)
    label?.setFeedback?.(state)
  })
}
```

Add a helper inside `onResetEvent()` before rendering hotspots:

```js
const mapData = this._mapData
const hotspots = mapData?.hotspots?.length ? mapData.hotspots : FALLBACK_HALL_HOTSPOTS
```

Render background and foreground from `mapData.imageLayers` when present, otherwise use loader names:

```js
const addImageLayer = (layer, fallbackName, depth) => {
  const image = layer?.source ? me.loader.getImage(layer.source.split('/').pop().replace(/\.png$/, '')) : me.loader.getImage(fallbackName)
  const fallbackImage = image || me.loader.getImage(fallbackName)
  if (!fallbackImage) return
  const sprite = new me.Sprite(vpW / 2, vpH / 2, {
    image: fallbackImage,
    anchorPoint: new me.Vector2d(0.5, 0.5)
  })
  sprite.floating = true
  sprite.scale(vpW / sprite.width, vpH / sprite.height)
  me.game.world.addChild(sprite, depth)
}
```

Use `addImageLayer(mapData?.imageLayers?.background, 'liangshan-hall-bg', DEPTH_LAYERS.BACKGROUND)` and foreground equivalent.

Replace `HALL_HOTSPOTS.forEach` with `hotspots.forEach`.

- [ ] **Step 4: Add hotspot marker renderable**

Inside `HallScene.js`, add a small renderable class in `onResetEvent()` before the hotspot loop:

```js
class HotspotMarker extends me.Renderable {
  constructor(x, y, w, h, data) {
    super(x, y, w, h)
    this.anchorPoint.set(0.5, 0.5)
    this.data = data
    this.feedback = null
  }

  setFeedback(feedback) {
    this.feedback = feedback || null
  }

  draw(renderer) {
    const ctx = renderer.getContext?.()
    if (!ctx) return
    ctx.save()
    const active = this.feedback?.state && this.feedback.state !== 'idle'
    ctx.fillStyle = active ? 'rgba(255, 214, 113, 0.18)' : 'rgba(255, 235, 180, 0.06)'
    ctx.strokeStyle = active ? 'rgba(255, 221, 130, 0.66)' : 'rgba(255, 235, 180, 0.16)'
    ctx.lineWidth = active ? 2 : 1
    ctx.beginPath()
    ctx.roundRect(this.pos.x - this.width / 2, this.pos.y - this.height / 2, this.width, this.height, 8)
    ctx.fill()
    ctx.stroke()
    if (this.feedback?.feedbackText) {
      ctx.font = 'bold 12px sans-serif'
      ctx.fillStyle = '#fff4d4'
      ctx.textAlign = 'center'
      ctx.fillText(this.feedback.feedbackText, this.pos.x, this.pos.y - this.height / 2 - 8)
    }
    ctx.restore()
  }
}
```

When creating markers:

```js
const marker = new HotspotMarker(ox + ow / 2, oy + oh / 2, ow, oh, h)
const state = this._hotspotState.get(h.id)
marker.setFeedback(state)
me.game.world.addChild(marker, DEPTH_LAYERS.HOTSPOTS)
this._hotspots.push({ marker, hitArea, data: h })
```

- [ ] **Step 5: Update `HallStage.vue` readiness class**

Change the hall board binding:

```vue
:class="{ 'is-dragging': mapDrag.active, 'is-melon-ready': melonReady }"
```

- [ ] **Step 6: Run the focused test and verify it passes**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "syncs scene agents"
```

Expected: PASS.

## Task 4: Agent Spritesheet Animation and Click Handling

**Files:**
- Modify: `web/src/game/entities/HallAgent.js`
- Modify: `web/src/game/scenes/HallScene.js`
- Test: `web/tests/juyiting-component-behavior.test.js`

- [ ] **Step 1: Add test coverage for agent click callback**

In `web/tests/juyiting-component-behavior.test.js`, add a new test:

```js
it('wires melonJS agent clicks back to Vue selection', async () => {
  let clickHandler
  hallGameMock = {
    destroy: () => {},
    mount: async (_container, options = {}) => {
      clickHandler = options.onAgentClick
      options.onReady?.()
    },
    setSelectedAgent: () => {},
    start: () => {},
    syncAgents: () => {},
    syncHotspots: () => {}
  }
  HallStage = loadSfc('../src/components/juyiting/HallStage.vue')
  const sceneAgents = [{ agentId: 'linchong', name: '林冲', x: 34, y: 63 }]
  const wrapper = mount(HallStage, {
    global: { stubs },
    props: {
      agentKey: agent => agent.agentId,
      agentStyle: () => ({}),
      portraitName: agent => agent.name,
      portraitShortName: agent => agent.name,
      portraitStyle: () => ({}),
      roleClass: () => '',
      sceneAgents,
      statusClass: () => '',
      statusText: () => '',
      visibleAgents: []
    }
  })

  clickHandler({ agentId: 'linchong' })

  expect(wrapper.emitted('select-agent')[0]).to.deep.equal([sceneAgents[0]])
})
```

- [ ] **Step 2: Run the new test**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "wires melonJS agent clicks"
```

Expected: PASS because the callback already exists. This locks the Vue/melonJS contract before changing entities.

- [ ] **Step 3: Implement sprite animation state in `HallAgent.js`**

In `HallAgent.js`, add fields:

```js
this._animTimer = 0
this._animFrame = 0
this._selected = false
this._focused = false
this._sourceData = agentData
```

Add:

```js
syncState(agentData = {}) {
  this._sourceData = { ...this._sourceData, ...agentData }
  if (agentData.x !== undefined && agentData.y !== undefined) this.setDestination(agentData.x, agentData.y)
  if (agentData.sceneStatus) this.setAnimState(agentData.sceneStatus)
  if (agentData.bubble) this.setBubble(agentData.bubble.text, agentData.bubble.ttlMs || 5000)
  this.setSelected(Boolean(agentData.selected))
  this._focused = Boolean(agentData.focused || agentData.recommended)
  if (agentData.facing) this.setFacing(agentData.facing)
}

setSelected(on) {
  this._selected = !!on
  this.setHighlighted(this._selected || this._focused)
}

containsPoint(x, y) {
  const width = this.width * this.scale
  const height = this.height * this.scale
  return x >= this.pos.x - width / 2 && x <= this.pos.x + width / 2 && y >= this.pos.y - height && y <= this.pos.y
}
```

Update `update(dt)`:

```js
this._animTimer += dt
if (this._animTimer > 160) {
  this._animTimer = 0
  this._animFrame = (this._animFrame + 1) % 4
}
```

Update `draw(renderer)` before `super.draw(renderer)`:

```js
const bob = this.currentAnim === ANIM_STATES.WALK || this.currentAnim === ANIM_STATES.BUSY
  ? Math.sin(this._animFrame * Math.PI / 2) * 2
  : Math.sin(this._animFrame * Math.PI / 2) * 0.8
this.pos.y += bob
super.draw(renderer)
this.pos.y -= bob
```

Then draw selected/focused rings:

```js
if (this._selected || this._focused) {
  ctx.save()
  ctx.strokeStyle = this._selected ? 'rgba(255, 221, 130, 0.85)' : 'rgba(255, 244, 212, 0.42)'
  ctx.lineWidth = this._selected ? 3 : 2
  ctx.beginPath()
  ctx.ellipse(this.pos.x, this.pos.y - 8, 24 * this.scale, 9 * this.scale, 0, 0, Math.PI * 2)
  ctx.stroke()
  ctx.restore()
}
```

- [ ] **Step 4: Register agent pointer hit areas in `HallScene.js`**

In `_fullSyncAgents()`, after creating a new agent:

```js
agent.onPointerDown = () => this._onAgentClick?.(agent._sourceData || data)
```

Add to `onResetEvent()` a canvas-level pointer registration:

```js
const stageHitArea = new me.Rect(0, 0, vpW, vpH)
me.input.registerPointerEvent('pointerdown', stageHitArea, (event) => {
  const x = event.gameX ?? event.clientX
  const y = event.gameY ?? event.clientY
  const hit = [...this._agents.values()].reverse().find(agent => agent.containsPoint(x, y))
  if (hit) {
    hit.onPointerDown?.()
    return false
  }
  return true
})
this._hotspots.push({ hitArea: stageHitArea, stage: true })
```

Update existing agent sync branch:

```js
agent.syncState(data)
```

- [ ] **Step 5: Run component behavior tests**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "JuyiHall component behavior"
```

Expected: PASS.

## Task 5: HallStage Primary melonJS Layer with DOM Fallback

**Files:**
- Modify: `web/src/components/juyiting/HallStage.vue`
- Test: `web/tests/juyiting-component-behavior.test.js`

- [ ] **Step 1: Add a test for DOM fallback hiding**

In `web/tests/juyiting-component-behavior.test.js`, in the sync test after ready:

```js
expect(wrapper.find('.map-world').classes()).to.include('is-dom-fallback-hidden')
```

Run the focused test and expect failure.

- [ ] **Step 2: Update `HallStage.vue` template**

Change:

```vue
<div ref="mapWorldRef" class="map-world" :style="mapWorldStyle">
```

to:

```vue
<div
  ref="mapWorldRef"
  class="map-world"
  :class="{ 'is-dom-fallback-hidden': melonReady }"
  :style="mapWorldStyle"
>
```

Keep `.melon-layer` after `.map-world`.

- [ ] **Step 3: Update layer CSS**

In `HallStage.vue` style:

```css
.melon-layer {
  position: absolute;
  inset: 0;
  z-index: 6;
  pointer-events: auto;
}

.melon-layer :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.map-world.is-dom-fallback-hidden .agent-token,
.map-world.is-dom-fallback-hidden .hall-foreground,
.map-world.is-dom-fallback-hidden .room-prop-layer,
.map-world.is-dom-fallback-hidden .map-region,
.map-world.is-dom-fallback-hidden .map-road {
  opacity: 0;
  pointer-events: none;
}

.map-world.is-dom-fallback-hidden .hall-room {
  opacity: 0;
  pointer-events: none;
}
```

Keep the `empty-hall` and `hall-overflow` visible only if they are needed outside melonJS:

```css
.map-world.is-dom-fallback-hidden .empty-hall {
  display: none;
}
```

- [ ] **Step 4: Run focused test**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test -- --grep "syncs scene agents"
```

Expected: PASS.

## Task 6: Full Verification and Deployment

**Files:**
- Verify all changed frontend files.

- [ ] **Step 1: Run lint**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run lint
```

Expected: exit 0.

- [ ] **Step 2: Run frontend tests**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run test
```

Expected: all tests pass.

- [ ] **Step 3: Run production build**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run build
```

Expected: Vite build exits 0.

- [ ] **Step 4: Optional browser visual smoke when dev server is needed**

Run:

```bash
cd /home/isp/wsps/cyf/web && npm run dev -- --host 0.0.0.0
```

Expected: Juyi Hall route shows a nonblank melonJS canvas with background, visible agents, clickable hotspots, and animated feedback.

- [ ] **Step 5: Deploy**

Run:

```bash
bash /home/isp/bin/cyf_web_kit_start.sh
```

Expected: deployment script exits 0.

- [ ] **Step 6: Public smoke check**

Run:

```bash
curl -k -sS -o /tmp/cyf-kit-index.html -w '%{http_code} %{size_download}\n' https://kit.chaoyoufan.cn/
```

Expected: `200` and a nonzero byte count.

- [ ] **Step 7: Commit and push frontend code**

Run:

```bash
cd /home/isp/wsps/cyf/web
git status --short --branch
git add src/game src/components/juyiting/HallStage.vue tests/juyiting-component-behavior.test.js tests/juyiting-tiled-map.test.js
git commit -m "feat: make juyi hall melonjs stage immersive"
git push origin develop
```

Expected: commit succeeds and `develop` pushes to `origin/develop`.

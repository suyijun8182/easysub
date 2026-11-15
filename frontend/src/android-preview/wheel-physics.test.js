import test from 'node:test'
import assert from 'node:assert/strict'
import { WHEEL_PHYSICS, wheelStep } from './wheel-physics.js'

test('damped wheel settles from either edge without exceeding the frame time cap', () => {
  for (const start of [-.8, 2.4, 7.8]) {
    let state = { position: start, velocity: 0 }
    for (let i = 0; i < 240; i++) state = wheelStep(state, 3, 1 / 60)
    assert.ok(Math.abs(state.position - 3) < WHEEL_PHYSICS.positionEpsilon)
    assert.ok(Math.abs(state.velocity) < WHEEL_PHYSICS.velocityEpsilon)
  }
  const state = { position: 0, velocity: 0 }
  assert.deepEqual(wheelStep(state, 3, 5), wheelStep(state, 3, WHEEL_PHYSICS.maxFrameSeconds))
})

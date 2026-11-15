// Positions are wheel rows; time is seconds except pointer timestamps (ms).
// Keep drag resistance, velocity projection and damped snapping calibrated together.
export const WHEEL_PHYSICS = Object.freeze({
  row: 44, bandTop: 66, center: 88,
  spring: 210, damping: 25, edgeResistance: .22,
  projectionMs: 160, staleVelocityMs: 90, minSampleMs: 8, tapSlop: 5,
  maxFrameSeconds: .032, positionEpsilon: .003, velocityEpsilon: .02
})
export function wheelStep({ position, velocity }, target, elapsed) {
  const dt = Math.min(elapsed, WHEEL_PHYSICS.maxFrameSeconds)
  velocity += ((target - position) * WHEEL_PHYSICS.spring - velocity * WHEEL_PHYSICS.damping) * dt
  return { position: position + velocity * dt, velocity }
}

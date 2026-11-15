import { createBitmapRenderer } from './bitmap-renderer.js'
import lightBackground from '../../../assest/debug24/backgrounds/onboarding-light.png'
import darkBackground from '../../../assest/debug24/backgrounds/onboarding-dark.png'

const files = import.meta.glob('../../../assest/debug24/icons/light/*.png', { eager: true, query: '?url', import: 'default' })
export const bitmapUrls = Object.fromEntries(Object.entries(files).map(([path, url]) => [path.split('/').at(-1).replace(/\.png$/, ''), url]))
export const bitmapIcon = createBitmapRenderer(bitmapUrls)
export const aboutBackgroundStyle = { '--about-bg-light': `url("${lightBackground}")`, '--about-bg-dark': `url("${darkBackground}")` }

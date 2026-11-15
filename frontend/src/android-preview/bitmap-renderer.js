const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]))

// PNG alpha supplies the shape. currentColor preserves theme and semantic states
// without shipping a different color bitmap for every button/state combination.
export function createBitmapRenderer(urls) {
  let sequence = 0
  return name => {
    if (!Object.hasOwn(urls, name) || typeof urls[name] !== 'string') return null
    const id = `app-png-mask-${++sequence}`
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%" aria-hidden="true" data-png-icon="${escape(name)}"><defs><mask id="${id}" x="0" y="0" width="24" height="24" maskUnits="userSpaceOnUse" style="mask-type:alpha"><image href="${escape(urls[name])}" x="0" y="0" width="24" height="24"/></mask></defs><rect width="24" height="24" fill="currentColor" mask="url(#${id})"/></svg>`
  }
}

const categoryGlyphs = {
  '📺':'category-streaming', '🤖':'category-ai', '🎮':'category-gaming',
  '🖥':'category-server', '📱':'category-sim', '🧩':'category-software',
  '🎵':'category-music', '☁':'category-cloud', '🌐':'category-domain',
  '💳':'category-membership', '🎓':'category-education', '📚':'category-education', '📰':'category-news',
  '💪':'category-fitness', '📦':'category-other'
}
export const categoryIconName = glyph => categoryGlyphs[String(glyph || '').replace(/\ufe0f/g, '')] || null

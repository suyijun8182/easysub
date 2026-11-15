import { readFile } from 'node:fs/promises'
import { parse } from '@vue/compiler-dom'
import { parse as parseSFC } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'

export async function renderClass(file, name, values) {
  const source = await readFile(new URL(file, import.meta.url), 'utf8')
  const template = parseSFC(source).descriptor.template.content
  function find(node) {
    if (node.props?.some(p => p.name === 'class' && p.value?.content.split(/\s+/).includes(name))) return node.loc.source
    for (const child of node.children || []) { const found = find(child); if (found) return found }
  }
  const fragment = find(parse(template))
  if (!fragment) throw new Error(`Missing template element: ${name}`)
  const app = createSSRApp({ template: fragment, setup: () => values })
  app.component('RouterLink', { props: ['to'], template:'<a :href="typeof to === \'string\' ? to : to.path"><slot /></a>' })
  app.component('SubIcon', { template: '<span />' })
  return renderToString(app)
}

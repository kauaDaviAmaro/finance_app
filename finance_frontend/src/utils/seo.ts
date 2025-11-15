interface SEOConfig {
  title?: string
  description?: string
  keywords?: string
  image?: string
  url?: string
  type?: string
  siteName?: string
  locale?: string
}

const defaultConfig: Required<SEOConfig> = {
  title: 'Finance App - Gerencie seus investimentos',
  description: 'Plataforma profissional para traders: scanner de ações, análise técnica com 6+ indicadores, alertas automáticos e gestão de portfólio com P&L em tempo real.',
  keywords: 'investimentos, ações, análise técnica, scanner de ações, RSI, MACD, Bollinger Bands, portfólio, trading, Brasil',
  image: '/favicon.svg',
  url: '',
  type: 'website',
  siteName: 'Finance App',
  locale: 'pt_BR',
}

export function useSEO(config: SEOConfig = {}) {
  const mergedConfig = { ...defaultConfig, ...config }

  // Update document title
  if (mergedConfig.title) {
    document.title = mergedConfig.title
  }

  // Update or create meta tags
  const updateMetaTag = (name: string, content: string, attribute: string = 'name') => {
    let element = document.querySelector(`meta[${attribute}="${name}"]`) as HTMLMetaElement
    if (!element) {
      element = document.createElement('meta')
      element.setAttribute(attribute, name)
      document.head.appendChild(element)
    }
    element.setAttribute('content', content)
  }

  // Basic meta tags
  if (mergedConfig.description) {
    updateMetaTag('description', mergedConfig.description)
  }

  if (mergedConfig.keywords) {
    updateMetaTag('keywords', mergedConfig.keywords)
  }

  // Open Graph tags
  updateMetaTag('og:title', mergedConfig.title, 'property')
  updateMetaTag('og:description', mergedConfig.description, 'property')
  updateMetaTag('og:type', mergedConfig.type, 'property')
  updateMetaTag('og:site_name', mergedConfig.siteName, 'property')
  updateMetaTag('og:locale', mergedConfig.locale, 'property')

  if (mergedConfig.url) {
    updateMetaTag('og:url', mergedConfig.url, 'property')
  }

  if (mergedConfig.image) {
    const fullImageUrl = mergedConfig.image.startsWith('http')
      ? mergedConfig.image
      : `${globalThis.location.origin}${mergedConfig.image}`
    updateMetaTag('og:image', fullImageUrl, 'property')
    updateMetaTag('og:image:secure_url', fullImageUrl, 'property')
    updateMetaTag('og:image:type', 'image/svg+xml', 'property')
  }

  // Twitter Card tags
  updateMetaTag('twitter:card', 'summary_large_image')
  updateMetaTag('twitter:title', mergedConfig.title)
  updateMetaTag('twitter:description', mergedConfig.description)

  if (mergedConfig.image) {
    const fullImageUrl = mergedConfig.image.startsWith('http')
      ? mergedConfig.image
      : `${globalThis.location.origin}${mergedConfig.image}`
    updateMetaTag('twitter:image', fullImageUrl)
  }

  // Canonical URL
  let canonicalLink = document.querySelector('link[rel="canonical"]') as HTMLLinkElement
  if (!canonicalLink) {
    canonicalLink = document.createElement('link')
    canonicalLink.setAttribute('rel', 'canonical')
    document.head.appendChild(canonicalLink)
  }
  if (mergedConfig.url) {
    canonicalLink.setAttribute('href', mergedConfig.url)
  } else {
    canonicalLink.setAttribute('href', globalThis.location.href)
  }
}

export function addStructuredData(data: object) {
  // Remove existing structured data script if any
  const existingScript = document.querySelector('script[type="application/ld+json"]')
  if (existingScript) {
    existingScript.remove()
  }

  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.textContent = JSON.stringify(data)
  document.head.appendChild(script)
}


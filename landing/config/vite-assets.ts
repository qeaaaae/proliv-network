const FONT_EXTENSIONS = new Set(['woff', 'woff2', 'ttf', 'otf', 'eot'])
const IMAGE_EXTENSIONS = new Set(['svg', 'png', 'jpg', 'jpeg', 'webp', 'avif', 'gif', 'ico'])

export const BUILD_ASSETS_DIR = '/_nuxt/'

const BUILD_ASSETS_OUTPUT_DIR = BUILD_ASSETS_DIR.replace(/^\/+|\/+$/g, '')
const APP_IMAGE_PATH_RE = /(?:^|\/app\/)assets\/images\/([^/]+)\//

interface BuildAssetInfo {
  names: string[]
  originalFileNames: string[]
}

const normalizePath = (value: string) => value.replace(/\\/g, '/')

const getExtension = (value: string) => {
  const match = value.match(/\.([^.\/]+)$/)
  return match?.[1]?.toLowerCase() ?? ''
}

const getImageGroup = (sourcePath: string) => {
  const group = sourcePath.match(APP_IMAGE_PATH_RE)?.[1]
  return group && /^[a-z0-9_-]+$/i.test(group) ? group : 'misc'
}

const assetsInlineLimit = (filePath: string) => (
  APP_IMAGE_PATH_RE.test(normalizePath(filePath)) ? false : undefined
)

const assetFileNames = (assetInfo: BuildAssetInfo) => {
  const sourcePath = normalizePath(assetInfo.originalFileNames[0] ?? '')
  const sourceName = assetInfo.names[0] ?? sourcePath.split('/').at(-1) ?? 'asset'
  const extension = getExtension(sourceName) || getExtension(sourcePath)

  if (extension === 'css') {
    return `${BUILD_ASSETS_OUTPUT_DIR}/css/[name].[hash].[ext]`
  }

  if (FONT_EXTENSIONS.has(extension)) {
    return `${BUILD_ASSETS_OUTPUT_DIR}/fonts/[name].[hash].[ext]`
  }

  if (IMAGE_EXTENSIONS.has(extension)) {
    return `${BUILD_ASSETS_OUTPUT_DIR}/images/${getImageGroup(sourcePath)}/[name].[hash].[ext]`
  }

  return `${BUILD_ASSETS_OUTPUT_DIR}/assets/[name].[hash].[ext]`
}

export const viteAssetBuild = {
  assetsInlineLimit,
  rolldownOptions: {
    output: {
      entryFileNames: `${BUILD_ASSETS_OUTPUT_DIR}/js/[name].[hash].js`,
      chunkFileNames: `${BUILD_ASSETS_OUTPUT_DIR}/js/[name].[hash].js`,
      assetFileNames
    }
  }
}

export const viteServerAssetBuild = {
  assetsInlineLimit,
  rolldownOptions: {
    output: {
      assetFileNames
    }
  }
}

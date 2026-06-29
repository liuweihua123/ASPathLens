import { createContext, useContext, useState, useCallback } from 'react'
import t from './translations.js'

const LangContext = createContext()

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'en')

  const toggle = useCallback(() => {
    setLang((prev) => {
      const next = prev === 'en' ? 'zh' : 'en'
      localStorage.setItem('lang', next)
      return next
    })
  }, [])

  /** Translate a key. Returns the key itself if not found. */
  const tr = useCallback(
    (key) => {
      const entry = t[key]
      if (!entry) return key
      return entry[lang] || entry.en || key
    },
    [lang],
  )

  /** Pick the right explanation field from API data: explanation_en or explanation_zh */
  const explain = useCallback(
    (obj) => {
      if (!obj) return ''
      if (lang === 'zh') return obj.explanation_zh || obj.explanation_en || ''
      return obj.explanation_en || obj.explanation_zh || ''
    },
    [lang],
  )

  /** Pick interpretation field from diff result */
  const interp = useCallback(
    (obj) => {
      if (!obj) return ''
      if (lang === 'zh') return obj.interpretation_zh || obj.interpretation_en || ''
      return obj.interpretation_en || obj.interpretation_zh || ''
    },
    [lang],
  )

  return (
    <LangContext.Provider value={{ lang, toggle, tr, explain, interp }}>
      {children}
    </LangContext.Provider>
  )
}

/** Access translations. `tr(key)` returns text, `explain(obj)` picks _en/_zh, `lang` is 'en'|'zh'. */
export function useLang() {
  return useContext(LangContext)
}

import { useEffect, useRef, useState } from 'react'
import JsBarcode from 'jsbarcode'

function ean13Valid(code) {
  if (!/^\d{13}$/.test(code)) return false
  let sum = 0
  for (let i = 0; i < 12; i += 1) {
    const n = Number(code[i])
    sum += i % 2 === 0 ? n : n * 3
  }
  return String((10 - (sum % 10)) % 10) === code[12]
}

function pickFormat(value) {
  const v = String(value || '').trim()
  if (ean13Valid(v)) return 'EAN13'
  if (/^\d{8}$/.test(v)) return 'EAN8'
  if (/^\d{12}$/.test(v)) return 'UPC'
  return 'CODE128'
}

/**
 * Renders a scannable barcode SVG for the given value.
 */
export default function BarcodePreview({ value, className = '', svgId }) {
  const svgRef = useRef(null)
  const [invalid, setInvalid] = useState(false)

  useEffect(() => {
    const raw = String(value || '').trim()
    const svg = svgRef.current
    if (!svg) return undefined

    if (!raw) {
      svg.replaceChildren()
      setInvalid(false)
      return undefined
    }

    try {
      JsBarcode(svg, raw, {
        format: pickFormat(raw),
        displayValue: true,
        fontSize: 13,
        height: 56,
        width: 1.6,
        margin: 6,
        background: '#ffffff',
        lineColor: '#111111',
        textMargin: 4,
      })
      setInvalid(false)
    } catch {
      svg.replaceChildren()
      setInvalid(true)
    }
    return undefined
  }, [value])

  if (!String(value || '').trim()) return null

  return (
    <div className={`barcode-preview ${className}`.trim()}>
      <svg ref={svgRef} id={svgId} role="img" aria-label={String(value)} />
      {invalid && <p className="barcode-preview-error muted">—</p>}
    </div>
  )
}

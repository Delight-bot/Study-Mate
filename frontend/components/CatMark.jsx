import React from 'react'

export default function CatMark({ size = 30 }) {
  return (
    <svg
      className="cat-mark"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
    >
      <path
        className="cat-mark-ears"
        d="M10 6 L18 20 L8 22 Z M38 6 L30 20 L40 22 Z"
      />
      <circle className="cat-mark-face" cx="24" cy="26" r="16" />
      <path className="cat-mark-inner-ear" d="M12 11 L16 19 L10.5 20 Z" />
      <path className="cat-mark-inner-ear" d="M36 11 L32 19 L37.5 20 Z" />
      {/* sleepy closed eyes */}
      <path className="cat-mark-eye" d="M16 26 q3 3 6 0" />
      <path className="cat-mark-eye" d="M26 26 q3 3 6 0" />
      <path className="cat-mark-nose" d="M22.5 31 L25.5 31 L24 33 Z" />
      <circle className="cat-mark-blush" cx="13" cy="30" r="2.2" />
      <circle className="cat-mark-blush" cx="35" cy="30" r="2.2" />
    </svg>
  )
}

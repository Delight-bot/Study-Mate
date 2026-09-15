import React from 'react'

export default function DeskAccessories({ active }) {
  return (
    <div className="desk-accessories" aria-hidden="true">
      <div className="fairy-lights">
        {Array.from({ length: 14 }).map((_, i) => (
          <span key={i} className="light" style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>

      <div className="accessory-row">
        <div className={`vinyl ${active ? 'spinning' : ''}`}>
          <div className="vinyl-center" />
        </div>

        <div className="mug">
          <span className={`mug-steam s1 ${active ? 'steaming' : ''}`} />
          <span className={`mug-steam s2 ${active ? 'steaming' : ''}`} />
          <span className={`mug-steam s3 ${active ? 'steaming' : ''}`} />
          <svg viewBox="0 0 64 48" className="mug-svg">
            <path className="mug-body" d="M8 14h36v20a10 10 0 0 1-10 10H18a10 10 0 0 1-10-10z" />
            <path className="mug-handle" d="M44 18h4a7 7 0 0 1 0 14h-4" fill="none" strokeWidth="4" />
          </svg>
        </div>

        <div className="plant">
          <svg viewBox="0 0 60 70" className="plant-svg">
            <path className="plant-stem" d="M30 62V38" strokeWidth="3" fill="none" />
            <path className="plant-leaf" d="M30 40c-10-2-16-12-14-22 10 2 16 12 14 22z" />
            <path className="plant-leaf" d="M30 34c10-2 16-12 14-22-10 2-16 12-14 22z" />
            <path className="plant-leaf" d="M30 44c-8-1-13-8-12-17 8 1 13 8 12 17z" />
            <rect className="plant-pot" x="14" y="46" width="32" height="18" rx="4" />
          </svg>
        </div>

        <div className="napping-cat">
          <svg viewBox="0 0 70 40" className="napping-cat-svg">
            <path className="cat-body" d="M4 34c0-12 10-20 30-20s32 8 32 20z" />
            <path className="cat-tail" d="M62 30c6-2 7-9 3-13" fill="none" strokeWidth="3" strokeLinecap="round" />
            <path className="cat-ear" d="M14 16 L20 6 L24 17 Z" />
            <path className="cat-ear" d="M30 13 L34 3 L38 14 Z" />
            <path className="cat-eye" d="M20 22 q2 2 4 0" />
            <path className="cat-eye" d="M30 22 q2 2 4 0" />
            <text className="cat-zzz" x="44" y="8">z</text>
          </svg>
        </div>
      </div>
    </div>
  )
}

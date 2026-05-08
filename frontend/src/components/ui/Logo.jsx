export default function Logo({ size = 32, dark = false }) {
  const bg = dark ? '#ffffff' : '#0f172a'
  const fg = dark ? '#0f172a' : '#ffffff'

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="32" height="32" rx="8" fill={bg} />
      {/* Left node */}
      <circle cx="7" cy="16" r="3" fill={fg} />
      {/* Right node */}
      <circle cx="25" cy="16" r="3" fill={fg} />
      {/* Arrow: line + chevron head */}
      <path
        d="M10 16H19M17 12.5L21 16L17 19.5"
        stroke={fg}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

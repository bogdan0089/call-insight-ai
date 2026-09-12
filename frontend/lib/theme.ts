export const color = {
  bg: "#0b0f12",
  surface: "#111819",
  surfaceRaised: "#16201f",
  surfaceInset: "#0e1416",

  borderSoft: "#1b2528",
  border: "#243135",
  borderStrong: "#33454a",

  text: "#eef5f4",
  textMuted: "#8fa5a6",
  textDim: "#6c8184",
  textFaint: "#47585c",

  accent: "#2dd4bf",
  accentSoft: "#2dd4bf1a",
  accentBorder: "#2dd4bf40",
  onAccent: "#04211d",

  pass: "#34d399",
  passBg: "#34d39912",
  passBorder: "#34d39940",

  fail: "#f87171",
  failBg: "#f8717112",
  failBorder: "#f8717140",

  warn: "#fbbf24",
  warnBg: "#fbbf2412",
  warnBorder: "#fbbf2440",

  info: "#60a5fa",
  infoBg: "#60a5fa12",
  infoBorder: "#60a5fa40",
} as const;

export const radius = {
  sm: "6px",
  md: "10px",
  lg: "14px",
  pill: "999px",
} as const;

export const space = {
  xs: "6px",
  sm: "10px",
  md: "16px",
  lg: "24px",
  xl: "36px",
} as const;

export const type = {
  mono: '"JetBrains Mono", "SF Mono", ui-monospace, "Cascadia Mono", Menlo, monospace',
  label: {
    fontSize: "10px",
    letterSpacing: "1.4px",
    textTransform: "uppercase" as const,
    fontWeight: 700,
  },
} as const;

interface ChatPanelIconProps {
  size?: number;
}

export function ChatPanelIcon({ size = 16 }: ChatPanelIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        d="M3 2.5h10a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5H7l-2.2 2.2A.5.5 0 0 1 4 13.5V11.5H3a1.5 1.5 0 0 1-1.5-1.5V4A1.5 1.5 0 0 1 3 2.5z"
      />
    </svg>
  );
}

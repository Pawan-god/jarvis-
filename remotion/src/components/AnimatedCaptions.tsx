import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";

interface Caption {
  word: string;
  start: number; // seconds
  end: number; // seconds
}

interface AnimatedCaptionsProps {
  captions: Caption[];
  style: string;
}

export const AnimatedCaptions: React.FC<AnimatedCaptionsProps> = ({
  captions,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (style === "word-by-word") {
    return <WordByWordCaptions captions={captions} currentTime={currentTime} fps={fps} frame={frame} />;
  }

  return <SentenceCaptions captions={captions} currentTime={currentTime} fps={fps} frame={frame} />;
};

/**
 * TikTok-style word-by-word captions with pop-in animation.
 * Shows 3-4 words at a time, highlighting the current word.
 */
const WordByWordCaptions: React.FC<{
  captions: Caption[];
  currentTime: number;
  fps: number;
  frame: number;
}> = ({ captions, currentTime, fps, frame }) => {
  // Group words into chunks of 3-4
  const chunkSize = 3;
  const chunks: Caption[][] = [];
  for (let i = 0; i < captions.length; i += chunkSize) {
    chunks.push(captions.slice(i, i + chunkSize));
  }

  // Find the active chunk
  const activeChunk = chunks.find((chunk) => {
    const chunkStart = chunk[0].start;
    const chunkEnd = chunk[chunk.length - 1].end;
    return currentTime >= chunkStart && currentTime <= chunkEnd;
  });

  if (!activeChunk) return null;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        top: "35%",
        zIndex: 20,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 12,
          padding: "0 40px",
        }}
      >
        {activeChunk.map((caption, index) => {
          const isActive = currentTime >= caption.start && currentTime <= caption.end;
          const wordFrame = Math.max(0, frame - caption.start * fps);

          const scale = spring({
            frame: wordFrame,
            fps,
            config: { damping: 8, stiffness: 200 },
          });

          return (
            <span
              key={`${caption.word}-${index}`}
              style={{
                fontSize: 72,
                fontWeight: 900,
                fontFamily: "'Inter', 'SF Pro Display', sans-serif",
                color: isActive ? "#FFD700" : "#FFFFFF",
                textShadow: isActive
                  ? "0 0 20px rgba(255, 215, 0, 0.5), 2px 2px 4px rgba(0,0,0,0.8)"
                  : "2px 2px 4px rgba(0,0,0,0.8)",
                transform: `scale(${isActive ? scale : 1})`,
                transition: "color 0.1s ease",
                textTransform: "uppercase",
                letterSpacing: "-0.02em",
              }}
            >
              {caption.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Full sentence captions with fade-in.
 */
const SentenceCaptions: React.FC<{
  captions: Caption[];
  currentTime: number;
  fps: number;
  frame: number;
}> = ({ captions, currentTime, fps, frame }) => {
  // Build sentences from word timestamps
  const activeCaptions = captions.filter(
    (c) => currentTime >= c.start && currentTime <= c.end + 0.5
  );

  if (activeCaptions.length === 0) return null;

  const text = activeCaptions.map((c) => c.word).join(" ");
  const startFrame = activeCaptions[0].start * fps;

  const opacity = interpolate(
    frame,
    [startFrame, startFrame + 5],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        top: "35%",
        zIndex: 20,
        pointerEvents: "none",
        opacity,
      }}
    >
      <div
        style={{
          fontSize: 56,
          fontWeight: 800,
          fontFamily: "'Inter', 'SF Pro Display', sans-serif",
          color: "#FFFFFF",
          textShadow: "2px 2px 8px rgba(0,0,0,0.9)",
          textAlign: "center",
          padding: "0 60px",
          lineHeight: 1.2,
          textTransform: "uppercase",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

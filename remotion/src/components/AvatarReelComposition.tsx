import {
  AbsoluteFill,
  Audio,
  Sequence,
  Video,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { AnimatedCaptions } from "./AnimatedCaptions";

interface Caption {
  word: string;
  start: number; // seconds
  end: number; // seconds
}

interface CompositionConfig {
  width: number;
  height: number;
  fps: number;
  avatarPosition: string;
  avatarSizeRatio: number;
  captionStyle: string;
  musicVolume: number;
  transitionType: string;
  transitionDuration: number;
}

interface AvatarReelProps {
  avatarVideo: string;
  brollClips: string[];
  audioPath: string;
  captions: Caption[];
  musicPath: string | null;
  config: CompositionConfig;
}

export const AvatarReelComposition: React.FC<AvatarReelProps> = ({
  avatarVideo,
  brollClips,
  audioPath,
  captions,
  musicPath,
  config,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Calculate b-roll clip duration in frames
  const totalFrames = fps * 60; // will be overridden
  const clipDurationFrames = brollClips.length > 0
    ? Math.floor(totalFrames / brollClips.length)
    : totalFrames;

  // Avatar dimensions
  const avatarWidth = Math.floor(width * config.avatarSizeRatio);
  const avatarHeight = Math.floor(avatarWidth * (16 / 9)); // maintain aspect

  // Avatar position
  const avatarStyle: React.CSSProperties = {
    position: "absolute",
    width: avatarWidth,
    height: avatarHeight,
    bottom: 120, // space for captions
    left: "50%",
    transform: "translateX(-50%)",
    borderRadius: 20,
    overflow: "hidden",
    zIndex: 10,
    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
  };

  // Avatar entrance animation
  const avatarScale = spring({
    frame: frame,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* B-Roll Background Layer */}
      {brollClips.map((clip, index) => {
        const startFrame = index * clipDurationFrames;
        const transitionFrames = Math.floor(config.transitionDuration * fps);

        // Crossfade opacity
        const opacity = interpolate(
          frame,
          [
            startFrame,
            startFrame + transitionFrames,
            startFrame + clipDurationFrames - transitionFrames,
            startFrame + clipDurationFrames,
          ],
          [0, 1, 1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        // Subtle zoom effect (Ken Burns)
        const scale = interpolate(
          frame,
          [startFrame, startFrame + clipDurationFrames],
          [1.0, 1.08],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={clipDurationFrames}
          >
            <AbsoluteFill
              style={{
                opacity,
                transform: `scale(${scale})`,
              }}
            >
              <Video
                src={clip}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Gradient overlay for text readability */}
      <AbsoluteFill
        style={{
          background: "linear-gradient(transparent 40%, rgba(0,0,0,0.6) 100%)",
          zIndex: 5,
        }}
      />

      {/* Avatar Overlay (Picture-in-Picture) */}
      {avatarVideo && (
        <div
          style={{
            ...avatarStyle,
            transform: `translateX(-50%) scale(${avatarScale})`,
          }}
        >
          <Video
            src={avatarVideo}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </div>
      )}

      {/* Animated Captions */}
      {captions.length > 0 && (
        <AnimatedCaptions
          captions={captions}
          style={config.captionStyle}
        />
      )}

      {/* Narration Audio */}
      {audioPath && <Audio src={audioPath} />}

      {/* Background Music */}
      {musicPath && <Audio src={musicPath} volume={config.musicVolume} />}
    </AbsoluteFill>
  );
};

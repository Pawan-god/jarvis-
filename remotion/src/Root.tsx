import { Composition } from "remotion";
import { AvatarReelComposition } from "./components/AvatarReelComposition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AvatarReelComposition"
        component={AvatarReelComposition}
        durationInFrames={30 * 60} // 60 seconds at 30fps, overridden by props
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          avatarVideo: "",
          brollClips: [],
          audioPath: "",
          captions: [],
          musicPath: null,
          config: {
            width: 1080,
            height: 1920,
            fps: 30,
            avatarPosition: "bottom-center",
            avatarSizeRatio: 0.35,
            captionStyle: "word-by-word",
            musicVolume: 0.15,
            transitionType: "crossfade",
            transitionDuration: 0.5,
          },
        }}
      />
    </>
  );
};

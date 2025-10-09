import { useEffect, useState } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { artworkService, Artwork } from "@/services/artwork";
import { visionAiService } from "@/services/visionAi";
import { Loader2, ExternalLink } from "lucide-react";

interface Story {
  id: string;
  name: string;
  avatar: string;
  artworkId: string;
  image: string;
  storyText?: {
    title: string;
    narrative: string;
    tutorial: string;
  };
  createdAt: string;
}

export const StoryBar = () => {
  const [stories, setStories] = useState<Story[]>([]);
  const [activeStory, setActiveStory] = useState<Story | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [loadingStory, setLoadingStory] = useState(false);

  // Auto-advance slides like Instagram stories
  useEffect(() => {
    if (!activeStory) return;

    const timer = setTimeout(() => {
      if (currentSlide < 2) {
        setCurrentSlide((prev) => prev + 1);
      } else {
        closeStory();
      }
    }, 8000); // 8 seconds per slide

    return () => clearTimeout(timer);
  }, [activeStory, currentSlide]);

  // Load artworks and map to stories
  useEffect(() => {
    const loadStories = async () => {
      const res = await artworkService.getAllArtworks();
      if (res.artworks) {
        const validStories = res.artworks
          .filter(
            (art) =>
              new Date().getTime() -
                new Date(art.createdAt).getTime() <
              48 * 60 * 60 * 1000 // 48h expiry
          )
          .map((art) => ({
            id: art._id,
            name: art.artistId.name,
            avatar:
              art.artistId.avatarUrl ||
              `https://ui-avatars.com/api/?name=${encodeURIComponent(
                art.artistId.name
              )}`,
            artworkId: art._id,
            image: art.media?.[0]?.url || "",
            createdAt: art.createdAt,
          }));
        setStories(validStories);
      }
    };
    loadStories();
  }, []);

  const openStory = async (story: Story) => {
    setActiveStory(story);
    setCurrentSlide(0);

    if (!story.storyText) {
      try {
        setLoadingStory(true);
        const fileResp = await fetch(story.image);
        const blob = await fileResp.blob();
        const aiResp = await visionAiService.generateStory(
          new File([blob], "art.jpg", { type: blob.type })
        );

        const text = {
          title: aiResp?.data?.title ?? "Untitled Artwork",
          narrative: aiResp?.data?.narrative ?? "No story generated.",
          tutorial: aiResp?.data?.tutorial ?? "No tutorial generated.",
        };

        setActiveStory({ ...story, storyText: text });
        setStories((prev) =>
          prev.map((s) => (s.id === story.id ? { ...s, storyText: text } : s))
        );
      } catch (err) {
        console.error("Failed to generate story", err);
      } finally {
        setLoadingStory(false);
      }
    }
  };

  const closeStory = () => {
    setActiveStory(null);
    setCurrentSlide(0);
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-2">
      {stories.map((story) => (
        <div
          key={story.id}
          className="flex flex-col items-center gap-2 cursor-pointer"
          onClick={() => openStory(story)}
        >
          <div className="story-ring p-0.5 rounded-full border-2 border-pink-500">
            <Avatar className="w-16 h-16">
              <AvatarImage src={story.image} alt={story.name} />
              <AvatarFallback>{story.name[0]}</AvatarFallback>
            </Avatar>
          </div>
          <span className="text-xs text-muted-foreground">{story.name}</span>
        </div>
      ))}

      {/* Story Modal */}
      <Dialog open={!!activeStory} onOpenChange={closeStory}>
        <DialogContent className="max-w-md p-0 overflow-hidden bg-[#dfc5fe] text-white">
          {activeStory && (
            <div className="relative w-full h-full flex flex-col items-center justify-center">
              {/* Progress Bar for Slides */}
              <div className="absolute top-0 left-0 w-full flex gap-1 p-2">
                {[0, 1, 2].map((index) => (
                  <div
                    key={index}
                    className={`h-1 flex-1 rounded-full ${
                      index <= currentSlide ? "bg-white" : "bg-white/30"
                    } ${index === currentSlide ? "animate-pulse" : ""}`}
                  />
                ))}
              </div>

              {currentSlide === 0 && (
                <div className="w-full flex flex-col items-center justify-center p-6">
                  <img
                    src={activeStory.image}
                    alt={activeStory.name}
                    className="max-h-[60vh] w-auto object-contain rounded-md"
                  />
                  <h2 className="mt-4 text-2xl font-bold text-center text-gray-800 font-serif">
                    {activeStory.storyText?.title || "Untitled Artwork"}
                  </h2>
                  <div className="mt-4 flex gap-4">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setCurrentSlide(1)}
                    >
                      Next →
                    </Button>
                  </div>
                </div>
              )}

              {currentSlide === 1 && (
                <div className="w-full flex flex-col items-center justify-center px-6 py-10">
                  {loadingStory ? (
                    <Loader2 className="animate-spin h-8 w-8 text-gray-800" />
                  ) : (
                    <>
                      <p className="text-base text-center text-gray-800 font-sans leading-relaxed whitespace-pre-line max-h-[60vh] overflow-y-auto">
                        {activeStory.storyText?.narrative || "No narrative available."}
                      </p>
                      <div className="mt-6 flex gap-4">
                        <Button size="sm" onClick={() => setCurrentSlide(0)}>
                          ← Back
                        </Button>
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => setCurrentSlide(2)}
                        >
                          Next →
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {currentSlide === 2 && (
                <div className="w-full flex flex-col items-center justify-center px-6 py-10">
                  {loadingStory ? (
                    <Loader2 className="animate-spin h-8 w-8 text-gray-800" />
                  ) : (
                    <>
                      <p className="text-base text-center text-gray-800 font-sans leading-relaxed whitespace-pre-line max-h-[60vh] overflow-y-auto">
                        {activeStory.storyText?.tutorial || "No tutorial available."}
                      </p>
                      <a
                        href={`/artwork/${activeStory.artworkId}`}
                        className="mt-4 flex items-center gap-2 text-pink-600 hover:underline font-semibold"
                      >
                        View Artwork <ExternalLink size={16} />
                      </a>
                      <div className="mt-6 flex gap-4">
                        <Button size="sm" onClick={() => setCurrentSlide(1)}>
                          ← Back
                        </Button>
                        <Button size="sm" variant="secondary" onClick={closeStory}>
                          Close
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
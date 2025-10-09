// Mock AI client for generating captions, stories, and hashtags
// This is designed to be easily replaced with a real GenAI endpoint

export interface AIGenerateRequest {
  type: 'caption' | 'story' | 'hashtags';
  prompt: string;
}

export interface AIGenerateResponse {
  text: string;
}

const mockResponses = {
  caption: [
    "✨ Living my best life! What's your favorite way to unwind? 💫",
    "Found this gem and had to share! Perfect for your collection 🌟",
    "Sunday vibes hitting different today ☀️ What are you up to?",
    "When you find something that just speaks to your soul 💝",
    "Creating memories one moment at a time 📸 #blessed",
  ],
  story: [
    "Hey everyone! 👋 Just discovered this amazing find and couldn't wait to share it with you all!",
    "Behind the scenes moment! 🎬 This is how I create content that connects with you",
    "Quick update from my day! Thanks for following along on this journey 💕",
    "Real talk: Sometimes the best moments are the unplanned ones ✨",
    "Coffee in hand, ready to take on the world! ☕ What's motivating you today?",
  ],
  hashtags: [
    "#lifestyle #vibes #authentic #discover #moments #blessed #grateful #community",
    "#creative #inspiration #handmade #unique #artisan #smallbusiness #supportlocal #love",
    "#weekend #selfcare #mindfulness #positivity #growth #journey #explore #dream",
    "#fashion #style #trendy #chic #elegant #timeless #vintage #modern",
    "#home #decor #cozy #minimalist #aesthetic #design #comfort #sanctuary",
  ],
};

// Simulate API delay for realistic behavior
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const aiClient = {
  async generate({ type, prompt }: AIGenerateRequest): Promise<AIGenerateResponse> {
    // Simulate API call delay
    await delay(1000 + Math.random() * 2000);

    // Mock different responses based on prompt content
    const responses = mockResponses[type];
    let selectedResponse: string;

    // Simple logic to vary responses based on prompt
    if (prompt.toLowerCase().includes('product')) {
      selectedResponse = responses[0];
    } else if (prompt.toLowerCase().includes('lifestyle')) {
      selectedResponse = responses[1];
    } else if (prompt.toLowerCase().includes('creative')) {
      selectedResponse = responses[2];
    } else {
      // Random selection for other cases
      selectedResponse = responses[Math.floor(Math.random() * responses.length)];
    }

    return { text: selectedResponse };
  },
};
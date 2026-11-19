const ODYSSEY_API_KEY = process.env.ODYSSEY_API_KEY;
export function createVideoSession(prompt) {
  return { available: true, apiKey: ODYSSEY_API_KEY, prompt };
}

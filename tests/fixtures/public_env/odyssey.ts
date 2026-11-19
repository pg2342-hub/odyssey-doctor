import { Odyssey } from '@odysseyml/odyssey';
export const client = new Odyssey({ apiKey: process.env.NEXT_PUBLIC_ODYSSEY_API_KEY });

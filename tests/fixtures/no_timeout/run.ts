import { Odyssey } from '@odysseyml/odyssey';
const client = new Odyssey({ apiKey: process.env.ODYSSEY_API_KEY });
try { await client.connect(); await client.startStream({ prompt: 'A cat' }); } finally { client.disconnect(); }

import { Odyssey } from '@odysseyml/odyssey';
const client = new Odyssey({ apiKey: process.env.ODYSSEY_API_KEY });
export default client;

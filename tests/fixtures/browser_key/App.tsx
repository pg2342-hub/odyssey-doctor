import { Odyssey } from '@odysseyml/odyssey';
const client = new Odyssey({ apiKey: 'ody_your_api_key_here' });
export default function App() { return <button onClick={() => client.connect()}>Go</button>; }

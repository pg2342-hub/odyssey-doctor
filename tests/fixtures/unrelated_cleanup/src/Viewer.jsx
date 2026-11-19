import { Odyssey } from '@odysseyml/odyssey';
import { useEffect } from 'react';
export function Viewer({ creds }) {
  const client = new Odyssey();
  useEffect(() => {
    const id = requestAnimationFrame(() => {});
    return () => { cancelAnimationFrame(id); };
  }, []);
  const go = async () => { await client.connectWithCredentials(creds, {}); await client.startStream({ prompt: 'A lake' }); };
  const switchMode = () => client.disconnect();
  return <div onClick={go} onDoubleClick={switchMode} />;
}

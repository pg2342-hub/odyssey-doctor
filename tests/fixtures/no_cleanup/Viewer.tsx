'use client';
import { Odyssey } from '@odysseyml/odyssey';
export function Viewer({ creds }) {
  const client = new Odyssey();
  const go = async () => { await client.connectWithCredentials(creds, { onStreamError: () => {} }); await client.startStream({ prompt: 'A lake' }); };
  const stop = () => client.disconnect();
  return <div onClick={go} onDoubleClick={stop} />;
}

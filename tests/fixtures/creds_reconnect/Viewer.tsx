'use client';
import { useEffect } from 'react';
import { Odyssey } from '@odysseyml/odyssey';
export function Viewer({ creds }) {
  useEffect(() => {
    const client = new Odyssey();
    client.connectWithCredentials(creds, {
      onStreamError: async (reason) => { if (reason === 'session_timeout') { await client.connect(); } },
    });
    return () => client.disconnect();
  }, []);
  return null;
}

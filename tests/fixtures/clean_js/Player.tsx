'use client';
import { useEffect } from 'react';
import { Odyssey, credentialsFromDict, MonthlyLimitReachedError, ConcurrentLimitReachedError } from '@odysseyml/odyssey';
export function Player() {
  useEffect(() => {
    const client = new Odyssey();
    async function start() {
      const creds = credentialsFromDict(await (await fetch('/api/credentials', { method: 'POST' })).json());
      try {
        await client.connectWithCredentials(creds, {
          onStreamError: (reason) => { if (reason === 'session_timeout') { client.disconnect(); start(); } },
        });
        await client.startStream({ prompt: 'A forest' });
      } catch (e) {
        if (e instanceof MonthlyLimitReachedError || e instanceof ConcurrentLimitReachedError) { /* tell the user */ }
      }
    }
    start();
    return () => client.disconnect();
  }, []);
  return null;
}

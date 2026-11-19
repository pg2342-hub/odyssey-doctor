'use client';
import { useOdyssey } from '@odysseyml/odyssey/react';
export default function App({ creds }) {
  const odyssey = useOdyssey({ handlers: { onStreamError: (r) => { if (r === 'session_timeout') odyssey.connect(); } } });
  return <button onClick={() => odyssey.connect()}>Go</button>;
}

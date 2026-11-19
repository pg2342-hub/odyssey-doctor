import express from 'express';
import { Odyssey, credentialsToDict } from '@odysseyml/odyssey';
const app = express();
const server = new Odyssey({ apiKey: process.env.ODYSSEY_API_KEY! });
app.post('/api/credentials', async (_req, res) => res.json(credentialsToDict(await server.createClientCredentials())));

import express from 'express';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';

const app = express();
const PORT = process.env.PORT || 3000;
const __dirname = dirname(fileURLToPath(import.meta.url));
app.use(cors());
app.use(express.static(resolve(__dirname, 'dist')));
app.all('*', (req, res) => {
  res.sendFile(resolve(__dirname, 'dist', 'index.html'));
});
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
